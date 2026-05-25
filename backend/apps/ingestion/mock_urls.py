"""URL configuration for mock ingestion endpoints."""
from django.urls import path

from apps.ingestion.mock_views import MockTravelFeedView

app_name = 'mock_ingestion'

urlpatterns = [
    path('travel-feed/', MockTravelFeedView.as_view(), name='travel-feed'),
]
