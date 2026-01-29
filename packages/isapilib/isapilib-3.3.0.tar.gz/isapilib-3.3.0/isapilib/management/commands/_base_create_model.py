import sys

from django.core import exceptions
from django.core.management.base import BaseCommand
from django.db import models
from django.utils.text import capfirst


class NotRunningInTTYException(Exception):
    pass


class BaseCreateModelCommand(BaseCommand):
    Model = None

    def add_arguments(self, parser):
        parser.add_argument(
            "--all_fields",
            help="Specifies whether the record should be created using only the minimum required fields or all available fields",
            default=False,
        )

    def is_required(self, field):
        return not field.blank and field.default is models.NOT_PROVIDED

    def is_foreign_key(self, field):
        return field.is_relation and field.many_to_one

    def _get_input_message(self, field, default=None):
        return "%s%s%s: " % (
            capfirst(field.verbose_name),
            " (leave blank to use '%s')" % default if default else "",
            (
                " (%s.%s)"
                % (
                    field.remote_field.model._meta.object_name,
                    (
                        field.m2m_target_field_name()
                        if field.many_to_many
                        else field.remote_field.field_name
                    ),
                )
                if field.remote_field
                else ""
            ),
        )

    def get_input_data(self, field, message, default=None):
        raw_value = input(message)
        if default and raw_value == "":
            raw_value = default
        try:
            val = field.clean(raw_value, None)
        except exceptions.ValidationError as e:
            self.stderr.write("Error: %s" % "; ".join(e.messages))
            val = None

        return val

    def handle(self, *args, **options):
        if hasattr(sys.stdin, "isatty") and not sys.stdin.isatty():
            raise NotRunningInTTYException

        all_fields = options["all_fields"]

        data = {}

        fields = self.Model._meta.fields
        if not all_fields:
            fields = [i for i in fields if self.is_required(i)]

        for field in fields:
            if field.primary_key:
                continue

            field_name = field.name
            data[field_name] = None
            while data[field_name] is None:
                message = self._get_input_message(field)
                input_value = self.get_input_data(field, message)
                data[field_name] = input_value

                if field.many_to_many and input_value:
                    if not input_value.strip():
                        data[field_name] = None
                        self.stderr.write("Error: This field cannot be blank.")
                        continue
                    data[field_name] = [pk.strip() for pk in input_value.split(",")]

            if self.is_foreign_key(field):
                data[f"{field_name}_id"] = data.pop(field_name)

        instance = self.Model.objects.using('default').create(**data)

        self.stdout.write(self.style.SUCCESS(f"{self.Model.__name__} ({instance.pk}) created successfully."))
