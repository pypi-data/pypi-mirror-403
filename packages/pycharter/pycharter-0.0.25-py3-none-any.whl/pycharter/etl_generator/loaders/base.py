"""
Base loader class for ETL pipelines.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from pycharter.etl_generator.result import LoadResult


class BaseLoader(ABC):
    """
    Base class for data loaders.
    
    All loaders must implement the async load() method.
    """
    
    @abstractmethod
    async def load(self, data: List[Dict[str, Any]], **params) -> LoadResult:
        """
        Load data to the destination.
        
        Args:
            data: List of records to load
            **params: Additional load parameters
            
        Returns:
            LoadResult with loading statistics
        """
        ...
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "BaseLoader":
        """Create loader from configuration dict."""
        raise NotImplementedError("Subclasses must implement from_config")
