"""
Unit tests for core.variables module.

Tests VariableContext and VariableResolver classes for:
- Basic get/set/delete operations
- Nested key access with dot notation
- Array index access
- Default values
- Variable resolution in templates
"""

import json
import os
import tempfile

import pytest

from core.variables import VariableContext, VariableResolver


class TestVariableContext:
    """Tests for VariableContext class."""

    def test_init_empty(self):
        """Test empty initialization."""
        ctx = VariableContext()
        assert len(ctx) == 0
        assert ctx.to_dict() == {}

    def test_init_with_values(self):
        """Test initialization with initial values."""
        ctx = VariableContext({"username": "test", "count": 5})
        assert ctx.get("username") == "test"
        assert ctx.get("count") == 5
        assert len(ctx) == 2

    def test_get_set_basic(self):
        """Test basic get and set operations."""
        ctx = VariableContext()
        ctx.set("name", "Alice")
        assert ctx.get("name") == "Alice"

    def test_get_default(self):
        """Test get with default value."""
        ctx = VariableContext()
        assert ctx.get("missing") is None
        assert ctx.get("missing", "default") == "default"

    def test_has(self):
        """Test has method."""
        ctx = VariableContext({"exists": True})
        assert ctx.has("exists") is True
        assert ctx.has("missing") is False

    def test_delete(self):
        """Test delete method."""
        ctx = VariableContext({"key": "value"})
        ctx.delete("key")
        assert ctx.has("key") is False

    def test_delete_nonexistent(self):
        """Test deleting non-existent key doesn't raise."""
        ctx = VariableContext()
        ctx.delete("nonexistent")  # Should not raise

    def test_nested_get_dot_notation(self):
        """Test nested access with dot notation."""
        ctx = VariableContext({"user": {"name": "Alice", "age": 30}, "settings": {"theme": "dark"}})
        assert ctx.get("user.name") == "Alice"
        assert ctx.get("user.age") == 30
        assert ctx.get("settings.theme") == "dark"

    def test_nested_get_missing(self):
        """Test nested access with missing keys."""
        ctx = VariableContext({"user": {"name": "Alice"}})
        assert ctx.get("user.email") is None
        assert ctx.get("user.email", "default@example.com") == "default@example.com"

    def test_array_access(self):
        """Test array index access."""
        ctx = VariableContext({"items": ["a", "b", "c"]})
        assert ctx.get("items[0]") == "a"
        assert ctx.get("items[1]") == "b"
        assert ctx.get("items[2]") == "c"

    def test_nested_array_access(self):
        """Test nested array access."""
        ctx = VariableContext({"data": {"items": [{"name": "first"}, {"name": "second"}]}})
        assert ctx.get("data.items[0].name") == "first"
        assert ctx.get("data.items[1].name") == "second"

    def test_set_nested(self):
        """Test setting nested values."""
        ctx = VariableContext()
        ctx.set("user.name", "Bob")
        assert ctx.get("user.name") == "Bob"
        assert ctx.get("user") == {"name": "Bob"}

    def test_update(self):
        """Test update method."""
        ctx = VariableContext({"a": 1})
        ctx.update({"b": 2, "c": 3})
        assert ctx.get("a") == 1
        assert ctx.get("b") == 2
        assert ctx.get("c") == 3

    def test_clear(self):
        """Test clear method."""
        ctx = VariableContext({"a": 1, "b": 2})
        ctx.clear()
        assert len(ctx) == 0

    def test_contains_operator(self):
        """Test 'in' operator."""
        ctx = VariableContext({"key": "value"})
        assert "key" in ctx
        assert "missing" not in ctx

    def test_bracket_notation(self):
        """Test bracket notation access."""
        ctx = VariableContext()
        ctx["name"] = "Test"
        assert ctx["name"] == "Test"

    def test_from_env(self):
        """Test loading from environment variables."""
        os.environ["DITTO_USERNAME"] = "envuser"
        os.environ["DITTO_COUNT"] = "42"
        os.environ["OTHER_VAR"] = "ignored"

        ctx = VariableContext()
        ctx.from_env(prefix="DITTO_")

        assert ctx.get("username") == "envuser"
        assert ctx.get("count") == 42  # Should be parsed as int
        assert ctx.has("other_var") is False

        # Cleanup
        del os.environ["DITTO_USERNAME"]
        del os.environ["DITTO_COUNT"]
        del os.environ["OTHER_VAR"]

    def test_from_file_json(self):
        """Test loading from JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"var1": "value1", "var2": 123}, f)
            temp_path = f.name

        try:
            ctx = VariableContext()
            ctx.from_file(temp_path)
            assert ctx.get("var1") == "value1"
            assert ctx.get("var2") == 123
        finally:
            os.unlink(temp_path)

    def test_to_dict(self):
        """Test to_dict returns a copy."""
        ctx = VariableContext({"key": "value"})
        d = ctx.to_dict()
        d["key"] = "modified"
        assert ctx.get("key") == "value"  # Original unchanged


class TestVariableResolver:
    """Tests for VariableResolver class."""

    def test_resolve_simple(self):
        """Test simple variable resolution."""
        ctx = VariableContext({"name": "Alice"})
        resolver = VariableResolver(ctx)
        result = resolver.resolve_string("Hello {{name}}!")
        assert result == "Hello Alice!"

    def test_resolve_multiple(self):
        """Test multiple variable resolution."""
        ctx = VariableContext({"first": "John", "last": "Doe"})
        resolver = VariableResolver(ctx)
        result = resolver.resolve_string("{{first}} {{last}}")
        assert result == "John Doe"

    def test_resolve_nested(self):
        """Test nested variable resolution."""
        ctx = VariableContext({"user": {"name": "Bob"}})
        resolver = VariableResolver(ctx)
        result = resolver.resolve_string("User: {{user.name}}")
        assert result == "User: Bob"

    def test_resolve_with_default(self):
        """Test resolution with default value."""
        ctx = VariableContext()
        resolver = VariableResolver(ctx)
        result = resolver.resolve_string("Value: {{missing|default_value}}")
        assert result == "Value: default_value"

    def test_resolve_missing_no_raise(self):
        """Test missing variable without raising."""
        ctx = VariableContext()
        resolver = VariableResolver(ctx)
        result = resolver.resolve_string("Value: {{missing}}")
        assert result == "Value: {{missing}}"  # Unchanged

    def test_resolve_missing_raises(self):
        """Test missing variable with raise_on_missing."""
        from core.exceptions import VariableNotFoundError

        ctx = VariableContext()
        resolver = VariableResolver(ctx)

        with pytest.raises(VariableNotFoundError):
            resolver.resolve_string("{{missing}}", raise_on_missing=True)

    def test_resolve_whitespace(self):
        """Test resolution with whitespace in placeholder."""
        ctx = VariableContext({"name": "Test"})
        resolver = VariableResolver(ctx)
        result = resolver.resolve_string("{{ name }}")
        assert result == "Test"

    def test_resolve_value_dict(self):
        """Test resolve_value with dictionary."""
        ctx = VariableContext({"name": "Alice"})
        resolver = VariableResolver(ctx)
        data = {"greeting": "Hello {{name}}", "count": 5}
        result = resolver.resolve_value(data)
        assert result == {"greeting": "Hello Alice", "count": 5}

    def test_resolve_value_list(self):
        """Test resolve_value with list."""
        ctx = VariableContext({"item": "test"})
        resolver = VariableResolver(ctx)
        data = ["{{item}}", "static", "{{item}}2"]
        result = resolver.resolve_value(data)
        assert result == ["test", "static", "test2"]

    def test_has_variables(self):
        """Test has_variables method."""
        ctx = VariableContext()
        resolver = VariableResolver(ctx)

        assert resolver.has_variables("Hello {{name}}") is True
        assert resolver.has_variables("Hello world") is False

    def test_extract_variables(self):
        """Test extract_variables method."""
        ctx = VariableContext()
        resolver = VariableResolver(ctx)

        vars_list = resolver.extract_variables("{{a}} and {{b}} and {{c|default}}")
        assert vars_list == ["a", "b", "c"]

    def test_resolve_numeric(self):
        """Test resolving numeric values."""
        ctx = VariableContext({"count": 42, "pi": 3.14})
        resolver = VariableResolver(ctx)

        assert resolver.resolve_string("Count: {{count}}") == "Count: 42"
        assert resolver.resolve_string("Pi: {{pi}}") == "Pi: 3.14"

    def test_resolve_boolean(self):
        """Test resolving boolean values."""
        ctx = VariableContext({"flag": True, "other": False})
        resolver = VariableResolver(ctx)

        assert resolver.resolve_string("Flag: {{flag}}") == "Flag: True"
        assert resolver.resolve_string("Other: {{other}}") == "Other: False"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
