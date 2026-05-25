"""
Anomaly detection functions for the pipeline app.

Provides statistical and rule-based anomaly detection for each source type:
- Utility: consumption spike detection (3x average threshold)
- SAP: quantity outlier detection (z-score > 3)
- Travel: missing flight distance detection
"""
from __future__ import annotations

import logging
from typing import List

from django.db.models import Avg, StdDev

from apps.pipeline.models import NormalizedRecord, ValidationFlag

logger = logging.getLogger(__name__)


def detect_consumption_spike(record: NormalizedRecord) -> List[ValidationFlag]:
    """
    For utility records: compare against average of last 6 records for the same facility.

    Flags if current consumption is more than 3x the historical average.

    Args:
        record: The NormalizedRecord to check.

    Returns:
        List of unsaved ValidationFlag instances.
    """
    flags: List[ValidationFlag] = []

    if record.quantity_normalized is None:
        return flags

    recent = (
        NormalizedRecord.objects.filter(
            organization=record.organization,
            source_type='utility_electricity',
            facility_or_entity=record.facility_or_entity,
            quantity_normalized__isnull=False,
        )
        .exclude(id=record.id)
        .order_by('-created_at')[:6]
    )

    count = recent.count()
    if count > 0:
        avg = sum(r.quantity_normalized for r in recent) / count
        if avg > 0 and record.quantity_normalized > 3 * avg:
            ratio = record.quantity_normalized / avg
            flags.append(
                ValidationFlag(
                    normalized_record=record,
                    flag_type='CONSUMPTION_SPIKE',
                    severity='warning',
                    message=(
                        f'Consumption {record.quantity_normalized} is '
                        f'{ratio:.1f}x the average ({avg:.1f}) of last '
                        f'{count} records.'
                    ),
                    field_name='quantity_normalized',
                )
            )

    return flags


def detect_quantity_outlier(record: NormalizedRecord) -> List[ValidationFlag]:
    """
    For SAP records: z-score outlier detection within the same source_type + facility.

    Flags if the z-score exceeds 3.0.

    Args:
        record: The NormalizedRecord to check.

    Returns:
        List of unsaved ValidationFlag instances.
    """
    flags: List[ValidationFlag] = []

    if record.quantity_normalized is None:
        return flags

    stats = NormalizedRecord.objects.filter(
        organization=record.organization,
        source_type='sap_procurement',
        facility_or_entity=record.facility_or_entity,
        quantity_normalized__isnull=False,
    ).aggregate(
        avg=Avg('quantity_normalized'),
        stddev=StdDev('quantity_normalized'),
    )

    avg = stats.get('avg') or 0
    stddev = stats.get('stddev') or 0

    if stddev > 0:
        z_score = abs(record.quantity_normalized - avg) / stddev
        if z_score > 3:
            flags.append(
                ValidationFlag(
                    normalized_record=record,
                    flag_type='QUANTITY_OUTLIER',
                    severity='warning',
                    message=(
                        f'Quantity z-score is {z_score:.2f} (> 3.0 threshold). '
                        f'Value: {record.quantity_normalized}, '
                        f'Mean: {avg:.2f}, StdDev: {stddev:.2f}'
                    ),
                    field_name='quantity_normalized',
                )
            )

    return flags


def detect_missing_flight_distance(
    record: NormalizedRecord,
) -> List[ValidationFlag]:
    """
    For travel records: flag if distance_km is null and source indicates air travel.

    Args:
        record: The NormalizedRecord to check.

    Returns:
        List of unsaved ValidationFlag instances.
    """
    flags: List[ValidationFlag] = []

    if record.quantity_normalized is None:
        raw_payload = record.raw_record.raw_payload
        trip_type = raw_payload.get('trip_type', '').lower()
        if trip_type in ('flight', 'air', 'one_way', 'round_trip', ''):
            flags.append(
                ValidationFlag(
                    normalized_record=record,
                    flag_type='MISSING_DISTANCE',
                    severity='warning',
                    message=(
                        'Flight record is missing distance_km. '
                        'Unable to calculate emissions.'
                    ),
                    field_name='distance_km',
                )
            )

    return flags
