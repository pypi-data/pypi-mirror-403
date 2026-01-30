"""
ADB Wrapper - Foundation for all ADB interactions.

Provides utilities for executing ADB commands, detecting device info,
capturing UI hierarchy, and streaming shell output.

Features:
- Automatic ADB path detection
- Retry logic with exponential backoff
- Custom exceptions for better error handling
- Structured logging
"""

import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from typing import Dict, Generator, List, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config_manager import get_config_value
from core.exceptions import (
    ADBCommandError,
    ADBNotFoundError,
    ADBTimeoutError,
    DeviceNotFoundError,
    DeviceOfflineError,
    DeviceUnauthorizedError,
    InvalidInputDeviceError,
    UIHierarchyError,
)
from core.logging_config import get_logger

# Module logger
logger = get_logger("adb_wrapper")


def get_adb_path() -> str:
    """
    Auto-detect ADB location.

    Checks in order:
    1. Configuration file setting
    2. ANDROID_HOME/platform-tools/adb (or adb.exe on Windows)
    3. User's local Android SDK
    4. System PATH

    Returns:
        Path to adb executable

    Raises:
        ADBNotFoundError: If ADB cannot be found
    """
    import platform

    searched_paths = []

    # Check configuration first
    config_path = get_config_value("adb.path")
    if config_path and os.path.exists(config_path):
        logger.debug(f"Using ADB from config: {config_path}")
        return config_path

    # Determine adb executable name based on OS
    is_windows = platform.system() == "Windows"
    adb_name = "adb.exe" if is_windows else "adb"

    # Check ANDROID_HOME environment variable
    android_home = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if android_home:
        adb_path = os.path.join(android_home, "platform-tools", adb_name)
        searched_paths.append(adb_path)
        if os.path.exists(adb_path):
            logger.debug(f"Found ADB at ANDROID_HOME: {adb_path}")
            return adb_path

    # Check common locations based on OS
    if is_windows:
        # Check Windows-specific locations
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if local_app_data:
            adb_path = os.path.join(local_app_data, "Android", "Sdk", "platform-tools", adb_name)
            searched_paths.append(adb_path)
            if os.path.exists(adb_path):
                logger.debug(f"Found ADB at LocalAppData: {adb_path}")
                return adb_path

        # Check user profile path
        user_profile = os.environ.get("USERPROFILE", "")
        if user_profile:
            adb_path = os.path.join(
                user_profile, "AppData", "Local", "Android", "Sdk", "platform-tools", adb_name
            )
            searched_paths.append(adb_path)
            if os.path.exists(adb_path):
                logger.debug(f"Found ADB at UserProfile: {adb_path}")
                return adb_path
    else:
        # Check Unix-like OS locations
        home = os.path.expanduser("~")
        common_paths = [
            os.path.join(home, "Android", "Sdk", "platform-tools", adb_name),
            os.path.join(home, "Library", "Android", "sdk", "platform-tools", adb_name),  # macOS
            "/usr/local/bin/adb",
            "/usr/bin/adb",
        ]
        for adb_path in common_paths:
            searched_paths.append(adb_path)
            if os.path.exists(adb_path):
                logger.debug(f"Found ADB at: {adb_path}")
                return adb_path

    # Try system PATH
    try:
        # Use 'where' on Windows, 'which' on Unix-like
        path_cmd = "where" if is_windows else "which"
        result = subprocess.run([path_cmd, "adb"], capture_output=True, text=True)
        if result.returncode == 0:
            adb_path = result.stdout.strip().split("\n")[0]
            logger.debug(f"Found ADB in PATH: {adb_path}")
            return adb_path
    except Exception:
        pass

    logger.error(f"ADB not found. Searched paths: {searched_paths}")
    raise ADBNotFoundError(searched_paths)


# Cache ADB path after first detection
_adb_path: Optional[str] = None

# Cache screen size per device
_screen_size_cache: Dict[str, Tuple[int, int]] = {}


def _get_adb() -> str:
    """Get cached ADB path."""
    global _adb_path
    if _adb_path is None:
        _adb_path = get_adb_path()
        logger.info(f"ADB path: {_adb_path}")
    return _adb_path


