"""
Configuration management for DittoMation.

This module provides:
- Loading configuration from JSON/YAML files
- Environment variable override support
- Configuration validation
- Default configuration values
- Device-specific configurations
"""

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .exceptions import ConfigLoadError, ConfigValidationError

# Try to import YAML support (optional dependency)
try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

# Default configuration directory
DEFAULT_CONFIG_DIR = Path("config")

# Environment variable prefix for configuration overrides
ENV_PREFIX = "DITTO_"


# ============================================================================
# Default Configuration
# ============================================================================

DEFAULT_CONFIG: Dict[str, Any] = {
    # Logging configuration
    "logging": {
        "level": "INFO",
        "log_to_file": True,
        "log_to_console": True,
        "log_dir": "logs",
        "json_format": False,
        "max_file_size_mb": 10,
        "backup_count": 5,
    },
    # ADB configuration
    "adb": {
        "path": None,  # Auto-detect if None
        "timeout": 30,
        "retry_count": 3,
        "retry_delay": 1.0,
        "retry_backoff": 2.0,  # Exponential backoff multiplier
    },
    # Recording configuration
    "recording": {
        "output_dir": "output",
        "default_workflow_file": "workflow.json",
        "capture_screenshots": False,
        "double_tap_threshold_ms": 300,
        "double_tap_distance_px": 50,
    },
    # Replay configuration
    "replay": {
        "default_delay_ms": 500,
        "element_timeout_ms": 5000,
        "retry_on_failure": True,
        "max_retries": 3,
        "screenshot_on_failure": False,
    },
    # Natural language runner configuration
    "nl_runner": {
        "default_delay_ms": 800,
        "scroll_distance_px": 600,
        "swipe_distance_px": 400,
        "scroll_duration_ms": 400,
        "swipe_duration_ms": 200,
        "min_clickable_area_px": 5000,
    },
    # Gesture configuration
    "gestures": {
        "tap_max_duration_ms": 500,
        "tap_max_movement_px": 50,
        "swipe_min_distance_px": 50,
        "long_press_duration_ms": 1000,
        "pinch_distance_threshold": 30,
    },
    # UI capture configuration
    "ui_capture": {"max_retries": 5, "retry_delay_ms": 1000, "loading_screen_timeout_ms": 10000},
    # Device configuration
    "device": {
        "default_device": None,  # Auto-select if None
        "screen_width": None,  # Auto-detect
        "screen_height": None,  # Auto-detect
    },
    # Ad filter configuration
    "ad_filter": {
        "enabled": True,  # Enable ad filtering
        "strict_mode": False,  # Use stricter detection (fewer false positives)
        "log_filtered": True,  # Log when ads are filtered
        "custom_patterns": {  # Custom ad detection patterns
            "resource_id": [],
            "text": [],
            "content_desc": [],
            "package": [],
            "class": [],
        },
    },
    # Emulator configuration
    "emulator": {
        "default_avd": None,  # Default AVD to use
        "headless": True,  # Run emulators in headless mode
        "gpu": "swiftshader_indirect",  # GPU rendering mode
        "memory_mb": 2048,  # Emulator memory in MB
        "cores": 2,  # Number of CPU cores
        "boot_timeout": 300,  # Boot timeout in seconds
        "auto_start": False,  # Auto-start emulator if no device
        "auto_stop": True,  # Auto-stop emulator after automation
        "no_audio": True,  # Disable audio
        "no_boot_anim": True,  # Skip boot animation
    },
    # Cloud provider configuration
    "cloud": {
        "default_provider": None,  # Default cloud provider (firebase, aws)
        "firebase": {
            "project_id": None,  # Google Cloud project ID
            "credentials_file": None,  # Path to service account JSON
            "results_bucket": None,  # GCS bucket for results
        },
        "aws": {
            "region": "us-west-2",  # AWS region
            "project_arn": None,  # Device Farm project ARN
            "device_pool_arn": None,  # Device pool ARN (optional)
        },
        "test_timeout": 3600,  # Default test timeout in seconds
        "poll_interval": 30,  # Status poll interval in seconds
    },
}


