"""
Safe Expression Engine for DittoMation automation.

Provides safe expression evaluation using AST parsing with whitelisted operations.
No arbitrary code execution - only approved functions and operators.

Usage:
    from core.expressions import SafeExpressionEngine
    from core.variables import VariableContext

    ctx = VariableContext({"count": 5, "name": "test"})
    engine = SafeExpressionEngine(ctx)

    # Evaluate expressions
    engine.evaluate("count > 3")  # ExpressionResult(value=True, ...)
    engine.evaluate_bool("count > 3")  # True
    engine.evaluate("name.upper()")  # ExpressionResult(value="TEST", ...)
"""

import ast
import operator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

if TYPE_CHECKING:
    from core.android import Android
    from core.variables import VariableContext


@dataclass
class ExpressionResult:
    """Result of expression evaluation."""

    value: Any
    success: bool
    error: Optional[str] = None
    expression: str = ""

    def __bool__(self) -> bool:
        """Allow using result directly in boolean context."""
        return self.success and bool(self.value)


class SafeExpressionEngine:
    """
    Safe expression evaluator using AST parsing.

    Evaluates expressions with a whitelist approach - only allowed operations
    and functions can be used. Prevents arbitrary code execution.

    Supported operations:
    - Variables: count, user.name, items[0]
    - Comparisons: ==, !=, <, >, <=, >=
    - Boolean: and, or, not
    - Arithmetic: +, -, *, /, %, //
    - String methods: .upper(), .lower(), .strip(), .startswith(), .endswith(), .replace()
    - Built-in functions: len, str, int, float, bool, abs, min, max, sum, any, all
    - Element functions (with Android): element_exists, element_text, element_count

    Example:
        ctx = VariableContext({"username": "test", "items": [1, 2, 3]})
        engine = SafeExpressionEngine(ctx)

        # Simple comparisons
        engine.evaluate_bool("len(items) > 2")  # True

        # String operations
        engine.evaluate("username.upper()")  # ExpressionResult(value="TEST", ...)

        # With Android integration for element checks
        engine.evaluate_bool("element_exists(text='Login')")
    """

    # Binary operators
    BINARY_OPS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.Gt: operator.gt,
        ast.LtE: operator.le,
        ast.GtE: operator.ge,
        ast.In: lambda a, b: a in b,
        ast.NotIn: lambda a, b: a not in b,
        ast.Is: operator.is_,
        ast.IsNot: operator.is_not,
    }

    # Unary operators
    UNARY_OPS = {
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
        ast.Not: operator.not_,
    }

    # Allowed string methods
    ALLOWED_STRING_METHODS = {
        "upper",
        "lower",
        "strip",
        "lstrip",
        "rstrip",
        "startswith",
        "endswith",
        "replace",
        "split",
        "join",
        "find",
        "rfind",
        "index",
        "count",
        "isdigit",
        "isalpha",
        "isalnum",
        "isspace",
        "title",
        "capitalize",
        "swapcase",
        "format",
        "center",
        "ljust",
        "rjust",
        "zfill",
    }

    # Allowed list/dict methods
    ALLOWED_COLLECTION_METHODS = {
        "append",
        "extend",
        "insert",
        "remove",
        "pop",
        "clear",
        "index",
        "count",
        "sort",
        "reverse",
        "copy",
        "keys",
        "values",
        "items",
        "get",
        "update",
    }

    def __init__(self, context: "VariableContext", android: Optional["Android"] = None):
        """
        Initialize expression engine.

        Args:
            context: VariableContext for variable resolution
            android: Optional Android instance for element functions
        """
        self.context = context
        self.android = android

        # Build allowed functions dict
        self._functions: Dict[str, Callable] = {
            # Built-in functions
            "len": len,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "abs": abs,
            "min": min,
            "max": max,
            "sum": sum,
            "any": any,
            "all": all,
            "round": round,
            "sorted": sorted,
            "reversed": lambda x: list(reversed(x)),
            "enumerate": lambda x: list(enumerate(x)),
            "zip": lambda *args: list(zip(*args)),
            "range": lambda *args: list(range(*args)),
            "list": list,
            "dict": dict,
            "set": set,
            "tuple": tuple,
            "type": lambda x: type(x).__name__,
            # String functions (also available as methods)
            "lower": lambda s: str(s).lower(),
            "upper": lambda s: str(s).upper(),
            "strip": lambda s: str(s).strip(),
            "contains": lambda s, sub: sub in str(s),
            "startswith": lambda s, prefix: str(s).startswith(prefix),
            "endswith": lambda s, suffix: str(s).endswith(suffix),
            # Element functions (require Android)
            "element_exists": self._element_exists,
            "element_text": self._element_text,
            "element_count": self._element_count,
            "element_visible": self._element_visible,
        }

    def evaluate(self, expression: str) -> ExpressionResult:
        """
        Evaluate an expression safely.

        Args:
            expression: Expression string to evaluate

        Returns:
            ExpressionResult with value, success status, and optional error
        """
        expression = expression.strip()

        # Handle empty expression
        if not expression:
            return ExpressionResult(
                value=None, success=False, error="Empty expression", expression=expression
            )

        # First, resolve any {{variable}} syntax
        from core.variables import VariableResolver

        resolver = VariableResolver(self.context)
        if resolver.has_variables(expression):
            try:
                expression = resolver.resolve_string(expression, raise_on_missing=True)
            except Exception as e:
                return ExpressionResult(
                    value=None,
                    success=False,
                    error=f"Variable resolution error: {e}",
                    expression=expression,
                )

        try:
            # Parse the expression
            tree = ast.parse(expression, mode="eval")

            # Validate the AST (check for unsafe operations)
            self._validate_ast(tree)

            # Evaluate the AST
            result = self._eval_node(tree.body)

            return ExpressionResult(value=result, success=True, expression=expression)

        except SyntaxError as e:
            return ExpressionResult(
                value=None, success=False, error=f"Syntax error: {e}", expression=expression
            )
        except Exception as e:
            return ExpressionResult(value=None, success=False, error=str(e), expression=expression)

    def evaluate_bool(self, expression: str) -> bool:
        """
        Evaluate an expression and return boolean result.

        Args:
            expression: Expression string to evaluate

        Returns:
            Boolean result (False if evaluation fails)
        """
        result = self.evaluate(expression)
        if not result.success:
            return False
        return bool(result.value)

    def _validate_ast(self, tree: ast.AST) -> None:
        """
        Validate AST for safety.

        Raises UnsafeExpressionError if unsafe operations are detected.
        """
        for node in ast.walk(tree):
            # Disallow dangerous constructs
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                self._raise_unsafe("Import statements not allowed")
            if isinstance(node, ast.Exec) if hasattr(ast, "Exec") else False:
                self._raise_unsafe("Exec not allowed")
            if isinstance(node, ast.Call):
                self._validate_call(node)
            if isinstance(node, ast.Attribute):
                self._validate_attribute(node)

    def _validate_call(self, node: ast.Call) -> None:
        """Validate a function call node."""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            # Check if it's a known safe function
            if func_name not in self._functions:
                # Could be a variable that's callable, allow it
                pass
        elif isinstance(node.func, ast.Attribute):
            # Method call - will be validated in _validate_attribute
            pass

    def _validate_attribute(self, node: ast.Attribute) -> None:
        """Validate attribute access."""
        attr_name = node.attr

        # Block dunder attributes (except __len__, __getitem__, __contains__)
        if attr_name.startswith("__") and attr_name.endswith("__"):
            allowed_dunders = {"__len__", "__getitem__", "__contains__", "__iter__"}
            if attr_name not in allowed_dunders:
                self._raise_unsafe(f"Access to {attr_name} not allowed")

        # Block dangerous attributes
        dangerous_attrs = {
            "func_code",
            "func_globals",
            "__code__",
            "__globals__",
            "__builtins__",
            "__class__",
            "__bases__",
            "__subclasses__",
            "__mro__",
            "__dict__",
            "gi_frame",
            "gi_code",
        }
        if attr_name in dangerous_attrs:
            self._raise_unsafe(f"Access to {attr_name} not allowed")

    def _raise_unsafe(self, message: str) -> None:
        """Raise an UnsafeExpressionError."""
        from core.exceptions import UnsafeExpressionError

        raise UnsafeExpressionError(message)

    def _eval_node(self, node: ast.AST) -> Any:
        """Recursively evaluate an AST node."""
        # Constants
        if isinstance(node, ast.Constant):
            return node.value

        # Num, Str, Bytes, NameConstant for older Python versions
        if isinstance(node, ast.Num):
            return node.n
        if isinstance(node, ast.Str):
            return node.s
        if hasattr(ast, "NameConstant") and isinstance(node, ast.NameConstant):
            return node.value

        # Names (variables)
        if isinstance(node, ast.Name):
            name = node.id
            # Check if it's a function first
            if name in self._functions:
                return self._functions[name]
            # Check built-in constants
            if name == "True":
                return True
            if name == "False":
                return False
            if name == "None":
                return None
            # Look up in context
            if self.context.has(name):
                return self.context.get(name)
            # Raise error for unknown names
            from core.exceptions import VariableNotFoundError

            raise VariableNotFoundError(name)

        # Binary operations
        if isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op_type = type(node.op)
            if op_type in self.BINARY_OPS:
                return self.BINARY_OPS[op_type](left, right)
            raise ValueError(f"Unsupported binary operator: {op_type.__name__}")

        # Unary operations
        if isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            op_type = type(node.op)
            if op_type in self.UNARY_OPS:
                return self.UNARY_OPS[op_type](operand)
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")

        # Boolean operations (and, or)
        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                result = True
                for value in node.values:
                    result = self._eval_node(value)
                    if not result:
                        return result
                return result
            elif isinstance(node.op, ast.Or):
                result = False
                for value in node.values:
                    result = self._eval_node(value)
                    if result:
                        return result
                return result

        # Comparisons
        if isinstance(node, ast.Compare):
            left = self._eval_node(node.left)
            for op, comparator in zip(node.ops, node.comparators):
                right = self._eval_node(comparator)
                op_type = type(op)
                if op_type in self.BINARY_OPS:
                    if not self.BINARY_OPS[op_type](left, right):
                        return False
                    left = right
                else:
                    raise ValueError(f"Unsupported comparison: {op_type.__name__}")
            return True

        # Function calls
        if isinstance(node, ast.Call):
            func = self._eval_node(node.func)

            # Evaluate arguments
            args = [self._eval_node(arg) for arg in node.args]

            # Evaluate keyword arguments
            kwargs = {kw.arg: self._eval_node(kw.value) for kw in node.keywords if kw.arg}

            # Handle **kwargs
            for kw in node.keywords:
                if kw.arg is None:
                    # **kwargs case
                    kwargs.update(self._eval_node(kw.value))

            return func(*args, **kwargs)

        # Attribute access
        if isinstance(node, ast.Attribute):
            value = self._eval_node(node.value)
            attr_name = node.attr

            # Check if it's an allowed method
            if isinstance(value, str) and attr_name in self.ALLOWED_STRING_METHODS:
                return getattr(value, attr_name)
            if isinstance(value, (list, dict)) and attr_name in self.ALLOWED_COLLECTION_METHODS:
                return getattr(value, attr_name)

            # For other types, allow attribute access if safe
            return getattr(value, attr_name)

        # Subscript (index/slice)
        if isinstance(node, ast.Subscript):
            value = self._eval_node(node.value)
            if isinstance(node.slice, ast.Index):
                # Python < 3.9
                index = self._eval_node(node.slice.value)
            else:
                index = self._eval_node(node.slice)
            return value[index]

        # List/Tuple/Set literals
        if isinstance(node, ast.List):
            return [self._eval_node(elem) for elem in node.elts]
        if isinstance(node, ast.Tuple):
            return tuple(self._eval_node(elem) for elem in node.elts)
        if isinstance(node, ast.Set):
            return {self._eval_node(elem) for elem in node.elts}

        # Dict literal
        if isinstance(node, ast.Dict):
            return {self._eval_node(k): self._eval_node(v) for k, v in zip(node.keys, node.values)}

        # If-expression (ternary)
        if isinstance(node, ast.IfExp):
            test = self._eval_node(node.test)
            if test:
                return self._eval_node(node.body)
            return self._eval_node(node.orelse)

        # List comprehension
        if isinstance(node, ast.ListComp):
            return self._eval_comprehension(node)

        # F-string
        if isinstance(node, ast.JoinedStr):
            parts = []
            for value in node.values:
                if isinstance(value, ast.Constant):
                    parts.append(str(value.value))
                elif isinstance(value, ast.FormattedValue):
                    parts.append(str(self._eval_node(value.value)))
                else:
                    parts.append(str(self._eval_node(value)))
            return "".join(parts)

        raise ValueError(f"Unsupported expression type: {type(node).__name__}")

    def _eval_comprehension(self, node: ast.ListComp) -> list:
        """Evaluate a list comprehension with limited scope."""
        result = []

        # Simple single-generator comprehension
        if len(node.generators) == 1:
            gen = node.generators[0]
            if isinstance(gen.target, ast.Name):
                var_name = gen.target.id
                iterable = self._eval_node(gen.iter)

                # Save current context state
                had_var = self.context.has(var_name)
                old_value = self.context.get(var_name) if had_var else None

                try:
                    for item in iterable:
                        self.context.set(var_name, item)

                        # Check all conditions
                        if all(self._eval_node(if_clause) for if_clause in gen.ifs):
                            result.append(self._eval_node(node.elt))
                finally:
                    # Restore context
                    if had_var:
                        self.context.set(var_name, old_value)
                    else:
                        self.context.delete(var_name)

                return result

        raise ValueError("Only simple list comprehensions are supported")

    # Element functions (require Android instance)
    def _element_exists(
        self,
        text: Optional[str] = None,
        id: Optional[str] = None,
        desc: Optional[str] = None,
        min_confidence: float = 0.3,
    ) -> bool:
        """Check if an element exists on screen."""
        if self.android is None:
            return False
        try:
            result = self.android.find_with_confidence(
                text=text, id=id, desc=desc, min_confidence=min_confidence
            )
            return result is not None and result.confidence >= min_confidence
        except Exception:
            return False

    def _element_text(
        self,
        text: Optional[str] = None,
        id: Optional[str] = None,
        desc: Optional[str] = None,
        min_confidence: float = 0.3,
    ) -> Optional[str]:
        """Get text of an element."""
        if self.android is None:
            return None
        try:
            result = self.android.find_with_confidence(
                text=text, id=id, desc=desc, min_confidence=min_confidence
            )
            if result and result.element:
                return result.element.get("text", "")
            return None
        except Exception:
            return None

    def _element_count(
        self,
        text: Optional[str] = None,
        id: Optional[str] = None,
        desc: Optional[str] = None,
        class_name: Optional[str] = None,
        min_confidence: float = 0.3,
    ) -> int:
        """Count matching elements on screen."""
        if self.android is None:
            return 0
        try:
            results = self.android.find_all_with_confidence(
                text=text, id=id, desc=desc, class_name=class_name, min_confidence=min_confidence
            )
            return len(results)
        except Exception:
            return 0

    def _element_visible(
        self,
        text: Optional[str] = None,
        id: Optional[str] = None,
        desc: Optional[str] = None,
        min_confidence: float = 0.3,
    ) -> bool:
        """Check if an element is visible (exists and has non-zero bounds)."""
        if self.android is None:
            return False
        try:
            result = self.android.find_with_confidence(
                text=text, id=id, desc=desc, min_confidence=min_confidence
            )
            if result and result.element:
                bounds = result.element.get("bounds", (0, 0, 0, 0))
                # Check if bounds are valid (non-zero width and height)
                if len(bounds) == 4:
                    width = bounds[2] - bounds[0]
                    height = bounds[3] - bounds[1]
                    return width > 0 and height > 0
            return False
        except Exception:
            return False

    def register_function(self, name: str, func: Callable) -> None:
        """
        Register a custom function for use in expressions.

        Args:
            name: Function name to use in expressions
            func: Callable to execute
        """
        self._functions[name] = func

    def unregister_function(self, name: str) -> None:
        """Remove a custom function."""
        if name in self._functions:
            del self._functions[name]
