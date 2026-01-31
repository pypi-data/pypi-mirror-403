"""
API models for quality tracking endpoints.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ExportFormat(str, Enum):
    """Supported export formats."""

    JSON = "json"
    PROMETHEUS = "prometheus"
    CSV = "csv"


class ValidationMetricResponse(BaseModel):
    """Response model for a single validation metric."""

    id: str = Field(..., description="Unique metric identifier")
    schema_name: str = Field(..., description="Name of the schema validated")
    version: str = Field(..., description="Version of the schema")
    timestamp: datetime = Field(..., description="When the validation occurred")
    record_count: int = Field(..., description="Number of records validated")
    valid_count: int = Field(..., description="Number of valid records")
    error_count: int = Field(..., description="Number of records with errors")
    validity_rate: float = Field(..., description="Ratio of valid records (0.0 to 1.0)")
    completeness: float = Field(..., description="Data completeness ratio (0.0 to 1.0)")
    field_completeness: Dict[str, float] = Field(
        default_factory=dict, description="Per-field completeness ratios"
    )
    duration_ms: float = Field(..., description="Validation duration in milliseconds")
    errors_by_type: Dict[str, int] = Field(
        default_factory=dict, description="Error counts by type"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class MetricsSummaryResponse(BaseModel):
    """Response model for aggregated metrics summary."""

    schema_name: str = Field(..., description="Name of the schema")
    period_start: datetime = Field(..., description="Start of the summary period")
    period_end: datetime = Field(..., description="End of the summary period")
    total_validations: int = Field(..., description="Total validation runs in period")
    total_records: int = Field(..., description="Total records validated")
    total_valid: int = Field(..., description="Total valid records")
    total_errors: int = Field(..., description="Total records with errors")
    avg_validity_rate: float = Field(..., description="Average validity rate")
    min_validity_rate: float = Field(..., description="Minimum validity rate")
    max_validity_rate: float = Field(..., description="Maximum validity rate")
    avg_completeness: float = Field(..., description="Average completeness")
    avg_duration_ms: float = Field(..., description="Average validation duration")
    overall_validity_rate: float = Field(..., description="Overall validity rate from totals")
    top_error_types: Dict[str, int] = Field(
        default_factory=dict, description="Most common error types"
    )


class MetricsQueryResponse(BaseModel):
    """Response model for metrics query."""

    metrics: List[ValidationMetricResponse] = Field(
        ..., description="List of matching metrics"
    )
    total: int = Field(..., description="Total number of metrics matching filters")
    limit: int = Field(..., description="Maximum results returned")
    offset: int = Field(..., description="Pagination offset")


class RecordMetricRequest(BaseModel):
    """Request model for recording a validation metric."""

    schema_name: str = Field(..., description="Name of the schema validated")
    version: str = Field(..., description="Version of the schema")
    record_count: int = Field(default=1, description="Number of records validated")
    valid_count: int = Field(default=1, description="Number of valid records")
    error_count: int = Field(default=0, description="Number of records with errors")
    validity_rate: Optional[float] = Field(
        default=None, description="Validity rate (calculated if not provided)"
    )
    completeness: float = Field(default=1.0, description="Data completeness")
    field_completeness: Dict[str, float] = Field(
        default_factory=dict, description="Per-field completeness"
    )
    duration_ms: float = Field(default=0.0, description="Validation duration")
    errors_by_type: Dict[str, int] = Field(
        default_factory=dict, description="Error counts by type"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class ExportResponse(BaseModel):
    """Response model for metrics export."""

    format: ExportFormat = Field(..., description="Export format used")
    data: str = Field(..., description="Exported data as string")
    count: int = Field(..., description="Number of metrics exported")


class SchemaListResponse(BaseModel):
    """Response model for list of schemas with metrics."""

    schemas: List[str] = Field(..., description="List of schema names with recorded metrics")
