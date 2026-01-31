"""
Unified configuration loader for ETL pipelines.

Supports both single-file (pipeline.yaml) and multi-file (extract.yaml, transform.yaml, load.yaml) formats.
Handles variable resolution and config validation.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import yaml

from pycharter.shared.errors import ConfigLoadError
from pycharter.etl_generator.config_validator import (
    ConfigValidator,
    ConfigValidationError,
)


# Variable pattern: ${VAR_NAME} or ${VAR_NAME:-default} or ${VAR_NAME:?error}
VARIABLE_PATTERN = re.compile(r'\$\{([^}:]+)(?::([?-])([^}]*))?\}')


class PipelineConfig:
    """
    Loaded and validated pipeline configuration.
    
    Attributes:
        extract: Extract configuration dict
        transform: Transform configuration dict (may be empty)
        load: Load configuration dict
        name: Pipeline name (from config or directory name)
        version: Pipeline version (if specified)
        source_path: Path to the config file or directory
    """
    
    def __init__(
        self,
        extract: Dict[str, Any],
        transform: Dict[str, Any],
        load: Dict[str, Any],
        name: Optional[str] = None,
        version: Optional[str] = None,
        source_path: Optional[str] = None,
    ):
        self.extract = extract
        self.transform = transform
        self.load = load
        self.name = name
        self.version = version
        self.source_path = source_path
    
    def __repr__(self) -> str:
        return f"PipelineConfig(name={self.name!r}, source={self.source_path!r})"


class ConfigLoader:
    """
    Loads ETL pipeline configurations from files or directories.
    
    Supports:
    - Single-file format: pipeline.yaml with extract, transform, load sections
    - Multi-file format: Directory with extract.yaml, transform.yaml, load.yaml
    - Variable resolution: ${VAR}, ${VAR:-default}, ${VAR:?error}
    - Config validation with clear error messages
    
    Usage:
        loader = ConfigLoader()
        
        # Load from single file
        config = loader.load("pipelines/users/pipeline.yaml")
        
        # Load from directory
        config = loader.load("pipelines/users/")
        
        # Load with variables
        config = loader.load("pipelines/users/", variables={"API_KEY": "xxx"})
    """
    
    def __init__(
        self,
        validate: bool = True,
        strict: bool = True,
    ):
        """
        Initialize the config loader.
        
        Args:
            validate: If True, validate configs against schemas
            strict: If True, raise errors on validation failure
        """
        self.validate = validate
        self.strict = strict
        self._validator = ConfigValidator(strict=strict) if validate else None
    
    def load(
        self,
        path: Union[str, Path],
        variables: Optional[Dict[str, str]] = None,
    ) -> PipelineConfig:
        """
        Load pipeline configuration from a file or directory.
        
        Args:
            path: Path to config file or directory
            variables: Additional variables for resolution (in addition to env vars)
            
        Returns:
            PipelineConfig with loaded and validated configuration
            
        Raises:
            ConfigLoadError: If config files cannot be found or loaded
            ConfigValidationError: If config validation fails
        """
        path = Path(path).resolve()
        
        if path.is_file():
            return self._load_single_file(path, variables)
        elif path.is_dir():
            return self._load_multi_file(path, variables)
        else:
            # Check if it's a path without extension
            for ext in (".yaml", ".yml"):
                single_file = path.with_suffix(ext)
                if single_file.exists():
                    return self._load_single_file(single_file, variables)
            
            # Check if adding pipeline.yaml works
            pipeline_file = path / "pipeline.yaml"
            if pipeline_file.exists():
                return self._load_single_file(pipeline_file, variables)
            
            raise ConfigLoadError(
                f"Config not found: {path}. Expected a YAML file or directory with config files.",
                str(path),
            )
    
    def _load_single_file(
        self,
        path: Path,
        variables: Optional[Dict[str, str]] = None,
    ) -> PipelineConfig:
        """Load configuration from a single pipeline.yaml file."""
        config = self._load_yaml(path, variables, str(path.parent))
        
        if not isinstance(config, dict):
            raise ConfigLoadError(
                f"Invalid config format: expected a dict, got {type(config).__name__}",
                str(path),
            )
        
        # Extract sections
        extract = config.get("extract")
        transform = config.get("transform", {})
        load = config.get("load")
        
        if extract is None:
            raise ConfigLoadError(
                "Missing 'extract' section in pipeline config",
                str(path),
            )
        
        if load is None:
            raise ConfigLoadError(
                "Missing 'load' section in pipeline config",
                str(path),
            )
        
        # Normalize transform config
        transform = self._normalize_transform(transform)
        
        # Validate if enabled
        if self._validator:
            self._validator.validate_pipeline(config, str(path))
        
        return PipelineConfig(
            extract=extract,
            transform=transform,
            load=load,
            name=config.get("name", path.stem),
            version=config.get("version"),
            source_path=str(path),
        )
    
    def _load_multi_file(
        self,
        directory: Path,
        variables: Optional[Dict[str, str]] = None,
    ) -> PipelineConfig:
        """Load configuration from separate extract.yaml, transform.yaml, load.yaml files."""
        contract_dir = str(directory)
        
        # Load extract config (required)
        extract_path = self._find_config_file(directory, "extract")
        if extract_path is None:
            raise ConfigLoadError(
                f"Missing extract config in {directory}. Expected extract.yaml or extract.yml",
                str(directory),
            )
        extract = self._load_yaml(extract_path, variables, contract_dir)
        
        # Load transform config (optional)
        transform_path = self._find_config_file(directory, "transform")
        if transform_path:
            transform = self._load_yaml(transform_path, variables, contract_dir)
            transform = self._normalize_transform(transform)
        else:
            transform = {}
        
        # Load load config (required)
        load_path = self._find_config_file(directory, "load")
        if load_path is None:
            raise ConfigLoadError(
                f"Missing load config in {directory}. Expected load.yaml or load.yml",
                str(directory),
            )
        load_config = self._load_yaml(load_path, variables, contract_dir)
        
        # Validate if enabled
        if self._validator:
            self._validator.validate_extract(extract, str(extract_path))
            if transform:
                self._validator.validate_transform(
                    {"transform": transform} if isinstance(transform, list) else transform,
                    str(transform_path) if transform_path else None,
                )
            self._validator.validate_load(load_config, str(load_path))
        
        return PipelineConfig(
            extract=extract,
            transform=transform,
            load=load_config,
            name=directory.name,
            source_path=str(directory),
        )
    
    def _find_config_file(self, directory: Path, name: str) -> Optional[Path]:
        """Find a config file by name, checking for .yaml and .yml extensions."""
        for ext in (".yaml", ".yml"):
            path = directory / f"{name}{ext}"
            if path.exists():
                return path
        return None
    
    def _load_yaml(
        self,
        path: Path,
        variables: Optional[Dict[str, str]] = None,
        contract_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Load and parse a YAML file with variable resolution."""
        try:
            with open(path) as f:
                content = f.read()
        except FileNotFoundError:
            raise ConfigLoadError(f"Config file not found: {path}", str(path))
        except IOError as e:
            raise ConfigLoadError(f"Error reading config file: {e}", str(path))
        
        # Resolve variables in the YAML content
        content = self._resolve_variables(content, variables, contract_dir)
        
        try:
            config = yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise ConfigLoadError(f"Invalid YAML: {e}", str(path))
        
        return config or {}
    
    def _resolve_variables(
        self,
        content: str,
        variables: Optional[Dict[str, str]] = None,
        contract_dir: Optional[str] = None,
    ) -> str:
        """
        Resolve ${VAR} placeholders in content.
        
        Supports:
        - ${VAR} - Use variable or env var
        - ${VAR:-default} - Use default if not set
        - ${VAR:?error message} - Raise error if not set
        """
        variables = variables or {}
        
        def replace_var(match):
            var_name = match.group(1)
            modifier = match.group(2)  # '-' for default, '?' for required
            modifier_value = match.group(3)  # default value or error message
            
            # Check variables dict first, then environment
            value = variables.get(var_name) or os.environ.get(var_name)
            
            if value:
                return value
            
            # Handle modifiers
            if modifier == "-":
                return modifier_value if modifier_value is not None else ""
            elif modifier == "?":
                error_msg = modifier_value or f"Required variable {var_name} is not set"
                raise ConfigLoadError(error_msg, path=None)
            
            # No modifier - return original placeholder (will be resolved later or cause error)
            return match.group(0)
        
        return VARIABLE_PATTERN.sub(replace_var, content)
    
    def _normalize_transform(
        self,
        transform: Union[Dict[str, Any], list, None],
    ) -> Union[Dict[str, Any], list]:
        """
        Normalize transform config to consistent format.
        
        Handles:
        - Empty/None -> {}
        - List (ordered) -> list (unchanged)
        - Dict with 'transform' key -> unwrap
        - Dict (legacy) -> dict (unchanged)
        """
        if transform is None:
            return {}
        
        if isinstance(transform, list):
            return transform
        
        if isinstance(transform, dict):
            # Check if wrapped in 'transform' key
            if "transform" in transform and len(transform) == 1:
                return transform["transform"]
            return transform
        
        return {}


