"""
Loader factory for ETL pipelines.

Provides a registry pattern to select and instantiate the appropriate loader
based on the target type specified in load configuration.

Usage:
    from pycharter.etl_generator.loaders.factory import LoaderFactory
    
    # Create loader from config
    loader = LoaderFactory.create(load_config)
    
    # Register custom loader
    LoaderFactory.register("bigquery", BigQueryLoader)
"""

import logging
from typing import Any, Dict, List, Optional, Type

from pycharter.etl_generator.loaders.base import BaseLoader
from pycharter.etl_generator.loaders.database import PostgresLoader, DatabaseLoader
from pycharter.etl_generator.loaders.file import FileLoader
from pycharter.etl_generator.loaders.cloud import CloudStorageLoader

logger = logging.getLogger(__name__)


class LoaderFactory:
    """
    Factory for creating loader instances based on target type.
    
    Supports:
    - Explicit 'type' field (recommended)
    - Legacy 'target_type' field
    - Auto-detection from config keys (for backward compatibility)
    
    Example:
        # With explicit type (recommended)
        config = {"type": "postgres", "table": "users", "database": {"url": "..."}}
        loader = LoaderFactory.create(config)
        
        # Auto-detected (legacy)
        config = {"table": "users", "connection_string": "postgresql://..."}
        loader = LoaderFactory.create(config)  # Detected as postgres
    """
    
    # Registry of loaders by target type
    _registry: Dict[str, Type[BaseLoader]] = {
        "postgres": PostgresLoader,
        "postgresql": PostgresLoader,
        "database": DatabaseLoader,
        "sqlite": DatabaseLoader,
        "file": FileLoader,
        "cloud_storage": CloudStorageLoader,
    }
    
    @classmethod
    def register(cls, type_name: str, loader_class: Type[BaseLoader]) -> None:
        """
        Register a custom loader class.
        
        Args:
            type_name: Type identifier (e.g., 'bigquery', 'snowflake')
            loader_class: Loader class that inherits from BaseLoader
            
        Example:
            class BigQueryLoader(BaseLoader):
                ...
            
            LoaderFactory.register("bigquery", BigQueryLoader)
        """
        if not issubclass(loader_class, BaseLoader):
            raise TypeError(f"Loader class must inherit from BaseLoader: {loader_class}")
        cls._registry[type_name.lower()] = loader_class
        logger.info(f"Registered loader: {type_name} -> {loader_class.__name__}")
    
    @classmethod
    def unregister(cls, type_name: str) -> None:
        """Remove a loader from the registry."""
        cls._registry.pop(type_name.lower(), None)
    
    @classmethod
    def list_types(cls) -> List[str]:
        """List all registered loader types."""
        return list(cls._registry.keys())
    
    @classmethod
    def create(cls, config: Dict[str, Any]) -> BaseLoader:
        """
        Create a loader instance from configuration.
        
        Args:
            config: Load configuration dictionary
        
        Returns:
            Configured loader instance
        
        Raises:
            ValueError: If type cannot be determined or is not registered
        """
        # Get type from config (check 'type' first, then 'target_type' for legacy)
        load_type = config.get("type") or config.get("target_type")
        
        # Auto-detect if not specified
        if not load_type:
            load_type = cls._detect_type(config)
            if load_type:
                logger.debug(f"Auto-detected loader type: {load_type}")
            else:
                raise ValueError(
                    "Cannot determine loader type. "
                    f"Add 'type' field with one of: {', '.join(set(cls._registry.keys()))}"
                )
        
        load_type = load_type.lower()
        
        # Get loader class from registry
        loader_class = cls._registry.get(load_type)
        if not loader_class:
            raise ValueError(
                f"Unknown loader type: '{load_type}'. "
                f"Available types: {', '.join(set(cls._registry.keys()))}. "
                f"Register custom loaders with LoaderFactory.register()"
            )
        
        # Create loader using from_config if available
        if hasattr(loader_class, "from_config"):
            loader = loader_class.from_config(config)
        else:
            loader = loader_class()
        
        logger.debug(f"Created {loader_class.__name__} for type: {load_type}")
        return loader
    
    @classmethod
    def _detect_type(cls, config: Dict[str, Any]) -> Optional[str]:
        """
        Auto-detect loader type from configuration keys.
        
        This is for backward compatibility. New configs should use explicit 'type'.
        """
        # Database indicators
        if "table" in config:
            if "connection_string" in config or "database" in config:
                # Check if it's SQLite
                conn_str = config.get("connection_string", "")
                if not conn_str and "database" in config:
                    conn_str = config["database"].get("url", "")
                if "sqlite" in conn_str.lower():
                    return "sqlite"
                return "postgres"
        
        # File indicators
        if any(key in config for key in ("path", "file_path")) and "storage" not in config:
            return "file"
        
        # Cloud storage indicators
        if any(key in config for key in ("storage", "bucket", "container")):
            return "cloud_storage"
        
        return None
    
    # Legacy method name for consistency with ExtractorFactory
    @classmethod
    def get_loader(cls, load_config: Dict[str, Any]) -> BaseLoader:
        """Legacy method. Use create() instead."""
        return cls.create(load_config)


def get_loader(load_config: Dict[str, Any]) -> BaseLoader:
    """
    Convenience function to get loader instance.
    
    Args:
        load_config: Load configuration dictionary
    
    Returns:
        Loader instance
    """
    return LoaderFactory.create(load_config)
