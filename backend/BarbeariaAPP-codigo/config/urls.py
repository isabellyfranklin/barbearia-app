from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from .health import HealthView
from .openapi import annotate_views

annotate_views()

api_patterns = [
    path("", include("accounts.urls")),
    path("", include("catalog.urls")),
    path("", include("scheduling.urls")),
]
urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/health", HealthView.as_view(), name="health"),
    path("api/v1/schema", SpectacularAPIView.as_view(), name="api-schema"),
    path("api/v1/docs", SpectacularSwaggerView.as_view(url_name="api-schema"), name="api-docs"),
    path("api/v1/", include(api_patterns)),
    # Compatibilidade transitória com o Django preliminar; não são rotas FastAPI.
    path("api/", include(api_patterns)),
]
