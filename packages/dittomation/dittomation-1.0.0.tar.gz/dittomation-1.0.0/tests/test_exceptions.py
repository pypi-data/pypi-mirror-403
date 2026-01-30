"""Tests for core.exceptions module."""

from core.exceptions import (
    ADBCommandError,
    ADBError,
    ADBNotFoundError,
    ADBTimeoutError,
    AssertionFailedError,
    AVDNotFoundError,
    BreakException,
    CloudAuthenticationError,
    CloudDeviceNotAvailableError,
    CloudProviderError,
    CloudQuotaExceededError,
    CloudTestRunError,
    CloudTimeoutError,
    CommandParseError,
    ConfigLoadError,
    ConfigValidationError,
    ContinueException,
    DeviceConnectionError,
    DeviceError,
    DeviceNotFoundError,
    DeviceOfflineError,
    DeviceUnauthorizedError,
    DittoMationError,
    ElementNotFoundError,
    EmulatorBootTimeoutError,
    EmulatorNotRunningError,
    EmulatorStartError,
    EventParseError,
    ExpressionError,
    GestureExecutionError,
    InvalidBoundsError,
    InvalidConfigValueError,
    InvalidControlFlowError,
    InvalidGestureError,
    InvalidInputDeviceError,
    LoopLimitError,
    MultipleElementsFoundError,
    StepExecutionError,
    UIError,
    UIHierarchyError,
    UnknownActionError,
    UnsafeExpressionError,
    VariableNotFoundError,
    WorkflowLoadError,
    WorkflowSaveError,
    WorkflowValidationError,
)


class TestDittoMationError:
    """Tests for base DittoMationError class."""

    def test_basic_init(self):
        err = DittoMationError("Test error")
        assert err.message == "Test error"
        assert err.details == {}
        assert err.hint is None

    def test_init_with_details(self):
        err = DittoMationError("Error", details={"key": "value"})
        assert err.details == {"key": "value"}

    def test_init_with_hint(self):
        err = DittoMationError("Error", hint="Try this")
        assert err.hint == "Try this"

    def test_str_without_hint(self):
        err = DittoMationError("Test error")
        assert str(err) == "Test error"

    def test_str_with_hint(self):
        err = DittoMationError("Test error", hint="Try this")
        assert "Test error" in str(err)
        assert "Hint: Try this" in str(err)

    def test_to_dict(self):
        err = DittoMationError("Error", details={"foo": "bar"}, hint="Help")
        d = err.to_dict()
        assert d["error_type"] == "DittoMationError"
        assert d["message"] == "Error"
        assert d["details"] == {"foo": "bar"}
        assert d["hint"] == "Help"


class TestDeviceErrors:
    """Tests for device-related exceptions."""

    def test_device_error_inheritance(self):
        err = DeviceError("Device error")
        assert isinstance(err, DittoMationError)

    def test_device_not_found_error(self):
        err = DeviceNotFoundError()
        assert "No Android device found" in err.message
        assert err.hint is not None
        assert "adb devices" in err.hint

    def test_device_not_found_error_custom_message(self):
        err = DeviceNotFoundError("Custom message")
        assert err.message == "Custom message"

    def test_device_connection_error(self):
        err = DeviceConnectionError(device_id="abc123")
        assert "abc123" in err.details.get("device_id", "")

    def test_device_offline_error(self):
        err = DeviceOfflineError("emulator-5554")
        assert "emulator-5554" in err.message
        assert err.details["device_id"] == "emulator-5554"

    def test_device_unauthorized_error(self):
        err = DeviceUnauthorizedError("device123")
        assert "device123" in err.message
        assert "authorization" in err.hint.lower()


