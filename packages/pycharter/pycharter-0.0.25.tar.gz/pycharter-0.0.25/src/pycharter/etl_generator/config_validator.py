"""
Configuration validation for ETL pipelines.

Provides validation of extract, transform, and load configurations
with clear, actionable error messages.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    import jsonschema
    from jsonschema import Draft7Validator, ValidationError as JsonschemaValidationError
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    JsonschemaValidationError = Exception  # type: ignore[misc, assignment]

from pycharter.shared.errors import ConfigValidationError
from pycharter.etl_generator.schemas import (
    get_extract_schema,
    get_transform_schema,
    get_load_schema,
    get_pipeline_schema,
)


class ConfigValidator:
    """
    Validates ETL pipeline configurations against JSON schemas.
    
    Provides clear error messages to help users fix configuration issues.
    
    Usage:
        validator = ConfigValidator()
        
        # Validate individual configs
        validator.validate_extract(extract_config)
        validator.validate_transform(transform_config)
        validator.validate_load(load_config)
        
        # Validate combined pipeline
        validator.validate_pipeline(pipeline_config)
        
        # Check if valid without raising
        is_valid, errors = validator.check_extract(extract_config)
    """
    
    def __init__(self, strict: bool = True):
        """
        Initialize the validator.
        
        Args:
            strict: If True, raise errors on validation failure.
                   If False, return errors without raising.
        """
        self.strict = strict
        self._extract_schema = None
        self._transform_schema = None
        self._load_schema = None
        self._pipeline_schema = None
    
    @property
    def extract_schema(self) -> Dict[str, Any]:
        if self._extract_schema is None:
            self._extract_schema = get_extract_schema()
        return self._extract_schema
    
    @property
    def transform_schema(self) -> Dict[str, Any]:
        if self._transform_schema is None:
            self._transform_schema = get_transform_schema()
        return self._transform_schema
    
    @property
    def load_schema(self) -> Dict[str, Any]:
        if self._load_schema is None:
            self._load_schema = get_load_schema()
        return self._load_schema
    
    @property
    def pipeline_schema(self) -> Dict[str, Any]:
        if self._pipeline_schema is None:
            self._pipeline_schema = get_pipeline_schema()
        return self._pipeline_schema
    
    def _validate(
        self,
        config: Dict[str, Any],
        schema: Dict[str, Any],
        config_type: str,
        config_path: Optional[str] = None,
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate config against schema.
        
        Returns:
            Tuple of (is_valid, list of error dicts)
        """
        if not HAS_JSONSCHEMA:
            # If jsonschema not installed, do basic validation
            return self._basic_validate(config, config_type)
        
        errors = []
        validator = Draft7Validator(schema)
        
        for error in sorted(validator.iter_errors(config), key=lambda e: str(e.path)):
            error_dict = {
                "path": ".".join(str(p) for p in error.absolute_path) or "(root)",
                "message": self._format_error_message(error, config_type),
                "validator": error.validator,
                "schema_path": list(error.schema_path),
            }
            errors.append(error_dict)
        
        return len(errors) == 0, errors
    
    def _basic_validate(
        self,
        config: Dict[str, Any],
        config_type: str,
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """Basic validation without jsonschema library."""
        errors = []
        
        if config_type == "extract":
            if "type" not in config:
                errors.append({
                    "path": "type",
                    "message": "Missing required field 'type'. Must be one of: http, file, database, cloud_storage",
                })
            elif config["type"] not in ("http", "file", "database", "cloud_storage"):
                errors.append({
                    "path": "type",
                    "message": f"Invalid type '{config['type']}'. Must be one of: http, file, database, cloud_storage",
                })
        
        elif config_type == "load":
            if "type" not in config:
                errors.append({
                    "path": "type",
                    "message": "Missing required field 'type'. Must be one of: postgres, sqlite, file, cloud_storage",
                })
            elif config["type"] not in ("postgres", "postgresql", "sqlite", "database", "file", "cloud_storage"):
                errors.append({
                    "path": "type",
                    "message": f"Invalid type '{config['type']}'. Must be one of: postgres, sqlite, file, cloud_storage",
                })
        
        elif config_type == "pipeline":
            if "extract" not in config:
                errors.append({
                    "path": "extract",
                    "message": "Missing required section 'extract'",
                })
            if "load" not in config:
                errors.append({
                    "path": "load",
                    "message": "Missing required section 'load'",
                })
        
        return len(errors) == 0, errors
    
    def _format_error_message(self, error: JsonschemaValidationError, config_type: str) -> str:
        """Format a validation error into a user-friendly message."""
        msg = error.message
        
        # Improve common error messages
        if error.validator == "required":
            missing = list(error.validator_value)
            if "type" in missing:
                valid_types = {
                    "extract": "http, file, database, cloud_storage",
                    "load": "postgres, sqlite, file, cloud_storage",
                }
                types = valid_types.get(config_type, "")
                if types:
                    return f"Missing required 'type' field. Must be one of: {types}"
            return f"Missing required field(s): {', '.join(missing)}"
        
        elif error.validator == "enum":
            allowed = error.validator_value
            return f"Invalid value. Allowed values: {', '.join(str(v) for v in allowed)}"
        
        elif error.validator == "type":
            expected = error.validator_value
            actual = type(error.instance).__name__
            return f"Expected {expected}, got {actual}"
        
        elif error.validator == "anyOf":
            return "Config doesn't match any of the allowed patterns"
        
        elif error.validator == "oneOf":
            return "Config must match exactly one of the allowed patterns"
        
        return msg
    
    def validate_extract(
        self,
        config: Dict[str, Any],
        config_path: Optional[str] = None,
    ) -> None:
        """
        Validate extract configuration.
        
        Args:
            config: Extract configuration dict
            config_path: Optional path to config file (for error messages)
            
        Raises:
            ConfigValidationError: If validation fails and strict=True
        """
        is_valid, errors = self._validate(config, self.extract_schema, "extract", config_path)
        
        if not is_valid and self.strict:
            raise ConfigValidationError(
                f"Invalid extract configuration",
                errors=errors,
                config_type="extract",
                config_path=config_path,
            )
    
    def validate_transform(
        self,
        config: Dict[str, Any],
        config_path: Optional[str] = None,
    ) -> None:
        """
        Validate transform configuration.
        
        Args:
            config: Transform configuration dict
            config_path: Optional path to config file (for error messages)
            
        Raises:
            ConfigValidationError: If validation fails and strict=True
        """
        # Transform is optional, empty config is valid
        if not config:
            return
        
        is_valid, errors = self._validate(config, self.transform_schema, "transform", config_path)
        
        if not is_valid and self.strict:
            raise ConfigValidationError(
                f"Invalid transform configuration",
                errors=errors,
                config_type="transform",
                config_path=config_path,
            )
    
    def validate_load(
        self,
        config: Dict[str, Any],
        config_path: Optional[str] = None,
    ) -> None:
        """
        Validate load configuration.
        
        Args:
            config: Load configuration dict
            config_path: Optional path to config file (for error messages)
            
        Raises:
            ConfigValidationError: If validation fails and strict=True
        """
        is_valid, errors = self._validate(config, self.load_schema, "load", config_path)
        
        if not is_valid and self.strict:
            raise ConfigValidationError(
                f"Invalid load configuration",
                errors=errors,
                config_type="load",
                config_path=config_path,
            )
    
    def validate_pipeline(
        self,
        config: Dict[str, Any],
        config_path: Optional[str] = None,
    ) -> None:
        """
        Validate complete pipeline configuration.
        
        Args:
            config: Pipeline configuration dict with extract, transform, load sections
            config_path: Optional path to config file (for error messages)
            
        Raises:
            ConfigValidationError: If validation fails and strict=True
        """
        # Basic structure validation
        errors = []
        
        if "extract" not in config:
            errors.append({
                "path": "extract",
                "message": "Missing required 'extract' section",
            })
        else:
            is_valid, extract_errors = self._validate(
                config["extract"], self.extract_schema, "extract"
            )
            for e in extract_errors:
                e["path"] = f"extract.{e['path']}" if e["path"] != "(root)" else "extract"
            errors.extend(extract_errors)
        
        if "transform" in config and config["transform"]:
            # Validate transform if present
            transform_config = config["transform"]
            # If transform is directly the operations (list or dict), wrap it
            if isinstance(transform_config, (list, dict)):
                if isinstance(transform_config, list) or not any(
                    k in transform_config for k in ("transform", "jsonata", "custom_function")
                ):
                    transform_config = {"transform": transform_config}
            
            is_valid, transform_errors = self._validate(
                transform_config, self.transform_schema, "transform"
            )
            for e in transform_errors:
                e["path"] = f"transform.{e['path']}" if e["path"] != "(root)" else "transform"
            errors.extend(transform_errors)
        
        if "load" not in config:
            errors.append({
                "path": "load",
                "message": "Missing required 'load' section",
            })
        else:
            is_valid, load_errors = self._validate(
                config["load"], self.load_schema, "load"
            )
            for e in load_errors:
                e["path"] = f"load.{e['path']}" if e["path"] != "(root)" else "load"
            errors.extend(load_errors)
        
        if errors and self.strict:
            raise ConfigValidationError(
                f"Invalid pipeline configuration",
                errors=errors,
                config_type="pipeline",
                config_path=config_path,
            )
    
    def check_extract(
        self,
        config: Dict[str, Any],
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """Check extract config without raising. Returns (is_valid, errors)."""
        return self._validate(config, self.extract_schema, "extract")
    
    def check_transform(
        self,
        config: Dict[str, Any],
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """Check transform config without raising. Returns (is_valid, errors)."""
        if not config:
            return True, []
        return self._validate(config, self.transform_schema, "transform")
    
    def check_load(
        self,
        config: Dict[str, Any],
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """Check load config without raising. Returns (is_valid, errors)."""
        return self._validate(config, self.load_schema, "load")


def validate_config(
    config: Dict[str, Any],
    config_type: str = "pipeline",
    config_path: Optional[str] = None,
    strict: bool = True,
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Convenience function to validate a config.
    
    Args:
        config: Configuration dict
        config_type: One of "extract", "transform", "load", "pipeline"
        config_path: Optional path to config file
        strict: If True, raise on validation failure
        
    Returns:
        Tuple of (is_valid, errors)
        
    Raises:
        ConfigValidationError: If strict=True and validation fails
    """
    validator = ConfigValidator(strict=strict)
    
    if config_type == "extract":
        validator.validate_extract(config, config_path)
        return validator.check_extract(config)
    elif config_type == "transform":
        validator.validate_transform(config, config_path)
        return validator.check_transform(config)
    elif config_type == "load":
        validator.validate_load(config, config_path)
        return validator.check_load(config)
    elif config_type == "pipeline":
        validator.validate_pipeline(config, config_path)
        # Return combined check
        errors = []
        if "extract" in config:
            _, e = validator.check_extract(config["extract"])
            errors.extend(e)
        if "transform" in config:
            _, e = validator.check_transform(config.get("transform", {}))
            errors.extend(e)
        if "load" in config:
            _, e = validator.check_load(config["load"])
            errors.extend(e)
        return len(errors) == 0, errors
    else:
        raise ValueError(f"Unknown config_type: {config_type}")
