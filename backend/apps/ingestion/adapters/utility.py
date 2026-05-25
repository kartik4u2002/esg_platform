"""
Utility Electricity data adapter.

Reads CSV exports from utility providers containing electricity billing data.
"""
from __future__ import annotations

import csv
import io
from typing import Any, Iterator, List

from apps.ingestion.adapters.base import BaseAdapter, ParsedRow, compute_checksum


class UtilityElectricityAdapter(BaseAdapter):
    """Adapter for utility electricity billing CSV data."""

    source_type = 'utility_electricity'

    EXPECTED_COLUMNS = {
        'meter_id', 'billing_start', 'billing_end',
        'usage', 'unit', 'tariff', 'facility_id', 'anomaly_label',
    }

    REQUIRED_COLUMNS = {
        'meter_id', 'billing_start', 'billing_end', 'usage', 'unit',
    }
    REQUIRED_COLUMNS_ALT = {'Timestamp', 'Electricity_Consumed'}

    def parse(self, data: Any) -> Iterator[ParsedRow]:
        """
        Parse a utility electricity CSV file.

        Args:
            data: File path (str), bytes, or file-like object.

        Yields:
            ParsedRow for each row. Missing tariff is set to None.
        """
        if isinstance(data, str):
            with open(data, 'r', encoding='utf-8-sig', newline='') as f:
                yield from self._parse_file(f)
        elif isinstance(data, bytes):
            text = data.decode('utf-8-sig')
            yield from self._parse_file(io.StringIO(text))
        else:
            if hasattr(data, 'read'):
                content = data.read()
                if isinstance(content, bytes):
                    content = content.decode('utf-8-sig')
                yield from self._parse_file(io.StringIO(content))
            else:
                raise TypeError(f'Unsupported data type: {type(data)}')

    def _parse_file(self, file_obj: io.StringIO) -> Iterator[ParsedRow]:
        """Parse rows from a CSV file object."""
        reader = csv.DictReader(file_obj)
        for row_number, row in enumerate(reader, start=1):
            payload = {}
            for col, value in row.items():
                clean_col = col.strip()
                cleaned_value = value.strip() if value else value
                payload[clean_col] = cleaned_value

            # Map alternative smart meter columns to standard fields
            if 'Timestamp' in payload:
                # Map Timestamp to both start and end dates
                payload['billing_start'] = payload.get('Timestamp')
                payload['billing_end'] = payload.get('Timestamp')
                payload['usage'] = payload.get('Electricity_Consumed')
                payload['anomaly_label'] = payload.get('Anomaly_Label', '')

            # Apply defaults for missing fields
            if 'meter_id' not in payload or not payload['meter_id']:
                payload['meter_id'] = 'MTR-SMART'
            if 'unit' not in payload or not payload['unit']:
                payload['unit'] = 'kWh'
            if 'facility_id' not in payload or not payload['facility_id']:
                payload['facility_id'] = 'FAC-001'
            if 'tariff' not in payload or payload.get('tariff') == '':
                payload['tariff'] = None

            checksum = compute_checksum(payload)
            yield ParsedRow(
                source_row_number=row_number,
                raw_payload=payload,
                checksum=checksum,
            )

    def validate_source_format(self, data: Any) -> List[str]:
        """
        Validate that the CSV file contains required Utility or Smart Meter columns.

        Args:
            data: File path (str), bytes, or file-like object.

        Returns:
            List of error messages. Empty if valid.
        """
        errors: List[str] = []
        try:
            if isinstance(data, str):
                with open(data, 'r', encoding='utf-8-sig', newline='') as f:
                    reader = csv.DictReader(f)
                    headers = set(h.strip() for h in (reader.fieldnames or []))
            elif isinstance(data, bytes):
                text = data.decode('utf-8-sig')
                reader = csv.DictReader(io.StringIO(text))
                headers = set(h.strip() for h in (reader.fieldnames or []))
            else:
                if hasattr(data, 'read'):
                    content = data.read()
                    if isinstance(content, bytes):
                        content = content.decode('utf-8-sig')
                    data.seek(0)
                    reader = csv.DictReader(io.StringIO(content))
                    headers = set(h.strip() for h in (reader.fieldnames or []))
                else:
                    return ['Unsupported data type for validation']

            missing_std = self.REQUIRED_COLUMNS - headers
            missing_alt = self.REQUIRED_COLUMNS_ALT - headers
            if missing_std and missing_alt:
                errors.append(
                    f"Missing required columns. CSV must contain standard Utility columns: {list(self.REQUIRED_COLUMNS)} OR Smart Meter columns: {list(self.REQUIRED_COLUMNS_ALT)}"
                )
        except Exception as e:
            errors.append(f'Error reading CSV: {str(e)}')

        return errors