def run_adb_with_retry(
    args: List[str],
    timeout: Optional[int] = None,
    retry_count: Optional[int] = None,
    retry_delay: Optional[float] = None,
    retry_backoff: Optional[float] = None,
) -> str:
    """
    Execute ADB command with exponential backoff retry.

    Args:
        args: List of arguments to pass to adb
        timeout: Command timeout in seconds (from config if None)
        retry_count: Number of retries (from config if None)
        retry_delay: Initial delay between retries in seconds (from config if None)
        retry_backoff: Backoff multiplier (from config if None)

    Returns:
        Command stdout as string

    Raises:
        ADBCommandError: If command fails after all retries
        ADBTimeoutError: If command times out
    """
    # Get defaults from config
    timeout = timeout or get_config_value("adb.timeout", 30)
    retry_count = retry_count if retry_count is not None else get_config_value("adb.retry_count", 3)
    retry_delay = (
        retry_delay if retry_delay is not None else get_config_value("adb.retry_delay", 1.0)
    )
    retry_backoff = (
        retry_backoff if retry_backoff is not None else get_config_value("adb.retry_backoff", 2.0)
    )

    adb = _get_adb()
    cmd = [adb] + args
    cmd_str = " ".join(args)

    last_error = None
    current_delay = retry_delay

    for attempt in range(retry_count + 1):
        try:
            logger.debug(
                f"Executing ADB command (attempt {attempt + 1}/{retry_count + 1}): {cmd_str}"
            )

            result = subprocess.run(cmd, capture_output=True, timeout=timeout)

            # Decode with UTF-8, ignoring errors for special characters
            stdout = result.stdout.decode("utf-8", errors="ignore")
            stderr = result.stderr.decode("utf-8", errors="ignore")

            if result.returncode != 0:
                # Check for specific device errors
                if "device not found" in stderr.lower() or "no devices" in stderr.lower():
                    raise DeviceNotFoundError(details={"stderr": stderr})
                if "device offline" in stderr.lower():
                    device_serial = get_device_serial()
                    raise DeviceOfflineError(device_serial or "unknown", details={"stderr": stderr})
                if "device unauthorized" in stderr.lower():
                    device_serial = get_device_serial()
                    raise DeviceUnauthorizedError(
                        device_serial or "unknown", details={"stderr": stderr}
                    )

                raise ADBCommandError(cmd_str, result.returncode, stdout, stderr)

            logger.debug(f"ADB command succeeded: {cmd_str}")
            return stdout

        except subprocess.TimeoutExpired:
            logger.warning(f"ADB command timed out after {timeout}s: {cmd_str}")
            last_error = ADBTimeoutError(cmd_str, timeout)

            if attempt < retry_count:
                logger.info(f"Retrying in {current_delay:.1f}s...")
                time.sleep(current_delay)
                current_delay *= retry_backoff
                continue
            raise last_error

        except (
            ADBCommandError,
            DeviceNotFoundError,
            DeviceOfflineError,
            DeviceUnauthorizedError,
        ) as e:
            last_error = e

            # Don't retry on device-level errors
            if isinstance(e, (DeviceNotFoundError, DeviceOfflineError, DeviceUnauthorizedError)):
                raise

            if attempt < retry_count:
                logger.warning(f"ADB command failed, retrying in {current_delay:.1f}s: {e.message}")
                time.sleep(current_delay)
                current_delay *= retry_backoff
                continue
            raise

    raise last_error


def run_adb(args: List[str], timeout: Optional[int] = 30) -> str:
    """
    Execute ADB command and return output (backward compatible).

    Args:
        args: List of arguments to pass to adb
        timeout: Command timeout in seconds (None for no timeout)

    Returns:
        Command stdout as string

    Raises:
        ADBCommandError: If command fails
        ADBTimeoutError: If command times out
    """
    return run_adb_with_retry(args, timeout=timeout, retry_count=0)


def get_device_serial() -> Optional[str]:
    """
    Get the serial number of the connected device.

    Returns:
        Device serial or None if no device connected
    """
    try:
        output = run_adb(["devices"])
        lines = output.strip().split("\n")
        for line in lines[1:]:  # Skip header
            if "\tdevice" in line:
                parts = line.split("\t")
                if len(parts) >= 1:
                    logger.debug(f"Found device: {parts[0]}")
                    return parts[0]
    except Exception as e:
        logger.debug(f"Failed to get device serial: {e}")
    return None


def get_connected_devices() -> List[dict]:
    """
    Get list of all connected devices with their status.

    Returns:
        List of dicts with 'serial' and 'status' keys
    """
    devices = []
    try:
        output = run_adb(["devices"])
        lines = output.strip().split("\n")
        for line in lines[1:]:  # Skip header
            parts = line.split("\t")
            if len(parts) >= 2:
                devices.append({"serial": parts[0], "status": parts[1]})
        logger.debug(f"Found {len(devices)} connected device(s)")
    except Exception as e:
        logger.warning(f"Failed to get connected devices: {e}")
    return devices


