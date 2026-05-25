"""Audit app serializers."""
from rest_framework import serializers

from apps.audit.models import AuditEvent, AuditLock
from apps.pipeline.models import NormalizedRecord


class AuditEventSerializer(serializers.ModelSerializer):
    """Serializer for individual audit trail events."""

    actor_name = serializers.SerializerMethodField()
    occurred_at_display = serializers.SerializerMethodField()

    class Meta:
        model = AuditEvent
        fields = [
            'id', 'entity_type', 'entity_id', 'action',
            'before_state', 'after_state',
            'actor', 'actor_name', 'occurred_at', 'occurred_at_display',
            'ip_address',
        ]

    def get_actor_name(self, obj):
        if obj.actor:
            return obj.actor.email or obj.actor.username
        return 'System'

    def get_occurred_at_display(self, obj):
        return obj.occurred_at.strftime('%Y-%m-%d %H:%M:%S UTC')


class AuditLockSerializer(serializers.ModelSerializer):
    """Serializer for audit lock records."""

    locked_by_name = serializers.SerializerMethodField()

    class Meta:
        model = AuditLock
        fields = [
            'id', 'normalized_record', 'locked_by', 'locked_by_name',
            'locked_at', 'content_hash',
        ]

    def get_locked_by_name(self, obj):
        if obj.locked_by:
            return obj.locked_by.email or obj.locked_by.username
        return ''


class LockedRecordSerializer(serializers.ModelSerializer):
    """Serializer for locked NormalizedRecords in the audit view."""

    lock = AuditLockSerializer(read_only=True)
    source_name = serializers.SerializerMethodField()
    raw_payload = serializers.SerializerMethodField()
    error_count = serializers.SerializerMethodField()
    warning_count = serializers.SerializerMethodField()

    class Meta:
        model = NormalizedRecord
        fields = [
            'id', 'source_type', 'emission_scope',
            'facility_or_entity', 'quantity_normalized', 'unit_normalized',
            'period_start', 'period_end', 'review_status', 'is_locked',
            'created_at', 'updated_at',
            'lock', 'source_name', 'raw_payload',
            'error_count', 'warning_count',
        ]

    def get_source_name(self, obj):
        try:
            return obj.raw_record.batch.source.name
        except Exception:
            return ''

    def get_raw_payload(self, obj):
        try:
            return obj.raw_record.raw_payload
        except Exception:
            return {}

    def get_error_count(self, obj):
        return obj.flags.filter(severity='error').count()

    def get_warning_count(self, obj):
        return obj.flags.filter(severity='warning').count()
