"""
Schema Evolution Diff - Compute differences between schemas.

Provides detailed diff analysis between JSON Schema versions.
"""

from typing import Any, Dict, List, Optional, Set

from pycharter.schema_evolution.models import ChangeType, SchemaChange, SchemaDiff


def compute_diff(
    old_schema: Dict[str, Any],
    new_schema: Dict[str, Any],
    path: str = "",
) -> SchemaDiff:
    """
    Compute detailed diff between two JSON Schema versions.

    Args:
        old_schema: Original schema
        new_schema: New schema
        path: Current path (for nested comparison)

    Returns:
        SchemaDiff with all detected changes
    """
    changes: List[SchemaChange] = []

    # Compare top-level attributes
    changes.extend(_compare_attributes(old_schema, new_schema, path))

    # Compare properties
    if "properties" in old_schema or "properties" in new_schema:
        changes.extend(
            _compare_properties(
                old_schema.get("properties", {}),
                new_schema.get("properties", {}),
                f"{path}.properties" if path else "properties",
            )
        )

    # Compare required fields
    changes.extend(
        _compare_required(
            old_schema.get("required", []),
            new_schema.get("required", []),
            f"{path}.required" if path else "required",
        )
    )

    # Compare items (for arrays)
    if "items" in old_schema or "items" in new_schema:
        changes.extend(
            _compare_items(
                old_schema.get("items"),
                new_schema.get("items"),
                f"{path}.items" if path else "items",
            )
        )

    return SchemaDiff(changes=changes)


def _compare_attributes(
    old_schema: Dict[str, Any],
    new_schema: Dict[str, Any],
    path: str,
) -> List[SchemaChange]:
    """Compare top-level schema attributes."""
    changes = []

    # Type changes
    old_type = old_schema.get("type")
    new_type = new_schema.get("type")
    if old_type != new_type:
        change_type, breaking = _analyze_type_change(old_type, new_type)
        changes.append(
            SchemaChange(
                path=f"{path}.type" if path else "type",
                change_type=change_type,
                old_value=old_type,
                new_value=new_type,
                breaking=breaking,
                message=f"Type changed from '{old_type}' to '{new_type}'",
            )
        )

    # Format changes
    if old_schema.get("format") != new_schema.get("format"):
        changes.append(
            SchemaChange(
                path=f"{path}.format" if path else "format",
                change_type=ChangeType.FORMAT_CHANGED,
                old_value=old_schema.get("format"),
                new_value=new_schema.get("format"),
                breaking=True,  # Format changes are typically breaking
                message=f"Format changed from '{old_schema.get('format')}' to '{new_schema.get('format')}'",
            )
        )

    # Pattern changes
    if old_schema.get("pattern") != new_schema.get("pattern"):
        changes.append(
            SchemaChange(
                path=f"{path}.pattern" if path else "pattern",
                change_type=ChangeType.PATTERN_CHANGED,
                old_value=old_schema.get("pattern"),
                new_value=new_schema.get("pattern"),
                breaking=True,  # Pattern changes are typically breaking
                message="Pattern constraint changed",
            )
        )

    # Enum changes
    changes.extend(_compare_enum(old_schema, new_schema, path))

    # Constraint changes
    changes.extend(_compare_constraints(old_schema, new_schema, path))

    # Default value changes
    changes.extend(_compare_default(old_schema, new_schema, path))

    # Description changes (non-breaking)
    if old_schema.get("description") != new_schema.get("description"):
        changes.append(
            SchemaChange(
                path=f"{path}.description" if path else "description",
                change_type=ChangeType.DESCRIPTION_CHANGED,
                old_value=old_schema.get("description"),
                new_value=new_schema.get("description"),
                breaking=False,
                message="Description changed",
            )
        )

    # Title changes (non-breaking)
    if old_schema.get("title") != new_schema.get("title"):
        changes.append(
            SchemaChange(
                path=f"{path}.title" if path else "title",
                change_type=ChangeType.TITLE_CHANGED,
                old_value=old_schema.get("title"),
                new_value=new_schema.get("title"),
                breaking=False,
                message="Title changed",
            )
        )

    return changes


