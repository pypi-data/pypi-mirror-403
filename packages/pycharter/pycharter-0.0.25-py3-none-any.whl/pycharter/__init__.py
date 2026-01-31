"""
PyCharter - Data Contract Management, ETL Pipelines, and Validation

Core Services:
1. ETL Pipelines - Build and run ETL pipelines with | operator
2. Contract Parser - Reads and decomposes data contract files
3. Contract Builder - Constructs consolidated contracts from separate artifacts
4. Metadata Store - Database operations for metadata storage
5. Pydantic Generator - Generates Pydantic models from JSON Schema
6. JSON Schema Converter - Converts Pydantic models to JSON Schema
7. Runtime Validator - Validation utilities
8. Quality Assurance - Data quality checking and monitoring

ETL API:
    >>> from pycharter import Pipeline, HTTPExtractor, PostgresLoader, Rename, AddField
    >>> 
    >>> # Programmatic pipeline with | operator
    >>> pipeline = (
    ...     Pipeline(HTTPExtractor(url="https://api.example.com/data"))
    ...     | Rename({"old": "new"})
    ...     | AddField("processed_at", "now()")
    ...     | PostgresLoader(connection_string="...", table="users")
    ... )
    >>> result = await pipeline.run()  # run() is async; use asyncio.run() from scripts
    >>> 
    >>> # Config-driven (explicit files)
    >>> pipeline = Pipeline.from_config_files(
    ...     extract="configs/extract.yaml",
    ...     load="configs/load.yaml",
    ...     variables={"API_KEY": "secret"}
    ... )
    >>> 
    >>> # Config-driven (directory with extract.yaml, transform.yaml, load.yaml)
    >>> pipeline = Pipeline.from_config_dir("pipelines/users/")
    >>> 
    >>> # Config-driven (single file)
    >>> pipeline = Pipeline.from_config_file("pipelines/users/pipeline.yaml")

Validator API:
    >>> from pycharter import Validator
    >>> 
    >>> # From explicit files
    >>> validator = Validator.from_files(schema="schema.yaml")
    >>> 
    >>> # From directory
    >>> validator = Validator.from_dir("contracts/users/")
    >>> 
    >>> result = validator.validate({"name": "Alice", "age": 30})
"""

__version__ = "0.1.0"

# ============================================================================
# ETL PIPELINES
# ============================================================================

from pycharter.etl_generator import (
    # Core
    Pipeline,
    PipelineBuilder,
    PipelineContext,
    PipelineResult,
    BatchResult,
    LoadResult,
    # Protocols
    Extractor,
    Transformer,
    Loader,
    # Extractors
    BaseExtractor,
    HTTPExtractor,
    FileExtractor,
    DatabaseExtractor,
    CloudStorageExtractor,
    # Transformers
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
    # Loaders
    BaseLoader,
    PostgresLoader,
    DatabaseLoader,
    FileLoader,
    CloudStorageLoader,
)

# ============================================================================
# TIER 1: PRIMARY INTERFACES (Classes - Use these for best performance)
# ============================================================================

# Runtime Validator (PRIMARY INTERFACE)
from pycharter.runtime_validator import (
    Validator,  # ⭐ PRIMARY: Use this for validation
    ValidatorBuilder,  # Fluent API for building validators
    create_validator,
    QualityMetrics as ValidationQualityMetrics,  # Quality metrics from validation
)

# Quality Assurance (PRIMARY INTERFACE)
from pycharter.quality import (
    QualityCheck,  # ⭐ PRIMARY: Use this for quality checks
    QualityCheckOptions,
    QualityReport,
    QualityThresholds,
)

# Metadata Store (PRIMARY INTERFACE)
from pycharter.metadata_store import MetadataStoreClient

# ============================================================================
# TIER 2: CONVENIENCE FUNCTIONS (Quick start - one-off use cases)
# ============================================================================

# Contract Parser
from pycharter.contract_parser import (
    ContractMetadata,
    parse_contract,
    parse_contract_file,
)

# Contract Builder
from pycharter.contract_builder import (
    ContractArtifacts,
    build_contract,
    build_contract_from_store,
)

# Pydantic Generator - Input type helpers (convenience)
from pycharter.pydantic_generator import (
    from_dict,  # Quick: schema from dict
    from_file,  # Quick: schema from file
    from_json,  # Quick: schema from JSON string
    from_url,  # Quick: schema from URL
    generate_model,  # Advanced: when you need more control
    generate_model_file,
)

# JSON Schema Converter - Output type helpers (convenience)
from pycharter.json_schema_converter import (
    to_dict,  # Quick: schema to dict
    to_file,  # Quick: schema to file
    to_json,  # Quick: schema to JSON string
    model_to_schema,  # Advanced: core conversion
)

# Runtime Validator - Data source helpers (convenience)
from pycharter.runtime_validator import (
    ValidationResult,
    # Quick validation functions (use Validator class for multiple validations)
    validate_with_store,  # Quick: validate with metadata store
    validate_batch_with_store,  # Quick: batch validate with metadata store
    validate_with_contract,  # Quick: validate with contract file/dict
    validate_batch_with_contract,  # Quick: batch validate with contract file/dict
    get_model_from_store,  # Quick: get model from store
    get_model_from_contract,  # Quick: get model from contract
    # Decorators
    validate_input,
    validate_output,
    validate_with_contract_decorator,
)

# ============================================================================
# TIER 3: LOW-LEVEL UTILITIES (When you already have models/schemas)
# ============================================================================

