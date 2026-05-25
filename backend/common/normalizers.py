"""
Normalizers for ESG data ingestion pipeline.

Functions to normalize units, dates, and quantities into canonical formats,
each returning a tuple of (normalized_value, metadata_log_entry).
"""
from __future__ import annotations

from datetime import date, datetime

# ---------------------------------------------------------------------------
# Unit conversion table
# ---------------------------------------------------------------------------
UNIT_CONVERSIONS: dict[str, dict] = {
    'L':   {'to': 'litre',    'factor': 1.0},
    'GAL': {'to': 'litre',    'factor': 3.78541},
    'KG':  {'to': 'kilogram', 'factor': 1.0},
    'MWH': {'to': 'kWh',      'factor': 1000.0},
    'KWH': {'to': 'kWh',      'factor': 1.0},
}

# ---------------------------------------------------------------------------
# Date formats to attempt (order matters — first match wins)
# ---------------------------------------------------------------------------
DATE_FORMATS: list[str] = [
    '%d.%m.%Y',
    '%Y-%m-%d',
    '%m/%d/%Y',
    '%d-%m-%Y',
    '%Y/%m/%d',
]


def normalize_unit(value: float, unit: str) -> tuple[float, str, dict]:
    """
    Convert *value* from *unit* to a canonical unit using ``UNIT_CONVERSIONS``.

    Returns:
        (normalized_value, canonical_unit, log_entry)
    """
    unit_upper = unit.strip().upper()
    conv = UNIT_CONVERSIONS.get(unit_upper)
    if conv is not None:
        normalized_value = value * conv['factor']
        log_entry = {
            'transformation': 'unit_conversion',
            'original_value': value,
            'original_unit': unit,
            'normalized_value': normalized_value,
            'normalized_unit': conv['to'],
            'factor': conv['factor'],
        }
        return normalized_value, conv['to'], log_entry

    # Unknown unit — pass through unchanged
    log_entry = {
        'transformation': 'unit_passthrough',
        'original_unit': unit,
        'note': f'No conversion found for unit "{unit}", passing through as-is',
    }
    return value, unit, log_entry


def normalize_date(raw_date: str) -> tuple[date, str, dict]:
    """
    Parse *raw_date* by trying each format in ``DATE_FORMATS``.

    Returns:
        (parsed_date, detected_format, log_entry)

    Raises:
        ValueError: if none of the known formats match.
    """
    raw_date = str(raw_date).strip()
    for fmt in DATE_FORMATS:
        try:
            parsed = datetime.strptime(raw_date, fmt).date()
            log_entry = {
                'transformation': 'date_parsing',
                'original': raw_date,
                'detected_format': fmt,
                'normalized': parsed.isoformat(),
            }
            return parsed, fmt, log_entry
        except ValueError:
            continue
    raise ValueError(f'Could not parse date: {raw_date}')


def normalize_quantity(raw_value: str) -> tuple[float, dict]:
    """
    Parse a numeric string that may use European (``1.234,56``) or US
    (``1,234.56``) formatting.

    Returns:
        (float_value, log_entry)
    """
    original = str(raw_value).strip()
    cleaned = original

    if ',' in cleaned and '.' in cleaned:
        # Both separators present — last one is decimal
        if cleaned.rfind(',') > cleaned.rfind('.'):
            # European: 1.234,56
            cleaned = cleaned.replace('.', '').replace(',', '.')
        else:
            # US: 1,234.56
            cleaned = cleaned.replace(',', '')
    elif ',' in cleaned:
        # Only comma — treat as decimal if <=3 digits after it
        parts = cleaned.split(',')
        if len(parts) == 2 and len(parts[1]) <= 3:
            cleaned = cleaned.replace(',', '.')
        else:
            cleaned = cleaned.replace(',', '')

    value = float(cleaned)
    log_entry = {
        'transformation': 'quantity_normalization',
        'original': original,
        'normalized': value,
    }
    return value, log_entry
