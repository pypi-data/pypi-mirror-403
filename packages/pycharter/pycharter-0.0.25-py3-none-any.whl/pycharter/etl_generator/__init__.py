"""
ETL Generator - Modern ETL pipeline framework.

Two APIs:
=========
1. Programmatic API (Pipeline with | operator):
   >>> pipeline = Pipeline(HTTPExtractor(url="...")) | Rename(...) | PostgresLoader(...)
   >>> result = await pipeline.run()

2. Config-driven API (YAML files):
   >>> # From explicit files (most flexible)
   >>> pipeline = Pipeline.from_config_files(
   ...     extract="configs/extract.yaml",
   ...     load="configs/load.yaml",
   ...     variables={"API_KEY": "secret"}
   ... )
   >>> 
   >>> # From directory (expects extract.yaml, transform.yaml, load.yaml)
   >>> pipeline = Pipeline.from_config_dir("pipelines/users/")
   >>> 
   >>> # From single file (pipeline.yaml)
   >>> pipeline = Pipeline.from_config_file("pipelines/users/pipeline.yaml")

Quick Start:
============
    from pycharter.etl_generator import (
        Pipeline, HTTPExtractor, PostgresLoader,
        Rename, AddField, Filter
    )
    
    # Programmatic
    pipeline = (
        Pipeline(HTTPExtractor(url="https://api.example.com/users"))
        | Rename({"user_name": "name"})
        | AddField("full_name", "${first_name} ${last_name}")
        | PostgresLoader(connection_string="...", table="users")
    )
    result = await pipeline.run()
    
    # Config-driven (explicit files)
    pipeline = Pipeline.from_config_files(
        extract="pipelines/users/extract.yaml",
        load="pipelines/users/load.yaml",
        variables={"DATA_DIR": "./data"}
    )
    result = await pipeline.run()

Config Format:
==============
    Single-file (pipeline.yaml):
        name: users_pipeline
        extract:
          type: http  # Required: http | file | database | cloud_storage
          url: https://api.example.com/users
        transform:
          - rename: {userId: user_id}
          - add:
              full_name: "${first_name} ${last_name}"
        load:
          type: postgres  # Required: postgres | sqlite | file | cloud_storage
          table: users
          database:
            url: ${DATABASE_URL}
"""

# Core pipeline classes
from pycharter.etl_generator.pipeline import Pipeline
from pycharter.etl_generator.builder import PipelineBuilder
from pycharter.etl_generator.context import PipelineContext
from pycharter.etl_generator.result import PipelineResult, BatchResult, LoadResult
from pycharter.etl_generator.protocols import Extractor, Transformer, Loader

# Config loading and validation
from pycharter.etl_generator.config_loader import (
    ConfigLoader,
    PipelineConfig,
    load_pipeline_config,
    ConfigLoadError,
)
from pycharter.etl_generator.config_validator import (
    ConfigValidator,
    ConfigValidationError,
    validate_config,
)

# Expression evaluation
from pycharter.etl_generator.expression import (
    ExpressionEvaluator,
    ExpressionError,
    evaluate_expression,
    is_expression,
)

# Extractors
from pycharter.etl_generator.extractors import (
    BaseExtractor,
    HTTPExtractor,
    FileExtractor,
    DatabaseExtractor,
    CloudStorageExtractor,
    ExtractorFactory,
)

# Transformers
from pycharter.etl_generator.transformers import (
    BaseTransformer,
    TransformerChain,
    Rename,
    AddField,
    Drop,
    Select,
    Filter,
    Convert,
    Default,
    Map,
    FlatMap,
    CustomFunction,
)

# Loaders
from pycharter.etl_generator.loaders import (
    BaseLoader,
    PostgresLoader,
    DatabaseLoader,
    FileLoader,
    CloudStorageLoader,
    LoaderFactory,
)

__all__ = [
    # Core
    "Pipeline",
    "PipelineBuilder",
    "PipelineContext",
    "PipelineResult",
    "BatchResult",
    "LoadResult",
    # Protocols
    "Extractor",
    "Transformer",
    "Loader",
    # Config loading
    "ConfigLoader",
    "PipelineConfig",
    "load_pipeline_config",
    "ConfigLoadError",
    "ConfigValidator",
    "ConfigValidationError",
    "validate_config",
    # Expressions
    "ExpressionEvaluator",
    "ExpressionError",
    "evaluate_expression",
    "is_expression",
    # Extractors
    "BaseExtractor",
    "HTTPExtractor",
    "FileExtractor",
    "DatabaseExtractor",
    "CloudStorageExtractor",
    "ExtractorFactory",
    # Transformers
    "BaseTransformer",
    "TransformerChain",
    "Rename",
    "AddField",
    "Drop",
    "Select",
    "Filter",
    "Convert",
    "Default",
    "Map",
    "FlatMap",
    "CustomFunction",
    # Loaders
    "BaseLoader",
    "PostgresLoader",
    "DatabaseLoader",
    "FileLoader",
    "CloudStorageLoader",
    "LoaderFactory",
]
