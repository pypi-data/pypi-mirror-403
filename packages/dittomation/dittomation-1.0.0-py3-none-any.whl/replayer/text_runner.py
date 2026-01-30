"""
Text Runner - Execute workflows from plain text commands.

Usage:
    python text_runner.py workflow.txt

Or inline:
    python text_runner.py -c "tap Phone; tap Contacts; swipe down"

Text format:
    tap "element text"
    tap element_id
    tap 540,1200
    long_press "Settings"
    swipe up
    swipe down
    swipe left
    swipe right
    scroll up
    scroll down
    type "hello world"
    back
    home
    wait 2
"""

import argparse
import os
import re
import sys
import time
from typing import Dict, List, Optional, Tuple

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from recorder.adb_wrapper import check_device_connected, get_screen_size, wait_for_device
from recorder.ui_dumper import capture_ui_fast, get_center
from replayer.executor import input_text, long_press, press_back, press_home, swipe, tap


class TextRunner:
    """Executes text-based workflow commands."""

    def __init__(self, delay_ms: int = 500, verbose: bool = False):
        self.delay_ms = delay_ms
        self.verbose = verbose
        self.screen_width = 1080
        self.screen_height = 2400

    def _find_element(self, target: str, elements: List[Dict]) -> Optional[Tuple[int, int]]:
        """Find element by text, content-desc, or resource-id."""
        target_lower = target.lower().strip()

        # Try exact matches first
        for elem in elements:
            if elem.get("text", "").lower() == target_lower:
                return get_center(elem["bounds"])
            if elem.get("content_desc", "").lower() == target_lower:
                return get_center(elem["bounds"])
            rid = elem.get("resource_id", "").split("/")[-1].lower()
            if rid == target_lower:
                return get_center(elem["bounds"])

        # Try partial matches
        for elem in elements:
            if target_lower in elem.get("text", "").lower():
                return get_center(elem["bounds"])
            if target_lower in elem.get("content_desc", "").lower():
                return get_center(elem["bounds"])
            rid = elem.get("resource_id", "").split("/")[-1].lower()
            if target_lower in rid:
                return get_center(elem["bounds"])

        return None

    def _parse_target(self, target: str, elements: List[Dict]) -> Optional[Tuple[int, int]]:
        """Parse target string to coordinates."""
        # Check for coordinates: "540,1200" or "540, 1200"
        coord_match = re.match(r"(\d+)\s*,\s*(\d+)", target)
        if coord_match:
            return int(coord_match.group(1)), int(coord_match.group(2))

        # Try to find element
        coords = self._find_element(target, elements)
        if coords:
            return coords

        return None

    def _get_swipe_coords(self, direction: str) -> Tuple[int, int, int, int]:
        """Get swipe coordinates for direction."""
        cx, cy = self.screen_width // 2, self.screen_height // 2
        distance = 500

        if direction == "up":
            return cx, cy + distance // 2, cx, cy - distance // 2
        elif direction == "down":
            return cx, cy - distance // 2, cx, cy + distance // 2
        elif direction == "left":
            return cx + distance // 2, cy, cx - distance // 2, cy
        elif direction == "right":
            return cx - distance // 2, cy, cx + distance // 2, cy
        else:
            return cx, cy, cx, cy

    def execute_command(self, command: str) -> bool:
        """
        Execute a single command.

        Returns:
            True if successful
        """
        command = command.strip()
        if not command or command.startswith("#"):
            return True  # Skip empty lines and comments

        # Parse command
        parts = command.split(None, 1)
        action = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        # Remove quotes from argument
        arg = arg.strip().strip("\"'")

        if self.verbose:
            print(f"  Command: {action} {arg}")

        # Get current UI for element finding
        _, elements = capture_ui_fast()

        # Execute based on action
        if action == "tap":
            coords = self._parse_target(arg, elements)
            if coords:
                print(f"  Tap at ({coords[0]}, {coords[1]})")
                return tap(coords[0], coords[1])
            else:
                print(f"  Error: Element '{arg}' not found")
                return False

        elif action == "long_press" or action == "longpress" or action == "hold":
            coords = self._parse_target(arg, elements)
            if coords:
                print(f"  Long press at ({coords[0]}, {coords[1]})")
                return long_press(coords[0], coords[1], 1000)
            else:
                print(f"  Error: Element '{arg}' not found")
                return False

        elif action == "swipe":
            x1, y1, x2, y2 = self._get_swipe_coords(arg.lower())
            print(f"  Swipe {arg}")
            return swipe(x1, y1, x2, y2, 300)

        elif action == "scroll":
            x1, y1, x2, y2 = self._get_swipe_coords(arg.lower())
            print(f"  Scroll {arg}")
            return swipe(x1, y1, x2, y2, 500)

        elif action == "type" or action == "text" or action == "input":
            print(f"  Type: {arg}")
            return input_text(arg)

        elif action == "back":
            print("  Press back")
            return press_back()

        elif action == "home":
            print("  Press home")
            return press_home()

        elif action == "wait" or action == "sleep":
            try:
                seconds = float(arg) if arg else 1
                print(f"  Wait {seconds}s")
                time.sleep(seconds)
                return True
            except ValueError:
                print(f"  Error: Invalid wait time '{arg}'")
                return False

        else:
            print(f"  Error: Unknown action '{action}'")
            return False

    def run_commands(self, commands: List[str]) -> Tuple[int, int]:
        """
        Run a list of commands.

        Returns:
            Tuple of (success_count, fail_count)
        """
        success = 0
        failed = 0

        for i, cmd in enumerate(commands, 1):
            cmd = cmd.strip()
            if not cmd or cmd.startswith("#"):
                continue

            print(f"\nStep {i}: {cmd}")

            if self.execute_command(cmd):
                success += 1
            else:
                failed += 1

            # Delay between commands
            time.sleep(self.delay_ms / 1000.0)

        return success, failed

    def run_file(self, filepath: str) -> Tuple[int, int]:
        """Run commands from a file."""
        with open(filepath, encoding="utf-8") as f:
            commands = f.readlines()
        return self.run_commands(commands)

    def run_inline(self, text: str) -> Tuple[int, int]:
        """Run commands from inline text (semicolon separated)."""
        commands = [c.strip() for c in text.split(";")]
        return self.run_commands(commands)


