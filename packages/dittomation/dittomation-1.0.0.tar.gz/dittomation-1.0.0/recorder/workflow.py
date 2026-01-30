"""
Workflow - Builds semantic workflow from gestures and elements.

Records interaction steps with element locators and gesture information,
supporting save/load operations for workflow files.
"""

import json
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from recorder.adb_wrapper import get_current_app, get_device_serial, get_screen_size
    from recorder.gesture_classifier import Gesture
except ImportError:
    from adb_wrapper import get_current_app, get_device_serial, get_screen_size
    from gesture_classifier import Gesture

from core.config_manager import get_config_value
from core.exceptions import WorkflowLoadError, WorkflowSaveError
from core.logging_config import get_logger

# Module logger
logger = get_logger("workflow")


# Deduplication thresholds (from config or defaults)
DOUBLE_TAP_TIME_MS = get_config_value("recording.double_tap_threshold_ms", 300)
DOUBLE_TAP_DISTANCE_PX = get_config_value("recording.double_tap_distance_px", 50)


class WorkflowStep:
    """Represents a single step in the workflow."""

    def __init__(
        self,
        step_id: int,
        action: str,
        locator: Dict[str, Any],
        gesture: Dict[str, Any],
        element_snapshot: Optional[Dict[str, Any]] = None,
        ui_xml_file: Optional[str] = None,
        timestamp: Optional[float] = None,
    ):
        self.step_id = step_id
        self.action = action
        self.locator = locator
        self.gesture = gesture
        self.element_snapshot = element_snapshot
        self.ui_xml_file = ui_xml_file
        self.timestamp = timestamp or time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "step_id": self.step_id,
            "timestamp": self.timestamp,
            "action": self.action,
            "locator": self.locator,
            "gesture": self.gesture,
        }

        if self.element_snapshot:
            result["element_snapshot"] = self.element_snapshot

        if self.ui_xml_file:
            result["ui_xml_file"] = self.ui_xml_file

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowStep":
        """Create WorkflowStep from dictionary."""
        return cls(
            step_id=data["step_id"],
            action=data["action"],
            locator=data["locator"],
            gesture=data["gesture"],
            element_snapshot=data.get("element_snapshot"),
            ui_xml_file=data.get("ui_xml_file"),
            timestamp=data.get("timestamp"),
        )


