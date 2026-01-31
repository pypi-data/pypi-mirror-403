"""
Extractor factory for ETL pipelines.

Provides a registry pattern to select and instantiate the appropriate extractor
based on the source type specified in extract configuration.

Usage:
    from pycharter.etl_generator.extractors.factory import ExtractorFactory
    
    # Create extractor from config
    extractor = ExtractorFactory.create(extract_config)
    
    # Register custom extractor
    ExtractorFactory.register("kafka", KafkaExtractor)
"""

import logging
from typing import Any, Dict, List, Optional, Type

from pycharter.etl_generator.extractors.base import BaseExtractor
from pycharter.etl_generator.extractors.cloud_storage import CloudStorageExtractor
from pycharter.etl_generator.extractors.database import DatabaseExtractor
from pycharter.etl_generator.extractors.file import FileExtractor
from pycharter.etl_generator.extractors.http import HTTPExtractor

logger = logging.getLogger(__name__)


class ExtractorFactory:
    """
    Factory for creating extractor instances based on source type.
    
    Supports:
    - Explicit 'type' field (recommended)
    - Legacy 'source_type' field
    - Auto-detection from config keys (for backward compatibility)
    
    Example:
        # With explicit type (recommended)
        config = {"type": "http", "url": "https://api.example.com/data"}
        extractor = ExtractorFactory.create(config)
        
        # Auto-detected (legacy)
        config = {"url": "https://api.example.com/data"}
        extractor = ExtractorFactory.create(config)  # Detected as HTTP
    """
    
    # Registry of extractors by source type
    _registry: Dict[str, Type[BaseExtractor]] = {
        "http": HTTPExtractor,
        "file": FileExtractor,
        "database": DatabaseExtractor,
        "cloud_storage": CloudStorageExtractor,
    }
    
    @classmethod
    def register(cls, type_name: str, extractor_class: Type[BaseExtractor]) -> None:
        """
        Register a custom extractor class.
        
        Args:
            type_name: Type identifier (e.g., 'kafka', 'mongodb')
            extractor_class: Extractor class that inherits from BaseExtractor
            
        Example:
            class KafkaExtractor(BaseExtractor):
                ...
            
            ExtractorFactory.register("kafka", KafkaExtractor)
        """
        if not issubclass(extractor_class, BaseExtractor):
            raise TypeError(f"Extractor class must inherit from BaseExtractor: {extractor_class}")
        cls._registry[type_name.lower()] = extractor_class
        logger.info(f"Registered extractor: {type_name} -> {extractor_class.__name__}")
    
    @classmethod
    def unregister(cls, type_name: str) -> None:
        """Remove an extractor from the registry."""
        cls._registry.pop(type_name.lower(), None)
    
    @classmethod
    def list_types(cls) -> List[str]:
        """List all registered extractor types."""
        return list(cls._registry.keys())
    
    @classmethod
    def create(cls, config: Dict[str, Any]) -> BaseExtractor:
        """
        Create an extractor instance from configuration.
        
        Args:
            config: Extract configuration dictionary
        
        Returns:
            Configured extractor instance
        
        Raises:
            ValueError: If type cannot be determined or is not registered
        """
        # Get type from config (check 'type' first, then 'source_type' for legacy)
        extract_type = config.get("type") or config.get("source_type")
        
        # Auto-detect if not specified
        if not extract_type:
            extract_type = cls._detect_type(config)
            if extract_type:
                logger.debug(f"Auto-detected extractor type: {extract_type}")
            else:
                raise ValueError(
                    "Cannot determine extractor type. "
                    f"Add 'type' field with one of: {', '.join(cls._registry.keys())}"
                )
        
        extract_type = extract_type.lower()
        
        # Get extractor class from registry
        extractor_class = cls._registry.get(extract_type)
        if not extractor_class:
            raise ValueError(
                f"Unknown extractor type: '{extract_type}'. "
                f"Available types: {', '.join(cls._registry.keys())}. "
                f"Register custom extractors with ExtractorFactory.register()"
            )
        
        # Create extractor using from_config if available
        if hasattr(extractor_class, "from_config"):
            extractor = extractor_class.from_config(config)
        else:
            extractor = extractor_class()
            if hasattr(extractor, "validate_config"):
                extractor.validate_config(config)
        
        logger.debug(f"Created {extractor_class.__name__} for type: {extract_type}")
        return extractor
    
    @classmethod
    def _detect_type(cls, config: Dict[str, Any]) -> Optional[str]:
        """
        Auto-detect extractor type from configuration keys.
        
        This is for backward compatibility. New configs should use explicit 'type'.
        """
        # HTTP indicators
        if any(key in config for key in ("url", "base_url", "api_endpoint", "endpoint")):
            return "http"
        
        # File indicators
        if any(key in config for key in ("path", "file_path")) and "storage" not in config:
            return "file"
        
        # Database indicators
        if "query" in config or (
            "database" in config and "connection_string" not in config.get("database", {}).get("url", "s3")
        ):
            return "database"
        
        # Cloud storage indicators
        if any(key in config for key in ("storage", "bucket", "container")):
            return "cloud_storage"
        
        return None
    
    # Legacy method names for backward compatibility
    @classmethod
    def register_extractor(cls, source_type: str, extractor_class: Type[BaseExtractor]) -> None:
        """Legacy method. Use register() instead."""
        cls.register(source_type, extractor_class)
    
    @classmethod
    def get_extractor(cls, extract_config: Dict[str, Any]) -> BaseExtractor:
        """Legacy method. Use create() instead."""
        return cls.create(extract_config)


def get_extractor(extract_config: Dict[str, Any]) -> BaseExtractor:
    """
    Convenience function to get extractor instance.
    
    Args:
        extract_config: Extract configuration dictionary
    
    Returns:
        Extractor instance
    """
    return ExtractorFactory.create(extract_config)
