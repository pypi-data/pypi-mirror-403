"""
Quality Tracking Exporters - Export metrics in various formats.

Provides functions to export validation metrics in different
formats for external consumption.
"""

import json
from datetime import datetime
from typing import List, Optional

from pycharter.quality.tracking.models import MetricsSummary, ValidationMetric


def export_json(
    metrics: List[ValidationMetric],
    pretty: bool = True,
    include_metadata: bool = True,
) -> str:
    """
    Export metrics as JSON.

    Args:
        metrics: List of ValidationMetrics to export
        pretty: If True, format with indentation
        include_metadata: If True, include metric metadata

    Returns:
        JSON string representation of metrics
    """
    data = []
    for m in metrics:
        metric_dict = m.to_dict()
        if not include_metadata:
            metric_dict.pop("metadata", None)
        data.append(metric_dict)

    if pretty:
        return json.dumps(data, indent=2, default=str)
    return json.dumps(data, default=str)


def export_prometheus(
    metrics: List[ValidationMetric],
    summaries: Optional[List[MetricsSummary]] = None,
    prefix: str = "pycharter",
) -> str:
    """
    Export metrics in Prometheus text format.

    Generates Prometheus-compatible metrics that can be scraped
    by a Prometheus server or used with pushgateway.

    Args:
        metrics: List of ValidationMetrics to export
        summaries: Optional list of MetricsSummaries to export
        prefix: Metric name prefix

    Returns:
        Prometheus text format string

    Example output:
        # HELP pycharter_validation_total Total validation runs
        # TYPE pycharter_validation_total counter
        pycharter_validation_total{schema="users",version="1.0.0"} 100
    """
    lines = []
    timestamp_ms = int(datetime.utcnow().timestamp() * 1000)

    # Helper to format labels
    def format_labels(labels: dict) -> str:
        parts = [f'{k}="{v}"' for k, v in labels.items()]
        return "{" + ",".join(parts) + "}"

    # Aggregate metrics by schema for summary metrics
    schema_metrics: dict = {}
    for m in metrics:
        key = (m.schema_name, m.version)
        if key not in schema_metrics:
            schema_metrics[key] = {
                "record_count": 0,
                "valid_count": 0,
                "error_count": 0,
                "validity_rates": [],
                "completeness_values": [],
                "durations": [],
                "latest": m,
            }
        data = schema_metrics[key]
        data["record_count"] += m.record_count
        data["valid_count"] += m.valid_count
        data["error_count"] += m.error_count
        data["validity_rates"].append(m.validity_rate)
        data["completeness_values"].append(m.completeness)
        data["durations"].append(m.duration_ms)
        if m.timestamp > data["latest"].timestamp:
            data["latest"] = m

    # Total validations counter
    lines.append(f"# HELP {prefix}_validations_total Total number of validation runs")
    lines.append(f"# TYPE {prefix}_validations_total counter")
    for (schema, version), data in schema_metrics.items():
        labels = format_labels({"schema": schema, "version": version})
        lines.append(f"{prefix}_validations_total{labels} {len(data['validity_rates'])}")

    lines.append("")

    # Total records processed
    lines.append(f"# HELP {prefix}_records_total Total number of records processed")
    lines.append(f"# TYPE {prefix}_records_total counter")
    for (schema, version), data in schema_metrics.items():
        labels = format_labels({"schema": schema, "version": version})
        lines.append(f"{prefix}_records_total{labels} {data['record_count']}")

    lines.append("")

    # Valid records counter
    lines.append(f"# HELP {prefix}_valid_records_total Total number of valid records")
    lines.append(f"# TYPE {prefix}_valid_records_total counter")
    for (schema, version), data in schema_metrics.items():
        labels = format_labels({"schema": schema, "version": version})
        lines.append(f"{prefix}_valid_records_total{labels} {data['valid_count']}")

    lines.append("")

    # Error records counter
    lines.append(f"# HELP {prefix}_error_records_total Total number of records with errors")
    lines.append(f"# TYPE {prefix}_error_records_total counter")
    for (schema, version), data in schema_metrics.items():
        labels = format_labels({"schema": schema, "version": version})
        lines.append(f"{prefix}_error_records_total{labels} {data['error_count']}")

    lines.append("")

    # Validity rate gauge (latest value)
    lines.append(f"# HELP {prefix}_validity_rate Current validity rate")
    lines.append(f"# TYPE {prefix}_validity_rate gauge")
    for (schema, version), data in schema_metrics.items():
        labels = format_labels({"schema": schema, "version": version})
        latest_rate = data["latest"].validity_rate
        lines.append(f"{prefix}_validity_rate{labels} {latest_rate:.6f}")

    lines.append("")

    # Completeness gauge (latest value)
    lines.append(f"# HELP {prefix}_completeness Current data completeness")
    lines.append(f"# TYPE {prefix}_completeness gauge")
    for (schema, version), data in schema_metrics.items():
        labels = format_labels({"schema": schema, "version": version})
        latest_completeness = data["latest"].completeness
        lines.append(f"{prefix}_completeness{labels} {latest_completeness:.6f}")

    lines.append("")

    # Validation duration (latest value)
    lines.append(f"# HELP {prefix}_validation_duration_ms Validation duration in milliseconds")
    lines.append(f"# TYPE {prefix}_validation_duration_ms gauge")
    for (schema, version), data in schema_metrics.items():
        labels = format_labels({"schema": schema, "version": version})
        latest_duration = data["latest"].duration_ms
        lines.append(f"{prefix}_validation_duration_ms{labels} {latest_duration:.3f}")

    lines.append("")

    # Average validity rate
    lines.append(f"# HELP {prefix}_validity_rate_avg Average validity rate")
    lines.append(f"# TYPE {prefix}_validity_rate_avg gauge")
    for (schema, version), data in schema_metrics.items():
        labels = format_labels({"schema": schema, "version": version})
        avg_rate = sum(data["validity_rates"]) / len(data["validity_rates"])
        lines.append(f"{prefix}_validity_rate_avg{labels} {avg_rate:.6f}")

    # Include summary metrics if provided
    if summaries:
        lines.append("")
        lines.append(f"# HELP {prefix}_summary_total_validations Total validations in summary period")
        lines.append(f"# TYPE {prefix}_summary_total_validations gauge")
        for s in summaries:
            labels = format_labels({"schema": s.schema_name})
            lines.append(f"{prefix}_summary_total_validations{labels} {s.total_validations}")

        lines.append("")
        lines.append(f"# HELP {prefix}_summary_avg_validity_rate Average validity rate in summary period")
        lines.append(f"# TYPE {prefix}_summary_avg_validity_rate gauge")
        for s in summaries:
            labels = format_labels({"schema": s.schema_name})
            lines.append(f"{prefix}_summary_avg_validity_rate{labels} {s.avg_validity_rate:.6f}")

    return "\n".join(lines) + "\n"


def export_csv(
    metrics: List[ValidationMetric],
    include_header: bool = True,
) -> str:
    """
    Export metrics as CSV.

    Args:
        metrics: List of ValidationMetrics to export
        include_header: If True, include header row

    Returns:
        CSV string representation of metrics
    """
    columns = [
        "id",
        "schema_name",
        "version",
        "timestamp",
        "record_count",
        "valid_count",
        "error_count",
        "validity_rate",
        "completeness",
        "duration_ms",
    ]

    lines = []
    if include_header:
        lines.append(",".join(columns))

    for m in metrics:
        row = [
            m.id,
            m.schema_name,
            m.version,
            m.timestamp.isoformat(),
            str(m.record_count),
            str(m.valid_count),
            str(m.error_count),
            f"{m.validity_rate:.6f}",
            f"{m.completeness:.6f}",
            f"{m.duration_ms:.3f}",
        ]
        lines.append(",".join(row))

    return "\n".join(lines) + "\n"
