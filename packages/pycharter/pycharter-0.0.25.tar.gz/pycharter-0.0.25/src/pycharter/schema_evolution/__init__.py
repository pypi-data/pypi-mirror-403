"""
Schema Evolution - Schema compatibility checking and diff analysis.

This module provides tools for checking schema compatibility between versions
and computing detailed diffs for schema evolution management.

Primary Interface:
    - check_compatibility: Check if two schemas are compatible
    - compute_diff: Compute detailed diff between schemas
    - CompatibilityResult: Result of compatibility check
    - SchemaDiff: Detailed schema difference

Models:
    - ChangeType: Types of schema changes
    - SchemaChange: Single schema change
    - CompatibilityMode: Compatibility checking modes

Example:
    >>> from pycharter.schema_evolution import check_compatibility, compute_diff
    >>>
    >>> old_schema = {"type": "object", "properties": {"name": {"type": "string"}}}
    >>> new_schema = {
    ...     "type": "object",
    ...     "properties": {
    ...         "name": {"type": "string"},
    ...         "age": {"type": "integer"}
    ...     }
    ... }
    >>>
    >>> # Check compatibility
    >>> result = check_compatibility(old_schema, new_schema, mode="backward")
    >>> print(f"Compatible: {result.compatible}")
    >>>
    >>> # Get detailed diff
    >>> diff = compute_diff(old_schema, new_schema)
    >>> for change in diff.changes:
    ...     print(f"{change.change_type}: {change.path}")
"""

from pycharter.schema_evolution.models import (
    ChangeType,
    CompatibilityMode,
    CompatibilityResult,
    SchemaChange,
    SchemaDiff,
)
from pycharter.schema_evolution.compatibility import check_compatibility
from pycharter.schema_evolution.diff import compute_diff

__all__ = [
    # Primary interface
    "check_compatibility",
    "compute_diff",
    # Result types
    "CompatibilityResult",
    "SchemaDiff",
    "SchemaChange",
    # Enums
    "ChangeType",
    "CompatibilityMode",
]
