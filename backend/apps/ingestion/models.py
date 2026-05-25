"""
Ingestion app models.

Defines DataSource, ImportBatch, and RawRecord — the core data ingestion layer.
Raw records are written once and never mutated (immutable raw_payload).
"""
import uuid

from django.conf import settings
from django.db import models

from common.querysets import TenantManager


class DataSource(models.Model):
    """A configured data source for ESG data ingestion."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'tenancy.Organization',
        on_delete=models.CASCADE,
        related_name='data_sources',
    )
    SOURCE_TYPES = [
        ('sap_procurement', 'SAP Procurement'),
        ('utility_electricity', 'Utility Electricity'),
        ('corporate_travel', 'Corporate Travel'),
    ]
    source_type = models.CharField(max_length=50, choices=SOURCE_TYPES)
    SCOPE_CHOICES = [
        ('scope1', 'Scope 1'),
        ('scope2', 'Scope 2'),
        ('scope3', 'Scope 3'),
    ]
    scope_category = models.CharField(max_length=10, choices=SCOPE_CHOICES)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    objects = TenantManager()

    class Meta:
        app_label = 'ingestion'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.source_type})'


class ImportBatch(models.Model):
    """A batch of imported records from a specific data source."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'tenancy.Organization',
        on_delete=models.CASCADE,
        related_name='import_batches',
    )
    source = models.ForeignKey(
        DataSource,
        on_delete=models.PROTECT,
        related_name='batches',
    )
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    ingested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='import_batches',
    )
    ingested_at = models.DateTimeField(auto_now_add=True)
    total_rows = models.IntegerField(default=0)
    processed_rows = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, default='')
    file_name = models.CharField(max_length=255, blank=True, default='')

    objects = TenantManager()

    class Meta:
        app_label = 'ingestion'
        ordering = ['-ingested_at']

    def __str__(self):
        return f'Batch {self.id} ({self.status})'


class RawRecord(models.Model):
    """
    An immutable raw record ingested from a data source.

    The raw_payload field contains the original row data and is NEVER mutated
    after creation. This ensures full audit traceability.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(
        ImportBatch,
        on_delete=models.CASCADE,
        related_name='raw_records',
    )
    organization = models.ForeignKey(
        'tenancy.Organization',
        on_delete=models.CASCADE,
        related_name='raw_records',
    )
    raw_payload = models.JSONField()  # original row, never mutated
    checksum = models.CharField(max_length=64, db_index=True)
    source_row_number = models.IntegerField()
    PIPELINE_STATUS = [
        ('ingested', 'Ingested'),
        ('validating', 'Validating'),
        ('validation_failed', 'Validation Failed'),
        ('normalizing', 'Normalizing'),
        ('anomaly_detection', 'Anomaly Detection'),
        ('review_pending', 'Review Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    pipeline_status = models.CharField(
        max_length=30, choices=PIPELINE_STATUS, default='ingested'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantManager()

    class Meta:
        app_label = 'ingestion'
        unique_together = [('batch', 'checksum')]  # duplicate detection within batch

    def __str__(self):
        return f'RawRecord {self.id} ({self.pipeline_status})'
