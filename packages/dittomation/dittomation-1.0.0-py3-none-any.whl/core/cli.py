"""
DittoMation CLI - Command-line interface for Android automation.

Usage:
    ditto tap 100 200              # Tap at coordinates
    ditto tap --text "Login"       # Tap element by text
    ditto swipe up                 # Swipe up
    ditto type "Hello"             # Type text
    ditto screenshot               # Take screenshot
    ditto info                     # Show device info
"""

import json
import sys

import click

# Lazy import Android to avoid import errors when just showing help
_android = None


def get_android():
    """Lazily initialize Android instance."""
    global _android
    if _android is None:
        from core.android import Android
        from core.exceptions import DeviceNotFoundError

        try:
            _android = Android()
        except DeviceNotFoundError as e:
            click.echo(f"Error: {e.message}", err=True)
            click.echo("Make sure your device is connected and USB debugging is enabled.", err=True)
            sys.exit(1)
    return _android


@click.group()
@click.version_option(version="1.0.0", prog_name="ditto")
def main():
    """DittoMation - Android automation made simple.

    Control your Android device from the command line with intuitive commands.

    Examples:

        ditto tap 500 500           # Tap at coordinates

        ditto tap -t "Login"        # Tap element by text

        ditto swipe up              # Swipe up

        ditto type "Hello world"    # Type text

        ditto screenshot            # Take screenshot
    """
    pass


# =============================================================================
# Gesture Commands
# =============================================================================


@main.command()
@click.argument("x", type=int, required=False)
@click.argument("y", type=int, required=False)
@click.option("--text", "-t", help="Tap element by visible text")
@click.option("--id", "-i", "resource_id", help="Tap element by resource-id")
@click.option("--desc", "-d", help="Tap element by content-description")
@click.option("--timeout", default=5.0, help="Timeout for element search (seconds)")
@click.option(
    "--min-confidence",
    "-c",
    type=float,
    default=0.3,
    help="Minimum confidence threshold 0.0-1.0 (default: 0.3)",
)
def tap(x, y, text, resource_id, desc, timeout, min_confidence):
    """Tap at coordinates or on an element.

    Uses confidence scoring for fuzzy element matching.

    Examples:

        ditto tap 500 500           # Tap at coordinates

        ditto tap -t "Login"        # Tap element by text

        ditto tap --id btn_submit   # Tap element by ID

        ditto tap -t "Lgoin" -c 0.5 # Fuzzy match with 50% min confidence
    """
    android = get_android()

    if text or resource_id or desc:
        # Element-based tap with confidence
        target = text or resource_id or desc

        # Get confidence info first
        result = android.find_with_confidence(
            text, id=resource_id, desc=desc, min_confidence=min_confidence
        )

        if result:
            success = android.tap(
                text, id=resource_id, desc=desc, timeout=timeout, min_confidence=min_confidence
            )
            if success:
                click.echo(f"Tapped element: {target} ({result.confidence:.0%} confidence)")
            else:
                click.echo(f"Failed to tap element: {target}", err=True)
                sys.exit(1)
        else:
            click.echo(
                f"Element not found: {target} (below {min_confidence:.0%} confidence)", err=True
            )
            sys.exit(1)
    elif x is not None and y is not None:
        # Coordinate-based tap
        success = android.tap(x, y)
        if success:
            click.echo(f"Tapped at ({x}, {y})")
        else:
            click.echo(f"Failed to tap at ({x}, {y})", err=True)
            sys.exit(1)
    else:
        click.echo(
            "Error: Provide coordinates (x y) or element identifier (--text, --id, --desc)",
            err=True,
        )
        sys.exit(1)


@main.command("long-press")
@click.argument("x", type=int, required=False)
@click.argument("y", type=int, required=False)
@click.option("--text", "-t", help="Element text")
@click.option("--id", "-i", "resource_id", help="Element resource-id")
@click.option("--desc", "-d", help="Element content-description")
@click.option("--duration", default=1000, help="Press duration in ms")
@click.option("--timeout", default=5.0, help="Element search timeout (seconds)")
def long_press(x, y, text, resource_id, desc, duration, timeout):
    """Long press at coordinates or on an element.

    Examples:

        ditto long-press 500 500                 # Long press at coordinates

        ditto long-press -t "Item" --duration 2000   # Long press for 2 seconds
    """
    android = get_android()

    if text or resource_id or desc:
        target = text or resource_id or desc
        success = android.long_press(
            text, id=resource_id, desc=desc, duration_ms=duration, timeout=timeout
        )
        if success:
            click.echo(f"Long pressed element: {target}")
        else:
            click.echo(f"Failed to long press: {target}", err=True)
            sys.exit(1)
    elif x is not None and y is not None:
        success = android.long_press(x, y, duration_ms=duration)
        if success:
            click.echo(f"Long pressed at ({x}, {y}) for {duration}ms")
        else:
            click.echo(f"Failed to long press at ({x}, {y})", err=True)
            sys.exit(1)
    else:
        click.echo("Error: Provide coordinates or element identifier", err=True)
        sys.exit(1)


