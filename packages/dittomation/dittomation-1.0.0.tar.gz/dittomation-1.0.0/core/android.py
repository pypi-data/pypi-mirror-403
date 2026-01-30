"""
Android - High-level Python API for Android device control.

Provides a clean, intuitive interface for automating Android devices.
Wraps the lower-level recorder and replayer modules.

Usage:
    from core import Android

    android = Android()  # Auto-connects to device

    # Gestures
    android.tap(100, 200)           # By coordinates
    android.tap("Login")            # By text
    android.tap(id="btn_login")     # By resource-id

    # Apps
    android.open_app("Chrome")
    print(android.current_app())

    # Elements
    element = android.find("Login")
    android.wait_for("Welcome", timeout=10)
"""

import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple, Union

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.exceptions import (
    DeviceNotFoundError,
)
from core.logging_config import get_logger
from recorder.adb_wrapper import (
    get_connected_devices,
    get_current_app,
    get_device_serial,
    get_screen_size,
    run_adb,
)
from recorder.element_matcher import (
    MatchResult,
    find_best_match,
    find_elements_with_confidence,
)
from recorder.ui_dumper import (
    capture_ui_fast,
    get_center,
)
from replayer.executor import (
    input_text as _input_text,
)
from replayer.executor import (
    long_press as _long_press,
)
from replayer.executor import (
    pinch as _pinch,
)
from replayer.executor import (
    press_back as _press_back,
)
from replayer.executor import (
    press_enter as _press_enter,
)
from replayer.executor import (
    press_home as _press_home,
)
from replayer.executor import (
    press_key as _press_key,
)
from replayer.executor import (
    scroll as _scroll,
)
from replayer.executor import (
    swipe as _swipe,
)
from replayer.executor import (
    tap as _tap,
)
from replayer.locator import ElementLocator

# Module logger
logger = get_logger("android")

# Direction to coordinate offsets (relative to screen center)
DIRECTION_OFFSETS = {
    "up": (0, -0.3),
    "down": (0, 0.3),
    "left": (-0.3, 0),
    "right": (0.3, 0),
}

# Default confidence threshold for element matching
DEFAULT_CONFIDENCE_THRESHOLD = 0.3


