"""Tests for core.android module."""

from unittest.mock import MagicMock, patch

import pytest

from core.android import DIRECTION_OFFSETS, Android
from core.exceptions import DeviceNotFoundError


class TestAndroidInit:
    """Tests for Android class initialization."""

    @patch("core.android.get_device_serial")
    @patch("core.android.ElementLocator")
    def test_init_with_auto_detect(self, mock_locator, mock_serial):
        mock_serial.return_value = "device123"
        mock_locator.return_value = MagicMock()

        android = Android()

        assert android.device == "device123"

    @patch("core.android.get_device_serial")
    @patch("core.android.ElementLocator")
    def test_init_with_specific_device(self, mock_locator, mock_serial):
        mock_locator.return_value = MagicMock()

        android = Android(device="my-device")

        assert android.device == "my-device"
        mock_serial.assert_not_called()

    @patch("core.android.get_device_serial")
    def test_init_no_device_raises(self, mock_serial):
        mock_serial.return_value = None

        with pytest.raises(DeviceNotFoundError):
            Android()

    @patch("core.android.get_device_serial")
    @patch("core.android.ElementLocator")
    def test_init_with_custom_confidence(self, mock_locator, mock_serial):
        mock_serial.return_value = "device123"
        mock_locator.return_value = MagicMock()

        android = Android(min_confidence=0.8)

        assert android.min_confidence == 0.8


class TestAndroidGestures:
    """Tests for Android gesture methods."""

    @patch("core.android.get_device_serial", return_value="device123")
    @patch("core.android.ElementLocator")
    @patch("core.android._tap")
    def test_tap_with_coordinates(self, mock_tap, mock_locator, mock_serial):
        mock_locator.return_value = MagicMock()
        mock_tap.return_value = True

        android = Android()
        result = android.tap(100, 200)

        assert result is True
        mock_tap.assert_called_once_with(100, 200)

    @patch("core.android.get_device_serial", return_value="device123")
    @patch("core.android.ElementLocator")
    @patch("core.android.capture_ui_fast")
    @patch("core.android.find_best_match")
    @patch("core.android.get_center")
    @patch("core.android._tap")
    def test_tap_with_text(
        self, mock_tap, mock_center, mock_match, mock_ui, mock_locator, mock_serial
    ):
        mock_locator.return_value = MagicMock()
        mock_ui.return_value = (None, [{"text": "Login", "bounds": (100, 200, 200, 250)}])
        mock_match.return_value = MagicMock(
            element={"bounds": (100, 200, 200, 250)}, confidence=0.9
        )
        mock_center.return_value = (150, 225)
        mock_tap.return_value = True

        android = Android()
        result = android.tap("Login")

        assert result is True

    @patch("core.android.get_device_serial", return_value="device123")
    @patch("core.android.ElementLocator")
    @patch("core.android._long_press")
    def test_long_press_with_coordinates(self, mock_lp, mock_locator, mock_serial):
        mock_locator.return_value = MagicMock()
        mock_lp.return_value = True

        android = Android()
        result = android.long_press(100, 200, duration_ms=2000)

        assert result is True
        mock_lp.assert_called_once_with(100, 200, 2000)

    @patch("core.android.get_device_serial", return_value="device123")
    @patch("core.android.ElementLocator")
    @patch("core.android.get_screen_size")
    @patch("core.android._swipe")
    def test_swipe_direction_up(self, mock_swipe, mock_screen, mock_locator, mock_serial):
        mock_locator.return_value = MagicMock()
        mock_screen.return_value = (1080, 1920)
        mock_swipe.return_value = True

        android = Android()
        result = android.swipe("up")

        assert result is True
        mock_swipe.assert_called_once()

    @patch("core.android.get_device_serial", return_value="device123")
    @patch("core.android.ElementLocator")
    @patch("core.android._swipe")
    def test_swipe_with_coordinates(self, mock_swipe, mock_locator, mock_serial):
        mock_locator.return_value = MagicMock()
        mock_swipe.return_value = True

        android = Android()
        result = android.swipe(100, 200, 100, 500, 300)

        assert result is True
        mock_swipe.assert_called_once_with(100, 200, 100, 500, 300)

    @patch("core.android.get_device_serial", return_value="device123")
    @patch("core.android.ElementLocator")
    def test_swipe_invalid_direction(self, mock_locator, mock_serial):
        mock_locator.return_value = MagicMock()

        android = Android()
        result = android.swipe("diagonal")

        assert result is False

    @patch("core.android.get_device_serial", return_value="device123")
    @patch("core.android.ElementLocator")
    @patch("core.android.get_screen_size")
    @patch("core.android._scroll")
    def test_scroll(self, mock_scroll, mock_screen, mock_locator, mock_serial):
        mock_locator.return_value = MagicMock()
        mock_screen.return_value = (1080, 1920)
        mock_scroll.return_value = True

        android = Android()
        result = android.scroll("down", distance=0.5)

        assert result is True
        mock_scroll.assert_called_once()


