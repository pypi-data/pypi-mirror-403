"""
Touch Event Listener - Captures raw touch events from getevent.

Parses the output of `adb shell getevent` to capture touch events
and converts them to screen coordinates.
"""

import os
import re
import subprocess
import sys
import threading
import time
from typing import Any, Callable, Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from recorder.adb_wrapper import (
        _get_adb,
        get_input_device,
        get_input_max_values,
        get_screen_size,
    )
except ImportError:
    from adb_wrapper import _get_adb, get_input_device, get_input_max_values, get_screen_size

from core.logging_config import get_logger

# Module logger
logger = get_logger("event_listener")


# Linux input event codes for touch events
EV_SYN = 0x00  # Synchronization event
EV_ABS = 0x03  # Absolute axis event

# ABS event codes
ABS_MT_TRACKING_ID = 0x39  # 57 - Tracking ID for multi-touch
ABS_MT_POSITION_X = 0x35  # 53 - X coordinate
ABS_MT_POSITION_Y = 0x36  # 54 - Y coordinate
ABS_MT_TOUCH_MAJOR = 0x30  # 48 - Touch major axis
ABS_MT_PRESSURE = 0x3A  # 58 - Pressure

# SYN event codes
SYN_REPORT = 0x00  # Report sync

# Tracking ID values
TRACKING_ID_LIFT = 0xFFFFFFFF  # -1 in unsigned, indicates touch up


class TouchEvent:
    """Represents a single touch event."""

    def __init__(
        self,
        event_type: str,
        raw_x: int,
        raw_y: int,
        screen_x: int,
        screen_y: int,
        timestamp: float,
        tracking_id: int,
    ):
        self.type = event_type
        self.raw_x = raw_x
        self.raw_y = raw_y
        self.screen_x = screen_x
        self.screen_y = screen_y
        self.timestamp = timestamp
        self.tracking_id = tracking_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "type": self.type,
            "raw_x": self.raw_x,
            "raw_y": self.raw_y,
            "screen_x": self.screen_x,
            "screen_y": self.screen_y,
            "timestamp": self.timestamp,
            "tracking_id": self.tracking_id,
        }


