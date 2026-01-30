"""
Logging configuration for DittoMation.

This module provides a centralized logging framework with:
- Configurable log levels
- Console and file handlers
- Log rotation
- Structured JSON logging option
- Separate loggers for different components
"""

import json
import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Default log directory
DEFAULT_LOG_DIR = Path("logs")

# Default log format
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# JSON format for structured logging
JSON_FORMAT = True

# Log level mapping
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs log records as JSON."""

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string."""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data

        return json.dumps(log_data)


class ContextAdapter(logging.LoggerAdapter):
    """Logger adapter that adds context to log messages."""

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Process the logging message and keyword arguments."""
        extra = kwargs.get("extra", {})
        if self.extra:
            extra.update(self.extra)
        kwargs["extra"] = extra
        return msg, kwargs


def get_log_level(level: str) -> int:
    """
    Convert log level string to logging constant.

    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Logging level constant
    """
    return LOG_LEVELS.get(level.upper(), logging.INFO)


def setup_logging(
    level: str = "INFO",
    log_dir: Optional[Path] = None,
    log_to_file: bool = True,
    log_to_console: bool = True,
    json_format: bool = False,
    max_file_size_mb: int = 10,
    backup_count: int = 5,
    component: Optional[str] = None,
) -> logging.Logger:
    """
    Set up logging with the specified configuration.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (default: logs/)
        log_to_file: Enable file logging
        log_to_console: Enable console logging
        json_format: Use JSON format for logs
        max_file_size_mb: Maximum log file size in MB before rotation
        backup_count: Number of backup files to keep
        component: Component name for logger (e.g., 'recorder', 'replayer')

    Returns:
        Configured logger instance
    """
    log_dir = log_dir or DEFAULT_LOG_DIR
    log_level = get_log_level(level)

    # Create logger
    logger_name = f"dittoMation.{component}" if component else "dittoMation"
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatters
    if json_format:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(DEFAULT_FORMAT, DEFAULT_DATE_FORMAT)

    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler with rotation
    if log_to_file:
        log_dir.mkdir(parents=True, exist_ok=True)

        # Determine log filename
        if component:
            log_filename = log_dir / f"{component}.log"
        else:
            log_filename = log_dir / "dittoMation.log"

        file_handler = logging.handlers.RotatingFileHandler(
            log_filename,
            maxBytes=max_file_size_mb * 1024 * 1024,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name (will be prefixed with 'dittoMation.')

    Returns:
        Logger instance
    """
    return logging.getLogger(f"dittoMation.{name}")


def log_exception(
    logger: logging.Logger, exc: Exception, context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an exception with optional context.

    Args:
        logger: Logger instance
        exc: Exception to log
        context: Optional dictionary with additional context
    """
    from .exceptions import DittoMationError

    if isinstance(exc, DittoMationError):
        error_data = exc.to_dict()
        if context:
            error_data["context"] = context
        logger.error(
            f"{exc.__class__.__name__}: {exc.message}",
            extra={"extra_data": error_data},
            exc_info=True,
        )
    else:
        logger.error(
            f"{exc.__class__.__name__}: {str(exc)}",
            extra={"extra_data": context} if context else {},
            exc_info=True,
        )


class LoggerMixin:
    """Mixin class that provides logging capability to any class."""

    @property
    def logger(self) -> logging.Logger:
        """Get the logger for this class."""
        if not hasattr(self, "_logger"):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger


# ============================================================================
# Convenience functions for quick logging setup
# ============================================================================


def setup_recorder_logging(level: str = "INFO", **kwargs) -> logging.Logger:
    """Set up logging for the recorder component."""
    return setup_logging(level=level, component="recorder", **kwargs)


def setup_replayer_logging(level: str = "INFO", **kwargs) -> logging.Logger:
    """Set up logging for the replayer component."""
    return setup_logging(level=level, component="replayer", **kwargs)


def setup_nl_runner_logging(level: str = "INFO", **kwargs) -> logging.Logger:
    """Set up logging for the natural language runner component."""
    return setup_logging(level=level, component="nl_runner", **kwargs)


# ============================================================================
# Global logger instance (for simple use cases)
# ============================================================================

_global_logger: Optional[logging.Logger] = None


def init_logging(level: str = "INFO", **kwargs) -> logging.Logger:
    """
    Initialize the global logger.

    Args:
        level: Log level
        **kwargs: Additional arguments passed to setup_logging

    Returns:
        The global logger instance
    """
    global _global_logger
    _global_logger = setup_logging(level=level, **kwargs)
    return _global_logger


def get_global_logger() -> logging.Logger:
    """
    Get the global logger instance.

    Returns:
        The global logger (initializes with defaults if not set up)
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = setup_logging()
    return _global_logger
