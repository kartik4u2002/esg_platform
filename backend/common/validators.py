"""
Validators for ESG data ingestion pipeline.

Each validator function accepts a payload dict (and optional context) and
returns a list of flag dicts with keys: flag_type, severity, message, field_name.
"""
from __future__ import annotations

import re
from typing import Optional


def require_fields(payload: dict, fields: list[str]) -> list[dict]:
    """Return error flag for each missing or empty field."""
    flags: list[dict] = []
    for field in fields:
        val = payload.get(field)
        if val is None or (isinstance(val, str) and val.strip() == ''):
            flags.append({
                'flag_type': 'MISSING_FIELD',
                'severity': 'error',
                'message': f'Required field "{field}" is missing or empty.',
                'field_name': field,
            })
    return flags


def check_positive(payload: dict, field: str) -> list[dict]:
    """Return error flag if value is <= 0 or non-numeric."""
    val = payload.get(field)
    if val is None:
        return []
    try:
        numeric = float(str(val).replace(',', '.'))
        if numeric <= 0:
            return [{
                'flag_type': 'NEGATIVE_VALUE',
                'severity': 'error',
                'message': f'Field "{field}" has non-positive value: {val}',
                'field_name': field,
            }]
    except (ValueError, TypeError):
        return [{
            'flag_type': 'NEGATIVE_VALUE',
            'severity': 'error',
            'message': f'Field "{field}" is not numeric: {val}',
            'field_name': field,
        }]
    return []


def check_date_parseable(payload: dict, field: str) -> list[dict]:
    """Try multiple date formats. Return error flag if unparseable."""
    from datetime import datetime

    from common.normalizers import DATE_FORMATS

    val = payload.get(field)
    if val is None or str(val).strip() == '':
        return []
    for fmt in DATE_FORMATS:
        try:
            datetime.strptime(str(val).strip(), fmt)
            return []
        except ValueError:
            continue
    return [{
        'flag_type': 'INVALID_DATE',
        'severity': 'error',
        'message': f'Field "{field}" has unparseable date: {val}',
        'field_name': field,
    }]


def check_unit_supported(payload: dict, field: str, allowed: set) -> list[dict]:
    """Return error flag if the unit value is not in the allowed set."""
    val = payload.get(field)
    if val is None:
        return []
    if str(val).strip().upper() not in {u.upper() for u in allowed}:
        return [{
            'flag_type': 'UNSUPPORTED_UNIT',
            'severity': 'error',
            'message': f'Unit "{val}" is not supported. Allowed: {allowed}',
            'field_name': field,
        }]
    return []


def check_duplicate_invoice(
    payload: dict,
    invoice_field: str,
    company_field: str,
    organization_id,
    current_record_id=None,
) -> list[dict]:
    """Query DB for existing RawRecord with same invoice+company within the org."""
    from apps.ingestion.models import RawRecord

    invoice = payload.get(invoice_field)
    company = payload.get(company_field)
    if not invoice or not company:
        return []
    qs = RawRecord.objects.filter(
        organization_id=organization_id,
        raw_payload__contains={invoice_field: invoice, company_field: company},
    )
    if current_record_id:
        qs = qs.exclude(id=current_record_id)
    if qs.exists():
        return [{
            'flag_type': 'DUPLICATE_INVOICE',
            'severity': 'error',
            'message': f'Duplicate invoice {invoice} for company {company} found.',
            'field_name': invoice_field,
        }]
    return []


def check_no_overlapping_periods(
    payload: dict,
    meter_field: str,
    start_field: str,
    end_field: str,
    organization_id,
    current_record_id=None,
) -> list[dict]:
    """Check whether a billing period overlaps existing normalized records."""
    from apps.pipeline.models import NormalizedRecord
    from common.normalizers import normalize_date

    meter = payload.get(meter_field)
    start_raw = payload.get(start_field)
    end_raw = payload.get(end_field)
    if not meter or not start_raw or not end_raw:
        return []
    try:
        start_date, _, _ = normalize_date(str(start_raw))
        end_date, _, _ = normalize_date(str(end_raw))
    except Exception:
        return []
    overlapping = NormalizedRecord.objects.filter(
        organization_id=organization_id,
        source_type='utility_electricity',
        facility_or_entity=meter,
        period_start__lt=end_date,
        period_end__gt=start_date,
    )
    if current_record_id:
        overlapping = overlapping.exclude(raw_record_id=current_record_id)
    if overlapping.exists():
        return [{
            'flag_type': 'OVERLAPPING_PERIOD',
            'severity': 'warning',
            'message': f'Overlapping billing period for meter {meter}: {start_raw} - {end_raw}',
            'field_name': start_field,
        }]
    return []


def check_iata_codes(payload: dict, fields: list[str]) -> list[dict]:
    """Validate IATA airport codes — format check + common-airports lookup."""
    COMMON_IATA = {
        'ATL', 'PEK', 'LAX', 'DXB', 'HND', 'ORD', 'LHR', 'PVG', 'CDG', 'DFW',
        'AMS', 'FRA', 'IST', 'CAN', 'JFK', 'SIN', 'DEN', 'ICN', 'BKK', 'SFO',
        'DEL', 'CGK', 'BOM', 'NRT', 'KUL', 'MAD', 'CTU', 'BCN', 'LAS', 'MIA',
        'MUC', 'SYD', 'YYZ', 'FCO', 'LGW', 'EWR', 'SEA', 'MSP', 'DTW', 'BOS',
        'PHX', 'MCO', 'IAH', 'CLT', 'SZX', 'MEX', 'DOH', 'HKG', 'TPE', 'MNL',
    }
    flags: list[dict] = []
    for field in fields:
        val = payload.get(field)
        if val is None or str(val).strip() == '':
            continue
        code = str(val).strip().upper()
        if not re.match(r'^[A-Z]{3}$', code):
            flags.append({
                'flag_type': 'INVALID_IATA',
                'severity': 'error',
                'message': f'Invalid IATA code format: "{val}" (must be 3 uppercase letters)',
                'field_name': field,
            })
        elif code not in COMMON_IATA:
            flags.append({
                'flag_type': 'INVALID_IATA',
                'severity': 'warning',
                'message': f'IATA code "{code}" not in common airports list',
                'field_name': field,
            })
    return flags


def check_positive_if_present(payload: dict, field: str) -> list[dict]:
    """Return warning flag if a present value is non-positive (optional field)."""
    val = payload.get(field)
    if val is None:
        return []
    try:
        numeric = float(str(val).replace(',', '.'))
        if numeric <= 0:
            return [{
                'flag_type': 'NEGATIVE_VALUE',
                'severity': 'warning',
                'message': f'Field "{field}" is present but non-positive: {val}',
                'field_name': field,
            }]
    except (ValueError, TypeError):
        return []
    return []
