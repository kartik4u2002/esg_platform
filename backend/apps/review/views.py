"""
Review app views.

Provides the review queue, record detail, and atomic approve/reject endpoints.
Approved/locked records return 403 on any write attempt.
"""
from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import AuditLock
from apps.audit.services import compute_lock_hash, log_event
from apps.pipeline.models import NormalizedRecord
from apps.review.models import ReviewDecision
from apps.review.serializers import (
    ApproveRequestSerializer,
    RejectRequestSerializer,
    ReviewQueueSerializer,
    ReviewRecordDetailSerializer,
)
from common.exceptions import LockedRecordError
from common.pagination import StandardResultsPagination


class ReviewQueueView(generics.ListAPIView):
    """
    GET /api/v1/review/queue/

    Filterable list of NormalizedRecords pending review, scoped to the
    requesting user's organization.
    """

    serializer_class = ReviewQueueSerializer
    pagination_class = StandardResultsPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = NormalizedRecord.objects.for_tenant(
            self.request.user.organization
        ).select_related(
            'raw_record__batch__source'
        ).prefetch_related('flags')

        # Filter by review status (default: pending)
        review_status = self.request.query_params.get('review_status', 'pending')
        if review_status != 'all':
            qs = qs.filter(review_status=review_status)

        # Filter by source type
        source_type = self.request.query_params.get('source_type')
        if source_type:
            qs = qs.filter(source_type=source_type)

        # Filter by batch
        batch_id = self.request.query_params.get('batch')
        if batch_id:
            qs = qs.filter(raw_record__batch_id=batch_id)

        # Filter by severity (has errors, has warnings)
        severity = self.request.query_params.get('severity')
        if severity == 'error':
            qs = qs.filter(flags__severity='error').distinct()
        elif severity == 'warning':
            qs = qs.filter(flags__severity__in=['error', 'warning']).distinct()

        # Date range filter
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)

        return qs.order_by('-created_at')


class ReviewRecordDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/review/records/{id}/

    Full detail view of a normalized record including raw payload,
    normalized fields, and all validation flags.
    """

    serializer_class = ReviewRecordDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return NormalizedRecord.objects.for_tenant(
            self.request.user.organization
        ).select_related(
            'raw_record__batch__source'
        ).prefetch_related('flags')


class ApproveRecordView(APIView):
    """
    POST /api/v1/review/records/{id}/approve/

    Atomically approve a record:
    1. Create ReviewDecision
    2. Set NormalizedRecord.review_status = "approved", is_locked = True
    3. Create AuditLock with SHA-256 hash
    4. Write AuditEvent action="RECORD_APPROVED"
    5. Update RawRecord.pipeline_status = "approved"

    Returns 403 if the record is already locked.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=ApproveRequestSerializer,
        responses={200: ReviewRecordDetailSerializer},
    )
    def post(self, request, id):
        try:
            record = NormalizedRecord.objects.for_tenant(
                request.user.organization
            ).select_related('raw_record').get(id=id)
        except NormalizedRecord.DoesNotExist:
            return Response(
                {'detail': 'Record not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if record.is_locked:
            raise LockedRecordError()

        serializer = ApproveRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notes = serializer.validated_data.get('notes', '')

        before_state = {
            'review_status': record.review_status,
            'is_locked': record.is_locked,
            'pipeline_status': record.raw_record.pipeline_status,
        }

        with transaction.atomic():
            # 1. Create ReviewDecision
            ReviewDecision.objects.create(
                normalized_record=record,
                analyst=request.user,
                decision='approved',
                notes=notes,
            )

            # 2. Update NormalizedRecord
            record.review_status = 'approved'
            record.is_locked = True
            record.save(update_fields=['review_status', 'is_locked', 'updated_at'])

            # 3. Create AuditLock
            content_hash = compute_lock_hash(record)
            AuditLock.objects.create(
                normalized_record=record,
                locked_by=request.user,
                content_hash=content_hash,
            )

            # 4. Write AuditEvent
            after_state = {
                'review_status': 'approved',
                'is_locked': True,
                'pipeline_status': 'approved',
                'notes': notes,
            }
            log_event(
                actor=request.user,
                entity=record,
                action='RECORD_APPROVED',
                before=before_state,
                after=after_state,
                request=request,
            )

            # 5. Update RawRecord
            record.raw_record.pipeline_status = 'approved'
            record.raw_record.save(update_fields=['pipeline_status'])

        # Refresh and serialize
        record.refresh_from_db()
        detail_serializer = ReviewRecordDetailSerializer(record)
        return Response(detail_serializer.data, status=status.HTTP_200_OK)


class RejectRecordView(APIView):
    """
    POST /api/v1/review/records/{id}/reject/

    Atomically reject a record:
    1. Create ReviewDecision
    2. Set NormalizedRecord.review_status = "rejected"
    3. Write AuditEvent action="RECORD_REJECTED"
    4. Update RawRecord.pipeline_status = "rejected"

    Returns 403 if the record is already locked.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=RejectRequestSerializer,
        responses={200: ReviewRecordDetailSerializer},
    )
    def post(self, request, id):
        try:
            record = NormalizedRecord.objects.for_tenant(
                request.user.organization
            ).select_related('raw_record').get(id=id)
        except NormalizedRecord.DoesNotExist:
            return Response(
                {'detail': 'Record not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if record.is_locked:
            raise LockedRecordError()

        serializer = RejectRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notes = serializer.validated_data.get('notes', '')
        rejection_reason = serializer.validated_data['rejection_reason']

        before_state = {
            'review_status': record.review_status,
            'pipeline_status': record.raw_record.pipeline_status,
        }

        with transaction.atomic():
            # 1. Create ReviewDecision
            ReviewDecision.objects.create(
                normalized_record=record,
                analyst=request.user,
                decision='rejected',
                notes=notes,
                rejection_reason=rejection_reason,
            )

            # 2. Update NormalizedRecord
            record.review_status = 'rejected'
            record.save(update_fields=['review_status', 'updated_at'])

            # 3. Write AuditEvent
            after_state = {
                'review_status': 'rejected',
                'pipeline_status': 'rejected',
                'notes': notes,
                'rejection_reason': rejection_reason,
            }
            log_event(
                actor=request.user,
                entity=record,
                action='RECORD_REJECTED',
                before=before_state,
                after=after_state,
                request=request,
            )

            # 4. Update RawRecord
            record.raw_record.pipeline_status = 'rejected'
            record.raw_record.save(update_fields=['pipeline_status'])

        record.refresh_from_db()
        detail_serializer = ReviewRecordDetailSerializer(record)
        return Response(detail_serializer.data, status=status.HTTP_200_OK)
