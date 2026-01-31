"""
Data Quality Assurance Module

Provides quality checking, metrics calculation, violation tracking, and reporting
for data contracts.

Submodules:
    - tracking: Time-series metrics collection and analysis
"""

from pycharter.quality.check import QualityCheck
from pycharter.quality.metrics import QualityMetrics, QualityScore
from pycharter.quality.models import (
    FieldQualityMetrics,
    QualityCheckOptions,
    QualityReport,
    QualityThresholds,
)
from pycharter.quality.profiling import DataProfiler
from pycharter.quality.violations import ViolationRecord, ViolationTracker

# Tracking submodule exports
from pycharter.quality import tracking
from pycharter.quality.tracking import (
    MetricsCollector,
    ValidationMetric,
    MetricsSummary,
    MetricsFilter,
    MetricsStore,
    InMemoryMetricsStore,
    SQLiteMetricsStore,
)

__all__ = [
    # Quality checking
    "QualityCheck",
    "QualityMetrics",
    "QualityScore",
    "QualityReport",
    "QualityThresholds",
    "QualityCheckOptions",
    "FieldQualityMetrics",
    "ViolationTracker",
    "ViolationRecord",
    "DataProfiler",
    # Tracking submodule
    "tracking",
    "MetricsCollector",
    "ValidationMetric",
    "MetricsSummary",
    "MetricsFilter",
    "MetricsStore",
    "InMemoryMetricsStore",
    "SQLiteMetricsStore",
]

