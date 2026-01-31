"""
Transform pipeline: simple_ops → jsonata → custom_function.

Single entry point: apply_transforms(data, transform_config, **kwargs).
"""

from typing import Any, Dict, List

from pycharter.etl_generator.transformers.config import normalize_transform_config
from pycharter.etl_generator.transformers.custom_function import (
    apply_custom_function,
)
from pycharter.etl_generator.transformers.jsonata_transformer import (
    apply_jsonata,
)
from pycharter.etl_generator.transformers.simple_operations import (
    apply_simple_operations,
)


def apply_transforms(
    data: List[Dict[str, Any]],
    transform_config: Dict[str, Any],
    **kwargs: Any,
) -> List[Dict[str, Any]]:
    """
    Run the full transform pipeline on data.

    Order: simple_ops → jsonata → custom_function. Each step is skipped
    if not configured.

    Args:
        data: Input list of records.
        transform_config: Raw transform config (canonical or legacy).
        **kwargs: Passed to custom_function.

    Returns:
        Transformed list of records.
    """
    if not transform_config:
        return data

    normalized = normalize_transform_config(transform_config)

    if normalized.get("simple_ops"):
        data = apply_simple_operations(data, normalized["simple_ops"])
    if normalized.get("jsonata"):
        data = apply_jsonata(data, normalized["jsonata"])
    if normalized.get("custom_function"):
        data = apply_custom_function(
            data, normalized["custom_function"], **kwargs
        )

    return data
