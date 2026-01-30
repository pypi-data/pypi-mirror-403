"""Tests for recorder.workflow module."""

import os
import tempfile
from dataclasses import dataclass
from unittest.mock import patch

import pytest

from core.exceptions import WorkflowLoadError
from recorder.workflow import (
    WorkflowRecorder,
    WorkflowStep,
    format_step,
)


# Mock Gesture for testing
@dataclass
class MockGesture:
    type: str = "tap"

    def to_dict(self):
        return {
            "type": self.type,
            "start": [100, 200],
            "end": [100, 200],
            "duration_ms": 100,
        }


class TestWorkflowStep:
    """Tests for WorkflowStep class."""

    def test_create_step(self):
        step = WorkflowStep(
            step_id=1,
            action="tap",
            locator={"primary": {"strategy": "text", "value": "Login"}},
            gesture={"type": "tap", "start": [100, 200]},
        )
        assert step.step_id == 1
        assert step.action == "tap"
        assert step.locator["primary"]["value"] == "Login"

    def test_to_dict(self):
        step = WorkflowStep(
            step_id=1,
            action="tap",
            locator={"primary": {"strategy": "id", "value": "btn"}},
            gesture={"type": "tap"},
            element_snapshot={"text": "Button"},
            ui_xml_file="ui_001.xml",
            timestamp=1234567890.0,
        )
        d = step.to_dict()

        assert d["step_id"] == 1
        assert d["action"] == "tap"
        assert d["locator"]["primary"]["strategy"] == "id"
        assert d["element_snapshot"]["text"] == "Button"
        assert d["ui_xml_file"] == "ui_001.xml"
        assert d["timestamp"] == 1234567890.0

    def test_to_dict_without_optional_fields(self):
        step = WorkflowStep(
            step_id=1,
            action="tap",
            locator={},
            gesture={},
        )
        d = step.to_dict()

        assert "element_snapshot" not in d
        assert "ui_xml_file" not in d

    def test_from_dict(self):
        data = {
            "step_id": 5,
            "action": "swipe",
            "locator": {"primary": {"strategy": "text", "value": "Item"}},
            "gesture": {"type": "swipe", "direction": "down"},
            "element_snapshot": {"class": "TextView"},
            "ui_xml_file": "ui_005.xml",
            "timestamp": 9876543210.0,
        }
        step = WorkflowStep.from_dict(data)

        assert step.step_id == 5
        assert step.action == "swipe"
        assert step.gesture["direction"] == "down"
        assert step.element_snapshot["class"] == "TextView"
        assert step.timestamp == 9876543210.0


