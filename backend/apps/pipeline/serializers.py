"""
Serializers for the pipeline app.

Provides serialization for NormalizedRecord and ValidationFlag models,
including computed fields for error and warning counts.
"""
from rest_framework import serializers

from apps.pipeline.models import NormalizedRecord, ValidationFlag


class ValidationFlagSerializer(serializers.ModelSerializer):
    """Serializer for the ValidationFlag model."""

    class Meta:
        model = ValidationFlag
        fields = [
            'id', 'normalized_record', 'flag_type', 'severity',
            'message', 'field_name', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class NormalizedRecordSerializer(serializers.ModelSerializer):
    """
    Serializer for NormalizedRecord with nested ValidationFlags
    and computed error/warning counts.
    """

    flags = ValidationFlagSerializer(many=True, read_only=True)
    error_count = serializers.SerializerMethodField()
    warning_count = serializers.SerializerMethodField()
    raw_payload = serializers.SerializerMethodField()
    pipeline_status = serializers.SerializerMethodField()

    class Meta:
        model = NormalizedRecord
        fields = [
            'id', 'raw_record', 'organization',
            'quantity_normalized', 'unit_normalized',
            'emission_scope', 'source_type',
            'period_start', 'period_end',
            'facility_or_entity', 'normalization_log',
            'review_status', 'is_locked',
            'created_at', 'updated_at',
            'flags', 'error_count', 'warning_count',
            'raw_payload', 'pipeline_status',
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'error_count', 'warning_count',
        ]

    def get_error_count(self, obj: NormalizedRecord) -> int:
        """Return the count of error-severity flags."""
        if hasattr(obj, '_prefetched_objects_cache') and 'flags' in obj._prefetched_objects_cache:
            return sum(1 for f in obj.flags.all() if f.severity == 'error')
        return obj.flags.filter(severity='error').count()

    def get_warning_count(self, obj: NormalizedRecord) -> int:
        """Return the count of warning-severity flags."""
        if hasattr(obj, '_prefetched_objects_cache') and 'flags' in obj._prefetched_objects_cache:
            return sum(1 for f in obj.flags.all() if f.severity == 'warning')
        return obj.flags.filter(severity='warning').count()

    def get_raw_payload(self, obj: NormalizedRecord) -> dict:
        """Return the original raw_payload from the RawRecord."""
        try:
            return obj.raw_record.raw_payload
        except Exception:
            return {}

    def get_pipeline_status(self, obj: NormalizedRecord) -> str:
        """Return the current pipeline_status from the RawRecord."""
        try:
            return obj.raw_record.pipeline_status
        except Exception:
            return ''
