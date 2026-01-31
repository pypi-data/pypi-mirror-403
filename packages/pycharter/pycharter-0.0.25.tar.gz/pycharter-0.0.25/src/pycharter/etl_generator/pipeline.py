"""
Pipeline class with | operator for chaining.

Supports both config-driven and programmatic pipeline construction.
"""

import logging
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import yaml

from pycharter.etl_generator.context import PipelineContext
from pycharter.etl_generator.protocols import Extractor, Transformer, Loader
from pycharter.etl_generator.result import PipelineResult, BatchResult
from pycharter.shared.errors import ErrorContext, ErrorMode, get_error_context

logger = logging.getLogger(__name__)

# Variable pattern: ${VAR} or ${VAR:-default} or ${VAR:?error}
VARIABLE_PATTERN = re.compile(r'\$\{([^}:]+)(?::([?-])([^}]*))?\}')


class Pipeline:
    """
    ETL Pipeline with | operator for chaining transformers.
    
    Programmatic usage:
        >>> pipeline = (
        ...     Pipeline(HTTPExtractor(url="..."))
        ...     | Rename({"old": "new"})
        ...     | PostgresLoader(...)
        ... )
        >>> result = await pipeline.run()
    
    Config-driven usage:
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
        >>> # From single file (pipeline.yaml with all sections)
        >>> pipeline = Pipeline.from_config_file("pipelines/users/pipeline.yaml")
        >>> 
        >>> result = await pipeline.run()
    
    Async execution:
        run() is async. From a script use asyncio.run():
            asyncio.run(pipeline.run())
        From an async context (FastAPI, Jupyter) await directly:
            result = await pipeline.run()
        See pycharter/etl_generator/ASYNC_AND_EXECUTION.md for details.
    """
    
    def __init__(
        self,
        extractor: Optional[Extractor] = None,
        transformers: Optional[List[Transformer]] = None,
        loader: Optional[Loader] = None,
        context: Optional[PipelineContext] = None,
        name: Optional[str] = None,
    ):
        self.extractor = extractor
        self._transformers: List[Transformer] = list(transformers) if transformers else []
        self.loader = loader
        self.context = context or PipelineContext()
        self.name = name
    
    def __or__(self, other: Union[Transformer, Loader]) -> "Pipeline":
        """Chain transformer or set loader using | operator."""
        if isinstance(other, Loader):
            return Pipeline(
                extractor=self.extractor,
                transformers=self._transformers.copy(),
                loader=other,
                context=self.context,
                name=self.name,
            )
        else:
            new_transformers = self._transformers.copy()
            new_transformers.append(other)
            return Pipeline(
                extractor=self.extractor,
                transformers=new_transformers,
                loader=self.loader,
                context=self.context,
                name=self.name,
            )
    
    async def run(
        self,
        dry_run: bool = False,
        error_context: Optional[ErrorContext] = None,
        **params,
    ) -> PipelineResult:
        """
        Run the ETL pipeline.
        
        Args:
            dry_run: If True, extract and transform but do not load.
            error_context: Optional error context for handling failures.
                If not set, uses the default from get_error_context().
                In STRICT mode, extraction or load failures raise.
                In LENIENT/COLLECT mode, errors are logged and appended to result.errors.
            **params: Passed to extractor.extract() and loader.load().
        
        Returns:
            PipelineResult with counts and any errors.
        """
        run_id = str(uuid.uuid4())[:8]
        start_time = datetime.now(timezone.utc)
        ctx = error_context or get_error_context()
        
        result = PipelineResult(
            pipeline_name=self.name,
            run_id=run_id,
            start_time=start_time,
        )
        
        if not self.extractor:
            result.success = False
            result.errors.append("No extractor configured")
            return result
        
        logger.info(f"[{run_id}] Starting pipeline: {self.name or 'unnamed'}")
        
        try:
            batch_index = 0
            async for batch in self.extractor.extract(**params):
                batch_result = BatchResult(batch_index=batch_index, rows_in=len(batch))
                
                # Transform
                transformed = self._apply_transforms(batch)
                batch_result.rows_out = len(transformed)
                
                # Load
                if not dry_run and self.loader and transformed:
                    try:
                        load_result = await self.loader.load(transformed, **params)
                        if load_result.success:
                            result.rows_loaded += load_result.rows_loaded
                        else:
                            msg = load_result.error or "Load failed"
                            ctx.handle_error(msg, category="load")
                            batch_result.errors.append(msg)
                            batch_result.rows_failed += len(transformed)
                    except Exception as e:
                        ctx.handle_error(str(e), e, category="load")
                        batch_result.errors.append(str(e))
                        batch_result.rows_failed += len(transformed)
                elif dry_run:
                    result.rows_loaded += len(transformed)
                
                result.rows_extracted += len(batch)
                result.rows_transformed += len(transformed)
                result.batches_processed += 1
                result.batch_results.append(batch_result)
                batch_index += 1
        
        except Exception as e:
            result.success = False
            result.errors.append(str(e))
            ctx.handle_error(str(e), e, category="pipeline")
            logger.error(f"[{run_id}] Pipeline error: {e}")
        
        result.end_time = datetime.now(timezone.utc)
        result.duration_seconds = (result.end_time - start_time).total_seconds()
        result.rows_failed = sum(br.rows_failed for br in result.batch_results)
        
        if result.errors:
            result.success = False
        
        logger.info(f"[{run_id}] Complete: extracted={result.rows_extracted}, loaded={result.rows_loaded}")
        return result
    
    def _apply_transforms(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply all transformers to data."""
        result = data
        for transformer in self._transformers:
            result = transformer.transform(result)
        return result
    
    # =========================================================================
    # CONFIG-DRIVEN FACTORY METHODS
    # =========================================================================
    
    @classmethod
    def from_config_files(
        cls,
        extract: Union[str, Path, Dict[str, Any]],
        load: Union[str, Path, Dict[str, Any]],
        transform: Optional[Union[str, Path, Dict[str, Any], List[Dict[str, Any]]]] = None,
        variables: Optional[Dict[str, str]] = None,
        validate: bool = True,
        name: Optional[str] = None,
    ) -> "Pipeline":
        """
        Create pipeline from explicit file paths or dictionaries.
        
        This is the most flexible method - use any file paths without any
        assumptions about directory structure or file naming.
        
        Args:
            extract: Path to extract config file OR config as dict
            load: Path to load config file OR config as dict
            transform: Optional path to transform config OR config as dict/list
            variables: Variables for ${VAR} substitution in config values
            validate: If True, validate configs against schemas
            name: Optional pipeline name
        
        Returns:
            Configured Pipeline instance
        
        Example:
            pipeline = Pipeline.from_config_files(
                extract="configs/my_http_source.yaml",
                transform="configs/my_transforms.yaml",
                load="configs/my_postgres_sink.yaml",
                variables={"API_KEY": "secret", "DB_URL": "postgresql://..."}
            )
        """
        variables = variables or {}
        
        # Load configs
        extract_config = _load_config_input(extract, variables)
        load_config = _load_config_input(load, variables)
        
        if transform is not None:
            transform_config = _load_config_input(transform, variables)
        else:
            transform_config = {}
        
        return cls._build_from_configs(
            extract_config=extract_config,
            transform_config=transform_config,
            load_config=load_config,
            variables=variables,
            validate=validate,
            name=name,
        )
    
    @classmethod
    def from_config_dir(
        cls,
        directory: Union[str, Path],
        variables: Optional[Dict[str, str]] = None,
        validate: bool = True,
        name: Optional[str] = None,
    ) -> "Pipeline":
        """
        Create pipeline from a directory containing config files.
        
        Expects files with standard names:
        - extract.yaml (required)
        - transform.yaml (optional)
        - load.yaml (required)
        
        Args:
            directory: Path to directory containing config files
            variables: Variables for ${VAR} substitution
            validate: If True, validate configs against schemas
            name: Optional pipeline name (defaults to directory name)
        
        Returns:
            Configured Pipeline instance
        
        Example:
            pipeline = Pipeline.from_config_dir(
                "pipelines/users/",
                variables={"DATA_DIR": "./data", "OUTPUT_DIR": "./output"}
            )
        """
        directory = Path(directory)
        if not directory.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory}")
        
        variables = variables or {}
        
        # Check for required files
        extract_file = directory / "extract.yaml"
        load_file = directory / "load.yaml"
        transform_file = directory / "transform.yaml"
        
        if not extract_file.exists():
            raise FileNotFoundError(f"Required file not found: {extract_file}")
        if not load_file.exists():
            raise FileNotFoundError(f"Required file not found: {load_file}")
        
        # Load configs
        extract_config = _load_config_input(extract_file, variables)
        load_config = _load_config_input(load_file, variables)
        transform_config = _load_config_input(transform_file, variables) if transform_file.exists() else {}
        
        return cls._build_from_configs(
            extract_config=extract_config,
            transform_config=transform_config,
            load_config=load_config,
            variables=variables,
            validate=validate,
            name=name or directory.name,
        )
    
    @classmethod
    def from_config_file(
        cls,
        path: Union[str, Path],
        variables: Optional[Dict[str, str]] = None,
        validate: bool = True,
    ) -> "Pipeline":
        """
        Create pipeline from a single config file containing all sections.
        
        The file should have extract, transform (optional), and load sections:
        
            name: my_pipeline
            extract:
              type: http
              url: https://api.example.com
            transform:
              - rename: {old: new}
            load:
              type: file
              path: output.json
        
        Args:
            path: Path to pipeline config file (YAML)
            variables: Variables for ${VAR} substitution
            validate: If True, validate config against schema
        
        Returns:
            Configured Pipeline instance
        
        Example:
            pipeline = Pipeline.from_config_file(
                "pipelines/users/pipeline.yaml",
                variables={"API_KEY": "secret"}
            )
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        if not path.is_file():
            raise ValueError(f"Not a file: {path}. Use from_config_dir() for directories.")
        
        variables = variables or {}
        
        # Load the full config
        config = _load_config_input(path, variables)
        
        if "extract" not in config:
            raise ValueError(f"Config file missing 'extract' section: {path}")
        if "load" not in config:
            raise ValueError(f"Config file missing 'load' section: {path}")
        
        return cls._build_from_configs(
            extract_config=config["extract"],
            transform_config=config.get("transform", {}),
            load_config=config["load"],
            variables=variables,
            validate=validate,
            name=config.get("name"),
        )
    
    @classmethod
    def from_dict(
        cls,
        config: Dict[str, Any],
        variables: Optional[Dict[str, str]] = None,
        validate: bool = True,
    ) -> "Pipeline":
        """
        Create pipeline from a configuration dictionary.
        
        Args:
            config: Dict with 'extract', 'transform' (optional), 'load' sections
            variables: Variables for ${VAR} substitution
            validate: If True, validate config against schema
        
        Returns:
            Configured Pipeline instance
        
        Example:
            pipeline = Pipeline.from_dict({
                "name": "my_pipeline",
                "extract": {"type": "http", "url": "https://api.example.com"},
                "transform": [{"rename": {"userId": "user_id"}}],
                "load": {"type": "file", "path": "${OUTPUT_DIR}/result.json"}
            }, variables={"OUTPUT_DIR": "./output"})
        """
        if "extract" not in config:
            raise ValueError("Config dict missing 'extract' section")
        if "load" not in config:
            raise ValueError("Config dict missing 'load' section")
        
        variables = variables or {}
        context = PipelineContext(variables=variables)
        
        # Resolve variables in config
        extract_config = context.resolve_dict(config["extract"])
        raw_transform = config.get("transform", {})
        if isinstance(raw_transform, list):
            transform_config = [
                context.resolve_dict(item) if isinstance(item, dict) else item
                for item in raw_transform
            ]
        else:
            transform_config = context.resolve_dict(raw_transform)
        load_config = context.resolve_dict(config["load"])
        
        return cls._build_from_configs(
            extract_config=extract_config,
            transform_config=transform_config,
            load_config=load_config,
            variables=variables,
            validate=validate,
            name=config.get("name"),
        )
    
    @classmethod
    def _build_from_configs(
        cls,
        extract_config: Dict[str, Any],
        transform_config: Union[Dict[str, Any], List[Dict[str, Any]]],
        load_config: Dict[str, Any],
        variables: Dict[str, str],
        validate: bool,
        name: Optional[str],
    ) -> "Pipeline":
        """Internal method to build pipeline from resolved configs."""
        from pycharter.etl_generator.config_validator import ConfigValidator
        
        # Validate if enabled
        if validate:
            validator = ConfigValidator(strict=True)
            validator.validate_extract(extract_config)
            if transform_config:
                # Wrap list in dict for validation
                if isinstance(transform_config, list):
                    validator.validate_transform({"transform": transform_config})
                else:
                    validator.validate_transform(transform_config)
            validator.validate_load(load_config)
        
        # Create context
        context = PipelineContext(variables=variables)
        
        # Create components
        extractor = _create_extractor(extract_config)
        transformers = _create_transformers(transform_config)
        loader_instance = _create_loader(load_config)
        
        return cls(
            extractor=extractor,
            transformers=transformers,
            loader=loader_instance,
            context=context,
            name=name,
        )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _load_config_input(
    config_input: Union[str, Path, Dict[str, Any], List[Dict[str, Any]]],
    variables: Dict[str, str],
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """Load config from file path or return dict/list directly."""
    if isinstance(config_input, (dict, list)):
        return config_input
    
    path = Path(config_input)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    
    with open(path) as f:
        content = f.read()
    
    # Resolve variables in content before parsing
    content = _resolve_variables(content, variables)
    
    return yaml.safe_load(content) or {}


def _resolve_variables(content: str, variables: Dict[str, str]) -> str:
    """Resolve ${VAR} placeholders in content string."""
    def replace_var(match):
        var_name = match.group(1)
        modifier = match.group(2)
        modifier_value = match.group(3)
        
        # Check provided variables first, then environment
        value = variables.get(var_name) or os.environ.get(var_name)
        
        if value:
            return value
        
        # Handle modifiers
        if modifier == "-":
            return modifier_value if modifier_value is not None else ""
        elif modifier == "?":
            error_msg = modifier_value or f"Required variable {var_name} is not set"
            raise ValueError(error_msg)
        
        return match.group(0)
    
    return VARIABLE_PATTERN.sub(replace_var, content)


def _create_extractor(config: Dict[str, Any]) -> Optional[Extractor]:
    """Create extractor from config using explicit type field."""
    if not config:
        return None
    
    from pycharter.etl_generator.extractors import (
        HTTPExtractor,
        FileExtractor,
        DatabaseExtractor,
        CloudStorageExtractor,
    )
    
    EXTRACTOR_REGISTRY = {
        "http": HTTPExtractor,
        "file": FileExtractor,
        "database": DatabaseExtractor,
        "cloud_storage": CloudStorageExtractor,
    }
    
    # Get type field
    extract_type = config.get("type")
    
    if not extract_type:
        raise ValueError(
            "Extract config missing required 'type' field. "
            f"Supported types: {list(EXTRACTOR_REGISTRY.keys())}"
        )
    
    extract_type = extract_type.lower()
    extractor_class = EXTRACTOR_REGISTRY.get(extract_type)
    
    if not extractor_class:
        raise ValueError(
            f"Unknown extractor type: '{extract_type}'. "
            f"Supported types: {list(EXTRACTOR_REGISTRY.keys())}"
        )
    
    return extractor_class.from_config(config)


def _create_transformers(config: Union[Dict[str, Any], List[Dict[str, Any]]]) -> List[Transformer]:
    """Create transformer chain from config."""
    if not config:
        return []
    
    # Handle nested 'transform' key
    if isinstance(config, dict) and "transform" in config:
        config = config["transform"]
    
    # List format - ordered transforms
    if isinstance(config, list):
        return _create_transformers_from_list(config)
    
    # Dict format - fixed order
    return _create_transformers_from_dict(config)


def _create_transformers_from_list(config: List[Dict[str, Any]]) -> List[Transformer]:
    """Create transformers from list format (user-specified order)."""
    transformers = []
    
    for step in config:
        if not isinstance(step, dict):
            logger.warning(f"Invalid transform step (expected dict): {step}")
            continue
        
        for op_name, op_config in step.items():
            transformer = _create_single_transformer(op_name, op_config)
            if transformer:
                if isinstance(transformer, list):
                    transformers.extend(transformer)
                else:
                    transformers.append(transformer)
    
    return transformers


def _create_transformers_from_dict(config: Dict[str, Any]) -> List[Transformer]:
    """Create transformers from dict format (fixed order)."""
    transformers = []
    ordered_ops = ["rename", "convert", "defaults", "add", "select", "drop", "filter", "custom_function"]
    
    for op_name in ordered_ops:
        if op_name in config:
            transformer = _create_single_transformer(op_name, config[op_name])
            if transformer:
                if isinstance(transformer, list):
                    transformers.extend(transformer)
                else:
                    transformers.append(transformer)
    
    return transformers


def _create_single_transformer(op_name: str, op_config: Any) -> Optional[Union[Transformer, List[Transformer]]]:
    """Create a single transformer from operation name and config."""
    from pycharter.etl_generator.transformers import (
        Rename, AddField, Drop, Select, Filter, Convert, Default, CustomFunction,
    )
    from pycharter.etl_generator.transformers.simple_operations import convert_type
    
    op_name = op_name.lower()
    
    if op_name == "rename":
        if isinstance(op_config, dict):
            return Rename(op_config)
    
    elif op_name == "add":
        if isinstance(op_config, dict):
            return [AddField(field, value) for field, value in op_config.items()]
    
    elif op_name == "drop":
        if isinstance(op_config, list):
            return Drop(op_config)
    
    elif op_name == "select":
        if isinstance(op_config, list):
            return Select(op_config)
    
    elif op_name == "convert":
        if isinstance(op_config, dict):
            type_map = {
                "int": int, "integer": int,
                "float": float, "number": float, "numeric": float,
                "str": str, "string": str,
                "bool": bool, "boolean": bool,
            }
            conversions = {}
            for field, target_type in op_config.items():
                target_lower = target_type.lower() if isinstance(target_type, str) else str(target_type)
                if target_lower in type_map:
                    conversions[field] = type_map[target_lower]
                elif target_lower in ("datetime", "date"):
                    conversions[field] = lambda v, t=target_lower: convert_type(v, t)
                else:
                    conversions[field] = str
            return Convert(conversions)
    
    elif op_name == "defaults":
        if isinstance(op_config, dict):
            return Default(op_config)
    
    elif op_name == "filter":
        if isinstance(op_config, dict):
            field = op_config.get("field")
            operator = op_config.get("operator", "eq")
            value = op_config.get("value")
            if field and operator:
                predicate = _create_filter_predicate(field, operator, value)
                if predicate:
                    return Filter(predicate)
    
    elif op_name == "custom_function":
        if isinstance(op_config, dict):
            return CustomFunction(
                module=op_config.get("module"),
                function=op_config.get("function"),
                kwargs=op_config.get("kwargs", {}),
            )
    
    else:
        logger.warning(f"Unknown transform operation: {op_name}")
    
    return None


def _create_filter_predicate(field: str, operator: str, value: Any) -> Optional[Callable]:
    """Create a filter predicate function from operator and value."""
    operators = {
        "eq": lambda r: r.get(field) == value,
        "ne": lambda r: r.get(field) != value,
        "gt": lambda r: r.get(field) is not None and r.get(field) > value,
        "gte": lambda r: r.get(field) is not None and r.get(field) >= value,
        "lt": lambda r: r.get(field) is not None and r.get(field) < value,
        "lte": lambda r: r.get(field) is not None and r.get(field) <= value,
        "in": lambda r: r.get(field) in (value if isinstance(value, (list, tuple, set)) else [value]),
        "not_in": lambda r: r.get(field) not in (value if isinstance(value, (list, tuple, set)) else [value]),
        "contains": lambda r: value in str(r.get(field, "")),
        "not_contains": lambda r: value not in str(r.get(field, "")),
        "is_null": lambda r: r.get(field) is None,
        "is_not_null": lambda r: r.get(field) is not None,
    }
    return operators.get(operator)


def _create_loader(config: Dict[str, Any]) -> Optional[Loader]:
    """Create loader from config using explicit type field."""
    if not config:
        return None
    
    from pycharter.etl_generator.loaders import (
        PostgresLoader,
        FileLoader,
        CloudStorageLoader,
    )
    
    LOADER_REGISTRY = {
        "postgres": PostgresLoader,
        "postgresql": PostgresLoader,
        "database": PostgresLoader,
        "sqlite": PostgresLoader,
        "file": FileLoader,
        "cloud_storage": CloudStorageLoader,
    }
    
    # Get type field
    load_type = config.get("type")
    
    if not load_type:
        raise ValueError(
            "Load config missing required 'type' field. "
            f"Supported types: postgres, sqlite, file, cloud_storage"
        )
    
    load_type = load_type.lower()
    loader_class = LOADER_REGISTRY.get(load_type)
    
    if not loader_class:
        raise ValueError(
            f"Unknown loader type: '{load_type}'. "
            f"Supported types: postgres, sqlite, file, cloud_storage"
        )
    
    return loader_class.from_config(config)