def get_screen_size() -> Tuple[int, int]:
    """
    Get device screen size (cached per device).

    Returns:
        Tuple of (width, height) in pixels

    Raises:
        ADBCommandError: If screen size cannot be determined
    """
    # Check cache first
    device_serial = get_device_serial()
    if device_serial and device_serial in _screen_size_cache:
        return _screen_size_cache[device_serial]

    # Try wm size first
    try:
        output = run_adb(["shell", "wm", "size"])
        # Output format: "Physical size: 1080x2340"
        match = re.search(r"(\d+)x(\d+)", output)
        if match:
            width, height = int(match.group(1)), int(match.group(2))
            logger.debug(f"Screen size from wm: {width}x{height}")
            # Cache the result
            if device_serial:
                _screen_size_cache[device_serial] = (width, height)
            return width, height
    except Exception as e:
        logger.debug(f"wm size failed: {e}")

    # Fallback: try SurfaceFlinger (works on Android 13+)
    try:
        output = run_adb(["shell", "dumpsys", "SurfaceFlinger"])
        # Look for "size=[1080 2400]" pattern
        match = re.search(r"size=\[(\d+)\s+(\d+)\]", output)
        if match:
            width, height = int(match.group(1)), int(match.group(2))
            logger.debug(f"Screen size from SurfaceFlinger: {width}x{height}")
            if device_serial:
                _screen_size_cache[device_serial] = (width, height)
            return width, height
        # Look for "w/h:1080x2400" pattern
        match = re.search(r"w/h:(\d+)x(\d+)", output)
        if match:
            width, height = int(match.group(1)), int(match.group(2))
            logger.debug(f"Screen size from SurfaceFlinger (w/h): {width}x{height}")
            if device_serial:
                _screen_size_cache[device_serial] = (width, height)
            return width, height
    except Exception as e:
        logger.debug(f"SurfaceFlinger failed: {e}")

    # Fallback: try dumpsys display
    try:
        output = run_adb(["shell", "dumpsys", "display"])
        match = re.search(r"mDisplayWidth=(\d+).*?mDisplayHeight=(\d+)", output, re.DOTALL)
        if match:
            width, height = int(match.group(1)), int(match.group(2))
            logger.debug(f"Screen size from display: {width}x{height}")
            if device_serial:
                _screen_size_cache[device_serial] = (width, height)
            return width, height
        # Alternative pattern
        match = re.search(r"(\d+)\s*x\s*(\d+)", output)
        if match:
            width, height = int(match.group(1)), int(match.group(2))
            logger.debug(f"Screen size from display (alt): {width}x{height}")
            if device_serial:
                _screen_size_cache[device_serial] = (width, height)
            return width, height
    except Exception as e:
        logger.debug(f"dumpsys display failed: {e}")

    # Fallback: try getprop
    try:
        width_out = run_adb(["shell", "getprop", "persist.sys.lcd_density_width"])
        height_out = run_adb(["shell", "getprop", "persist.sys.lcd_density_height"])
        if width_out.strip() and height_out.strip():
            width, height = int(width_out.strip()), int(height_out.strip())
            logger.debug(f"Screen size from getprop: {width}x{height}")
            if device_serial:
                _screen_size_cache[device_serial] = (width, height)
            return width, height
    except Exception as e:
        logger.debug(f"getprop failed: {e}")

    # Fallback: use config or common default sizes
    config_width = get_config_value("device.screen_width")
    config_height = get_config_value("device.screen_height")
    if config_width and config_height:
        logger.info(f"Using screen size from config: {config_width}x{config_height}")
        result = (config_width, config_height)
        if device_serial:
            _screen_size_cache[device_serial] = result
        return result

    logger.warning("Could not detect screen size, using default 1080x1920")
    return 1080, 1920


def get_input_devices() -> List[dict]:
    """
    Get list of input devices.

    Returns:
        List of device info dicts with 'path' and 'name' keys
    """
    output = run_adb(["shell", "getevent", "-pl"])
    devices = []
    current_device = None

    for line in output.split("\n"):
        if line.startswith("add device"):
            # Parse: "add device 1: /dev/input/event1"
            match = re.search(r"/dev/input/event\d+", line)
            if match:
                current_device = {"path": match.group(0), "name": ""}
        elif "name:" in line and current_device:
            # Parse: '  name:     "device_name"'
            match = re.search(r'name:\s+"([^"]+)"', line)
            if match:
                current_device["name"] = match.group(1)
                devices.append(current_device)
                current_device = None

    logger.debug(f"Found {len(devices)} input device(s)")
    return devices


