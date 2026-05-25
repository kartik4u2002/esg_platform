"""
Corporate Travel data adapter.

Processes travel booking data from JSON API responses.
"""
from __future__ import annotations

from typing import Any, Dict, Iterator, List

from apps.ingestion.adapters.base import BaseAdapter, ParsedRow, compute_checksum


class CorporateTravelAdapter(BaseAdapter):
    """Adapter for corporate travel JSON data from booking APIs."""

    source_type = 'corporate_travel'

    REQUIRED_FIELDS = {
        'trip_id', 'employee_id', 'booking_source',
        'from_airport', 'to_airport', 'trip_type',
    }

    def parse(self, data: Any) -> Iterator[ParsedRow]:
        """
        Parse a list of travel record dicts (from JSON API).

        Args:
            data: A list of dicts, each representing a travel booking.

        Yields:
            ParsedRow for each record. Missing distance_km is set to None.
        """
        if not isinstance(data, list):
            raise TypeError(f'Expected list of dicts, got {type(data)}')

        for row_number, record in enumerate(data, start=1):
            payload = dict(record)

            # Handle missing distance_km
            if 'distance_km' not in payload or payload['distance_km'] is None:
                payload['distance_km'] = None

            checksum = compute_checksum(payload)
            yield ParsedRow(
                source_row_number=row_number,
                raw_payload=payload,
                checksum=checksum,
            )

    def validate_source_format(self, data: Any) -> List[str]:
        """
        Validate that the first record in the list has all required fields.

        Args:
            data: A list of dicts.

        Returns:
            List of error messages. Empty if valid.
        """
        errors: List[str] = []

        if not isinstance(data, list):
            return ['Expected a list of dicts']

        if len(data) == 0:
            return ['Empty data list']

        first_record = data[0]
        if not isinstance(first_record, dict):
            return ['First record is not a dict']

        missing = self.REQUIRED_FIELDS - set(first_record.keys())
        if missing:
            errors.append(
                f"Missing required fields in first record: {', '.join(sorted(missing))}"
            )

        return errors
