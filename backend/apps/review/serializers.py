"""Review app serializers."""
from rest_framework import serializers

from apps.pipeline.models import NormalizedRecord, ValidationFlag
from apps.review.models import ReviewDecision


class ValidationFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValidationFlag
        fields = [
            'id', 'flag_type', 'severity', 'message',
            'field_name', 'created_at',
        ]


class ReviewQueueSerializer(serializers.ModelSerializer):
    """Serializer for the review queue list view."""

    flags = ValidationFlagSerializer(many=True, read_only=True)
    error_count = serializers.SerializerMethodField()
    warning_count = serializers.SerializerMethodField()
    info_count = serializers.SerializerMethodField()
    raw_payload = serializers.SerializerMethodField()
    batch_id = serializers.SerializerMethodField()
    scope_category = serializers.SerializerMethodField()

    class Meta:
        model = NormalizedRecord
        fields = [
            'id', 'source_type', 'emission_scope', 'scope_category',
            'facility_or_entity', 'quantity_normalized', 'unit_normalized',
            'period_start', 'period_end', 'review_status', 'is_locked',
            'created_at', 'updated_at',
            'error_count', 'warning_count', 'info_count',
            'flags', 'raw_payload', 'batch_id',
        ]

    def get_error_count(self, obj):
        return obj.flags.filter(severity='error').count()

    def get_warning_count(self, obj):
        return obj.flags.filter(severity='warning').count()

    def get_info_count(self, obj):
        return obj.flags.filter(severity='info').count()

    def get_raw_payload(self, obj):
        if hasattr(obj, 'raw_record') and obj.raw_record:
            return obj.raw_record.raw_payload
        return {}

    def get_batch_id(self, obj):
        if hasattr(obj, 'raw_record') and obj.raw_record:
            return str(obj.raw_record.batch_id)
        return None

    def get_scope_category(self, obj):
        if hasattr(obj, 'raw_record') and obj.raw_record:
            return obj.raw_record.batch.source.scope_category
        return obj.emission_scope


class ReviewRecordDetailSerializer(serializers.ModelSerializer):
    """Full detail serializer for a single record under review."""

    flags = ValidationFlagSerializer(many=True, read_only=True)
    raw_payload = serializers.SerializerMethodField()
    normalization_log = serializers.JSONField(read_only=True)
    error_count = serializers.SerializerMethodField()
    warning_count = serializers.SerializerMethodField()
    info_count = serializers.SerializerMethodField()
    decision = serializers.SerializerMethodField()
    batch_id = serializers.SerializerMethodField()
    source_name = serializers.SerializerMethodField()

    class Meta:
        model = NormalizedRecord
        fields = [
            'id', 'source_type', 'emission_scope',
            'facility_or_entity', 'quantity_normalized', 'unit_normalized',
            'period_start', 'period_end', 'review_status', 'is_locked',
            'normalization_log', 'created_at', 'updated_at',
            'error_count', 'warning_count', 'info_count',
            'flags', 'raw_payload', 'decision', 'batch_id', 'source_name',
        ]

    def get_error_count(self, obj):
        return obj.flags.filter(severity='error').count()

    def get_warning_count(self, obj):
        return obj.flags.filter(severity='warning').count()

    def get_info_count(self, obj):
        return obj.flags.filter(severity='info').count()

    def get_raw_payload(self, obj):
        if hasattr(obj, 'raw_record') and obj.raw_record:
            return obj.raw_record.raw_payload
        return {}

    def get_decision(self, obj):
        try:
            decision = obj.decision
            return {
                'decision': decision.decision,
                'notes': decision.notes,
                'rejection_reason': decision.rejection_reason,
                'analyst': str(decision.analyst),
                'decided_at': decision.decided_at.isoformat(),
            }
        except ReviewDecision.DoesNotExist:
            return None

    def get_batch_id(self, obj):
        if hasattr(obj, 'raw_record') and obj.raw_record:
            return str(obj.raw_record.batch_id)
        return None

    def get_source_name(self, obj):
        if hasattr(obj, 'raw_record') and obj.raw_record:
            return obj.raw_record.batch.source.name
        return ''


class ApproveRequestSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True, default='')


class RejectRequestSerializer(serializers.Serializer):
    rejection_reason = serializers.CharField(required=True, max_length=100)
    notes = serializers.CharField(required=False, allow_blank=True, default='')


class ReviewDecisionSerializer(serializers.ModelSerializer):
    analyst_name = serializers.SerializerMethodField()

    class Meta:
        model = ReviewDecision
        fields = [
            'id', 'decision', 'notes', 'rejection_reason',
            'analyst', 'analyst_name', 'decided_at',
        ]

    def get_analyst_name(self, obj):
        return str(obj.analyst) if obj.analyst else ''
