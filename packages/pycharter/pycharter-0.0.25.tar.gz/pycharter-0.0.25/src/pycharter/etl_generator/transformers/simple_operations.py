"""
Simple declarative transformation operations.

Order: rename → convert → defaults → add → select → drop.
"""

import logging
from datetime import date, datetime
from typing import Any, Dict, List

from pycharter.etl_generator.expression import evaluate_expression, ExpressionEvaluator

logger = logging.getLogger(__name__)


def apply_simple_operations(
    data: List[Dict[str, Any]], config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Apply simple declarative operations to a list of records.

    Operations (in order): rename, convert, defaults, add, select, drop.
    """
    if not data:
        return data

    result = []
    available_fields = set(data[0].keys())
    rename_map = config.get("rename") or {}
    convert_map = config.get("convert") or {}
    defaults_map = config.get("defaults") or {}
    add_map = config.get("add") or {}
    select_fields = config.get("select")
    drop_fields = set(config.get("drop") or [])

    if rename_map:
        missing = [k for k in rename_map if k not in available_fields]
        if missing:
            logger.warning(
                "Rename operation: fields not in data: %s. Available: %s",
                missing,
                sorted(available_fields),
            )

    for record in data:
        row = dict(record)
        for old_name, new_name in rename_map.items():
            if old_name in row:
                row[new_name] = row.pop(old_name)
        for field_name, target_type in convert_map.items():
            if field_name in row:
                try:
                    row[field_name] = convert_type(row[field_name], target_type)
                except (ValueError, TypeError) as e:
                    logger.warning(
                        "Failed to convert field %r to %s: %s. Keeping original.",
                        field_name,
                        target_type,
                        e,
                    )
        for field_name, default_value in defaults_map.items():
            if field_name not in row or row[field_name] is None:
                row[field_name] = default_value
        for field_name, expression in add_map.items():
            try:
                row[field_name] = evaluate_expression(expression, row)
            except Exception as e:
                logger.warning(
                    "Failed to compute field %r: %s. Skipping.", field_name, e
                )
        if select_fields:
            row = {k: v for k, v in row.items() if k in select_fields}
        if drop_fields:
            row = {k: v for k, v in row.items() if k not in drop_fields}
        result.append(row)

    return result


def convert_type(value: Any, target_type: str) -> Any:
    """Convert a value to the given type (string, integer, float, boolean, datetime, date)."""
    if value is None:
        return None
    t = target_type.lower().strip()
    if t in ("str", "string"):
        return str(value)
    if t in ("int", "integer"):
        if isinstance(value, str):
            try:
                return int(float(value))
            except ValueError:
                return int(value)
        return int(value)
    if t in ("float", "number", "numeric"):
        return float(value) if isinstance(value, str) else float(value)
    if t in ("bool", "boolean"):
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "on")
        return bool(value)
    if t == "datetime":
        if isinstance(value, str):
            for fmt in (
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f",
            ):
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
            raise ValueError(f"Cannot parse datetime: {value}")
        return value
    if t == "date":
        if isinstance(value, str):
            for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y"]:
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
            raise ValueError(f"Cannot parse date: {value}")
        if isinstance(value, datetime):
            return value.date()
        return value
    raise ValueError(f"Unsupported target type: {target_type}")


# evaluate_expression is now imported from pycharter.etl_generator.expression
# Keeping this comment for backwards compatibility - the function is available via import