# Configuration schema for validation
CONFIG_SCHEMA: Dict[str, Dict[str, Any]] = {
    "logging.level": {"type": str, "allowed": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]},
    "logging.log_to_file": {"type": bool},
    "logging.log_to_console": {"type": bool},
    "logging.log_dir": {"type": str},
    "logging.json_format": {"type": bool},
    "logging.max_file_size_mb": {"type": int, "min": 1, "max": 1000},
    "logging.backup_count": {"type": int, "min": 0, "max": 100},
    "adb.timeout": {"type": int, "min": 1, "max": 300},
    "adb.retry_count": {"type": int, "min": 0, "max": 10},
    "adb.retry_delay": {"type": (int, float), "min": 0},
    "adb.retry_backoff": {"type": (int, float), "min": 1},
    "recording.double_tap_threshold_ms": {"type": int, "min": 100, "max": 2000},
    "recording.double_tap_distance_px": {"type": int, "min": 10, "max": 200},
    "replay.default_delay_ms": {"type": int, "min": 0, "max": 10000},
    "replay.element_timeout_ms": {"type": int, "min": 1000, "max": 60000},
    "replay.max_retries": {"type": int, "min": 0, "max": 10},
    "nl_runner.default_delay_ms": {"type": int, "min": 0, "max": 10000},
    "nl_runner.scroll_distance_px": {"type": int, "min": 100, "max": 2000},
    "nl_runner.swipe_distance_px": {"type": int, "min": 100, "max": 2000},
    "gestures.tap_max_duration_ms": {"type": int, "min": 100, "max": 2000},
    "gestures.tap_max_movement_px": {"type": int, "min": 10, "max": 200},
    "gestures.swipe_min_distance_px": {"type": int, "min": 20, "max": 500},
    "gestures.long_press_duration_ms": {"type": int, "min": 500, "max": 5000},
    "ui_capture.max_retries": {"type": int, "min": 1, "max": 20},
    "ui_capture.retry_delay_ms": {"type": int, "min": 100, "max": 5000},
    # Emulator configuration validation
    "emulator.headless": {"type": bool},
    "emulator.gpu": {
        "type": str,
        "allowed": ["auto", "host", "swiftshader_indirect", "angle_indirect", "off"],
    },
    "emulator.memory_mb": {"type": int, "min": 512, "max": 16384},
    "emulator.cores": {"type": int, "min": 1, "max": 16},
    "emulator.boot_timeout": {"type": int, "min": 30, "max": 900},
    "emulator.auto_start": {"type": bool},
    "emulator.auto_stop": {"type": bool},
    "emulator.no_audio": {"type": bool},
    "emulator.no_boot_anim": {"type": bool},
    # Cloud configuration validation
    "cloud.test_timeout": {"type": int, "min": 60, "max": 14400},
    "cloud.poll_interval": {"type": int, "min": 5, "max": 300},
    "cloud.aws.region": {"type": str},
}


