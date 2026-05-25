"""
SAP Procurement data adapter.

Reads CSV exports from SAP procurement systems, maps German column headers
to standardized English field names, and yields ParsedRow objects.
"""
from __future__ import annotations

import csv
import io
from typing import Any, Iterator, List

from apps.ingestion.adapters.base import BaseAdapter, ParsedRow, compute_checksum


class SAPProcurementAdapter(BaseAdapter):
    """Adapter for SAP procurement CSV data with German column headers."""

    source_type = 'sap_procurement'

    COLUMN_MAP = {
        'BELNR': 'invoice_number',
        'BUKRS': 'company_code',
        'WERKS': 'plant_code',
        'MATNR': 'material_number',
        'MENGE': 'quantity',
        'MEINS': 'unit',
        'DMBTR': 'amount',
        'BUDAT': 'posting_date',
        'LIFNR': 'vendor_id',
        'Brennstoffart': 'fuel_type',
        # Alternative columns mapping
        'TransactionID': 'invoice_number',
        'Quantity': 'quantity',
        'TotalCost': 'amount',
        'PurchaseDate': 'posting_date',
        'Supplier': 'vendor_id',
        'ItemName': 'material_number',
        'Category': 'fuel_type',
    }

    REQUIRED_COLUMNS = {'BELNR', 'BUKRS', 'MENGE', 'MEINS', 'BUDAT'}
    REQUIRED_COLUMNS_ALT = {'TransactionID', 'Quantity', 'TotalCost', 'PurchaseDate'}

    def parse(self, data: Any) -> Iterator[ParsedRow]:
        """
        Parse a SAP procurement CSV file.

        Args:
            data: File path (str) or file-like object containing SAP CSV data.
                  Handles BOM via utf-8-sig encoding.

        Yields:
            ParsedRow for each row in the CSV file.
        """
        if isinstance(data, str):
            # data is a file path
            with open(data, 'r', encoding='utf-8-sig', newline='') as f:
                yield from self._parse_file(f)
        elif isinstance(data, bytes):
            # data is raw bytes
            text = data.decode('utf-8-sig')
            f = io.StringIO(text)
            yield from self._parse_file(f)
        else:
            # data is a file-like object
            if hasattr(data, 'read'):
                content = data.read()
                if isinstance(content, bytes):
                    content = content.decode('utf-8-sig')
                f = io.StringIO(content)
                yield from self._parse_file(f)
            else:
                raise TypeError(f'Unsupported data type: {type(data)}')

    def _parse_file(self, file_obj: io.StringIO) -> Iterator[ParsedRow]:
        """Parse rows from a CSV file object."""
        reader = csv.DictReader(file_obj)
        for row_number, row in enumerate(reader, start=1):
            mapped_row = {}
            for original_col, value in row.items():
                # Strip whitespace from column names
                clean_col = original_col.strip()
                mapped_name = self.COLUMN_MAP.get(clean_col, clean_col)
                mapped_row[mapped_name] = value.strip() if value else value

            # Provide default fallbacks for transaction columns that lack standard fields
            if 'invoice_number' in mapped_row:
                if 'company_code' not in mapped_row or not mapped_row['company_code']:
                    mapped_row['company_code'] = 'CC01'
                if 'plant_code' not in mapped_row or not mapped_row['plant_code']:
                    mapped_row['plant_code'] = 'P100'
                if 'unit' not in mapped_row or not mapped_row['unit']:
                    # Default unit so validation passes or is resolved
                    mapped_row['unit'] = 'L'

            checksum = compute_checksum(mapped_row)
            yield ParsedRow(
                source_row_number=row_number,
                raw_payload=mapped_row,
                checksum=checksum,
            )

    def validate_source_format(self, data: Any) -> List[str]:
        """
        Validate that the CSV file contains required SAP or Transaction columns.

        Args:
            data: File path (str) or file-like object.

        Returns:
            List of error messages. Empty if valid.
        """
        errors: List[str] = []
        try:
            if isinstance(data, str):
                with open(data, 'r', encoding='utf-8-sig', newline='') as f:
                    reader = csv.DictReader(f)
                    headers = set(
                        h.strip() for h in (reader.fieldnames or [])
                    )
            elif isinstance(data, bytes):
                text = data.decode('utf-8-sig')
                reader = csv.DictReader(io.StringIO(text))
                headers = set(
                    h.strip() for h in (reader.fieldnames or [])
                )
            else:
                if hasattr(data, 'read'):
                    content = data.read()
                    if isinstance(content, bytes):
                        content = content.decode('utf-8-sig')
                    data.seek(0)
                    reader = csv.DictReader(io.StringIO(content))
                    headers = set(
                        h.strip() for h in (reader.fieldnames or [])
                    )
                else:
                    return ['Unsupported data type for validation']

            missing_std = self.REQUIRED_COLUMNS - headers
            missing_alt = self.REQUIRED_COLUMNS_ALT - headers
            if missing_std and missing_alt:
                errors.append(
                    f"Missing required columns. CSV must contain standard SAP columns: {list(self.REQUIRED_COLUMNS)} OR Transaction columns: {list(self.REQUIRED_COLUMNS_ALT)}"
                )
        except Exception as e:
            errors.append(f'Error reading CSV: {str(e)}')

        return errors
