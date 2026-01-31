"""
JSONata-based transformation.

Applies a JSONata expression to data in batch or record mode.
"""

import logging
from typing import Any, Dict, List

import jsonata

logger = logging.getLogger(__name__)


def apply_jsonata(
    data: List[Dict[str, Any]], config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Apply a JSONata expression to transform data.

    Args:
        data: Input data (list of records).
        config: Must have 'expression'. Optional 'mode': "batch" (default) or "record".

    Returns:
        Transformed list of records.

    Example config:
        jsonata:
          expression: |
            $.{"ticker": symbol, "avg_price": $average(prices)}
          mode: "batch"
    """
    expression_str = config.get("expression")
    if not expression_str:
        return data

    mode = config.get("mode", "batch")

    try:
        expr = jsonata.Jsonata(expression_str)

        if mode == "batch":
            result = expr.evaluate(data)
            if result is None:
                return []
            return result if isinstance(result, list) else [result]
        # record mode
        return [
            expr.evaluate(record)
            for record in data
            if expr.evaluate(record) is not None
        ]
    except Exception as e:
        logger.error("JSONata transformation failed: %s", e)
        raise ValueError(f"JSONata transformation error: {e}") from e
