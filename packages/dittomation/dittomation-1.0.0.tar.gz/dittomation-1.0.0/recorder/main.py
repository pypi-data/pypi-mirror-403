"""
Recorder Main - CLI entry point for recording Android interactions.

Usage:
    python -m recorder.main --output workflow.json

Flow:
1. Initialize ADB connection
2. Detect touch device and calibration values
3. Start event listener
4. On TOUCH_DOWN: capture UI snapshot
5. On gesture complete: match element, classify gesture, add step
6. On Ctrl+C: save workflow and exit
"""

import argparse
import os
import signal
import sys
import time
from typing import Any, Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from recorder.adb_wrapper import check_device_connected, get_screen_size, wait_for_device
    from recorder.element_matcher import describe_match, match_element_at_point
    from recorder.event_listener import TouchEvent, TouchEventListener
    from recorder.gesture_classifier import Gesture, GestureClassifier, describe_gesture
    from recorder.ui_dumper import (
        capture_ui,
        find_scrollable_parent,
        pretty_print_element,
    )
    from recorder.workflow import WorkflowRecorder, format_step
except ImportError:
    from adb_wrapper import check_device_connected, get_screen_size, wait_for_device
    from element_matcher import describe_match, match_element_at_point
    from event_listener import TouchEvent, TouchEventListener
    from gesture_classifier import Gesture, GestureClassifier, describe_gesture
    from ui_dumper import capture_ui, find_scrollable_parent, pretty_print_element
    from workflow import WorkflowRecorder, format_step

from core.config_manager import init_config
from core.exceptions import DittoMationError
from core.logging_config import get_logger, setup_recorder_logging

# Module logger
logger = get_logger("recorder.main")


