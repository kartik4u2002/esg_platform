"""
Base adapter module for ESG data ingestion.

Provides the abstract BaseAdapter class and the ParsedRow dataclass that all
source-specific adapters must implement.
"""
from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional


@dataclass
class ParsedRow:
    """Represents a single parsed row from a data source."""

    source_row_number: int
    raw_payload: Dict[str, Any]
    checksum: str


def compute_checksum(payload: Dict[str, Any]) -> str:
    """
    Compute a deterministic SHA-256 checksum from a dictionary payload.

    Keys are sorted to ensure consistent ordering regardless of insertion order.
    """
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


class BaseAdapter(ABC):
    """
    Abstract base class for data source adapters.

    Each adapter is responsible for:
    1. Parsing raw input (CSV file, JSON payload, etc.) into ParsedRow objects.
    2. Validating the source format before parsing begins.
    """

    source_type: str = ''

    @abstractmethod
    def parse(self, data: Any) -> Iterator[ParsedRow]:
        """
        Parse input data and yield ParsedRow instances.

        Args:
            data: The raw input data (file path, list of dicts, etc.)

        Yields:
            ParsedRow for each valid row in the input.
        """

    @abstractmethod
    def validate_source_format(self, data: Any) -> List[str]:
        """
        Validate that the source data has the expected format/columns.

        Args:
            data: The raw input data to validate.

        Returns:
            A list of error message strings. Empty list means valid.
        """
