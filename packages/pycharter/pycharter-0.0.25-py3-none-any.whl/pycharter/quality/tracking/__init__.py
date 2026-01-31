"""
Quality Tracking - Time-series metrics collection and analysis.

This submodule provides tools for tracking validation metrics over time,
enabling trend analysis and quality monitoring.

Primary Interface:
    - MetricsCollector: Collect and query validation metrics
    - ValidationMetric: Single validation run metric
    - MetricsSummary: Aggregated metrics summary

Stores:
    - MetricsStore: Protocol for metrics storage backends
    - InMemoryMetricsStore: In-memory store for testing/development
    - SQLiteMetricsStore: SQLite-based persistent storage

Exporters:
    - export_json: Export metrics as JSON
    - export_prometheus: Export metrics in Prometheus format

Example:
    >>> from pycharter.quality.tracking import MetricsCollector, InMemoryMetricsStore
    >>>
    >>> # Create collector with in-memory store
    >>> store = InMemoryMetricsStore()
    >>> collector = MetricsCollector(store)
    >>>
    >>> # Record validation results
    >>> result = validator.validate(data)
    >>> collector.record(result, schema_name="users", version="1.0.0")
    >>>
    >>> # Query metrics
    >>> metrics = collector.query(schema_name="users", limit=10)
    >>> summary = collector.get_summary("users")
"""

from pycharter.quality.tracking.collector import MetricsCollector
from pycharter.quality.tracking.models import (
    MetricsFilter,
    MetricsSummary,
    ValidationMetric,
)
from pycharter.quality.tracking.store import (
    InMemoryMetricsStore,
    MetricsStore,
    SQLiteMetricsStore,
)
from pycharter.quality.tracking.exporters import export_json, export_prometheus

__all__ = [
    # Primary interface
    "MetricsCollector",
    # Models
    "ValidationMetric",
    "MetricsSummary",
    "MetricsFilter",
    # Stores
    "MetricsStore",
    "InMemoryMetricsStore",
    "SQLiteMetricsStore",
    # Exporters
    "export_json",
    "export_prometheus",
]