class RecordingSession:
    """
    Manages a recording session.

    Coordinates event listening, UI capture, gesture classification,
    and workflow recording.
    """

    def __init__(self, output_path: str, output_dir: str = "output"):
        """
        Initialize recording session.

        Args:
            output_path: Path for workflow JSON output
            output_dir: Directory for UI snapshots
        """
        self.output_path = output_path
        self.output_dir = output_dir

        # Components
        self.listener: Optional[TouchEventListener] = None
        self.classifier: Optional[GestureClassifier] = None
        self.workflow: Optional[WorkflowRecorder] = None

        # State
        self._running = False
        self._pending_ui_tree = None
        self._pending_elements: List[Dict[str, Any]] = []
        self._touch_down_time: float = 0

    def _on_touch_event(self, event: TouchEvent) -> None:
        """
        Handle incoming touch events.

        Args:
            event: TouchEvent from listener
        """
        # On touch down, capture UI snapshot
        if event.type == "touch_down":
            self._touch_down_time = time.time()
            try:
                step_num = len(self.workflow) + 1
                xml_path = self.workflow.get_ui_snapshot_path(step_num)
                self._pending_ui_tree, self._pending_elements = capture_ui(xml_path)
                logger.debug(f"UI captured ({len(self._pending_elements)} elements)")
            except Exception as e:
                logger.warning(f"UI capture failed: {e}")
                self._pending_ui_tree = None
                self._pending_elements = []

        # Feed event to classifier
        self.classifier.feed(event)

        # Check for completed gesture
        gesture = self.classifier.get_gesture()
        if gesture:
            self._on_gesture_complete(gesture)

    def _on_gesture_complete(self, gesture: Gesture) -> None:
        """
        Handle completed gesture.

        Args:
            gesture: Classified Gesture
        """
        logger.info(f"{describe_gesture(gesture)}")

        # Match element at gesture start point
        x, y = gesture.start
        element, locator = match_element_at_point(self._pending_elements, x, y)

        if element:
            logger.debug(f"Element: {pretty_print_element(element)}")
            logger.debug(f"Locator: {describe_match(element, locator)}")
        else:
            logger.debug(f"No element matched at ({x}, {y})")

        # Add step to workflow
        step_num = len(self.workflow) + 1
        xml_path = self.workflow.get_ui_snapshot_path(step_num)

        step = self.workflow.add_step(
            gesture=gesture, element=element, locator=locator, ui_xml_file=xml_path
        )

        logger.info(f"Step recorded: {format_step(step)}")

    def _check_scrollable(self, x: int, y: int) -> bool:
        """Check if coordinates are in a scrollable container."""
        if not self._pending_elements:
            return False

        scrollable = find_scrollable_parent(self._pending_elements, x, y)
        return scrollable is not None

    def start(self) -> None:
        """Start the recording session."""
        logger.info("=" * 50)
        logger.info("Android Recorder")
        logger.info("=" * 50)

        # Check device connection
        if not check_device_connected():
            logger.info("No device detected. Waiting for device...")
            if not wait_for_device(timeout=60):
                logger.error("No Android device connected.")
                logger.error("Please connect a device or start an emulator.")
                sys.exit(1)

        # Get screen info (with retry for slow boot)
        width, height = get_screen_size()
        logger.info(f"Screen size: {width}x{height}")

        # Initialize components
        self.workflow = WorkflowRecorder(output_dir=self.output_dir)
        self.classifier = GestureClassifier(scrollable_checker=self._check_scrollable)
        self.listener = TouchEventListener()

        # Register event callback
        self.listener.on_event(self._on_touch_event)

        # Start listening
        logger.info("Starting touch event capture...")
        self.listener.start()
        self._running = True

        logger.info("=" * 50)
        logger.info("Recording started. Interact with the device.")
        logger.info("Press Ctrl+C to stop and save.")
        logger.info("=" * 50)

    def stop(self) -> None:
        """Stop the recording session and save workflow."""
        self._running = False

        if self.listener:
            self.listener.stop()

        if self.workflow and len(self.workflow) > 0:
            logger.info("=" * 50)
            logger.info("Recording stopped.")
            logger.info("=" * 50)

            # Deduplicate
            removed = self.workflow.deduplicate()
            if removed > 0:
                logger.info(f"Removed {removed} duplicate step(s)")

            # Save workflow
            self.workflow.save(self.output_path)

            # Print summary
            logger.info(self.workflow.summary())
        else:
            logger.info("No steps recorded.")

    def wait(self) -> None:
        """Wait for recording to complete (Ctrl+C)."""
        try:
            while self._running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Record Android touch interactions to a workflow file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m recorder.main --output my_workflow.json
  python -m recorder.main -o test.json --output-dir ./snapshots
  python -m recorder.main --log-level DEBUG

The recorder will:
1. Capture touch events from the connected Android device
2. Match taps to UI elements
3. Classify gestures (tap, long_press, swipe, scroll, pinch)
4. Save a replayable workflow file
        """,
    )

    parser.add_argument(
        "-o",
        "--output",
        default="workflow.json",
        help="Output workflow file path (default: workflow.json)",
    )

    parser.add_argument(
        "--output-dir", default="output", help="Directory for UI snapshots (default: output)"
    )

    parser.add_argument("--config", help="Path to configuration file (JSON or YAML)")

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Log level (default: INFO)",
    )

    parser.add_argument("--log-file", action="store_true", help="Enable logging to file")

    args = parser.parse_args()

    # Initialize configuration
    if args.config:
        init_config(args.config)

    # Setup logging
    setup_recorder_logging(level=args.log_level, log_to_file=args.log_file, log_to_console=True)

    logger.info("DittoMation Recorder starting...")

    # Create session
    session = RecordingSession(output_path=args.output, output_dir=args.output_dir)

    # Handle signals
    def signal_handler(sig, frame):
        session.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run recording
    try:
        session.start()
        session.wait()
    except DittoMationError as e:
        logger.error(f"Error: {e.message}")
        if e.hint:
            logger.info(f"Hint: {e.hint}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        session.stop()


if __name__ == "__main__":
    main()
