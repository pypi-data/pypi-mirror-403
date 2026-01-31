"""
Pipeline context for variable resolution.

Provides a simple, flexible way to pass variables into pipeline configurations.
"""

import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

# Variable pattern: ${VAR_NAME} or ${VAR_NAME:-default} or ${VAR_NAME:?error}
VARIABLE_PATTERN = re.compile(r'\$\{([^}:]+)(?::([?-])([^}]*))?\}')


@dataclass
class PipelineContext:
    """
    Pipeline execution context with variable resolution.
    
    A simple container for variables that can be substituted into pipeline configs.
    
    Resolves ${VAR} placeholders from:
    1. Provided variables (highest priority)
    2. Environment variables (fallback)
    
    Supports:
    - ${VAR} - Use variable value
    - ${VAR:-default} - Use default if not set
    - ${VAR:?error} - Raise error if not set
    
    Example:
        >>> context = PipelineContext(variables={
        ...     "API_KEY": "secret",
        ...     "DATA_DIR": "/path/to/data",
        ...     "OUTPUT_DIR": "./output"
        ... })
        >>> context.resolve("${DATA_DIR}/input.json")
        '/path/to/data/input.json'
        >>> context.resolve("${MISSING:-default_value}")
        'default_value'
    """
    
    variables: Dict[str, Any] = field(default_factory=dict)
    
    def resolve(self, value: str) -> str:
        """
        Resolve ${VAR} placeholders in a string.
        
        Args:
            value: String potentially containing ${VAR} placeholders
            
        Returns:
            String with placeholders resolved
            
        Raises:
            ValueError: If ${VAR:?error} syntax is used and variable is not set
        """
        if not isinstance(value, str):
            return value
        
        def replace_var(match):
            var_name = match.group(1)
            modifier = match.group(2)  # '-' for default, '?' for required
            modifier_value = match.group(3)
            
            # Check variables dict first
            if var_name in self.variables:
                return str(self.variables[var_name])
            
            # Check environment
            env_value = os.environ.get(var_name)
            if env_value:
                return env_value
            
            # Handle modifiers
            if modifier == "-":
                return modifier_value if modifier_value is not None else ""
            elif modifier == "?":
                error_msg = modifier_value or f"Required variable {var_name} is not set"
                raise ValueError(error_msg)
            
            # No modifier - keep original placeholder
            return match.group(0)
        
        return VARIABLE_PATTERN.sub(replace_var, value)
    
    def resolve_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively resolve variables in a dictionary.
        
        Args:
            data: Dictionary potentially containing ${VAR} placeholders in values
            
        Returns:
            Dictionary with all string values resolved
        """
        if not data:
            return data
            
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self.resolve(value)
            elif isinstance(value, dict):
                result[key] = self.resolve_dict(value)
            elif isinstance(value, list):
                result[key] = [
                    self.resolve(v) if isinstance(v, str) 
                    else self.resolve_dict(v) if isinstance(v, dict)
                    else v
                    for v in value
                ]
            else:
                result[key] = value
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context variables to dictionary."""
        return dict(self.variables)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a variable value."""
        return self.variables.get(key, os.environ.get(key, default))
    
    def set(self, key: str, value: Any) -> None:
        """Set a variable value."""
        self.variables[key] = value
    
    def update(self, variables: Dict[str, Any]) -> None:
        """Update variables from a dictionary."""
        self.variables.update(variables)