class TestADBErrors:
    """Tests for ADB-related exceptions."""

    def test_adb_error_inheritance(self):
        err = ADBError("ADB error")
        assert isinstance(err, DittoMationError)

    def test_adb_not_found_error(self):
        err = ADBNotFoundError(searched_paths=["/usr/bin", "/opt/android"])
        assert "ADB executable not found" in err.message
        assert err.details["searched_paths"] == ["/usr/bin", "/opt/android"]

    def test_adb_command_error(self):
        err = ADBCommandError(
            command="adb shell ls", returncode=1, stdout="output", stderr="device not found"
        )
        assert "exit code 1" in err.message
        assert err.details["command"] == "adb shell ls"
        assert "device" in err.hint.lower()

    def test_adb_command_error_permission_denied(self):
        err = ADBCommandError(command="adb root", returncode=1, stderr="permission denied")
        assert "permission" in err.hint.lower()

    def test_adb_timeout_error(self):
        err = ADBTimeoutError(command="adb shell dumpsys", timeout=30)
        assert "30 seconds" in err.message
        assert err.details["timeout"] == 30


class TestUIErrors:
    """Tests for UI-related exceptions."""

    def test_ui_error_inheritance(self):
        err = UIError("UI error")
        assert isinstance(err, DittoMationError)

    def test_ui_hierarchy_error(self):
        err = UIHierarchyError()
        assert "UI hierarchy" in err.message

    def test_element_not_found_error(self):
        err = ElementNotFoundError("Login", strategy="text")
        assert "Login" in err.message
        assert err.details["locator"] == "Login"
        assert err.details["strategy"] == "text"

    def test_multiple_elements_found_error(self):
        err = MultipleElementsFoundError("Button", count=5)
        assert "5" in err.message
        assert "Button" in err.message
        assert err.details["count"] == 5

    def test_invalid_bounds_error(self):
        err = InvalidBoundsError("[0,0][0,0]", element_info="TextView")
        assert "[0,0][0,0]" in err.message
        assert err.details["element"] == "TextView"


class TestWorkflowErrors:
    """Tests for workflow-related exceptions."""

    def test_workflow_load_error(self):
        err = WorkflowLoadError("/path/to/file.json", reason="File not found")
        assert "/path/to/file.json" in err.message
        assert "File not found" in err.message

    def test_workflow_save_error(self):
        err = WorkflowSaveError("/path/to/file.json", reason="Permission denied")
        assert "/path/to/file.json" in err.message

    def test_workflow_validation_error(self):
        err = WorkflowValidationError(["Error 1", "Error 2"])
        assert "2 error" in err.message
        assert err.details["validation_errors"] == ["Error 1", "Error 2"]

    def test_step_execution_error(self):
        err = StepExecutionError(step_id=5, action="tap", reason="Element not found")
        assert "Step 5" in err.message
        assert "tap" in err.message


class TestGestureErrors:
    """Tests for gesture-related exceptions."""

    def test_invalid_gesture_error(self):
        err = InvalidGestureError("pinch", "Requires two touch points")
        assert "pinch" in err.message
        assert "two touch points" in err.message

    def test_gesture_execution_error(self):
        err = GestureExecutionError("tap", (100, 200), reason="Screen changed")
        assert "tap" in err.message
        assert "(100, 200)" in err.message


class TestInputErrors:
    """Tests for input-related exceptions."""

    def test_invalid_input_device_error(self):
        err = InvalidInputDeviceError()
        assert "Touch input device" in err.message

    def test_event_parse_error(self):
        err = EventParseError("invalid_event_line", reason="Unknown format")
        assert "parse" in err.message.lower()


class TestConfigurationErrors:
    """Tests for configuration-related exceptions."""

    def test_config_load_error(self):
        err = ConfigLoadError("/path/config.yaml", reason="Invalid syntax")
        assert "/path/config.yaml" in err.message
        assert "Invalid syntax" in err.message

    def test_config_validation_error(self):
        err = ConfigValidationError(["Invalid timeout value"])
        assert "1 error" in err.message

    def test_invalid_config_value_error(self):
        err = InvalidConfigValueError("timeout", -1, "positive integer")
        assert "timeout" in err.message
        assert "-1" in err.message


