"""
Normalize transform configuration for use by transformer modules.

Supports both the canonical shape (transform: { rename, convert, ... }) and
legacy top-level keys; outputs a single normalized dict for each step.
"""

from typing import Any, Dict


def normalize_transform_config(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize transform config so transformers see a single shape.

    Canonical: transform: { rename, convert, defaults, add, select, drop }
    Legacy: rename, convert, ... at top level (when 'transform' not in config)

    Returns a dict with keys: simple_ops, jsonata, custom_function.
    Each is a dict or None if not configured.
    """
    out: Dict[str, Any] = {
        "simple_ops": None,
        "jsonata": None,
        "custom_function": None,
    }

    # Simple operations: merge from transform.X or top-level X
    simple_ops: Dict[str, Any] = {}
    if "transform" in raw:
        simple_ops = dict(raw.get("transform") or {})
    for key in ("rename", "convert", "defaults", "add", "select", "drop"):
        if key in raw and "transform" not in raw:
            val = raw.get(key)
            if val is not None:
                simple_ops[key] = val
    if simple_ops:
        out["simple_ops"] = simple_ops

    if raw.get("jsonata"):
        out["jsonata"] = dict(raw["jsonata"])

    if raw.get("custom_function"):
        out["custom_function"] = dict(raw["custom_function"])

    return out