@main.command()
@click.argument("direction_or_x1", required=True)
@click.argument("y1", type=int, required=False)
@click.argument("x2", type=int, required=False)
@click.argument("y2", type=int, required=False)
@click.option("--duration", default=300, help="Swipe duration in ms")
def swipe(direction_or_x1, y1, x2, y2, duration):
    """Swipe by direction or coordinates.

    Directions: up, down, left, right

    Examples:

        ditto swipe up                    # Swipe up from center

        ditto swipe down                  # Swipe down

        ditto swipe 100 500 100 200       # Swipe from (100,500) to (100,200)
    """
    android = get_android()

    # Check if first arg is a direction
    if direction_or_x1.lower() in ("up", "down", "left", "right"):
        success = android.swipe(direction_or_x1.lower(), duration_ms=duration)
        if success:
            click.echo(f"Swiped {direction_or_x1}")
        else:
            click.echo(f"Failed to swipe {direction_or_x1}", err=True)
            sys.exit(1)
    else:
        # Coordinate-based swipe
        try:
            x1 = int(direction_or_x1)
        except ValueError:
            click.echo(f"Invalid direction or coordinate: {direction_or_x1}", err=True)
            sys.exit(1)

        if y1 is None or x2 is None or y2 is None:
            click.echo("Error: Coordinate swipe requires: x1 y1 x2 y2", err=True)
            sys.exit(1)

        success = android.swipe(x1, y1, x2, y2, duration_ms=duration)
        if success:
            click.echo(f"Swiped from ({x1}, {y1}) to ({x2}, {y2})")
        else:
            click.echo("Failed to swipe", err=True)
            sys.exit(1)


@main.command()
@click.argument("direction", type=click.Choice(["up", "down", "left", "right"]))
@click.option("--distance", default=0.5, help="Scroll distance (0.0-1.0)")
@click.option("--duration", default=500, help="Scroll duration in ms")
def scroll(direction, distance, duration):
    """Scroll in a direction.

    Examples:

        ditto scroll down                  # Scroll down

        ditto scroll up --distance 0.8     # Scroll up more
    """
    android = get_android()
    success = android.scroll(direction, distance=distance, duration_ms=duration)
    if success:
        click.echo(f"Scrolled {direction}")
    else:
        click.echo(f"Failed to scroll {direction}", err=True)
        sys.exit(1)


@main.command()
@click.option("--scale", default=0.5, help="Scale factor (>1 zoom in, <1 zoom out)")
@click.option("--x", "center_x", type=int, help="Center X (default: screen center)")
@click.option("--y", "center_y", type=int, help="Center Y (default: screen center)")
@click.option("--duration", default=500, help="Gesture duration in ms")
def pinch(scale, center_x, center_y, duration):
    """Pinch gesture (zoom in/out).

    Examples:

        ditto pinch --scale 2.0        # Zoom in

        ditto pinch --scale 0.5        # Zoom out
    """
    android = get_android()
    success = android.pinch(scale=scale, center_x=center_x, center_y=center_y, duration_ms=duration)
    if success:
        action = "Zoomed in" if scale > 1 else "Zoomed out"
        click.echo(f"{action} (scale: {scale})")
    else:
        click.echo("Failed to pinch", err=True)
        sys.exit(1)


# =============================================================================
# Input Commands
# =============================================================================


@main.command("type")
@click.argument("text")
@click.option("--clear", is_flag=True, help="Clear field before typing")
def type_text(text, clear):
    """Type text into focused field.

    Examples:

        ditto type "Hello world"

        ditto type "username" --clear
    """
    android = get_android()
    success = android.type(text, clear_first=clear)
    if success:
        display_text = text[:30] + "..." if len(text) > 30 else text
        click.echo(f"Typed: {display_text}")
    else:
        click.echo("Failed to type text", err=True)
        sys.exit(1)


@main.command()
@click.argument(
    "button",
    type=click.Choice(
        ["home", "back", "enter", "menu", "recent", "search", "volume-up", "volume-down"]
    ),
)
def press(button):
    """Press a device button.

    Buttons: home, back, enter, menu, recent, search, volume-up, volume-down

    Examples:

        ditto press home

        ditto press back
    """
    android = get_android()

    button_map = {
        "home": "KEYCODE_HOME",
        "back": "KEYCODE_BACK",
        "enter": "KEYCODE_ENTER",
        "menu": "KEYCODE_MENU",
        "recent": "KEYCODE_APP_SWITCH",
        "search": "KEYCODE_SEARCH",
        "volume-up": "KEYCODE_VOLUME_UP",
        "volume-down": "KEYCODE_VOLUME_DOWN",
    }

    if button == "home":
        success = android.press_home()
    elif button == "back":
        success = android.press_back()
    elif button == "enter":
        success = android.press_enter()
    else:
        keycode = button_map[button]
        success = android.press_key(keycode)

    if success:
        click.echo(f"Pressed {button}")
    else:
        click.echo(f"Failed to press {button}", err=True)
        sys.exit(1)


@main.command()
@click.argument("keycode")
def key(keycode):
    """Press a key by keycode.

    Examples:

        ditto key KEYCODE_VOLUME_UP

        ditto key KEYCODE_POWER
    """
    android = get_android()
    success = android.press_key(keycode)
    if success:
        click.echo(f"Pressed key: {keycode}")
    else:
        click.echo(f"Failed to press key: {keycode}", err=True)
        sys.exit(1)


# =============================================================================
# App Commands
# =============================================================================


@main.command("open")
@click.argument("app_name")
def open_app_cmd(app_name):
    """Open an app by name or package.

    Examples:

        ditto open Chrome

        ditto open com.android.settings
    """
    android = get_android()
    success = android.open_app(app_name)
    if success:
        click.echo(f"Opened: {app_name}")
    else:
        click.echo(f"Failed to open: {app_name}", err=True)
        sys.exit(1)


@main.command()
def app():
    """Show current foreground app."""
    android = get_android()
    current = android.current_app()
    click.echo(f"Package:  {current['package']}")
    click.echo(f"Activity: {current['activity']}")


# =============================================================================
# Screen Commands
# =============================================================================