class TouchEventListener:
    """
    Captures touch events from Android device via getevent.

    Usage:
        listener = TouchEventListener()
        listener.on_event(lambda event: print(event.to_dict()))
        listener.start()
        # ... recording ...
        listener.stop()
    """

    def __init__(self, device_path: Optional[str] = None):
        """
        Initialize the touch event listener.

        Args:
            device_path: Specific input device path (auto-detected if None)
        """
        self.device_path = device_path
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._process: Optional[subprocess.Popen] = None
        self._callbacks: List[Callable[[TouchEvent], None]] = []

        # Calibration values
        self._max_x = 0
        self._max_y = 0
        self._screen_width = 0
        self._screen_height = 0

        # Current touch state
        self._current_x = 0
        self._current_y = 0
        self._current_tracking_id = -1
        self._touch_active = False
        self._pending_events: List[Dict[str, Any]] = []

    def _calibrate(self) -> None:
        """Load device calibration values."""
        if not self.device_path:
            self.device_path = get_input_device()

        self._max_x, self._max_y = get_input_max_values(self.device_path)
        self._screen_width, self._screen_height = get_screen_size()

        logger.info(f"Touch device: {self.device_path}")
        logger.info(f"Input range: {self._max_x} x {self._max_y}")
        logger.info(f"Screen size: {self._screen_width} x {self._screen_height}")

    def _raw_to_screen(self, raw_x: int, raw_y: int) -> tuple:
        """
        Convert raw input coordinates to screen coordinates.

        Args:
            raw_x: Raw X coordinate from input device
            raw_y: Raw Y coordinate from input device

        Returns:
            Tuple of (screen_x, screen_y)
        """
        if self._max_x > 0 and self._max_y > 0:
            screen_x = int(raw_x * self._screen_width / self._max_x)
            screen_y = int(raw_y * self._screen_height / self._max_y)
        else:
            # Assume 1:1 mapping if calibration failed
            screen_x = raw_x
            screen_y = raw_y

        # Clamp to screen bounds
        screen_x = max(0, min(screen_x, self._screen_width - 1))
        screen_y = max(0, min(screen_y, self._screen_height - 1))

        return screen_x, screen_y

    def on_event(self, callback: Callable[[TouchEvent], None]) -> None:
        """
        Register callback for touch events.

        Args:
            callback: Function to call with TouchEvent on each event
        """
        self._callbacks.append(callback)

    def _emit_event(self, event: TouchEvent) -> None:
        """Emit event to all registered callbacks."""
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in event callback: {e}")

    def _parse_line(self, line: str) -> None:
        """
        Parse a single line from getevent output.

        Format: /dev/input/event1: 0003 0035 00000215
                device           : type code value (hex)
        """
        # Match getevent output format
        match = re.match(
            r"(/dev/input/event\d+):\s+([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+([0-9a-fA-F]+)", line
        )
        if not match:
            return

        device, ev_type, ev_code, ev_value = match.groups()

        # Skip if not our device
        if self.device_path and device != self.device_path:
            return

        ev_type = int(ev_type, 16)
        ev_code = int(ev_code, 16)
        ev_value = int(ev_value, 16)

        # Handle absolute position events
        if ev_type == EV_ABS:
            if ev_code == ABS_MT_POSITION_X:
                self._current_x = ev_value
            elif ev_code == ABS_MT_POSITION_Y:
                self._current_y = ev_value
            elif ev_code == ABS_MT_TRACKING_ID:
                if ev_value == TRACKING_ID_LIFT or ev_value == 0xFFFFFFFF:
                    # Touch up
                    self._pending_events.append(
                        {"type": "touch_up", "tracking_id": self._current_tracking_id}
                    )
                    self._touch_active = False
                    self._current_tracking_id = -1
                else:
                    # Touch down - new tracking ID
                    if not self._touch_active:
                        self._pending_events.append({"type": "touch_down", "tracking_id": ev_value})
                        self._touch_active = True
                    self._current_tracking_id = ev_value

        # Handle sync events - this is when we emit the complete event
        elif ev_type == EV_SYN and ev_code == SYN_REPORT:
            timestamp = time.time()
            screen_x, screen_y = self._raw_to_screen(self._current_x, self._current_y)

            # Process pending events
            for pending in self._pending_events:
                event = TouchEvent(
                    event_type=pending["type"],
                    raw_x=self._current_x,
                    raw_y=self._current_y,
                    screen_x=screen_x,
                    screen_y=screen_y,
                    timestamp=timestamp,
                    tracking_id=pending.get("tracking_id", self._current_tracking_id),
                )
                self._emit_event(event)

            # If touch is active and no pending events, it's a move
            if self._touch_active and not self._pending_events:
                event = TouchEvent(
                    event_type="touch_move",
                    raw_x=self._current_x,
                    raw_y=self._current_y,
                    screen_x=screen_x,
                    screen_y=screen_y,
                    timestamp=timestamp,
                    tracking_id=self._current_tracking_id,
                )
                self._emit_event(event)

            self._pending_events.clear()

    def _listen_loop(self) -> None:
        """Main listening loop running in background thread."""
        adb = _get_adb()

        # Use specific device path if set, otherwise listen to all
        if self.device_path:
            getevent_cmd = f"getevent {self.device_path}"
        else:
            getevent_cmd = "getevent"

        cmd = [adb, "shell", getevent_cmd]

        self._process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0  # Unbuffered
        )

        try:
            # Read byte by byte to avoid buffering issues
            line_buffer = b""
            while self._running:
                byte = self._process.stdout.read(1)
                if not byte:
                    break
                if byte == b"\n":
                    line = line_buffer.decode("utf-8", errors="ignore").strip()
                    line_buffer = b""
                    if line:
                        self._parse_line(line)
                else:
                    line_buffer += byte
        except Exception as e:
            if self._running:
                logger.error(f"Error in event listener: {e}")
        finally:
            if self._process:
                self._process.terminate()
                self._process.wait()

    def start(self) -> None:
        """Begin listening to touch device."""
        if self._running:
            return

        self._calibrate()
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        logger.info("Touch event listener started")

    def stop(self) -> None:
        """Stop listening."""
        self._running = False

        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                # Force kill if terminate didn't work
                self._process.kill()
                self._process.wait()
            except Exception as e:
                logger.warning(f"Error stopping process: {e}")

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

        logger.info("Touch event listener stopped")

    def is_running(self) -> bool:
        """Check if listener is currently running."""
        return self._running


class MultiTouchState:
    """
    Tracks state for multi-touch gestures (pinch).

    Maintains positions of multiple fingers for pinch detection.
    """

    def __init__(self):
        self.touches: Dict[int, Dict[str, Any]] = {}  # tracking_id -> position

    def update(self, event: TouchEvent) -> None:
        """Update touch state with new event."""
        if event.type == "touch_down":
            self.touches[event.tracking_id] = {
                "x": event.screen_x,
                "y": event.screen_y,
                "start_x": event.screen_x,
                "start_y": event.screen_y,
                "timestamp": event.timestamp,
            }
        elif event.type == "touch_move":
            if event.tracking_id in self.touches:
                self.touches[event.tracking_id]["x"] = event.screen_x
                self.touches[event.tracking_id]["y"] = event.screen_y
        elif event.type == "touch_up":
            self.touches.pop(event.tracking_id, None)

    def get_finger_count(self) -> int:
        """Get number of active fingers."""
        return len(self.touches)

    def get_positions(self) -> List[Dict[str, int]]:
        """Get current positions of all fingers."""
        return [{"x": t["x"], "y": t["y"], "id": tid} for tid, t in self.touches.items()]

    def clear(self) -> None:
        """Clear all touch state."""
        self.touches.clear()
