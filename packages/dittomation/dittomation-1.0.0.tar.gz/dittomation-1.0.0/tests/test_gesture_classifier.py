"""Tests for recorder.gesture_classifier module."""

from dataclasses import dataclass

from recorder.gesture_classifier import (
    Gesture,
    GestureClassifier,
    TouchPoint,
    TouchTrack,
    describe_gesture,
)


# Mock TouchEvent for testing
@dataclass
class MockTouchEvent:
    type: str
    screen_x: int
    screen_y: int
    timestamp: float
    tracking_id: int = 0


class TestTouchPoint:
    """Tests for TouchPoint dataclass."""

    def test_create_touch_point(self):
        point = TouchPoint(x=100, y=200, timestamp=1.0, tracking_id=0)
        assert point.x == 100
        assert point.y == 200
        assert point.timestamp == 1.0
        assert point.tracking_id == 0


class TestTouchTrack:
    """Tests for TouchTrack dataclass."""

    def test_create_touch_track(self):
        start = TouchPoint(100, 200, 1.0, 0)
        track = TouchTrack(tracking_id=0, start=start, current=start, points=[start])
        assert track.tracking_id == 0
        assert track.start == start

    def test_update(self):
        start = TouchPoint(100, 200, 1.0, 0)
        track = TouchTrack(tracking_id=0, start=start, current=start, points=[start])
        track.update(150, 250, 1.5)
        assert track.current.x == 150
        assert track.current.y == 250
        assert len(track.points) == 2

    def test_duration_ms(self):
        start = TouchPoint(100, 200, 1.0, 0)
        track = TouchTrack(tracking_id=0, start=start, current=start, points=[start])
        track.update(150, 250, 2.0)  # 1 second later
        assert track.duration_ms == 1000.0

    def test_distance(self):
        start = TouchPoint(0, 0, 1.0, 0)
        track = TouchTrack(tracking_id=0, start=start, current=start, points=[start])
        track.update(300, 400, 1.5)  # 3-4-5 triangle = distance 500
        assert track.distance == 500.0

    def test_direction_right(self):
        start = TouchPoint(0, 0, 1.0, 0)
        track = TouchTrack(tracking_id=0, start=start, current=start, points=[start])
        track.update(200, 0, 1.5)
        assert track.direction == "right"

    def test_direction_left(self):
        start = TouchPoint(200, 0, 1.0, 0)
        track = TouchTrack(tracking_id=0, start=start, current=start, points=[start])
        track.update(0, 0, 1.5)
        assert track.direction == "left"

    def test_direction_up(self):
        start = TouchPoint(0, 200, 1.0, 0)
        track = TouchTrack(tracking_id=0, start=start, current=start, points=[start])
        track.update(0, 0, 1.5)
        assert track.direction == "up"

    def test_direction_down(self):
        start = TouchPoint(0, 0, 1.0, 0)
        track = TouchTrack(tracking_id=0, start=start, current=start, points=[start])
        track.update(0, 200, 1.5)
        assert track.direction == "down"

    def test_direction_none_minimal_movement(self):
        start = TouchPoint(100, 100, 1.0, 0)
        track = TouchTrack(tracking_id=0, start=start, current=start, points=[start])
        track.update(110, 110, 1.5)  # Less than SWIPE_MIN_DISTANCE_PX
        assert track.direction is None


class TestGesture:
    """Tests for Gesture dataclass."""

    def test_create_tap_gesture(self):
        gesture = Gesture(type="tap", start=(100, 200), end=(100, 200), duration_ms=100)
        assert gesture.type == "tap"
        assert gesture.start == (100, 200)
        assert gesture.duration_ms == 100

    def test_to_dict_tap(self):
        gesture = Gesture(type="tap", start=(100, 200), end=(100, 200), duration_ms=100)
        d = gesture.to_dict()
        assert d["type"] == "tap"
        assert d["start"] == [100, 200]
        assert d["duration_ms"] == 100

    def test_to_dict_swipe(self):
        gesture = Gesture(
            type="swipe",
            start=(100, 200),
            end=(100, 400),
            duration_ms=300,
            direction="down",
            distance=200,
        )
        d = gesture.to_dict()
        assert d["type"] == "swipe"
        assert d["direction"] == "down"
        assert d["distance"] == 200

    def test_to_dict_pinch(self):
        gesture = Gesture(
            type="pinch", start=(100, 200), end=(100, 200), duration_ms=500, scale=1.5
        )
        d = gesture.to_dict()
        assert d["type"] == "pinch"
        assert d["scale"] == 1.5


