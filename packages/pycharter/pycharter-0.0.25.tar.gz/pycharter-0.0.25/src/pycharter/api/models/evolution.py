"""
API models for schema evolution endpoints.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CompatibilityModeEnum(str, Enum):
    """Compatibility checking modes."""

    BACKWARD = "backward"
    FORWARD = "forward"
    FULL = "full"


class ChangeTypeEnum(str, Enum):
    """Types of schema changes."""

    FIELD_ADDED = "field_added"
    FIELD_REMOVED = "field_removed"
    FIELD_RENAMED = "field_renamed"
    TYPE_CHANGED = "type_changed"
    TYPE_WIDENED = "type_widened"
    TYPE_NARROWED = "type_narrowed"
    CONSTRAINT_ADDED = "constraint_added"
    CONSTRAINT_REMOVED = "constraint_removed"
    CONSTRAINT_MODIFIED = "constraint_modified"
    REQUIRED_ADDED = "required_added"
    REQUIRED_REMOVED = "required_removed"
    ENUM_VALUE_ADDED = "enum_value_added"
    ENUM_VALUE_REMOVED = "enum_value_removed"
    DEFAULT_ADDED = "default_added"
    DEFAULT_REMOVED = "default_removed"
    DEFAULT_CHANGED = "default_changed"
    DESCRIPTION_CHANGED = "description_changed"
    TITLE_CHANGED = "title_changed"
    FORMAT_CHANGED = "format_changed"
    PATTERN_CHANGED = "pattern_changed"


class SchemaChangeResponse(BaseModel):
    """Response model for a single schema change."""

    path: str = Field(..., description="JSON path to the changed element")
    change_type: ChangeTypeEnum = Field(..., description="Type of change")
    old_value: Optional[Any] = Field(default=None, description="Value in old schema")
    new_value: Optional[Any] = Field(default=None, description="Value in new schema")
    breaking: bool = Field(..., description="Whether this is a breaking change")
    message: str = Field(..., description="Human-readable description")


class SchemaDiffResponse(BaseModel):
    """Response model for schema diff."""

    changes: List[SchemaChangeResponse] = Field(..., description="All detected changes")
    breaking_changes: List[SchemaChangeResponse] = Field(
        ..., description="Only breaking changes"
    )
    additions: List[SchemaChangeResponse] = Field(..., description="Added elements")
    removals: List[SchemaChangeResponse] = Field(..., description="Removed elements")
    modifications: List[SchemaChangeResponse] = Field(
        ..., description="Modified elements"
    )
    has_breaking_changes: bool = Field(
        ..., description="Whether any breaking changes exist"
    )
    total_changes: int = Field(..., description="Total number of changes")


class CompatibilityCheckRequest(BaseModel):
    """Request model for checking compatibility between two schemas."""

    old_schema: Dict[str, Any] = Field(..., description="Original/existing schema")
    new_schema: Dict[str, Any] = Field(..., description="New schema to check")
    mode: CompatibilityModeEnum = Field(
        default=CompatibilityModeEnum.BACKWARD,
        description="Compatibility mode to check against",
    )


class CompatibilityCheckResponse(BaseModel):
    """Response model for compatibility check."""

    compatible: bool = Field(
        ..., description="Whether schemas are compatible in the specified mode"
    )
    mode: CompatibilityModeEnum = Field(..., description="Compatibility mode used")
    diff: Optional[SchemaDiffResponse] = Field(
        default=None, description="Detailed schema diff"
    )
    issues: List[str] = Field(
        default_factory=list, description="Breaking change descriptions"
    )
    warnings: List[str] = Field(
        default_factory=list, description="Non-breaking issues that may need attention"
    )
    breaking_change_count: int = Field(
        ..., description="Number of breaking changes detected"
    )


class DiffRequest(BaseModel):
    """Request model for computing schema diff."""

    old_schema: Dict[str, Any] = Field(..., description="Original schema")
    new_schema: Dict[str, Any] = Field(..., description="New schema")


class StoredSchemaDiffRequest(BaseModel):
    """Request model for diffing stored schema versions."""

    schema_name: str = Field(..., description="Name of the schema")
    old_version: str = Field(..., description="Old version to compare")
    new_version: str = Field(..., description="New version to compare")