def load_pipeline_config(
    path: Union[str, Path],
    variables: Optional[Dict[str, str]] = None,
    validate: bool = True,
) -> PipelineConfig:
    """
    Convenience function to load a pipeline configuration.
    
    Args:
        path: Path to config file or directory
        variables: Additional variables for resolution
        validate: If True, validate configs against schemas
        
    Returns:
        PipelineConfig with loaded configuration
    """
    loader = ConfigLoader(validate=validate)
    return loader.load(path, variables)


def detect_config_format(path: Union[str, Path]) -> str:
    """
    Detect whether a path points to single-file or multi-file config.
    
    Args:
        path: Path to check
        
    Returns:
        "single" for single-file format, "multi" for multi-file format
        
    Raises:
        ConfigLoadError: If config format cannot be determined
    """
    path = Path(path)
    
    if path.is_file():
        return "single"
    
    if path.is_dir():
        # Check for pipeline.yaml (single-file in directory)
        if (path / "pipeline.yaml").exists() or (path / "pipeline.yml").exists():
            return "single"
        
        # Check for extract.yaml (multi-file)
        if (path / "extract.yaml").exists() or (path / "extract.yml").exists():
            return "multi"
    
    # Check with extensions
    for ext in (".yaml", ".yml"):
        if path.with_suffix(ext).exists():
            return "single"
    
    raise ConfigLoadError(
        f"Cannot determine config format for: {path}",
        str(path),
    )
