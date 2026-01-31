"""
Abstract base class for validation backends.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from pycharter.metadata_store import MetadataStoreClient


class ValidationBackend(ABC):
    """Abstract base class for validation compute backends."""

    @abstractmethod
    def validate(
        self,
        schema_id: str,
        data_source: str,
        options: Dict[str, Any],
        store: MetadataStoreClient,
    ) -> Dict[str, Any]:
        """
        Execute validation asynchronously.

        Args:
            schema_id: Schema identifier from metadata store
            data_source: Data source (S3 path, file path, table name, etc.)
            options: Validation options (include_profiling, etc.)
            store: Metadata store client

        Returns:
            Dictionary with validation results:
            - total_count: Total number of records
            - valid_count: Number of valid records
            - invalid_count: Number of invalid records
            - violations: List of violation details
            - quality_score: Overall quality score (0.0-1.0)
            - field_scores: Per-field quality scores (optional)
        """
        pass

    @abstractmethod
    def close(self):
        """Close backend resources (e.g., Spark session)."""
        pass