def get_input_device() -> str:
    """
    Find the primary touch input device path.

    Returns:
        Device path like '/dev/input/event1'

    Raises:
        InvalidInputDeviceError: If no touch device found
    """
    devices = get_input_devices()

    if not devices:
        logger.error("No input devices found")
        raise InvalidInputDeviceError(details={"device_count": 0})

    # Sort by event number to prefer lower numbered devices (usually the primary)
    def get_event_num(d):
        match = re.search(r"event(\d+)", d["path"])
        return int(match.group(1)) if match else 999

    devices.sort(key=get_event_num)

    # Look for touch-related devices
    touch_keywords = ["touch", "touchscreen", "ts", "input"]

    for device in devices:
        name_lower = device["name"].lower()
        if any(kw in name_lower for kw in touch_keywords):
            logger.info(f"Found touch device: {device['path']} ({device['name']})")
            return device["path"]

    # Fallback: return first event device
    logger.warning(f"No touch-specific device found, using first device: {devices[0]['path']}")
    return devices[0]["path"]


def get_input_max_values(device: str) -> Tuple[int, int]:
    """
    Get max X/Y values for coordinate scaling from input device.

    Args:
        device: Device path like '/dev/input/event1'

    Returns:
        Tuple of (max_x, max_y)
    """
    output = run_adb(["shell", "getevent", "-pl"])

    max_x = 0
    max_y = 0
    in_device_section = False

    for line in output.split("\n"):
        if device in line:
            in_device_section = True
        elif line.startswith("add device") and in_device_section:
            break
        elif in_device_section:
            # Look for ABS_MT_POSITION_X or ABS_MT_POSITION_Y
            if "ABS_MT_POSITION_X" in line or "0035" in line:
                match = re.search(r"max\s+(\d+)", line)
                if match:
                    max_x = int(match.group(1))
            elif "ABS_MT_POSITION_Y" in line or "0036" in line:
                match = re.search(r"max\s+(\d+)", line)
                if match:
                    max_y = int(match.group(1))

    # Fallback to screen size if not found
    if max_x == 0 or max_y == 0:
        logger.debug("Could not get input max values, falling back to screen size")
        width, height = get_screen_size()
        return width, height

    logger.debug(f"Input max values: {max_x}x{max_y}")
    return max_x, max_y


