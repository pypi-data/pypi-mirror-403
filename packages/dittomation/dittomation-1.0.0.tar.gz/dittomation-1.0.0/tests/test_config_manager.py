"""Tests for core.config_manager module."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from core.config_manager import (
    DEFAULT_CONFIG,
    ConfigManager,
    get_config,
    get_config_value,
    init_config,
)
from core.exceptions import ConfigLoadError, ConfigValidationError


class TestConfigManager:
    """Tests for ConfigManager class."""

    def test_init_default(self):
        config = ConfigManager()
        assert config._config is not None
        assert "logging" in config._config
        assert "adb" in config._config

    def test_init_loads_defaults(self):
        config = ConfigManager()
        assert config.get("logging.level") == "INFO"
        assert config.get("adb.timeout") == 30

    def test_get_nested_value(self):
        config = ConfigManager()
        assert config.get("logging.level") == "INFO"
        assert config.get("adb.retry_count") == 3

    def test_get_default_for_missing_key(self):
        config = ConfigManager()
        assert config.get("nonexistent.key", "default") == "default"

    def test_set_value(self):
        config = ConfigManager()
        config.set("logging.level", "DEBUG")
        assert config.get("logging.level") == "DEBUG"

    def test_set_nested_value(self):
        config = ConfigManager()
        config.set("custom.nested.key", "value")
        assert config.get("custom.nested.key") == "value"

    def test_get_section(self):
        config = ConfigManager()
        logging_config = config.get_section("logging")
        assert "level" in logging_config
        assert "log_to_file" in logging_config

    def test_get_section_returns_copy(self):
        config = ConfigManager()
        section = config.get_section("logging")
        section["level"] = "CHANGED"
        assert config.get("logging.level") != "CHANGED"

    def test_to_dict_returns_copy(self):
        config = ConfigManager()
        d = config.to_dict()
        d["logging"]["level"] = "CHANGED"
        assert config.get("logging.level") != "CHANGED"


class TestConfigManagerLoadFile:
    """Tests for loading configuration from files."""

    def test_load_json_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"logging": {"level": "DEBUG"}}, f)
            f.flush()
            filepath = f.name

        try:
            config = ConfigManager(filepath)
            assert config.get("logging.level") == "DEBUG"
        finally:
            os.unlink(filepath)

    def test_load_file_not_found(self):
        with pytest.raises(ConfigLoadError) as exc_info:
            ConfigManager("/nonexistent/config.json")
        assert "not found" in str(exc_info.value).lower()

    def test_load_invalid_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{ invalid json }")
            f.flush()
            filepath = f.name

        try:
            with pytest.raises(ConfigLoadError) as exc_info:
                ConfigManager(filepath)
            assert "Invalid JSON" in str(exc_info.value)
        finally:
            os.unlink(filepath)

    def test_load_merges_with_defaults(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"logging": {"level": "DEBUG"}}, f)
            f.flush()
            filepath = f.name

        try:
            config = ConfigManager(filepath)
            # Custom value should be loaded
            assert config.get("logging.level") == "DEBUG"
            # Default values should still exist
            assert config.get("adb.timeout") == 30
        finally:
            os.unlink(filepath)


class TestConfigManagerValidation:
    """Tests for configuration validation."""

    def test_validate_valid_config(self):
        config = ConfigManager()
        errors = config.validate()
        assert errors == []

    def test_validate_invalid_log_level(self):
        config = ConfigManager()
        config.set("logging.level", "INVALID_LEVEL")
        errors = config.validate()
        assert len(errors) > 0
        assert any("logging.level" in e for e in errors)

    def test_validate_invalid_timeout(self):
        config = ConfigManager()
        config.set("adb.timeout", -1)
        errors = config.validate()
        assert len(errors) > 0
        assert any("adb.timeout" in e for e in errors)

    def test_validate_timeout_above_max(self):
        config = ConfigManager()
        config.set("adb.timeout", 999999)
        errors = config.validate()
        assert len(errors) > 0

    def test_validate_or_raise_valid(self):
        config = ConfigManager()
        config.validate_or_raise()  # Should not raise

    def test_validate_or_raise_invalid(self):
        config = ConfigManager()
        config.set("logging.level", "INVALID")
        with pytest.raises(ConfigValidationError):
            config.validate_or_raise()


class TestConfigManagerEnvOverrides:
    """Tests for environment variable overrides."""

    def test_load_env_string_override(self):
        config = ConfigManager()
        with patch.dict(os.environ, {"DITTO_LOGGING_LEVEL": "DEBUG"}):
            config.load_env_overrides()
        assert config.get("logging.level") == "DEBUG"

    def test_load_env_bool_override(self):
        config = ConfigManager()
        with patch.dict(os.environ, {"DITTO_LOGGING_LOG_TO_FILE": "false"}):
            config.load_env_overrides()
        assert config.get("logging.log_to_file") is False

    def test_load_env_int_override(self):
        config = ConfigManager()
        with patch.dict(os.environ, {"DITTO_ADB_TIMEOUT": "60"}):
            config.load_env_overrides()
        assert config.get("adb.timeout") == 60

    def test_load_env_ignores_invalid(self):
        config = ConfigManager()
        original = config.get("adb.timeout")
        with patch.dict(os.environ, {"DITTO_ADB_TIMEOUT": "not_a_number"}):
            config.load_env_overrides()
        assert config.get("adb.timeout") == original


class TestConfigManagerSave:
    """Tests for saving configuration."""

    def test_save_to_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "config.json"

            config = ConfigManager()
            config.set("logging.level", "DEBUG")
            config.save(filepath)

            # Verify file contents
            with open(filepath) as f:
                data = json.load(f)
            assert data["logging"]["level"] == "DEBUG"

    def test_save_without_filepath_raises(self):
        config = ConfigManager()
        with pytest.raises(ConfigLoadError):
            config.save()

    def test_save_creates_parent_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "subdir" / "config.json"

            config = ConfigManager()
            config.save(filepath)

            assert filepath.exists()


class TestConfigManagerDeviceConfig:
    """Tests for device-specific configuration."""

    def test_load_device_config(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"custom_setting": "value"}, f)
            f.flush()
            filepath = f.name

        try:
            config = ConfigManager()
            config.load_device_config("device123", filepath)
            assert config.get_device_config("device123", "custom_setting") == "value"
        finally:
            os.unlink(filepath)

    def test_get_device_config_falls_back_to_global(self):
        config = ConfigManager()
        # No device config loaded, should return global config
        assert config.get_device_config("device123", "logging.level") == "INFO"

    def test_load_device_config_file_not_found(self):
        config = ConfigManager()
        with pytest.raises(ConfigLoadError):
            config.load_device_config("device123", "/nonexistent/device.json")


class TestGlobalConfigFunctions:
    """Tests for global configuration functions."""

    def test_init_config(self):
        # Reset global config
        import core.config_manager as cm

        cm._global_config = None

        config = init_config(validate=False)
        assert config is not None
        assert isinstance(config, ConfigManager)

    def test_get_config_initializes_if_needed(self):
        import core.config_manager as cm

        cm._global_config = None

        config = get_config()
        assert config is not None
        assert isinstance(config, ConfigManager)

    def test_get_config_value(self):
        import core.config_manager as cm

        cm._global_config = None

        value = get_config_value("logging.level", "DEFAULT")
        assert value == "INFO"  # Default from DEFAULT_CONFIG

    def test_get_config_value_with_default(self):
        value = get_config_value("nonexistent.key", "default_value")
        assert value == "default_value"


class TestDefaultConfig:
    """Tests for DEFAULT_CONFIG structure."""

    def test_default_config_has_required_sections(self):
        required_sections = [
            "logging",
            "adb",
            "recording",
            "replay",
            "nl_runner",
            "gestures",
            "ui_capture",
            "device",
            "ad_filter",
            "emulator",
            "cloud",
        ]
        for section in required_sections:
            assert section in DEFAULT_CONFIG

    def test_default_config_logging_values(self):
        assert DEFAULT_CONFIG["logging"]["level"] == "INFO"
        assert DEFAULT_CONFIG["logging"]["log_to_file"] is True
        assert DEFAULT_CONFIG["logging"]["log_to_console"] is True

    def test_default_config_adb_values(self):
        assert DEFAULT_CONFIG["adb"]["timeout"] == 30
        assert DEFAULT_CONFIG["adb"]["retry_count"] == 3
