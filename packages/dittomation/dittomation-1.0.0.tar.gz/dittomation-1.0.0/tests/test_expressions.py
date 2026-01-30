"""
Unit tests for core.expressions module.

Tests SafeExpressionEngine for:
- Basic expression evaluation
- Comparison operators
- Boolean operators
- Arithmetic operations
- String methods
- Built-in functions
- Safety checks (blocking unsafe operations)
"""

import pytest

from core.expressions import ExpressionResult, SafeExpressionEngine
from core.variables import VariableContext


class TestBasicExpressions:
    """Tests for basic expression evaluation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ctx = VariableContext({"x": 10, "y": 5, "name": "test"})
        self.engine = SafeExpressionEngine(self.ctx)

    def test_constant_int(self):
        """Test integer constant."""
        result = self.engine.evaluate("42")
        assert result.success
        assert result.value == 42

    def test_constant_float(self):
        """Test float constant."""
        result = self.engine.evaluate("3.14")
        assert result.success
        assert result.value == 3.14

    def test_constant_string(self):
        """Test string constant."""
        result = self.engine.evaluate("'hello'")
        assert result.success
        assert result.value == "hello"

    def test_constant_boolean(self):
        """Test boolean constants."""
        assert self.engine.evaluate("True").value is True
        assert self.engine.evaluate("False").value is False

    def test_variable_access(self):
        """Test variable access."""
        result = self.engine.evaluate("x")
        assert result.success
        assert result.value == 10

    def test_variable_not_found(self):
        """Test accessing undefined variable."""
        result = self.engine.evaluate("undefined_var")
        assert not result.success

    def test_empty_expression(self):
        """Test empty expression."""
        result = self.engine.evaluate("")
        assert not result.success


class TestComparisonOperators:
    """Tests for comparison operators."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ctx = VariableContext({"x": 10, "y": 5})
        self.engine = SafeExpressionEngine(self.ctx)

    def test_equality(self):
        """Test equality operators."""
        assert self.engine.evaluate_bool("x == 10") is True
        assert self.engine.evaluate_bool("x == 5") is False
        assert self.engine.evaluate_bool("x != 5") is True
        assert self.engine.evaluate_bool("x != 10") is False

    def test_less_than(self):
        """Test less than operators."""
        assert self.engine.evaluate_bool("y < x") is True
        assert self.engine.evaluate_bool("x < y") is False
        assert self.engine.evaluate_bool("y <= 5") is True
        assert self.engine.evaluate_bool("y <= 4") is False

    def test_greater_than(self):
        """Test greater than operators."""
        assert self.engine.evaluate_bool("x > y") is True
        assert self.engine.evaluate_bool("y > x") is False
        assert self.engine.evaluate_bool("x >= 10") is True
        assert self.engine.evaluate_bool("x >= 11") is False

    def test_chained_comparison(self):
        """Test chained comparisons."""
        assert self.engine.evaluate_bool("1 < y < x") is True
        assert self.engine.evaluate_bool("0 < y < 4") is False

    def test_in_operator(self):
        """Test 'in' operator."""
        self.ctx.set("items", [1, 2, 3])
        assert self.engine.evaluate_bool("2 in items") is True
        assert self.engine.evaluate_bool("5 in items") is False

    def test_string_in(self):
        """Test 'in' with strings."""
        assert self.engine.evaluate_bool("'hello' in 'hello world'") is True
        assert self.engine.evaluate_bool("'xyz' in 'hello world'") is False


class TestBooleanOperators:
    """Tests for boolean operators."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ctx = VariableContext({"a": True, "b": False})
        self.engine = SafeExpressionEngine(self.ctx)

    def test_and(self):
        """Test 'and' operator."""
        assert self.engine.evaluate_bool("a and a") is True
        assert self.engine.evaluate_bool("a and b") is False
        assert self.engine.evaluate_bool("b and b") is False

    def test_or(self):
        """Test 'or' operator."""
        assert self.engine.evaluate_bool("a or b") is True
        assert self.engine.evaluate_bool("b or a") is True
        assert self.engine.evaluate_bool("b or b") is False

    def test_not(self):
        """Test 'not' operator."""
        assert self.engine.evaluate_bool("not b") is True
        assert self.engine.evaluate_bool("not a") is False

    def test_combined(self):
        """Test combined boolean operations."""
        assert self.engine.evaluate_bool("a and not b") is True
        assert self.engine.evaluate_bool("(a or b) and a") is True


class TestArithmeticOperators:
    """Tests for arithmetic operators."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ctx = VariableContext({"x": 10, "y": 3})
        self.engine = SafeExpressionEngine(self.ctx)

    def test_addition(self):
        """Test addition."""
        result = self.engine.evaluate("x + y")
        assert result.value == 13

    def test_subtraction(self):
        """Test subtraction."""
        result = self.engine.evaluate("x - y")
        assert result.value == 7

    def test_multiplication(self):
        """Test multiplication."""
        result = self.engine.evaluate("x * y")
        assert result.value == 30

    def test_division(self):
        """Test division."""
        result = self.engine.evaluate("x / y")
        assert abs(result.value - 3.333) < 0.01

    def test_floor_division(self):
        """Test floor division."""
        result = self.engine.evaluate("x // y")
        assert result.value == 3

    def test_modulo(self):
        """Test modulo."""
        result = self.engine.evaluate("x % y")
        assert result.value == 1

    def test_power(self):
        """Test power."""
        result = self.engine.evaluate("y ** 2")
        assert result.value == 9

    def test_unary_minus(self):
        """Test unary minus."""
        result = self.engine.evaluate("-x")
        assert result.value == -10

    def test_parentheses(self):
        """Test parentheses for precedence."""
        result = self.engine.evaluate("(x + y) * 2")
        assert result.value == 26


