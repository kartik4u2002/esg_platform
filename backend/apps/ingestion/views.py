"""
Views for the ingestion app.

Provides ViewSets for DataSource and ImportBatch listing, plus upload
endpoints for SAP, Utility, and Travel data sources.
"""
from __future__ import annotations

from django.core.files.storage import default_storage
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status, viewsets
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ingestion.models import DataSource, ImportBatch
from apps.ingestion.serializers import (
    DataSourceSerializer,
    ImportBatchSerializer,
)
from common.pagination import StandardResultsPagination


class DataSourceViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for DataSource, scoped to the authenticated user's organization.
    """

    serializer_class = DataSourceSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsPagination

    def get_queryset(self):
        """Return DataSources belonging to the user's organization."""
        return DataSource.objects.for_tenant(self.request.user.organization)

    def perform_create(self, serializer):
        """Set organization from the authenticated user."""
        serializer.save(organization=self.request.user.organization)


class ImportBatchViewSet(viewsets.mixins.ListModelMixin,
                         viewsets.mixins.RetrieveModelMixin,
                         viewsets.GenericViewSet):
    """
    Read-only ViewSet for ImportBatch, scoped to the user's organization.
    """

    serializer_class = ImportBatchSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsPagination

    def get_queryset(self):
        """Return ImportBatches belonging to the user's organization."""
        return ImportBatch.objects.for_tenant(
            self.request.user.organization
        ).select_related('source', 'ingested_by')


class SAPUploadView(APIView):
    """
    Upload a SAP procurement CSV file for ingestion.

    POST /api/ingestion/upload/sap/
    Content-Type: multipart/form-data
    Body: file (CSV), source_id (UUID of the SAP DataSource)
    """

    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Upload SAP procurement CSV',
        description='Upload a CSV file exported from SAP for procurement data ingestion.',
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'file': {'type': 'string', 'format': 'binary'},
                    'source_id': {'type': 'string', 'format': 'uuid'},
                },
                'required': ['file', 'source_id'],
            },
        },
        responses={201: ImportBatchSerializer},
    )
    def post(self, request: Request) -> Response:
        """Handle SAP CSV file upload."""
        uploaded_file = request.FILES.get('file')
        source_id = request.data.get('source_id')

        if not uploaded_file:
            return Response(
                {'error': 'No file provided.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not source_id:
            return Response(
                {'error': 'source_id is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate file extension
        if not uploaded_file.name.lower().endswith('.csv'):
            return Response(
                {'error': 'Only .csv files are accepted.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify the source exists and belongs to the org
        try:
            source = DataSource.objects.for_tenant(
                request.user.organization
            ).get(id=source_id, source_type='sap_procurement')
        except DataSource.DoesNotExist:
            return Response(
                {'error': 'SAP data source not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Save file to default storage
        file_path = default_storage.save(
            f'uploads/sap/{uploaded_file.name}', uploaded_file
        )

        # Create import batch
        batch = ImportBatch.objects.create(
            organization=request.user.organization,
            source=source,
            status='pending',
            ingested_by=request.user,
            file_name=file_path,
        )

        # Dispatch Celery task
        from apps.ingestion.tasks import ingest_file
        ingest_file.delay(str(batch.id))

        serializer = ImportBatchSerializer(batch)
        return Response(
            {'batch_id': str(batch.id), 'batch': serializer.data},
            status=status.HTTP_201_CREATED,
        )


class UtilityUploadView(APIView):
    """
    Upload a utility electricity CSV file for ingestion.

    POST /api/ingestion/upload/utility/
    Content-Type: multipart/form-data
    Body: file (CSV), source_id (UUID of the Utility DataSource)
    """

    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Upload utility electricity CSV',
        description='Upload a CSV file from a utility provider for electricity data ingestion.',
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'file': {'type': 'string', 'format': 'binary'},
                    'source_id': {'type': 'string', 'format': 'uuid'},
                },
                'required': ['file', 'source_id'],
            },
        },
        responses={201: ImportBatchSerializer},
    )
    def post(self, request: Request) -> Response:
        """Handle utility CSV file upload."""
        uploaded_file = request.FILES.get('file')
        source_id = request.data.get('source_id')

        if not uploaded_file:
            return Response(
                {'error': 'No file provided.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not source_id:
            return Response(
                {'error': 'source_id is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate file extension
        if not uploaded_file.name.lower().endswith('.csv'):
            return Response(
                {'error': 'Only .csv files are accepted.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify the source exists and belongs to the org
        try:
            source = DataSource.objects.for_tenant(
                request.user.organization
            ).get(id=source_id, source_type='utility_electricity')
        except DataSource.DoesNotExist:
            return Response(
                {'error': 'Utility data source not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Save file to default storage
        file_path = default_storage.save(
            f'uploads/utility/{uploaded_file.name}', uploaded_file
        )

        # Create import batch
        batch = ImportBatch.objects.create(
            organization=request.user.organization,
            source=source,
            status='pending',
            ingested_by=request.user,
            file_name=file_path,
        )

        # Dispatch Celery task
        from apps.ingestion.tasks import ingest_file
        ingest_file.delay(str(batch.id))

        serializer = ImportBatchSerializer(batch)
        return Response(
            {'batch_id': str(batch.id), 'batch': serializer.data},
            status=status.HTTP_201_CREATED,
        )


class TravelTriggerView(APIView):
    """
    Trigger ingestion of corporate travel data from the configured API endpoint.

    POST /api/ingestion/travel/trigger/
    Body: source_id (UUID of the Travel DataSource)
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Trigger travel data ingestion',
        description='Trigger a fetch from the corporate travel API and ingest the data.',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'source_id': {'type': 'string', 'format': 'uuid'},
                },
                'required': ['source_id'],
            },
        },
        responses={201: ImportBatchSerializer},
    )
    def post(self, request: Request) -> Response:
        """Handle travel data ingestion trigger."""
        source_id = request.data.get('source_id')

        if not source_id:
            return Response(
                {'error': 'source_id is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify the source exists and belongs to the org
        try:
            source = DataSource.objects.for_tenant(
                request.user.organization
            ).get(id=source_id, source_type='corporate_travel')
        except DataSource.DoesNotExist:
            return Response(
                {'error': 'Travel data source not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Create import batch
        batch = ImportBatch.objects.create(
            organization=request.user.organization,
            source=source,
            status='pending',
            ingested_by=request.user,
            file_name='travel_api_fetch',
        )

        # Dispatch Celery task
        from apps.ingestion.tasks import ingest_travel
        ingest_travel.delay(str(batch.id))

        serializer = ImportBatchSerializer(batch)
        return Response(
            {'batch_id': str(batch.id), 'batch': serializer.data},
            status=status.HTTP_201_CREATED,
        )
