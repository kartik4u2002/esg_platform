"""
URL configuration for ESG Platform.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    # API v1 endpoints
    path('api/v1/auth/', include('apps.tenancy.urls')),
    path('api/v1/ingestion/', include('apps.ingestion.urls')),
    path('api/v1/review/', include('apps.review.urls')),
    path('api/v1/audit/', include('apps.audit.urls')),
    # Mock endpoints
    path('api/mock/', include('apps.ingestion.mock_urls')),
    # OpenAPI schema & docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
