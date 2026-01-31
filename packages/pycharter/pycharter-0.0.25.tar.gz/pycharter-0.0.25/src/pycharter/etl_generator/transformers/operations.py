"""
Built-in transformer operations.
"""

from typing import Any, Callable, Dict, List, Optional, Union

from pycharter.etl_generator.transformers.base import BaseTransformer
from pycharter.etl_generator.expression import evaluate_expression, is_expression


class Rename(BaseTransformer):
    """Rename fields in records."""
    
    def __init__(self, mapping: Dict[str, str]):
        self.mapping = mapping
    
    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [
            {self.mapping.get(k, k): v for k, v in record.items()}
            for record in data
        ]


class AddField(BaseTransformer):
    """
    Add a new field to records.
    
    Supports:
    - Static values: AddField("status", "active")
    - Callable: AddField("full_name", lambda r: f"{r['first']} {r['last']}")
    - Expressions: AddField("full_name", "${first_name} ${last_name}")
    - Functions: AddField("id", "uuid()")
    
    Expression syntax:
    - ${field_name} - Reference field value
    - ${field_name:-default} - Field with default
    - now() - Current timestamp
    - uuid() - Generate UUID
    - concat(${a}, " ", ${b}) - Concatenate values
    """
    
    def __init__(
        self,
        field: str,
        value: Union[Any, Callable[[Dict[str, Any]], Any]],
        evaluate_expressions: bool = True,
    ):
        """
        Initialize AddField transformer.
        
        Args:
            field: Name of the field to add
            value: Value, callable, or expression string
            evaluate_expressions: If True, evaluate string expressions.
                                 Set to False to use literal string values.
        """
        self.field = field
        self.value = value
        self.evaluate_expressions = evaluate_expressions
        
        # Pre-check if value is an expression to optimize
        self._is_expression = (
            evaluate_expressions 
            and isinstance(value, str) 
            and is_expression(value)
        )
    
    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        result = []
        for record in data:
            new_record = dict(record)
            
            if callable(self.value):
                # Callable - call with record
                new_record[self.field] = self.value(record)
            elif self._is_expression:
                # Expression - evaluate in record context
                new_record[self.field] = evaluate_expression(self.value, record)
            else:
                # Static value
                new_record[self.field] = self.value
            
            result.append(new_record)
        return result


class Drop(BaseTransformer):
    """Drop fields from records."""
    
    def __init__(self, fields: List[str]):
        self.fields = set(fields)
    
    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [
            {k: v for k, v in record.items() if k not in self.fields}
            for record in data
        ]


class Select(BaseTransformer):
    """Select only specific fields."""
    
    def __init__(self, fields: List[str]):
        self.fields = set(fields)
    
    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [
            {k: v for k, v in record.items() if k in self.fields}
            for record in data
        ]


class Filter(BaseTransformer):
    """Filter records based on a predicate."""
    
    def __init__(self, predicate: Callable[[Dict[str, Any]], bool]):
        self.predicate = predicate
    
    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [record for record in data if self.predicate(record)]


class Convert(BaseTransformer):
    """Convert field types."""
    
    def __init__(self, conversions: Dict[str, Callable[[Any], Any]], errors: str = "ignore"):
        self.conversions = conversions
        self.errors = errors
    
    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        result = []
        for record in data:
            new_record = dict(record)
            for field, converter in self.conversions.items():
                if field in new_record:
                    try:
                        new_record[field] = converter(new_record[field])
                    except (ValueError, TypeError):
                        if self.errors == "raise":
                            raise
                        elif self.errors == "null":
                            new_record[field] = None
            result.append(new_record)
        return result


class Default(BaseTransformer):
    """Set default values for missing or null fields."""
    
    def __init__(self, defaults: Dict[str, Any], replace_null: bool = True):
        self.defaults = defaults
        self.replace_null = replace_null
    
    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        result = []
        for record in data:
            new_record = dict(record)
            for field, default in self.defaults.items():
                if field not in new_record:
                    new_record[field] = default
                elif self.replace_null and new_record[field] is None:
                    new_record[field] = default
            result.append(new_record)
        return result


class Map(BaseTransformer):
    """Apply a function to each record."""
    
    def __init__(self, func: Callable[[Dict[str, Any]], Dict[str, Any]]):
        self.func = func
    
    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [self.func(record) for record in data]


class FlatMap(BaseTransformer):
    """Apply a function that returns multiple records per input."""
    
    def __init__(self, func: Callable[[Dict[str, Any]], List[Dict[str, Any]]]):
        self.func = func
    
    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        result = []
        for record in data:
            result.extend(self.func(record))
        return result


class CustomFunction(BaseTransformer):
    """Run a custom Python function on data."""
    
    def __init__(
        self,
        module: Optional[str] = None,
        function: Optional[str] = None,
        func: Optional[Callable[[List[Dict[str, Any]]], List[Dict[str, Any]]]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ):
        self.module = module
        self.function = function
        self._func = func
        self.kwargs = kwargs or {}
        
        if func is not None:
            self._resolved_func = func
        elif module and function:
            self._resolved_func = self._import_function(module, function)
        else:
            raise ValueError("Must provide either 'func' or both 'module' and 'function'")
    
    def _import_function(self, module: str, function: str) -> Callable:
        import importlib
        mod = importlib.import_module(module)
        return getattr(mod, function)
    
    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return self._resolved_func(data, **self.kwargs)
