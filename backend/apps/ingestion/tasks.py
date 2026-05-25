"""
Celery tasks for the ingestion app.

Handles asynchronous file parsing and API data fetching, creating RawRecords
and dispatching them into the pipeline.
"""
from __future__ import annotations

import logging

import requests
from celery import shared_task
from django.conf import settings
from django.core.files.storage import default_storage

from apps.ingestion.adapters import ADAPTER_REGISTRY
from apps.ingestion.models import ImportBatch, RawRecord

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def ingest_file(self, batch_id: str) -> dict:
    """
    Ingest a CSV file for a given ImportBatch.

    Steps:
    1. Load the file from default storage.
    2. Look up the adapter for the source type.
    3. Parse rows and create RawRecords (bulk_create with ignore_conflicts).
    4. Update batch status and counts.
    5. Dispatch run_pipeline_for_batch.

    Args:
        batch_id: The UUID (as string) of the ImportBatch to process.

    Returns:
        dict with batch_id and row counts.
    """
    try:
        batch = ImportBatch.objects.select_related('source').get(id=batch_id)
    except ImportBatch.DoesNotExist:
        logger.error('ImportBatch %s not found', batch_id)
        return {'error': f'Batch {batch_id} not found'}

    batch.status = 'processing'
    batch.save(update_fields=['status'])

    source_type = batch.source.source_type
    adapter_cls = ADAPTER_REGISTRY.get(source_type)
    if not adapter_cls:
        batch.status = 'failed'
        batch.error_message = f'No adapter found for source type: {source_type}'
        batch.save(update_fields=['status', 'error_message'])
        return {'error': batch.error_message}

    adapter = adapter_cls()

    try:
        # Read file from storage
        file_path = batch.file_name
        with default_storage.open(file_path, 'rb') as f:
            file_content = f.read()

        # Validate source format
        errors = adapter.validate_source_format(file_content)
        if errors:
            batch.status = 'failed'
            batch.error_message = '; '.join(errors)
            batch.save(update_fields=['status', 'error_message'])
            return {'error': batch.error_message}

        # Parse rows and build RawRecord objects
        raw_records = []
        for parsed_row in adapter.parse(file_content):
            raw_records.append(
                RawRecord(
                    batch=batch,
                    organization=batch.organization,
                    raw_payload=parsed_row.raw_payload,
                    checksum=parsed_row.checksum,
                    source_row_number=parsed_row.source_row_number,
                    pipeline_status='ingested',
                )
            )

        # Bulk create with ignore_conflicts to handle duplicate checksums
        created = RawRecord.objects.bulk_create(
            raw_records, ignore_conflicts=True
        )

        batch.total_rows = len(raw_records)
        batch.save(update_fields=['total_rows'])

        # Dispatch pipeline processing
        from apps.pipeline.tasks import run_pipeline_for_batch
        run_pipeline_for_batch.delay(str(batch.id))

        logger.info(
            'Batch %s: ingested %d rows (source: %s)',
            batch_id, len(raw_records), source_type,
        )
        return {
            'batch_id': batch_id,
            'total_rows': len(raw_records),
            'status': 'processing',
        }

    except Exception as exc:
        batch.status = 'failed'
        batch.error_message = str(exc)
        batch.save(update_fields=['status', 'error_message'])
        logger.exception('Failed to ingest batch %s', batch_id)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def ingest_travel(self, batch_id: str) -> dict:
    """
    Fetch corporate travel data from the configured API and ingest it.

    Steps:
    1. Fetch data from TRAVEL_API_URL.
    2. Parse with the CorporateTravelAdapter.
    3. Create RawRecords.
    4. Dispatch pipeline processing.

    Args:
        batch_id: The UUID (as string) of the ImportBatch to process.

    Returns:
        dict with batch_id and row counts.
    """
    try:
        batch = ImportBatch.objects.select_related('source').get(id=batch_id)
    except ImportBatch.DoesNotExist:
        logger.error('ImportBatch %s not found', batch_id)
        return {'error': f'Batch {batch_id} not found'}

    batch.status = 'processing'
    batch.save(update_fields=['status'])

    travel_api_url = getattr(
        settings, 'TRAVEL_API_URL',
        'http://localhost:8000/api/mock/travel-feed/'
    )

    try:
        # Fetch travel data from API
        response = requests.get(travel_api_url, timeout=30)
        response.raise_for_status()
        travel_data = response.json()

        adapter_cls = ADAPTER_REGISTRY.get('corporate_travel')
        if not adapter_cls:
            batch.status = 'failed'
            batch.error_message = 'No adapter for corporate_travel'
            batch.save(update_fields=['status', 'error_message'])
            return {'error': batch.error_message}

        adapter = adapter_cls()

        # Validate format
        errors = adapter.validate_source_format(travel_data)
        if errors:
            batch.status = 'failed'
            batch.error_message = '; '.join(errors)
            batch.save(update_fields=['status', 'error_message'])
            return {'error': batch.error_message}

        # Parse and build RawRecords
        raw_records = []
        for parsed_row in adapter.parse(travel_data):
            raw_records.append(
                RawRecord(
                    batch=batch,
                    organization=batch.organization,
                    raw_payload=parsed_row.raw_payload,
                    checksum=parsed_row.checksum,
                    source_row_number=parsed_row.source_row_number,
                    pipeline_status='ingested',
                )
            )

        RawRecord.objects.bulk_create(raw_records, ignore_conflicts=True)

        batch.total_rows = len(raw_records)
        batch.save(update_fields=['total_rows'])

        # Dispatch pipeline
        from apps.pipeline.tasks import run_pipeline_for_batch
        run_pipeline_for_batch.delay(str(batch.id))

        logger.info(
            'Batch %s: ingested %d travel records', batch_id, len(raw_records)
        )
        return {
            'batch_id': batch_id,
            'total_rows': len(raw_records),
            'status': 'processing',
        }

    except Exception as exc:
        batch.status = 'failed'
        batch.error_message = str(exc)
        batch.save(update_fields=['status', 'error_message'])
        logger.exception('Failed to ingest travel batch %s', batch_id)
        raise self.retry(exc=exc)
