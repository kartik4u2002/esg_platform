"""URL configuration for the ingestion app."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.ingestion.views import (
    DataSourceViewSet,
    ImportBatchViewSet,
    SAPUploadView,
    TravelTriggerView,
    UtilityUploadView,
)

router = DefaultRouter()
router.register(r'sources', DataSourceViewSet, basename='datasource')
router.register(r'batches', ImportBatchViewSet, basename='importbatch')

app_name = 'ingestion'

urlpatterns = [
    path('', include(router.urls)),
    path('upload/sap/', SAPUploadView.as_view(), name='upload-sap'),
    path('upload/utility/', UtilityUploadView.as_view(), name='upload-utility'),
    path('travel/trigger/', TravelTriggerView.as_view(), name='travel-trigger'),
]