def main():
    parser = argparse.ArgumentParser(
        description="Execute workflows from plain text commands",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  tap "element"      Tap on element by text/id
  tap 540,1200       Tap at coordinates
  long_press "el"    Long press on element
  swipe up/down/left/right
  scroll up/down
  type "text"        Input text
  back               Press back button
  home               Press home button
  wait 2             Wait 2 seconds

Examples:
  python text_runner.py workflow.txt
  python text_runner.py -c "tap Phone; wait 1; tap Contacts"
        """,
    )

    parser.add_argument("file", nargs="?", help="Workflow text file")
    parser.add_argument("-c", "--command", help="Inline commands (semicolon separated)")
    parser.add_argument("-d", "--delay", type=int, default=500, help="Delay between commands (ms)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if not args.file and not args.command:
        parser.print_help()
        sys.exit(1)

    # Check device
    if not check_device_connected():
        print("Waiting for device...")
        if not wait_for_device(30):
            print("Error: No device connected")
            sys.exit(1)

    # Get screen size
    runner = TextRunner(delay_ms=args.delay, verbose=args.verbose)
    try:
        runner.screen_width, runner.screen_height = get_screen_size()
    except Exception:
        pass

    print("=" * 50)
    print("Text Workflow Runner")
    print(f"Screen: {runner.screen_width}x{runner.screen_height}")
    print("=" * 50)

    # Run commands
    if args.command:
        success, failed = runner.run_inline(args.command)
    else:
        success, failed = runner.run_file(args.file)

    # Summary
    print("\n" + "=" * 50)
    print(f"Completed: {success} success, {failed} failed")
    print("=" * 50)

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
