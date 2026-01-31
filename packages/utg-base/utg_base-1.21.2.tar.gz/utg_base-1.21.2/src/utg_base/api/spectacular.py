from django.conf import settings
from django.http import HttpResponseForbidden
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.views import APIView

from utg_base.env import env


class DebugTokenRequiredMixin(APIView):
    """
    If Request header X-Debug-Token not found then 403
    """

    def dispatch(self, request, *args, **kwargs):
        token = request.headers.get("X-Debug-Token")
        if not settings.DEBUG and token != env("DJANGO_SECRET_KEY"):
            return HttpResponseForbidden("Forbidden")
        return super().dispatch(request, *args, **kwargs)


class ProtectedSpectacularAPIView(DebugTokenRequiredMixin, SpectacularAPIView):
    pass


class ProtectedSpectacularSwaggerView(DebugTokenRequiredMixin, SpectacularSwaggerView):
    pass


urlpatterns = [
    path('api/swagger/schema/', ProtectedSpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', ProtectedSpectacularSwaggerView.as_view(url_name='schema'), name='docs'),
]
