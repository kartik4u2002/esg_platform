"""Audit app admin."""
from django.contrib import admin

from apps.audit.models import AuditEvent, AuditLock


@admin.register(AuditLock)
class AuditLockAdmin(admin.ModelAdmin):
    list_display = ['id', 'normalized_record', 'locked_by', 'locked_at']
    list_filter = ['locked_at']
    readonly_fields = ['id', 'locked_at', 'content_hash']
    raw_id_fields = ['normalized_record', 'locked_by']


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ['id', 'action', 'entity_type', 'entity_id', 'actor', 'occurred_at']
    list_filter = ['action', 'entity_type', 'occurred_at']
    readonly_fields = [
        'id', 'organization', 'actor', 'entity_type', 'entity_id',
        'action', 'before_state', 'after_state', 'occurred_at', 'ip_address',
    ]
    search_fields = ['action', 'entity_type']

    def has_change_permission(self, request, obj=None):
        return False  # Audit events are immutable

    def has_delete_permission(self, request, obj=None):
        return False  # Audit events are immutable