@main.command()
@click.argument("filename", required=False)
def screenshot(filename):
    """Take a screenshot.

    Examples:

        ditto screenshot                   # Auto-named screenshot

        ditto screenshot login.png         # Named screenshot
    """
    android = get_android()
    try:
        filepath = android.screenshot(filename)
        click.echo(f"Screenshot saved: {filepath}")
    except Exception as e:
        click.echo(f"Screenshot failed: {e}", err=True)
        sys.exit(1)


@main.command("screen-size")
def screen_size():
    """Show screen dimensions."""
    android = get_android()
    width, height = android.screen_size()
    click.echo(f"{width} x {height}")


# =============================================================================
# Element Commands
# =============================================================================


@main.command()
@click.option("--text", "-t", help="Find by visible text")
@click.option("--id", "-i", "resource_id", help="Find by resource-id")
@click.option("--desc", "-d", help="Find by content-description")
@click.option("--class", "class_name", help="Find by class name")
@click.option("--all", "find_all", is_flag=True, help="Find all matching elements")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option(
    "--min-confidence",
    "-c",
    type=float,
    default=0.3,
    help="Minimum confidence threshold 0.0-1.0 (default: 0.3)",
)
@click.option("--show-confidence", is_flag=True, help="Show confidence scores")
def find(text, resource_id, desc, class_name, find_all, as_json, min_confidence, show_confidence):
    """Find elements on screen with confidence scoring.

    Uses fuzzy matching to find elements even with minor text differences.

    Examples:

        ditto find -t "Login"              # Find by text

        ditto find --id btn_submit         # Find by ID

        ditto find -t "Item" --all         # Find all matching

        ditto find -t "Setings" -c 0.5     # Fuzzy match "Settings"

        ditto find -t "Login" --show-confidence  # Show confidence score
    """
    android = get_android()

    if not any([text, resource_id, desc, class_name]):
        click.echo("Error: Provide at least one search criteria", err=True)
        sys.exit(1)

    if find_all:
        results = android.find_all_with_confidence(
            text=text,
            id=resource_id,
            desc=desc,
            class_name=class_name,
            min_confidence=min_confidence,
        )
        if as_json:
            output = [
                {"element": r.element, "confidence": r.confidence, "match_details": r.match_details}
                for r in results
            ]
            click.echo(json.dumps(output, indent=2, default=str))
        else:
            click.echo(f"Found {len(results)} element(s) (>= {min_confidence:.0%} confidence):")
            for r in results:
                _print_element_with_confidence(r.element, r.confidence, show_confidence)
    else:
        result = android.find_with_confidence(
            text=text, id=resource_id, desc=desc, min_confidence=min_confidence
        )
        if result:
            if as_json:
                output = {
                    "element": result.element,
                    "confidence": result.confidence,
                    "match_details": result.match_details,
                }
                click.echo(json.dumps(output, indent=2, default=str))
            else:
                _print_element_with_confidence(
                    result.element, result.confidence, show_confidence or True
                )
        else:
            click.echo(f"Element not found (below {min_confidence:.0%} confidence)", err=True)
            sys.exit(1)


@main.command()
@click.option("--text", "-t", help="Wait for element by text")
@click.option("--id", "-i", "resource_id", help="Wait for element by resource-id")
@click.option("--desc", "-d", help="Wait for element by content-description")
@click.option("--timeout", default=10.0, help="Timeout in seconds")
@click.option(
    "--min-confidence",
    "-c",
    type=float,
    default=0.3,
    help="Minimum confidence threshold 0.0-1.0 (default: 0.3)",
)
def wait(text, resource_id, desc, timeout, min_confidence):
    """Wait for an element to appear with confidence scoring.

    Examples:

        ditto wait -t "Welcome" --timeout 15

        ditto wait --id main_content

        ditto wait -t "Loaded" -c 0.7      # Require 70% confidence
    """
    android = get_android()

    if not any([text, resource_id, desc]):
        click.echo("Error: Provide at least one search criteria", err=True)
        sys.exit(1)

    target = text or resource_id or desc
    click.echo(f"Waiting for: {target} (timeout: {timeout}s, min confidence: {min_confidence:.0%})")

    result = android.wait_for_with_confidence(
        text=text, id=resource_id, desc=desc, timeout=timeout, min_confidence=min_confidence
    )
    if result:
        click.echo(f"Found element! ({result.confidence:.0%} confidence)")
        _print_element_with_confidence(result.element, result.confidence, show_confidence=True)
    else:
        click.echo(
            f"Element not found within {timeout}s (below {min_confidence:.0%} confidence)", err=True
        )
        sys.exit(1)


@main.command()
@click.option("--text", "-t", help="Check element by text")
@click.option("--id", "-i", "resource_id", help="Check element by resource-id")
@click.option("--desc", "-d", help="Check element by content-description")
def confidence(text, resource_id, desc):
    """Get confidence score for an element match.

    Returns the match confidence without requiring a minimum threshold.

    Examples:

        ditto confidence -t "Login"        # Check confidence for "Login"

        ditto confidence -t "Logn"         # Check fuzzy match confidence
    """
    android = get_android()

    if not any([text, resource_id, desc]):
        click.echo("Error: Provide at least one search criteria", err=True)
        sys.exit(1)

    target = text or resource_id or desc
    score = android.get_confidence(text=text, id=resource_id, desc=desc)

    if score > 0:
        quality = _confidence_quality(score)
        click.echo(f"Confidence for '{target}': {score:.0%} ({quality})")
    else:
        click.echo(f"No match found for '{target}'")
        sys.exit(1)


# =============================================================================
# Device Commands
# =============================================================================