class TestStringOperations:
    """Tests for string operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ctx = VariableContext({"name": "  Hello World  "})
        self.engine = SafeExpressionEngine(self.ctx)

    def test_upper(self):
        """Test upper method."""
        result = self.engine.evaluate("name.upper()")
        assert result.value == "  HELLO WORLD  "

    def test_lower(self):
        """Test lower method."""
        result = self.engine.evaluate("name.lower()")
        assert result.value == "  hello world  "

    def test_strip(self):
        """Test strip method."""
        result = self.engine.evaluate("name.strip()")
        assert result.value == "Hello World"

    def test_startswith(self):
        """Test startswith method."""
        self.ctx.set("text", "Hello")
        assert self.engine.evaluate_bool("text.startswith('He')") is True
        assert self.engine.evaluate_bool("text.startswith('lo')") is False

    def test_endswith(self):
        """Test endswith method."""
        self.ctx.set("text", "Hello")
        assert self.engine.evaluate_bool("text.endswith('lo')") is True
        assert self.engine.evaluate_bool("text.endswith('He')") is False

    def test_replace(self):
        """Test replace method."""
        result = self.engine.evaluate("'hello'.replace('l', 'L')")
        assert result.value == "heLLo"

    def test_split(self):
        """Test split method."""
        result = self.engine.evaluate("'a,b,c'.split(',')")
        assert result.value == ["a", "b", "c"]


class TestBuiltinFunctions:
    """Tests for built-in functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ctx = VariableContext({"items": [1, 2, 3, 4, 5], "name": "hello"})
        self.engine = SafeExpressionEngine(self.ctx)

    def test_len(self):
        """Test len function."""
        assert self.engine.evaluate("len(items)").value == 5
        assert self.engine.evaluate("len(name)").value == 5

    def test_str(self):
        """Test str function."""
        assert self.engine.evaluate("str(42)").value == "42"

    def test_int(self):
        """Test int function."""
        assert self.engine.evaluate("int('42')").value == 42
        assert self.engine.evaluate("int(3.7)").value == 3

    def test_float(self):
        """Test float function."""
        assert self.engine.evaluate("float('3.14')").value == 3.14

    def test_bool(self):
        """Test bool function."""
        assert self.engine.evaluate("bool(1)").value is True
        assert self.engine.evaluate("bool(0)").value is False
        assert self.engine.evaluate("bool('')").value is False

    def test_abs(self):
        """Test abs function."""
        assert self.engine.evaluate("abs(-5)").value == 5

    def test_min_max(self):
        """Test min and max functions."""
        assert self.engine.evaluate("min(items)").value == 1
        assert self.engine.evaluate("max(items)").value == 5
        assert self.engine.evaluate("min(3, 1, 2)").value == 1

    def test_sum(self):
        """Test sum function."""
        assert self.engine.evaluate("sum(items)").value == 15

    def test_any_all(self):
        """Test any and all functions."""
        self.ctx.set("bools", [True, True, True])
        assert self.engine.evaluate("all(bools)").value is True
        self.ctx.set("bools", [True, False, True])
        assert self.engine.evaluate("all(bools)").value is False
        assert self.engine.evaluate("any(bools)").value is True

    def test_round(self):
        """Test round function."""
        assert self.engine.evaluate("round(3.7)").value == 4
        assert self.engine.evaluate("round(3.14159, 2)").value == 3.14

    def test_sorted(self):
        """Test sorted function."""
        self.ctx.set("nums", [3, 1, 2])
        assert self.engine.evaluate("sorted(nums)").value == [1, 2, 3]

    def test_range(self):
        """Test range function."""
        assert self.engine.evaluate("range(3)").value == [0, 1, 2]
        assert self.engine.evaluate("range(1, 4)").value == [1, 2, 3]


