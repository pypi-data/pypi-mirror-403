"""
Shared utilities used across all services.

Includes:
- Protocols (interface definitions for extensible components)
- Coercions (pre-validation transformations)
- Validations (post-validation checks)
- JSON Schema support utilities
- Schema resolution utilities
"""

from pycharter.shared.coercions import get_coercion, register_coercion
from pycharter.shared.json_schema_support import (
    apply_json_schema_constraints,
    create_const_validator,
    create_enum_validator,
    create_pattern_validator,
    create_unique_items_validator,
)
from pycharter.shared.json_schema_validator import (
    is_valid_json_schema,
    validate_json_schema,
)
from pycharter.shared.protocols import (
    MetadataStore,
    CoercionFunc,
    CoercionRegistry,
    ValidatorFunc,
    ValidationFactory,
    ValidationRegistry,
    ContractParser,
    ContractMetadataProtocol,
    ModelGenerator,
    DataValidator,
    ValidationResultProtocol,
)
from pycharter.shared.schema_parser import (
    get_schema_type,
    is_required,
    normalize_schema,
    validate_schema,
)
from pycharter.shared.schema_resolver import normalize_schema_structure, resolve_refs
from pycharter.shared.name_validator import (
    is_valid_name,
    normalize_name,
    validate_name,
)
from pycharter.shared.validations import get_validation, register_validation
from pycharter.shared.errors import (
    PyCharterError,
    ConfigError,
    ConfigValidationError,
    ConfigLoadError,
    ExpressionError,
    ErrorMode,
    ErrorContext,
    get_error_context,
    set_error_mode,
    handle_error,
    handle_warning,
    StrictMode,
    LenientMode,
)

__all__ = [
    # Protocols
    "MetadataStore",
    "CoercionFunc",
    "CoercionRegistry",
    "ValidatorFunc",
    "ValidationFactory",
    "ValidationRegistry",
    "ContractParser",
    "ContractMetadataProtocol",
    "ModelGenerator",
    "DataValidator",
    "ValidationResultProtocol",
    # Coercions
    "get_coercion",
    "register_coercion",
    # Validations
    "get_validation",
    "register_validation",
    # JSON Schema support
    "apply_json_schema_constraints",
    "create_const_validator",
    "create_enum_validator",
    "create_pattern_validator",
    "create_unique_items_validator",
    # Schema resolver
    "normalize_schema_structure",
    "resolve_refs",
    # Schema parser
    "get_schema_type",
    "is_required",
    "normalize_schema",
    "validate_schema",
    # JSON Schema validator
    "validate_json_schema",
    "is_valid_json_schema",
    # Name validator
    "validate_name",
    "is_valid_name",
    "normalize_name",
    # Exception hierarchy
    "PyCharterError",
    "ConfigError",
    "ConfigValidationError",
    "ConfigLoadError",
    "ExpressionError",
    # Error handling
    "ErrorMode",
    "ErrorContext",
    "get_error_context",
    "set_error_mode",
    "handle_error",
    "handle_warning",
    "StrictMode",
    "LenientMode",
]
