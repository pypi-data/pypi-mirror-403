"""
Interactive Recorder - Manual step-by-step recording for emulators.

Since emulators inject touch events at a higher level than getevent can capture,
this recorder uses an interactive approach where the user:
1. Performs an action on the device
2. Presses Enter to record it
3. The recorder captures the UI and asks for action details

Usage:
    python interactive_recorder.py --output workflow.json
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

try:
    from recorder.adb_wrapper import (
        check_device_connected,
        get_current_app,
        get_device_serial,
        get_screen_size,
        wait_for_device,
    )
    from recorder.element_matcher import build_locator, find_elements_at_point, select_best_match
    from recorder.ui_dumper import capture_ui, get_center, pretty_print_element
except ImportError:
    from adb_wrapper import (
        check_device_connected,
        get_current_app,
        get_device_serial,
        get_screen_size,
        wait_for_device,
    )
    from element_matcher import build_locator, find_elements_at_point, select_best_match
    from ui_dumper import capture_ui, get_center, pretty_print_element


class InteractiveRecorder:
    """Interactive step-by-step recorder for emulators."""

    def __init__(self, output_path: str, output_dir: str = "output"):
        self.output_path = output_path
        self.output_dir = output_dir
        self.steps: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}

        os.makedirs(output_dir, exist_ok=True)

    def _init_metadata(self) -> None:
        """Initialize workflow metadata."""
        try:
            width, height = get_screen_size()
            package, activity = get_current_app()
            device = get_device_serial()

            self.metadata = {
                "app_package": package,
                "device": device or "unknown",
                "screen_size": [width, height],
                "recorded_at": datetime.now().isoformat(),
            }
        except Exception as e:
            print(f"Warning: Could not get device info: {e}")
            self.metadata = {
                "app_package": "",
                "device": "unknown",
                "screen_size": [1080, 1920],
                "recorded_at": datetime.now().isoformat(),
            }

    def _capture_ui_state(self, step_num: int) -> Tuple[Optional[Any], List[Dict]]:
        """Capture current UI state."""
        xml_path = os.path.join(self.output_dir, f"ui_{step_num:03d}.xml")
        try:
            tree, elements = capture_ui(xml_path)
            return tree, elements
        except Exception as e:
            print(f"Warning: UI capture failed: {e}")
            return None, []

    def _find_element_by_text_or_id(self, elements: List[Dict], search: str) -> Optional[Dict]:
        """Find element by text, content-desc, or resource-id."""
        search_lower = search.lower()

        # Try exact matches first
        for elem in elements:
            if elem.get("text", "").lower() == search_lower:
                return elem
            if elem.get("content_desc", "").lower() == search_lower:
                return elem
            rid = elem.get("resource_id", "").split("/")[-1].lower()
            if rid == search_lower:
                return elem

        # Try partial matches
        for elem in elements:
            if search_lower in elem.get("text", "").lower():
                return elem
            if search_lower in elem.get("content_desc", "").lower():
                return elem
            rid = elem.get("resource_id", "").split("/")[-1].lower()
            if search_lower in rid:
                return elem

        return None

    def _show_elements(self, elements: List[Dict]) -> None:
        """Display clickable elements in the current UI."""
        print("\n--- Clickable Elements ---")
        count = 0
        for elem in elements:
            # Skip non-interactive elements
            if not (elem.get("clickable") or elem.get("long_clickable")):
                continue

            count += 1
            cls = elem.get("class", "").split(".")[-1]
            text = elem.get("text", "")
            desc = elem.get("content_desc", "")
            rid = elem.get("resource_id", "").split("/")[-1]
            bounds = elem.get("bounds", (0, 0, 0, 0))
            center_x = (bounds[0] + bounds[2]) // 2
            center_y = (bounds[1] + bounds[3]) // 2

            # Build display string
            identifier = text or desc or rid or f"({center_x},{center_y})"
            if len(identifier) > 40:
                identifier = identifier[:37] + "..."

            print(f"  {count:2}. [{cls}] {identifier}")

            if count >= 20:
                remaining = (
                    sum(1 for e in elements if e.get("clickable") or e.get("long_clickable"))
                    - count
                )
                if remaining > 0:
                    print(f"  ... and {remaining} more elements")
                break

        if count == 0:
            print("  No clickable elements found")
        print("-" * 30)

    def _select_action_type(self) -> str:
        """Prompt user to select action type."""
        print("\nAction types:")
        print("  1. tap (default)")
        print("  2. long_press")
        print("  3. swipe")
        print("  4. scroll")
        print("  5. type_text")
        print("  6. press_back")
        print("  7. press_home")

        choice = input("Select action [1]: ").strip() or "1"

        action_map = {
            "1": "tap",
            "tap": "tap",
            "2": "long_press",
            "long_press": "long_press",
            "long": "long_press",
            "3": "swipe",
            "swipe": "swipe",
            "4": "scroll",
            "scroll": "scroll",
            "5": "type_text",
            "type": "type_text",
            "text": "type_text",
            "6": "press_back",
            "back": "press_back",
            "7": "press_home",
            "home": "press_home",
        }

        return action_map.get(choice, "tap")

    def _get_swipe_direction(self) -> Dict[str, Any]:
        """Get swipe/scroll direction and distance."""
        print("\nSwipe direction:")
        print("  1. up")
        print("  2. down")
        print("  3. left")
        print("  4. right")

        choice = input("Select direction [1]: ").strip() or "1"

        direction_map = {
            "1": "up",
            "up": "up",
            "u": "up",
            "2": "down",
            "down": "down",
            "d": "down",
            "3": "left",
            "left": "left",
            "l": "left",
            "4": "right",
            "right": "right",
            "r": "right",
        }

        direction = direction_map.get(choice, "up")

        distance = input("Distance in pixels [500]: ").strip()
        try:
            distance = int(distance) if distance else 500
        except ValueError:
            distance = 500

        return {"direction": direction, "distance": distance}

    def _record_step(self, step_num: int, elements: List[Dict]) -> Optional[Dict]:
        """Record a single step interactively."""
        print(f"\n{'='*50}")
        print(f"Recording Step {step_num}")
        print(f"{'='*50}")

        action = self._select_action_type()

        step = {
            "step_id": step_num,
            "timestamp": time.time(),
            "action": action,
            "locator": None,
            "gesture": {"type": action},
            "element_snapshot": None,
        }

        # Handle different action types
        if action in ("press_back", "press_home"):
            step["gesture"] = {"type": action}
            return step

        if action == "type_text":
            text = input("Enter text to type: ").strip()
            step["gesture"] = {"type": "type_text", "text": text}
            return step

        if action in ("swipe", "scroll"):
            # Get start point
            start_input = input("Enter start point (x,y) or element text: ").strip()

            if "," in start_input:
                try:
                    x, y = map(int, start_input.split(","))
                except ValueError:
                    print("Invalid coordinates, using center of screen")
                    x, y = (
                        self.metadata["screen_size"][0] // 2,
                        self.metadata["screen_size"][1] // 2,
                    )
            else:
                elem = self._find_element_by_text_or_id(elements, start_input)
                if elem:
                    x, y = get_center(elem["bounds"])
                    print(f"Found element: {pretty_print_element(elem)}")
                else:
                    print("Element not found, using center of screen")
                    x, y = (
                        self.metadata["screen_size"][0] // 2,
                        self.metadata["screen_size"][1] // 2,
                    )

            swipe_info = self._get_swipe_direction()

            # Calculate end point
            dx, dy = 0, 0
            if swipe_info["direction"] == "up":
                dy = -swipe_info["distance"]
            elif swipe_info["direction"] == "down":
                dy = swipe_info["distance"]
            elif swipe_info["direction"] == "left":
                dx = -swipe_info["distance"]
            elif swipe_info["direction"] == "right":
                dx = swipe_info["distance"]

            step["gesture"] = {
                "type": action,
                "start": [x, y],
                "end": [x + dx, y + dy],
                "direction": swipe_info["direction"],
                "distance": swipe_info["distance"],
                "duration_ms": 300,
            }

            step["locator"] = {
                "primary": {"strategy": "bounds", "value": [x, y, x, y]},
                "fallbacks": [],
                "bounds": [x, y, x, y],
            }

            return step

        # For tap and long_press
        while True:
            target = input(
                "Enter target element (text, id, x,y) or 'list' to see elements: "
            ).strip()

            if target.lower() == "list":
                self._show_elements(elements)
                continue
            break

        if not target:
            print("No target specified, skipping step")
            return None

        element = None
        x, y = 0, 0

        if "," in target:
            # Coordinates provided
            try:
                x, y = map(int, target.split(","))
                candidates = find_elements_at_point(elements, x, y)
                element = select_best_match(candidates)
            except ValueError:
                # Try as text search
                element = self._find_element_by_text_or_id(elements, target)
        else:
            # Text/ID search
            element = self._find_element_by_text_or_id(elements, target)

        if element:
            print(f"Found: {pretty_print_element(element)}")
            x, y = get_center(element["bounds"])
            step["locator"] = build_locator(element)
            step["element_snapshot"] = {
                "class": element.get("class"),
                "resource_id": element.get("resource_id"),
                "text": element.get("text"),
                "content_desc": element.get("content_desc"),
                "bounds": element.get("bounds"),
            }
        else:
            if x == 0 and y == 0:
                print(f"Element '{target}' not found in current UI")
                retry = input("Enter coordinates (x,y) or 'skip': ").strip()
                if retry.lower() == "skip":
                    return None
                try:
                    x, y = map(int, retry.split(","))
                except ValueError:
                    print("Invalid input, skipping step")
                    return None

            step["locator"] = {
                "primary": {"strategy": "bounds", "value": [x, y, x, y]},
                "fallbacks": [],
                "bounds": [x, y, x, y],
            }

        duration = 100 if action == "tap" else 800
        step["gesture"] = {"type": action, "start": [x, y], "end": [x, y], "duration_ms": duration}

        return step

    def run(self) -> None:
        """Run interactive recording session."""
        print("=" * 50)
        print("Interactive Android Recorder")
        print("=" * 50)

        # Check device
        if not check_device_connected():
            print("Waiting for device...")
            if not wait_for_device(timeout=30):
                print("Error: No device connected")
                sys.exit(1)

        self._init_metadata()
        print(f"Screen size: {self.metadata['screen_size']}")
        print(f"App: {self.metadata['app_package']}")

        print("\n" + "=" * 50)
        print("Instructions:")
        print("1. Perform an action on the device/emulator")
        print("2. Press Enter to record it")
        print("3. Follow the prompts to describe the action")
        print("4. Type 'done' when finished recording")
        print("=" * 50)

        step_num = 0

        while True:
            print("\n" + "-" * 30)
            cmd = input("Press Enter to record next step (or 'done' to finish): ").strip().lower()

            if cmd == "done":
                break

            if cmd == "quit" or cmd == "exit":
                if input("Discard recording? (y/N): ").lower() == "y":
                    print("Recording discarded")
                    return
                continue

            step_num += 1

            # Capture current UI
            print("Capturing UI state...")
            tree, elements = self._capture_ui_state(step_num)

            if not elements:
                print("Warning: Could not capture UI. Continuing anyway...")

            clickable_count = sum(
                1 for e in elements if e.get("clickable") or e.get("long_clickable")
            )
            print(f"Found {len(elements)} UI elements ({clickable_count} clickable)")

            # Record step
            step = self._record_step(step_num, elements)

            if step:
                self.steps.append(step)
                print(f"\n✓ Recorded: {step['action']} - Step {step['step_id']}")
            else:
                step_num -= 1  # Reuse step number

        # Save workflow
        if self.steps:
            self._save_workflow()
        else:
            print("No steps recorded")

    def _save_workflow(self) -> None:
        """Save recorded workflow to file."""
        workflow = {"metadata": self.metadata, "steps": self.steps}

        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(workflow, f, indent=2, ensure_ascii=False)

        print(f"\n{'='*50}")
        print(f"Workflow saved: {self.output_path}")
        print(f"Total steps: {len(self.steps)}")
        print(f"{'='*50}")


def main():
    parser = argparse.ArgumentParser(
        description="Interactive Android workflow recorder for emulators"
    )
    parser.add_argument(
        "-o",
        "--output",
        default="workflow.json",
        help="Output workflow file (default: workflow.json)",
    )
    parser.add_argument(
        "--output-dir", default="output", help="Directory for UI snapshots (default: output)"
    )

    args = parser.parse_args()

    recorder = InteractiveRecorder(output_path=args.output, output_dir=args.output_dir)
    recorder.run()


if __name__ == "__main__":
    main()
