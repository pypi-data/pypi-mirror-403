"""
Replayer Main - CLI entry point for replaying recorded workflows.

Usage:
    python -m replayer.main --workflow workflow.json --delay 500

Flow:
1. Load workflow JSON
2. For each step:
   a. Capture current UI
   b. Locate element using smart fallback
   c. Execute gesture at element center (or recorded coords if not found)
   d. Wait for delay between steps
3. Report success/failure for each step
"""

import argparse
import os
import signal
import sys
from typing import Any, Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config_manager import init_config
from core.exceptions import DittoMationError, WorkflowLoadError
from core.logging_config import get_logger, setup_replayer_logging
from recorder.adb_wrapper import check_device_connected
from recorder.ui_dumper import capture_ui_fast
from recorder.workflow import WorkflowRecorder, WorkflowStep, format_step
from replayer.executor import GestureExecutor
from replayer.locator import ElementLocator

# Module logger
logger = get_logger("replayer.main")


class ReplaySession:
    """
    Manages a replay session.

    Coordinates workflow loading, element location, and gesture execution.
    """

    def __init__(self, workflow_path: str, delay_ms: int = 500, verbose: bool = False):
        """
        Initialize replay session.

        Args:
            workflow_path: Path to workflow JSON file
            delay_ms: Delay between steps in milliseconds
            verbose: Enable verbose output
        """
        self.workflow_path = workflow_path
        self.delay_ms = delay_ms
        self.verbose = verbose

        # Components
        self.workflow: Optional[WorkflowRecorder] = None
        self.locator = ElementLocator()
        self.executor = GestureExecutor(delay_ms=delay_ms)

        # Results tracking
        self.results: List[Dict[str, Any]] = []
        self._running = False
        self._stop_requested = False

    def load(self) -> bool:
        """
        Load the workflow file.

        Returns:
            True if loaded successfully
        """
        try:
            self.workflow = WorkflowRecorder.load(self.workflow_path)
            logger.info(f"Loaded workflow: {len(self.workflow)} steps")

            if self.verbose:
                logger.info(self.workflow.summary())

            return True
        except WorkflowLoadError as e:
            logger.error(f"Error loading workflow: {e.message}")
            if e.hint:
                logger.info(f"Hint: {e.hint}")
            return False
        except Exception as e:
            logger.error(f"Error loading workflow: {e}")
            return False

    def run(self) -> bool:
        """
        Run the replay session.

        Returns:
            True if all steps succeeded
        """
        if not self.workflow:
            logger.error("No workflow loaded")
            return False

        if len(self.workflow) == 0:
            logger.warning("Workflow is empty")
            return True

        logger.info("=" * 50)
        logger.info("Starting replay...")
        logger.info("=" * 50)

        self._running = True
        self.results = []

        for step in self.workflow:
            if self._stop_requested:
                logger.info("Replay stopped by user")
                break

            result = self._replay_step(step)
            self.results.append(result)

            if not result["success"]:
                logger.error(f"Step {step.step_id} FAILED: {result.get('error', 'Unknown error')}")

        self._running = False
        return self._print_summary()

    def _replay_step(self, step: WorkflowStep) -> Dict[str, Any]:
        """
        Replay a single workflow step.

        Args:
            step: WorkflowStep to replay

        Returns:
            Result dict with success status and details
        """
        result = {
            "step_id": step.step_id,
            "action": step.action,
            "success": False,
            "strategy_used": None,
            "fallback_level": 0,
            "error": None,
        }

        logger.info(f"Step {step.step_id}: {step.action.upper()}")

        try:
            # Capture current UI
            ui_tree, elements = capture_ui_fast()

            if not elements:
                logger.debug("No UI elements found, using coordinates")
                # Fall back to recorded coordinates
                coordinates = self._get_fallback_coordinates(step)
                success = self.executor.execute(step.gesture, coordinates)
                result["success"] = success
                result["strategy_used"] = "coordinates"
                result["fallback_level"] = 99
                return result

            # Find element using locator
            loc_result = self.locator.find_element(step.locator, elements)

            if loc_result.found:
                strategy_info = f"{loc_result.strategy_used}"
                if loc_result.fallback_level > 0:
                    strategy_info += f" (fallback #{loc_result.fallback_level})"
                logger.debug(f"Element found using: {strategy_info}")
            else:
                logger.debug("Element not found, using coordinates")

            # Execute gesture
            success = self.executor.execute(step.gesture, loc_result.coordinates)

            result["success"] = success
            result["strategy_used"] = loc_result.strategy_used
            result["fallback_level"] = loc_result.fallback_level

            if self.verbose and loc_result.element:
                elem = loc_result.element
                logger.debug(f"Element: {elem.get('class', '').split('.')[-1]}")
                if elem.get("resource_id"):
                    logger.debug(f"ID: {elem['resource_id'].split('/')[-1]}")
                if elem.get("text"):
                    logger.debug(f"Text: {elem['text'][:50]}")

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Step execution error: {e}")

        return result

    def _get_fallback_coordinates(self, step: WorkflowStep) -> tuple:
        """
        Get fallback coordinates from step.

        Args:
            step: WorkflowStep

        Returns:
            (x, y) coordinates
        """
        gesture = step.gesture
        start = gesture.get("start", [0, 0])
        return (start[0], start[1])

    def _print_summary(self) -> bool:
        """
        Print replay summary.

        Returns:
            True if all steps succeeded
        """
        logger.info("=" * 50)
        logger.info("Replay Summary")
        logger.info("=" * 50)

        total = len(self.results)
        success = sum(1 for r in self.results if r["success"])
        failed = total - success

        logger.info(f"Total steps: {total}")
        logger.info(f"Successful: {success}")
        logger.info(f"Failed: {failed}")

        # Strategy breakdown
        strategy_counts: Dict[str, int] = {}
        fallback_counts: Dict[int, int] = {}

        for r in self.results:
            if r["success"]:
                strategy = r.get("strategy_used", "unknown")
                strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

                level = r.get("fallback_level", 0)
                fallback_counts[level] = fallback_counts.get(level, 0) + 1

        if strategy_counts:
            logger.info("Strategies used:")
            for strategy, count in sorted(strategy_counts.items()):
                logger.info(f"  {strategy}: {count}")

        if any(level > 0 for level in fallback_counts):
            logger.info("Fallback usage:")
            for level, count in sorted(fallback_counts.items()):
                if level == 0:
                    logger.info(f"  Primary worked: {count}")
                else:
                    logger.info(f"  Fallback #{level}: {count}")

        # Failed steps
        if failed > 0:
            logger.error("Failed steps:")
            for r in self.results:
                if not r["success"]:
                    logger.error(f"  Step {r['step_id']}: {r.get('error', 'Unknown')}")

        return failed == 0

    def stop(self) -> None:
        """Request stop of replay."""
        self._stop_requested = True


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Replay recorded Android workflows.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m replayer.main --workflow my_workflow.json
  python -m replayer.main -w test.json --delay 1000 --verbose
  python -m replayer.main -w test.json --log-level DEBUG

