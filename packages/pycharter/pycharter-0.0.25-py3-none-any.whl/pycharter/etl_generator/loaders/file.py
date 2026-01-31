"""
File loader for ETL pipelines.
"""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from pycharter.etl_generator.loaders.base import BaseLoader
from pycharter.etl_generator.loaders.file_loader import load_to_file
from pycharter.etl_generator.result import LoadResult


class FileLoader(BaseLoader):
    """
    Loader for local files.
    
    Supports JSON, CSV, Parquet, and JSONL formats.
    
    Example:
        >>> loader = FileLoader(path="output/data.json", format="json")
        >>> result = await loader.load(data)
    """
    
    def __init__(
        self,
        path: str,
        file_format: str = "json",
        write_mode: str = "overwrite",
    ):
        self.path = path
        self.file_format = file_format
        self.write_mode = write_mode
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "FileLoader":
        """Create loader from configuration dict."""
        return cls(
            path=config.get("file_path") or config.get("path"),
            file_format=config.get("format", "json"),
            write_mode=config.get("write_mode", "overwrite"),
        )
    
    async def load(self, data: List[Dict[str, Any]], **params) -> LoadResult:
        """Load data to file."""
        start_time = time.time()
        
        if not data:
            return LoadResult(success=True, rows_loaded=0)
        
        try:
            load_config = {
                "file_path": self.path,
                "format": self.file_format,
                "write_mode": self.write_mode,
            }
            
            result = load_to_file(data, load_config)
            
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
