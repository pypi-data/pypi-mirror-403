from django.conf import settings

from isapilib.api.models import BranchAPI
from isapilib.auth.permissions import IsapilibPermission
from isapilib.core.exceptions import RequestError
from isapilib.core.utilities import is_test, get_dealer_field
from isapilib.external.connection import add_conn
from isapilib.logging import logger


class BaseRouter:
    default_database = (
        'ConnectionAPI'.lower(),
        'BranchAPI'.lower(),
        'UserAPI'.lower(),
        'PermissionAPI'.lower(),
        'ApiLogs'.lower(),
        'idtoken',
        'accesstoken',
        'refreshtoken',
        'application',
    )

    def get_branch(self, user, request) -> BranchAPI:
        if request.user.branch is None:
            raise RequestError(f"User don't have a default branch ({request.user})")
        return request.user.branch

    def external_db(self, request):
        if name := getattr(request, '_isapi_external_db', None):
            return name

        branch = self.get_branch(request.user, request)
        logger.debug('External database, request %s user %s, branch %s', id(request), request.user.pk, branch.pk)
        name = add_conn(request.user, branch)
        setattr(request, '_isapi_external_db', name)
        return name

    def _get_model_name(self, model):
        try:
            return model._meta.model_name
        except Exception:
            return 'execution'

    def db_for_read(self, model, **hints):
        model_name = self._get_model_name(model)
        if model_name in self.default_database:
            return 'default'

        request = IsapilibPermission.get_current_request()
        alias = self.external_db(request)

        logger.info('Database for read, model %s, alias %s, request %s', model_name, alias, id(request))
        return alias

    def db_for_write(self, model, **hints):
        model_name = self._get_model_name(model)
        if model_name in self.default_database:
            return 'default'

        request = IsapilibPermission.get_current_request()
        alias = self.external_db(request)

        logger.info("Database for write, model %s, alias %s, request %s", model_name, alias, id(request))
        return alias

    def allow_relation(self, *args, **kwargs):
        return True


def get_branch(dealer_id: str, src='header') -> BranchAPI:
    field = get_dealer_field()
    if dealer_id is None: raise RequestError(f'{field} {src} is required')
    branch = BranchAPI.objects.exclude(gwmbac='').filter(gwmbac=dealer_id, gwmbac__isnull=False).first()
    if branch is None: raise RequestError(f'El DealerID ({dealer_id}) no existe')
    return branch


class DealerRouter(BaseRouter):
    field = get_dealer_field()

    def get_branch(self, user, request) -> BranchAPI:
        if is_test():
            dealer_id = getattr(settings, self.field)
        else:
            dealer_id = request.headers.get(self.field)
        return get_branch(dealer_id)


class DealerBodyRouter(BaseRouter):
    field = get_dealer_field()

    def get_branch(self, user, request) -> BranchAPI:
        if is_test():
            dealer_id = getattr(settings, self.field)
        else:
            dealer_id = request.data.get(self.field)
        return get_branch(dealer_id, src='body')
