"""
Expression evaluation for ETL transformations.

Provides a unified expression evaluator for field values, computed columns,
and dynamic expressions in ETL pipelines.

Supported expressions:
- ${field_name} - Reference a field value
- ${field_name:-default} - Field with default if missing/null
- now() - Current timestamp (ISO format)
- uuid() - Generate a UUID
- env(VAR_NAME) - Get environment variable
- lower(${field}) - Lowercase a field value
- upper(${field}) - Uppercase a field value
- concat(${field1}, " ", ${field2}) - Concatenate values
- coalesce(${field1}, ${field2}, "default") - First non-null value
- Literal values - Strings, numbers, booleans
"""

import logging
import os
import re
import uuid as uuid_module
from datetime import datetime, date
from typing import Any, Callable, Dict, List, Optional, Union

from pycharter.shared.errors import ExpressionError

logger = logging.getLogger(__name__)


# Pattern for field references: ${field} or ${field:-default}
FIELD_PATTERN = re.compile(r'\$\{([^}:]+)(?::-([^}]*))?\}')

# Pattern for function calls: func_name(args)
FUNCTION_PATTERN = re.compile(r'^(\w+)\((.*)\)$', re.DOTALL)


class ExpressionEvaluator:
    """
    Evaluates expressions in the context of a data record.
    
    Usage:
        evaluator = ExpressionEvaluator()
        
        # Evaluate field reference
        result = evaluator.evaluate("${first_name}", {"first_name": "Alice"})
        # -> "Alice"
        
        # Evaluate with default
        result = evaluator.evaluate("${middle_name:-N/A}", {"first_name": "Alice"})
        # -> "N/A"
        
        # Evaluate function
        result = evaluator.evaluate("now()", {})
        # -> "2024-01-15T10:30:00"
        
        # Evaluate string interpolation
        result = evaluator.evaluate("Hello, ${name}!", {"name": "World"})
        # -> "Hello, World!"
        
        # Evaluate computed expression
        result = evaluator.evaluate("concat(${first_name}, ' ', ${last_name})", 
                                   {"first_name": "Alice", "last_name": "Smith"})
        # -> "Alice Smith"
    """
    
    def __init__(
        self,
        strict: bool = False,
        default_on_missing: Optional[str] = None,
    ):
        """
        Initialize the expression evaluator.
        
        Args:
            strict: If True, raise errors on missing fields. 
                   If False, replace with empty string or default.
            default_on_missing: Default value for missing fields when not strict.
        """
        self.strict = strict
        self.default_on_missing = default_on_missing or ""
        
        # Register built-in functions
        self._functions: Dict[str, Callable] = {
            "now": self._fn_now,
            "uuid": self._fn_uuid,
            "env": self._fn_env,
            "lower": self._fn_lower,
            "upper": self._fn_upper,
            "concat": self._fn_concat,
            "coalesce": self._fn_coalesce,
            "len": self._fn_len,
            "trim": self._fn_trim,
            "default": self._fn_default,
            "date": self._fn_date,
            "datetime": self._fn_datetime,
            "int": self._fn_int,
            "float": self._fn_float,
            "str": self._fn_str,
            "bool": self._fn_bool,
        }
    
    def evaluate(
        self,
        expression: Any,
        record: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Evaluate an expression in the context of a record.
        
        Args:
            expression: The expression to evaluate (string or literal)
            record: The data record providing field values
            context: Additional context variables
            
        Returns:
            The evaluated value
            
        Raises:
            ExpressionError: If evaluation fails and strict=True
        """
        context = context or {}
        
        # Non-string values are returned as-is
        if not isinstance(expression, str):
            return expression
        
        expression = expression.strip()
        
        # Empty string
        if not expression:
            return expression
        
        # Check for function call (entire expression is a function)
        func_match = FUNCTION_PATTERN.match(expression)
        if func_match:
            func_name = func_match.group(1).lower()
            args_str = func_match.group(2).strip()
            
            if func_name in self._functions:
                return self._call_function(func_name, args_str, record, context)
        
        # Check for field references in the expression
        if "${" in expression:
            return self._interpolate_fields(expression, record, context)
        
        # Check for simple function calls without $ prefix (now(), uuid())
        if expression.endswith("()") and expression[:-2].isidentifier():
            func_name = expression[:-2].lower()
            if func_name in self._functions:
                return self._call_function(func_name, "", record, context)
        
        # Return as literal
        return expression
    
    def _interpolate_fields(
        self,
        expression: str,
        record: Dict[str, Any],
        context: Dict[str, Any],
    ) -> str:
        """Interpolate ${field} references in a string."""
        
        def replace_field(match):
            field_name = match.group(1)
            default_value = match.group(2)
            
            # Check record first, then context
            if field_name in record:
                value = record[field_name]
            elif field_name in context:
                value = context[field_name]
            else:
                if self.strict and default_value is None:
                    raise ExpressionError(
                        f"Field '{field_name}' not found in record. "
                        f"Available: {sorted(record.keys())}"
                    )
                value = default_value if default_value is not None else self.default_on_missing
            
            # Convert to string for interpolation
            if value is None:
                return default_value if default_value is not None else ""
            return str(value)
        
        return FIELD_PATTERN.sub(replace_field, expression)
    
    def _call_function(
        self,
        func_name: str,
        args_str: str,
        record: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Any:
        """Call a built-in function with parsed arguments."""
        func = self._functions.get(func_name)
        if func is None:
            if self.strict:
                raise ExpressionError(f"Unknown function: {func_name}")
            logger.warning(f"Unknown function: {func_name}")
            return f"{func_name}({args_str})"
        
        # Parse arguments
        args = self._parse_args(args_str, record, context) if args_str else []
        
        try:
            return func(args, record, context)
        except Exception as e:
            if self.strict:
                raise ExpressionError(f"Error in {func_name}(): {e}")
            logger.warning(f"Error in {func_name}(): {e}")
            return None
    
    def _parse_args(
        self,
        args_str: str,
        record: Dict[str, Any],
        context: Dict[str, Any],
    ) -> List[Any]:
        """Parse function arguments, handling nested expressions."""
        if not args_str:
            return []
        
        args = []
        current_arg = ""
        depth = 0
        in_string = False
        string_char = None
        
        for i, char in enumerate(args_str):
            if char in ('"', "'") and (i == 0 or args_str[i-1] != '\\'):
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    in_string = False
                    string_char = None
                current_arg += char
            elif in_string:
                current_arg += char
            elif char == '(':
                depth += 1
                current_arg += char
            elif char == ')':
                depth -= 1
                current_arg += char
            elif char == ',' and depth == 0:
                # Argument separator
                args.append(self._evaluate_arg(current_arg.strip(), record, context))
                current_arg = ""
            else:
                current_arg += char
        
        # Add last argument
        if current_arg.strip():
            args.append(self._evaluate_arg(current_arg.strip(), record, context))
        
        return args
    
    def _evaluate_arg(
        self,
        arg: str,
        record: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Any:
        """Evaluate a single argument."""
        # Remove surrounding quotes
        if (arg.startswith('"') and arg.endswith('"')) or \
           (arg.startswith("'") and arg.endswith("'")):
            return arg[1:-1]
        
        # Check for number
        try:
            if '.' in arg:
                return float(arg)
            return int(arg)
        except ValueError:
            pass
        
        # Check for boolean
        if arg.lower() == 'true':
            return True
        if arg.lower() == 'false':
            return False
        if arg.lower() == 'null' or arg.lower() == 'none':
            return None
        
        # Evaluate as expression
        return self.evaluate(arg, record, context)
    
    # Built-in functions
    
    def _fn_now(self, args: List[Any], record: Dict, context: Dict) -> str:
        """Return current timestamp in ISO format."""
        fmt = args[0] if args else None
        now = datetime.now()
        if fmt:
            return now.strftime(fmt)
        return now.isoformat()
    
    def _fn_uuid(self, args: List[Any], record: Dict, context: Dict) -> str:
        """Generate a UUID."""
        return str(uuid_module.uuid4())
    
    def _fn_env(self, args: List[Any], record: Dict, context: Dict) -> Optional[str]:
        """Get environment variable."""
        if not args:
            raise ExpressionError("env() requires a variable name")
        var_name = str(args[0])
        default = args[1] if len(args) > 1 else None
        return os.environ.get(var_name, default)
    
    def _fn_lower(self, args: List[Any], record: Dict, context: Dict) -> str:
        """Lowercase a value."""
        if not args:
            raise ExpressionError("lower() requires an argument")
        return str(args[0]).lower() if args[0] is not None else ""
    
    def _fn_upper(self, args: List[Any], record: Dict, context: Dict) -> str:
        """Uppercase a value."""
        if not args:
            raise ExpressionError("upper() requires an argument")
        return str(args[0]).upper() if args[0] is not None else ""
    
    def _fn_concat(self, args: List[Any], record: Dict, context: Dict) -> str:
        """Concatenate values."""
        return "".join(str(a) if a is not None else "" for a in args)
    
    def _fn_coalesce(self, args: List[Any], record: Dict, context: Dict) -> Any:
        """Return first non-null value."""
        for arg in args:
            if arg is not None:
                return arg
        return None
    
    def _fn_len(self, args: List[Any], record: Dict, context: Dict) -> int:
        """Return length of a value."""
        if not args:
            raise ExpressionError("len() requires an argument")
        val = args[0]
        if val is None:
            return 0
        if isinstance(val, (str, list, dict)):
            return len(val)
        return len(str(val))
    
    def _fn_trim(self, args: List[Any], record: Dict, context: Dict) -> str:
        """Trim whitespace from a value."""
        if not args:
            raise ExpressionError("trim() requires an argument")
        return str(args[0]).strip() if args[0] is not None else ""
    
    def _fn_default(self, args: List[Any], record: Dict, context: Dict) -> Any:
        """Return value or default if null."""
        if len(args) < 2:
            raise ExpressionError("default() requires two arguments")
        return args[0] if args[0] is not None else args[1]
    
    def _fn_date(self, args: List[Any], record: Dict, context: Dict) -> str:
        """Return current date or parse date string."""
        if not args:
            return date.today().isoformat()
        # Parse date from string
        val = args[0]
        if isinstance(val, date):
            return val.isoformat()
        if isinstance(val, datetime):
            return val.date().isoformat()
        # Try parsing
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(str(val), fmt).date().isoformat()
            except ValueError:
                continue
        return str(val)
    
    def _fn_datetime(self, args: List[Any], record: Dict, context: Dict) -> str:
        """Return current datetime or parse datetime string."""
        if not args:
            return datetime.now().isoformat()
        val = args[0]
        if isinstance(val, datetime):
            return val.isoformat()
        # Try parsing
        for fmt in (
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ):
            try:
                return datetime.strptime(str(val), fmt).isoformat()
            except ValueError:
                continue
        return str(val)
    
    def _fn_int(self, args: List[Any], record: Dict, context: Dict) -> Optional[int]:
        """Convert to integer."""
        if not args or args[0] is None:
            return None
        val = args[0]
        if isinstance(val, str):
            try:
                return int(float(val))
            except ValueError:
                return None
        return int(val)
    
    def _fn_float(self, args: List[Any], record: Dict, context: Dict) -> Optional[float]:
        """Convert to float."""
        if not args or args[0] is None:
            return None
        return float(args[0])
    
    def _fn_str(self, args: List[Any], record: Dict, context: Dict) -> str:
        """Convert to string."""
        if not args or args[0] is None:
            return ""
        return str(args[0])
    
    def _fn_bool(self, args: List[Any], record: Dict, context: Dict) -> bool:
        """Convert to boolean."""
        if not args or args[0] is None:
            return False
        val = args[0]
        if isinstance(val, str):
            return val.lower() in ("true", "1", "yes", "on")
        return bool(val)
    
    def register_function(
        self,
        name: str,
        func: Callable[[List[Any], Dict, Dict], Any],
    ) -> None:
        """
        Register a custom function.
        
        Args:
            name: Function name (will be lowercased)
            func: Function that takes (args, record, context) and returns a value
        """
        self._functions[name.lower()] = func


# Default evaluator instance
_default_evaluator = ExpressionEvaluator()


def evaluate_expression(
    expression: Any,
    record: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> Any:
    """
    Evaluate an expression in the context of a record.
    
    This is a convenience function using the default evaluator.
    
    Args:
        expression: The expression to evaluate
        record: The data record providing field values
        context: Additional context variables
        
    Returns:
        The evaluated value
    """
    return _default_evaluator.evaluate(expression, record, context)


def is_expression(value: Any) -> bool:
    """
    Check if a value contains expression syntax.
    
    Args:
        value: The value to check
        
    Returns:
        True if the value contains ${} or function calls
    """
    if not isinstance(value, str):
        return False
    
    value = value.strip()
    
    # Check for field reference
    if "${" in value:
        return True
    
    # Check for function call
    if FUNCTION_PATTERN.match(value):
        return True
    
    # Check for simple function (now(), uuid())
    if value.endswith("()") and value[:-2].isidentifier():
        return True
    
    return False