class TestAndroidInput:
    """Tests for Android input methods."""

    @patch("core.android.get_device_serial", return_value="device123")
    @patch("core.android.ElementLocator")
    @patch("core.android._input_text")
    def test_type(self, mock_input, mock_locator, mock_serial):
        mock_locator.return_value = MagicMock()
        mock_input.return_value = True

        android = Android()
        result = android.type("hello world")

        assert result is True
        mock_input.assert_called_once()

    @patch("core.android.get_device_serial", return_value="device123")
    @patch("core.android.ElementLocator")
    @patch("core.android._press_home")
    def test_press_home(self, mock_home, mock_locator, mock_serial):
        mock_locator.return_value = MagicMock()
        mock_home.return_value = True

        android = Android()
        result = android.press_home()

        assert result is True

    @patch("core.android.get_device_serial", return_value="device123")
    @patch("core.android.ElementLocator")
    @patch("core.android._press_back")
    def test_press_back(self, mock_back, mock_locator, mock_serial):
        mock_locator.return_value = MagicMock()
        mock_back.return_value = True

        android = Android()
        result = android.press_back()

        assert result is True

    @patch("core.android.get_device_serial", return_value="device123")
    @patch("core.android.ElementLocator")
    @patch("core.android._press_enter")
    def test_press_enter(self, mock_enter, mock_locator, mock_serial):
        mock_locator.return_value = MagicMock()
        mock_enter.return_value = True

        android = Android()
        result = android.press_enter()

        assert result is True


class TestAndroidElementMethods:
    """Tests for Android element finding methods."""

    @patch("core.android.get_device_serial", return_value="device123")
    @patch("core.android.ElementLocator")
    @patch("core.android.capture_ui_fast")
    @patch("core.android.find_best_match")
    def test_find_by_text(self, mock_match, mock_ui, mock_locator, mock_serial):
        mock_locator.return_value = MagicMock()
        mock_ui.return_value = (None, [{"text": "Login", "bounds": (0, 0, 100, 50)}])
        mock_match.return_value = MagicMock(element={"text": "Login"}, confidence=0.9)

        android = Android()
        element = android.find(text="Login")

        assert element is not None
        assert element["text"] == "Login"

    @patch("core.android.get_device_serial", return_value="device123")
    @patch("core.android.ElementLocator")
    @patch("core.android.capture_ui_fast")
    @patch("core.android.find_best_match")
    def test_find_not_found(self, mock_match, mock_ui, mock_locator, mock_serial):
        mock_locator.return_value = MagicMock()
        mock_ui.return_value = (None, [])
        mock_match.return_value = None

        android = Android()
        element = android.find(text="NonExistent")

        assert element is None

    @patch("core.android.get_device_serial", return_value="device123")
    @patch("core.android.ElementLocator")
    @patch("core.android.capture_ui_fast")
    @patch("core.android.find_best_match")
    def test_exists_true(self, mock_match, mock_ui, mock_locator, mock_serial):
        mock_locator.return_value = MagicMock()
        mock_ui.return_value = (None, [{"text": "Login"}])
        mock_match.return_value = MagicMock(element={"text": "Login"}, confidence=0.9)

        android = Android()
        assert android.exists(text="Login") is True

    @patch("core.android.get_device_serial", return_value="device123")
    @patch("core.android.ElementLocator")
    @patch("core.android.capture_ui_fast")
    @patch("core.android.find_best_match")
    def test_exists_false(self, mock_match, mock_ui, mock_locator, mock_serial):
        mock_locator.return_value = MagicMock()
        mock_ui.return_value = (None, [])
        mock_match.return_value = None

        android = Android()
        assert android.exists(text="NonExistent") is False


class TestAndroidScreenMethods:
    """Tests for Android screen methods."""

    @patch("core.android.get_device_serial", return_value="device123")
    @patch("core.android.ElementLocator")
    @patch("core.android.get_screen_size")
    def test_screen_size(self, mock_size, mock_locator, mock_serial):
        mock_locator.return_value = MagicMock()
        mock_size.return_value = (1080, 1920)

        android = Android()
        width, height = android.screen_size()

        assert width == 1080
        assert height == 1920

    @patch("core.android.get_device_serial", return_value="device123")
    @patch("core.android.ElementLocator")
    @patch("core.android.get_screen_size")
    def test_screen_size_cached(self, mock_size, mock_locator, mock_serial):
        mock_locator.return_value = MagicMock()
        mock_size.return_value = (1080, 1920)

        android = Android()
        android.screen_size()
        android.screen_size()

        # Should only call get_screen_size once due to caching
        assert mock_size.call_count == 1


