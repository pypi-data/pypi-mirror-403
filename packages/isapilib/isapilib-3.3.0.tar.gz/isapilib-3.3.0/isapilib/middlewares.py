import io
import sys
import time
import traceback

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from isapilib.auth.permissions import IsapilibPermission
from isapilib.core.get_functions import get_insert_log_function, get_safe_method_function
from isapilib.logging import logger

insert_log = get_insert_log_function()
safe_method = get_safe_method_function()


class LoggerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.get_exception_response = safe_method(self.launch_exception)

        self.interfaz = getattr(settings, 'INTERFAZ_NAME', '')

        self.authentication_classes = api_settings.DEFAULT_AUTHENTICATION_CLASSES
        self.authenticators = [auth() for auth in self.authentication_classes]

    @staticmethod
    def launch_exception(exception):
        raise exception

    @staticmethod
    def get_log_type(view_func) -> str:
        view_class = getattr(view_func, 'view_class', None)
        name = view_class.__name__ if view_class else view_func.__name__

        for suffix in ['View', 'ViewSet']:
            if name.endswith(suffix):
                name = name[:-len(suffix)]

        return name

    def process_view(self, base_request, view_func, view_args, view_kwargs):
        base_request.user = getattr(base_request, 'user', AnonymousUser())
        base_request.log_type = self.get_log_type(view_func)

        view_class = getattr(view_func, 'view_class', getattr(view_func, 'cls', None))
        permission_classes: tuple = getattr(view_class, 'permission_classes', ())
        base_request.is_drf = view_class is not None and issubclass(view_class, APIView)
        base_request.log_transaction = IsapilibPermission in permission_classes

    def process_exception(self, _, exception):
        tb = traceback.format_exc().strip().replace("\n", " | ")
        logger.error("Exception detected exception=%s: %s traceback=%s", type(exception).__name__, str(exception), tb)

        response = self.get_exception_response(exception)

        if not isinstance(response, Response):
            return response

        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = "application/json"
        response.renderer_context = {}

        response.render()
        return HttpResponse(
            content=response.content,
            status=response.status_code,
            content_type=response.content_type,
        )

    def __call__(self, base_request):
        IsapilibPermission.reset_current_request()

        start = time.time()
        response = self.get_response(base_request)
        end = time.time()

        is_drf = getattr(base_request, 'is_drf', False)
        request = IsapilibPermission.get_current_request(raise_exception=False)

        if not is_drf or request is None or not base_request.log_transaction:
            return response

        user = request.user

        if user.is_authenticated:
            log_type = f'{request.log_type} {request.method}'
            response_time = (end - start) * 1000

            logger.debug('Logged %s %s %sms', self.interfaz, log_type, response_time)

            insert_log(
                request=request,
                response=response,
                interfaz=self.interfaz,
                tipo=log_type,
                time=response_time,
            )

        return response


class ChunkedMiddleware:
    def __init__(self, get_response):
        development = any(arg for arg in sys.argv if "manage.py" in arg)
        support = any(s in arg for arg in sys.argv for s in ("uvicorn", "hypercorn", "daphne"))

        if not support and not development:
            raise Exception('Chunked request not supported. Use a server that handles Transfer-Encoding.')

        self.get_response = get_response

    def __call__(self, request):
        has_transfer_encoding = 'Transfer-Encoding' in request.headers
        transfer_encoding = request.headers.get('Transfer-Encoding')

        if has_transfer_encoding and transfer_encoding == 'chunked':
            logger.info('Chunked request received chunked transfer encoding')

            content_length = request.META.get('CONTENT_LENGTH')
            if content_length in (None, '0'):
                content_length = str(len(request.body))
                request.META['CONTENT_LENGTH'] = content_length
                request._stream = io.BytesIO(request.body)
                logger.debug('Transformed chunked request to standard encoding, set CONTENT_LENGTH=%s', content_length)

        response = self.get_response(request)
        return response
