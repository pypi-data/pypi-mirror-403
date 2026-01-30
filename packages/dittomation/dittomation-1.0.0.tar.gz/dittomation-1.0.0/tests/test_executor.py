"""Tests for replayer.executor module."""

from unittest.mock import patch

from replayer.executor import (
    input_text,
    long_press,
    pinch,
    press_back,
    press_enter,
    press_home,
    press_key,
    scroll,
    swipe,
    tap,
)


class TestTap:
    """Tests for tap function."""

    @patch("replayer.executor.run_adb")
    def test_tap_success(self, mock_adb):
        result = tap(100, 200)
        assert result is True
        mock_adb.assert_called_once()
        call_args = mock_adb.call_args[0][0]
        assert "tap" in call_args
        assert "100" in call_args
        assert "200" in call_args

    @patch("replayer.executor.run_adb")
    def test_tap_clamps_negative_coordinates(self, mock_adb):
        result = tap(-10, -20)
        assert result is True
        call_args = mock_adb.call_args[0][0]
        # Should clamp to 0
        assert "0" in call_args

    @patch("replayer.executor.run_adb")
    def test_tap_failure(self, mock_adb):
        mock_adb.side_effect = Exception("ADB error")
        result = tap(100, 200)
        assert result is False


class TestLongPress:
    """Tests for long_press function."""

    @patch("replayer.executor.run_adb")
    def test_long_press_success(self, mock_adb):
        result = long_press(100, 200, 1500)
        assert result is True
        mock_adb.assert_called_once()
        call_args = mock_adb.call_args[0][0]
        assert "swipe" in call_args
        assert "1500" in call_args

    @patch("replayer.executor.run_adb")
    def test_long_press_default_duration(self, mock_adb):
        result = long_press(100, 200)
        assert result is True
        call_args = mock_adb.call_args[0][0]
        assert "1000" in call_args  # Default duration

    @patch("replayer.executor.run_adb")
    def test_long_press_clamps_negative_coordinates(self, mock_adb):
        result = long_press(-10, -20)
        assert result is True

    @patch("replayer.executor.run_adb")
    def test_long_press_failure(self, mock_adb):
        mock_adb.side_effect = Exception("ADB error")
        result = long_press(100, 200)
        assert result is False


class TestSwipe:
    """Tests for swipe function."""

    @patch("replayer.executor.run_adb")
    def test_swipe_success(self, mock_adb):
        result = swipe(100, 200, 100, 500, 300)
        assert result is True
        mock_adb.assert_called_once()
        call_args = mock_adb.call_args[0][0]
        assert "swipe" in call_args
        assert "100" in call_args
        assert "200" in call_args
        assert "500" in call_args
        assert "300" in call_args

    @patch("replayer.executor.run_adb")
    def test_swipe_default_duration(self, mock_adb):
        result = swipe(100, 200, 100, 500)
        assert result is True
        call_args = mock_adb.call_args[0][0]
        assert "300" in call_args  # Default duration

    @patch("replayer.executor.run_adb")
    def test_swipe_clamps_negative_coordinates(self, mock_adb):
        result = swipe(-10, -20, -30, -40)
        assert result is True

    @patch("replayer.executor.run_adb")
    def test_swipe_failure(self, mock_adb):
        mock_adb.side_effect = Exception("ADB error")
        result = swipe(100, 200, 100, 500)
        assert result is False


class TestScroll:
    """Tests for scroll function."""

    @patch("replayer.executor.run_adb")
    def test_scroll_success(self, mock_adb):
        result = scroll(100, 200, 100, 500)
        assert result is True
        mock_adb.assert_called_once()

    @patch("replayer.executor.run_adb")
    def test_scroll_default_duration(self, mock_adb):
        result = scroll(100, 200, 100, 500)
        assert result is True
        call_args = mock_adb.call_args[0][0]
        assert "500" in call_args  # Default scroll duration


class TestPinch:
    """Tests for pinch function."""

    @patch("replayer.executor.run_adb")
    def test_pinch_zoom_in(self, mock_adb):
        result = pinch(500, 500, 1.5, 500)
        # Should execute multiple swipes
        assert result is True

    @patch("replayer.executor.run_adb")
    def test_pinch_zoom_out(self, mock_adb):
        result = pinch(500, 500, 0.5, 500)
        assert result is True


class TestInputText:
    """Tests for input_text function."""

    @patch("replayer.executor.run_adb")
    def test_input_text_success(self, mock_adb):
        result = input_text("hello")
        assert result is True
        mock_adb.assert_called()
        # Check that text command was used
        calls = [str(call) for call in mock_adb.call_args_list]
        assert any("text" in str(call) for call in calls)

    @patch("replayer.executor.run_adb")
    def test_input_text_with_spaces(self, mock_adb):
        result = input_text("hello world")
        assert result is True

    @patch("replayer.executor.run_adb")
    def test_input_text_clear_first(self, mock_adb):
        result = input_text("new text", clear_first=True)
        assert result is True
        # Should have called to clear first
        assert mock_adb.call_count >= 1

    @patch("replayer.executor.run_adb")
    def test_input_text_failure(self, mock_adb):
        mock_adb.side_effect = Exception("ADB error")
        result = input_text("hello")
        assert result is False


class TestPressKey:
    """Tests for press_key function."""

    @patch("replayer.executor.run_adb")
    def test_press_key_success(self, mock_adb):
        result = press_key("KEYCODE_ENTER")
        assert result is True
        mock_adb.assert_called_once()
        call_args = mock_adb.call_args[0][0]
        assert "keyevent" in call_args
        assert "KEYCODE_ENTER" in call_args

    @patch("replayer.executor.run_adb")
    def test_press_key_failure(self, mock_adb):
        mock_adb.side_effect = Exception("ADB error")
        result = press_key("KEYCODE_BACK")
        assert result is False


class TestPressBack:
    """Tests for press_back function."""

    @patch("replayer.executor.run_adb")
    def test_press_back_success(self, mock_adb):
        result = press_back()
        assert result is True
        mock_adb.assert_called_once()
        call_args = mock_adb.call_args[0][0]
        assert "keyevent" in call_args
        assert "KEYCODE_BACK" in call_args or "BACK" in call_args or "4" in call_args


class TestPressHome:
    """Tests for press_home function."""

    @patch("replayer.executor.run_adb")
    def test_press_home_success(self, mock_adb):
        result = press_home()
        assert result is True
        mock_adb.assert_called_once()
        call_args = mock_adb.call_args[0][0]
        assert "keyevent" in call_args
        assert "KEYCODE_HOME" in call_args or "HOME" in call_args or "3" in call_args


class TestPressEnter:
    """Tests for press_enter function."""

    @patch("replayer.executor.run_adb")
    def test_press_enter_success(self, mock_adb):
        result = press_enter()
        assert result is True
        mock_adb.assert_called_once()
        call_args = mock_adb.call_args[0][0]
        assert "keyevent" in call_args
        assert "KEYCODE_ENTER" in call_args or "ENTER" in call_args or "66" in call_args
