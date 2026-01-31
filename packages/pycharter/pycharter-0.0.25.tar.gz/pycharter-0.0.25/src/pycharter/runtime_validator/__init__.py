"""
Runtime Validator - Contract-based validation utilities.

PRIMARY INTERFACE: Validator Class
===================================

The Validator class is the recommended and primary way to perform validation
in pycharter. It can be instantiated with contract artifacts from various sources:

    >>> from pycharter.runtime_validator import Validator
    >>> 
    >>> # From contract directory
    >>> validator = Validator(contract_dir="data/contracts/user")
    >>> result = validator.validate({"name": "Alice", "age": 30})
    >>> 
    >>> # From metadata store
    >>> from pycharter.metadata_store import SQLiteMetadataStore
    >>> store = SQLiteMetadataStore("metadata.db")
    >>> validator = Validator(store=store, schema_id="user_schema")
    >>> result = validator.validate({"name": "Alice", "age": 30})
    >>> 
    >>> # Using builder pattern
    >>> from pycharter.runtime_validator import ValidatorBuilder
    >>> validator = (
    ...     ValidatorBuilder()
    ...     .from_directory("data/contracts/user")
    ...     .strict()
    ...     .with_quality_checks()
    ...     .build()
    ... )
    >>> result = validator.validate({"name": "Alice", "age": 30})
    >>> print(result.quality.completeness)

Core Components:
- Validator: Primary validation class
- ValidatorBuilder: Fluent API for constructing validators
- ValidationResult: Validation result with optional quality metrics
- QualityMetrics: Data quality metrics
"""

from pycharter.runtime_validator.builder import ValidatorBuilder
from pycharter.runtime_validator.decorators import (
    validate_input,
    validate_output,
    validate_with_contract as validate_with_contract_decorator,
)
from pycharter.runtime_validator.validator_core import (
    QualityMetrics,
    ValidationResult,
    validate,
    validate_batch,
)
from pycharter.runtime_validator.wrappers import (
    get_model_from_contract,
    get_model_from_store,
    validate_batch_with_contract,
    validate_batch_with_store,
    validate_with_contract,
    validate_with_store,
)
from pycharter.runtime_validator.validator import (
    Validator,
    create_validator,
)

__all__ = [
    # PRIMARY INTERFACE: Validator and Builder
    "Validator",
    "ValidatorBuilder",
    "create_validator",
    # Result classes
    "ValidationResult",
    "QualityMetrics",
    # Low-level validation functions (for direct model validation)
    "validate",
    "validate_batch",
    # Convenience functions (prefer Validator class for better performance)
    "validate_with_store",
    "validate_batch_with_store",
    "get_model_from_store",
    "validate_with_contract",
    "validate_batch_with_contract",
    "get_model_from_contract",
    # Decorators
    "validate_input",
    "validate_output",
    "validate_with_contract_decorator",
]