class TestCollections:
    """Tests for collection literals and operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ctx = VariableContext()
        self.engine = SafeExpressionEngine(self.ctx)

    def test_list_literal(self):
        """Test list literal."""
        result = self.engine.evaluate("[1, 2, 3]")
        assert result.value == [1, 2, 3]

    def test_tuple_literal(self):
        """Test tuple literal."""
        result = self.engine.evaluate("(1, 2, 3)")
        assert result.value == (1, 2, 3)

    def test_dict_literal(self):
        """Test dict literal."""
        result = self.engine.evaluate("{'a': 1, 'b': 2}")
        assert result.value == {"a": 1, "b": 2}

    def test_set_literal(self):
        """Test set literal."""
        result = self.engine.evaluate("{1, 2, 3}")
        assert result.value == {1, 2, 3}

    def test_subscript(self):
        """Test subscript access."""
        self.ctx.set("items", [10, 20, 30])
        assert self.engine.evaluate("items[0]").value == 10
        assert self.engine.evaluate("items[1]").value == 20
        assert self.engine.evaluate("items[-1]").value == 30

    def test_dict_access(self):
        """Test dictionary access."""
        self.ctx.set("data", {"key": "value"})
        assert self.engine.evaluate("data['key']").value == "value"


class TestTernaryExpression:
    """Tests for ternary (if-else) expressions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ctx = VariableContext({"x": 10})
        self.engine = SafeExpressionEngine(self.ctx)

    def test_ternary_true(self):
        """Test ternary with true condition."""
        result = self.engine.evaluate("'yes' if x > 5 else 'no'")
        assert result.value == "yes"

    def test_ternary_false(self):
        """Test ternary with false condition."""
        result = self.engine.evaluate("'yes' if x < 5 else 'no'")
        assert result.value == "no"


class TestListComprehension:
    """Tests for list comprehensions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ctx = VariableContext({"nums": [1, 2, 3, 4, 5]})
        self.engine = SafeExpressionEngine(self.ctx)

    def test_simple_comprehension(self):
        """Test simple list comprehension."""
        result = self.engine.evaluate("[x * 2 for x in nums]")
        assert result.value == [2, 4, 6, 8, 10]

    def test_filtered_comprehension(self):
        """Test list comprehension with filter."""
        result = self.engine.evaluate("[x for x in nums if x > 2]")
        assert result.value == [3, 4, 5]


class TestVariableResolution:
    """Tests for {{variable}} syntax resolution."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ctx = VariableContext({"name": "Alice", "count": 5})
        self.engine = SafeExpressionEngine(self.ctx)

    def test_variable_template(self):
        """Test {{variable}} resolution."""
        result = self.engine.evaluate("{{count}} > 3")
        assert result.value is True

    def test_combined_template(self):
        """Test mixed template and expression."""
        result = self.engine.evaluate("'{{name}}'.upper()")
        assert result.value == "ALICE"


class TestSafetyChecks:
    """Tests for safety checks against malicious expressions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ctx = VariableContext()
        self.engine = SafeExpressionEngine(self.ctx)

    def test_import_blocked(self):
        """Test that import is blocked."""
        result = self.engine.evaluate("__import__('os')")
        assert not result.success

    def test_dunder_access_blocked(self):
        """Test that __class__ access is blocked."""
        result = self.engine.evaluate("''.__class__")
        assert not result.success

    def test_globals_blocked(self):
        """Test that __globals__ access is blocked."""
        result = self.engine.evaluate("(lambda: 0).__globals__")
        assert not result.success

    def test_builtins_blocked(self):
        """Test that __builtins__ access is blocked."""
        result = self.engine.evaluate("().__class__.__bases__[0].__subclasses__")
        assert not result.success

    def test_eval_not_available(self):
        """Test that eval is not available."""
        result = self.engine.evaluate("eval('1+1')")
        assert not result.success

    def test_exec_not_available(self):
        """Test that exec is not available."""
        result = self.engine.evaluate("exec('x=1')")
        assert not result.success

    def test_open_not_available(self):
        """Test that open is not available."""
        result = self.engine.evaluate("open('/etc/passwd')")
        assert not result.success


class TestCustomFunctions:
    """Tests for custom function registration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ctx = VariableContext()
        self.engine = SafeExpressionEngine(self.ctx)

    def test_register_function(self):
        """Test registering a custom function."""
        self.engine.register_function("double", lambda x: x * 2)
        result = self.engine.evaluate("double(5)")
        assert result.value == 10

    def test_unregister_function(self):
        """Test unregistering a function."""
        self.engine.register_function("custom", lambda: "test")
        self.engine.unregister_function("custom")
        result = self.engine.evaluate("custom()")
        assert not result.success


class TestExpressionResult:
    """Tests for ExpressionResult class."""

    def test_bool_conversion_success(self):
        """Test boolean conversion for successful result."""
        result = ExpressionResult(value=True, success=True)
        assert bool(result) is True

        result = ExpressionResult(value=False, success=True)
        assert bool(result) is False

    def test_bool_conversion_failure(self):
        """Test boolean conversion for failed result."""
        result = ExpressionResult(value=None, success=False, error="Error")
        assert bool(result) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
