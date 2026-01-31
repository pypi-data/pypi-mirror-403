"""
Protocol definitions for ETL components.

Uses Python's Protocol for structural subtyping (duck typing with type hints).
"""

from typing import Any, AsyncIterator, Dict, List, Protocol, runtime_checkable

from pycharter.etl_generator.result import LoadResult


@runtime_checkable
class Extractor(Protocol):
    """
    Protocol for data extractors.
    
    Extractors read data from sources (HTTP, files, databases, cloud storage)
    and yield batches of records.
    """
    
    async def extract(self, **params) -> AsyncIterator[List[Dict[str, Any]]]:
        """
        Extract data from the source.
        
        Yields:
            Batches of records (list of dicts)
        """
        ...


@runtime_checkable
class Transformer(Protocol):
    """
    Protocol for data transformers.
    
    Transformers process batches of records. They can be chained with |.
    """
    
    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform a batch of records."""
        ...


@runtime_checkable
class Loader(Protocol):
    """
    Protocol for data loaders.
    
    Loaders write data to destinations (databases, files, cloud storage).
    """
    
    async def load(self, data: List[Dict[str, Any]], **params) -> LoadResult:
        """Load data to the destination."""
        ...
