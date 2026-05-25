"""
Audit app models.

AuditLock stores SHA-256 hashes of approved records for tamper detection.
AuditEvent is an append-only log of every state transition in the system.
"""
import uuid

from django.conf import settings
from django.db import models

from common.querysets import TenantManager


class AuditLock(models.Model):
    """
    Immutable lock record created when a NormalizedRecord is approved.

    Stores a SHA-256 hash of the record's state at lock time to enable
    tamper detection via hash verification.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    normalized_record = models.OneToOneField(
        'pipeline.NormalizedRecord',
        on_delete=models.CASCADE,
        related_name='lock',
    )
    locked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='audit_locks',
    )
    locked_at = models.DateTimeField(auto_now_add=True)
    content_hash = models.CharField(max_length=64)  # SHA-256 of record state

    class Meta:
        app_label = 'audit'

    def __str__(self):
        return f'Lock {self.id} for record {self.normalized_record_id}'


class AuditEvent(models.Model):
    """
    Append-only audit event log.

    Every state transition in the system writes an AuditEvent row.
    DB-level rules prevent UPDATE and DELETE operations on this table.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'tenancy.Organization',
        on_delete=models.CASCADE,
        related_name='audit_events',
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='audit_events',
    )
    entity_type = models.CharField(max_length=50)
    entity_id = models.UUIDField()
    action = models.CharField(max_length=50)
    before_state = models.JSONField(default=dict)
    after_state = models.JSONField(default=dict)
    occurred_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    objects = TenantManager()

    class Meta:
        app_label = 'audit'
        ordering = ['-occurred_at']
        indexes = [
            models.Index(fields=['entity_type', 'entity_id']),
        ]

    def __str__(self):
        return f'{self.action} on {self.entity_type}({self.entity_id})'