class TestGestureClassifier:
    """Tests for GestureClassifier class."""

    def test_init(self):
        classifier = GestureClassifier()
        assert classifier._tracks == {}
        assert classifier._completed_gesture is None

    def test_reset(self):
        classifier = GestureClassifier()
        # Simulate some state
        classifier._tracks[0] = "track"
        classifier._completed_gesture = "gesture"
        classifier.reset()
        assert classifier._tracks == {}
        assert classifier._completed_gesture is None

    def test_classify_tap(self):
        classifier = GestureClassifier()

        # Touch down
        classifier.feed(MockTouchEvent("touch_down", 100, 200, 1.0, 0))
        assert classifier.is_active()

        # Touch up (quick, no movement = tap)
        classifier.feed(MockTouchEvent("touch_up", 100, 200, 1.1, 0))

        gesture = classifier.get_gesture()
        assert gesture is not None
        assert gesture.type == "tap"
        assert gesture.start == (100, 200)

    def test_classify_long_press(self):
        classifier = GestureClassifier()

        # Touch down
        classifier.feed(MockTouchEvent("touch_down", 100, 200, 1.0, 0))

        # Touch up after long duration (> TAP_MAX_DURATION_MS)
        classifier.feed(MockTouchEvent("touch_up", 100, 200, 2.0, 0))  # 1 second

        gesture = classifier.get_gesture()
        assert gesture is not None
        assert gesture.type == "long_press"

    def test_classify_swipe(self):
        classifier = GestureClassifier()

        # Touch down
        classifier.feed(MockTouchEvent("touch_down", 100, 200, 1.0, 0))

        # Move
        classifier.feed(MockTouchEvent("touch_move", 100, 400, 1.1, 0))

        # Touch up (significant movement = swipe)
        classifier.feed(MockTouchEvent("touch_up", 100, 500, 1.2, 0))

        gesture = classifier.get_gesture()
        assert gesture is not None
        assert gesture.type == "swipe"
        assert gesture.direction == "down"

    def test_classify_scroll_with_checker(self):
        def scrollable_checker(x, y):
            return True  # Everything is scrollable

        classifier = GestureClassifier(scrollable_checker=scrollable_checker)

        classifier.feed(MockTouchEvent("touch_down", 100, 200, 1.0, 0))
        classifier.feed(MockTouchEvent("touch_move", 100, 400, 1.1, 0))
        classifier.feed(MockTouchEvent("touch_up", 100, 500, 1.2, 0))

        gesture = classifier.get_gesture()
        assert gesture is not None
        assert gesture.type == "scroll"

    def test_is_active(self):
        classifier = GestureClassifier()
        assert not classifier.is_active()

        classifier.feed(MockTouchEvent("touch_down", 100, 200, 1.0, 0))
        assert classifier.is_active()

        classifier.feed(MockTouchEvent("touch_up", 100, 200, 1.1, 0))
        assert not classifier.is_active()

    def test_get_active_tracks(self):
        classifier = GestureClassifier()
        classifier.feed(MockTouchEvent("touch_down", 100, 200, 1.0, 0))

        tracks = classifier.get_active_tracks()
        assert len(tracks) == 1
        assert tracks[0].tracking_id == 0

    def test_get_gesture_returns_none_when_not_complete(self):
        classifier = GestureClassifier()
        classifier.feed(MockTouchEvent("touch_down", 100, 200, 1.0, 0))
        assert classifier.get_gesture() is None

    def test_get_gesture_clears_after_read(self):
        classifier = GestureClassifier()
        classifier.feed(MockTouchEvent("touch_down", 100, 200, 1.0, 0))
        classifier.feed(MockTouchEvent("touch_up", 100, 200, 1.1, 0))

        gesture1 = classifier.get_gesture()
        gesture2 = classifier.get_gesture()

        assert gesture1 is not None
        assert gesture2 is None


class TestDescribeGesture:
    """Tests for describe_gesture function."""

    def test_describe_tap(self):
        gesture = Gesture("tap", (100, 200), (100, 200), 50)
        desc = describe_gesture(gesture)
        assert "Tap" in desc
        assert "100" in desc
        assert "200" in desc

    def test_describe_long_press(self):
        gesture = Gesture("long_press", (100, 200), (100, 200), 1500)
        desc = describe_gesture(gesture)
        assert "Long press" in desc
        assert "1500ms" in desc

    def test_describe_swipe(self):
        gesture = Gesture("swipe", (100, 200), (100, 400), 300, direction="down", distance=200)
        desc = describe_gesture(gesture)
        assert "Swipe" in desc
        assert "down" in desc
        assert "200px" in desc

    def test_describe_scroll(self):
        gesture = Gesture("scroll", (100, 200), (100, 400), 300, direction="down", distance=200)
        desc = describe_gesture(gesture)
        assert "Scroll" in desc
        assert "down" in desc

    def test_describe_pinch_zoom_in(self):
        gesture = Gesture("pinch", (100, 200), (100, 200), 500, scale=1.5)
        desc = describe_gesture(gesture)
        assert "Pinch" in desc
        assert "zoom in" in desc
        assert "1.5" in desc

    def test_describe_pinch_zoom_out(self):
        gesture = Gesture("pinch", (100, 200), (100, 200), 500, scale=0.5)
        desc = describe_gesture(gesture)
        assert "Pinch" in desc
        assert "zoom out" in desc

    def test_describe_unknown(self):
        gesture = Gesture("unknown_type", (0, 0), (0, 0), 0)
        desc = describe_gesture(gesture)
        assert "Unknown" in desc


class TestMultiTouchGestures:
    """Tests for multi-touch gesture classification."""

    def test_two_finger_pinch(self):
        classifier = GestureClassifier()

        # First finger down
        classifier.feed(MockTouchEvent("touch_down", 100, 200, 1.0, 0))

        # Second finger down
        classifier.feed(MockTouchEvent("touch_down", 300, 200, 1.0, 1))

        # Move fingers apart (zoom in)
        classifier.feed(MockTouchEvent("touch_move", 50, 200, 1.1, 0))
        classifier.feed(MockTouchEvent("touch_move", 350, 200, 1.1, 1))

        # First finger up - this should complete pinch
        classifier.feed(MockTouchEvent("touch_up", 50, 200, 1.2, 0))

        gesture = classifier.get_gesture()
        assert gesture is not None
        assert gesture.type == "pinch"
