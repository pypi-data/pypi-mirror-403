"""
Quality Tracking Models - Data models for metrics tracking.

Defines the core data structures for validation metrics
and aggregated summaries.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ValidationMetric:
    """
    Single validation run metric.

    Captures all relevant metrics from a single validation operation
    for time-series tracking and analysis.

    Attributes:
        id: Unique identifier for this metric
        schema_name: Name of the schema validated against
        version: Version of the schema
        timestamp: When the validation occurred
        record_count: Number of records validated
        valid_count: Number of valid records
        error_count: Number of records with errors
        validity_rate: Ratio of valid records (0.0 to 1.0)
        completeness: Overall data completeness (0.0 to 1.0)
        field_completeness: Per-field completeness ratios
        duration_ms: Validation duration in milliseconds
        errors_by_type: Count of errors by error type
        metadata: Additional custom metadata
    """

    schema_name: str
    version: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    record_count: int = 0
    valid_count: int = 0
    error_count: int = 0
    validity_rate: float = 1.0
    completeness: float = 1.0
    field_completeness: Dict[str, float] = field(default_factory=dict)
    duration_ms: float = 0.0
    errors_by_type: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "schema_name": self.schema_name,
            "version": self.version,
            "timestamp": self.timestamp.isoformat(),
            "record_count": self.record_count,
            "valid_count": self.valid_count,
            "error_count": self.error_count,
            "validity_rate": self.validity_rate,
            "completeness": self.completeness,
            "field_completeness": self.field_completeness,
            "duration_ms": self.duration_ms,
            "errors_by_type": self.errors_by_type,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ValidationMetric":
        """Create from dictionary."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.utcnow()

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            schema_name=data["schema_name"],
            version=data["version"],
            timestamp=timestamp,
            record_count=data.get("record_count", 0),
            valid_count=data.get("valid_count", 0),
            error_count=data.get("error_count", 0),
            validity_rate=data.get("validity_rate", 1.0),
            completeness=data.get("completeness", 1.0),
            field_completeness=data.get("field_completeness", {}),
            duration_ms=data.get("duration_ms", 0.0),
            errors_by_type=data.get("errors_by_type", {}),
            metadata=data.get("metadata", {}),
        )


@dataclass
class MetricsSummary:
    """
    Aggregated metrics summary for a schema over a time period.

    Provides statistical aggregations of validation metrics
    for trend analysis and monitoring.

    Attributes:
        schema_name: Name of the schema
        period_start: Start of the summary period
        period_end: End of the summary period
        total_validations: Total number of validation runs
        total_records: Total number of records validated
        total_valid: Total number of valid records
        total_errors: Total number of errors
        avg_validity_rate: Average validity rate
        min_validity_rate: Minimum validity rate
        max_validity_rate: Maximum validity rate
        avg_completeness: Average completeness
        avg_duration_ms: Average validation duration
        top_error_types: Most common error types with counts
    """

    schema_name: str
    period_start: datetime
    period_end: datetime
    total_validations: int = 0
    total_records: int = 0
    total_valid: int = 0
    total_errors: int = 0
    avg_validity_rate: float = 0.0
    min_validity_rate: float = 1.0
    max_validity_rate: float = 0.0
    avg_completeness: float = 0.0
    avg_duration_ms: float = 0.0
    top_error_types: Dict[str, int] = field(default_factory=dict)

    @property
    def overall_validity_rate(self) -> float:
        """Calculate overall validity rate from totals."""
        if self.total_records == 0:
            return 1.0
        return self.total_valid / self.total_records

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "schema_name": self.schema_name,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "total_validations": self.total_validations,
            "total_records": self.total_records,
            "total_valid": self.total_valid,
            "total_errors": self.total_errors,
            "avg_validity_rate": self.avg_validity_rate,
            "min_validity_rate": self.min_validity_rate,
            "max_validity_rate": self.max_validity_rate,
            "avg_completeness": self.avg_completeness,
            "avg_duration_ms": self.avg_duration_ms,
            "overall_validity_rate": self.overall_validity_rate,
            "top_error_types": self.top_error_types,
        }


@dataclass
class MetricsFilter:
    """
    Filter criteria for querying metrics.

    Attributes:
        schema_name: Filter by schema name
        version: Filter by schema version
        since: Filter metrics after this time
        until: Filter metrics before this time
        min_validity_rate: Filter by minimum validity rate
        limit: Maximum number of results
        offset: Offset for pagination
    """

    schema_name: Optional[str] = None
    version: Optional[str] = None
    since: Optional[datetime] = None
    until: Optional[datetime] = None
    min_validity_rate: Optional[float] = None
    limit: int = 100
    offset: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (for serialization)."""
        return {
            "schema_name": self.schema_name,
            "version": self.version,
            "since": self.since.isoformat() if self.since else None,
            "until": self.until.isoformat() if self.until else None,
            "min_validity_rate": self.min_validity_rate,
            "limit": self.limit,
            "offset": self.offset,
        }
