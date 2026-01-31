"""
Quality Tracking Store - Storage backends for metrics.

Provides Protocol definition and implementations for storing
validation metrics.
"""

import json
import sqlite3
import threading
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

from pycharter.quality.tracking.models import MetricsFilter, MetricsSummary, ValidationMetric


class MetricsStore(Protocol):
    """
    Protocol for metrics storage backends.

    Implementations must provide methods for storing, querying,
    and summarizing validation metrics.
    """

    def store(self, metric: ValidationMetric) -> None:
        """Store a validation metric."""
        ...

    def query(self, filters: MetricsFilter) -> List[ValidationMetric]:
        """Query metrics with filters."""
        ...

    def get_summary(
        self, schema_name: str, window_hours: int = 24
    ) -> MetricsSummary:
        """Get aggregated summary for a schema within a time window."""
        ...

    def delete(self, metric_id: str) -> bool:
        """Delete a metric by ID. Returns True if deleted."""
        ...

    def clear(self, schema_name: Optional[str] = None) -> int:
        """Clear metrics. If schema_name provided, only clear that schema. Returns count deleted."""
        ...


class InMemoryMetricsStore:
    """
    In-memory metrics store for testing and development.

    Stores metrics in memory. Data is lost when the process ends.
    Thread-safe implementation.
    """

    def __init__(self, max_metrics: int = 10000):
        """
        Initialize in-memory store.

        Args:
            max_metrics: Maximum number of metrics to store (oldest removed when exceeded)
        """
        self._metrics: List[ValidationMetric] = []
        self._lock = threading.Lock()
        self._max_metrics = max_metrics

    def store(self, metric: ValidationMetric) -> None:
        """Store a validation metric."""
        with self._lock:
            self._metrics.append(metric)
            # Remove oldest if over limit
            if len(self._metrics) > self._max_metrics:
                self._metrics = self._metrics[-self._max_metrics :]

    def query(self, filters: MetricsFilter) -> List[ValidationMetric]:
        """Query metrics with filters."""
        with self._lock:
            results = self._metrics.copy()

        # Apply filters
        if filters.schema_name:
            results = [m for m in results if m.schema_name == filters.schema_name]
        if filters.version:
            results = [m for m in results if m.version == filters.version]
        if filters.since:
            results = [m for m in results if m.timestamp >= filters.since]
        if filters.until:
            results = [m for m in results if m.timestamp <= filters.until]
        if filters.min_validity_rate is not None:
            results = [m for m in results if m.validity_rate >= filters.min_validity_rate]

        # Sort by timestamp descending (most recent first)
        results.sort(key=lambda m: m.timestamp, reverse=True)

        # Apply pagination
        if filters.offset:
            results = results[filters.offset :]
        if filters.limit:
            results = results[: filters.limit]

        return results

    def get_summary(
        self, schema_name: str, window_hours: int = 24
    ) -> MetricsSummary:
        """Get aggregated summary for a schema within a time window."""
        cutoff = datetime.utcnow() - timedelta(hours=window_hours)

        filters = MetricsFilter(schema_name=schema_name, since=cutoff, limit=0)
        metrics = self.query(filters)

        if not metrics:
            return MetricsSummary(
                schema_name=schema_name,
                period_start=cutoff,
                period_end=datetime.utcnow(),
            )

        return self._compute_summary(schema_name, metrics, cutoff, datetime.utcnow())

    def _compute_summary(
        self,
        schema_name: str,
        metrics: List[ValidationMetric],
        period_start: datetime,
        period_end: datetime,
    ) -> MetricsSummary:
        """Compute summary statistics from a list of metrics."""
        if not metrics:
            return MetricsSummary(
                schema_name=schema_name,
                period_start=period_start,
                period_end=period_end,
            )

        total_validations = len(metrics)
        total_records = sum(m.record_count for m in metrics)
        total_valid = sum(m.valid_count for m in metrics)
        total_errors = sum(m.error_count for m in metrics)

        validity_rates = [m.validity_rate for m in metrics]
        avg_validity_rate = sum(validity_rates) / len(validity_rates)
        min_validity_rate = min(validity_rates)
        max_validity_rate = max(validity_rates)

        completeness_values = [m.completeness for m in metrics]
        avg_completeness = sum(completeness_values) / len(completeness_values)

        durations = [m.duration_ms for m in metrics]
        avg_duration_ms = sum(durations) / len(durations)

        # Aggregate error types
        error_counts: Dict[str, int] = defaultdict(int)
        for m in metrics:
            for error_type, count in m.errors_by_type.items():
                error_counts[error_type] += count

        # Get top 10 error types
        top_errors = dict(
            sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        )

        return MetricsSummary(
            schema_name=schema_name,
            period_start=period_start,
            period_end=period_end,
            total_validations=total_validations,
            total_records=total_records,
            total_valid=total_valid,
            total_errors=total_errors,
            avg_validity_rate=avg_validity_rate,
            min_validity_rate=min_validity_rate,
            max_validity_rate=max_validity_rate,
            avg_completeness=avg_completeness,
            avg_duration_ms=avg_duration_ms,
            top_error_types=top_errors,
        )

    def delete(self, metric_id: str) -> bool:
        """Delete a metric by ID."""
        with self._lock:
            original_len = len(self._metrics)
            self._metrics = [m for m in self._metrics if m.id != metric_id]
            return len(self._metrics) < original_len

    def clear(self, schema_name: Optional[str] = None) -> int:
        """Clear metrics."""
        with self._lock:
            if schema_name:
                original_len = len(self._metrics)
                self._metrics = [m for m in self._metrics if m.schema_name != schema_name]
                return original_len - len(self._metrics)
            else:
                count = len(self._metrics)
                self._metrics = []
                return count


