"""
Runtime Validator Core - Core validation utilities.

This module provides low-level validation utilities that work directly with
Pydantic models. These are the building blocks for validation.

PRIMARY INTERFACE: Validator Class
==================================

For most use cases, use the Validator class from pycharter.runtime_validator.validator:

    >>> from pycharter.runtime_validator import Validator
    >>> validator = Validator(contract_dir="data/contracts/user")
    >>> result = validator.validate({"name": "Alice", "age": 30})

Core Functions (use when you already have a Pydantic model):
- ValidationResult: Result class for validation operations
- validate(): Validate data against a Pydantic model
- validate_batch(): Validate batch of data against a Pydantic model

For convenience wrapper functions that use the Validator class internally,
see pycharter.runtime_validator.wrappers.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel, ValidationError


@dataclass
class QualityMetrics:
    """
    Quality metrics for validated data.
    
    Attributes:
        completeness: Ratio of non-null fields (0.0 to 1.0)
        field_completeness: Per-field completeness ratios
        record_count: Number of records validated
        valid_count: Number of valid records
        error_count: Number of records with errors
    """
    completeness: float = 1.0
    field_completeness: Dict[str, float] = field(default_factory=dict)
    record_count: int = 0
    valid_count: int = 0
    error_count: int = 0
    
    @property
    def validity_rate(self) -> float:
        """Ratio of valid records."""
        if self.record_count == 0:
            return 1.0
        return self.valid_count / self.record_count
    
    def passes_thresholds(self, thresholds: Dict[str, float]) -> bool:
        """Check if metrics pass the specified thresholds."""
        if "completeness" in thresholds and self.completeness < thresholds["completeness"]:
            return False
        if "validity_rate" in thresholds and self.validity_rate < thresholds["validity_rate"]:
            return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "completeness": self.completeness,
            "field_completeness": self.field_completeness,
            "record_count": self.record_count,
            "valid_count": self.valid_count,
            "error_count": self.error_count,
            "validity_rate": self.validity_rate,
        }


class ValidationResult:
    """
    Result of a validation operation.

    Attributes:
        is_valid: Whether validation passed
        data: Validated data (Pydantic model instance) if valid
        errors: List of validation errors if invalid
        quality: Optional quality metrics
    """

    def __init__(
        self,
        is_valid: bool,
        data: Optional[BaseModel] = None,
        errors: Optional[List[str]] = None,
        quality: Optional[QualityMetrics] = None,
    ):
        self.is_valid = is_valid
        self.data = data
        self.errors = errors or []
        self.quality = quality

    def __bool__(self) -> bool:
        """Return True if validation passed."""
        return self.is_valid
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "is_valid": self.is_valid,
            "errors": self.errors,
        }
        if self.data:
            result["data"] = self.data.model_dump() if hasattr(self.data, "model_dump") else dict(self.data)
        if self.quality:
            result["quality"] = self.quality.to_dict()
        return result


def validate(
    model: Type[BaseModel],
    data: Dict[str, Any],
    strict: bool = False,
) -> ValidationResult:
    """
    Low-level function to validate data against a Pydantic model.
    
    This is a low-level utility function. For contract-based validation,
    use the Validator class instead:
    
        >>> from pycharter.runtime_validator import Validator
        >>> validator = Validator(contract_dir="data/contracts/user")
        >>> result = validator.validate(data)
    
    Use this function directly only when you already have a Pydantic model
    and don't need contract loading/management.

    Args:
        model: Pydantic model class (generated from JSON Schema)
        data: Data dictionary to validate
        strict: If True, raise exceptions on validation errors

    Returns:
        ValidationResult object

    Raises:
        ValidationError: If strict=True and validation fails

    Example:
        >>> from pycharter.pydantic_generator import from_dict
        >>> schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        >>> Person = from_dict(schema, "Person")
        >>> result = validate(Person, {"name": "Alice"})
        >>> result.is_valid
        True
        >>> result.data.name
        'Alice'
    """
    try:
        instance = model(**data)
        return ValidationResult(is_valid=True, data=instance)
    except ValidationError as e:
        # Format Pydantic errors for better readability
        errors = [f"{err.get('loc', 'unknown')}: {err.get('msg', 'validation error')}" 
                  for err in e.errors()]
        if strict:
            raise
        return ValidationResult(is_valid=False, errors=errors)
    except Exception as e:
        error_msg = f"Unexpected validation error: {type(e).__name__}: {str(e)}"
        if strict:
            raise
        return ValidationResult(is_valid=False, errors=[error_msg])


def validate_batch(
    model: Type[BaseModel],
    data_list: List[Dict[str, Any]],
    strict: bool = False,
) -> List[ValidationResult]:
    """
    Low-level function to validate a batch of data items against a Pydantic model.
    
    This is a low-level utility function. For contract-based validation,
    use the Validator class instead:
    
        >>> from pycharter.runtime_validator import Validator
        >>> validator = Validator(contract_dir="data/contracts/user")
        >>> results = validator.validate_batch(data_list)
    
    Use this function directly only when you already have a Pydantic model
    and don't need contract loading/management.

    Args:
        model: Pydantic model class
        data_list: List of data dictionaries to validate
        strict: If True, stop on first validation error

    Returns:
        List of ValidationResult objects

    Example:
        >>> results = validate_batch(Person, [{"name": "Alice"}, {"name": "Bob"}])
        >>> all(r.is_valid for r in results)
        True
    """
    results = []
    for data in data_list:
        result = validate(model, data, strict=strict)
        results.append(result)
        if strict and not result.is_valid:
            break
    return results