from pycharter.runtime_validator import (
    validate,  # Low-level: validate with existing model
    validate_batch,  # Low-level: batch validate with existing model
)

# ============================================================================
# METADATA STORE IMPLEMENTATIONS
# ============================================================================

try:
    from pycharter.metadata_store import InMemoryMetadataStore
except ImportError:
    InMemoryMetadataStore = None  # type: ignore[assignment,misc]

try:
    from pycharter.metadata_store import MongoDBMetadataStore
except ImportError:
    MongoDBMetadataStore = None  # type: ignore[assignment,misc]

try:
    from pycharter.metadata_store import PostgresMetadataStore
except ImportError:
    PostgresMetadataStore = None  # type: ignore[assignment,misc]

try:
    from pycharter.metadata_store import RedisMetadataStore
except ImportError:
    RedisMetadataStore = None  # type: ignore[assignment,misc]

try:
    from pycharter.metadata_store import SQLiteMetadataStore
except ImportError:
    SQLiteMetadataStore = None  # type: ignore[assignment,misc]

# ============================================================================
# QUALITY ASSURANCE - Additional utilities (if needed for advanced use)
# ============================================================================

from pycharter.quality import (
    QualityMetrics,
    QualityScore,
    FieldQualityMetrics,
    ViolationTracker,
    ViolationRecord,
    DataProfiler,
    # Tracking submodule
    MetricsCollector,
    ValidationMetric,
    MetricsSummary,
    InMemoryMetricsStore,
    SQLiteMetricsStore,
)

# ============================================================================
# DOCUMENTATION GENERATION
# ============================================================================

from pycharter.docs_generator import (
    DocsGenerator,
    generate_docs,
    MarkdownRenderer,
    HTMLRenderer,
)

# ============================================================================
# SCHEMA EVOLUTION
# ============================================================================

from pycharter.schema_evolution import (
    check_compatibility,
    compute_diff,
    CompatibilityResult,
    SchemaDiff,
    SchemaChange,
    ChangeType,
    CompatibilityMode,
)

# ============================================================================
# PROTOCOLS AND ERROR HANDLING
# ============================================================================

from pycharter.shared import (
    # Protocols for extensibility
    MetadataStore,
    CoercionRegistry,
    ValidationRegistry,
    DataValidator,
    # Exception hierarchy (catch PyCharterError for any pycharter failure)
    PyCharterError,
    ConfigError,
    ConfigValidationError,
    ConfigLoadError,
    ExpressionError,
    # Error handling
    ErrorMode,
    ErrorContext,
    StrictMode,
    LenientMode,
    set_error_mode,
)

__all__ = [
    # ========================================================================
    # ETL PIPELINES
    # ========================================================================
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
    # Extractors
    "BaseExtractor",
    "HTTPExtractor",
    "FileExtractor",
    "DatabaseExtractor",
    "CloudStorageExtractor",
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
    # Exceptions and error handling
    "PyCharterError",
    "ConfigError",
    "ConfigValidationError",
    "ConfigLoadError",
    "ExpressionError",
    "ErrorMode",
    "ErrorContext",
    "StrictMode",
    "LenientMode",
    "set_error_mode",
    # ========================================================================
    # DATA CONTRACT SERVICES
    # ========================================================================
    # Validation
    "Validator",
    "ValidatorBuilder",
    "create_validator",
    "ValidationResult",
    "ValidationQualityMetrics",
    "validate_with_store",
    "validate_batch_with_store",
    "validate_with_contract",
    "validate_batch_with_contract",
    "get_model_from_store",
    "get_model_from_contract",
    "validate",
    "validate_batch",
    "validate_input",
    "validate_output",
    "validate_with_contract_decorator",
    # Quality
    "QualityCheck",
    "QualityCheckOptions",
    "QualityReport",
    "QualityThresholds",
    "QualityMetrics",
    "QualityScore",
    "FieldQualityMetrics",
    "ViolationTracker",
    "ViolationRecord",
    "DataProfiler",
    # Contract Management
    "parse_contract",
    "parse_contract_file",
    "ContractMetadata",
    "build_contract",
    "build_contract_from_store",
    "ContractArtifacts",
    # Pydantic Generator
    "from_dict",
    "from_file",
    "from_json",
    "from_url",
    "generate_model",
    "generate_model_file",
    # JSON Schema Converter
    "to_dict",
    "to_file",
    "to_json",
    "model_to_schema",
    # Metadata Store
    "MetadataStoreClient",
    "InMemoryMetadataStore",
    "MongoDBMetadataStore",
    "PostgresMetadataStore",
    "RedisMetadataStore",
    "SQLiteMetadataStore",
    # Protocols
    "MetadataStore",
    "CoercionRegistry",
    "ValidationRegistry",
    "DataValidator",
    # Error handling
    "ErrorMode",
    "ErrorContext",
    "StrictMode",
    "LenientMode",
    "set_error_mode",
    # ========================================================================
    # QUALITY TRACKING
    # ========================================================================
    "MetricsCollector",
    "ValidationMetric",
    "MetricsSummary",
    "InMemoryMetricsStore",
    "SQLiteMetricsStore",
    # ========================================================================
    # DOCUMENTATION GENERATION
    # ========================================================================
    "DocsGenerator",
    "generate_docs",
    "MarkdownRenderer",
    "HTMLRenderer",
    # ========================================================================
    # SCHEMA EVOLUTION
    # ========================================================================
    "check_compatibility",
    "compute_diff",
    "CompatibilityResult",
    "SchemaDiff",
    "SchemaChange",
    "ChangeType",
    "CompatibilityMode",
]
