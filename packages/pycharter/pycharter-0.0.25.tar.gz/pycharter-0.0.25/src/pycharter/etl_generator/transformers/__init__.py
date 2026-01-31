"""
Transform stage for ETL pipelines.

Two APIs:
1. Config-driven: apply_transforms(data, config) - uses YAML config
2. Programmatic: Rename(...) | AddField(...) | Filter(...) - chainable

Pipeline order for config: Simple operations → JSONata → Custom function.
"""

# Config-driven API
from pycharter.etl_generator.transformers.pipeline import apply_transforms

# Chainable transformers
from pycharter.etl_generator.transformers.base import (
    BaseTransformer,
    TransformerChain,
)
from pycharter.etl_generator.transformers.operations import (
    Rename,
    AddField,
    Drop,
    Select,
    Filter,
    Convert,
    Default,
    Map,
    FlatMap,
    CustomFunction,
)

__all__ = [
    # Config-driven
    "apply_transforms",
    # Base classes
    "BaseTransformer",
    "TransformerChain",
    # Operations
    "Rename",
    "AddField",
    "Drop",
    "Select",
    "Filter",
    "Convert",
    "Default",
    "Map",
    "FlatMap",
    "CustomFunction",
]
