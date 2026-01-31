"""
Cloud storage loader for ETL pipelines.
"""

import time
from typing import Any, Dict, List, Optional

from pycharter.etl_generator.loaders.base import BaseLoader
from pycharter.etl_generator.loaders.cloud_storage_loader import load_to_cloud_storage
from pycharter.etl_generator.result import LoadResult


class CloudStorageLoader(BaseLoader):
    """
    Loader for cloud storage (S3, GCS, Azure).
    
    Supports JSON, CSV, Parquet, and JSONL formats.
    
    Example:
        >>> loader = CloudStorageLoader(
        ...     provider="s3",
        ...     bucket="my-bucket",
        ...     path="output/data.json",
        ...     format="json",
        ... )
        >>> result = await loader.load(data)
    """
    
    def __init__(
        self,
        provider: str,
        bucket: str,
        path: str,
        credentials: Optional[Dict[str, Any]] = None,
        file_format: str = "json",
    ):
        self.provider = provider
        self.bucket = bucket
        self.path = path
        self.credentials = credentials
        self.file_format = file_format
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "CloudStorageLoader":
        """Create loader from configuration dict."""
        storage_config = config.get("storage", {})
        return cls(
            provider=storage_config.get("provider") or config.get("provider"),
            bucket=storage_config.get("bucket") or config.get("bucket"),
            path=storage_config.get("path") or config.get("path"),
            credentials=storage_config.get("credentials") or config.get("credentials"),
            file_format=config.get("format", "json"),
        )
    
    async def load(self, data: List[Dict[str, Any]], **params) -> LoadResult:
        """Load data to cloud storage."""
        start_time = time.time()
        
        if not data:
            return LoadResult(success=True, rows_loaded=0)
        
        try:
            load_config = {
                "storage": {
                    "provider": self.provider,
                    "bucket": self.bucket,
                    "path": self.path,
                    "credentials": self.credentials,
                },
                "format": self.file_format,
            }
            
            result = load_to_cloud_storage(data, load_config)
            
            duration = time.time() - start_time
            return LoadResult(
                success=True,
                rows_loaded=result.get("written", 0),
                duration_seconds=duration,
            )
        
        except Exception as e:
            return LoadResult(
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time,
            )
