"""
Request/Response models for metadata entity endpoints (owners, domains, systems, etc.).
"""

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Owner Models
class OwnerCreateRequest(BaseModel):
    """Request model for creating an owner."""
    
    id: str = Field(..., description="Owner identifier")
    name: Optional[str] = Field(None, description="Display name")
    email: Optional[str] = Field(None, description="Email address")
    team: Optional[str] = Field(None, description="Team name")
    additional_info: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class OwnerUpdateRequest(BaseModel):
    """Request model for updating an owner."""
    
    name: Optional[str] = Field(None, description="Display name")
    email: Optional[str] = Field(None, description="Email address")
    team: Optional[str] = Field(None, description="Team name")
    additional_info: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


# Domain Models
class DomainCreateRequest(BaseModel):
    """Request model for creating a domain."""
    
    name: str = Field(..., description="Domain name")
    description: Optional[str] = Field(None, description="Domain description")


class DomainUpdateRequest(BaseModel):
    """Request model for updating a domain."""
    
    name: Optional[str] = Field(None, description="Domain name")
    description: Optional[str] = Field(None, description="Domain description")


# System Models
class SystemCreateRequest(BaseModel):
    """Request model for creating a system."""
    
    name: str = Field(..., description="System name")
    app_id: Optional[str] = Field(None, description="Application ID")
    description: Optional[str] = Field(None, description="System description")


class SystemUpdateRequest(BaseModel):
    """Request model for updating a system."""
    
    name: Optional[str] = Field(None, description="System name")
    app_id: Optional[str] = Field(None, description="Application ID")
    description: Optional[str] = Field(None, description="System description")


# Environment Models
class EnvironmentCreateRequest(BaseModel):
    """Request model for creating an environment."""
    
    name: str = Field(..., description="Environment name")
    description: Optional[str] = Field(None, description="Environment description")
    environment_type: Optional[str] = Field(None, description="Environment type")
    is_production: bool = Field(False, description="Is production environment")
    additional_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class EnvironmentUpdateRequest(BaseModel):
    """Request model for updating an environment."""
    
    name: Optional[str] = Field(None, description="Environment name")
    description: Optional[str] = Field(None, description="Environment description")
    environment_type: Optional[str] = Field(None, description="Environment type")
    is_production: Optional[bool] = Field(None, description="Is production environment")
    additional_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


# Storage Location Models
class StorageLocationCreateRequest(BaseModel):
    """Request model for creating a storage location."""
    
    name: str = Field(..., description="Storage location name")
    location_type: Optional[str] = Field(None, description="Location type")
    cluster: Optional[str] = Field(None, description="Cluster name")
    database: Optional[str] = Field(None, description="Database name")
    collection: Optional[str] = Field(None, description="Collection name (for NoSQL)")
    schema_name: Optional[str] = Field(None, description="Schema name (for SQL)")
    table_name: Optional[str] = Field(None, description="Table name")
    connection_string: Optional[str] = Field(None, description="Connection string")
    system_id: Optional[UUID] = Field(None, description="Related system ID")
    environment_id: Optional[UUID] = Field(None, description="Related environment ID")
    additional_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class StorageLocationUpdateRequest(BaseModel):
    """Request model for updating a storage location."""
    
    name: Optional[str] = Field(None, description="Storage location name")
    location_type: Optional[str] = Field(None, description="Location type")
    cluster: Optional[str] = Field(None, description="Cluster name")
    database: Optional[str] = Field(None, description="Database name")
    collection: Optional[str] = Field(None, description="Collection name (for NoSQL)")
    schema_name: Optional[str] = Field(None, description="Schema name (for SQL)")
    table_name: Optional[str] = Field(None, description="Table name")
    connection_string: Optional[str] = Field(None, description="Connection string")
    system_id: Optional[UUID] = Field(None, description="Related system ID")
    environment_id: Optional[UUID] = Field(None, description="Related environment ID")
    additional_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


# Tag Models
class TagCreateRequest(BaseModel):
    """Request model for creating a tag."""
    
    name: str = Field(..., description="Tag name")
    description: Optional[str] = Field(None, description="Tag description")
    category: Optional[str] = Field(None, description="Tag category")
    color: Optional[str] = Field(None, description="Hex color code")
    additional_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class TagUpdateRequest(BaseModel):
    """Request model for updating a tag."""
    
    name: Optional[str] = Field(None, description="Tag name")
    description: Optional[str] = Field(None, description="Tag description")
    category: Optional[str] = Field(None, description="Tag category")
    color: Optional[str] = Field(None, description="Hex color code")
    additional_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
