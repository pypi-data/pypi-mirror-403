"""
ValidatorBuilder - Fluent API for constructing validators.

Provides a clean, chainable interface for creating Validator instances
with various configuration options.
"""

from pathlib import Path
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pycharter.contract_parser import ContractMetadata
    from pycharter.metadata_store import MetadataStoreClient
    from pycharter.quality.tracking import MetricsCollector


class ValidatorBuilder:
    """
    Fluent builder for constructing Validator instances.
    
    Provides a clean, chainable API for configuring validators:
    
    Example:
        >>> from pycharter.runtime_validator import ValidatorBuilder
        >>> 
        >>> # From explicit files (most flexible)
        >>> validator = (
        ...     ValidatorBuilder()
        ...     .from_files(schema="schema.yaml", coercion_rules="coercion.yaml")
        ...     .strict()
        ...     .build()
        ... )
        >>> 
        >>> # From directory (expects schema.yaml, coercion_rules.yaml, validation_rules.yaml)
        >>> validator = (
        ...     ValidatorBuilder()
        ...     .from_dir("contracts/user/")
        ...     .strict()
        ...     .build()
        ... )
        >>> 
        >>> # From single file
        >>> validator = (
        ...     ValidatorBuilder()
        ...     .from_file("contracts/user.yaml")
        ...     .with_quality_checks()
        ...     .build()
        ... )
    """
    
    def __init__(self):
        self._contract_dir: Optional[str] = None
        self._contract_file: Optional[str] = None
        self._contract_dict: Optional[Dict[str, Any]] = None
        self._contract_metadata: Optional["ContractMetadata"] = None
        self._store: Optional["MetadataStoreClient"] = None
        self._schema_id: Optional[str] = None
        self._schema_version: Optional[str] = None
        self._strict_mode: bool = False
        self._include_quality: bool = False
        self._quality_thresholds: Optional[Dict[str, float]] = None
        self._metrics_collector: Optional["MetricsCollector"] = None
    
    def from_dir(self, directory: str) -> "ValidatorBuilder":
        """
        Load contract from directory.
        
        Expects files with standard names:
        - schema.yaml (required)
        - coercion_rules.yaml (optional)
        - validation_rules.yaml (optional)
        
        Args:
            directory: Path to contract directory
            
        Returns:
            Self for chaining
        """
        self._contract_dir = directory
        return self
    
    def from_file(self, path: str) -> "ValidatorBuilder":
        """
        Load contract from a single file containing all sections.
        
        Args:
            path: Path to contract file (YAML/JSON)
            
        Returns:
            Self for chaining
        """
        self._contract_file = path
        return self
    
    def from_dict(self, contract_dict: Dict[str, Any]) -> "ValidatorBuilder":
        """
        Load contract from dictionary.
        
        Args:
            contract_dict: Contract dictionary with 'schema', 'coercion_rules', 
                          'validation_rules' keys
            
        Returns:
            Self for chaining
        """
        self._contract_dict = contract_dict
        return self
    
    def from_files(
        self,
        schema: str,
        coercion_rules: Optional[str] = None,
        validation_rules: Optional[str] = None,
    ) -> "ValidatorBuilder":
        """
        Load contract from explicit file paths.
        
        This method accepts any file paths without assuming directory structure
        or file naming conventions. Use any file names you want.
        
        Args:
            schema: Path to schema file (YAML or JSON)
            coercion_rules: Optional path to coercion rules file
            validation_rules: Optional path to validation rules file
            
        Returns:
            Self for chaining
        
        Example:
            validator = (
                ValidatorBuilder()
                .from_files(
                    schema="my_schema.yaml",
                    coercion_rules="my_coercions.yaml",
                    validation_rules="my_validations.yaml"
                )
                .strict()
                .build()
            )
        """
        import yaml
        
        schema_path = Path(schema)
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        # Load schema
        with open(schema_path) as f:
            schema_data = yaml.safe_load(f)
        
        # Load coercion rules if provided
        coercion_data = {}
        if coercion_rules:
            coercion_path = Path(coercion_rules)
            if coercion_path.exists():
                with open(coercion_path) as f:
                    coercion_data = yaml.safe_load(f) or {}
        
        # Load validation rules if provided
        validation_data = {}
        if validation_rules:
            validation_path = Path(validation_rules)
            if validation_path.exists():
                with open(validation_path) as f:
                    validation_data = yaml.safe_load(f) or {}
        
        self._contract_dict = {
            "schema": schema_data,
            "coercion_rules": coercion_data,
            "validation_rules": validation_data,
        }
        return self
    
    def from_metadata(self, contract_metadata: "ContractMetadata") -> "ValidatorBuilder":
        """
        Load contract from ContractMetadata object.
        
        Args:
            contract_metadata: ContractMetadata object from parse_contract
            
        Returns:
            Self for chaining
        """
        self._contract_metadata = contract_metadata
        return self
    
    def from_store(
        self,
        store: "MetadataStoreClient",
        schema_id: str,
        version: Optional[str] = None,
    ) -> "ValidatorBuilder":
        """
        Load contract from metadata store.
        
        Args:
            store: MetadataStoreClient instance
            schema_id: Schema identifier
            version: Optional schema version (defaults to latest)
            
        Returns:
            Self for chaining
        """
        self._store = store
        self._schema_id = schema_id
        self._schema_version = version
        return self
    
    def strict(self) -> "ValidatorBuilder":
        """
        Enable strict mode.
        
        In strict mode, validation errors will raise exceptions
        instead of returning ValidationResult with is_valid=False.
        
        Returns:
            Self for chaining
        """
        self._strict_mode = True
        return self
    
    def lenient(self) -> "ValidatorBuilder":
        """
        Enable lenient mode (default).
        
        In lenient mode, validation errors are captured in
        ValidationResult.errors without raising exceptions.
        
        Returns:
            Self for chaining
        """
        self._strict_mode = False
        return self
    
    def with_quality_checks(
        self,
        thresholds: Optional[Dict[str, float]] = None,
    ) -> "ValidatorBuilder":
        """
        Enable quality checks during validation.
        
        When enabled, validation results will include quality metrics
        like completeness, accuracy, and uniqueness scores.
        
        Args:
            thresholds: Optional quality thresholds for pass/fail
                       e.g., {"completeness": 0.95, "accuracy": 0.99}
            
        Returns:
            Self for chaining
        """
        self._include_quality = True
        self._quality_thresholds = thresholds
        return self
    
    def with_tracking(self, collector: "MetricsCollector") -> "ValidatorBuilder":
        """
        Enable metrics tracking for validation runs.
        
        When enabled, validation metrics are automatically recorded
        to the provided MetricsCollector for time-series analysis.
        
        Args:
            collector: MetricsCollector instance for recording metrics
            
        Returns:
            Self for chaining
            
        Example:
            >>> from pycharter.quality.tracking import MetricsCollector, InMemoryMetricsStore
            >>> 
            >>> store = InMemoryMetricsStore()
            >>> collector = MetricsCollector(store)
            >>> 
            >>> validator = (
            ...     ValidatorBuilder()
            ...     .from_directory("contracts/user")
            ...     .with_tracking(collector)
            ...     .build()
            ... )
            >>> 
            >>> # Validation metrics are automatically recorded
            >>> result = validator.validate(data)
            >>> 
            >>> # Query recorded metrics
            >>> metrics = collector.query(schema_name="user")
        """
        self._metrics_collector = collector
        return self
    
    def build(self) -> "Validator":
        """
        Build the Validator instance.
        
        Returns:
            Configured Validator instance
            
        Raises:
            ValueError: If no contract source is specified
        """
        from pycharter.runtime_validator.validator import Validator
        
        # Create base validator
        validator = Validator(
            contract_dir=self._contract_dir,
            contract_file=self._contract_file,
            contract_dict=self._contract_dict,
            contract_metadata=self._contract_metadata,
            store=self._store,
            schema_id=self._schema_id,
            schema_version=self._schema_version,
        )
        
        # Apply configuration
        validator._strict_mode = self._strict_mode
        validator._include_quality = self._include_quality
        validator._quality_thresholds = self._quality_thresholds
        validator._metrics_collector = self._metrics_collector
        
        return validator


class Validator:
    """Extended Validator with builder configuration support."""
    
    # This is a forward reference - actual implementation is in validator.py
    # The builder will use the real Validator class
    pass
