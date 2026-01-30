"""
DittoMation Core Module.

This module provides core functionality shared across all components:
- Custom exceptions
- Logging configuration
- Configuration management
- Android control API

Usage:
    from core import Android

    android = Android()
    android.tap(100, 200)
    android.tap("Login")
    android.open_app("Chrome")
"""

__version__ = "1.0.0"

# These imports don't cause circular dependencies
from .ad_filter import (
    AdFilter,
    add_custom_ad_pattern,
    clear_custom_patterns,
    filter_ad_elements,
    find_non_ad_alternative,
    get_ad_filter,
    get_non_ad_elements_at_point,
    is_ad_element,
    is_sponsored_content,
    load_custom_patterns_from_config,
)
from .config_manager import (
    DEFAULT_CONFIG,
    ConfigManager,
    get_config,
    get_config_value,
    init_config,
)
from .exceptions import (
    ADBCommandError,
    # ADB errors
    ADBError,
    ADBNotFoundError,
    ADBTimeoutError,
    CommandParseError,
    ConfigLoadError,
    # Configuration errors
    ConfigurationError,
    ConfigValidationError,
    DeviceConnectionError,
    # Device errors
    DeviceError,
    DeviceNotFoundError,
    DeviceOfflineError,
    DeviceUnauthorizedError,
    # Base
    DittoMationError,
    ElementNotFoundError,
    EventParseError,
    # Gesture errors
    GestureError,
    GestureExecutionError,
    # Input errors
    InputError,
    InvalidBoundsError,
    InvalidConfigValueError,
    InvalidGestureError,
    InvalidInputDeviceError,
    MultipleElementsFoundError,
    # Natural language errors
    NaturalLanguageError,
    StepExecutionError,
    # UI errors
    UIError,
    UIHierarchyError,
    UnknownActionError,
    # Workflow errors
    WorkflowError,
    WorkflowLoadError,
    WorkflowSaveError,
    WorkflowValidationError,
)
from .logging_config import (
    LoggerMixin,
    get_global_logger,
    get_logger,
    init_logging,
    log_exception,
    setup_logging,
    setup_nl_runner_logging,
    setup_recorder_logging,
    setup_replayer_logging,
)

__all__ = [
    # Version
    "__version__",
    # Android API (lazy loaded)
    "Android",
    # Automation (lazy loaded)
    "Automation",
    "Step",
    "StepResult",
    "AutomationResult",
    "StepType",
    "StepStatus",
    "run_steps",
    "tap",
    "wait",
    "wait_for",
    "type_text",
    "swipe",
    "open_app",
    "press",
    # Exceptions
    "DittoMationError",
    "DeviceError",
    "DeviceNotFoundError",
    "DeviceConnectionError",
    "DeviceOfflineError",
    "DeviceUnauthorizedError",
    "ADBError",
    "ADBNotFoundError",
    "ADBCommandError",
    "ADBTimeoutError",
    "UIError",
    "UIHierarchyError",
    "ElementNotFoundError",
    "MultipleElementsFoundError",
    "InvalidBoundsError",
    "WorkflowError",
    "WorkflowLoadError",
    "WorkflowSaveError",
    "WorkflowValidationError",
    "StepExecutionError",
    "GestureError",
    "InvalidGestureError",
    "GestureExecutionError",
    "InputError",
    "InvalidInputDeviceError",
    "EventParseError",
    "ConfigurationError",
    "ConfigLoadError",
    "ConfigValidationError",
    "InvalidConfigValueError",
    "NaturalLanguageError",
    "CommandParseError",
    "UnknownActionError",
    # Logging
    "setup_logging",
    "get_logger",
    "log_exception",
    "LoggerMixin",
    "setup_recorder_logging",
    "setup_replayer_logging",
    "setup_nl_runner_logging",
    "init_logging",
    "get_global_logger",
    # Configuration
    "ConfigManager",
    "init_config",
    "get_config",
    "get_config_value",
    "DEFAULT_CONFIG",
    # Ad Filter
    "is_ad_element",
    "is_sponsored_content",
    "filter_ad_elements",
    "get_non_ad_elements_at_point",
    "find_non_ad_alternative",
    "add_custom_ad_pattern",
    "clear_custom_patterns",
    "load_custom_patterns_from_config",
    "AdFilter",
    "get_ad_filter",
]


def __getattr__(name):
    """Lazy import of modules that have circular dependencies with recorder."""
    # Android module depends on recorder.element_matcher
    if name == "Android":
        from .android import Android

        return Android

    # Automation module depends on recorder indirectly
    if name in (
        "Automation",
        "Step",
        "StepResult",
        "AutomationResult",
        "StepType",
        "StepStatus",
        "run_steps",
        "tap",
        "wait",
        "wait_for",
        "type_text",
        "swipe",
        "open_app",
        "press",
    ):
        from .automation import (
            Automation,
            AutomationResult,
            Step,
            StepResult,
            StepStatus,
            StepType,
            open_app,
            press,
            run_steps,
            swipe,
            tap,
            type_text,
            wait,
            wait_for,
        )

        return {
            "Automation": Automation,
            "Step": Step,
            "StepResult": StepResult,
            "AutomationResult": AutomationResult,
            "StepType": StepType,
            "StepStatus": StepStatus,
            "run_steps": run_steps,
            "tap": tap,
            "wait": wait,
            "wait_for": wait_for,
            "type_text": type_text,
            "swipe": swipe,
            "open_app": open_app,
            "press": press,
        }[name]

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