class ConfigManager:
    """
    Configuration manager for DittoMation.

    Provides loading, validation, and access to configuration values.
    """

    def __init__(self, config_file: Optional[Union[str, Path]] = None):
        """
        Initialize the configuration manager.

        Args:
            config_file: Optional path to configuration file
        """
        self._config: Dict[str, Any] = deepcopy(DEFAULT_CONFIG)
        self._config_file: Optional[Path] = None
        self._device_configs: Dict[str, Dict[str, Any]] = {}

        if config_file:
            self.load(config_file)

    def load(self, config_file: Union[str, Path]) -> None:
        """
        Load configuration from a file.

        Args:
            config_file: Path to configuration file (JSON or YAML)

        Raises:
            ConfigLoadError: If the file cannot be loaded
        """
        config_path = Path(config_file)

        if not config_path.exists():
            raise ConfigLoadError(str(config_path), "File not found")

        try:
            content = config_path.read_text(encoding="utf-8")

            if config_path.suffix.lower() in (".yaml", ".yml"):
                if not YAML_AVAILABLE:
                    raise ConfigLoadError(
                        str(config_path),
                        "YAML support not available. Install PyYAML or use JSON format.",
                    )
                data = yaml.safe_load(content)
            else:
                data = json.loads(content)

            self._merge_config(data)
            self._config_file = config_path

        except json.JSONDecodeError as e:
            raise ConfigLoadError(str(config_path), f"Invalid JSON: {e}")
        except Exception as e:
            if isinstance(e, ConfigLoadError):
                raise
            raise ConfigLoadError(str(config_path), str(e))

    def _merge_config(
        self, data: Dict[str, Any], target: Optional[Dict[str, Any]] = None, prefix: str = ""
    ) -> None:
        """
        Recursively merge configuration data into target.

        Args:
            data: Configuration data to merge
            target: Target dictionary (defaults to self._config)
            prefix: Key prefix for nested values
        """
        if target is None:
            target = self._config

        for key, value in data.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_config(value, target[key], f"{prefix}{key}.")
            else:
                target[key] = value

    def load_env_overrides(self) -> None:
        """
        Load configuration overrides from environment variables.

        Environment variables follow the pattern: DITTO_SECTION_KEY
        For example: DITTO_LOGGING_LEVEL=DEBUG
        """
        for env_key, env_value in os.environ.items():
            if not env_key.startswith(ENV_PREFIX):
                continue

            # Convert DITTO_LOGGING_LEVEL to logging.level
            config_key = env_key[len(ENV_PREFIX) :].lower().replace("_", ".", 1)

            # Find the section and key
            parts = config_key.split(".", 1)
            if len(parts) != 2:
                continue

            section, key = parts
            if section in self._config and key in self._config[section]:
                # Convert value to appropriate type
                current_value = self._config[section][key]
                try:
                    if isinstance(current_value, bool):
                        self._config[section][key] = env_value.lower() in ("true", "1", "yes")
                    elif isinstance(current_value, int):
                        self._config[section][key] = int(env_value)
                    elif isinstance(current_value, float):
                        self._config[section][key] = float(env_value)
                    else:
                        self._config[section][key] = env_value
                except ValueError:
                    pass  # Ignore invalid conversions

    def validate(self) -> List[str]:
        """
        Validate the current configuration.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        for key_path, schema in CONFIG_SCHEMA.items():
            parts = key_path.split(".")
            value = self._config

            # Navigate to the value
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    value = None
                    break

            if value is None:
                continue

            # Type check
            expected_type = schema.get("type")
            if expected_type and not isinstance(value, expected_type):
                # Handle tuple of types (e.g., (int, float))
                if isinstance(expected_type, tuple):
                    type_names = " or ".join(t.__name__ for t in expected_type)
                    errors.append(f"{key_path}: expected {type_names}, got {type(value).__name__}")
                else:
                    errors.append(
                        f"{key_path}: expected {expected_type.__name__}, got {type(value).__name__}"
                    )
                continue

            # Allowed values check
            allowed = schema.get("allowed")
            if allowed and value not in allowed:
                errors.append(f"{key_path}: value '{value}' not in allowed values {allowed}")

            # Range check
            min_val = schema.get("min")
            max_val = schema.get("max")
            if min_val is not None and value < min_val:
                errors.append(f"{key_path}: value {value} is below minimum {min_val}")
            if max_val is not None and value > max_val:
                errors.append(f"{key_path}: value {value} is above maximum {max_val}")

        return errors

    def validate_or_raise(self) -> None:
        """
        Validate configuration and raise exception if invalid.

        Raises:
            ConfigValidationError: If validation fails
        """
        errors = self.validate()
        if errors:
            raise ConfigValidationError(errors)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by dot-separated key.

        Args:
            key: Configuration key (e.g., "logging.level")
            default: Default value if key not found

        Returns:
            Configuration value
        """
        parts = key.split(".")
        value = self._config

        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value by dot-separated key.

        Args:
            key: Configuration key (e.g., "logging.level")
            value: Value to set
        """
        parts = key.split(".")
        target = self._config

        for part in parts[:-1]:
            if part not in target:
                target[part] = {}
            target = target[part]

        target[parts[-1]] = value

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get an entire configuration section.

        Args:
            section: Section name (e.g., "logging")

        Returns:
            Dictionary with section configuration
        """
        return deepcopy(self._config.get(section, {}))

    def load_device_config(self, device_id: str, config_file: Union[str, Path]) -> None:
        """
        Load device-specific configuration.

        Args:
            device_id: Device identifier
            config_file: Path to device configuration file
        """
        config_path = Path(config_file)

        if not config_path.exists():
            raise ConfigLoadError(str(config_path), "Device config file not found")

        try:
            content = config_path.read_text(encoding="utf-8")
            if config_path.suffix.lower() in (".yaml", ".yml"):
                if not YAML_AVAILABLE:
                    raise ConfigLoadError(str(config_path), "YAML not available")
                data = yaml.safe_load(content)
            else:
                data = json.loads(content)

            self._device_configs[device_id] = data

        except Exception as e:
            if isinstance(e, ConfigLoadError):
                raise
            raise ConfigLoadError(str(config_path), str(e))

    def get_device_config(self, device_id: str, key: str, default: Any = None) -> Any:
        """
        Get a device-specific configuration value.

        Falls back to global configuration if device-specific value not found.

        Args:
            device_id: Device identifier
            key: Configuration key
            default: Default value

        Returns:
            Configuration value
        """
        # Check device-specific config first
        if device_id in self._device_configs:
            device_config = self._device_configs[device_id]
            parts = key.split(".")
            value = device_config

            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    value = None
                    break

            if value is not None:
                return value

        # Fall back to global config
        return self.get(key, default)

    def save(self, filepath: Optional[Union[str, Path]] = None) -> None:
        """
        Save current configuration to a file.

        Args:
            filepath: Output file path (defaults to loaded config file)

        Raises:
            ConfigLoadError: If no filepath specified and no config loaded
        """
        if filepath is None:
            if self._config_file is None:
                raise ConfigLoadError("", "No configuration file specified")
            filepath = self._config_file

        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if output_path.suffix.lower() in (".yaml", ".yml"):
            if not YAML_AVAILABLE:
                raise ConfigLoadError(str(output_path), "YAML not available")
            content = yaml.dump(self._config, default_flow_style=False)
        else:
            content = json.dumps(self._config, indent=2)

        output_path.write_text(content, encoding="utf-8")

    def to_dict(self) -> Dict[str, Any]:
        """
        Get the entire configuration as a dictionary.

        Returns:
            Copy of configuration dictionary
        """
        return deepcopy(self._config)

    def __repr__(self) -> str:
        return f"ConfigManager(config_file={self._config_file})"


# ============================================================================
# Global configuration instance
# ============================================================================

_global_config: Optional[ConfigManager] = None


def init_config(
    config_file: Optional[Union[str, Path]] = None, load_env: bool = True, validate: bool = True
) -> ConfigManager:
    """
    Initialize the global configuration.

    Args:
        config_file: Optional path to configuration file
        load_env: Load environment variable overrides
        validate: Validate configuration after loading

    Returns:
        The global ConfigManager instance
    """
    global _global_config

    _global_config = ConfigManager(config_file)

    if load_env:
        _global_config.load_env_overrides()

    if validate:
        _global_config.validate_or_raise()

    return _global_config


def get_config() -> ConfigManager:
    """
    Get the global configuration instance.

    Returns:
        The global ConfigManager (initializes with defaults if not set up)
    """
    global _global_config
    if _global_config is None:
        _global_config = ConfigManager()
    return _global_config


def get_config_value(key: str, default: Any = None) -> Any:
    """
    Get a configuration value from the global config.

    Args:
        key: Configuration key (e.g., "logging.level")
        default: Default value if key not found

    Returns:
        Configuration value
    """
    return get_config().get(key, default)
