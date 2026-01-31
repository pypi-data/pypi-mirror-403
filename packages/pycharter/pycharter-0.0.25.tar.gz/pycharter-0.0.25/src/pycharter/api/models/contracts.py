"""
Request/Response models for contract endpoints.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from pycharter.shared.name_validator import validate_name


class ContractParseRequest(BaseModel):
    """Request model for parsing a contract."""
    
    contract: Dict[str, Any] = Field(..., description="Contract data as dictionary")
    
    class Config:
        json_schema_extra = {
            "example": {
                "contract": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "age": {"type": "integer"}
                        }
                    },
                    "metadata": {
                        "title": "User Contract",
                        "version": "1.0.0"
                    }
                }
            }
        }


class ContractParseResponse(BaseModel):
    """Response model for parsed contract."""
    
    schema: Dict[str, Any] = Field(..., description="JSON Schema definition", alias="schema")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata information")
    ownership: Optional[Dict[str, Any]] = Field(None, description="Ownership information")
    governance_rules: Optional[Dict[str, Any]] = Field(None, description="Governance rules")
    coercion_rules: Optional[Dict[str, Any]] = Field(None, description="Coercion rules")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="Validation rules")
    versions: Optional[Dict[str, str]] = Field(None, description="Component versions")
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer"}
                    }
                },
                "metadata": {
                    "title": "User Contract",
                    "version": "1.0.0"
                },
                "versions": {
                    "schema": "1.0.0",
                    "metadata": "1.0.0"
                }
            }
        }
    )


class ContractBuildRequest(BaseModel):
    """Request model for building a contract from store."""
    
    schema_title: str = Field(..., description="Schema title/identifier")
    schema_version: Optional[str] = Field(None, description="Schema version (default: latest)")
    coercion_rules_title: Optional[str] = Field(None, description="Coercion rules title/identifier (default: schema_title)")
    coercion_rules_version: Optional[str] = Field(None, description="Coercion rules version (default: latest or schema_version)")
    validation_rules_title: Optional[str] = Field(None, description="Validation rules title/identifier (default: schema_title)")
    validation_rules_version: Optional[str] = Field(None, description="Validation rules version (default: latest or schema_version)")
    metadata_title: Optional[str] = Field(None, description="Metadata title/identifier (default: schema_title)")
    metadata_version: Optional[str] = Field(None, description="Metadata version (default: latest or schema_version)")
    include_metadata: bool = Field(True, description="Include metadata in contract")
    include_ownership: bool = Field(True, description="Include ownership in contract")
    include_governance: bool = Field(True, description="Include governance rules in contract")
    
    class Config:
        json_schema_extra = {
            "example": {
                "schema_title": "user_schema",
                "schema_version": "1.0.0",
                "coercion_rules_title": "user_schema",
                "coercion_rules_version": "1.0.0",
                "validation_rules_title": "user_schema",
                "validation_rules_version": "1.0.0",
                "metadata_title": "user_schema",
                "metadata_version": "1.0.0",
                "include_metadata": True,
                "include_ownership": True,
                "include_governance": True
            }
        }


class ContractBuildResponse(BaseModel):
    """Response model for built contract."""
    
    contract: Dict[str, Any] = Field(..., description="Complete contract dictionary")
    
    class Config:
        json_schema_extra = {
            "example": {
                "contract": {
                    "schema": {...},
                    "metadata": {...},
                    "ownership": {...},
                    "governance_rules": {...}
                }
            }
        }
    
    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema, handler):
        """Custom JSON schema generation to handle Dict[str, Any] with potential sets."""
        # Return a simple object schema for Dict[str, Any] to avoid set hashing issues
        return {
            "type": "object",
            "additionalProperties": True,
            "description": field_schema.get("description", "Complete contract dictionary"),
        }


class ContractListItem(BaseModel):
    """Model for a single contract in the list."""
    
    id: str = Field(..., description="Contract ID (UUID)")
    name: str = Field(..., description="Contract name")
    version: str = Field(..., description="Contract version")
    status: Optional[str] = Field(None, description="Contract status")
    description: Optional[str] = Field(None, description="Contract description")
    schema_id: Optional[str] = Field(None, description="Schema ID (UUID) associated with this contract")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "user_contract",
                "version": "1.0.0",
                "status": "active",
                "description": "User data contract",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }


class ContractListResponse(BaseModel):
    """Response model for contract list."""
    
    contracts: List[ContractListItem] = Field(..., description="List of contracts")
    total: int = Field(..., description="Total number of contracts")
    
    class Config:
        json_schema_extra = {
            "example": {
                "contracts": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "user_contract",
                        "version": "1.0.0",
                        "status": "active",
                        "description": "User data contract"
                    }
                ],
                "total": 1
            }
        }


class ContractCreateFromArtifactsRequest(BaseModel):
    """Request model for creating a contract from existing artifacts."""
    
    name: str = Field(..., description="Contract name")
    version: str = Field(..., description="Contract version")
    schema_title: str = Field(..., description="Schema artifact title")
    schema_version: str = Field(..., description="Schema artifact version")
    coercion_rules_title: Optional[str] = Field(None, description="Coercion rules artifact title (optional)")
    coercion_rules_version: Optional[str] = Field(None, description="Coercion rules artifact version (optional)")
    validation_rules_title: Optional[str] = Field(None, description="Validation rules artifact title (optional)")
    validation_rules_version: Optional[str] = Field(None, description="Validation rules artifact version (optional)")
    metadata_title: Optional[str] = Field(None, description="Metadata artifact title (optional)")
    metadata_version: Optional[str] = Field(None, description="Metadata artifact version (optional)")
    status: Optional[str] = Field("active", description="Contract status")
    description: Optional[str] = Field(None, description="Contract description")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate contract name follows naming convention."""
        return validate_name(v, field_name="name")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "user_contract",
                "version": "2.0.0",
                "schema_title": "user_schema",
                "schema_version": "1.0.0",
                "coercion_rules_title": "user_schema_coercion_rules",
                "coercion_rules_version": "1.0.0",
                "validation_rules_title": "user_schema_validation_rules",
                "validation_rules_version": "1.0.0",
                "metadata_title": "user_metadata",
                "metadata_version": "1.0.0",
                "status": "active",
                "description": "User data contract"
            }
        }


