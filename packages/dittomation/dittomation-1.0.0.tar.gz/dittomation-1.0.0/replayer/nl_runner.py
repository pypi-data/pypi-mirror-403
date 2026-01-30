"""
Natural Language Workflow Runner

Converts natural language descriptions into executable Android actions.

Usage:
    python nl_runner.py "Open Phone app, tap on Contacts, scroll down"
    python nl_runner.py --file instructions.txt
    python nl_runner.py --interactive

Examples:
    "Open the Settings app"
    "Tap on Phone and then tap Contacts"
    "Scroll down and click on John"
    "Go back to home screen"
    "Type hello world in the search box"
    "Long press on the Chrome icon"
    "Call 1234567890, wait 10 seconds, end call"
    "Open YouTube, search for cats, play first video"

Clipboard/State Support:
    "Open Phone, copy last number I called, go home, open YouTube, search for that number you copied"
    - "copy last number I called" - finds and stores first phone number on screen
    - "copy the number" - copies visible phone number
    - "search for that number you copied" - uses stored clipboard value
    - "search for it" - uses clipboard value
"""

import argparse
import os
import re
import sys
import time
from typing import Dict, List, Optional, Tuple

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ad_filter import get_ad_filter
from core.logging_config import get_logger
from recorder.adb_wrapper import check_device_connected, get_screen_size, wait_for_device
from recorder.ui_dumper import capture_ui_fast, get_center
from replayer.executor import (
    dial_number,
    end_call,
    input_text,
    long_press,
    make_call,
    press_back,
    press_home,
    press_key,
    swipe,
    tap,
)

# Module logger
logger = get_logger("nl_runner")


# UI Element Detection Constants
MIN_CLICKABLE_AREA_PX = 5000  # Minimum area for clickable elements
MIN_LINK_WIDTH_PX = 100  # Minimum width for search result links
MIN_LINK_HEIGHT_PX = 30  # Minimum height for search result links
MIN_VIDEO_WIDTH_PX = 200  # Minimum width for video thumbnails

# Layout Constants
NAVBAR_HEIGHT_PX = 300  # Height of navigation bar area to skip
BOTTOM_SWIPE_MARGIN_PX = 200  # Margin from bottom for swipe gestures

# Gesture Distance Constants
SCROLL_DISTANCE_PX = 600  # Distance for scroll gestures
SWIPE_DISTANCE_PX = 400  # Distance for swipe gestures
SCROLL_TO_DISTANCE_PX = 800  # Distance for scrolling to top/bottom
DEFAULT_SWIPE_DISTANCE_PX = 500  # Default swipe distance

# Gesture Duration Constants
SCROLL_DURATION_MS = 400  # Duration for scroll gestures
SWIPE_DURATION_MS = 200  # Duration for swipe gestures
SCROLL_TO_DURATION_MS = 300  # Duration for scroll to top/bottom
APP_DRAWER_SWIPE_DURATION_MS = 300  # Duration for opening app drawer

# Video Detection Constants
VIDEO_ASPECT_RATIO_MIN = 1.3  # Minimum aspect ratio for video thumbnails (wider than tall)
SQUARE_ASPECT_RATIO_MIN = 0.8  # Lower bound for square aspect ratio
SQUARE_ASPECT_RATIO_MAX = 1.2  # Upper bound for square aspect ratio
MAX_AVATAR_AREA_PX = 50000  # Maximum area for channel avatars

# Default Values
DEFAULT_SCREEN_WIDTH = 1080
DEFAULT_SCREEN_HEIGHT = 2400
DEFAULT_ACTION_DELAY_MS = 800  # Default delay between actions


