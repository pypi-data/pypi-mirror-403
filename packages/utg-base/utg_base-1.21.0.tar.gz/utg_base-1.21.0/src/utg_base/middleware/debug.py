from django.utils.deprecation import MiddlewareMixin

from utg_base.env import env


class DebugOverrideMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        if request.headers.get("X-Debug-Token") == env("DJANGO_SECRET_KEY"):
            from django.views import debug
            return debug.technical_500_response(request, type(exception), exception, exception.__traceback__)