class ContractCreateMixedRequest(BaseModel):
    """Request model for creating a contract with mixed artifacts (some new, some existing)."""
    
    name: str = Field(..., description="Contract name")
    version: str = Field(..., description="Contract version")
    
    # Schema: either new data or existing title+version
    schema: Optional[Dict[str, Any]] = Field(None, description="New schema definition (if creating new schema)")
    schema_title: Optional[str] = Field(None, description="Existing schema title (if using existing schema)")
    schema_version: Optional[str] = Field(None, description="Existing schema version (if using existing schema)")
    
    # Coercion rules: either new data or existing title+version
    coercion_rules: Optional[Dict[str, Any]] = Field(None, description="New coercion rules (if creating new)")
    coercion_rules_title: Optional[str] = Field(None, description="Existing coercion rules title (if using existing)")
    coercion_rules_version: Optional[str] = Field(None, description="Existing coercion rules version (if using existing)")
    
    # Validation rules: either new data or existing title+version
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="New validation rules (if creating new)")
    validation_rules_title: Optional[str] = Field(None, description="Existing validation rules title (if using existing)")
    validation_rules_version: Optional[str] = Field(None, description="Existing validation rules version (if using existing)")
    
    # Metadata: either new data or existing title+version
    metadata: Optional[Dict[str, Any]] = Field(None, description="New metadata (if creating new)")
    metadata_title: Optional[str] = Field(None, description="Existing metadata title (if using existing)")
    metadata_version: Optional[str] = Field(None, description="Existing metadata version (if using existing)")
    
    status: Optional[str] = Field("active", description="Contract status")
    description: Optional[str] = Field(None, description="Contract description")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate contract name follows naming convention."""
        return validate_name(v, field_name="name")
    
    @model_validator(mode='after')
    def validate_artifacts(self):
        """Validate that each artifact is either new or existing, but not both or neither (for schema)."""
        # Schema must be provided (either new or existing)
        has_new_schema = self.schema is not None
        has_existing_schema = self.schema_title is not None and self.schema_version is not None
        
        if not has_new_schema and not has_existing_schema:
            raise ValueError("Schema must be provided either as new data (schema) or existing artifact (schema_title + schema_version)")
        if has_new_schema and has_existing_schema:
            raise ValueError("Cannot specify both new schema and existing schema. Choose one.")
        
        # Coercion rules: either new or existing, but not both
        has_new_coercion = self.coercion_rules is not None and len(self.coercion_rules) > 0
        has_existing_coercion = self.coercion_rules_title is not None and self.coercion_rules_version is not None
        
        if has_new_coercion and has_existing_coercion:
            raise ValueError("Cannot specify both new coercion rules and existing coercion rules. Choose one.")
        
        # Validation rules: either new or existing, but not both
        has_new_validation = self.validation_rules is not None and len(self.validation_rules) > 0
        has_existing_validation = self.validation_rules_title is not None and self.validation_rules_version is not None
        
        if has_new_validation and has_existing_validation:
            raise ValueError("Cannot specify both new validation rules and existing validation rules. Choose one.")
        
        # Metadata: either new or existing, but not both
        has_new_metadata = self.metadata is not None and len(self.metadata) > 0
        has_existing_metadata = self.metadata_title is not None and self.metadata_version is not None
        
        if has_new_metadata and has_existing_metadata:
            raise ValueError("Cannot specify both new metadata and existing metadata. Choose one.")
        
        return self
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "user_contract",
                "version": "1.0.0",
                "schema": {"type": "object", "properties": {}},
                "coercion_rules_title": "existing_coercion_rules",
                "coercion_rules_version": "1.0.0",
                "validation_rules": {"rules": {}},
                "metadata_title": "existing_metadata",
                "metadata_version": "1.0.0",
                "status": "active",
                "description": "User data contract"
            }
        }


class ContractUpdateRequest(BaseModel):
    """Request model for updating a contract."""
    
    name: Optional[str] = Field(None, description="Contract name")
    version: Optional[str] = Field(None, description="Contract version")
    status: Optional[str] = Field(None, description="Contract status (e.g., 'active', 'deprecated', 'draft')")
    description: Optional[str] = Field(None, description="Contract description")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate contract name follows naming convention."""
        if v is not None:
            return validate_name(v, field_name="name")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "updated_contract_name",
                "version": "1.1.0",
                "status": "active",
                "description": "Updated contract description"
            }
        }