def _compare_properties(
    old_props: Dict[str, Any],
    new_props: Dict[str, Any],
    path: str,
) -> List[SchemaChange]:
    """Compare properties between schemas."""
    changes = []

    old_keys = set(old_props.keys())
    new_keys = set(new_props.keys())

    # Added properties
    for key in new_keys - old_keys:
        changes.append(
            SchemaChange(
                path=f"{path}.{key}",
                change_type=ChangeType.FIELD_ADDED,
                old_value=None,
                new_value=new_props[key],
                breaking=False,  # Adding optional fields is not breaking
                message=f"Field '{key}' added",
            )
        )

    # Removed properties
    for key in old_keys - new_keys:
        changes.append(
            SchemaChange(
                path=f"{path}.{key}",
                change_type=ChangeType.FIELD_REMOVED,
                old_value=old_props[key],
                new_value=None,
                breaking=False,  # Removing fields is backward compatible
                message=f"Field '{key}' removed",
            )
        )

    # Modified properties (recursively)
    for key in old_keys & new_keys:
        nested_diff = compute_diff(old_props[key], new_props[key], f"{path}.{key}")
        changes.extend(nested_diff.changes)

    return changes


def _compare_required(
    old_required: List[str],
    new_required: List[str],
    path: str,
) -> List[SchemaChange]:
    """Compare required fields."""
    changes = []

    old_set = set(old_required)
    new_set = set(new_required)

    # Newly required fields (breaking for backward compatibility)
    for field in new_set - old_set:
        changes.append(
            SchemaChange(
                path=f"{path}.{field}",
                change_type=ChangeType.REQUIRED_ADDED,
                old_value=None,
                new_value=field,
                breaking=True,  # Adding required is breaking
                message=f"Field '{field}' is now required",
            )
        )

    # No longer required fields (not breaking)
    for field in old_set - new_set:
        changes.append(
            SchemaChange(
                path=f"{path}.{field}",
                change_type=ChangeType.REQUIRED_REMOVED,
                old_value=field,
                new_value=None,
                breaking=False,  # Removing required is not breaking
                message=f"Field '{field}' is no longer required",
            )
        )

    return changes


def _compare_items(
    old_items: Optional[Dict[str, Any]],
    new_items: Optional[Dict[str, Any]],
    path: str,
) -> List[SchemaChange]:
    """Compare array items schema."""
    changes = []

    if old_items is None and new_items is not None:
        changes.append(
            SchemaChange(
                path=path,
                change_type=ChangeType.CONSTRAINT_ADDED,
                old_value=None,
                new_value=new_items,
                breaking=True,
                message="Array items schema added",
            )
        )
    elif old_items is not None and new_items is None:
        changes.append(
            SchemaChange(
                path=path,
                change_type=ChangeType.CONSTRAINT_REMOVED,
                old_value=old_items,
                new_value=None,
                breaking=False,
                message="Array items schema removed",
            )
        )
    elif old_items is not None and new_items is not None:
        nested_diff = compute_diff(old_items, new_items, path)
        changes.extend(nested_diff.changes)

    return changes


def _compare_enum(
    old_schema: Dict[str, Any],
    new_schema: Dict[str, Any],
    path: str,
) -> List[SchemaChange]:
    """Compare enum values."""
    changes = []

    old_enum = set(old_schema.get("enum", []) or [])
    new_enum = set(new_schema.get("enum", []) or [])

    if not old_enum and not new_enum:
        return changes

    # Added enum values (not breaking)
    for value in new_enum - old_enum:
        changes.append(
            SchemaChange(
                path=f"{path}.enum",
                change_type=ChangeType.ENUM_VALUE_ADDED,
                old_value=None,
                new_value=value,
                breaking=False,
                message=f"Enum value '{value}' added",
            )
        )

    # Removed enum values (breaking)
    for value in old_enum - new_enum:
        changes.append(
            SchemaChange(
                path=f"{path}.enum",
                change_type=ChangeType.ENUM_VALUE_REMOVED,
                old_value=value,
                new_value=None,
                breaking=True,
                message=f"Enum value '{value}' removed",
            )
        )

    return changes


