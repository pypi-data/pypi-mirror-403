import threading

from rest_framework.permissions import BasePermission

from isapilib.core.exceptions import IsapiException
from isapilib.logging import logger

_thread_local = threading.local()


class IsapilibPermission(BasePermission):
    def has_permission(self, request, view):
        self.set_current_request(request)
        return True

    @staticmethod
    def get_current_request(raise_exception=True):
        request = getattr(_thread_local, 'request', None)
        if request is None and raise_exception:
            raise IsapiException(
                'Request is not available in thread-local context. '
                'Make sure IsapilibPermission is set either in DEFAULT_PERMISSION_CLASSES '
                'or included in the view\'s permission_classes.'
            )
        return request

    @staticmethod
    def set_current_request(request):
        logger.debug('Current request set in thread-local storage %s', id(request))
        _thread_local.request = request

    @staticmethod
    def reset_current_request():
        logger.debug('Thread-local request cleared')
        _thread_local.request = None