class NaturalLanguageRunner:
    """Converts natural language to Android actions and executes them."""

    def __init__(self, delay_ms: int = DEFAULT_ACTION_DELAY_MS, verbose: bool = False):
        self.delay_ms = delay_ms
        self.verbose = verbose
        self.screen_width = DEFAULT_SCREEN_WIDTH
        self.screen_height = DEFAULT_SCREEN_HEIGHT

        # Clipboard/state storage for "copy" and "paste" operations
        self.clipboard = None
        self.last_copied_type = None  # 'number', 'text', etc.

        # Common app name to package/intent mapping for direct launch
        self.app_intents = {
            "clock": "android.intent.action.SHOW_ALARMS",
            "alarm": "android.intent.action.SHOW_ALARMS",
            "timer": "android.intent.action.SHOW_TIMERS",
            "calendar": "android.intent.action.MAIN -c android.intent.category.APP_CALENDAR",
            "camera": "android.media.action.IMAGE_CAPTURE",
            "browser": "android.intent.action.VIEW -d https://google.com",
            "chrome": "android.intent.action.VIEW -d https://google.com -p com.android.chrome",
            "settings": "android.settings.SETTINGS",
            "wifi": "android.settings.WIFI_SETTINGS",
            "bluetooth": "android.settings.BLUETOOTH_SETTINGS",
            "contacts": "android.intent.action.MAIN -c android.intent.category.APP_CONTACTS",
            "messages": "android.intent.action.MAIN -c android.intent.category.APP_MESSAGING",
            "sms": "android.intent.action.MAIN -c android.intent.category.APP_MESSAGING",
            "email": "android.intent.action.MAIN -c android.intent.category.APP_EMAIL",
            "maps": "android.intent.action.VIEW -d geo:0,0",
            "music": "android.intent.action.MAIN -c android.intent.category.APP_MUSIC",
            "gallery": "android.intent.action.MAIN -c android.intent.category.APP_GALLERY",
            "photos": "android.intent.action.MAIN -c android.intent.category.APP_GALLERY",
            "calculator": "android.intent.action.MAIN -c android.intent.category.APP_CALCULATOR",
            "files": "android.intent.action.MAIN -c android.intent.category.APP_FILES",
            "phone": "android.intent.action.DIAL",
            "dialer": "android.intent.action.DIAL",
            "youtube": "android.intent.action.VIEW -d https://youtube.com -p com.google.android.youtube",
        }

        # Action patterns (order matters - more specific first)
        self.patterns = [
            # Call actions
            (
                r'\b(?:make\s+a\s+)?call\s+(?:to\s+)?(?:number\s+)?["\']?(\+?[\d\s\-]+)["\']?',
                self._action_call,
            ),
            (r'\bcall\s+["\']?(\+?[\d\s\-]+)["\']?', self._action_call),
            (r'\bdial\s+["\']?(\+?[\d\s\-]+)["\']?', self._action_dial),
            (r"\b(?:end|hang\s*up|disconnect|cut)(?:\s+the)?\s*(?:call)?\b", self._action_end_call),
            # Alarm actions
            (
                r"\bset\s+(?:an?\s+)?alarm\s+(?:for\s+)?(\d{1,2})[:\s]?(\d{2})?\s*(am|pm)?",
                self._action_set_alarm,
            ),
            (
                r"\bcreate\s+(?:an?\s+)?alarm\s+(?:for\s+)?(\d{1,2})[:\s]?(\d{2})?\s*(am|pm)?",
                self._action_set_alarm,
            ),
            (r"\balarm\s+(?:at\s+)?(\d{1,2})[:\s]?(\d{2})?\s*(am|pm)?", self._action_set_alarm),
            # Copy actions - copy text/number from screen
            (
                r"\bcopy\s+(?:the\s+)?last\s+(?:number\s+)?(?:i\s+)?called",
                self._action_copy_last_called,
            ),
            (
                r"\bcopy\s+(?:the\s+)?(?:last\s+)?(?:dialed|called)\s+number",
                self._action_copy_last_called,
            ),
            (r"\bcopy\s+(?:the\s+)?(?:phone\s+)?number", self._action_copy_number),
            (r'\bcopy\s+(?:the\s+)?text\s+(?:from\s+)?["\']?(.+?)["\']?', self._action_copy_text),
            (r'\bcopy\s+["\']?(.+?)["\']?', self._action_copy_element),
            # Navigate to URL
            (
                r'\b(?:go\s+to|open|navigate\s+to|visit)\s+(?:url\s+)?["\']?(https?://\S+)["\']?',
                self._action_goto_url,
            ),
            (
                r'\b(?:go\s+to|open|navigate\s+to|visit)\s+(?:url\s+)?["\']?(www\.\S+)["\']?',
                self._action_goto_url,
            ),
            (
                r'\b(?:go\s+to|open|navigate\s+to|visit)\s+(?:url\s+)?["\']?(\S+\.(com|org|net|io|dev|app)\S*)["\']?',
                self._action_goto_url,
            ),
            # Back/Home
            (r"\b(go\s+)?back\b", self._action_back),
            (r"\b(go\s+)?(to\s+)?home(\s+screen)?\b", self._action_home),
            (r"\bpress\s+(the\s+)?back(\s+button)?\b", self._action_back),
            (r"\bpress\s+(the\s+)?home(\s+button)?\b", self._action_home),
            # Scroll/Swipe
            (r"\bscroll\s+(up|down|left|right)\b", self._action_scroll),
            (r"\bswipe\s+(up|down|left|right)\b", self._action_swipe),
            (r"\bscroll\s+to\s+(top|bottom)\b", self._action_scroll_to),
            # Wait
            (r"\bwait\s+(\d+)\s*(s|sec|seconds?)?\b", self._action_wait),
            (r"\bpause\s+(\d+)\s*(s|sec|seconds?)?\b", self._action_wait),
            # App search (open app drawer and search)
            (
                r'\bsearch\s+(?:for\s+)?(?:the\s+)?["\']?(.+?)["\']?\s*(?:app)\b',
                self._action_search_app,
            ),
            (r'\bfind\s+(?:the\s+)?["\']?(.+?)["\']?\s*(?:app)\b', self._action_search_app),
            (
                r'\bopen\s+app\s+drawer\s+(?:and\s+)?search\s+(?:for\s+)?["\']?(.+?)["\']?',
                self._action_search_app,
            ),
            # Search (tap search, type, submit)
            (r'\bsearch\s+(?:for\s+)?["\']?(.+?)["\']?\s*$', self._action_search),
            # Filter/Sort
            (r"\bfilter\s+(?:by|for)\s+(.+)", self._action_filter),
            (r"\bsort\s+(?:by\s+)?(.+)", self._action_filter),
            # Play/Click first/top/latest result
            (
                r"\bplay\s+(?:the\s+)?(?:first|top|latest|newest|most\s+recent|most\s+watched|most\s+viewed)(?:\s+video)?",
                self._action_play_first,
            ),
            (
                r"\b(?:click|tap|select|open)\s+(?:the\s+)?(?:first|top|latest|newest)(?:\s+result|\s+video|\s+item|\s+link|\s+url)?",
                self._action_click_first_result,
            ),
            (
                r"\bopen\s+(?:the\s+)?(?:first|latest)(?:\s+result|\s+link|\s+url)?",
                self._action_click_first_result,
            ),
            # Type/Input text
            (r'\btype\s+["\'](.+?)["\']', self._action_type),
            (r"\btype\s+(.+?)(?:\s+in|\s+into|$)", self._action_type),
            (r'\benter\s+["\'](.+?)["\']', self._action_type),
            (r'\binput\s+["\'](.+?)["\']', self._action_type),
            # Long press
            (
                r'\blong\s*press\s+(?:on\s+)?(?:the\s+)?["\']?(.+?)["\']?(?:\s+icon|\s+button|\s+app)?(?:\s|$)',
                self._action_long_press,
            ),
            (
                r'\bpress\s+and\s+hold\s+(?:on\s+)?(?:the\s+)?["\']?(.+?)["\']?(?:\s|$)',
                self._action_long_press,
            ),
            (r'\bhold\s+(?:on\s+)?(?:the\s+)?["\']?(.+?)["\']?(?:\s|$)', self._action_long_press),
            # Tap/Click/Open (most general - last)
            (
                r'\b(?:tap|click|press|select)\s+(?:on\s+)?(?:the\s+)?["\']?(.+?)["\']?(?:\s+icon|\s+button|\s+app)?(?:\s|$)',
                self._action_tap,
            ),
            (r'\bopen\s+(?:the\s+)?["\']?(.+?)["\']?(?:\s+app)?(?:\s|$)', self._action_tap),
            (r'\blaunch\s+(?:the\s+)?["\']?(.+?)["\']?(?:\s+app)?(?:\s|$)', self._action_tap),
            (r'\bgo\s+to\s+["\']?(.+?)["\']?(?:\s|$)', self._action_tap),
        ]

    def _find_element(
        self, target: str, elements: List[Dict], filter_ads: bool = True
    ) -> Optional[Dict]:
        """Find element by text, content-desc, or resource-id, optionally filtering ads."""
        target_lower = target.lower().strip()

        # Remove common suffixes
        target_clean = re.sub(r"\s*(app|icon|button|option|menu|item)$", "", target_lower).strip()

        # Get ad filter if enabled
        ad_filter = get_ad_filter() if filter_ads else None

        candidates = []

        # First pass: look for exact matches (can return immediately)
        for elem in elements:
            if not (elem.get("clickable") or elem.get("long_clickable") or elem.get("focusable")):
                continue

            # Skip ad elements
            if ad_filter and ad_filter.is_ad(elem):
                continue

            text = elem.get("text", "").lower()
            desc = elem.get("content_desc", "").lower()
            rid = elem.get("resource_id", "").split("/")[-1].lower()

            # Skip URL bars and address fields - they contain URLs that shouldn't match
            if any(skip in rid for skip in ["url", "address", "omnibox", "location_bar"]):
                continue
            # Skip if text looks like a URL
            if (
                text.startswith("http")
                or text.startswith("www.")
                or ".com/" in text
                or ".org/" in text
            ):
                continue

            # Exact matches (highest priority) - return immediately
            if text == target_clean or text == target_lower:
                return elem
            if desc == target_clean or desc == target_lower:
                return elem
            if rid == target_clean or rid == target_lower:
                return elem

        # Second pass: look for partial matches
        for elem in elements:
            if not (elem.get("clickable") or elem.get("long_clickable") or elem.get("focusable")):
                continue

            # Skip ad elements
            if ad_filter and ad_filter.is_ad(elem):
                continue

            text = elem.get("text", "").lower()
            desc = elem.get("content_desc", "").lower()
            rid = elem.get("resource_id", "").split("/")[-1].lower()

            # Skip URL-related elements
            if any(skip in rid for skip in ["url", "address", "omnibox", "location_bar"]):
                continue
            if (
                text.startswith("http")
                or text.startswith("www.")
                or ".com/" in text
                or ".org/" in text
            ):
                continue

            # Partial matches
            score = 0
            if target_clean in text:
                score = 10 + (10 if text.startswith(target_clean) else 0)
            elif target_clean in desc:
                score = 8 + (8 if desc.startswith(target_clean) else 0)
            elif target_clean in rid:
                score = 5

            if score > 0:
                candidates.append((score, elem))

        # Return best match
        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            return candidates[0][1]

        return None

    def _get_swipe_coords(
        self, direction: str, distance: int = DEFAULT_SWIPE_DISTANCE_PX
    ) -> Tuple[int, int, int, int]:
        """Get swipe coordinates for direction."""
        cx, cy = self.screen_width // 2, self.screen_height // 2

        if direction == "up":
            return cx, cy + distance, cx, cy - distance
        elif direction == "down":
            return cx, cy - distance, cx, cy + distance
        elif direction == "left":
            return cx + distance, cy, cx - distance, cy
        elif direction == "right":
            return cx - distance, cy, cx + distance, cy
        return cx, cy, cx, cy

    def _launch_app_by_intent(self, app_name: str) -> Tuple[bool, str]:
        """Try to launch app using Android intent."""
        app_lower = app_name.lower().strip()

        # Check if we have a known intent for this app
        if app_lower in self.app_intents:
            intent = self.app_intents[app_lower]
            from recorder.adb_wrapper import run_adb

            try:
                cmd = ["shell", "am", "start", "-a"] + intent.split()
                run_adb(cmd)
                time.sleep(1.5)
                return True, f"Opened {app_name} app"
            except Exception as e:
                return False, f"Failed to launch {app_name}: {e}"

        return False, f"No intent mapping for '{app_name}'"

    # Action handlers
    def _action_tap(self, match, elements) -> Tuple[bool, str]:
        target = match.group(1).strip()
        elem = self._find_element(target, elements)
        if elem:
            x, y = get_center(elem["bounds"])
            name = (
                elem.get("text")
                or elem.get("content_desc")
                or elem.get("resource_id", "").split("/")[-1]
            )
            tap(x, y)
            return True, f"Tapped '{name}' at ({x}, {y})"

        # Fallback: try to launch as an app using intent
        success, msg = self._launch_app_by_intent(target)
        if success:
            return success, msg

        return False, f"Could not find element '{target}'"

    def _action_long_press(self, match, elements) -> Tuple[bool, str]:
        target = match.group(1).strip()
        elem = self._find_element(target, elements)
        if elem:
            x, y = get_center(elem["bounds"])
            name = elem.get("text") or elem.get("content_desc") or "element"
            long_press(x, y, 1000)
            return True, f"Long pressed '{name}' at ({x}, {y})"
        return False, f"Could not find element '{target}'"

    def _action_scroll(self, match, elements) -> Tuple[bool, str]:
        direction = match.group(1).lower()
        x1, y1, x2, y2 = self._get_swipe_coords(direction, SCROLL_DISTANCE_PX)
        swipe(x1, y1, x2, y2, SCROLL_DURATION_MS)
        return True, f"Scrolled {direction}"

    def _action_swipe(self, match, elements) -> Tuple[bool, str]:
        direction = match.group(1).lower()
        x1, y1, x2, y2 = self._get_swipe_coords(direction, SWIPE_DISTANCE_PX)
        swipe(x1, y1, x2, y2, SWIPE_DURATION_MS)
        return True, f"Swiped {direction}"

    def _action_scroll_to(self, match, elements) -> Tuple[bool, str]:
        target = match.group(1).lower()
        direction = "up" if target == "top" else "down"
        for _ in range(5):  # Scroll multiple times
            x1, y1, x2, y2 = self._get_swipe_coords(direction, SCROLL_TO_DISTANCE_PX)
            swipe(x1, y1, x2, y2, SCROLL_TO_DURATION_MS)
            time.sleep(0.3)
        return True, f"Scrolled to {target}"

    def _action_back(self, match, elements) -> Tuple[bool, str]:
        press_back()
        return True, "Pressed back"

    def _action_home(self, match, elements) -> Tuple[bool, str]:
        press_home()
        return True, "Pressed home"

    def _action_wait(self, match, elements) -> Tuple[bool, str]:
        seconds = int(match.group(1))
        time.sleep(seconds)
        return True, f"Waited {seconds} seconds"

    def _action_type(self, match, elements) -> Tuple[bool, str]:
        text = match.group(1).strip()

        # Check for clipboard references
        clipboard_patterns = [
            r"\b(?:that|the)\s+(?:number|text)\s+(?:you|i)\s+copied\b",
            r"\b(?:the\s+)?copied\s+(?:number|text)\b",
            r"\bwhat\s+(?:you|i)\s+copied\b",
            r"\bthe\s+clipboard\b",
        ]

        for pattern in clipboard_patterns:
            if re.search(pattern, text.lower()):
                if self.clipboard:
                    text = self.clipboard
                    break
                else:
                    return False, "Nothing in clipboard to type"

        input_text(text)
        return True, f"Typed '{text}'"

    def _action_copy_last_called(self, match, elements) -> Tuple[bool, str]:
        """Copy the last called/dialed number from call history."""
        # Look for phone numbers on screen (in call log entries)
        # Phone numbers typically contain digits, possibly with +, -, spaces
        phone_pattern = re.compile(r"[\+]?[\d\s\-\(\)]{7,}")

        for elem in elements:
            text = elem.get("text", "")
            desc = elem.get("content_desc", "")

            # Check text field
            if text:
                match_num = phone_pattern.search(text)
                if match_num:
                    number = "".join(c for c in match_num.group() if c.isdigit() or c == "+")
                    if len(number) >= 7:  # Minimum phone number length
                        self.clipboard = number
                        self.last_copied_type = "number"
                        return True, f"Copied number: {number}"

            # Check content_desc
            if desc:
                match_num = phone_pattern.search(desc)
                if match_num:
                    number = "".join(c for c in match_num.group() if c.isdigit() or c == "+")
                    if len(number) >= 7:
                        self.clipboard = number
                        self.last_copied_type = "number"
                        return True, f"Copied number: {number}"

        # If no number found directly, try to tap on "Recents" tab first
        recents_elem = self._find_element("recents", elements) or self._find_element(
            "recent", elements
        )
        if recents_elem:
            x, y = get_center(recents_elem["bounds"])
            tap(x, y)
            time.sleep(1)

            # Re-capture UI
            _, elements = capture_ui_fast()

            # Try again to find a phone number
            for elem in elements:
                text = elem.get("text", "")
                if text:
                    match_num = phone_pattern.search(text)
                    if match_num:
                        number = "".join(c for c in match_num.group() if c.isdigit() or c == "+")
                        if len(number) >= 7:
                            self.clipboard = number
                            self.last_copied_type = "number"
                            return True, f"Copied number: {number}"

        return False, "Could not find a phone number to copy"

    def _action_copy_number(self, match, elements) -> Tuple[bool, str]:
        """Copy a phone number visible on screen."""
        phone_pattern = re.compile(r"[\+]?[\d\s\-\(\)]{7,}")

        for elem in elements:
            text = elem.get("text", "")
            desc = elem.get("content_desc", "")

            for content in [text, desc]:
                if content:
                    match_num = phone_pattern.search(content)
                    if match_num:
                        number = "".join(c for c in match_num.group() if c.isdigit() or c == "+")
                        if len(number) >= 7:
                            self.clipboard = number
                            self.last_copied_type = "number"
                            return True, f"Copied number: {number}"

        return False, "Could not find a phone number to copy"

    def _action_copy_text(self, match, elements) -> Tuple[bool, str]:
        """Copy text from a specific element."""
        target = match.group(1).strip() if match.lastindex else None

        if target:
            elem = self._find_element(target, elements)
            if elem:
                text = elem.get("text", "") or elem.get("content_desc", "")
                if text:
                    self.clipboard = text
                    self.last_copied_type = "text"
                    return True, f"Copied text: '{text}'"

        return False, f"Could not find text to copy from '{target}'"

    def _action_copy_element(self, match, elements) -> Tuple[bool, str]:
        """Copy text from an element found by name."""
        target = match.group(1).strip()

        elem = self._find_element(target, elements)
        if elem:
            text = elem.get("text", "") or elem.get("content_desc", "")
            if text:
                self.clipboard = text
                self.last_copied_type = "text"
                return True, f"Copied: '{text}'"
            else:
                return False, f"Element '{target}' has no text to copy"

        return False, f"Could not find element '{target}' to copy from"

    def _action_call(self, match, elements) -> Tuple[bool, str]:
        number = match.group(1).strip()
        number = "".join(c for c in number if c.isdigit() or c == "+")
        make_call(number)
        time.sleep(2)  # Wait for call UI to load
        return True, f"Calling {number}"

    def _action_dial(self, match, elements) -> Tuple[bool, str]:
        number = match.group(1).strip()
        number = "".join(c for c in number if c.isdigit() or c == "+")
        dial_number(number)
        return True, f"Opened dialer with {number}"

    def _action_end_call(self, match, elements) -> Tuple[bool, str]:
        end_call()
        return True, "Ended call"

    def _action_goto_url(self, match, elements) -> Tuple[bool, str]:
        """Navigate to a URL using Android intent."""
        url = match.group(1).strip()

        # Basic URL validation
        if not url:
            return False, "Empty URL provided"

        # Add https:// if no protocol
        if not url.startswith("http"):
            url = "https://" + url

        # Basic URL sanity check - must have a domain
        if not re.match(r"https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", url):
            return False, f"Invalid URL format: {url}"

        from recorder.adb_wrapper import run_adb

        try:
            run_adb(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", url])
            time.sleep(2)
            return True, f"Opened URL: {url}"
        except Exception as e:
            return False, f"Failed to open URL: {e}"

    def _action_set_alarm(self, match, elements) -> Tuple[bool, str]:
        """Set an alarm using Android intent."""
        hour = int(match.group(1))
        minutes = int(match.group(2)) if match.group(2) else 0
        ampm = match.group(3).lower() if match.group(3) else None

        # Convert to 24-hour format if AM/PM specified
        if ampm == "pm" and hour < 12:
            hour += 12
        elif ampm == "am" and hour == 12:
            hour = 0

        # Use Android SET_ALARM intent
        from recorder.adb_wrapper import run_adb

        try:
            run_adb(
                [
                    "shell",
                    "am",
                    "start",
                    "-a",
                    "android.intent.action.SET_ALARM",
                    "--ei",
                    "android.intent.extra.alarm.HOUR",
                    str(hour),
                    "--ei",
                    "android.intent.extra.alarm.MINUTES",
                    str(minutes),
                    "--ez",
                    "android.intent.extra.alarm.SKIP_UI",
                    "false",
                ]
            )
            time.sleep(2)

            # Try to save/confirm the alarm by looking for save/done button
            _, elements = capture_ui_fast()
            for elem in elements:
                if not elem.get("clickable"):
                    continue
                text = elem.get("text", "").lower()
                desc = elem.get("content_desc", "").lower()
                if any(
                    word in text or word in desc
                    for word in ["save", "done", "ok", "confirm", "set"]
                ):
                    x, y = get_center(elem["bounds"])
                    tap(x, y)
                    break

            time_str = f"{hour:02d}:{minutes:02d}"
            if ampm:
                time_str = f"{match.group(1)}:{minutes:02d} {ampm.upper()}"
            return True, f"Set alarm for {time_str}"
        except Exception as e:
            return False, f"Failed to set alarm: {e}"

    def _action_search_app(self, match, elements) -> Tuple[bool, str]:
        """Search for an app: go home, open app drawer, search."""
        app_name = match.group(1).strip()
        app_name_lower = app_name.lower()

        # Go to home screen first
        press_home()
        time.sleep(0.5)

        # Swipe up to open app drawer
        cx, cy = self.screen_width // 2, self.screen_height // 2
        swipe(
            cx,
            self.screen_height - BOTTOM_SWIPE_MARGIN_PX,
            cx,
            cy - SWIPE_DISTANCE_PX,
            APP_DRAWER_SWIPE_DURATION_MS,
        )
        time.sleep(1)

        # Capture UI to find search box in app drawer
        _, elements = capture_ui_fast()

        # Look for search box in app drawer
        search_elem = None
        search_keywords = ["search", "find", "apps", "search apps", "search_box", "search_edit"]

        for elem in elements:
            if not (elem.get("clickable") or elem.get("focusable")):
                continue

            text = elem.get("text", "").lower()
            desc = elem.get("content_desc", "").lower()
            rid = elem.get("resource_id", "").lower()

            for kw in search_keywords:
                if kw in text or kw in desc or kw in rid:
                    search_elem = elem
                    break
            if search_elem:
                break

        if search_elem:
            x, y = get_center(search_elem["bounds"])
            tap(x, y)
            time.sleep(0.5)

        # Type the app name
        input_text(app_name)
        time.sleep(1.5)

        # Refresh UI and find the app icon
        _, elements = capture_ui_fast()

        # Look for app icons - prioritize larger clickable elements with matching text/desc
        candidates = []
        for elem in elements:
            if not elem.get("clickable"):
                continue

            text = elem.get("text", "").lower()
            desc = elem.get("content_desc", "").lower()

            # Check if element matches app name
            if app_name_lower not in text and app_name_lower not in desc:
                continue

            bounds = elem.get("bounds", (0, 0, 0, 0))
            width = bounds[2] - bounds[0]
            height = bounds[3] - bounds[1]
            area = width * height

            # App icons are typically square-ish and reasonably sized
            # Skip very small elements (just text labels)
            if area < MIN_CLICKABLE_AREA_PX:
                continue

            # Prefer elements where content_desc contains app name (usually the actual icon)
            priority = 0
            if app_name_lower in desc:
                priority = 2
            elif app_name_lower == text:
                priority = 1

            candidates.append((priority, area, elem))

        if candidates:
            # Sort by priority desc, then by area desc (prefer larger icons)
            candidates.sort(key=lambda x: (-x[0], -x[1]))
            app_elem = candidates[0][2]
            x, y = get_center(app_elem["bounds"])
            tap(x, y)
            time.sleep(1)
            return True, f"Opened '{app_name}' app"

        # Fallback: just tap anywhere the app name appears
        app_elem = self._find_element(app_name, elements)
        if app_elem:
            x, y = get_center(app_elem["bounds"])
            tap(x, y)
            time.sleep(1)
            return True, f"Tapped '{app_name}'"

        # Final fallback: try to launch using intent
        success, msg = self._launch_app_by_intent(app_name)
        if success:
            return success, msg

        return False, f"Could not find '{app_name}' app"

    def _action_search(self, match, elements) -> Tuple[bool, str]:
        """Search: tap search box, type query, submit."""
        query = match.group(1).strip()

        # Check for clipboard references like "that number you copied", "the copied number", etc.
        clipboard_patterns = [
            r"\b(?:that|the)\s+(?:number|text)\s+(?:you|i)\s+copied\b",
            r"\b(?:the\s+)?copied\s+(?:number|text)\b",
            r"\bwhat\s+(?:you|i)\s+copied\b",
            r"\bthe\s+clipboard\b",
            r"\bit\b",  # "search for it" when clipboard has value
        ]

        for pattern in clipboard_patterns:
            if re.search(pattern, query.lower()):
                if self.clipboard:
                    query = self.clipboard
                    break
                else:
                    return False, "Nothing in clipboard to search for"

        # Find search box/icon
        search_keywords = ["search", "find", "query", "search_box", "search_edit_text"]
        search_elem = None

        for elem in elements:
            if not (elem.get("clickable") or elem.get("focusable")):
                continue

            text = elem.get("text", "").lower()
            desc = elem.get("content_desc", "").lower()
            rid = elem.get("resource_id", "").lower()

            for kw in search_keywords:
                if kw in text or kw in desc or kw in rid:
                    search_elem = elem
                    break
            if search_elem:
                break

        if search_elem:
            x, y = get_center(search_elem["bounds"])
            tap(x, y)
            time.sleep(1)

            # Clear any existing text in search field
            press_key("KEYCODE_MOVE_END")
            time.sleep(0.1)
            # Select all and delete
            from recorder.adb_wrapper import run_adb

            run_adb(["shell", "input", "keyevent", "KEYCODE_CTRL_A"])
            time.sleep(0.1)
            press_key("KEYCODE_DEL")
            time.sleep(0.2)

        # Type the search query
        input_text(query)
        time.sleep(0.8)

        # Press enter to submit
        press_key("KEYCODE_ENTER")
        time.sleep(2)  # Wait for results

        return True, f"Searched for '{query}'"

    def _action_filter(self, match, elements) -> Tuple[bool, str]:
        """Filter/sort results."""
        filter_type = match.group(1).strip().lower()

        # Refresh UI after previous action
        _, elements = capture_ui_fast()

        # Look for filter/sort button
        filter_elem = None
        for elem in elements:
            if not elem.get("clickable"):
                continue

            text = elem.get("text", "").lower()
            desc = elem.get("content_desc", "").lower()

            if "filter" in text or "filter" in desc or "sort" in text or "sort" in desc:
                filter_elem = elem
                break

        if filter_elem:
            x, y = get_center(filter_elem["bounds"])
            tap(x, y)
            time.sleep(1)

            # Refresh UI to see filter options
            _, elements = capture_ui_fast()

        # Try to find the specific filter option
        target_keywords = []
        if "view" in filter_type or "watch" in filter_type or "popular" in filter_type:
            target_keywords = ["view count", "most viewed", "most watched", "popular", "view"]
        elif "date" in filter_type or "recent" in filter_type or "new" in filter_type:
            target_keywords = ["upload date", "date", "recent", "newest", "new"]
        elif "rating" in filter_type:
            target_keywords = ["rating", "top rated"]
        else:
            target_keywords = [filter_type]

        for elem in elements:
            if not elem.get("clickable"):
                continue

            text = elem.get("text", "").lower()
            desc = elem.get("content_desc", "").lower()

            for kw in target_keywords:
                if kw in text or kw in desc:
                    x, y = get_center(elem["bounds"])
                    tap(x, y)
                    time.sleep(1)
                    return True, f"Applied filter: {filter_type}"

        return False, f"Could not find filter option for '{filter_type}'"

    def _action_click_first_result(self, match, elements) -> Tuple[bool, str]:
        """Click the first search result (works for web search, app stores, etc.), skipping ads."""
        # Refresh UI
        _, elements = capture_ui_fast()

        # Get ad filter
        ad_filter = get_ad_filter()

        # For web search results, look for clickable links below the search bar
        # Google search results typically have titles as clickable links
        candidates = []

        for elem in elements:
            if not elem.get("clickable"):
                continue

            # Skip ad/sponsored elements
            if ad_filter.is_ad(elem):
                logger.debug(f"Skipping ad result: {elem.get('text', '')[:30]}")
                continue

            # Additional ad detection
            text = elem.get("text", "").lower()
            rid = elem.get("resource_id", "").lower()

            # Skip sponsored/ad results
            if any(ad_word in text for ad_word in ["sponsored", "ad", "promoted", "advertisement"]):
                logger.debug(f"Skipping sponsored result: {text[:30]}")
                continue
            if any(ad_word in rid for ad_word in ["ad_", "_ad", "sponsor", "promo"]):
                continue

            bounds = elem.get("bounds", (0, 0, 0, 0))
            y_pos = bounds[1]
            width = bounds[2] - bounds[0]
            height = bounds[3] - bounds[1]

            # Skip elements at very top (navbar, search bar area)
            if y_pos < NAVBAR_HEIGHT_PX:
                continue

            # Skip very small elements
            if width < MIN_LINK_WIDTH_PX or height < MIN_LINK_HEIGHT_PX:
                continue

            # Skip full-width elements (usually containers, not actual links)
            if width > self.screen_width * 0.98:
                continue

            text_orig = elem.get("text", "")

            # Prioritize elements that look like search results
            priority = 0

            # Links/titles usually have text
            if text_orig and len(text_orig) > 5:
                priority += 2

            # Google search result indicators
            if "url" in rid or "title" in rid or "link" in rid or "result" in rid:
                priority += 3

            if priority > 0 or (text_orig and width > MIN_VIDEO_WIDTH_PX):
                candidates.append((priority, y_pos, elem))

        if candidates:
            # Sort by priority desc, then by Y position (topmost first)
            candidates.sort(key=lambda x: (-x[0], x[1]))
            elem = candidates[0][2]
            x, y = get_center(elem["bounds"])
            text_preview = elem.get("text", "")[:30] or "result"
            tap(x, y)
            time.sleep(2)
            return True, f"Opened first result: '{text_preview}...'"

        return False, "Could not find a search result to click"

    def _action_play_first(self, match, elements) -> Tuple[bool, str]:
        """Play/tap the first video or result (skipping ads/sponsored content)."""
        # Refresh UI
        _, elements = capture_ui_fast()

        # Get ad filter
        ad_filter = get_ad_filter()

        # First pass: Find all "Sponsored" label elements and get their positions
        # YouTube shows "Sponsored" as a separate label below ad videos
        sponsored_regions = []
        for elem in elements:
            text = elem.get("text", "").lower().strip()
            desc = elem.get("content_desc", "").lower().strip()

            # Check for sponsored labels
            if text in ["sponsored", "ad", "promoted", "advertisement"] or desc in [
                "sponsored",
                "ad",
                "promoted",
                "advertisement",
            ]:
                bounds = elem.get("bounds", (0, 0, 0, 0))
                # Mark a region above the sponsored label as "ad zone"
                # Typically the video thumbnail is directly above the label
                # Expand the region to cover typical video thumbnail area
                ad_zone = (
                    bounds[0] - 50,  # x1 with padding
                    bounds[1] - 400,  # y1: go up 400px to cover thumbnail
                    bounds[2] + 50,  # x2 with padding
                    bounds[3] + 50,  # y2 with padding
                )
                sponsored_regions.append(ad_zone)
                logger.debug(f"Found sponsored label at {bounds}, marking ad zone: {ad_zone}")

        def is_in_sponsored_region(elem_bounds):
            """Check if element is within any sponsored region."""
            ex1, ey1, ex2, ey2 = elem_bounds
            elem_center_x = (ex1 + ex2) // 2
            elem_center_y = (ey1 + ey2) // 2

            for zone in sponsored_regions:
                zx1, zy1, zx2, zy2 = zone
                if zx1 <= elem_center_x <= zx2 and zy1 <= elem_center_y <= zy2:
                    return True
            return False

        # Look for video thumbnails - need to distinguish from channel banners and ads
        candidates = []

        for elem in elements:
            if not elem.get("clickable"):
                continue

            # Skip ad/sponsored elements
            if ad_filter.is_ad(elem):
                logger.debug(
                    f"Skipping ad element: {elem.get('content_desc', '')[:30] or elem.get('text', '')[:30]}"
                )
                continue

            # Additional ad detection for YouTube-specific patterns
            rid = elem.get("resource_id", "").lower()
            desc = elem.get("content_desc", "").lower()
            text = elem.get("text", "").lower()

            # Skip sponsored/promoted content
            if any(ad_word in text for ad_word in ["sponsored", "ad", "promoted", "advertisement"]):
                logger.debug(f"Skipping sponsored text: {text[:30]}")
                continue
            if any(
                ad_word in desc
                for ad_word in ["sponsored", "ad ", " ad", "promoted", "advertisement"]
            ):
                logger.debug(f"Skipping sponsored desc: {desc[:30]}")
                continue
            if any(ad_word in rid for ad_word in ["ad_", "_ad", "sponsor", "promo"]):
                logger.debug(f"Skipping ad resource ID: {rid}")
                continue

            bounds = elem.get("bounds", (0, 0, 0, 0))
            width = bounds[2] - bounds[0]
            height = bounds[3] - bounds[1]
            area = width * height

            # Skip very small elements and full-screen elements
            if area < 10000 or width > self.screen_width * 0.95:
                continue

            # Skip elements at the very top (usually navigation)
            if bounds[1] < 250:
                continue

            # Skip channel-related elements
            if any(skip in rid for skip in ["channel", "avatar", "subscribe", "profile"]):
                continue
            if any(skip in desc for skip in ["channel", "subscribe", "profile picture"]):
                continue
            if "subscribe" in text:
                continue

            # Skip elements that are too square (likely channel avatars/icons)
            # Video thumbnails have aspect ratio around 16:9 (1.77) or wider
            aspect_ratio = width / height if height > 0 else 0
            if (
                SQUARE_ASPECT_RATIO_MIN < aspect_ratio < SQUARE_ASPECT_RATIO_MAX
                and area < MAX_AVATAR_AREA_PX
            ):  # Square-ish and small = likely avatar
                continue

            priority = 0

            # High priority: looks like a video thumbnail
            if "thumbnail" in rid or "video" in rid:
                priority = 5
            elif "thumbnail" in desc or "video" in desc:
                priority = 4
            # Medium priority: has video-like aspect ratio (wider than tall)
            elif aspect_ratio > VIDEO_ASPECT_RATIO_MIN and width > MIN_VIDEO_WIDTH_PX:
                priority = 3
            # Check for duration pattern in description (e.g., "10:30", "1:23:45")
            elif re.search(r"\d{1,2}:\d{2}", desc):
                priority = 4
            # Lower priority: generic clickable with text
            elif text and len(text) > 10:
                priority = 1

            if priority > 0:
                candidates.append((priority, bounds[1], elem))

        if candidates:
            # Sort by priority (desc) then by Y position (asc) to get topmost high-priority item
            candidates.sort(key=lambda x: (-x[0], x[1]))
            elem = candidates[0][2]
            x, y = get_center(elem["bounds"])
            desc_preview = elem.get("content_desc", "")[:40] or elem.get("text", "")[:40] or "video"
            tap(x, y)
            time.sleep(2)
            return True, f"Playing: '{desc_preview}...'"

        return False, "Could not find video to play"

    def parse_and_execute(self, instruction: str) -> List[Tuple[bool, str]]:
        """
        Parse natural language instruction and execute actions.

        Returns list of (success, message) tuples.
        """
        results = []

        # Validate input
        if not instruction or not instruction.strip():
            return [(False, "Empty instruction provided")]

        # Check for excessively long instructions
        if len(instruction) > 10000:
            return [(False, "Instruction too long (max 10000 characters)")]

        # Preserve quoted strings by replacing them with placeholders
        quoted_strings = []

        def save_quoted(match):
            quoted_strings.append(match.group(0))
            return f"__QUOTED_{len(quoted_strings) - 1}__"

        # Save quoted strings (both single and double quotes)
        preserved = re.sub(r'["\'][^"\']*["\']', save_quoted, instruction)

        # Now lowercase for processing
        preserved = preserved.lower().strip()

        # Split on common conjunctions, but not on periods that look like abbreviations
        # Split on: comma, "and", "then", or period followed by space and lowercase letter
        parts = re.split(
            r"\s*(?:,\s*(?:and\s+)?|(?:\s+and\s+)|\s+then\s+|(?<=[a-z])\.\s+(?=[a-z]))\s*",
            preserved,
        )
        parts = [p.strip() for p in parts if p.strip()]

        # Restore quoted strings
        def restore_quoted(text):
            for i, qs in enumerate(quoted_strings):
                text = text.replace(f"__quoted_{i}__", qs.strip("\"'"))
            return text

        parts = [restore_quoted(p) for p in parts]

        for part in parts:
            if not part:
                continue

            # Capture UI for each action with error handling
            try:
                _, elements = capture_ui_fast()
            except Exception as e:
                results.append((False, f"Failed to capture UI: {e}"))
                if self.verbose:
                    print(f"  ✗ Failed to capture UI: {e}")
                continue

            executed = False
            for pattern, handler in self.patterns:
                match = re.search(pattern, part, re.IGNORECASE)
                if match:
                    try:
                        success, message = handler(match, elements)
                        results.append((success, message))
                        if self.verbose:
                            status = "✓" if success else "✗"
                            print(f"  {status} {message}")
                        executed = True

                        # Delay between actions
                        time.sleep(self.delay_ms / 1000.0)
                        break
                    except Exception as e:
                        results.append((False, f"Action failed: {e}"))
                        if self.verbose:
                            print(f"  ✗ Action failed: {e}")
                        executed = True
                        break

            if not executed:
                results.append((False, f"Could not understand: '{part}'"))
                if self.verbose:
                    print(f"  ✗ Could not understand: '{part}'")

        return results

    def run_interactive(self):
        """Run in interactive mode."""
        print("\nInteractive Mode - Type instructions in natural language")
        print("Examples:")
        print("  'Open Phone app'")
        print("  'Tap Contacts and scroll down'")
        print("  'Go back, then go home'")
        print("\nType 'quit' to exit\n")

        while True:
            try:
                instruction = input(">>> ").strip()
                if instruction.lower() in ("quit", "exit", "q"):
                    break
                if not instruction:
                    continue

                print()
                results = self.parse_and_execute(instruction)

                success = sum(1 for r in results if r[0])
                failed = len(results) - success
                print(f"\nCompleted: {success} success, {failed} failed\n")

            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Execute Android actions from natural language",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python nl_runner.py "Open Phone app and tap Contacts"
  python nl_runner.py "Scroll down, then tap Settings"
  python nl_runner.py --interactive
  python nl_runner.py --file instructions.txt

Natural language examples:
  "Open the Phone app"
  "Tap on Contacts and scroll down"
  "Long press on Chrome icon"
  "Type hello world"
  "Go back and then go home"
  "Swipe left, wait 2 seconds, swipe right"
        """,
    )

    parser.add_argument("instruction", nargs="?", help="Natural language instruction")
    parser.add_argument("-f", "--file", help="File with instructions (one per line)")
    parser.add_argument("-i", "--interactive", action="store_true", help="Interactive mode")
    parser.add_argument(
        "-d",
        "--delay",
        type=int,
        default=DEFAULT_ACTION_DELAY_MS,
        help="Delay between actions (ms)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if not args.instruction and not args.file and not args.interactive:
        parser.print_help()
        sys.exit(1)

    # Check device
    if not check_device_connected():
        print("Waiting for device...")
        if not wait_for_device(30):
            print("Error: No device connected")
            sys.exit(1)

    runner = NaturalLanguageRunner(delay_ms=args.delay, verbose=True)

    try:
        runner.screen_width, runner.screen_height = get_screen_size()
    except Exception:
        pass

    print("=" * 50)
    print("Natural Language Workflow Runner")
    print(f"Screen: {runner.screen_width}x{runner.screen_height}")
    print("=" * 50)

    if args.interactive:
        runner.run_interactive()
    elif args.file:
        with open(args.file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    print(f"\n> {line}")
                    runner.parse_and_execute(line)
    else:
        print(f"\n> {args.instruction}")
        results = runner.parse_and_execute(args.instruction)

        success = sum(1 for r in results if r[0])
        failed = len(results) - success
        print(f"\n{'='*50}")
        print(f"Completed: {success} success, {failed} failed")

    sys.exit(0)


if __name__ == "__main__":
    main()
