"""
Variable Storage & Resolution for DittoMation automation.

Provides variable context management and template resolution for {{variable}} syntax.
Supports nested variables, environment variables, and JSON/YAML file loading.

Usage:
    from core.variables import VariableContext, VariableResolver

    # Create context with initial variables
    ctx = VariableContext({"username": "test", "retries": 3})

    # Set and get variables
    ctx.set("password", "secret")
    value = ctx.get("username")

    # Resolve templates
    resolver = VariableResolver(ctx)
    result = resolver.resolve_string("Hello {{username}}!")
"""

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

if TYPE_CHECKING:
    from core.automation import Step


@dataclass
class VariableContext:
    """
    Holds all variables for an automation run.

    Supports:
    - Basic key-value storage
    - Nested key access with dot notation (e.g., "user.name")
    - Array index access (e.g., "items[0]")
    - Environment variable loading
    - JSON/YAML file loading

    Example:
        ctx = VariableContext({"user": {"name": "John"}, "items": ["a", "b", "c"]})
        ctx.get("user.name")  # "John"
        ctx.get("items[0]")   # "a"
    """

    _variables: Dict[str, Any] = field(default_factory=dict)

    def __init__(self, initial: Optional[Dict[str, Any]] = None):
        """Initialize with optional initial variables."""
        self._variables = dict(initial) if initial else {}

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a variable value by key.

        Supports dot notation for nested access and bracket notation for arrays.

        Args:
            key: Variable key (e.g., "username", "user.name", "items[0]")
            default: Default value if key not found

        Returns:
            Variable value or default
        """
        try:
            return self._resolve_key(key)
        except (KeyError, IndexError, TypeError):
            return default

    def _resolve_key(self, key: str) -> Any:
        """Resolve a potentially nested key path."""
        # Handle simple keys first
        if key in self._variables:
            return self._variables[key]

        # Parse complex keys with dots and brackets
        parts = self._parse_key_path(key)
        current = self._variables

        for part in parts:
            if isinstance(part, int):
                # Array index
                current = current[part]
            else:
                # Dictionary key
                current = current[part]

        return current

    def _parse_key_path(self, key: str) -> list:
        """
        Parse a key path into parts.

        Examples:
            "user.name" -> ["user", "name"]
            "items[0]" -> ["items", 0]
            "data.items[0].name" -> ["data", "items", 0, "name"]
        """
        parts = []
        # Match either .identifier, [number], or [string]
        pattern = r"([a-zA-Z_][a-zA-Z0-9_]*|\[\d+\]|\[\'[^\']*\'\]|\[\"[^\"]*\"\])"
        tokens = re.findall(pattern, key)

        for token in tokens:
            if token.startswith("[") and token.endswith("]"):
                inner = token[1:-1]
                # Check if it's a number
                if inner.isdigit() or (inner.startswith("-") and inner[1:].isdigit()):
                    parts.append(int(inner))
                else:
                    # Remove quotes if present
                    if (inner.startswith("'") and inner.endswith("'")) or (
                        inner.startswith('"') and inner.endswith('"')
                    ):
                        inner = inner[1:-1]
                    parts.append(inner)
            else:
                parts.append(token)

        return parts

    def set(self, key: str, value: Any) -> None:
        """
        Set a variable value.

        Supports dot notation for creating nested structures.

        Args:
            key: Variable key (e.g., "username", "user.name")
            value: Value to set
        """
        if "." not in key and "[" not in key:
            # Simple key
            self._variables[key] = value
        else:
            # Nested key - create structure
            parts = self._parse_key_path(key)
            current = self._variables

            for i, part in enumerate(parts[:-1]):
                if isinstance(part, int):
                    # Ensure list exists and is long enough
                    while len(current) <= part:
                        current.append(None)
                    if current[part] is None:
                        next_part = parts[i + 1]
                        current[part] = [] if isinstance(next_part, int) else {}
                    current = current[part]
                else:
                    if part not in current:
                        next_part = parts[i + 1]
                        current[part] = [] if isinstance(next_part, int) else {}
                    current = current[part]

            # Set the final value
            final_part = parts[-1]
            if isinstance(final_part, int):
                while len(current) <= final_part:
                    current.append(None)
                current[final_part] = value
            else:
                current[final_part] = value

    def has(self, key: str) -> bool:
        """Check if a variable exists."""
        try:
            self._resolve_key(key)
            return True
        except (KeyError, IndexError, TypeError):
            return False

    def delete(self, key: str) -> None:
        """Delete a variable."""
        if "." not in key and "[" not in key:
            if key in self._variables:
                del self._variables[key]
        else:
            parts = self._parse_key_path(key)
            current = self._variables

            # Navigate to parent
            for part in parts[:-1]:
                if isinstance(part, int):
                    current = current[part]
                else:
                    current = current[part]

            # Delete final key
            final_part = parts[-1]
            if isinstance(final_part, int):
                del current[final_part]
            else:
                if final_part in current:
                    del current[final_part]

    def to_dict(self) -> Dict[str, Any]:
        """Return a copy of all variables as a dictionary."""
        return dict(self._variables)

    def update(self, values: Dict[str, Any]) -> None:
        """Update multiple variables at once."""
        self._variables.update(values)

    def clear(self) -> None:
        """Clear all variables."""
        self._variables.clear()

    def from_env(self, prefix: str = "DITTO_") -> None:
        """
        Load variables from environment variables.

        Args:
            prefix: Only load env vars starting with this prefix.
                   The prefix is stripped from the variable name.
        """
        for key, value in os.environ.items():
            if key.startswith(prefix):
                var_name = key[len(prefix) :].lower()
                # Try to parse as JSON for complex values
                try:
                    self._variables[var_name] = json.loads(value)
                except json.JSONDecodeError:
                    self._variables[var_name] = value

    def from_file(self, path: Union[str, Path], format: Optional[str] = None) -> None:
        """
        Load variables from a JSON or YAML file.

        Args:
            path: Path to the file
            format: File format ("json" or "yaml"). Auto-detected from extension if None.
        """
        path = Path(path)

        if format is None:
            ext = path.suffix.lower()
            if ext in (".yaml", ".yml"):
                format = "yaml"
            else:
                format = "json"

        with open(path, encoding="utf-8") as f:
            if format == "yaml":
                try:
                    import yaml

                    data = yaml.safe_load(f)
                except ImportError:
                    raise ImportError(
                        "PyYAML is required for YAML file support. Install with: pip install pyyaml"
                    )
            else:
                data = json.load(f)

        if isinstance(data, dict):
            self._variables.update(data)

    def __contains__(self, key: str) -> bool:
        """Support 'in' operator."""
        return self.has(key)

    def __getitem__(self, key: str) -> Any:
        """Support bracket notation access."""
        return self.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Support bracket notation assignment."""
        self.set(key, value)

    def __len__(self) -> int:
        """Return number of top-level variables."""
        return len(self._variables)