@main.command()
def devices():
    """List connected devices."""
    from recorder.adb_wrapper import get_connected_devices

    device_list = get_connected_devices()
    if not device_list:
        click.echo("No devices connected")
        return

    click.echo(f"Connected devices ({len(device_list)}):")
    for device in device_list:
        status_icon = "+" if device["status"] == "device" else "-"
        click.echo(f"  {status_icon} {device['serial']} ({device['status']})")


@main.command()
def info():
    """Show device information."""
    android = get_android()
    device_info = android.info()

    click.echo("Device Information:")
    click.echo(f"  Serial:          {device_info.get('serial', 'N/A')}")
    click.echo(f"  Model:           {device_info.get('model', 'N/A')}")
    click.echo(f"  Manufacturer:    {device_info.get('manufacturer', 'N/A')}")
    click.echo(f"  Android Version: {device_info.get('android_version', 'N/A')}")
    click.echo(f"  SDK Version:     {device_info.get('sdk_version', 'N/A')}")
    width, height = device_info.get("screen_size", (0, 0))
    click.echo(f"  Screen Size:     {width} x {height}")


# =============================================================================
# Helper Functions
# =============================================================================


def _print_element(elem: dict):
    """Print element info in readable format."""
    _print_element_with_confidence(elem, confidence=None, show_confidence=False)


def _print_element_with_confidence(
    elem: dict, confidence: float = None, show_confidence: bool = False
):
    """Print element info with optional confidence score."""
    class_name = elem.get("class", "").split(".")[-1]
    bounds = elem.get("bounds", (0, 0, 0, 0))

    parts = [f"  {class_name}"]

    if elem.get("resource_id"):
        rid = elem["resource_id"].split("/")[-1]
        parts.append(f"id={rid}")

    if elem.get("text"):
        text = elem["text"][:30]
        if len(elem["text"]) > 30:
            text += "..."
        parts.append(f'text="{text}"')

    if elem.get("content_desc"):
        desc = elem["content_desc"][:20]
        parts.append(f'desc="{desc}"')

    # Calculate center
    if len(bounds) == 4:
        center_x = (bounds[0] + bounds[2]) // 2
        center_y = (bounds[1] + bounds[3]) // 2
        parts.append(f"@({center_x},{center_y})")

    # Add confidence if provided
    if show_confidence and confidence is not None:
        quality = _confidence_quality(confidence)
        parts.append(f"[{confidence:.0%} {quality}]")

    click.echo(" ".join(parts))


def _confidence_quality(confidence: float) -> str:
    """Get quality descriptor for confidence score."""
    if confidence >= 0.9:
        return "excellent"
    elif confidence >= 0.7:
        return "good"
    elif confidence >= 0.5:
        return "fair"
    elif confidence >= 0.3:
        return "low"
    else:
        return "very low"


# =============================================================================
# Automation Commands
# =============================================================================


