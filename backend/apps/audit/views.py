"""
Audit app views.

Provides locked records listing, audit trail per entity, and CSV export.
All queries are scoped to the requesting user's organization.
"""
import csv

from django.http import HttpResponse
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import AuditEvent, AuditLock
from apps.audit.serializers import (
    AuditEventSerializer,
    LockedRecordSerializer,
)
from apps.pipeline.models import NormalizedRecord
from common.pagination import StandardResultsPagination


class AuditRecordListView(generics.ListAPIView):
    """
    GET /api/v1/audit/records/

    List all locked (approved) NormalizedRecords for the user's organization.
    """

    serializer_class = LockedRecordSerializer
    pagination_class = StandardResultsPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NormalizedRecord.objects.for_tenant(
            self.request.user.organization
        ).filter(
            is_locked=True
        ).select_related(
            'lock__locked_by',
            'raw_record__batch__source',
        ).prefetch_related('flags').order_by('-updated_at')


class AuditTrailView(generics.ListAPIView):
    """
    GET /api/v1/audit/records/{id}/trail/

    List all AuditEvents for a specific entity, ordered chronologically.
    """

    serializer_class = AuditEventSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # Return all events, no pagination

    def get_queryset(self):
        entity_id = self.kwargs['id']
        return AuditEvent.objects.for_tenant(
            self.request.user.organization
        ).filter(
            entity_id=entity_id,
        ).select_related('actor').order_by('-occurred_at')


class AuditExportView(APIView):
    """
    GET /api/v1/audit/export/?format=csv

    Export all locked records as CSV for the user's organization.
    """

    permission_classes = [IsAuthenticated]

    def perform_content_negotiation(self, request, force=False):
        # Bypass content negotiation to prevent DRF from raising 404 on format=csv
        from rest_framework.renderers import JSONRenderer
        return (JSONRenderer(), 'application/json')

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='format', type=str, location=OpenApiParameter.QUERY,
                description='Export format (csv)', required=False,
            ),
        ],
        responses={200: None},
    )
    def get(self, request):
        records = NormalizedRecord.objects.for_tenant(
            request.user.organization
        ).filter(
            is_locked=True
        ).select_related(
            'lock__locked_by',
            'raw_record__batch__source',
        ).order_by('-updated_at')

        export_format = request.query_params.get('format', 'csv')

        if export_format == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = (
                'attachment; filename="audit_locked_records.csv"'
            )

            writer = csv.writer(response)
            writer.writerow([
                'Record ID',
                'Source Type',
                'Emission Scope',
                'Facility/Entity',
                'Quantity (Normalized)',
                'Unit (Normalized)',
                'Period Start',
                'Period End',
                'Review Status',
                'Locked By',
                'Locked At',
                'Content Hash',
            ])

            for record in records:
                lock = getattr(record, 'lock', None)
                writer.writerow([
                    str(record.id),
                    record.source_type,
                    record.emission_scope,
                    record.facility_or_entity,
                    record.quantity_normalized,
                    record.unit_normalized,
                    record.period_start.isoformat() if record.period_start else '',
                    record.period_end.isoformat() if record.period_end else '',
                    record.review_status,
                    (lock.locked_by.email if lock and lock.locked_by else ''),
                    (lock.locked_at.isoformat() if lock else ''),
                    (lock.content_hash if lock else ''),
                ])

            return response

        return Response(
            {'detail': 'Unsupported export format. Use format=csv.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
