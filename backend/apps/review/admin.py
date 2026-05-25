"""Review app admin."""
from django.contrib import admin

from apps.review.models import ReviewDecision


@admin.register(ReviewDecision)
class ReviewDecisionAdmin(admin.ModelAdmin):
    list_display = ['id', 'decision', 'analyst', 'decided_at']
    list_filter = ['decision', 'decided_at']
    readonly_fields = ['id', 'decided_at']
    raw_id_fields = ['normalized_record', 'analyst']