The replayer will:
1. Load the workflow file
2. For each step, find the target element using smart fallbacks
3. Execute the recorded gesture
4. Report success/failure for each step
        """,
    )

    parser.add_argument("-w", "--workflow", required=True, help="Workflow JSON file to replay")

    parser.add_argument(
        "-d",
        "--delay",
        type=int,
        default=500,
        help="Delay between steps in milliseconds (default: 500)",
    )

    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")

    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be done without executing"
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
    setup_replayer_logging(level=args.log_level, log_to_file=args.log_file, log_to_console=True)

    logger.info("DittoMation Replayer starting...")

    # Check device connection
    if not args.dry_run:
        if not check_device_connected():
            logger.error("No Android device connected.")
            logger.error("Please connect a device or start an emulator.")
            sys.exit(1)

    # Create session
    session = ReplaySession(workflow_path=args.workflow, delay_ms=args.delay, verbose=args.verbose)

    # Handle signals
    def signal_handler(sig, frame):
        logger.info("Stopping replay...")
        session.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Load workflow
    if not session.load():
        sys.exit(1)

    # Dry run mode
    if args.dry_run:
        logger.info("[DRY RUN] Steps that would be executed:")
        for step in session.workflow:
            logger.info(f"  {format_step(step)}")
        sys.exit(0)

    # Run replay
    try:
        success = session.run()
        sys.exit(0 if success else 1)
    except DittoMationError as e:
        logger.error(f"Error: {e.message}")
        if e.hint:
            logger.info(f"Hint: {e.hint}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