class SQLiteMetricsStore:
    """
    SQLite-based persistent metrics store.

    Stores metrics in a SQLite database for persistence across restarts.
    Thread-safe implementation.
    """

    def __init__(self, db_path: str = "metrics.db"):
        """
        Initialize SQLite store.

        Args:
            db_path: Path to SQLite database file
        """
        self._db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS validation_metrics (
                    id TEXT PRIMARY KEY,
                    schema_name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    record_count INTEGER DEFAULT 0,
                    valid_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    validity_rate REAL DEFAULT 1.0,
                    completeness REAL DEFAULT 1.0,
                    field_completeness TEXT DEFAULT '{}',
                    duration_ms REAL DEFAULT 0.0,
                    errors_by_type TEXT DEFAULT '{}',
                    metadata TEXT DEFAULT '{}'
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_schema_name 
                ON validation_metrics(schema_name)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON validation_metrics(timestamp)
            """)
            conn.commit()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        return sqlite3.connect(self._db_path)

    def store(self, metric: ValidationMetric) -> None:
        """Store a validation metric."""
        with self._lock:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO validation_metrics 
                    (id, schema_name, version, timestamp, record_count, valid_count,
                     error_count, validity_rate, completeness, field_completeness,
                     duration_ms, errors_by_type, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        metric.id,
                        metric.schema_name,
                        metric.version,
                        metric.timestamp.isoformat(),
                        metric.record_count,
                        metric.valid_count,
                        metric.error_count,
                        metric.validity_rate,
                        metric.completeness,
                        json.dumps(metric.field_completeness),
                        metric.duration_ms,
                        json.dumps(metric.errors_by_type),
                        json.dumps(metric.metadata),
                    ),
                )
                conn.commit()

    def query(self, filters: MetricsFilter) -> List[ValidationMetric]:
        """Query metrics with filters."""
        conditions = []
        params: List[Any] = []

        if filters.schema_name:
            conditions.append("schema_name = ?")
            params.append(filters.schema_name)
        if filters.version:
            conditions.append("version = ?")
            params.append(filters.version)
        if filters.since:
            conditions.append("timestamp >= ?")
            params.append(filters.since.isoformat())
        if filters.until:
            conditions.append("timestamp <= ?")
            params.append(filters.until.isoformat())
        if filters.min_validity_rate is not None:
            conditions.append("validity_rate >= ?")
            params.append(filters.min_validity_rate)

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"""
            SELECT * FROM validation_metrics 
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """
        params.extend([filters.limit, filters.offset])

        with self._lock:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()

        return [self._row_to_metric(row) for row in rows]

    def _row_to_metric(self, row: sqlite3.Row) -> ValidationMetric:
        """Convert database row to ValidationMetric."""
        return ValidationMetric(
            id=row["id"],
            schema_name=row["schema_name"],
            version=row["version"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            record_count=row["record_count"],
            valid_count=row["valid_count"],
            error_count=row["error_count"],
            validity_rate=row["validity_rate"],
            completeness=row["completeness"],
            field_completeness=json.loads(row["field_completeness"]),
            duration_ms=row["duration_ms"],
            errors_by_type=json.loads(row["errors_by_type"]),
            metadata=json.loads(row["metadata"]),
        )

    def get_summary(
        self, schema_name: str, window_hours: int = 24
    ) -> MetricsSummary:
        """Get aggregated summary for a schema within a time window."""
        cutoff = datetime.utcnow() - timedelta(hours=window_hours)

        filters = MetricsFilter(
            schema_name=schema_name, since=cutoff, limit=10000  # Get all for summary
        )
        metrics = self.query(filters)

        if not metrics:
            return MetricsSummary(
                schema_name=schema_name,
                period_start=cutoff,
                period_end=datetime.utcnow(),
            )

        # Reuse InMemoryMetricsStore's compute logic
        return InMemoryMetricsStore()._compute_summary(
            schema_name, metrics, cutoff, datetime.utcnow()
        )

    def delete(self, metric_id: str) -> bool:
        """Delete a metric by ID."""
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "DELETE FROM validation_metrics WHERE id = ?", (metric_id,)
                )
                conn.commit()
                return cursor.rowcount > 0

    def clear(self, schema_name: Optional[str] = None) -> int:
        """Clear metrics."""
        with self._lock:
            with self._get_connection() as conn:
                if schema_name:
                    cursor = conn.execute(
                        "DELETE FROM validation_metrics WHERE schema_name = ?",
                        (schema_name,),
                    )
                else:
                    cursor = conn.execute("DELETE FROM validation_metrics")
                conn.commit()
                return cursor.rowcount
