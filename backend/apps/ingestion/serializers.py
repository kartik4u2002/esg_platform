"""
Serializers for the ingestion app.

Provides serialization for DataSource, ImportBatch, and RawRecord models.
"""
from rest_framework import serializers

from apps.ingestion.models import DataSource, ImportBatch, RawRecord


class DataSourceSerializer(serializers.ModelSerializer):
    """Serializer for the DataSource model."""

    class Meta:
        model = DataSource
        fields = [
            'id', 'organization', 'source_type', 'scope_category',
            'name', 'is_active',
        ]
        read_only_fields = ['id', 'organization']

    def create(self, validated_data: dict) -> DataSource:
        """Create a DataSource, automatically setting the organization from the request."""
        request = self.context.get('request')
        if request and hasattr(request.user, 'organization'):
            validated_data['organization'] = request.user.organization
        return super().create(validated_data)


class ImportBatchSerializer(serializers.ModelSerializer):
    """
    Serializer for ImportBatch with additional computed fields:
    source_name and ingested_by_name for display convenience.
    """

    source_name = serializers.SerializerMethodField()
    ingested_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ImportBatch
        fields = [
            'id', 'organization', 'source', 'source_name', 'status',
            'ingested_by', 'ingested_by_name', 'ingested_at',
            'total_rows', 'processed_rows', 'error_message', 'file_name',
        ]
        read_only_fields = [
            'id', 'organization', 'source_name', 'ingested_by_name',
            'ingested_at', 'processed_rows',
        ]

    def get_source_name(self, obj: ImportBatch) -> str:
        """Return the human-readable name of the associated DataSource."""
        return obj.source.name if obj.source else ''

    def get_ingested_by_name(self, obj: ImportBatch) -> str:
        """Return the display name or email of the user who triggered the import."""
        if obj.ingested_by:
            full_name = obj.ingested_by.get_full_name()
            return full_name if full_name else obj.ingested_by.email
        return ''


class RawRecordSerializer(serializers.ModelSerializer):
    """Serializer for the RawRecord model."""

    class Meta:
        model = RawRecord
        fields = [
            'id', 'batch', 'organization', 'raw_payload', 'checksum',
            'source_row_number', 'pipeline_status', 'created_at',
        ]
        read_only_fields = [
            'id', 'organization', 'checksum', 'created_at',
        ]
