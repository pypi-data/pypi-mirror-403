"""
Standardized error handling for pycharter.

Exception hierarchy:
- PyCharterError: Base for all pycharter exceptions (catch this for any pycharter error)
- ConfigError: Config loading/parsing failures (e.g. missing file, invalid YAML)
- ConfigValidationError: Schema validation failures (e.g. missing required 'type' field)
- ExpressionError: Expression evaluation failures (e.g. invalid syntax in add field)

Error handling modes:
- STRICT: Raise exceptions immediately on errors
- LENIENT: Log warnings and continue (best effort)
- COLLECT: Collect errors and return them with results
"""

import logging
import warnings
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# EXCEPTION HIERARCHY
# =============================================================================


class PyCharterError(Exception):
    """
    Base exception for all pycharter errors.
    
    Catch this to handle any pycharter-related failure without depending on
    specific exception types. Subclasses provide more specific handling.
    
    Example:
        try:
            pipeline = Pipeline.from_config_files(extract="e.yaml", load="l.yaml")
        except PyCharterError as e:
            logger.error("Pipeline config failed: %s", e)
    """
    pass


class ConfigError(PyCharterError):
    """
    Raised when configuration cannot be loaded or parsed.
    
    Use for: missing files, invalid YAML/JSON, I/O errors during config load.
    """
    def __init__(self, message: str, path: Optional[str] = None):
        self.path = path
        super().__init__(message + (f" (path: {path})" if path else ""))


class ConfigValidationError(PyCharterError):
    """
    Raised when configuration fails schema validation.
    
    Use for: missing required fields (e.g. 'type'), invalid structure,
    schema constraint violations. May include a list of validation errors.
    """
    def __init__(
        self,
        message: str,
        errors: Optional[List[dict]] = None,
        config_type: Optional[str] = None,
        config_path: Optional[str] = None,
    ):
        self.message = message
        self.errors = errors or []
        self.config_type = config_type
        self.config_path = config_path
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        parts = [self.message]
        if self.config_path:
            parts.append(f"  File: {self.config_path}")
        if self.errors:
            parts.append("\nValidation errors:")
            for i, error in enumerate(self.errors[:10], 1):
                path = error.get("path", "")
                msg = error.get("message", "Unknown error")
                parts.append(f"  {i}. {path}: {msg}" if path else f"  {i}. {msg}")
            if len(self.errors) > 10:
                parts.append(f"  ... and {len(self.errors) - 10} more errors")
        return "\n".join(parts)


class ConfigLoadError(ConfigError):
    """
    Raised when pipeline config cannot be loaded (missing file, invalid YAML, I/O).
    
    Subclass of ConfigError for backward compatibility and ETL-specific usage.
    """
    pass


class ExpressionError(PyCharterError):
    """
    Raised when an expression cannot be evaluated (e.g. in add field, defaults).
    
    Use for: invalid expression syntax, missing variables, type errors in evaluation.
    """
    pass


class ErrorMode(Enum):
    """Error handling mode for pycharter operations."""
    
    STRICT = "strict"
    """Raise exceptions immediately on any error."""
    
    LENIENT = "lenient"
    """Log warnings and continue with best effort."""
    
    COLLECT = "collect"
    """Collect errors and return them with results."""


@dataclass
class ErrorContext:
    """
    Context for tracking errors during operations.
    
    Use with ErrorMode.COLLECT to gather errors without stopping.
    """
    
    mode: ErrorMode = ErrorMode.LENIENT
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def handle_error(
        self,
        message: str,
        exception: Optional[Exception] = None,
        category: str = "error",
    ) -> None:
        """
        Handle an error according to the current mode.
        
        Args:
            message: Error message
            exception: Optional exception that caused the error
            category: Error category for logging
        """
        full_message = f"{category}: {message}"
        if exception:
            full_message += f" ({type(exception).__name__}: {exception})"
        
        if self.mode == ErrorMode.STRICT:
            if exception:
                raise type(exception)(full_message) from exception
            raise ValueError(full_message)
        
        elif self.mode == ErrorMode.LENIENT:
            warnings.warn(full_message)
            logger.warning(full_message)
            self.warnings.append(full_message)
        
        elif self.mode == ErrorMode.COLLECT:
            self.errors.append(full_message)
            logger.warning(full_message)
    
    def handle_warning(self, message: str, category: str = "warning") -> None:
        """
        Handle a warning (non-fatal issue).
        
        Args:
            message: Warning message
            category: Warning category
        """
        full_message = f"{category}: {message}"
        warnings.warn(full_message)
        logger.warning(full_message)
        self.warnings.append(full_message)
    
    @property
    def has_errors(self) -> bool:
        """Whether any errors were collected."""
        return len(self.errors) > 0
    
    def raise_if_errors(self) -> None:
        """Raise ValueError if any errors were collected."""
        if self.errors:
            raise ValueError(f"Errors occurred: {'; '.join(self.errors)}")
    
    def clear(self) -> None:
        """Clear all errors and warnings."""
        self.errors.clear()
        self.warnings.clear()


# Default error context (lenient by default)
_default_context = ErrorContext(mode=ErrorMode.LENIENT)


def get_error_context() -> ErrorContext:
    """Get the default error context."""
    return _default_context


def set_error_mode(mode: ErrorMode) -> None:
    """
    Set the default error handling mode.
    
    Args:
        mode: Error mode to use
    """
    _default_context.mode = mode


def handle_error(
    message: str,
    exception: Optional[Exception] = None,
    category: str = "error",
    context: Optional[ErrorContext] = None,
) -> None:
    """
    Handle an error using the specified or default context.
    
    Args:
        message: Error message
        exception: Optional exception that caused the error
        category: Error category
        context: Optional error context (uses default if not provided)
    """
    ctx = context or _default_context
    ctx.handle_error(message, exception, category)


def handle_warning(
    message: str,
    category: str = "warning",
    context: Optional[ErrorContext] = None,
) -> None:
    """
    Handle a warning using the specified or default context.
    
    Args:
        message: Warning message
        category: Warning category
        context: Optional error context (uses default if not provided)
    """
    ctx = context or _default_context
    ctx.handle_warning(message, category)


class StrictMode:
    """
    Context manager for temporarily enabling strict mode.
    
    Example:
        >>> with StrictMode():
        ...     # Errors will raise exceptions
        ...     validator.validate(data)
    """
    
    def __init__(self):
        self._previous_mode: Optional[ErrorMode] = None
    
    def __enter__(self):
        self._previous_mode = _default_context.mode
        _default_context.mode = ErrorMode.STRICT
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._previous_mode is not None:
            _default_context.mode = self._previous_mode
        return False


class LenientMode:
    """
    Context manager for temporarily enabling lenient mode.
    
    Example:
        >>> with LenientMode():
        ...     # Errors will be logged as warnings
        ...     validator.validate(data)
    """
    
    def __init__(self):
        self._previous_mode: Optional[ErrorMode] = None
    
    def __enter__(self):
        self._previous_mode = _default_context.mode
        _default_context.mode = ErrorMode.LENIENT
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._previous_mode is not None:
            _default_context.mode = self._previous_mode
        return False