class TestWorkflowRecorder:
    """Tests for WorkflowRecorder class."""

    @patch("recorder.workflow.get_screen_size")
    @patch("recorder.workflow.get_current_app")
    @patch("recorder.workflow.get_device_serial")
    def test_init(self, mock_serial, mock_app, mock_screen):
        mock_screen.return_value = (1080, 1920)
        mock_app.return_value = ("com.test.app", "MainActivity")
        mock_serial.return_value = "device123"

        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = WorkflowRecorder(output_dir=tmpdir)

            assert recorder.metadata["screen_size"] == [1080, 1920]
            assert recorder.metadata["app_package"] == "com.test.app"
            assert recorder.metadata["device"] == "device123"
            assert recorder.steps == []

    @patch("recorder.workflow.get_screen_size")
    @patch("recorder.workflow.get_current_app")
    @patch("recorder.workflow.get_device_serial")
    def test_init_handles_errors(self, mock_serial, mock_app, mock_screen):
        mock_screen.side_effect = Exception("No device")
        mock_app.side_effect = Exception("No device")
        mock_serial.side_effect = Exception("No device")

        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = WorkflowRecorder(output_dir=tmpdir)
            assert recorder.metadata["device"] == "unknown"

    @patch("recorder.workflow.get_screen_size", return_value=(1080, 1920))
    @patch("recorder.workflow.get_current_app", return_value=("com.test", "Main"))
    @patch("recorder.workflow.get_device_serial", return_value="device")
    def test_add_step(self, *mocks):
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = WorkflowRecorder(output_dir=tmpdir)

            gesture = MockGesture(type="tap")
            element = {
                "class": "Button",
                "resource_id": "com.app:id/btn",
                "text": "Click",
                "bounds": (0, 0, 100, 50),
                "clickable": True,
            }
            locator = {"primary": {"strategy": "text", "value": "Click"}}

            step = recorder.add_step(gesture, element, locator)

            assert step.step_id == 1
            assert step.action == "tap"
            assert step.element_snapshot["text"] == "Click"
            assert len(recorder.steps) == 1

    @patch("recorder.workflow.get_screen_size", return_value=(1080, 1920))
    @patch("recorder.workflow.get_current_app", return_value=("com.test", "Main"))
    @patch("recorder.workflow.get_device_serial", return_value="device")
    def test_add_step_without_element(self, *mocks):
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = WorkflowRecorder(output_dir=tmpdir)

            gesture = MockGesture(type="swipe")
            locator = {"coordinates": [100, 200]}

            step = recorder.add_step(gesture, None, locator)

            assert step.element_snapshot is None

    @patch("recorder.workflow.get_screen_size", return_value=(1080, 1920))
    @patch("recorder.workflow.get_current_app", return_value=("com.test", "Main"))
    @patch("recorder.workflow.get_device_serial", return_value="device")
    def test_save_and_load(self, *mocks):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "workflow.json")

            # Create and save
            recorder = WorkflowRecorder(output_dir=tmpdir)
            gesture = MockGesture(type="tap")
            recorder.add_step(gesture, None, {"test": "locator"})
            recorder.save(filepath)

            assert os.path.exists(filepath)

            # Load
            loaded = WorkflowRecorder.load(filepath)
            assert len(loaded.steps) == 1
            assert loaded.steps[0].action == "tap"

    def test_load_file_not_found(self):
        with pytest.raises(WorkflowLoadError) as exc_info:
            WorkflowRecorder.load("/nonexistent/workflow.json")
        assert "not found" in str(exc_info.value).lower()

    def test_load_invalid_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{ invalid json }")
            filepath = f.name

        try:
            with pytest.raises(WorkflowLoadError) as exc_info:
                WorkflowRecorder.load(filepath)
            assert "Invalid JSON" in str(exc_info.value)
        finally:
            os.unlink(filepath)

    @patch("recorder.workflow.get_screen_size", return_value=(1080, 1920))
    @patch("recorder.workflow.get_current_app", return_value=("com.test", "Main"))
    @patch("recorder.workflow.get_device_serial", return_value="device")
    def test_len(self, *mocks):
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = WorkflowRecorder(output_dir=tmpdir)
            assert len(recorder) == 0

            recorder.add_step(MockGesture(), None, {})
            assert len(recorder) == 1

            recorder.add_step(MockGesture(), None, {})
            assert len(recorder) == 2

    @patch("recorder.workflow.get_screen_size", return_value=(1080, 1920))
    @patch("recorder.workflow.get_current_app", return_value=("com.test", "Main"))
    @patch("recorder.workflow.get_device_serial", return_value="device")
    def test_iter(self, *mocks):
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = WorkflowRecorder(output_dir=tmpdir)
            recorder.add_step(MockGesture(type="tap"), None, {})
            recorder.add_step(MockGesture(type="swipe"), None, {})

            steps = list(recorder)
            assert len(steps) == 2
            assert steps[0].action == "tap"
            assert steps[1].action == "swipe"

    @patch("recorder.workflow.get_screen_size", return_value=(1080, 1920))
    @patch("recorder.workflow.get_current_app", return_value=("com.test", "Main"))
    @patch("recorder.workflow.get_device_serial", return_value="device")
    def test_get_ui_snapshot_path(self, *mocks):
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = WorkflowRecorder(output_dir=tmpdir)
            path = recorder.get_ui_snapshot_path(5)
            assert "ui_005.xml" in path

    @patch("recorder.workflow.get_screen_size", return_value=(1080, 1920))
    @patch("recorder.workflow.get_current_app", return_value=("com.test", "Main"))
    @patch("recorder.workflow.get_device_serial", return_value="device")
    def test_summary(self, *mocks):
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = WorkflowRecorder(output_dir=tmpdir)
            recorder.add_step(MockGesture(type="tap"), None, {})
            recorder.add_step(MockGesture(type="tap"), None, {})
            recorder.add_step(MockGesture(type="swipe"), None, {})

            summary = recorder.summary()
            assert "Steps: 3" in summary
            assert "tap: 2" in summary
            assert "swipe: 1" in summary