@main.command("run")
@click.argument("script_file", type=click.Path(exists=True))
@click.option("--retries", "-r", default=2, help="Default retry count per step")
@click.option("--timeout", "-t", default=5.0, help="Default timeout in seconds")
@click.option("--delay", "-d", default=0.3, help="Delay between steps in seconds")
@click.option(
    "--stop-on-failure/--continue-on-failure",
    default=True,
    help="Stop on first failure or continue",
)
@click.option("--screenshot-on-failure", is_flag=True, help="Take screenshot when a step fails")
@click.option("--output", "-o", type=click.Path(), help="Save result to JSON file")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed step output")
@click.option(
    "--var", "-V", multiple=True, help="Set variable: --var name=value (can be used multiple times)"
)
@click.option(
    "--vars-file", type=click.Path(exists=True), help="Load variables from JSON or YAML file"
)
@click.option("--device", help="Device serial or AVD name to use")
@click.option("--headless", is_flag=True, help="Start emulator in headless mode if needed")
@click.option(
    "--cloud-provider",
    type=click.Choice(["firebase", "aws"]),
    help="Run on cloud provider instead of local device",
)
@click.option("--cloud-device", help="Cloud device model to use")
def run_automation(
    script_file,
    retries,
    timeout,
    delay,
    stop_on_failure,
    screenshot_on_failure,
    output,
    verbose,
    var,
    vars_file,
    device,
    headless,
    cloud_provider,
    cloud_device,
):
    """Run an automation script from JSON file.

    The script file should contain a JSON array of steps or an object with a "steps" key.
    Scripts can also define variables in a "variables" object that can be referenced
    using {{variable}} syntax in step fields.

    Example script with variables (login.json):

    \b
        {
            "name": "login_test",
            "variables": {
                "username": "testuser",
                "password": "secret123"
            },
            "steps": [
                {"action": "open", "app": "MyApp"},
                {"action": "tap", "text": "Login"},
                {"action": "type", "value": "{{username}}"},
                {"action": "tap", "text": "Submit"}
            ]
        }

    Example with conditional logic:

    \b
        {
            "steps": [
                {"action": "if", "expr": "element_exists(text='Welcome')",
                 "then_steps": [{"action": "log", "message": "Already logged in"}],
                 "else_steps": [{"action": "tap", "text": "Login"}]}
            ]
        }

    Examples:

        ditto run alarm.json

        ditto run login.json --var username=myuser --var password=secret

        ditto run script.json --vars-file config.json --verbose

        ditto run script.json --device emulator-5554

        ditto run script.json --device Pixel_6_API_33 --headless

        ditto run script.json --cloud-provider firebase --cloud-device Pixel_6
    """
    from core.automation import Automation

    # Handle cloud execution
    if cloud_provider:
        if not cloud_device:
            click.echo("Error: --cloud-device is required when using --cloud-provider", err=True)
            sys.exit(1)

        try:
            provider = _get_cloud_provider(cloud_provider)
            devices = [provider.acquire_device(cloud_device)]

            click.echo(f"Running on {cloud_provider}: {cloud_device}")
            run = provider.run_test(devices=devices, workflow_path=script_file, timeout=3600)

            click.echo(f"Test run started: {run.run_id}")
            click.echo("Waiting for completion...")

            run = provider.wait_for_completion(run, poll_interval=30)

            if run.is_successful:
                click.echo("Test completed successfully!")
            else:
                click.echo(f"Test failed: {run.error_message or run.status.value}", err=True)
                sys.exit(1)
            return

        except Exception as e:
            click.echo(f"Cloud execution failed: {e}", err=True)
            sys.exit(1)

    # Handle local/emulator execution
    device_serial = None
    started_emulator = None

    try:
        # Device selection
        if device:
            from core.device_manager import DeviceManager
            from core.emulator import EmulatorConfig

            dm = DeviceManager()
            selected = dm.select_device(serial=device, avd_name=device)

            if selected:
                emulator_config = None
                if headless:
                    emulator_config = EmulatorConfig(headless=True)

                device_serial = dm.connect(
                    selected, start_if_avd=True, emulator_config=emulator_config
                )
                click.echo(f"Using device: {device_serial}")

                # Track if we started an emulator so we can stop it later
                if device_serial and device_serial.startswith("emulator-"):
                    from core.config_manager import get_config

                    config = get_config()
                    if config.get("emulator.auto_stop", True):
                        started_emulator = device_serial
            else:
                click.echo(f"Device not found: {device}", err=True)
                sys.exit(1)

        # Parse command-line variables
        extra_vars = {}
        for var_str in var:
            if "=" in var_str:
                key, value = var_str.split("=", 1)
                # Try to parse as JSON for complex values
                try:
                    extra_vars[key.strip()] = json.loads(value)
                except json.JSONDecodeError:
                    extra_vars[key.strip()] = value
            else:
                click.echo(f"Invalid variable format: {var_str} (expected name=value)", err=True)
                sys.exit(1)

        # Load variables from file if specified
        if vars_file:
            import os

            ext = os.path.splitext(vars_file)[1].lower()
            with open(vars_file, encoding="utf-8") as f:
                if ext in (".yaml", ".yml"):
                    try:
                        import yaml

                        file_vars = yaml.safe_load(f)
                    except ImportError:
                        click.echo(
                            "PyYAML required for YAML files. Install with: pip install pyyaml",
                            err=True,
                        )
                        sys.exit(1)
                else:
                    file_vars = json.load(f)

            if isinstance(file_vars, dict):
                # File vars are loaded first, CLI vars override
                merged_vars = dict(file_vars)
                merged_vars.update(extra_vars)
                extra_vars = merged_vars

        auto = Automation(
            default_retries=retries,
            default_timeout=timeout,
            step_delay=delay,
            stop_on_failure=stop_on_failure,
            screenshot_on_failure=screenshot_on_failure,
            device_serial=device_serial,
        )

        click.echo(f"Running automation: {script_file}")
        if extra_vars:
            click.echo(f"Variables: {', '.join(extra_vars.keys())}")

        result = auto.run_from_file(script_file, extra_vars=extra_vars if extra_vars else None)

        # Show results
        if verbose:
            for sr in result.step_results:
                status_icon = (
                    "+"
                    if sr.status.value == "success"
                    else "-" if sr.status.value == "failed" else "o"
                )
                confidence_str = f" ({sr.confidence:.0%})" if sr.confidence else ""
                click.echo(
                    f"  [{status_icon}] Step {sr.step_index + 1}: {sr.step_type}{confidence_str}"
                )
                if sr.error:
                    click.echo(f"      Error: {sr.error}")

        click.echo(result.summary())

        if output:
            auto.save_result(result, output)
            click.echo(f"Result saved to: {output}")

        if not result.success:
            sys.exit(1)

    except FileNotFoundError:
        click.echo(f"Script file not found: {script_file}", err=True)
        sys.exit(1)
    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON in script file: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Automation failed: {e}", err=True)
        sys.exit(1)
    finally:
        # Stop emulator if we started one and auto_stop is enabled
        if started_emulator:
            try:
                from core.emulator import EmulatorManager

                manager = EmulatorManager()
                manager.stop(started_emulator)
                click.echo(f"Stopped emulator: {started_emulator}")
            except Exception:
                pass  # Ignore errors when stopping


@main.command("create-script")
@click.argument("name")
@click.option(
    "--template",
    "-t",
    type=click.Choice(["empty", "alarm", "app"]),
    default="empty",
    help="Script template to use",
)
def create_script(name, template):
    """Create a new automation script from template.

    Examples:

        ditto create-script my_automation

        ditto create-script set_alarm --template alarm
    """
    import os

    if not name.endswith(".json"):
        name = name + ".json"

    if os.path.exists(name):
        click.echo(f"File already exists: {name}", err=True)
        sys.exit(1)

    templates = {
        "empty": [
            {"action": "wait", "timeout": 1.0, "description": "Initial wait"},
        ],
        "alarm": [
            {"action": "open", "app": "clock", "description": "Open Clock app"},
            {"action": "wait", "timeout": 1.5, "description": "Wait for app to load"},
            {"action": "tap", "text": "Alarm", "retries": 3, "description": "Go to Alarm tab"},
            {"action": "tap", "desc": "Add alarm", "retries": 2, "description": "Add new alarm"},
            {"action": "wait", "timeout": 0.5},
            {"action": "tap", "text": "11", "description": "Set hour to 11"},
            {"action": "tap", "text": "10", "description": "Set minute to 10"},
            {"action": "tap", "text": "OK", "retries": 2, "description": "Confirm alarm"},
        ],
        "app": [
            {"action": "open", "app": "APP_NAME", "description": "Open the app"},
            {"action": "wait", "timeout": 2.0, "description": "Wait for app to load"},
            {
                "action": "wait_for",
                "text": "ELEMENT_TEXT",
                "timeout": 10.0,
                "description": "Wait for main screen",
            },
            {"action": "tap", "text": "BUTTON_TEXT", "retries": 2, "description": "Tap the button"},
        ],
    }

    script_data = {
        "name": name.replace(".json", ""),
        "description": f"Automation script created from '{template}' template",
        "steps": templates[template],
    }

    with open(name, "w", encoding="utf-8") as f:
        json.dump(script_data, f, indent=2)

    click.echo(f"Created script: {name}")
    click.echo(f"Edit the file and run with: ditto run {name}")