def _compare_constraints(
    old_schema: Dict[str, Any],
    new_schema: Dict[str, Any],
    path: str,
) -> List[SchemaChange]:
    """Compare numeric and string constraints."""
    changes = []

    constraint_keys = [
        "minimum",
        "maximum",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "minLength",
        "maxLength",
        "minItems",
        "maxItems",
        "minProperties",
        "maxProperties",
        "multipleOf",
        "uniqueItems",
    ]

    for key in constraint_keys:
        old_val = old_schema.get(key)
        new_val = new_schema.get(key)

        if old_val != new_val:
            if old_val is None and new_val is not None:
                # Constraint added (may be breaking)
                breaking = _is_constraint_addition_breaking(key, new_val)
                changes.append(
                    SchemaChange(
                        path=f"{path}.{key}",
                        change_type=ChangeType.CONSTRAINT_ADDED,
                        old_value=None,
                        new_value=new_val,
                        breaking=breaking,
                        message=f"Constraint '{key}' added with value {new_val}",
                    )
                )
            elif old_val is not None and new_val is None:
                # Constraint removed (not breaking)
                changes.append(
                    SchemaChange(
                        path=f"{path}.{key}",
                        change_type=ChangeType.CONSTRAINT_REMOVED,
                        old_value=old_val,
                        new_value=None,
                        breaking=False,
                        message=f"Constraint '{key}' removed",
                    )
                )
            else:
                # Constraint modified
                breaking = _is_constraint_modification_breaking(key, old_val, new_val)
                changes.append(
                    SchemaChange(
                        path=f"{path}.{key}",
                        change_type=ChangeType.CONSTRAINT_MODIFIED,
                        old_value=old_val,
                        new_value=new_val,
                        breaking=breaking,
                        message=f"Constraint '{key}' changed from {old_val} to {new_val}",
                    )
                )

    return changes


def _compare_default(
    old_schema: Dict[str, Any],
    new_schema: Dict[str, Any],
    path: str,
) -> List[SchemaChange]:
    """Compare default values."""
    changes = []

    old_default = old_schema.get("default")
    new_default = new_schema.get("default")

    has_old = "default" in old_schema
    has_new = "default" in new_schema

    if has_old != has_new or old_default != new_default:
        if not has_old and has_new:
            changes.append(
                SchemaChange(
                    path=f"{path}.default",
                    change_type=ChangeType.DEFAULT_ADDED,
                    old_value=None,
                    new_value=new_default,
                    breaking=False,
                    message=f"Default value '{new_default}' added",
                )
            )
        elif has_old and not has_new:
            changes.append(
                SchemaChange(
                    path=f"{path}.default",
                    change_type=ChangeType.DEFAULT_REMOVED,
                    old_value=old_default,
                    new_value=None,
                    breaking=False,
                    message=f"Default value '{old_default}' removed",
                )
            )
        elif old_default != new_default:
            changes.append(
                SchemaChange(
                    path=f"{path}.default",
                    change_type=ChangeType.DEFAULT_CHANGED,
                    old_value=old_default,
                    new_value=new_default,
                    breaking=False,
                    message=f"Default value changed from '{old_default}' to '{new_default}'",
                )
            )

    return changes


def _analyze_type_change(
    old_type: Optional[str], new_type: Optional[str]
) -> tuple:
    """
    Analyze a type change and determine if it's breaking.

    Returns:
        Tuple of (ChangeType, is_breaking)
    """
    # Type widening (not breaking for backward compatibility)
    widening = {
        ("integer", "number"),
        ("int", "number"),
        ("null", "string"),
        ("null", "integer"),
        ("null", "number"),
    }

    # Type narrowing (breaking)
    narrowing = {
        ("number", "integer"),
        ("number", "int"),
        ("string", "null"),
        ("integer", "null"),
        ("number", "null"),
    }

    pair = (old_type, new_type)

    if pair in widening:
        return ChangeType.TYPE_WIDENED, False
    elif pair in narrowing:
        return ChangeType.TYPE_NARROWED, True
    else:
        return ChangeType.TYPE_CHANGED, True


def _is_constraint_addition_breaking(key: str, value: Any) -> bool:
    """Determine if adding a constraint is breaking."""
    # Adding minimum/maximum constraints is breaking
    # Adding length constraints is breaking
    return True


def _is_constraint_modification_breaking(key: str, old_val: Any, new_val: Any) -> bool:
    """Determine if modifying a constraint is breaking."""
    # For min* constraints: increasing is breaking
    # For max* constraints: decreasing is breaking

    if key.startswith("min"):
        return new_val > old_val
    elif key.startswith("max"):
        return new_val < old_val
    elif key == "uniqueItems":
        return new_val and not old_val  # Adding uniqueItems is breaking

    return True
