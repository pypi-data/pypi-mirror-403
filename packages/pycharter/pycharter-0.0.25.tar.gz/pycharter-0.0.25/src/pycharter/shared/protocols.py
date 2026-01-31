"""
Protocol definitions for pycharter interfaces.

These protocols define the expected interfaces for extensible components,
enabling type checking and clear contracts for custom implementations.
"""

from typing import Any, Callable, Dict, List, Optional, Protocol, Type, runtime_checkable

from pydantic import BaseModel, ValidationInfo


# =============================================================================
# Metadata Store Protocols
# =============================================================================

@runtime_checkable
class MetadataStore(Protocol):
    """
    Protocol for metadata store implementations.
    
    All metadata stores (SQLite, Postgres, MongoDB, Redis, InMemory) must
    implement this interface for storing and retrieving data contracts.
    
    Example implementation:
        >>> class MyCustomStore:
        ...     def get_schema(self, schema_id: str, version: str = None) -> dict | None:
        ...         # Custom implementation
        ...         return {"type": "object", "properties": {...}}
    """
    
    def get_schema(
        self, schema_id: str, version: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get a schema by ID and optional version."""
        ...
    
    def get_complete_schema(
        self, schema_id: str, version: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get a complete schema with coercion and validation rules merged."""
        ...
    
    def store_schema(
        self,
        schema_id: str,
        schema: Dict[str, Any],
        version: Optional[str] = None,
    ) -> str:
        """Store a schema and return its ID."""
        ...
    
    def list_schemas(self) -> List[Dict[str, Any]]:
        """List all available schemas."""
        ...


# =============================================================================
# Coercion Protocols
# =============================================================================

# Type alias for coercion functions
CoercionFunc = Callable[[Any], Any]


@runtime_checkable
class CoercionRegistry(Protocol):
    """
    Protocol for coercion function registries.
    
    Coercions are pre-validation transformations applied to data
    before Pydantic validation (mode='before').
    """
    
    def get(self, name: str) -> CoercionFunc:
        """Get a coercion function by name."""
        ...
    
    def register(self, name: str, func: CoercionFunc) -> None:
        """Register a custom coercion function."""
        ...
    
    def list_available(self) -> List[str]:
        """List all available coercion names."""
        ...


# =============================================================================
# Validation Protocols
# =============================================================================

# Type alias for validation functions (factory pattern)
# A validation factory returns a validator function that takes (value, info) -> value
ValidatorFunc = Callable[[Any, ValidationInfo], Any]
ValidationFactory = Callable[..., ValidatorFunc]


@runtime_checkable
class ValidationRegistry(Protocol):
    """
    Protocol for validation function registries.
    
    Validations are post-validation checks applied to data
    after Pydantic validation (mode='after').
    """
    
    def get(self, name: str) -> ValidationFactory:
        """Get a validation factory by name."""
        ...
    
    def register(self, name: str, factory: ValidationFactory) -> None:
        """Register a custom validation factory."""
        ...
    
    def list_available(self) -> List[str]:
        """List all available validation names."""
        ...


# =============================================================================
# Contract Parser Protocols
# =============================================================================

@runtime_checkable
class ContractParser(Protocol):
    """
    Protocol for contract parsers.
    
    Contract parsers decompose data contract files/dicts into
    their constituent components (schema, coercion_rules, validation_rules, metadata).
    """
    
    def parse(self, contract_data: Dict[str, Any]) -> "ContractMetadataProtocol":
        """Parse contract data into metadata components."""
        ...
    
    def parse_file(self, file_path: str) -> "ContractMetadataProtocol":
        """Parse contract from file."""
        ...


@runtime_checkable
class ContractMetadataProtocol(Protocol):
    """Protocol for contract metadata containers."""
    
    @property
    def schema(self) -> Dict[str, Any]:
        """Get the JSON Schema definition."""
        ...
    
    @property
    def coercion_rules(self) -> Dict[str, Any]:
        """Get coercion rules."""
        ...
    
    @property
    def validation_rules(self) -> Dict[str, Any]:
        """Get validation rules."""
        ...
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Get additional metadata."""
        ...
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        ...


# =============================================================================
# Model Generator Protocols
# =============================================================================

@runtime_checkable
class ModelGenerator(Protocol):
    """
    Protocol for Pydantic model generators.
    
    Model generators take JSON Schemas and produce Pydantic model classes.
    """
    
    def generate(
        self, schema: Dict[str, Any], model_name: str = "DynamicModel"
    ) -> Type[BaseModel]:
        """Generate a Pydantic model from JSON Schema."""
        ...


# =============================================================================
# Validator Protocols
# =============================================================================

@runtime_checkable
class DataValidator(Protocol):
    """
    Protocol for data validators.
    
    Validators validate data against contracts/schemas and return results.
    """
    
    def validate(self, data: Dict[str, Any]) -> "ValidationResultProtocol":
        """Validate a single data record."""
        ...
    
    def validate_batch(
        self, data_list: List[Dict[str, Any]]
    ) -> List["ValidationResultProtocol"]:
        """Validate a batch of data records."""
        ...
    
    def get_model(self) -> Type[BaseModel]:
        """Get the underlying Pydantic model."""
        ...


@runtime_checkable
class ValidationResultProtocol(Protocol):
    """Protocol for validation results."""
    
    @property
    def is_valid(self) -> bool:
        """Whether validation passed."""
        ...
    
    @property
    def data(self) -> Optional[Any]:
        """Validated/coerced data (if valid)."""
        ...
    
    @property
    def errors(self) -> List[Dict[str, Any]]:
        """Validation errors (if any)."""
        ...