@main.command("validate")
@click.argument("script_file", type=click.Path(exists=True))
def validate_script(script_file):
    """Validate an automation script without running it.

    Examples:

        ditto validate my_script.json
    """
    from core.automation import Step

    try:
        with open(script_file, encoding="utf-8") as f:
            data = json.load(f)

        steps_data = data.get("steps", data) if isinstance(data, dict) else data

        if not isinstance(steps_data, list):
            click.echo("Error: Script must contain a list of steps", err=True)
            sys.exit(1)

        errors = []
        for i, step_data in enumerate(steps_data):
            try:
                Step(**step_data)
            except Exception as e:
                errors.append(f"Step {i+1}: {e}")

        if errors:
            click.echo(f"Validation failed with {len(errors)} error(s):", err=True)
            for error in errors:
                click.echo(f"  - {error}", err=True)
            sys.exit(1)
        else:
            click.echo(f"Script is valid: {len(steps_data)} steps")

    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON: {e}", err=True)
        sys.exit(1)


# =============================================================================
# Emulator Commands
# =============================================================================


@main.group()
def emulator():
    """Manage Android emulators.

    Commands for listing, starting, stopping, and monitoring Android emulators.
    Useful for headless CI/CD environments.

    Examples:

        ditto emulator list                # List available AVDs

        ditto emulator start Pixel_6       # Start an emulator

        ditto emulator stop emulator-5554  # Stop an emulator

        ditto emulator status              # Show running emulators
    """
    pass


@emulator.command("list")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def emulator_list(as_json):
    """List available AVDs (Android Virtual Devices).

    Shows all AVDs that can be started as emulators.

    Examples:

        ditto emulator list

        ditto emulator list --json
    """
    from core.emulator import EmulatorManager

    try:
        manager = EmulatorManager()
        avds = manager.list_avds()

        if as_json:
            click.echo(json.dumps([avd.to_dict() for avd in avds], indent=2))
        else:
            if not avds:
                click.echo("No AVDs found. Create one using Android Studio or avdmanager.")
                return

            click.echo(f"Available AVDs ({len(avds)}):")
            for avd in avds:
                info_parts = [avd.name]
                if avd.device:
                    info_parts.append(f"({avd.device})")
                if avd.target:
                    info_parts.append(f"[{avd.target}]")
                click.echo(f"  {' '.join(info_parts)}")

    except Exception as e:
        click.echo(f"Error listing AVDs: {e}", err=True)
        sys.exit(1)


@emulator.command("start")
@click.argument("avd_name")
@click.option(
    "--headless/--no-headless", default=True, help="Run without window (default: headless)"
)
@click.option(
    "--gpu",
    default="swiftshader_indirect",
    type=click.Choice(["auto", "host", "swiftshader_indirect", "angle_indirect", "off"]),
    help="GPU rendering mode",
)
@click.option("--memory", type=int, default=2048, help="Memory in MB")
@click.option("--cores", type=int, default=2, help="Number of CPU cores")
@click.option("--timeout", type=int, default=300, help="Boot timeout in seconds")
@click.option("--no-wait", is_flag=True, help="Don't wait for boot completion")
@click.option("--wipe-data", is_flag=True, help="Wipe user data before starting")
def emulator_start(avd_name, headless, gpu, memory, cores, timeout, no_wait, wipe_data):
    """Start an Android emulator.

    Starts the specified AVD as an emulator. By default runs in headless
    mode (no window) which is ideal for CI/CD environments.

    Examples:

        ditto emulator start Pixel_6_API_33

        ditto emulator start Pixel_6 --headless --gpu swiftshader_indirect

        ditto emulator start Pixel_6 --no-headless  # Show emulator window
    """
    from core.emulator import EmulatorConfig, EmulatorManager

    try:
        manager = EmulatorManager()

        config = EmulatorConfig(
            headless=headless,
            gpu=gpu,
            memory_mb=memory,
            cores=cores,
            no_window=headless,
            wipe_data=wipe_data,
        )

        click.echo(f"Starting emulator: {avd_name}...")
        if headless:
            click.echo("  Mode: headless (no window)")
        click.echo(f"  GPU: {gpu}")
        click.echo(f"  Memory: {memory}MB")

        instance = manager.start(avd_name, config=config, wait_boot=not no_wait, timeout=timeout)

        click.echo(f"Emulator started: {instance.serial}")
        if instance.boot_completed:
            click.echo("Boot completed successfully.")

    except Exception as e:
        click.echo(f"Error starting emulator: {e}", err=True)
        sys.exit(1)


