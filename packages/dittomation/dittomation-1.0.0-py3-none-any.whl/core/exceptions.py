"""
Custom exception classes for DittoMation.

This module provides a hierarchy of exceptions for different error types,
enabling better error handling and user-friendly error messages.
"""

from typing import Any, Dict, List, Optional


class DittoMationError(Exception):
    """Base exception for all DittoMation errors."""

    def __init__(
        self, message: str, details: Optional[Dict[str, Any]] = None, hint: Optional[str] = None
    ):
        """
        Initialize the exception.

        Args:
            message: The error message.
            details: Optional dictionary with additional error details.
            hint: Optional troubleshooting hint for the user.
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.hint = hint

    def __str__(self) -> str:
        result = self.message
        if self.hint:
            result += f"\nHint: {self.hint}"
        return result

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/serialization."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
            "hint": self.hint,
        }


# ============================================================================
# Device Errors
# ============================================================================


class DeviceError(DittoMationError):
    """Base exception for device-related errors."""

    pass


class DeviceNotFoundError(DeviceError):
    """Raised when no Android device is connected or detected."""

    def __init__(
        self, message: str = "No Android device found", details: Optional[Dict[str, Any]] = None
    ):
        hint = (
            "Make sure your device is connected via USB and USB debugging is enabled. "
            "Run 'adb devices' to check connected devices."
        )
        super().__init__(message, details, hint)


class DeviceConnectionError(DeviceError):
    """Raised when connection to the device fails."""

    def __init__(
        self,
        message: str = "Failed to connect to device",
        device_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        hint = (
            "Try disconnecting and reconnecting the USB cable. "
            "You may also try 'adb kill-server' followed by 'adb start-server'."
        )
        details = details or {}
        if device_id:
            details["device_id"] = device_id
        super().__init__(message, details, hint)


class DeviceOfflineError(DeviceError):
    """Raised when device is detected but offline."""

    def __init__(self, device_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"Device '{device_id}' is offline"
        hint = (
            "The device may need to be authorized. Check the device screen "
            "for an authorization dialog and tap 'Allow'."
        )
        details = details or {}
        details["device_id"] = device_id
        super().__init__(message, details, hint)


class DeviceUnauthorizedError(DeviceError):
    """Raised when device is not authorized for debugging."""

    def __init__(self, device_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"Device '{device_id}' is not authorized"
        hint = (
            "Check the device screen for an authorization dialog. "
            "Tap 'Allow' to authorize this computer for USB debugging."
        )
        details = details or {}
        details["device_id"] = device_id
        super().__init__(message, details, hint)


# ============================================================================
# ADB Errors
# ============================================================================


class ADBError(DittoMationError):
    """Base exception for ADB-related errors."""

    pass


class ADBNotFoundError(ADBError):
    """Raised when ADB executable cannot be found."""

    def __init__(self, searched_paths: Optional[List[str]] = None):
        message = "ADB executable not found"
        hint = (
            "Install Android SDK Platform Tools and ensure ADB is in your PATH, "
            "or set ANDROID_HOME environment variable to your SDK location."
        )
        details = {}
        if searched_paths:
            details["searched_paths"] = searched_paths
        super().__init__(message, details, hint)


class ADBCommandError(ADBError):
    """Raised when an ADB command fails."""

    def __init__(
        self,
        command: str,
        returncode: int,
        stdout: str = "",
        stderr: str = "",
        details: Optional[Dict[str, Any]] = None,
    ):
        message = f"ADB command failed with exit code {returncode}"
        details = details or {}
        details.update(
            {
                "command": command,
                "returncode": returncode,
                "stdout": stdout[:500] if stdout else "",
                "stderr": stderr[:500] if stderr else "",
            }
        )
        hint = None
        if "device not found" in stderr.lower():
            hint = "No device connected. Check USB connection and USB debugging settings."
        elif "permission denied" in stderr.lower():
            hint = "Permission denied. The device may need to be rooted for this operation."
        super().__init__(message, details, hint)


class ADBTimeoutError(ADBError):
    """Raised when an ADB command times out."""

    def __init__(self, command: str, timeout: int, details: Optional[Dict[str, Any]] = None):
        message = f"ADB command timed out after {timeout} seconds"
        details = details or {}
        details.update({"command": command, "timeout": timeout})
        hint = (
            "The command took too long to complete. The device may be unresponsive "
            "or the operation may require more time. Try increasing the timeout."
        )
        super().__init__(message, details, hint)


# ============================================================================
# UI Errors
# ============================================================================


class UIError(DittoMationError):
    """Base exception for UI-related errors."""

    pass


class UIHierarchyError(UIError):
    """Raised when UI hierarchy cannot be captured or parsed."""

    def __init__(
        self,
        message: str = "Failed to capture UI hierarchy",
        details: Optional[Dict[str, Any]] = None,
    ):
        hint = (
            "The UI hierarchy dump may have failed. Wait for the screen to stabilize "
            "and try again. Some screens (like video players) may not dump properly."
        )
        super().__init__(message, details, hint)


class ElementNotFoundError(UIError):
    """Raised when a UI element cannot be found."""

    def __init__(
        self, locator: str, strategy: Optional[str] = None, details: Optional[Dict[str, Any]] = None
    ):
        message = f"Element not found: {locator}"
        details = details or {}
        details["locator"] = locator
        if strategy:
            details["strategy"] = strategy
        hint = (
            "The element may have changed or may not be visible. "
            "Try waiting for the screen to load, or update the locator."
        )
        super().__init__(message, details, hint)


class MultipleElementsFoundError(UIError):
    """Raised when multiple elements match when only one was expected."""

    def __init__(self, locator: str, count: int, details: Optional[Dict[str, Any]] = None):
        message = f"Multiple elements ({count}) found for locator: {locator}"
        details = details or {}
        details.update({"locator": locator, "count": count})
        hint = (
            "Make the locator more specific to match only one element. "
            "Consider using a more unique attribute like resource-id."
        )
        super().__init__(message, details, hint)


class InvalidBoundsError(UIError):
    """Raised when element bounds are invalid."""

    def __init__(
        self,
        bounds: str,
        element_info: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        message = f"Invalid element bounds: {bounds}"
        details = details or {}
        details["bounds"] = bounds
        if element_info:
            details["element"] = element_info
        hint = "The element may be off-screen or have zero dimensions."
        super().__init__(message, details, hint)


# ============================================================================
# Workflow Errors
# ============================================================================


class WorkflowError(DittoMationError):
    """Base exception for workflow-related errors."""

    pass


class WorkflowLoadError(WorkflowError):
    """Raised when a workflow file cannot be loaded."""

    def __init__(
        self, filepath: str, reason: Optional[str] = None, details: Optional[Dict[str, Any]] = None
    ):
        message = f"Failed to load workflow: {filepath}"
        if reason:
            message += f" ({reason})"
        details = details or {}
        details["filepath"] = filepath
        hint = (
            "Check that the file exists and contains valid JSON. "
            "The workflow may have been created with an incompatible version."
        )
        super().__init__(message, details, hint)


class WorkflowSaveError(WorkflowError):
    """Raised when a workflow cannot be saved."""

    def __init__(
        self, filepath: str, reason: Optional[str] = None, details: Optional[Dict[str, Any]] = None
    ):
        message = f"Failed to save workflow: {filepath}"
        if reason:
            message += f" ({reason})"
        details = details or {}
        details["filepath"] = filepath
        hint = "Check that you have write permissions to the directory."
        super().__init__(message, details, hint)


class WorkflowValidationError(WorkflowError):
    """Raised when a workflow fails validation."""

    def __init__(self, errors: List[str], details: Optional[Dict[str, Any]] = None):
        message = f"Workflow validation failed with {len(errors)} error(s)"
        details = details or {}
        details["validation_errors"] = errors
        hint = "Review the workflow file and fix the reported errors."
        super().__init__(message, details, hint)


class StepExecutionError(WorkflowError):
    """Raised when a workflow step fails to execute."""

    def __init__(
        self, step_id: int, action: str, reason: str, details: Optional[Dict[str, Any]] = None
    ):
        message = f"Step {step_id} ({action}) failed: {reason}"
        details = details or {}
        details.update({"step_id": step_id, "action": action})
        super().__init__(message, details)


# ============================================================================
# Gesture Errors
# ============================================================================


class GestureError(DittoMationError):
    """Base exception for gesture-related errors."""

    pass


class InvalidGestureError(GestureError):
    """Raised when a gesture is invalid or cannot be performed."""

    def __init__(self, gesture_type: str, reason: str, details: Optional[Dict[str, Any]] = None):
        message = f"Invalid gesture '{gesture_type}': {reason}"
        details = details or {}
        details["gesture_type"] = gesture_type
        super().__init__(message, details)


class GestureExecutionError(GestureError):
    """Raised when a gesture fails to execute."""

    def __init__(
        self,
        gesture_type: str,
        coordinates: tuple,
        reason: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        message = f"Failed to execute {gesture_type} at {coordinates}"
        if reason:
            message += f": {reason}"
        details = details or {}
        details.update({"gesture_type": gesture_type, "coordinates": coordinates})
        hint = (
            "The gesture may have failed due to the screen changing during execution. "
            "Try adding a wait before the gesture."
        )
        super().__init__(message, details, hint)


# ============================================================================
# Input Errors
# ============================================================================


class InputError(DittoMationError):
    """Base exception for input-related errors."""

    pass


class InvalidInputDeviceError(InputError):
    """Raised when the touch input device cannot be found."""

    def __init__(self, details: Optional[Dict[str, Any]] = None):
        message = "Touch input device not found"
        hint = (
            "The device may not have a touch screen or the input device "
            "path may have changed. Check 'getevent -p' for available devices."
        )
        super().__init__(message, details, hint)


class EventParseError(InputError):
    """Raised when an input event cannot be parsed."""

    def __init__(
        self,
        event_line: str,
        reason: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        message = "Failed to parse input event"
        if reason:
            message += f": {reason}"
        details = details or {}
        details["event_line"] = event_line[:100]
        super().__init__(message, details)


# ============================================================================
# Configuration Errors
# ============================================================================


class ConfigurationError(DittoMationError):
    """Base exception for configuration-related errors."""

    pass


class ConfigLoadError(ConfigurationError):
    """Raised when configuration cannot be loaded."""

    def __init__(
        self, filepath: str, reason: Optional[str] = None, details: Optional[Dict[str, Any]] = None
    ):
        message = f"Failed to load configuration: {filepath}"
        if reason:
            message += f" ({reason})"
        details = details or {}
        details["filepath"] = filepath
        hint = "Check that the configuration file exists and is valid YAML/JSON."
        super().__init__(message, details, hint)


class ConfigValidationError(ConfigurationError):
    """Raised when configuration fails validation."""

    def __init__(self, errors: List[str], details: Optional[Dict[str, Any]] = None):
        message = f"Configuration validation failed with {len(errors)} error(s)"
        details = details or {}
        details["validation_errors"] = errors
        hint = "Review the configuration file and fix the reported errors."
        super().__init__(message, details, hint)


class InvalidConfigValueError(ConfigurationError):
    """Raised when a configuration value is invalid."""

    def __init__(
        self, key: str, value: Any, expected: str, details: Optional[Dict[str, Any]] = None
    ):
        message = f"Invalid configuration value for '{key}': {value} (expected {expected})"
        details = details or {}
        details.update({"key": key, "value": value, "expected": expected})
        super().__init__(message, details)


# ============================================================================
# Natural Language Errors
# ============================================================================


class NaturalLanguageError(DittoMationError):
    """Base exception for natural language processing errors."""

    pass


class CommandParseError(NaturalLanguageError):
    """Raised when a natural language command cannot be parsed."""

    def __init__(
        self, command: str, reason: Optional[str] = None, details: Optional[Dict[str, Any]] = None
    ):
        message = f"Failed to parse command: '{command}'"
        if reason:
            message += f" ({reason})"
        details = details or {}
        details["command"] = command
        hint = (
            "Try rephrasing the command using simpler language. "
            "Example commands: 'tap Settings', 'scroll down', 'type hello world'"
        )
        super().__init__(message, details, hint)


class UnknownActionError(NaturalLanguageError):
    """Raised when a natural language action is not recognized."""

    def __init__(
        self,
        action: str,
        similar_actions: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        message = f"Unknown action: '{action}'"
        details = details or {}
        details["action"] = action
        if similar_actions:
            details["similar_actions"] = similar_actions
            hint = f"Did you mean: {', '.join(similar_actions)}?"
        else:
            hint = (
                "Supported actions include: tap, click, swipe, scroll, type, "
                "long press, back, home, search, open"
            )
        super().__init__(message, details, hint)


# ============================================================================
# Expression & Variable Errors
# ============================================================================


class ExpressionError(DittoMationError):
    """Base exception for expression evaluation errors."""

    def __init__(
        self,
        expression: str,
        reason: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        message = f"Expression evaluation failed: {expression}"
        if reason:
            message += f" ({reason})"
        details = details or {}
        details["expression"] = expression
        hint = (
            "Check the expression syntax. Supported: comparisons (==, !=, <, >), "
            "boolean (and, or, not), arithmetic (+, -, *, /), and functions (len, str, int)."
        )
        super().__init__(message, details, hint)


class UnsafeExpressionError(ExpressionError):
    """Raised when expression contains unsafe operations."""

    def __init__(self, reason: str, expression: str = "", details: Optional[Dict[str, Any]] = None):
        message = f"Unsafe expression blocked: {reason}"
        details = details or {}
        details["reason"] = reason
        if expression:
            details["expression"] = expression
        hint = (
            "Expressions cannot use imports, exec, eval, or access private attributes. "
            "Only whitelisted functions and operations are allowed."
        )
        # Call DittoMationError.__init__ directly to avoid ExpressionError's signature
        DittoMationError.__init__(self, message, details, hint)


class VariableNotFoundError(DittoMationError):
    """Raised when a referenced variable doesn't exist."""

    def __init__(
        self,
        variable: str,
        available: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        message = f"Variable not found: '{variable}'"
        details = details or {}
        details["variable"] = variable
        if available:
            details["available_variables"] = available[:10]  # Limit to first 10
            hint = f"Available variables: {', '.join(available[:5])}"
            if len(available) > 5:
                hint += f" (and {len(available) - 5} more)"
        else:
            hint = (
                "Make sure the variable is defined before use. "
                "Use set_variable action or pass via --var CLI option."
            )
        super().__init__(message, details, hint)


# ============================================================================
# Control Flow Errors
# ============================================================================


class ControlFlowError(DittoMationError):
    """Base exception for control flow errors."""

    pass


class LoopLimitError(ControlFlowError):
    """Raised when a loop exceeds its maximum iterations."""

    def __init__(
        self,
        loop_type: str,
        max_iterations: int,
        condition: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        message = f"{loop_type} loop exceeded maximum iterations ({max_iterations})"
        details = details or {}
        details.update({"loop_type": loop_type, "max_iterations": max_iterations})
        if condition:
            details["condition"] = condition
        hint = (
            "The loop ran too many times. Check your loop condition to ensure "
            "it will eventually terminate, or increase max_iterations if needed."
        )
        super().__init__(message, details, hint)


class BreakException(ControlFlowError):
    """Internal exception for break statement (not an error)."""

    def __init__(self):
        super().__init__("Break statement executed")


class ContinueException(ControlFlowError):
    """Internal exception for continue statement (not an error)."""

    def __init__(self):
        super().__init__("Continue statement executed")


class InvalidControlFlowError(ControlFlowError):
    """Raised when break/continue used outside of loop."""

    def __init__(self, statement: str, details: Optional[Dict[str, Any]] = None):
        message = f"'{statement}' statement outside of loop"
        details = details or {}
        details["statement"] = statement
        hint = f"The '{statement}' action can only be used inside for, while, or until loops."
        super().__init__(message, details, hint)


class AssertionFailedError(DittoMationError):
    """Raised when an assert action fails."""

    def __init__(
        self,
        condition: str,
        message_text: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        message = f"Assertion failed: {condition}"
        if message_text:
            message += f" - {message_text}"
        details = details or {}
        details["condition"] = condition
        hint = "The assert condition evaluated to False. Check your test conditions."
        super().__init__(message, details, hint)


# ============================================================================
# Emulator Errors
# ============================================================================


class EmulatorError(DittoMationError):
    """Base exception for emulator-related errors."""

    pass


class AVDNotFoundError(EmulatorError):
    """Raised when an AVD (Android Virtual Device) is not found."""

    def __init__(
        self,
        avd_name: str,
        available_avds: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        message = f"AVD not found: '{avd_name}'"
        details = details or {}
        details["avd_name"] = avd_name
        if available_avds:
            details["available_avds"] = available_avds
            hint = f"Available AVDs: {', '.join(available_avds)}"
        else:
            hint = (
                "Run 'emulator -list-avds' to see available AVDs. "
                "Create an AVD using Android Studio or 'avdmanager' command."
            )
        super().__init__(message, details, hint)


class EmulatorStartError(EmulatorError):
    """Raised when an emulator fails to start."""

    def __init__(
        self, avd_name: str, reason: Optional[str] = None, details: Optional[Dict[str, Any]] = None
    ):
        message = f"Failed to start emulator: '{avd_name}'"
        if reason:
            message += f" ({reason})"
        details = details or {}
        details["avd_name"] = avd_name
        hint = (
            "Check that the emulator is installed and the AVD is valid. "
            "Try running 'emulator -avd <name>' manually to see detailed errors."
        )
        super().__init__(message, details, hint)


class EmulatorBootTimeoutError(EmulatorError):
    """Raised when an emulator fails to boot within the timeout period."""

    def __init__(
        self,
        avd_name: str,
        timeout: int,
        serial: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        message = f"Emulator '{avd_name}' failed to boot within {timeout} seconds"
        details = details or {}
        details.update({"avd_name": avd_name, "timeout": timeout})
        if serial:
            details["serial"] = serial
        hint = (
            "The emulator may be too slow or encountered an error during boot. "
            "Try increasing the boot timeout or checking emulator logs."
        )
        super().__init__(message, details, hint)


class EmulatorNotRunningError(EmulatorError):
    """Raised when an operation requires a running emulator but none is found."""

    def __init__(self, serial: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        if serial:
            message = f"Emulator '{serial}' is not running"
        else:
            message = "No emulator is running"
        details = details or {}
        if serial:
            details["serial"] = serial
        hint = "Start an emulator using 'ditto emulator start <avd-name>'."
        super().__init__(message, details, hint)


# ============================================================================
# Cloud Provider Errors
# ============================================================================


class CloudProviderError(DittoMationError):
    """Base exception for cloud provider errors."""

    def __init__(
        self,
        provider: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        hint: Optional[str] = None,
    ):
        details = details or {}
        details["provider"] = provider
        super().__init__(f"[{provider}] {message}", details, hint)


class CloudAuthenticationError(CloudProviderError):
    """Raised when cloud provider authentication fails."""

    def __init__(
        self, provider: str, reason: Optional[str] = None, details: Optional[Dict[str, Any]] = None
    ):
        message = "Authentication failed"
        if reason:
            message += f": {reason}"
        if provider.lower() == "firebase":
            hint = (
                "Run 'gcloud auth login' and 'gcloud config set project <project-id>'. "
                "Ensure you have Firebase Test Lab permissions."
            )
        elif provider.lower() == "aws":
            hint = (
                "Configure AWS credentials using 'aws configure' or set "
                "AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables."
            )
        else:
            hint = "Check your cloud provider credentials and permissions."
        super().__init__(provider, message, details, hint)


class CloudDeviceNotAvailableError(CloudProviderError):
    """Raised when a requested cloud device is not available."""

    def __init__(
        self,
        provider: str,
        device_model: str,
        os_version: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        message = f"Device not available: {device_model}"
        if os_version:
            message += f" (OS {os_version})"
        details = details or {}
        details.update({"device_model": device_model, "os_version": os_version})
        hint = (
            f"The requested device may not exist or is currently unavailable. "
            f"Use 'ditto cloud list-devices --provider {provider}' to see available devices."
        )
        super().__init__(provider, message, details, hint)


class CloudTestRunError(CloudProviderError):
    """Raised when a cloud test run fails."""

    def __init__(
        self,
        provider: str,
        run_id: str,
        reason: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        message = f"Test run failed: {run_id}"
        if reason:
            message += f" ({reason})"
        details = details or {}
        details["run_id"] = run_id
        hint = (
            f"Check the test run status and logs using "
            f"'ditto cloud status {run_id} --provider {provider}'."
        )
        super().__init__(provider, message, details, hint)


class CloudQuotaExceededError(CloudProviderError):
    """Raised when cloud provider quota is exceeded."""

    def __init__(
        self,
        provider: str,
        quota_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        message = "Quota exceeded"
        if quota_type:
            message += f" ({quota_type})"
        details = details or {}
        if quota_type:
            details["quota_type"] = quota_type
        hint = (
            "You have exceeded your cloud provider's usage quota. "
            "Wait for the quota to reset or upgrade your plan."
        )
        super().__init__(provider, message, details, hint)


class CloudTimeoutError(CloudProviderError):
    """Raised when a cloud operation times out."""

    def __init__(
        self, provider: str, operation: str, timeout: int, details: Optional[Dict[str, Any]] = None
    ):
        message = f"Operation timed out: {operation} (after {timeout}s)"
        details = details or {}
        details.update({"operation": operation, "timeout": timeout})
        hint = "The operation took too long. Try increasing the timeout or retry later."
        super().__init__(provider, message, details, hint)
