"""
Result classes for ETL operations.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class LoadResult:
    """Result from a load operation."""
    success: bool = True
    rows_loaded: int = 0
    rows_failed: int = 0
    error: Optional[str] = None
    duration_seconds: Optional[float] = None


@dataclass
class BatchResult:
    """Result from processing a single batch."""
    batch_index: int
    rows_in: int = 0
    rows_out: int = 0
    rows_failed: int = 0
    errors: List[str] = field(default_factory=list)
    
    @property
    def success(self) -> bool:
        return len(self.errors) == 0 and self.rows_failed == 0


@dataclass
class PipelineResult:
    """Complete result from running an ETL pipeline."""
    success: bool = True
    rows_extracted: int = 0
    rows_transformed: int = 0
    rows_loaded: int = 0
    rows_failed: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    batches_processed: int = 0
    batch_results: List[BatchResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    pipeline_name: Optional[str] = None
    run_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "rows_extracted": self.rows_extracted,
            "rows_transformed": self.rows_transformed,
            "rows_loaded": self.rows_loaded,
            "rows_failed": self.rows_failed,
            "duration_seconds": self.duration_seconds,
            "batches_processed": self.batches_processed,
            "errors": self.errors,
            "pipeline_name": self.pipeline_name,
            "run_id": self.run_id,
        }