@emulator.command("stop")
@click.argument("serial", required=False)
@click.option("--all", "stop_all", is_flag=True, help="Stop all running emulators")
@click.option("--force", is_flag=True, help="Force kill the emulator")
def emulator_stop(serial, stop_all, force):
    """Stop a running emulator.

    Stop a specific emulator by its serial number, or stop all running
    emulators with --all.

    Examples:

        ditto emulator stop emulator-5554

        ditto emulator stop --all

        ditto emulator stop emulator-5554 --force
    """
    from core.emulator import EmulatorManager

    try:
        manager = EmulatorManager()

        if stop_all:
            count = manager.stop_all()
            click.echo(f"Stopped {count} emulator(s)")
        elif serial:
            success = manager.stop(serial, force=force)
            if success:
                click.echo(f"Stopped emulator: {serial}")
            else:
                click.echo(f"Failed to stop emulator: {serial}", err=True)
                sys.exit(1)
        else:
            click.echo("Error: Provide a serial number or use --all", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"Error stopping emulator: {e}", err=True)
        sys.exit(1)


@emulator.command("status")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def emulator_status(as_json):
    """Show running emulators.

    Displays information about all currently running Android emulators.

    Examples:

        ditto emulator status

        ditto emulator status --json
    """
    from core.emulator import EmulatorManager

    try:
        manager = EmulatorManager()
        running = manager.get_running_emulators()

        if as_json:
            click.echo(json.dumps([emu.to_dict() for emu in running], indent=2))
        else:
            if not running:
                click.echo("No emulators running")
                return

            click.echo(f"Running emulators ({len(running)}):")
            for emu in running:
                parts = [f"  {emu.serial}"]
                if emu.avd_name:
                    parts.append(f"({emu.avd_name})")
                parts.append(f"[{emu.state.value}]")
                click.echo(" ".join(parts))

    except Exception as e:
        click.echo(f"Error getting emulator status: {e}", err=True)
        sys.exit(1)


# =============================================================================
# Cloud Commands
# =============================================================================


@main.group()
def cloud():
    """Run tests on cloud device platforms.

    Commands for running DittoMation workflows on Firebase Test Lab
    or AWS Device Farm.

    Examples:

        ditto cloud list-devices --provider firebase

        ditto cloud run workflow.json --provider aws --device Pixel_6

        ditto cloud status <run-id> --provider firebase
    """
    pass


def _get_cloud_provider(provider_name: str):
    """Get a cloud provider instance."""
    from core.config_manager import get_config

    config = get_config()

    if provider_name == "firebase":
        from core.cloud.firebase import FirebaseTestLabProvider

        return FirebaseTestLabProvider(
            project_id=config.get("cloud.firebase.project_id"),
            credentials_file=config.get("cloud.firebase.credentials_file"),
            results_bucket=config.get("cloud.firebase.results_bucket"),
        )
    elif provider_name == "aws":
        from core.cloud.aws import AWSDeviceFarmProvider

        return AWSDeviceFarmProvider(
            project_arn=config.get("cloud.aws.project_arn"),
            region=config.get("cloud.aws.region", "us-west-2"),
            device_pool_arn=config.get("cloud.aws.device_pool_arn"),
        )
    else:
        raise click.ClickException(f"Unknown provider: {provider_name}")


@cloud.command("list-devices")
@click.option(
    "--provider",
    "-p",
    required=True,
    type=click.Choice(["firebase", "aws"]),
    help="Cloud provider to use",
)
@click.option("--model", "-m", help="Filter by model name")
@click.option("--os-version", "-o", help="Filter by OS version")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def cloud_list_devices(provider, model, os_version, as_json):
    """List available devices on a cloud platform.

    Examples:

        ditto cloud list-devices --provider firebase

        ditto cloud list-devices --provider aws --model Pixel

        ditto cloud list-devices --provider firebase --os-version 13 --json
    """
    from core.cloud.models import DeviceFilter

    try:
        cloud_provider = _get_cloud_provider(provider)

        # Build filter if criteria provided
        device_filter = None
        if model or os_version:
            device_filter = DeviceFilter(
                models=[model] if model else None,
                os_versions=[os_version] if os_version else None,
            )

        devices = cloud_provider.list_devices(filters=device_filter)

        if as_json:
            click.echo(json.dumps([d.to_dict() for d in devices], indent=2))
        else:
            if not devices:
                click.echo("No devices found matching criteria")
                return

            click.echo(f"Available devices ({len(devices)}):")
            for device in devices:
                parts = [f"  {device.model}"]
                if device.os_version:
                    parts.append(f"(Android {device.os_version})")
                if device.manufacturer:
                    parts.append(f"[{device.manufacturer}]")
                click.echo(" ".join(parts))

    except Exception as e:
        click.echo(f"Error listing devices: {e}", err=True)
        sys.exit(1)


