"""
Pipeline app models.

Defines NormalizedRecord (the cleaned, normalized version of a RawRecord)
and ValidationFlag (individual validation issues found during pipeline processing).
"""
import uuid

from django.db import models

from common.querysets import TenantManager


class NormalizedRecord(models.Model):
    """
    Cleaned and normalized version of a RawRecord.

    Created during the validation step and progressively enriched
    through normalization and anomaly detection pipeline stages.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    raw_record = models.OneToOneField(
        'ingestion.RawRecord',
        on_delete=models.CASCADE,
        related_name='normalized',
    )
    organization = models.ForeignKey(
        'tenancy.Organization',
        on_delete=models.CASCADE,
        related_name='normalized_records',
    )
    quantity_normalized = models.FloatField(null=True, blank=True)
    unit_normalized = models.CharField(max_length=50, blank=True, default='')

    SCOPE_CHOICES = [
        ('scope1', 'Scope 1'),
        ('scope2', 'Scope 2'),
        ('scope3', 'Scope 3'),
    ]
    emission_scope = models.CharField(
        max_length=10, choices=SCOPE_CHOICES, blank=True, default=''
    )
    source_type = models.CharField(max_length=50, blank=True, default='')

    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    facility_or_entity = models.CharField(max_length=255, blank=True, default='')
    normalization_log = models.JSONField(default=list)

    REVIEW_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    review_status = models.CharField(
        max_length=20, choices=REVIEW_STATUS_CHOICES, default='pending'
    )
    is_locked = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantManager()

    class Meta:
        app_label = 'pipeline'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'NormalizedRecord {self.id} ({self.review_status})'


class ValidationFlag(models.Model):
    """
    An individual validation or anomaly issue found during pipeline processing.

    Each flag is tied to a NormalizedRecord and categorized by type and severity.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    normalized_record = models.ForeignKey(
        NormalizedRecord,
        on_delete=models.CASCADE,
        related_name='flags',
    )

    FLAG_TYPE_CHOICES = [
        ('MISSING_FIELD', 'Missing Field'),
        ('INVALID_VALUE', 'Invalid Value'),
        ('NEGATIVE_VALUE', 'Negative Value'),
        ('UNSUPPORTED_UNIT', 'Unsupported Unit'),
        ('INVALID_DATE', 'Invalid Date'),
        ('DUPLICATE_INVOICE', 'Duplicate Invoice'),
        ('OVERLAPPING_PERIOD', 'Overlapping Period'),
        ('INVALID_IATA', 'Invalid IATA Code'),
        ('CONSUMPTION_SPIKE', 'Consumption Spike'),
        ('QUANTITY_OUTLIER', 'Quantity Outlier'),
        ('MISSING_DISTANCE', 'Missing Distance'),
    ]
    flag_type = models.CharField(max_length=30, choices=FLAG_TYPE_CHOICES)

    SEVERITY_CHOICES = [
        ('error', 'Error'),
        ('warning', 'Warning'),
        ('info', 'Info'),
    ]
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)

    message = models.TextField()
    field_name = models.CharField(max_length=100, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'pipeline'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.flag_type} ({self.severity}): {self.message[:60]}'
