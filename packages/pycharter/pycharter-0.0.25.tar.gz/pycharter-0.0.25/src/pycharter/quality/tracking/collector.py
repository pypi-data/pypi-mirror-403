"""
Quality Tracking Collector - Metrics collection and querying.

Provides the main interface for recording validation metrics
and querying historical data.
"""

import re
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from pycharter.quality.tracking.models import MetricsFilter, MetricsSummary, ValidationMetric
from pycharter.quality.tracking.store import MetricsStore, InMemoryMetricsStore

if TYPE_CHECKING:
    from pycharter.runtime_validator.validator_core import ValidationResult, QualityMetrics


class MetricsCollector:
    """
    Collect and query validation metrics over time.

    The MetricsCollector is the primary interface for tracking validation
    quality metrics. It records metrics from validation results and provides
    querying capabilities for analysis.

    Example:
        >>> from pycharter.quality.tracking import MetricsCollector, InMemoryMetricsStore
        >>> from pycharter.runtime_validator import Validator
        >>>
        >>> # Create collector
        >>> store = InMemoryMetricsStore()
        >>> collector = MetricsCollector(store)
        >>>
        >>> # Record validation results
        >>> validator = Validator(contract_dir="contracts/users")
        >>> result = validator.validate(data)
        >>> collector.record(result, schema_name="users", version="1.0.0")
        >>>
        >>> # Query metrics
        >>> recent = collector.query(schema_name="users", limit=10)
        >>> summary = collector.get_summary("users", window_hours=24)
    """

    def __init__(self, store: Optional[MetricsStore] = None):
        """
        Initialize the metrics collector.

        Args:
            store: Storage backend for metrics. Defaults to InMemoryMetricsStore.
        """
        self._store = store or InMemoryMetricsStore()

    @property
    def store(self) -> MetricsStore:
        """Get the underlying store."""
        return self._store

    def record(
        self,
        result: "ValidationResult",
        schema_name: str,
        version: str,
        duration_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ValidationMetric:
        """
        Record metrics from a validation result.

        Extracts metrics from the ValidationResult and stores them
        for later analysis.

        Args:
            result: ValidationResult from a validation operation
            schema_name: Name of the schema validated against
            version: Version of the schema
            duration_ms: Validation duration in milliseconds
            metadata: Additional custom metadata to store

        Returns:
            The recorded ValidationMetric
        """
        # Extract quality metrics if available
        quality = result.quality
        if quality:
            completeness = quality.completeness
            field_completeness = quality.field_completeness
            record_count = quality.record_count
            valid_count = quality.valid_count
            error_count = quality.error_count
            validity_rate = quality.validity_rate
        else:
            # Compute basic metrics from result
            completeness = 1.0
            field_completeness = {}
            record_count = 1
            valid_count = 1 if result.is_valid else 0
            error_count = 0 if result.is_valid else 1
            validity_rate = 1.0 if result.is_valid else 0.0

        # Extract error types from error messages
        errors_by_type = self._categorize_errors(result.errors)

        metric = ValidationMetric(
            schema_name=schema_name,
            version=version,
            timestamp=datetime.utcnow(),
            record_count=record_count,
            valid_count=valid_count,
            error_count=error_count,
            validity_rate=validity_rate,
            completeness=completeness,
            field_completeness=field_completeness,
            duration_ms=duration_ms,
            errors_by_type=errors_by_type,
            metadata=metadata or {},
        )

        self._store.store(metric)
        return metric

    def record_batch(
        self,
        results: List["ValidationResult"],
        schema_name: str,
        version: str,
        duration_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ValidationMetric:
        """
        Record aggregated metrics from a batch of validation results.

        Combines metrics from multiple validation results into a single
        metric record representing the batch.

        Args:
            results: List of ValidationResults from batch validation
            schema_name: Name of the schema validated against
            version: Version of the schema
            duration_ms: Total validation duration in milliseconds
            metadata: Additional custom metadata to store

        Returns:
            The recorded ValidationMetric for the batch
        """
        if not results:
            return self.record(
                _EmptyResult(),  # type: ignore
                schema_name,
                version,
                duration_ms,
                metadata,
            )

        record_count = len(results)
        valid_count = sum(1 for r in results if r.is_valid)
        error_count = record_count - valid_count
        validity_rate = valid_count / record_count if record_count > 0 else 1.0

        # Aggregate errors
        all_errors = []
        for r in results:
            all_errors.extend(r.errors)
        errors_by_type = self._categorize_errors(all_errors)

        # Aggregate quality metrics if available
        completeness_values = []
        field_completeness_agg: Dict[str, List[float]] = defaultdict(list)

        for r in results:
            if r.quality:
                completeness_values.append(r.quality.completeness)
                for field, comp in r.quality.field_completeness.items():
                    field_completeness_agg[field].append(comp)

        completeness = (
            sum(completeness_values) / len(completeness_values)
            if completeness_values
            else 1.0
        )
        field_completeness = {
            field: sum(values) / len(values)
            for field, values in field_completeness_agg.items()
        }

        metric = ValidationMetric(
            schema_name=schema_name,
            version=version,
            timestamp=datetime.utcnow(),
            record_count=record_count,
            valid_count=valid_count,
            error_count=error_count,
            validity_rate=validity_rate,
            completeness=completeness,
            field_completeness=field_completeness,
            duration_ms=duration_ms,
            errors_by_type=errors_by_type,
            metadata=metadata or {},
        )

        self._store.store(metric)
        return metric

    def query(
        self,
        schema_name: Optional[str] = None,
        version: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        min_validity_rate: Optional[float] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ValidationMetric]:
        """
        Query stored metrics with filters.

        Args:
            schema_name: Filter by schema name
            version: Filter by schema version
            since: Filter metrics after this time
            until: Filter metrics before this time
            min_validity_rate: Filter by minimum validity rate
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of matching ValidationMetrics, ordered by timestamp descending
        """
        filters = MetricsFilter(
            schema_name=schema_name,
            version=version,
            since=since,
            until=until,
            min_validity_rate=min_validity_rate,
            limit=limit,
            offset=offset,
        )
        return self._store.query(filters)

    def get_summary(self, schema_name: str, window_hours: int = 24) -> MetricsSummary:
        """
        Get aggregated summary for a schema within a time window.

        Args:
            schema_name: Name of the schema to summarize
            window_hours: Number of hours to look back

        Returns:
            MetricsSummary with aggregated statistics
        """
        return self._store.get_summary(schema_name, window_hours)

    def get_all_schemas(self) -> List[str]:
        """
        Get list of all schema names with recorded metrics.

        Returns:
            List of unique schema names
        """
        # Query all metrics to get unique schemas
        metrics = self._store.query(MetricsFilter(limit=10000))
        return list(set(m.schema_name for m in metrics))

    def _categorize_errors(self, errors: List[str]) -> Dict[str, int]:
        """
        Categorize errors by type.

        Extracts error types from error messages for aggregation.
        """
        error_counts: Dict[str, int] = defaultdict(int)

        for error in errors:
            error_type = self._extract_error_type(error)
            error_counts[error_type] += 1

        return dict(error_counts)

    def _extract_error_type(self, error: str) -> str:
        """
        Extract error type from error message.

        Attempts to identify the error category from the message.
        """
        error_lower = error.lower()

        # Common error patterns
        if "required" in error_lower or "missing" in error_lower:
            return "missing_required"
        if "type" in error_lower:
            return "type_error"
        if "pattern" in error_lower or "regex" in error_lower:
            return "pattern_mismatch"
        if "min" in error_lower or "max" in error_lower or "range" in error_lower:
            return "range_error"
        if "enum" in error_lower or "allowed" in error_lower:
            return "enum_error"
        if "format" in error_lower:
            return "format_error"
        if "null" in error_lower or "none" in error_lower:
            return "null_error"
        if "unique" in error_lower or "duplicate" in error_lower:
            return "uniqueness_error"

        # Extract field name if present (e.g., "('field_name',): error message")
        field_match = re.search(r"\('?(\w+)'?,?\)", error)
        if field_match:
            return f"validation_error_{field_match.group(1)}"

        return "validation_error"


class _EmptyResult:
    """Placeholder for empty batch results."""

    is_valid = True
    errors: List[str] = []
    quality = None