def dump_ui(
    output_path: Optional[str] = None,
    max_retries: Optional[int] = None,
    retry_delay: Optional[float] = None,
) -> ET.Element:
    """
    Capture UI hierarchy XML and return parsed tree.

    Args:
        output_path: Optional path to save raw XML
        max_retries: Number of retries if UI dump fails (from config if None)
        retry_delay: Seconds to wait between retries (from config if None)

    Returns:
        Root element of parsed XML tree

    Raises:
        UIHierarchyError: If UI dump fails after all retries
    """
    max_retries = (
        max_retries if max_retries is not None else get_config_value("ui_capture.max_retries", 5)
    )
    retry_delay_ms = (
        retry_delay
        if retry_delay is not None
        else get_config_value("ui_capture.retry_delay_ms", 1000)
    )
    retry_delay = retry_delay_ms / 1000.0 if retry_delay is None else retry_delay

    adb = _get_adb()
    device_path = "/sdcard/window_dump.xml"

    last_error = None

    for attempt in range(max_retries):
        try:
            # Kill any stuck uiautomator process before trying
            if attempt > 0:
                logger.debug(f"UI dump attempt {attempt + 1}/{max_retries}")
                subprocess.run(
                    [adb, "shell", "pkill", "-f", "uiautomator"], capture_output=True, timeout=5
                )
                time.sleep(0.5)

            # Dump UI - use quoted command to avoid path escaping issues
            dump_result = subprocess.run(
                [adb, "shell", f"uiautomator dump {device_path}"],
                capture_output=True,
                timeout=60,  # Increased timeout
            )

            dump_stdout = dump_result.stdout.decode("utf-8", errors="ignore")
            dump_stderr = dump_result.stderr.decode("utf-8", errors="ignore")

            # Check for common errors indicating UI not ready
            if "null root node" in dump_stdout or "null root node" in dump_stderr:
                logger.debug("UI not ready (null root node), retrying...")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue

            # Pull the file content
            cat_result = subprocess.run(
                [adb, "shell", f"cat {device_path}"], capture_output=True, timeout=10
            )

            xml_content = cat_result.stdout.decode("utf-8", errors="ignore")
            cat_stderr = cat_result.stderr.decode("utf-8", errors="ignore")

            if not xml_content or not xml_content.strip().startswith("<?xml"):
                last_error = f"{dump_stderr} {cat_stderr}"
                logger.debug(f"Invalid XML content: {last_error[:100]}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                raise UIHierarchyError(
                    f"UI dump failed: {last_error}",
                    details={"attempt": attempt + 1, "max_retries": max_retries},
                )

            # Clean up device file (ignore errors)
            subprocess.run([adb, "shell", f"rm {device_path}"], capture_output=True, timeout=5)

            # Save to output if requested
            if output_path:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(xml_content)
                logger.debug(f"Saved UI dump to: {output_path}")

            # Parse and return
            root = ET.fromstring(xml_content)
            logger.debug("UI dump successful")
            return root

        except ET.ParseError as e:
            last_error = f"XML parse error: {e}"
            logger.warning(f"Failed to parse UI XML: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue

        except subprocess.TimeoutExpired as e:
            last_error = f"Timeout: {e}"
            logger.warning("UI dump timed out")
            # Kill stuck uiautomator on timeout
            subprocess.run(
                [adb, "shell", "pkill", "-f", "uiautomator"], capture_output=True, timeout=5
            )
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue

    raise UIHierarchyError(
        f"UI dump failed after {max_retries} attempts",
        details={"last_error": str(last_error), "max_retries": max_retries},
    )


def shell_stream(cmd: str) -> Generator[str, None, None]:
    """
    Stream output from shell command (for getevent).

    Args:
        cmd: Shell command to execute

    Yields:
        Lines of output from the command
    """
    adb = _get_adb()
    full_cmd = [adb, "shell", cmd]

    logger.debug(f"Starting shell stream: {cmd}")

    process = subprocess.Popen(
        full_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1
    )

    try:
        for line in process.stdout:
            yield line.rstrip("\n\r")
    except Exception as e:
        logger.error(f"Error in shell stream: {e}")
    finally:
        try:
            process.terminate()
            process.wait(timeout=2.0)
            logger.debug("Shell stream terminated")
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            logger.debug("Shell stream killed after timeout")
        except Exception:
            pass


def get_current_app() -> Tuple[str, str]:
    """
    Get current foreground app package and activity.

    Returns:
        Tuple of (package_name, activity_name)
    """
    try:
        output = run_adb(["shell", "dumpsys", "activity", "activities"])

        # Look for mResumedActivity or mFocusedActivity
        for pattern in [r"mResumedActivity.*?(\S+)/(\S+)", r"mFocusedActivity.*?(\S+)/(\S+)"]:
            match = re.search(pattern, output)
            if match:
                package, activity = match.group(1), match.group(2)
                logger.debug(f"Current app: {package}/{activity}")
                return package, activity

        # Alternative: use window focus
        output = run_adb(["shell", "dumpsys", "window", "windows"])
        match = re.search(r"mCurrentFocus.*?(\S+)/(\S+)", output)
        if match:
            package, activity = match.group(1), match.group(2)
            logger.debug(f"Current app (from window): {package}/{activity}")
            return package, activity
    except Exception as e:
        logger.warning(f"Failed to get current app: {e}")

    return "", ""


def check_device_connected() -> bool:
    """Check if a device is connected and ready."""
    try:
        output = run_adb(["devices"])
        connected = "\tdevice" in output
        logger.debug(f"Device connected: {connected}")
        return connected
    except Exception as e:
        logger.debug(f"Device check failed: {e}")
        return False


def wait_for_device(timeout: int = 60) -> bool:
    """
    Wait for device to be fully booted.

    Args:
        timeout: Max seconds to wait

    Returns:
        True if device is ready, False if timeout
    """
    logger.info("Waiting for device...")

    # First wait for device to appear
    try:
        run_adb(["wait-for-device"], timeout=timeout)
    except Exception as e:
        logger.error(f"Failed waiting for device: {e}")
        return False

    # Then wait for boot to complete
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            output = run_adb(["shell", "getprop", "sys.boot_completed"])
            if output.strip() == "1":
                logger.info("Device ready")
                return True
        except Exception:
            pass
        time.sleep(1)

    logger.error("Timeout waiting for device boot")
    return False