class WorkflowRecorder:
    """
    Records and manages workflow steps.

    Handles step recording, deduplication, and serialization.
    """

    def __init__(self, output_dir: str = "output"):
        """
        Initialize workflow recorder.

        Args:
            output_dir: Directory for output files (UI snapshots, etc.)
        """
        self.output_dir = output_dir
        self.steps: List[WorkflowStep] = []
        self.metadata: Dict[str, Any] = {}

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Initialize metadata
        self._init_metadata()

    def _init_metadata(self) -> None:
        """Initialize workflow metadata from device."""
        try:
            width, height = get_screen_size()
            package, activity = get_current_app()
            device = get_device_serial()

            self.metadata = {
                "app_package": package,
                "app_activity": activity,
                "device": device or "unknown",
                "screen_size": [width, height],
                "recorded_at": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.warning(f"Could not initialize metadata: {e}")
            self.metadata = {
                "app_package": "",
                "device": "unknown",
                "screen_size": [0, 0],
                "recorded_at": datetime.now().isoformat(),
            }

    def add_step(
        self,
        gesture: Gesture,
        element: Optional[Dict[str, Any]],
        locator: Dict[str, Any],
        ui_xml_file: Optional[str] = None,
    ) -> WorkflowStep:
        """
        Add a recorded step to the workflow.

        Args:
            gesture: Classified gesture
            element: Element dictionary (or None if not matched)
            locator: Locator dictionary for element
            ui_xml_file: Path to saved UI XML (for debugging)

        Returns:
            Created WorkflowStep
        """
        step_id = len(self.steps) + 1

        # Create element snapshot (simplified)
        element_snapshot = None
        if element:
            element_snapshot = {
                "class": element.get("class"),
                "resource_id": element.get("resource_id"),
                "text": element.get("text"),
                "content_desc": element.get("content_desc"),
                "bounds": element.get("bounds"),
                "clickable": element.get("clickable"),
                "scrollable": element.get("scrollable"),
            }

        step = WorkflowStep(
            step_id=step_id,
            action=gesture.type,
            locator=locator,
            gesture=gesture.to_dict(),
            element_snapshot=element_snapshot,
            ui_xml_file=ui_xml_file,
        )

        self.steps.append(step)
        return step

    def deduplicate(self) -> int:
        """
        Remove accidental double-taps and duplicate steps.

        Returns:
            Number of steps removed
        """
        if len(self.steps) < 2:
            return 0

        original_count = len(self.steps)
        filtered_steps: List[WorkflowStep] = []

        i = 0
        while i < len(self.steps):
            current = self.steps[i]

            # Check if next step is a duplicate tap
            if i + 1 < len(self.steps):
                next_step = self.steps[i + 1]

                if self._is_duplicate_tap(current, next_step):
                    # Skip the duplicate
                    i += 2
                    filtered_steps.append(current)
                    continue

            filtered_steps.append(current)
            i += 1

        # Renumber steps
        for idx, step in enumerate(filtered_steps, 1):
            step.step_id = idx

        self.steps = filtered_steps
        return original_count - len(self.steps)

    def _is_duplicate_tap(self, step1: WorkflowStep, step2: WorkflowStep) -> bool:
        """
        Check if two steps are duplicate taps.

        Args:
            step1: First step
            step2: Second step

        Returns:
            True if steps are duplicate taps
        """
        # Must both be taps
        if step1.action != "tap" or step2.action != "tap":
            return False

        # Check time difference
        time_diff_ms = (step2.timestamp - step1.timestamp) * 1000
        if time_diff_ms > DOUBLE_TAP_TIME_MS:
            return False

        # Check position difference
        g1 = step1.gesture
        g2 = step2.gesture

        start1 = g1.get("start", [0, 0])
        start2 = g2.get("start", [0, 0])

        dx = abs(start1[0] - start2[0])
        dy = abs(start1[1] - start2[1])

        if dx > DOUBLE_TAP_DISTANCE_PX or dy > DOUBLE_TAP_DISTANCE_PX:
            return False

        return True

    def save(self, filepath: str) -> None:
        """
        Save workflow to JSON file.

        Args:
            filepath: Output file path

        Raises:
            WorkflowSaveError: If the workflow cannot be saved
        """
        try:
            workflow_data = {
                "metadata": self.metadata,
                "steps": [step.to_dict() for step in self.steps],
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(workflow_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Workflow saved: {filepath} ({len(self.steps)} steps)")
        except Exception as e:
            logger.error(f"Failed to save workflow: {e}")
            raise WorkflowSaveError(filepath, str(e))

    @classmethod
    def load(cls, filepath: str) -> "WorkflowRecorder":
        """
        Load workflow from JSON file.

        Args:
            filepath: Input file path

        Returns:
            WorkflowRecorder with loaded steps

        Raises:
            WorkflowLoadError: If the workflow cannot be loaded
        """
        try:
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)

            recorder = cls()
            recorder.metadata = data.get("metadata", {})
            recorder.steps = [
                WorkflowStep.from_dict(step_data) for step_data in data.get("steps", [])
            ]

            logger.info(f"Workflow loaded: {filepath} ({len(recorder.steps)} steps)")
            return recorder
        except FileNotFoundError:
            raise WorkflowLoadError(filepath, "File not found")
        except json.JSONDecodeError as e:
            raise WorkflowLoadError(filepath, f"Invalid JSON: {e}")
        except Exception as e:
            raise WorkflowLoadError(filepath, str(e))

    def get_ui_snapshot_path(self, step_id: int) -> str:
        """
        Generate path for UI snapshot file.

        Args:
            step_id: Step number

        Returns:
            Path string
        """
        return os.path.join(self.output_dir, f"ui_{step_id:03d}.xml")

    def summary(self) -> str:
        """
        Generate workflow summary.

        Returns:
            Summary string
        """
        lines = [
            f"Workflow: {self.metadata.get('app_package', 'unknown')}",
            f"Device: {self.metadata.get('device', 'unknown')}",
            f"Screen: {self.metadata.get('screen_size', [0, 0])}",
            f"Recorded: {self.metadata.get('recorded_at', 'unknown')}",
            f"Steps: {len(self.steps)}",
            "",
        ]

        # Action counts
        action_counts: Dict[str, int] = {}
        for step in self.steps:
            action_counts[step.action] = action_counts.get(step.action, 0) + 1

        for action, count in sorted(action_counts.items()):
            lines.append(f"  {action}: {count}")

        return "\n".join(lines)

    def __len__(self) -> int:
        return len(self.steps)

    def __iter__(self):
        return iter(self.steps)


def format_step(step: WorkflowStep) -> str:
    """
    Format step for display.

    Args:
        step: WorkflowStep to format

    Returns:
        Formatted string
    """
    parts = [f"[{step.step_id}]", step.action.upper()]

    # Add target info
    locator = step.locator
    primary = locator.get("primary", {})

    if primary.get("strategy") == "id":
        rid = primary["value"].split("/")[-1]
        parts.append(f"#{rid}")
    elif primary.get("strategy") == "text":
        parts.append(f'"{primary["value"]}"')
    elif primary.get("strategy") == "content_desc":
        parts.append(f'[{primary["value"]}]')

    # Add gesture details
    gesture = step.gesture
    if gesture.get("direction"):
        parts.append(gesture["direction"])

    if gesture.get("type") in ("swipe", "scroll"):
        parts.append(f"{gesture.get('distance', 0)}px")

    # Add coordinates
    start = gesture.get("start", [0, 0])
    parts.append(f"@({start[0]}, {start[1]})")

    return " ".join(parts)