class TestDeduplication:
    """Tests for workflow deduplication."""

    @patch("recorder.workflow.get_screen_size", return_value=(1080, 1920))
    @patch("recorder.workflow.get_current_app", return_value=("com.test", "Main"))
    @patch("recorder.workflow.get_device_serial", return_value="device")
    def test_deduplicate_removes_double_taps(self, *mocks):
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = WorkflowRecorder(output_dir=tmpdir)

            # Add two taps very close in time and position
            step1 = WorkflowStep(
                step_id=1,
                action="tap",
                locator={},
                gesture={"type": "tap", "start": [100, 200]},
                timestamp=1.0,
            )
            step2 = WorkflowStep(
                step_id=2,
                action="tap",
                locator={},
                gesture={"type": "tap", "start": [105, 205]},  # Within threshold
                timestamp=1.1,  # 100ms later
            )
            step3 = WorkflowStep(
                step_id=3,
                action="tap",
                locator={},
                gesture={"type": "tap", "start": [500, 500]},  # Different position
                timestamp=2.0,
            )

            recorder.steps = [step1, step2, step3]
            removed = recorder.deduplicate()

            assert removed == 1
            assert len(recorder.steps) == 2

    @patch("recorder.workflow.get_screen_size", return_value=(1080, 1920))
    @patch("recorder.workflow.get_current_app", return_value=("com.test", "Main"))
    @patch("recorder.workflow.get_device_serial", return_value="device")
    def test_deduplicate_keeps_swipes(self, *mocks):
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = WorkflowRecorder(output_dir=tmpdir)

            step1 = WorkflowStep(
                step_id=1,
                action="swipe",
                locator={},
                gesture={"type": "swipe", "start": [100, 200]},
                timestamp=1.0,
            )
            step2 = WorkflowStep(
                step_id=2,
                action="swipe",
                locator={},
                gesture={"type": "swipe", "start": [100, 200]},
                timestamp=1.1,
            )

            recorder.steps = [step1, step2]
            removed = recorder.deduplicate()

            # Swipes should not be deduplicated
            assert removed == 0
            assert len(recorder.steps) == 2

    @patch("recorder.workflow.get_screen_size", return_value=(1080, 1920))
    @patch("recorder.workflow.get_current_app", return_value=("com.test", "Main"))
    @patch("recorder.workflow.get_device_serial", return_value="device")
    def test_deduplicate_renumbers_steps(self, *mocks):
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = WorkflowRecorder(output_dir=tmpdir)

            recorder.add_step(MockGesture(type="tap"), None, {})
            recorder.add_step(MockGesture(type="swipe"), None, {})

            recorder.deduplicate()

            # Steps should be numbered 1, 2
            assert recorder.steps[0].step_id == 1
            assert recorder.steps[1].step_id == 2


class TestFormatStep:
    """Tests for format_step function."""

    def test_format_step_with_id(self):
        step = WorkflowStep(
            step_id=1,
            action="tap",
            locator={"primary": {"strategy": "id", "value": "com.app:id/my_button"}},
            gesture={"type": "tap", "start": [100, 200]},
        )
        formatted = format_step(step)
        assert "[1]" in formatted
        assert "TAP" in formatted
        assert "#my_button" in formatted

    def test_format_step_with_text(self):
        step = WorkflowStep(
            step_id=2,
            action="tap",
            locator={"primary": {"strategy": "text", "value": "Login"}},
            gesture={"type": "tap", "start": [100, 200]},
        )
        formatted = format_step(step)
        assert '"Login"' in formatted

    def test_format_step_with_content_desc(self):
        step = WorkflowStep(
            step_id=3,
            action="tap",
            locator={"primary": {"strategy": "content_desc", "value": "Settings"}},
            gesture={"type": "tap", "start": [100, 200]},
        )
        formatted = format_step(step)
        assert "[Settings]" in formatted

    def test_format_step_with_direction(self):
        step = WorkflowStep(
            step_id=4,
            action="swipe",
            locator={},
            gesture={"type": "swipe", "start": [100, 200], "direction": "down", "distance": 500},
        )
        formatted = format_step(step)
        assert "SWIPE" in formatted
        assert "down" in formatted
        assert "500px" in formatted
