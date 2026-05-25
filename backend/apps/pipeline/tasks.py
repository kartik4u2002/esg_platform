"""
Celery tasks for the pipeline app.

Implements the full 4-step pipeline chain for each RawRecord:
1. validate_record - Run source-specific validators
2. normalize_record - Convert quantities, units, dates to standard formats
3. detect_anomalies - Statistical anomaly detection
4. enqueue_for_review - Mark for human review and write audit trail
"""
from __future__ import annotations

import logging

from celery import chain, shared_task

from apps.ingestion.models import ImportBatch, RawRecord
from apps.pipeline.models import NormalizedRecord, ValidationFlag
from common.normalizers import normalize_date, normalize_quantity, normalize_unit
from common.validators import (
    check_date_parseable,
    check_duplicate_invoice,
    check_iata_codes,
    check_no_overlapping_periods,
    check_positive,
    check_positive_if_present,
    check_unit_supported,
    require_fields,
)

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def run_pipeline_for_batch(self, batch_id: str) -> dict:
    """
    Dispatch the pipeline chain for every RawRecord in an ImportBatch.

    Sets the batch status to 'processing' and creates a Celery chain
    for each record: validate → normalize → detect_anomalies → enqueue.
    """
    try:
        batch = ImportBatch.objects.get(id=batch_id)
    except ImportBatch.DoesNotExist:
        logger.error('Batch %s not found', batch_id)
        return {'error': f'Batch {batch_id} not found'}

    batch.status = 'processing'
    batch.save(update_fields=['status'])

    record_ids = list(batch.raw_records.values_list('id', flat=True))
    logger.info(
        'Starting pipeline for batch %s with %d records',
        batch_id, len(record_ids),
    )

    for record_id in record_ids:
        chain(
            validate_record.s(str(record_id)),
            normalize_record.s(),
            detect_anomalies.s(),
            enqueue_for_review.s(),
        ).delay()

    return {'batch_id': batch_id, 'records_dispatched': len(record_ids)}


@shared_task(bind=True, max_retries=3)
def validate_record(self, raw_record_id: str) -> str:
    """
    Run source-specific validation on a single RawRecord.

    Creates a NormalizedRecord (for flag attachment) and any ValidationFlags.
    Returns the raw_record_id for the next step in the chain.
    """
    record = RawRecord.objects.select_related('batch__source').get(
        id=raw_record_id
    )
    record.pipeline_status = 'validating'
    record.save(update_fields=['pipeline_status'])

    payload = record.raw_payload
    source_type = record.batch.source.source_type
    org_id = record.organization_id
    flags = []

    if source_type == 'sap_procurement':
        flags += require_fields(
            payload,
            ['invoice_number', 'company_code', 'quantity', 'unit', 'posting_date'],
        )
        flags += check_positive(payload, 'quantity')
        flags += check_date_parseable(payload, 'posting_date')
        flags += check_unit_supported(payload, 'unit', {'L', 'GAL', 'KG'})
        flags += check_duplicate_invoice(
            payload, 'invoice_number', 'company_code', org_id, record.id
        )

    elif source_type == 'utility_electricity':
        flags += require_fields(
            payload,
            ['meter_id', 'billing_start', 'billing_end', 'usage', 'unit'],
        )
        flags += check_positive(payload, 'usage')
        flags += check_date_parseable(payload, 'billing_start')
        flags += check_date_parseable(payload, 'billing_end')
        flags += check_unit_supported(payload, 'unit', {'kWh', 'MWh'})
        flags += check_no_overlapping_periods(
            payload, 'meter_id', 'billing_start', 'billing_end', org_id, record.id
        )

    elif source_type == 'corporate_travel':
        flags += require_fields(
            payload,
            ['trip_id', 'from_airport', 'to_airport', 'trip_type'],
        )
        flags += check_iata_codes(payload, ['from_airport', 'to_airport'])
        flags += check_positive_if_present(payload, 'distance_km')
        flags += check_positive_if_present(payload, 'transportation_cost')

    # Create NormalizedRecord first (even if validation fails, for flag attachment)
    normalized, created = NormalizedRecord.objects.get_or_create(
        raw_record=record,
        defaults={
            'organization': record.organization,
            'source_type': source_type,
        },
    )

    # Save flags
    error_flags = [f for f in flags if f['severity'] == 'error']
    for flag_data in flags:
        ValidationFlag.objects.create(
            normalized_record=normalized,
            flag_type=flag_data['flag_type'],
            severity=flag_data['severity'],
            message=flag_data['message'],
            field_name=flag_data.get('field_name', ''),
        )

    if error_flags:
        record.pipeline_status = 'validation_failed'
        record.save(update_fields=['pipeline_status'])
        logger.info(
            'Record %s validation failed with %d errors',
            raw_record_id, len(error_flags),
        )
    else:
        logger.info('Record %s validation passed', raw_record_id)

    return str(record.id)