@cloud.command("run")
@click.argument("workflow_file", type=click.Path(exists=True))
@click.option(
    "--provider",
    "-p",
    required=True,
    type=click.Choice(["firebase", "aws"]),
    help="Cloud provider to use",
)
@click.option(
    "--device",
    "-d",
    multiple=True,
    required=True,
    help="Device model(s) to run on (can be specified multiple times)",
)
@click.option("--os-version", "-o", help="OS version to use")
@click.option("--timeout", type=int, default=3600, help="Test timeout in seconds")
@click.option("--app", type=click.Path(exists=True), help="APK file to test")
@click.option("--wait/--no-wait", default=True, help="Wait for completion")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def cloud_run(workflow_file, provider, device, os_version, timeout, app, wait, as_json):
    """Run a workflow on cloud devices.

    Examples:

        ditto cloud run test.json --provider firebase --device Pixel_6

        ditto cloud run test.json --provider aws --device Pixel_6 --device Pixel_7

        ditto cloud run test.json --provider firebase --device Pixel_6 --app myapp.apk
    """
    try:
        cloud_provider = _get_cloud_provider(provider)

        # Get requested devices
        devices = []
        for device_model in device:
            found = cloud_provider.acquire_device(device_model, os_version)
            devices.append(found)

        click.echo(f"Starting test on {len(devices)} device(s)...")

        # Build options
        options = {}
        if app:
            options["app_apk"] = app

        # Start test
        run = cloud_provider.run_test(
            devices=devices, workflow_path=workflow_file, timeout=timeout, **options
        )

        click.echo(f"Test run started: {run.run_id}")

        if wait:
            click.echo("Waiting for completion...")
            from core.config_manager import get_config

            config = get_config()
            poll_interval = config.get("cloud.poll_interval", 30)

            run = cloud_provider.wait_for_completion(
                run, timeout=timeout + 300, poll_interval=poll_interval
            )

            if as_json:
                click.echo(json.dumps(run.to_dict(), indent=2))
            else:
                click.echo(f"Test completed: {run.status.value}")
                if run.is_successful:
                    click.echo("Result: PASSED")
                else:
                    click.echo("Result: FAILED")
                    if run.error_message:
                        click.echo(f"Error: {run.error_message}")
        else:
            click.echo("Test running in background")
            click.echo(f"Check status with: ditto cloud status {run.run_id} --provider {provider}")

    except Exception as e:
        click.echo(f"Error running test: {e}", err=True)
        sys.exit(1)


@cloud.command("status")
@click.argument("run_id")
@click.option(
    "--provider", "-p", required=True, type=click.Choice(["firebase", "aws"]), help="Cloud provider"
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def cloud_status(run_id, provider, as_json):
    """Get the status of a cloud test run.

    Examples:

        ditto cloud status abc123 --provider firebase

        ditto cloud status arn:aws:... --provider aws --json
    """
    try:
        cloud_provider = _get_cloud_provider(provider)
        run = cloud_provider.get_run_status(run_id)

        if as_json:
            click.echo(json.dumps(run.to_dict(), indent=2))
        else:
            click.echo(f"Run ID: {run.run_id}")
            click.echo(f"Status: {run.status.value}")
            if run.started_at:
                click.echo(f"Started: {run.started_at}")
            if run.completed_at:
                click.echo(f"Completed: {run.completed_at}")
            if run.duration_seconds:
                click.echo(f"Duration: {run.duration_seconds:.1f}s")
            if run.error_message:
                click.echo(f"Error: {run.error_message}")

    except Exception as e:
        click.echo(f"Error getting status: {e}", err=True)
        sys.exit(1)


@cloud.command("artifacts")
@click.argument("run_id")
@click.option(
    "--provider", "-p", required=True, type=click.Choice(["firebase", "aws"]), help="Cloud provider"
)
@click.option("--output", "-o", type=click.Path(), default="./artifacts", help="Output directory")
@click.option(
    "--type",
    "artifact_types",
    multiple=True,
    type=click.Choice(["screenshot", "video", "log", "all"]),
    help="Artifact types to download",
)
def cloud_artifacts(run_id, provider, output, artifact_types):
    """Download artifacts from a cloud test run.

    Examples:

        ditto cloud artifacts abc123 --provider firebase --output ./results

        ditto cloud artifacts arn:aws:... --provider aws --type screenshot --type log
    """
    try:
        cloud_provider = _get_cloud_provider(provider)
        run = cloud_provider.get_run_status(run_id)

        # Determine artifact types to download
        types_to_download = None
        if artifact_types and "all" not in artifact_types:
            types_to_download = list(artifact_types)

        click.echo(f"Collecting artifacts from run: {run_id}")

        artifacts = cloud_provider.collect_artifacts(
            run, output_dir=output, artifact_types=types_to_download
        )

        click.echo(f"Downloaded {len(artifacts)} artifact(s) to: {output}")
        for artifact in artifacts:
            click.echo(f"  - {artifact.name} ({artifact.artifact_type.value})")

    except Exception as e:
        click.echo(f"Error downloading artifacts: {e}", err=True)
        sys.exit(1)


@cloud.command("configure")
@click.option(
    "--provider",
    "-p",
    required=True,
    type=click.Choice(["firebase", "aws"]),
    help="Cloud provider to configure",
)
@click.option("--project", help="Project ID (Firebase) or Project ARN (AWS)")
@click.option("--region", help="AWS region")
@click.option(
    "--credentials", type=click.Path(exists=True), help="Path to credentials file (Firebase)"
)
@click.option("--bucket", help="Results bucket (Firebase)")
def cloud_configure(provider, project, region, credentials, bucket):
    """Configure cloud provider settings.

    Saves configuration to the DittoMation config file.

    Examples:

        ditto cloud configure --provider firebase --project my-project-id

        ditto cloud configure --provider aws --project arn:aws:... --region us-west-2
    """
    from core.config_manager import get_config

    config = get_config()
    changes = []

    if provider == "firebase":
        if project:
            config.set("cloud.firebase.project_id", project)
            changes.append(f"firebase.project_id = {project}")
        if credentials:
            config.set("cloud.firebase.credentials_file", credentials)
            changes.append(f"firebase.credentials_file = {credentials}")
        if bucket:
            config.set("cloud.firebase.results_bucket", bucket)
            changes.append(f"firebase.results_bucket = {bucket}")

    elif provider == "aws":
        if project:
            config.set("cloud.aws.project_arn", project)
            changes.append(f"aws.project_arn = {project}")
        if region:
            config.set("cloud.aws.region", region)
            changes.append(f"aws.region = {region}")

    if changes:
        click.echo("Configuration updated:")
        for change in changes:
            click.echo(f"  {change}")
        click.echo("\nTo persist, save config: ditto config save")
    else:
        click.echo("No changes made. Provide at least one option to configure.")


if __name__ == "__main__":
    main()