class VariableResolver:
    """
    Resolves {{variable}} placeholders in strings.

    Supports:
    - Simple variables: {{username}}
    - Nested access: {{user.name}}
    - Array access: {{items[0]}}
    - Default values: {{username|default_value}}

    Example:
        ctx = VariableContext({"name": "John", "count": 5})
        resolver = VariableResolver(ctx)
        resolver.resolve_string("Hello {{name}}!")  # "Hello John!"
        resolver.resolve_string("Count: {{count}}")  # "Count: 5"
    """

    # Pattern to match {{variable}} or {{variable|default}}
    PATTERN = re.compile(r"\{\{(.+?)\}\}")

    def __init__(self, context: VariableContext):
        """
        Initialize resolver with a variable context.

        Args:
            context: VariableContext instance
        """
        self.context = context

    def resolve_string(self, template: str, raise_on_missing: bool = False) -> str:
        """
        Resolve all {{variable}} placeholders in a string.

        Args:
            template: String with {{variable}} placeholders
            raise_on_missing: If True, raise VariableNotFoundError for missing variables.
                             If False, leave the placeholder unchanged.

        Returns:
            String with variables resolved

        Raises:
            VariableNotFoundError: If raise_on_missing=True and a variable is not found
        """

        def replace_match(match):
            expr = match.group(1).strip()

            # Check for default value syntax: {{var|default}}
            if "|" in expr:
                var_name, default = expr.split("|", 1)
                var_name = var_name.strip()
                default = default.strip()
            else:
                var_name = expr
                default = None

            # Try to get the value
            if self.context.has(var_name):
                value = self.context.get(var_name)
                return str(value) if value is not None else ""
            elif default is not None:
                return default
            elif raise_on_missing:
                from core.exceptions import VariableNotFoundError

                raise VariableNotFoundError(var_name)
            else:
                # Leave placeholder unchanged
                return match.group(0)

        return self.PATTERN.sub(replace_match, template)

    def resolve_value(self, value: Any, raise_on_missing: bool = False) -> Any:
        """
        Resolve variables in a value, handling different types.

        Args:
            value: Value to resolve (string, list, dict, or primitive)
            raise_on_missing: If True, raise for missing variables

        Returns:
            Value with all string fields resolved
        """
        if isinstance(value, str):
            return self.resolve_string(value, raise_on_missing)
        elif isinstance(value, dict):
            return {k: self.resolve_value(v, raise_on_missing) for k, v in value.items()}
        elif isinstance(value, list):
            return [self.resolve_value(item, raise_on_missing) for item in value]
        else:
            return value

    def resolve_step(self, step: "Step") -> "Step":
        """
        Resolve all variables in a Step object.

        Creates a new Step with resolved values for text, id, desc, value, app fields.

        Args:
            step: Step object to resolve

        Returns:
            New Step with resolved variables
        """
        from dataclasses import asdict

        # Get step as dict
        step_dict = asdict(step)

        # Fields that should have variables resolved
        resolvable_fields = {"text", "id", "desc", "value", "app", "direction", "description"}

        for field_name in resolvable_fields:
            if field_name in step_dict and step_dict[field_name] is not None:
                step_dict[field_name] = self.resolve_string(str(step_dict[field_name]))

        # Handle condition field specially - skip callable
        if "condition" in step_dict:
            step_dict["condition"] = None

        # Create new Step with resolved values
        from core.automation import Step

        return Step(**step_dict)

    def has_variables(self, template: str) -> bool:
        """Check if a string contains any {{variable}} placeholders."""
        return bool(self.PATTERN.search(template))

    def extract_variables(self, template: str) -> list:
        """
        Extract all variable names from a template string.

        Args:
            template: String with {{variable}} placeholders

        Returns:
            List of variable names (without default values)
        """
        matches = self.PATTERN.findall(template)
        variables = []
        for match in matches:
            # Strip default value if present
            var_name = match.split("|")[0].strip()
            variables.append(var_name)
        return variables