@shared_task
def normalize_record(raw_record_id: str) -> str:
    """
    Normalize quantities, units, and dates for a single RawRecord.

    Reads the raw_payload and populates the NormalizedRecord with
    standardized values. Returns the raw_record_id for chaining.
    """
    record = RawRecord.objects.select_related('batch__source').get(
        id=raw_record_id
    )
    record.pipeline_status = 'normalizing'
    record.save(update_fields=['pipeline_status'])

    payload = record.raw_payload
    source_type = record.batch.source.source_type
    normalized = record.normalized  # OneToOneField reverse
    log = []

    if source_type == 'sap_procurement':
        _normalize_sap(payload, normalized, record, log)
    elif source_type == 'utility_electricity':
        _normalize_utility(payload, normalized, record, log)
    elif source_type == 'corporate_travel':
        _normalize_travel(payload, normalized, record, log)

    normalized.normalization_log = log
    normalized.save()

    logger.info('Record %s normalized', raw_record_id)
    return str(record.id)


def _normalize_sap(
    payload: dict,
    normalized: NormalizedRecord,
    record: RawRecord,
    log: list,
) -> None:
    """Normalize SAP procurement record fields."""
    # Normalize quantity
    raw_qty = payload.get('quantity', '0')
    try:
        qty, qty_log = normalize_quantity(str(raw_qty))
        log.append(qty_log)
    except (ValueError, TypeError):
        qty = None
        log.append({
            'transformation': 'quantity_normalization',
            'error': f'Could not parse: {raw_qty}',
        })

    # Normalize unit
    raw_unit = payload.get('unit', '')
    if qty is not None and raw_unit:
        qty, unit, unit_log = normalize_unit(qty, raw_unit)
        log.append(unit_log)
    else:
        unit = raw_unit

    # Normalize date
    raw_date = payload.get('posting_date', '')
    try:
        parsed_date, fmt, date_log = normalize_date(str(raw_date))
        log.append(date_log)
    except (ValueError, TypeError):
        parsed_date = None
        log.append({
            'transformation': 'date_parsing',
            'error': f'Could not parse: {raw_date}',
        })

    normalized.quantity_normalized = qty
    normalized.unit_normalized = unit if unit else ''
    normalized.emission_scope = record.batch.source.scope_category
    normalized.period_start = parsed_date
    normalized.period_end = parsed_date
    normalized.facility_or_entity = payload.get(
        'plant_code', payload.get('company_code', '')
    )


