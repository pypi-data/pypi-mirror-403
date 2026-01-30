"""Tests for core.logging_config module."""

import json
import logging
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from core.exceptions import DittoMationError
from core.logging_config import (
    ContextAdapter,
    JsonFormatter,
    LoggerMixin,
    get_global_logger,
    get_log_level,
    get_logger,
    init_logging,
    log_exception,
    setup_logging,
    setup_nl_runner_logging,
    setup_recorder_logging,
    setup_replayer_logging,
)


class TestGetLogLevel:
    """Tests for get_log_level function."""

    def test_debug_level(self):
        assert get_log_level("DEBUG") == logging.DEBUG

    def test_info_level(self):
        assert get_log_level("INFO") == logging.INFO

    def test_warning_level(self):
        assert get_log_level("WARNING") == logging.WARNING

    def test_error_level(self):
        assert get_log_level("ERROR") == logging.ERROR

    def test_critical_level(self):
        assert get_log_level("CRITICAL") == logging.CRITICAL

    def test_case_insensitive(self):
        assert get_log_level("debug") == logging.DEBUG
        assert get_log_level("Info") == logging.INFO

    def test_invalid_level_returns_info(self):
        assert get_log_level("INVALID") == logging.INFO


class TestJsonFormatter:
    """Tests for JsonFormatter class."""

    def test_format_basic_record(self):
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert data["level"] == "INFO"
        assert data["logger"] == "test"
        assert data["message"] == "Test message"
        assert data["line"] == 10

    def test_format_with_extra_data(self):
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.extra_data = {"key": "value"}

        output = formatter.format(record)
        data = json.loads(output)

        assert data["extra"] == {"key": "value"}

    def test_format_with_exception(self):
        formatter = JsonFormatter()
        try:
            raise ValueError("Test exception")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert "exception" in data
        assert "ValueError" in data["exception"]


class TestContextAdapter:
    """Tests for ContextAdapter class."""

    def test_process_adds_extra(self):
        logger = logging.getLogger("test_context")
        adapter = ContextAdapter(logger, {"context_key": "context_value"})

        msg, kwargs = adapter.process("Test message", {})

        assert kwargs["extra"]["context_key"] == "context_value"

    def test_process_merges_extra(self):
        logger = logging.getLogger("test_context2")
        adapter = ContextAdapter(logger, {"key1": "value1"})

        msg, kwargs = adapter.process("Test", {"extra": {"key2": "value2"}})

        assert kwargs["extra"]["key1"] == "value1"
        assert kwargs["extra"]["key2"] == "value2"


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_with_defaults(self):
        logger = setup_logging()
        assert logger.name == "dittoMation"
        assert logger.level == logging.INFO

    def test_setup_with_debug_level(self):
        logger = setup_logging(level="DEBUG")
        assert logger.level == logging.DEBUG

    def test_setup_with_component(self):
        logger = setup_logging(component="recorder")
        assert logger.name == "dittoMation.recorder"

    def test_setup_console_only(self):
        logger = setup_logging(log_to_file=False, log_to_console=True)
        # Should have at least one handler (console)
        assert len(logger.handlers) >= 1

    def test_setup_with_json_format(self):
        logger = setup_logging(json_format=True, log_to_console=True, log_to_file=False)
        # Check that handler has JsonFormatter
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                assert isinstance(handler.formatter, JsonFormatter)

    def test_setup_file_logging(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            logger = setup_logging(
                log_to_file=True, log_to_console=False, log_dir=log_dir, component="test"
            )

            # Log something
            logger.info("Test log message")

            # Check file was created
            log_file = log_dir / "test.log"
            assert log_file.exists()

            # Close handlers to release file lock (required on Windows)
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger(self):
        logger = get_logger("my_component")
        assert logger.name == "dittoMation.my_component"

    def test_get_logger_returns_logger_instance(self):
        logger = get_logger("test")
        assert isinstance(logger, logging.Logger)


class TestLogException:
    """Tests for log_exception function."""

    def test_log_dittomation_error(self):
        logger = MagicMock(spec=logging.Logger)
        err = DittoMationError("Test error", details={"key": "value"})

        log_exception(logger, err, context={"step": 1})

        logger.error.assert_called_once()
        call_args = logger.error.call_args
        assert "DittoMationError" in call_args[0][0]

    def test_log_standard_exception(self):
        logger = MagicMock(spec=logging.Logger)
        err = ValueError("Standard error")

        log_exception(logger, err)

        logger.error.assert_called_once()
        call_args = logger.error.call_args
        assert "ValueError" in call_args[0][0]


class TestLoggerMixin:
    """Tests for LoggerMixin class."""

    def test_mixin_provides_logger(self):
        class MyClass(LoggerMixin):
            pass

        obj = MyClass()
        assert hasattr(obj, "logger")
        assert isinstance(obj.logger, logging.Logger)
        assert "MyClass" in obj.logger.name

    def test_logger_is_cached(self):
        class MyClass(LoggerMixin):
            pass

        obj = MyClass()
        logger1 = obj.logger
        logger2 = obj.logger
        assert logger1 is logger2


class TestConvenienceFunctions:
    """Tests for convenience logging functions."""

    def test_setup_recorder_logging(self):
        logger = setup_recorder_logging(log_to_file=False)
        assert "recorder" in logger.name

    def test_setup_replayer_logging(self):
        logger = setup_replayer_logging(log_to_file=False)
        assert "replayer" in logger.name

    def test_setup_nl_runner_logging(self):
        logger = setup_nl_runner_logging(log_to_file=False)
        assert "nl_runner" in logger.name


class TestGlobalLogger:
    """Tests for global logger functions."""

    def test_init_logging(self):
        logger = init_logging(level="WARNING", log_to_file=False)
        assert logger.level == logging.WARNING

    def test_get_global_logger_initializes_if_needed(self):
        # Reset global logger
        import core.logging_config as lc

        lc._global_logger = None

        logger = get_global_logger()
        assert logger is not None
        assert isinstance(logger, logging.Logger)

    def test_get_global_logger_returns_same_instance(self):
        logger1 = get_global_logger()
        logger2 = get_global_logger()
        # After first call, should return the same logger
        assert logger1.name == logger2.name
