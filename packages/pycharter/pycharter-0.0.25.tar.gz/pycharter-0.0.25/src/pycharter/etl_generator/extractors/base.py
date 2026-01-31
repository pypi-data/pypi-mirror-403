"""
Base extractor interface for ETL orchestrator.

All extractors must implement this interface to ensure consistent behavior
across different data sources.
"""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional


class BaseExtractor(ABC):
    """
    Base class for all data extractors.
    
    All extractors must implement the extract_streaming method which yields
    batches of records as dictionaries. Extractors are schema-agnostic and
    focus purely on data retrieval from their respective sources.
    """
    
    @abstractmethod
    async def extract_streaming(
        self,
        extract_config: Dict[str, Any],
        params: Dict[str, Any],
        headers: Dict[str, Any],
        contract_dir: Optional[Any] = None,
        batch_size: int = 1000,
        max_records: Optional[int] = None,
        config_context: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """
        Extract data in batches using async generator.
        
        This is the main interface that all extractors must implement.
        It yields batches of records as lists of dictionaries, allowing
        for memory-efficient processing of large datasets.
        
        Args:
            extract_config: Extract configuration dictionary (source-specific)
            params: Request/query parameters (may be source-specific)
            headers: Request headers (may be source-specific)
            contract_dir: Contract directory path (for variable resolution)
            batch_size: Number of records to yield per batch
            max_records: Maximum total records to extract (None = all)
            config_context: Optional context dictionary for value injection
        
        Yields:
            Batches of extracted records (lists of dictionaries)
        
        Raises:
            RuntimeError: If extraction fails
            ValueError: If configuration is invalid
        """
        pass
    
    def validate_config(self, extract_config: Dict[str, Any]) -> None:
        """
        Validate extractor-specific configuration.
        
        Override this method in subclasses to validate source-specific
        configuration requirements.
        
        Args:
            extract_config: Extract configuration dictionary
        
        Raises:
            ValueError: If configuration is invalid
        """
        pass