def _normalize_utility(
    payload: dict,
    normalized: NormalizedRecord,
    record: RawRecord,
    log: list,
) -> None:
    """Normalize utility electricity record fields."""
    raw_usage = payload.get('usage', '0')
    try:
        usage, qty_log = normalize_quantity(str(raw_usage))
        log.append(qty_log)
    except (ValueError, TypeError):
        usage = None
        log.append({
            'transformation': 'quantity_normalization',
            'error': f'Could not parse: {raw_usage}',
        })

    raw_unit = payload.get('unit', 'kWh')
    if usage is not None:
        usage, unit, unit_log = normalize_unit(usage, raw_unit)
        log.append(unit_log)
    else:
        unit = raw_unit

    try:
        start_date, _, start_log = normalize_date(
            str(payload.get('billing_start', ''))
        )
        log.append(start_log)
    except (ValueError, TypeError):
        start_date = None

    try:
        end_date, _, end_log = normalize_date(
            str(payload.get('billing_end', ''))
        )
        log.append(end_log)
    except (ValueError, TypeError):
        end_date = None

    normalized.quantity_normalized = usage
    normalized.unit_normalized = unit if unit else ''
    normalized.emission_scope = record.batch.source.scope_category
    normalized.period_start = start_date
    normalized.period_end = end_date
    normalized.facility_or_entity = payload.get(
        'facility_id', payload.get('meter_id', '')
    )


def _normalize_travel(
    payload: dict,
    normalized: NormalizedRecord,
    record: RawRecord,
    log: list,
) -> None:
    """Normalize corporate travel record fields."""
    distance = payload.get('distance_km')
    if distance is not None:
        try:
            distance, qty_log = normalize_quantity(str(distance))
            log.append(qty_log)
        except (ValueError, TypeError):
            distance = None
            log.append({
                'transformation': 'quantity_normalization',
                'error': 'Could not parse distance',
            })
    else:
        log.append({
            'transformation': 'missing_distance',
            'note': 'distance_km is null',
        })

    normalized.quantity_normalized = distance
    normalized.unit_normalized = 'km'
    normalized.emission_scope = record.batch.source.scope_category
    normalized.facility_or_entity = (
        payload.get('from_airport', '') + '-' + payload.get('to_airport', '')
    )


@shared_task
def detect_anomalies(raw_record_id: str) -> str:
    """
    Run statistical anomaly detection on a NormalizedRecord.

    Delegates to source-specific detectors in apps.pipeline.anomaly.
    Returns the raw_record_id for chaining.
    """
    record = RawRecord.objects.select_related('batch__source').get(
        id=raw_record_id
    )
    record.pipeline_status = 'anomaly_detection'
    record.save(update_fields=['pipeline_status'])

    normalized = record.normalized
    source_type = record.batch.source.source_type

    from apps.pipeline.anomaly import (
        detect_consumption_spike,
        detect_missing_flight_distance,
        detect_quantity_outlier,
    )

    anomaly_flags = []
    if source_type == 'utility_electricity':
        anomaly_flags += detect_consumption_spike(normalized)
    elif source_type == 'sap_procurement':
        anomaly_flags += detect_quantity_outlier(normalized)
    elif source_type == 'corporate_travel':
        anomaly_flags += detect_missing_flight_distance(normalized)

    for flag in anomaly_flags:
        flag.save()

    if anomaly_flags:
        logger.info(
            'Record %s: %d anomalies detected',
            raw_record_id, len(anomaly_flags),
        )

    return str(record.id)


@shared_task
def enqueue_for_review(raw_record_id: str) -> str:
    """
    Mark a record as ready for human review.

    Sets pipeline_status to 'review_pending', writes an audit event,
    and updates the batch progress counter.
    """
    record = RawRecord.objects.get(id=raw_record_id)
    record.pipeline_status = 'review_pending'
    record.save(update_fields=['pipeline_status'])

    normalized = record.normalized
    normalized.review_status = 'pending'
    normalized.save(update_fields=['review_status'])

    # Write audit event
    from apps.audit.services import log_event
    log_event(
        actor=None,
        entity=normalized,
        action='ENQUEUED_FOR_REVIEW',
        after={
            'review_status': 'pending',
            'pipeline_status': 'review_pending',
        },
    )

    # Update batch processed count
    batch = record.batch
    batch.processed_rows = batch.raw_records.exclude(
        pipeline_status='ingested'
    ).count()
    if batch.processed_rows >= batch.total_rows:
        batch.status = 'completed'
    batch.save(update_fields=['processed_rows', 'status'])

    logger.info('Record %s enqueued for review', raw_record_id)
    return str(record.id)