class TestAndroidAppMethods:
    """Tests for Android app methods."""

    @patch("core.android.get_device_serial", return_value="device123")
    @patch("core.android.ElementLocator")
    @patch("core.android.run_adb")
    def test_open_app_by_package(self, mock_adb, mock_locator, mock_serial):
        mock_locator.return_value = MagicMock()
        mock_adb.return_value = ""

        android = Android()
        result = android.open_app("com.android.chrome")

        assert result is True
        mock_adb.assert_called()

    @patch("core.android.get_device_serial", return_value="device123")
    @patch("core.android.ElementLocator")
    @patch("core.android.get_current_app")
    def test_current_app(self, mock_current, mock_locator, mock_serial):
        mock_locator.return_value = MagicMock()
        mock_current.return_value = ("com.test.app", "MainActivity")

        android = Android()
        app_info = android.current_app()

        assert app_info["package"] == "com.test.app"
        assert app_info["activity"] == "MainActivity"


class TestAndroidDeviceMethods:
    """Tests for Android device methods."""

    @patch("core.android.get_device_serial", return_value="device123")
    @patch("core.android.ElementLocator")
    @patch("core.android.get_connected_devices")
    def test_devices(self, mock_devices, mock_locator, mock_serial):
        mock_locator.return_value = MagicMock()
        mock_devices.return_value = [
            {"serial": "device1", "status": "device"},
            {"serial": "device2", "status": "device"},
        ]

        android = Android()
        devices = android.devices()

        assert len(devices) == 2
        assert devices[0]["serial"] == "device1"

    @patch("core.android.get_device_serial", return_value="device123")
    @patch("core.android.ElementLocator")
    @patch("core.android.get_screen_size")
    @patch("core.android.run_adb")
    def test_info(self, mock_adb, mock_screen, mock_locator, mock_serial):
        mock_locator.return_value = MagicMock()
        mock_screen.return_value = (1080, 1920)
        mock_adb.return_value = "Pixel 6"

        android = Android()
        info = android.info()

        assert info["serial"] == "device123"
        assert info["screen_size"] == (1080, 1920)


class TestAndroidMinConfidence:
    """Tests for min_confidence property."""

    @patch("core.android.get_device_serial", return_value="device123")
    @patch("core.android.ElementLocator")
    def test_get_min_confidence(self, mock_locator, mock_serial):
        mock_locator.return_value = MagicMock()

        android = Android(min_confidence=0.5)
        assert android.min_confidence == 0.5

    @patch("core.android.get_device_serial", return_value="device123")
    @patch("core.android.ElementLocator")
    def test_set_min_confidence(self, mock_locator, mock_serial):
        mock_locator_instance = MagicMock()
        mock_locator.return_value = mock_locator_instance

        android = Android()
        android.min_confidence = 0.8

        assert android.min_confidence == 0.8
        assert mock_locator_instance.min_confidence == 0.8

    @patch("core.android.get_device_serial", return_value="device123")
    @patch("core.android.ElementLocator")
    def test_set_min_confidence_clamps(self, mock_locator, mock_serial):
        mock_locator.return_value = MagicMock()

        android = Android()
        android.min_confidence = 1.5  # Should clamp to 1.0
        assert android.min_confidence == 1.0

        android.min_confidence = -0.5  # Should clamp to 0.0
        assert android.min_confidence == 0.0


class TestAndroidRepr:
    """Tests for Android __repr__ method."""

    @patch("core.android.get_device_serial", return_value="device123")
    @patch("core.android.ElementLocator")
    def test_repr(self, mock_locator, mock_serial):
        mock_locator.return_value = MagicMock()

        android = Android(min_confidence=0.5)
        repr_str = repr(android)

        assert "Android" in repr_str
        assert "device123" in repr_str
        assert "50%" in repr_str


class TestDirectionOffsets:
    """Tests for DIRECTION_OFFSETS constant."""

    def test_all_directions_defined(self):
        assert "up" in DIRECTION_OFFSETS
        assert "down" in DIRECTION_OFFSETS
        assert "left" in DIRECTION_OFFSETS
        assert "right" in DIRECTION_OFFSETS

    def test_offset_values(self):
        assert DIRECTION_OFFSETS["up"][1] < 0  # Y decreases going up
        assert DIRECTION_OFFSETS["down"][1] > 0  # Y increases going down
        assert DIRECTION_OFFSETS["left"][0] < 0  # X decreases going left
        assert DIRECTION_OFFSETS["right"][0] > 0  # X increases going right
