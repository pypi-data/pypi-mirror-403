"""
Schema Evolution Compatibility - Check schema compatibility.

Provides compatibility checking between JSON Schema versions
for different compatibility modes (backward, forward, full).
"""

from typing import Any, Dict, List, Union

from pycharter.schema_evolution.diff import compute_diff
from pycharter.schema_evolution.models import (
    ChangeType,
    CompatibilityMode,
    CompatibilityResult,
    SchemaDiff,
)


def check_compatibility(
    old_schema: Dict[str, Any],
    new_schema: Dict[str, Any],
    mode: Union[str, CompatibilityMode] = CompatibilityMode.BACKWARD,
) -> CompatibilityResult:
    """
    Check if two schemas are compatible according to the specified mode.

    Compatibility Modes:
        - BACKWARD: New schema can read data produced by old schema
                   (consumers can be upgraded before producers)
        - FORWARD: Old schema can read data produced by new schema
                  (producers can be upgraded before consumers)
        - FULL: Both backward and forward compatible

    Args:
        old_schema: The existing/original schema
        new_schema: The new schema to check
        mode: Compatibility mode to check against

    Returns:
        CompatibilityResult with compatibility status and details

    Example:
        >>> old = {"type": "object", "properties": {"name": {"type": "string"}}}
        >>> new = {
        ...     "type": "object",
        ...     "properties": {
        ...         "name": {"type": "string"},
        ...         "age": {"type": "integer"}  # Added optional field
        ...     }
        ... }
        >>> result = check_compatibility(old, new, mode="backward")
        >>> result.compatible
        True
    """
    # Normalize mode
    if isinstance(mode, str):
        mode = CompatibilityMode(mode.lower())

    # Compute diff
    diff = compute_diff(old_schema, new_schema)

    # Check compatibility based on mode
    if mode == CompatibilityMode.BACKWARD:
        return _check_backward_compatibility(diff, mode)
    elif mode == CompatibilityMode.FORWARD:
        return _check_forward_compatibility(diff, mode)
    else:  # FULL
        return _check_full_compatibility(diff, mode)


def _check_backward_compatibility(
    diff: SchemaDiff, mode: CompatibilityMode
) -> CompatibilityResult:
    """
    Check backward compatibility.

    Backward compatible changes (new consumer, old producer):
    - Adding optional fields: OK
    - Removing fields: OK (consumer ignores unknown fields)
    - Widening types: OK (int -> number)
    - Removing enum values: BREAKING (old data may have removed values)
    - Adding required fields: BREAKING (old data won't have them)
    - Narrowing types: BREAKING (old data may not fit)
    - Adding constraints: BREAKING (old data may violate new constraints)
    """
    issues = []
    warnings = []

    breaking_types = {
        ChangeType.REQUIRED_ADDED,
        ChangeType.TYPE_NARROWED,
        ChangeType.ENUM_VALUE_REMOVED,
    }

    for change in diff.changes:
        if change.change_type in breaking_types:
            issues.append(change.message)
        elif change.breaking:
            # Other breaking changes (constraints, patterns, etc.)
            issues.append(change.message)
        elif change.change_type in {
            ChangeType.FIELD_REMOVED,
            ChangeType.REQUIRED_REMOVED,
        }:
            # Not breaking but may warrant attention
            warnings.append(change.message)

    compatible = len(issues) == 0

    return CompatibilityResult(
        compatible=compatible,
        mode=mode,
        diff=diff,
        issues=issues,
        warnings=warnings,
    )


def _check_forward_compatibility(
    diff: SchemaDiff, mode: CompatibilityMode
) -> CompatibilityResult:
    """
    Check forward compatibility.

    Forward compatible changes (old consumer, new producer):
    - Adding fields: OK (old consumer ignores unknown)
    - Removing optional fields: OK
    - Narrowing types: OK (new data fits old schema)
    - Removing required fields: BREAKING (old consumer expects them)
    - Adding enum values: BREAKING (old consumer doesn't recognize new values)
    - Widening types: BREAKING (new data may not fit old schema)
    """
    issues = []
    warnings = []

    breaking_types = {
        ChangeType.FIELD_REMOVED,  # If the old consumer needs it
        ChangeType.TYPE_WIDENED,
        ChangeType.ENUM_VALUE_ADDED,
    }

    for change in diff.changes:
        if change.change_type in breaking_types:
            # Forward compatibility has different breaking rules
            if change.change_type == ChangeType.FIELD_REMOVED:
                # Only breaking if it was required
                if _was_required_field(change):
                    issues.append(f"Required field removed: {change.path}")
                else:
                    warnings.append(change.message)
            else:
                issues.append(change.message)
        elif change.change_type == ChangeType.CONSTRAINT_REMOVED:
            # Removing constraints is forward-breaking (new data may violate old constraints)
            warnings.append(change.message)

    compatible = len(issues) == 0

    return CompatibilityResult(
        compatible=compatible,
        mode=mode,
        diff=diff,
        issues=issues,
        warnings=warnings,
    )


def _check_full_compatibility(
    diff: SchemaDiff, mode: CompatibilityMode
) -> CompatibilityResult:
    """
    Check full (bidirectional) compatibility.

    Full compatible changes:
    - Adding optional fields with defaults: OK
    - Metadata changes (description, title): OK

    Everything else is potentially breaking in one direction.
    """
    issues = []
    warnings = []

    # Only very limited changes are fully compatible
    safe_types = {
        ChangeType.DESCRIPTION_CHANGED,
        ChangeType.TITLE_CHANGED,
        ChangeType.DEFAULT_ADDED,
        ChangeType.DEFAULT_CHANGED,
    }

    for change in diff.changes:
        if change.change_type in safe_types:
            # Safe changes
            continue
        elif change.change_type == ChangeType.FIELD_ADDED:
            # Adding fields is only fully compatible if optional with default
            if change.new_value and change.new_value.get("default") is not None:
                warnings.append(f"Field added with default: {change.path}")
            else:
                issues.append(f"Field added without default: {change.path}")
        else:
            # Most other changes break at least one direction
            issues.append(change.message)

    compatible = len(issues) == 0

    return CompatibilityResult(
        compatible=compatible,
        mode=mode,
        diff=diff,
        issues=issues,
        warnings=warnings,
    )


def _was_required_field(change) -> bool:
    """Check if a removed field was required."""
    # This is a heuristic - in a full implementation, we'd track required status
    return "required" in str(change.path).lower()


def is_backward_compatible(
    old_schema: Dict[str, Any], new_schema: Dict[str, Any]
) -> bool:
    """
    Quick check if new schema is backward compatible with old.

    Args:
        old_schema: Original schema
        new_schema: New schema

    Returns:
        True if backward compatible
    """
    result = check_compatibility(old_schema, new_schema, CompatibilityMode.BACKWARD)
    return result.compatible


def is_forward_compatible(
    old_schema: Dict[str, Any], new_schema: Dict[str, Any]
) -> bool:
    """
    Quick check if new schema is forward compatible with old.

    Args:
        old_schema: Original schema
        new_schema: New schema

    Returns:
        True if forward compatible
    """
    result = check_compatibility(old_schema, new_schema, CompatibilityMode.FORWARD)
    return result.compatible


def is_fully_compatible(
    old_schema: Dict[str, Any], new_schema: Dict[str, Any]
) -> bool:
    """
    Quick check if schemas are fully compatible (both directions).

    Args:
        old_schema: Original schema
        new_schema: New schema

    Returns:
        True if fully compatible
    """
    result = check_compatibility(old_schema, new_schema, CompatibilityMode.FULL)
    return result.compatible