class TestNaturalLanguageErrors:
    """Tests for natural language processing exceptions."""

    def test_command_parse_error(self):
        err = CommandParseError("tap on the xyz", reason="Unknown element")
        assert "tap on the xyz" in err.message

    def test_unknown_action_error(self):
        err = UnknownActionError("jump", similar_actions=["tap", "swipe"])
        assert "jump" in err.message
        assert "Did you mean" in err.hint

    def test_unknown_action_error_no_similar(self):
        err = UnknownActionError("xyz")
        assert "xyz" in err.message
        assert "Supported actions" in err.hint


class TestExpressionErrors:
    """Tests for expression-related exceptions."""

    def test_expression_error(self):
        err = ExpressionError("1 / 0", reason="Division by zero")
        assert "1 / 0" in err.message
        assert "Division by zero" in err.message

    def test_unsafe_expression_error(self):
        err = UnsafeExpressionError("Import blocked", expression="import os")
        assert "Import blocked" in err.message
        assert err.details["expression"] == "import os"

    def test_variable_not_found_error(self):
        err = VariableNotFoundError("username", available=["password", "email"])
        assert "username" in err.message
        assert "password" in err.hint


class TestControlFlowErrors:
    """Tests for control flow exceptions."""

    def test_loop_limit_error(self):
        err = LoopLimitError("while", max_iterations=100, condition="x < 10")
        assert "while" in err.message
        assert "100" in err.message

    def test_break_exception(self):
        err = BreakException()
        assert "Break" in err.message

    def test_continue_exception(self):
        err = ContinueException()
        assert "Continue" in err.message

    def test_invalid_control_flow_error(self):
        err = InvalidControlFlowError("break")
        assert "break" in err.message
        assert "outside" in err.message.lower()

    def test_assertion_failed_error(self):
        err = AssertionFailedError("x == 5", message_text="Expected x to be 5")
        assert "x == 5" in err.message
        assert "Expected x to be 5" in err.message


class TestEmulatorErrors:
    """Tests for emulator-related exceptions."""

    def test_avd_not_found_error(self):
        err = AVDNotFoundError("Pixel_4", available_avds=["Pixel_5", "Pixel_6"])
        assert "Pixel_4" in err.message
        assert "Pixel_5" in err.hint

    def test_emulator_start_error(self):
        err = EmulatorStartError("Pixel_4", reason="Insufficient memory")
        assert "Pixel_4" in err.message
        assert "Insufficient memory" in err.message

    def test_emulator_boot_timeout_error(self):
        err = EmulatorBootTimeoutError("Pixel_4", timeout=60, serial="emulator-5554")
        assert "Pixel_4" in err.message
        assert "60 seconds" in err.message

    def test_emulator_not_running_error(self):
        err = EmulatorNotRunningError(serial="emulator-5554")
        assert "emulator-5554" in err.message

    def test_emulator_not_running_error_no_serial(self):
        err = EmulatorNotRunningError()
        assert "No emulator" in err.message


class TestCloudProviderErrors:
    """Tests for cloud provider exceptions."""

    def test_cloud_provider_error(self):
        err = CloudProviderError("AWS", "Test failed")
        assert "[AWS]" in err.message
        assert "Test failed" in err.message

    def test_cloud_authentication_error_firebase(self):
        err = CloudAuthenticationError("firebase", reason="Invalid credentials")
        assert "firebase" in err.details["provider"]
        assert "gcloud" in err.hint

    def test_cloud_authentication_error_aws(self):
        err = CloudAuthenticationError("aws")
        assert "AWS" in err.hint

    def test_cloud_device_not_available_error(self):
        err = CloudDeviceNotAvailableError("AWS", "Pixel 4", os_version="11")
        assert "Pixel 4" in err.message
        assert "OS 11" in err.message

    def test_cloud_test_run_error(self):
        err = CloudTestRunError("firebase", "run-123", reason="Timeout")
        assert "run-123" in err.message

    def test_cloud_quota_exceeded_error(self):
        err = CloudQuotaExceededError("AWS", quota_type="device minutes")
        assert "device minutes" in err.message

    def test_cloud_timeout_error(self):
        err = CloudTimeoutError("firebase", "upload", timeout=300)
        assert "upload" in err.message
        assert "300" in err.message
