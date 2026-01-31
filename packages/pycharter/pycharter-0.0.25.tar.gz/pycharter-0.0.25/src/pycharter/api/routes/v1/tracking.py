"""
API routes for quality tracking (time-series metrics).

Provides endpoints to query, record, and export validation metrics
for quality monitoring and trend analysis.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from pycharter.api.models.tracking import (
    ExportFormat,
    ExportResponse,
    MetricsQueryResponse,
    MetricsSummaryResponse,
    RecordMetricRequest,
    SchemaListResponse,
    ValidationMetricResponse,
)
from pycharter.quality.tracking import (
    MetricsCollector,
    InMemoryMetricsStore,
    ValidationMetric,
    export_json,
    export_prometheus,
)
from pycharter.quality.tracking.exporters import export_csv

router = APIRouter(prefix="/quality/tracking", tags=["Quality Tracking"])

# Global metrics collector (in production, this would be configured via dependency injection)
# For now, use in-memory store that persists for the lifetime of the API
_store = InMemoryMetricsStore(max_metrics=50000)
_collector = MetricsCollector(_store)


def get_collector() -> MetricsCollector:
    """Get the global metrics collector."""
    return _collector


@router.get(
    "",
    response_model=MetricsQueryResponse,
    summary="Query validation metrics",
    description="Query validation metrics with optional filters for schema, time range, and quality thresholds",
)
async def query_metrics(
    schema_name: Optional[str] = Query(default=None, description="Filter by schema name"),
    version: Optional[str] = Query(default=None, description="Filter by schema version"),
    since: Optional[datetime] = Query(default=None, description="Filter metrics after this time"),
    until: Optional[datetime] = Query(default=None, description="Filter metrics before this time"),
    min_validity_rate: Optional[float] = Query(
        default=None, ge=0.0, le=1.0, description="Filter by minimum validity rate"
    ),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum results to return"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
) -> MetricsQueryResponse:
    """
    Query validation metrics with filters.

    Returns metrics ordered by timestamp (most recent first).
    """
    collector = get_collector()

    metrics = collector.query(
        schema_name=schema_name,
        version=version,
        since=since,
        until=until,
        min_validity_rate=min_validity_rate,
        limit=limit,
        offset=offset,
    )

    # Get total count (without pagination)
    all_metrics = collector.query(
        schema_name=schema_name,
        version=version,
        since=since,
        until=until,
        min_validity_rate=min_validity_rate,
        limit=0,  # No limit to get total count
    )

    return MetricsQueryResponse(
        metrics=[
            ValidationMetricResponse(
                id=m.id,
                schema_name=m.schema_name,
                version=m.version,
                timestamp=m.timestamp,
                record_count=m.record_count,
                valid_count=m.valid_count,
                error_count=m.error_count,
                validity_rate=m.validity_rate,
                completeness=m.completeness,
                field_completeness=m.field_completeness,
                duration_ms=m.duration_ms,
                errors_by_type=m.errors_by_type,
                metadata=m.metadata,
            )
            for m in metrics
        ],
        total=len(all_metrics),
        limit=limit,
        offset=offset,
    )


@router.get(
    "/schemas",
    response_model=SchemaListResponse,
    summary="List schemas with metrics",
    description="Get list of all schema names that have recorded metrics",
)
async def list_schemas() -> SchemaListResponse:
    """Get list of all schemas with recorded metrics."""
    collector = get_collector()
    schemas = collector.get_all_schemas()
    return SchemaListResponse(schemas=sorted(schemas))


@router.get(
    "/{schema_name}/summary",
    response_model=MetricsSummaryResponse,
    summary="Get metrics summary for a schema",
    description="Get aggregated metrics summary for a schema within a time window",
)
async def get_summary(
    schema_name: str,
    window_hours: int = Query(default=24, ge=1, le=720, description="Hours to look back"),
) -> MetricsSummaryResponse:
    """
    Get aggregated summary for a schema.

    Returns aggregated statistics for all validation runs
    within the specified time window.
    """
    collector = get_collector()
    summary = collector.get_summary(schema_name, window_hours=window_hours)

    return MetricsSummaryResponse(
        schema_name=summary.schema_name,
        period_start=summary.period_start,
        period_end=summary.period_end,
        total_validations=summary.total_validations,
        total_records=summary.total_records,
        total_valid=summary.total_valid,
        total_errors=summary.total_errors,
        avg_validity_rate=summary.avg_validity_rate,
        min_validity_rate=summary.min_validity_rate,
        max_validity_rate=summary.max_validity_rate,
        avg_completeness=summary.avg_completeness,
        avg_duration_ms=summary.avg_duration_ms,
        overall_validity_rate=summary.overall_validity_rate,
        top_error_types=summary.top_error_types,
    )


@router.post(
    "",
    response_model=ValidationMetricResponse,
    summary="Record a validation metric",
    description="Manually record a validation metric (typically called by validation services)",
)
async def record_metric(request: RecordMetricRequest) -> ValidationMetricResponse:
    """
    Record a validation metric.

    This endpoint allows external services to record validation metrics.
    Typically used by validation pipelines or batch processes.
    """
    collector = get_collector()

    # Calculate validity rate if not provided
    validity_rate = request.validity_rate
    if validity_rate is None:
        if request.record_count > 0:
            validity_rate = request.valid_count / request.record_count
        else:
            validity_rate = 1.0

    # Create and store the metric
    metric = ValidationMetric(
        schema_name=request.schema_name,
        version=request.version,
        record_count=request.record_count,
        valid_count=request.valid_count,
        error_count=request.error_count,
        validity_rate=validity_rate,
        completeness=request.completeness,
        field_completeness=request.field_completeness,
        duration_ms=request.duration_ms,
        errors_by_type=request.errors_by_type,
        metadata=request.metadata,
    )

    collector.store.store(metric)

    return ValidationMetricResponse(
        id=metric.id,
        schema_name=metric.schema_name,
        version=metric.version,
        timestamp=metric.timestamp,
        record_count=metric.record_count,
        valid_count=metric.valid_count,
        error_count=metric.error_count,
        validity_rate=metric.validity_rate,
        completeness=metric.completeness,
        field_completeness=metric.field_completeness,
        duration_ms=metric.duration_ms,
        errors_by_type=metric.errors_by_type,
        metadata=metric.metadata,
    )


@router.get(
    "/export",
    response_model=ExportResponse,
    summary="Export metrics",
    description="Export metrics in various formats (JSON, Prometheus, CSV)",
)
async def export_metrics(
    format: ExportFormat = Query(default=ExportFormat.JSON, description="Export format"),
    schema_name: Optional[str] = Query(default=None, description="Filter by schema name"),
    since: Optional[datetime] = Query(default=None, description="Filter metrics after this time"),
    limit: int = Query(default=1000, ge=1, le=10000, description="Maximum metrics to export"),
) -> ExportResponse:
    """
    Export metrics in the specified format.

    Supported formats:
    - json: JSON array of metrics
    - prometheus: Prometheus text format for scraping
    - csv: CSV format for spreadsheet analysis
    """
    collector = get_collector()

    metrics = collector.query(
        schema_name=schema_name,
        since=since,
        limit=limit,
    )

    if format == ExportFormat.JSON:
        data = export_json(metrics)
    elif format == ExportFormat.PROMETHEUS:
        # Include summaries for Prometheus export
        schemas = collector.get_all_schemas()
        if schema_name:
            schemas = [schema_name]
        summaries = [collector.get_summary(s) for s in schemas]
        data = export_prometheus(metrics, summaries=summaries)
    elif format == ExportFormat.CSV:
        data = export_csv(metrics)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

    return ExportResponse(
        format=format,
        data=data,
        count=len(metrics),
    )


@router.delete(
    "/{metric_id}",
    summary="Delete a metric",
    description="Delete a specific metric by ID",
)
async def delete_metric(metric_id: str) -> dict:
    """Delete a metric by ID."""
    collector = get_collector()
    deleted = collector.store.delete(metric_id)

    if not deleted:
        raise HTTPException(status_code=404, detail=f"Metric not found: {metric_id}")

    return {"deleted": True, "id": metric_id}


@router.delete(
    "",
    summary="Clear metrics",
    description="Clear all metrics or metrics for a specific schema",
)
async def clear_metrics(
    schema_name: Optional[str] = Query(default=None, description="Schema to clear (all if not specified)"),
) -> dict:
    """Clear metrics."""
    collector = get_collector()
    count = collector.store.clear(schema_name)

    return {
        "cleared": True,
        "count": count,
        "schema_name": schema_name or "all",
    }
