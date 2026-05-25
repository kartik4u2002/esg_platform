"""Audit app URL configuration."""
from django.urls import path

from apps.audit import views

app_name = 'audit'

urlpatterns = [
    path('records/', views.AuditRecordListView.as_view(), name='audit-records'),
    path('records/<uuid:id>/trail/', views.AuditTrailView.as_view(), name='audit-trail'),
    path('export/', views.AuditExportView.as_view(), name='audit-export'),
]
