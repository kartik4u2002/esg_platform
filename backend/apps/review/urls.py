"""Review app URL configuration."""
from django.urls import path

from apps.review import views

app_name = 'review'

urlpatterns = [
    path('queue/', views.ReviewQueueView.as_view(), name='review-queue'),
    path('records/<uuid:id>/', views.ReviewRecordDetailView.as_view(), name='review-detail'),
    path('records/<uuid:id>/approve/', views.ApproveRecordView.as_view(), name='review-approve'),
    path('records/<uuid:id>/reject/', views.RejectRecordView.as_view(), name='review-reject'),
]
