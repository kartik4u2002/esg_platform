"""Admin configuration for the ingestion app."""
from django.contrib import admin

from apps.ingestion.models import DataSource, ImportBatch, RawRecord


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    """Admin interface for DataSource model."""

    list_display = ['name', 'source_type', 'scope_category', 'organization', 'is_active']
    list_filter = ['source_type', 'scope_category', 'is_active']
    search_fields = ['name']
    readonly_fields = ['id']


@admin.register(ImportBatch)
class ImportBatchAdmin(admin.ModelAdmin):
    """Admin interface for ImportBatch model."""

    list_display = [
        'id', 'source', 'status', 'ingested_by',
        'ingested_at', 'total_rows', 'processed_rows',
    ]
    list_filter = ['status', 'source__source_type']
    search_fields = ['file_name']
    readonly_fields = ['id', 'ingested_at']
    raw_id_fields = ['source', 'ingested_by', 'organization']


@admin.register(RawRecord)
class RawRecordAdmin(admin.ModelAdmin):
    """Admin interface for RawRecord model."""

    list_display = [
        'id', 'batch', 'source_row_number',
        'pipeline_status', 'checksum', 'created_at',
    ]
    list_filter = ['pipeline_status']
    search_fields = ['checksum']
    readonly_fields = ['id', 'checksum', 'created_at']
    raw_id_fields = ['batch', 'organization']
