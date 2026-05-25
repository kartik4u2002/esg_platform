"""
Review app models.

Stores analyst review decisions for normalized records.
"""
import uuid

from django.conf import settings
from django.db import models


class ReviewDecision(models.Model):
    """An analyst's approval or rejection decision for a normalized record."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    normalized_record = models.OneToOneField(
        'pipeline.NormalizedRecord',
        on_delete=models.CASCADE,
        related_name='decision',
    )
    analyst = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='review_decisions',
    )
    DECISIONS = [('approved', 'Approved'), ('rejected', 'Rejected')]
    decision = models.CharField(max_length=20, choices=DECISIONS)
    notes = models.TextField(blank=True, default='')
    rejection_reason = models.CharField(max_length=100, blank=True, default='')
    decided_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'review'
        ordering = ['-decided_at']

    def __str__(self):
        return f'Review {self.decision} for {self.normalized_record_id}'