class Android:
    """
    High-level Android device control interface.

    Provides intuitive methods for controlling Android devices via ADB.
    Supports both coordinate-based and element-based interactions.
    Uses confidence scoring for robust element matching.
    """

    def __init__(
        self,
        device: Optional[str] = None,
        min_confidence: float = DEFAULT_CONFIDENCE_THRESHOLD,
    ):
        """
        Initialize Android controller.

        Args:
            device: Device serial number. If None, auto-detects first device.
            min_confidence: Minimum confidence threshold for element matching (0.0-1.0).
                          Default is 0.3 (30%). Higher values require stricter matches.

        Raises:
            DeviceNotFoundError: If no device is connected.
        """
        self.device = device or get_device_serial()
        if not self.device:
            raise DeviceNotFoundError("No Android device connected")

        self._screen_size: Optional[Tuple[int, int]] = None
        self._min_confidence = min_confidence
        self._locator = ElementLocator(filter_ads=True, min_confidence=min_confidence)

        logger.info(f"Connected to device: {self.device}")

    @property
    def min_confidence(self) -> float:
        """Get the minimum confidence threshold."""
        return self._min_confidence

    @min_confidence.setter
    def min_confidence(self, value: float) -> None:
        """Set the minimum confidence threshold (0.0-1.0)."""
        self._min_confidence = max(0.0, min(1.0, value))
        self._locator.min_confidence = self._min_confidence

    # =========================================================================
    # Gesture Methods
    # =========================================================================

    def tap(
        self,
        x_or_text: Optional[Union[int, str]] = None,
        y: Optional[int] = None,
        *,
        id: Optional[str] = None,
        desc: Optional[str] = None,
        timeout: float = 5.0,
        min_confidence: Optional[float] = None,
    ) -> bool:
        """
        Tap at coordinates or on an element.

        Args:
            x_or_text: X coordinate (int) or element text (str)
            y: Y coordinate (required if x_or_text is int)
            id: Find element by resource-id
            desc: Find element by content-description
            timeout: Timeout for element search in seconds
            min_confidence: Minimum confidence threshold (0.0-1.0), overrides default

        Returns:
            True if tap was successful

        Examples:
            android.tap(100, 200)           # Tap at coordinates
            android.tap("Login")            # Tap element with text "Login"
            android.tap(id="btn_submit")    # Tap element by ID
        """
        coords = self._resolve_target(
            x_or_text, y, id=id, desc=desc, timeout=timeout, min_confidence=min_confidence
        )
        if coords:
            return _tap(coords[0], coords[1])
        return False

    def long_press(
        self,
        x_or_text: Optional[Union[int, str]] = None,
        y: Optional[int] = None,
        *,
        id: Optional[str] = None,
        desc: Optional[str] = None,
        duration_ms: int = 1000,
        timeout: float = 5.0,
        min_confidence: Optional[float] = None,
    ) -> bool:
        """
        Long press at coordinates or on an element.

        Args:
            x_or_text: X coordinate (int) or element text (str)
            y: Y coordinate (required if x_or_text is int)
            id: Find element by resource-id
            desc: Find element by content-description
            duration_ms: Press duration in milliseconds
            timeout: Timeout for element search in seconds
            min_confidence: Minimum confidence threshold (0.0-1.0), overrides default

        Returns:
            True if long press was successful
        """
        coords = self._resolve_target(
            x_or_text, y, id=id, desc=desc, timeout=timeout, min_confidence=min_confidence
        )
        if coords:
            return _long_press(coords[0], coords[1], duration_ms)
        return False

    def swipe(
        self,
        x1_or_direction: Union[int, str],
        y1: Optional[int] = None,
        x2: Optional[int] = None,
        y2: Optional[int] = None,
        duration_ms: int = 300,
    ) -> bool:
        """
        Swipe by coordinates or direction.

        Args:
            x1_or_direction: Start X (int) or direction ("up", "down", "left", "right")
            y1: Start Y coordinate
            x2: End X coordinate
            y2: End Y coordinate
            duration_ms: Swipe duration in milliseconds

        Returns:
            True if swipe was successful

        Examples:
            android.swipe("up")                    # Swipe up (center of screen)
            android.swipe("down")                  # Swipe down
            android.swipe(100, 500, 100, 200)      # Swipe from (100,500) to (100,200)
        """
        if isinstance(x1_or_direction, str):
            # Direction-based swipe
            direction = x1_or_direction.lower()
            if direction not in DIRECTION_OFFSETS:
                logger.error(f"Invalid swipe direction: {direction}")
                return False

            width, height = self.screen_size()
            center_x, center_y = width // 2, height // 2

            offset_x, offset_y = DIRECTION_OFFSETS[direction]
            start_x = center_x
            start_y = center_y
            end_x = int(center_x + offset_x * width)
            end_y = int(center_y + offset_y * height)

            return _swipe(start_x, start_y, end_x, end_y, duration_ms)
        else:
            # Coordinate-based swipe
            if y1 is None or x2 is None or y2 is None:
                logger.error("Coordinate swipe requires all 4 coordinates")
                return False
            return _swipe(x1_or_direction, y1, x2, y2, duration_ms)

    def scroll(
        self,
        direction: str = "down",
        distance: float = 0.5,
        duration_ms: int = 500,
    ) -> bool:
        """
        Scroll in a direction.

        Args:
            direction: "up", "down", "left", or "right"
            distance: Scroll distance as fraction of screen (0.0-1.0)
            duration_ms: Scroll duration in milliseconds

        Returns:
            True if scroll was successful
        """
        direction = direction.lower()
        if direction not in DIRECTION_OFFSETS:
            logger.error(f"Invalid scroll direction: {direction}")
            return False

        width, height = self.screen_size()
        center_x, center_y = width // 2, height // 2

        # Calculate scroll distance
        distance = max(0.1, min(0.9, distance))  # Clamp to reasonable range

        if direction in ("up", "down"):
            delta = int(height * distance)
            if direction == "up":
                return _scroll(
                    center_x, center_y + delta // 2, center_x, center_y - delta // 2, duration_ms
                )
            else:
                return _scroll(
                    center_x, center_y - delta // 2, center_x, center_y + delta // 2, duration_ms
                )
        else:
            delta = int(width * distance)
            if direction == "left":
                return _scroll(
                    center_x + delta // 2, center_y, center_x - delta // 2, center_y, duration_ms
                )
            else:
                return _scroll(
                    center_x - delta // 2, center_y, center_x + delta // 2, center_y, duration_ms
                )

    def pinch(
        self,
        scale: float = 0.5,
        center_x: Optional[int] = None,
        center_y: Optional[int] = None,
        duration_ms: int = 500,
    ) -> bool:
        """
        Pinch gesture (zoom in/out).

        Args:
            scale: Scale factor (>1 zoom in, <1 zoom out)
            center_x: Center X of pinch (default: screen center)
            center_y: Center Y of pinch (default: screen center)
            duration_ms: Gesture duration

        Returns:
            True if pinch was successful

        Note:
            This is an approximation using sequential swipes.
            For accurate pinch, use sendevent-based implementation.
        """
        if center_x is None or center_y is None:
            width, height = self.screen_size()
            center_x = center_x or width // 2
            center_y = center_y or height // 2

        return _pinch(center_x, center_y, scale, duration_ms)

    # =========================================================================
    # Input Methods
    # =========================================================================

    def type(self, text: str, clear_first: bool = False) -> bool:
        """
        Type text string.

        Args:
            text: Text to type
            clear_first: Clear existing text before typing

        Returns:
            True if typing was successful
        """
        return _input_text(text, clear_first=clear_first)

    def press_home(self) -> bool:
        """Press home button."""
        return _press_home()

    def press_back(self) -> bool:
        """Press back button."""
        return _press_back()

    def press_enter(self) -> bool:
        """Press enter key."""
        return _press_enter()

    def press_key(self, keycode: str) -> bool:
        """
        Press a key by keycode.

        Args:
            keycode: Android keycode (e.g., "KEYCODE_VOLUME_UP")

        Returns:
            True if key press was successful

        Common keycodes:
            KEYCODE_HOME, KEYCODE_BACK, KEYCODE_MENU, KEYCODE_ENTER,
            KEYCODE_DEL, KEYCODE_VOLUME_UP, KEYCODE_VOLUME_DOWN
        """
        return _press_key(keycode)

    # =========================================================================
    # App Methods
    # =========================================================================

    def open_app(self, app: str) -> bool:
        """
        Open an app by name or package.

        Args:
            app: App name (e.g., "Chrome") or package (e.g., "com.android.chrome")

        Returns:
            True if app launch was initiated
        """
        try:
            if "." in app and " " not in app:
                # Looks like a package name
                package = app
            else:
                # Try to find package by app name
                package = self._find_package_by_name(app)
                if not package:
                    logger.warning(f"Could not find package for '{app}', trying as package name")
                    package = app

            # Launch with monkey tool (reliable for starting apps)
            run_adb(
                ["shell", "monkey", "-p", package, "-c", "android.intent.category.LAUNCHER", "1"]
            )
            logger.info(f"Launched app: {package}")
            return True
        except Exception as e:
            logger.error(f"Failed to open app: {e}")
            return False

    def current_app(self) -> Dict[str, str]:
        """
        Get current foreground app info.

        Returns:
            Dict with 'package' and 'activity' keys
        """
        package, activity = get_current_app()
        return {"package": package, "activity": activity}

    def _find_package_by_name(self, name: str) -> Optional[str]:
        """Find package name by app name from installed packages."""
        try:
            output = run_adb(["shell", "pm", "list", "packages", "-f"])
            name_lower = name.lower().replace(" ", "")

            for line in output.strip().split("\n"):
                if "=" in line:
                    # Format: package:/data/app/com.app.name-xxx/base.apk=com.app.name
                    package = line.split("=")[-1].strip()
                    # Check if app name matches package name
                    package_simple = package.split(".")[-1].lower()
                    if name_lower in package_simple or package_simple in name_lower:
                        return package

            # Fallback: check for common app packages
            common_apps = {
                "chrome": "com.android.chrome",
                "settings": "com.android.settings",
                "camera": "com.android.camera",
                "phone": "com.android.dialer",
                "messages": "com.android.messaging",
                "gmail": "com.google.android.gm",
                "youtube": "com.google.android.youtube",
                "maps": "com.google.android.apps.maps",
                "play store": "com.android.vending",
                "calculator": "com.android.calculator2",
                "clock": "com.android.deskclock",
                "calendar": "com.android.calendar",
                "contacts": "com.android.contacts",
                "files": "com.android.documentsui",
            }
            return common_apps.get(name_lower)
        except Exception as e:
            logger.debug(f"Error finding package: {e}")
            return None

    # =========================================================================
    # Screen Methods
    # =========================================================================

    def screenshot(self, filename: Optional[str] = None) -> str:
        """
        Take a screenshot.

        Args:
            filename: Output filename (default: screenshot_<timestamp>.png)

        Returns:
            Path to saved screenshot
        """
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"

        # Ensure .png extension
        if not filename.lower().endswith(".png"):
            filename += ".png"

        # Capture screenshot on device and pull
        device_path = "/sdcard/screenshot_tmp.png"
        try:
            run_adb(["shell", "screencap", "-p", device_path])
            run_adb(["pull", device_path, filename])
            run_adb(["shell", "rm", device_path])
            logger.info(f"Screenshot saved: {filename}")
            return os.path.abspath(filename)
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            raise

    def screen_size(self) -> Tuple[int, int]:
        """
        Get screen size.

        Returns:
            Tuple of (width, height) in pixels
        """
        if self._screen_size is None:
            self._screen_size = get_screen_size()
        return self._screen_size

    # =========================================================================
    # Element Methods (with Confidence Scoring)
    # =========================================================================

    def find(
        self,
        text: Optional[str] = None,
        *,
        id: Optional[str] = None,
        desc: Optional[str] = None,
        timeout: float = 0,
        min_confidence: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Find an element on screen using confidence scoring.

        Args:
            text: Find by visible text (fuzzy matching supported)
            id: Find by resource-id (partial match supported)
            desc: Find by content-description (fuzzy matching supported)
            timeout: Timeout in seconds (0 = single attempt)
            min_confidence: Minimum confidence threshold (0.0-1.0), overrides default

        Returns:
            Element dict with properties like 'bounds', 'text', 'resource_id', etc.
            None if no match above confidence threshold.
        """
        result = self._find_element_with_confidence(
            text=text, id=id, desc=desc, timeout=timeout, min_confidence=min_confidence
        )
        return result.element if result else None

    def find_with_confidence(
        self,
        text: Optional[str] = None,
        *,
        id: Optional[str] = None,
        desc: Optional[str] = None,
        timeout: float = 0,
        min_confidence: Optional[float] = None,
    ) -> Optional[MatchResult]:
        """
        Find an element with detailed confidence information.

        Args:
            text: Find by visible text
            id: Find by resource-id
            desc: Find by content-description
            timeout: Timeout in seconds
            min_confidence: Minimum confidence threshold

        Returns:
            MatchResult with element, confidence score, and match details.
            None if no match above threshold.

        Example:
            result = android.find_with_confidence("Login")
            if result:
                print(f"Found with {result.confidence:.0%} confidence")
                print(f"Match details: {result.match_details}")
        """
        return self._find_element_with_confidence(
            text=text, id=id, desc=desc, timeout=timeout, min_confidence=min_confidence
        )

    def find_all(
        self,
        text: Optional[str] = None,
        *,
        id: Optional[str] = None,
        desc: Optional[str] = None,
        class_name: Optional[str] = None,
        min_confidence: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find all matching elements using confidence scoring.

        Args:
            text: Find by visible text
            id: Find by resource-id
            desc: Find by content-description
            class_name: Find by class name
            min_confidence: Minimum confidence threshold

        Returns:
            List of matching element dicts, sorted by confidence (highest first)
        """
        results = self.find_all_with_confidence(
            text=text, id=id, desc=desc, class_name=class_name, min_confidence=min_confidence
        )
        return [r.element for r in results]

    def find_all_with_confidence(
        self,
        text: Optional[str] = None,
        *,
        id: Optional[str] = None,
        desc: Optional[str] = None,
        class_name: Optional[str] = None,
        min_confidence: Optional[float] = None,
    ) -> List[MatchResult]:
        """
        Find all matching elements with confidence scores.

        Args:
            text: Find by visible text
            id: Find by resource-id
            desc: Find by content-description
            class_name: Find by class name
            min_confidence: Minimum confidence threshold

        Returns:
            List of MatchResult sorted by confidence (highest first)

        Example:
            results = android.find_all_with_confidence("Item")
            for r in results:
                print(f"{r.element['text']}: {r.confidence:.0%}")
        """
        threshold = min_confidence if min_confidence is not None else self._min_confidence
        _, elements = capture_ui_fast()

        results = find_elements_with_confidence(
            elements,
            text=text,
            resource_id=id,
            content_desc=desc,
            class_name=class_name,
            min_confidence=threshold,
            filter_ads=True,
        )

        return results

    def wait_for(
        self,
        text: Optional[str] = None,
        *,
        id: Optional[str] = None,
        desc: Optional[str] = None,
        timeout: float = 10.0,
        poll_interval: float = 0.5,
        min_confidence: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Wait for an element to appear using confidence scoring.

        Args:
            text: Find by visible text
            id: Find by resource-id
            desc: Find by content-description
            timeout: Max time to wait in seconds
            poll_interval: Time between checks in seconds
            min_confidence: Minimum confidence threshold

        Returns:
            Element dict if found, None if timeout
        """
        result = self._find_element_with_confidence(
            text=text,
            id=id,
            desc=desc,
            timeout=timeout,
            poll_interval=poll_interval,
            min_confidence=min_confidence,
        )
        return result.element if result else None

    def wait_for_with_confidence(
        self,
        text: Optional[str] = None,
        *,
        id: Optional[str] = None,
        desc: Optional[str] = None,
        timeout: float = 10.0,
        poll_interval: float = 0.5,
        min_confidence: Optional[float] = None,
    ) -> Optional[MatchResult]:
        """
        Wait for an element with confidence information.

        Args:
            text: Find by visible text
            id: Find by resource-id
            desc: Find by content-description
            timeout: Max time to wait in seconds
            poll_interval: Time between checks in seconds
            min_confidence: Minimum confidence threshold

        Returns:
            MatchResult if found, None if timeout
        """
        return self._find_element_with_confidence(
            text=text,
            id=id,
            desc=desc,
            timeout=timeout,
            poll_interval=poll_interval,
            min_confidence=min_confidence,
        )

    def exists(
        self,
        text: Optional[str] = None,
        *,
        id: Optional[str] = None,
        desc: Optional[str] = None,
        min_confidence: Optional[float] = None,
    ) -> bool:
        """
        Check if an element exists on screen.

        Args:
            text: Find by visible text
            id: Find by resource-id
            desc: Find by content-description
            min_confidence: Minimum confidence threshold

        Returns:
            True if element exists above confidence threshold
        """
        result = self._find_element_with_confidence(
            text=text, id=id, desc=desc, timeout=0, min_confidence=min_confidence
        )
        return result is not None

    def get_confidence(
        self,
        text: Optional[str] = None,
        *,
        id: Optional[str] = None,
        desc: Optional[str] = None,
    ) -> float:
        """
        Get the confidence score for an element match.

        Args:
            text: Find by visible text
            id: Find by resource-id
            desc: Find by content-description

        Returns:
            Confidence score (0.0-1.0), or 0.0 if not found
        """
        result = self._find_element_with_confidence(
            text=text, id=id, desc=desc, timeout=0, min_confidence=0.0  # Get any match
        )
        return result.confidence if result else 0.0

    # =========================================================================
    # Device Methods
    # =========================================================================

    def devices(self) -> List[Dict[str, str]]:
        """
        List all connected devices.

        Returns:
            List of dicts with 'serial' and 'status' keys
        """
        return get_connected_devices()

    def info(self) -> Dict[str, Any]:
        """
        Get device information.

        Returns:
            Dict with device properties
        """
        info = {
            "serial": self.device,
            "screen_size": self.screen_size(),
        }

        try:
            # Get additional device info
            info["model"] = run_adb(["shell", "getprop", "ro.product.model"]).strip()
            info["android_version"] = run_adb(
                ["shell", "getprop", "ro.build.version.release"]
            ).strip()
            info["sdk_version"] = run_adb(["shell", "getprop", "ro.build.version.sdk"]).strip()
            info["manufacturer"] = run_adb(["shell", "getprop", "ro.product.manufacturer"]).strip()
        except Exception as e:
            logger.debug(f"Could not get all device info: {e}")

        return info

    # =========================================================================
    # Internal Methods
    # =========================================================================

    def _resolve_target(
        self,
        x_or_text: Optional[Union[int, str]],
        y: Optional[int],
        *,
        id: Optional[str] = None,
        desc: Optional[str] = None,
        timeout: float = 5.0,
        min_confidence: Optional[float] = None,
    ) -> Optional[Tuple[int, int]]:
        """
        Resolve tap target to coordinates using confidence scoring.

        Returns coordinates from either:
        - Direct coordinates (x, y)
        - Element lookup (text, id, or desc) with confidence scoring
        """
        # Check if using element-based targeting
        if id or desc or isinstance(x_or_text, str):
            result = self._find_element_with_confidence(
                text=x_or_text if isinstance(x_or_text, str) else None,
                id=id,
                desc=desc,
                timeout=timeout,
                min_confidence=min_confidence,
            )
            if result:
                logger.debug(f"Found element with {result.confidence:.0%} confidence")
                return get_center(result.element["bounds"])
            else:
                locator_desc = id or desc or x_or_text
                logger.error(f"Element not found: {locator_desc}")
                return None

        # Coordinate-based
        if isinstance(x_or_text, int) and y is not None:
            return (x_or_text, y)

        logger.error("Invalid target: provide coordinates (x, y) or element identifier")
        return None

    def _find_element_with_confidence(
        self,
        text: Optional[str] = None,
        id: Optional[str] = None,
        desc: Optional[str] = None,
        timeout: float = 0,
        poll_interval: float = 0.5,
        min_confidence: Optional[float] = None,
    ) -> Optional[MatchResult]:
        """
        Find element using confidence scoring with optional polling.

        Returns the best match above the confidence threshold.
        """
        threshold = min_confidence if min_confidence is not None else self._min_confidence
        start_time = time.time()
        best_result: Optional[MatchResult] = None
        best_confidence = 0.0

        while True:
            _, elements = capture_ui_fast()

            # Use confidence scoring to find best match
            result = find_best_match(
                elements,
                text=text,
                resource_id=id,
                content_desc=desc,
                min_confidence=threshold,
                filter_ads=True,
            )

            if result:
                # If high confidence match, return immediately
                if result.confidence >= 0.9:
                    logger.debug(f"Found with {result.confidence:.0%} confidence (excellent)")
                    return result

                # Track best result so far
                if result.confidence > best_confidence:
                    best_confidence = result.confidence
                    best_result = result

            # Check timeout
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                break

            # Poll again after interval
            time.sleep(poll_interval)

        if best_result:
            logger.debug(f"Best match: {best_result.confidence:.0%} confidence")

        return best_result

    def __repr__(self) -> str:
        return f"Android(device='{self.device}', min_confidence={self._min_confidence:.0%})"
