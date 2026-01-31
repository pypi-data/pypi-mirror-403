"""
Custom Python function transformation.

Dynamically imports and invokes a module/function or callable path,
with optional class instantiation (optimize/run/__call__).
"""

import importlib
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def apply_custom_function(
    data: List[Dict[str, Any]], config: Dict[str, Any], **kwargs: Any
) -> List[Dict[str, Any]]:
    """
    Run a custom Python function for transformation.

    Args:
        data: Input data.
        config: 'callable' ("module.func") or 'module' + 'function'.
                Optional 'mode': "batch" (default) or "record".
                Optional 'kwargs': dict merged with **kwargs.
        **kwargs: Runtime kwargs merged with config['kwargs'].

    Returns:
        Transformed list of records.

    Example config:
        custom_function:
          module: "pyoptima"
          function: "optimize_from_etl_inputs"
          mode: "batch"
          kwargs:
            method: "min_volatility"
    """
    callable_path = config.get("callable")
    module_path = config.get("module")
    func_name = config.get("function")

    if callable_path:
        parts = callable_path.rsplit(".", 1)
        if len(parts) != 2:
            raise ValueError(
                f"Invalid callable path: {callable_path}. "
                "Use 'module.function' format."
            )
        module_path, func_name = parts

    if not module_path or not func_name:
        raise ValueError(
            "custom_function requires either 'callable' or 'module' + 'function'"
        )

    try:
        module = importlib.import_module(module_path)
        func = getattr(module, func_name)
    except ImportError as e:
        raise ValueError(f"Cannot import module '{module_path}': {e}") from e
    except AttributeError as e:
        raise ValueError(
            f"Function '{func_name}' not found in module '{module_path}'"
        ) from e

    if isinstance(func, type):
        instance = func()
        if hasattr(instance, "optimize"):
            func = instance.optimize
        elif hasattr(instance, "run"):
            func = instance.run
        elif hasattr(instance, "__call__"):
            func = instance
        else:
            raise ValueError(
                f"Class '{func_name}' has no 'optimize', 'run', or '__call__'"
            )

    mode = config.get("mode", "batch")
    func_kwargs = config.get("kwargs", {})
    merged_kwargs = {**func_kwargs, **kwargs}

    try:
        if mode == "batch":
            result = func(data, **merged_kwargs)
            if result is None:
                return []
            return result if isinstance(result, list) else [result]
        results = []
        for record in data:
            record_result = func(record, **merged_kwargs)
            if record_result is not None:
                if isinstance(record_result, list):
                    results.extend(record_result)
                else:
                    results.append(record_result)
        return results
    except Exception as e:
        logger.error("Custom function %r failed: %s", func_name, e)
        raise ValueError(f"Custom function error: {e}") from e
