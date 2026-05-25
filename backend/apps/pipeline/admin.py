"""Admin configuration for the pipeline app."""
from django.contrib import admin

from apps.pipeline.models import NormalizedRecord, ValidationFlag


class ValidationFlagInline(admin.TabularInline):
    """Inline admin for ValidationFlags shown on the NormalizedRecord page."""

    model = ValidationFlag
    extra = 0
    readonly_fields = ['id', 'flag_type', 'severity', 'message', 'field_name', 'created_at']


@admin.register(NormalizedRecord)
class NormalizedRecordAdmin(admin.ModelAdmin):
    """Admin interface for NormalizedRecord model."""

    list_display = [
        'id', 'source_type', 'emission_scope', 'quantity_normalized',
        'unit_normalized', 'review_status', 'is_locked', 'created_at',
    ]
    list_filter = ['source_type', 'emission_scope', 'review_status', 'is_locked']
    search_fields = ['facility_or_entity']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['raw_record', 'organization']
    inlines = [ValidationFlagInline]


@admin.register(ValidationFlag)
class ValidationFlagAdmin(admin.ModelAdmin):
    """Admin interface for ValidationFlag model."""

    list_display = ['id', 'normalized_record', 'flag_type', 'severity', 'field_name', 'created_at']
    list_filter = ['flag_type', 'severity']
    search_fields = ['message', 'field_name']
    readonly_fields = ['id', 'created_at']
    raw_id_fields = ['normalized_record']
