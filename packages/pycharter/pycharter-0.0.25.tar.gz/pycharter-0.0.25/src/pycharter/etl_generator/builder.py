"""
Fluent PipelineBuilder API.
"""

from typing import Any, Dict, List, Optional

from pycharter.etl_generator.context import PipelineContext
from pycharter.etl_generator.pipeline import Pipeline
from pycharter.etl_generator.protocols import Extractor, Transformer, Loader


class PipelineBuilder:
    """
    Fluent API for building ETL pipelines.
    
    Example:
        >>> pipeline = (
        ...     PipelineBuilder()
        ...     .name("user_pipeline")
        ...     .extract_from("http", url="https://api.example.com/users")
        ...     .transform(Rename({"old": "new"}))
        ...     .load_to("postgres", table="users", connection_string="...")
        ...     .build()
        ... )
    """
    
    def __init__(self):
        self._name: Optional[str] = None
        self._extractor: Optional[Extractor] = None
        self._transformers: List[Transformer] = []
        self._loader: Optional[Loader] = None
        self._context: Optional[PipelineContext] = None
    
    def name(self, name: str) -> "PipelineBuilder":
        """Set pipeline name."""
        self._name = name
        return self
    
    def with_context(self, context: PipelineContext) -> "PipelineBuilder":
        """Set pipeline context."""
        self._context = context
        return self
    
    def extract_from(self, source_type: str, **config) -> "PipelineBuilder":
        """Configure extractor by type."""
        self._extractor = self._create_extractor(source_type, config)
        return self
    
    def extractor(self, extractor: Extractor) -> "PipelineBuilder":
        """Set extractor directly."""
        self._extractor = extractor
        return self
    
    def transform(self, transformer: Transformer) -> "PipelineBuilder":
        """Add transformer to pipeline."""
        self._transformers.append(transformer)
        return self
    
    def load_to(self, target_type: str, **config) -> "PipelineBuilder":
        """Configure loader by type."""
        self._loader = self._create_loader(target_type, config)
        return self
    
    def loader(self, loader: Loader) -> "PipelineBuilder":
        """Set loader directly."""
        self._loader = loader
        return self
    
    def build(self) -> Pipeline:
        """Build the pipeline."""
        if not self._extractor:
            raise ValueError("Extractor required. Call extract_from() or extractor()")
        
        return Pipeline(
            extractor=self._extractor,
            transformers=self._transformers,
            loader=self._loader,
            context=self._context or PipelineContext(),
            name=self._name,
        )
    
    def _create_extractor(self, source_type: str, config: Dict[str, Any]) -> Extractor:
        """Create extractor from type and config."""
        from pycharter.etl_generator.extractors import (
            HTTPExtractor,
            FileExtractor,
            DatabaseExtractor,
            CloudStorageExtractor,
        )
        
        source_type = source_type.lower()
        
        if source_type == "http":
            return HTTPExtractor(**config)
        elif source_type == "file":
            return FileExtractor(**config)
        elif source_type in ("database", "db", "sql"):
            return DatabaseExtractor(**config)
        elif source_type in ("s3", "cloud", "cloud_storage"):
            return CloudStorageExtractor(**config)
        else:
            raise ValueError(f"Unknown extractor type: {source_type}")
    
    def _create_loader(self, target_type: str, config: Dict[str, Any]) -> Loader:
        """Create loader from type and config."""
        from pycharter.etl_generator.loaders import (
            PostgresLoader,
            FileLoader,
            CloudStorageLoader,
        )
        
        target_type = target_type.lower()
        
        if target_type in ("postgres", "postgresql", "database", "db"):
            return PostgresLoader(**config)
        elif target_type == "file":
            return FileLoader(**config)
        elif target_type in ("s3", "cloud", "cloud_storage"):
            return CloudStorageLoader(**config)
        else:
            raise ValueError(f"Unknown loader type: {target_type}")
