"""
JSON Schemas for ETL Pipeline Configuration.

Provides validation schemas for extract, transform, load, and pipeline configs.
"""

import json
from pathlib import Path
from typing import Dict, Any

SCHEMA_DIR = Path(__file__).parent


def load_schema(name: str) -> Dict[str, Any]:
    """Load a JSON schema by name."""
    schema_path = SCHEMA_DIR / f"{name}.json"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    with open(schema_path) as f:
        return json.load(f)


def get_extract_schema() -> Dict[str, Any]:
    """Get the extract config schema."""
    return load_schema("extract")


def get_transform_schema() -> Dict[str, Any]:
    """Get the transform config schema."""
    return load_schema("transform")


def get_load_schema() -> Dict[str, Any]:
    """Get the load config schema."""
    return load_schema("load")


def get_pipeline_schema() -> Dict[str, Any]:
    """Get the combined pipeline config schema."""
    return load_schema("pipeline")


__all__ = [
    "load_schema",
    "get_extract_schema",
    "get_transform_schema",
    "get_load_schema",
    "get_pipeline_schema",
]
