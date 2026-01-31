"""
Schema Evolution Models - Data models for schema evolution.

Defines the core data structures for schema changes,
compatibility results, and diff analysis.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ChangeType(str, Enum):
    """Types of schema changes."""

    # Field changes
    FIELD_ADDED = "field_added"
    FIELD_REMOVED = "field_removed"
    FIELD_RENAMED = "field_renamed"

    # Type changes
    TYPE_CHANGED = "type_changed"
    TYPE_WIDENED = "type_widened"  # e.g., int -> number
    TYPE_NARROWED = "type_narrowed"  # e.g., number -> int

    # Constraint changes
    CONSTRAINT_ADDED = "constraint_added"
    CONSTRAINT_REMOVED = "constraint_removed"
    CONSTRAINT_MODIFIED = "constraint_modified"

    # Required/optional changes
    REQUIRED_ADDED = "required_added"
    REQUIRED_REMOVED = "required_removed"

    # Enum changes
    ENUM_VALUE_ADDED = "enum_value_added"
    ENUM_VALUE_REMOVED = "enum_value_removed"

    # Default value changes
    DEFAULT_ADDED = "default_added"
    DEFAULT_REMOVED = "default_removed"
    DEFAULT_CHANGED = "default_changed"

    # Description/metadata changes
    DESCRIPTION_CHANGED = "description_changed"
    TITLE_CHANGED = "title_changed"

    # Other
    FORMAT_CHANGED = "format_changed"
    PATTERN_CHANGED = "pattern_changed"


class CompatibilityMode(str, Enum):
    """Compatibility checking modes."""

    BACKWARD = "backward"  # New schema can read old data
    FORWARD = "forward"  # Old schema can read new data
    FULL = "full"  # Both backward and forward compatible


@dataclass
class SchemaChange:
    """
    Represents a single change between schema versions.

    Attributes:
        path: JSON path to the changed element (e.g., "properties.name.type")
        change_type: Type of change
        old_value: Value in the old schema
        new_value: Value in the new schema
        breaking: Whether this is a breaking change
        message: Human-readable description of the change
    """

    path: str
    change_type: ChangeType
    old_value: Any = None
    new_value: Any = None
    breaking: bool = False
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "path": self.path,
            "change_type": self.change_type.value,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "breaking": self.breaking,
            "message": self.message,
        }


@dataclass
class SchemaDiff:
    """
    Detailed diff between two schema versions.

    Attributes:
        changes: All changes detected
        breaking_changes: Only breaking changes
        additions: Fields/properties added
        removals: Fields/properties removed
        modifications: Fields/properties modified
        has_breaking_changes: Whether any breaking changes exist
    """

    changes: List[SchemaChange] = field(default_factory=list)

    @property
    def breaking_changes(self) -> List[SchemaChange]:
        """Get only breaking changes."""
        return [c for c in self.changes if c.breaking]

    @property
    def additions(self) -> List[SchemaChange]:
        """Get only additions."""
        addition_types = {
            ChangeType.FIELD_ADDED,
            ChangeType.ENUM_VALUE_ADDED,
            ChangeType.DEFAULT_ADDED,
            ChangeType.CONSTRAINT_ADDED,
        }
        return [c for c in self.changes if c.change_type in addition_types]

    @property
    def removals(self) -> List[SchemaChange]:
        """Get only removals."""
        removal_types = {
            ChangeType.FIELD_REMOVED,
            ChangeType.ENUM_VALUE_REMOVED,
            ChangeType.DEFAULT_REMOVED,
            ChangeType.CONSTRAINT_REMOVED,
            ChangeType.REQUIRED_REMOVED,
        }
        return [c for c in self.changes if c.change_type in removal_types]

    @property
    def modifications(self) -> List[SchemaChange]:
        """Get only modifications."""
        mod_types = {
            ChangeType.TYPE_CHANGED,
            ChangeType.TYPE_WIDENED,
            ChangeType.TYPE_NARROWED,
            ChangeType.CONSTRAINT_MODIFIED,
            ChangeType.DEFAULT_CHANGED,
            ChangeType.DESCRIPTION_CHANGED,
            ChangeType.FORMAT_CHANGED,
            ChangeType.PATTERN_CHANGED,
        }
        return [c for c in self.changes if c.change_type in mod_types]

    @property
    def has_breaking_changes(self) -> bool:
        """Check if any breaking changes exist."""
        return any(c.breaking for c in self.changes)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "changes": [c.to_dict() for c in self.changes],
            "breaking_changes": [c.to_dict() for c in self.breaking_changes],
            "additions": [c.to_dict() for c in self.additions],
            "removals": [c.to_dict() for c in self.removals],
            "modifications": [c.to_dict() for c in self.modifications],
            "has_breaking_changes": self.has_breaking_changes,
            "total_changes": len(self.changes),
        }


@dataclass
class CompatibilityResult:
    """
    Result of a schema compatibility check.

    Attributes:
        compatible: Whether schemas are compatible
        mode: Compatibility mode used for checking
        diff: Detailed diff between schemas
        issues: Human-readable issue descriptions
        warnings: Non-breaking issues that may need attention
    """

    compatible: bool
    mode: CompatibilityMode
    diff: Optional[SchemaDiff] = None
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "compatible": self.compatible,
            "mode": self.mode.value,
            "diff": self.diff.to_dict() if self.diff else None,
            "issues": self.issues,
            "warnings": self.warnings,
            "breaking_change_count": (
                len(self.diff.breaking_changes) if self.diff else 0
            ),
        }
