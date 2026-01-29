from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models, router
from django.db.models.fields.related_descriptors import ForwardManyToOneDescriptor

from isapilib.api.models import UserAPI  # noqa keep this
from isapilib.logging import logger


class DynamicManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        meta = queryset.model._meta
        db_table_options = meta.db_table

        if not isinstance(db_table_options, dict):
            return queryset

        name = queryset.model.__name__
        using = router.db_for_write(None)
        version = settings.DATABASES[using]['INTELISIS_VERSION']

        try:
            db_table_options = {int(k): v for k, v in db_table_options.items()}
        except ValueError:
            raise ImproperlyConfigured(f'{name} does not have a valid db_table definition, expected {{int:str}}')

        db_table_default = getattr(meta, 'db_table_default', 6000)

        logger.debug('Dynamic table resolution for model %s using=%s version=%s default=%s options=%s',
                     name, using, version, db_table_default, db_table_options)

        if table_name := db_table_options.get(version):
            meta.db_table = table_name
            logger.debug('Resolved table for %s using version %s → %s', name, version, table_name)
            return queryset

        if table_name := db_table_options.get(db_table_default):
            meta.db_table = table_name
            logger.debug('Resolved table for %s using default %s → %s', name, db_table_default, table_name)
            return queryset

        raise Exception(f'The model {name} does not have a table for version {version} using connection {using}')


class BaseModel(models.Model):
    objects = DynamicManager()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        for field in self._meta.get_fields():
            if isinstance(field, models.CharField):
                val = str(getattr(self, field.name) or '')
                if val and field.max_length < len(val):
                    truncated = val[:field.max_length]
                    setattr(self, field.name, truncated)
                    logger.warning('Value field %s.%s was truncated to %s characters (%r:%r)',
                                   self.__class__.__name__, field.name, field.max_length, val, truncated)

        if not using: using = router.db_for_write(None)
        query = self.__class__.objects.using(using).filter(pk=self.pk)

        if self.pk and query.exists():
            fields = update_fields or [
                field.name for field in self._meta.fields
                if field.name != self._meta.pk.name and not isinstance(field, (models.AutoField, models.BigAutoField))
            ]
            values = {field: getattr(self, field) for field in fields}
            query.update(**values)
        else:
            super().save(force_insert, force_update, using, update_fields)

    class Meta:
        abstract = True


class DummyForwardManyToOneDescriptor(ForwardManyToOneDescriptor):
    def __get__(self, instance, cls=None):
        try:
            value = super().__get__(instance, cls)
        except self.field.remote_field.model.DoesNotExist:
            value = getattr(instance, self.field.get_attname())
        return value

    def __set__(self, instance, value):
        if value is not None and not isinstance(value, self.field.remote_field.model._meta.concrete_model):
            setattr(instance, self.field.get_attname(), value)
            instance._state.fields_cache.pop(self.field.name, None)
        else:
            return super().__set__(instance, value)


class DummyForeignKey(models.ForeignKey):
    forward_related_accessor_class = DummyForwardManyToOneDescriptor


def contribute_to_model(model, column, field):
    field.contribute_to_class(model, column)
