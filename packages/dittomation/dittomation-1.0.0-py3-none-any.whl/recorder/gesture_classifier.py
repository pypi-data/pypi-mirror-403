"""
Gesture Classifier - Classifies touch sequences into gestures.

Analyzes touch events to detect taps, long presses, swipes, scrolls, and pinches.
"""

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

try:
    from recorder.event_listener import TouchEvent
except ImportError:
    from event_listener import TouchEvent


# Gesture classification thresholds
TAP_MAX_DURATION_MS = 500  # Max duration for tap (vs long press)
TAP_MAX_MOVEMENT_PX = 50  # Max movement for tap/long_press (vs swipe)
SWIPE_MIN_DISTANCE_PX = 50  # Min distance for swipe
PINCH_DISTANCE_THRESHOLD = 30  # Min change in finger distance for pinch


@dataclass
class TouchPoint:
    """Represents a touch point in time."""

    x: int
    y: int
    timestamp: float
    tracking_id: int


@dataclass
class TouchTrack:
    """Tracks a single finger's movement."""

    tracking_id: int
    start: TouchPoint
    current: TouchPoint
    points: List[TouchPoint] = field(default_factory=list)

    def update(self, x: int, y: int, timestamp: float) -> None:
        """Update current position."""
        self.current = TouchPoint(x, y, timestamp, self.tracking_id)
        self.points.append(self.current)

    @property
    def duration_ms(self) -> float:
        """Duration from start to current in milliseconds."""
        return (self.current.timestamp - self.start.timestamp) * 1000

    @property
    def distance(self) -> float:
        """Euclidean distance from start to current."""
        dx = self.current.x - self.start.x
        dy = self.current.y - self.start.y
        return math.sqrt(dx * dx + dy * dy)

    @property
    def direction(self) -> Optional[str]:
        """
        Primary direction of movement.

        Returns:
            'up', 'down', 'left', 'right', or None if minimal movement
        """
        dx = self.current.x - self.start.x
        dy = self.current.y - self.start.y

        if abs(dx) < SWIPE_MIN_DISTANCE_PX and abs(dy) < SWIPE_MIN_DISTANCE_PX:
            return None

        # Determine dominant direction
        if abs(dx) > abs(dy):
            return "right" if dx > 0 else "left"
        else:
            return "down" if dy > 0 else "up"


@dataclass
class Gesture:
    """Represents a classified gesture."""

    type: str  # tap, long_press, swipe, scroll, pinch
    start: Tuple[int, int]
    end: Tuple[int, int]
    duration_ms: int
    direction: Optional[str] = None
    distance: int = 0
    scale: float = 1.0  # For pinch: >1 zoom in, <1 zoom out

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "type": self.type,
            "start": list(self.start),
            "end": list(self.end),
            "duration_ms": self.duration_ms,
        }

        if self.direction:
            result["direction"] = self.direction

        if self.distance > 0:
            result["distance"] = self.distance

        if self.type == "pinch":
            result["scale"] = self.scale

        return result


class GestureClassifier:
    """
    Classifies touch event sequences into gestures.

    Usage:
        classifier = GestureClassifier()
        classifier.feed(touch_down_event)
        classifier.feed(touch_move_event)
        classifier.feed(touch_up_event)
        gesture = classifier.get_gesture()
    """

    def __init__(self, scrollable_checker=None):
        """
        Initialize gesture classifier.

        Args:
            scrollable_checker: Optional function(x, y) -> bool to check if
                               coordinates are in a scrollable container
        """
        self._tracks: Dict[int, TouchTrack] = {}
        self._completed_gesture: Optional[Gesture] = None
        self._scrollable_checker = scrollable_checker

        # Multi-touch tracking for pinch
        self._initial_finger_distance: Optional[float] = None

    def reset(self) -> None:
        """Reset classifier state."""
        self._tracks.clear()
        self._completed_gesture = None
        self._initial_finger_distance = None

    def feed(self, event: TouchEvent) -> None:
        """
        Feed a touch event to the classifier.

        Args:
            event: TouchEvent to process
        """
        tracking_id = event.tracking_id

        if event.type == "touch_down":
            # Start new track
            start_point = TouchPoint(event.screen_x, event.screen_y, event.timestamp, tracking_id)
            self._tracks[tracking_id] = TouchTrack(
                tracking_id=tracking_id,
                start=start_point,
                current=start_point,
                points=[start_point],
            )

            # Track initial distance for multi-touch
            if len(self._tracks) == 2:
                self._initial_finger_distance = self._calculate_finger_distance()

        elif event.type == "touch_move":
            if tracking_id in self._tracks:
                self._tracks[tracking_id].update(event.screen_x, event.screen_y, event.timestamp)

        elif event.type == "touch_up":
            if tracking_id in self._tracks:
                track = self._tracks[tracking_id]
                track.update(event.screen_x, event.screen_y, event.timestamp)

                # Check if this completes a gesture
                remaining_tracks = len(self._tracks) - 1

                if remaining_tracks == 0:
                    # Single touch gesture completed
                    self._completed_gesture = self._classify_single_touch(track)
                elif remaining_tracks == 1 and self._initial_finger_distance is not None:
                    # Pinch gesture completed
                    self._completed_gesture = self._classify_pinch()

                # Remove completed track
                del self._tracks[tracking_id]

    def _calculate_finger_distance(self) -> float:
        """Calculate distance between two fingers."""
        if len(self._tracks) != 2:
            return 0

        tracks = list(self._tracks.values())
        dx = tracks[0].current.x - tracks[1].current.x
        dy = tracks[0].current.y - tracks[1].current.y
        return math.sqrt(dx * dx + dy * dy)

    def _classify_single_touch(self, track: TouchTrack) -> Gesture:
        """
        Classify a single-touch gesture.

        Args:
            track: Completed touch track

        Returns:
            Classified Gesture
        """
        duration_ms = int(track.duration_ms)
        distance = int(track.distance)
        start = (track.start.x, track.start.y)
        end = (track.current.x, track.current.y)

        # Check for tap vs long press
        if distance < TAP_MAX_MOVEMENT_PX:
            if duration_ms < TAP_MAX_DURATION_MS:
                return Gesture(type="tap", start=start, end=start, duration_ms=duration_ms)
            else:
                return Gesture(type="long_press", start=start, end=start, duration_ms=duration_ms)

        # It's a swipe/scroll
        direction = track.direction

        # Check if it's within a scrollable container
        is_scroll = False
        if self._scrollable_checker:
            is_scroll = self._scrollable_checker(track.start.x, track.start.y)

        gesture_type = "scroll" if is_scroll else "swipe"

        return Gesture(
            type=gesture_type,
            start=start,
            end=end,
            duration_ms=duration_ms,
            direction=direction,
            distance=distance,
        )

    def _classify_pinch(self) -> Gesture:
        """
        Classify a pinch gesture.

        Returns:
            Classified pinch Gesture
        """
        if not self._initial_finger_distance or len(self._tracks) < 1:
            # Fallback
            return Gesture(type="pinch", start=(0, 0), end=(0, 0), duration_ms=0, scale=1.0)

        final_distance = self._calculate_finger_distance()

        # Calculate scale factor with division by zero check
        if self._initial_finger_distance > 0:
            scale = final_distance / self._initial_finger_distance
        else:
            scale = 1.0

        # Get center point of gesture
        tracks = list(self._tracks.values())
        if len(tracks) >= 1:
            center_x = sum(t.current.x for t in tracks) // len(tracks)
            center_y = sum(t.current.y for t in tracks) // len(tracks)
            start_x = sum(t.start.x for t in tracks) // len(tracks)
            start_y = sum(t.start.y for t in tracks) // len(tracks)
        else:
            center_x = center_y = start_x = start_y = 0

        # Duration from first touch with additional check
        if tracks:
            min_start = min(t.start.timestamp for t in tracks)
            max_end = max(t.current.timestamp for t in tracks)
            duration_ms = int((max_end - min_start) * 1000)
        else:
            duration_ms = 0

        return Gesture(
            type="pinch",
            start=(start_x, start_y),
            end=(center_x, center_y),
            duration_ms=duration_ms,
            scale=scale,
            distance=int(abs(final_distance - self._initial_finger_distance)),
        )

    def get_gesture(self) -> Optional[Gesture]:
        """
        Get the completed gesture if available.

        Returns:
            Gesture if completed, None otherwise
        """
        gesture = self._completed_gesture
        self._completed_gesture = None
        return gesture

    def is_active(self) -> bool:
        """Check if gesture is in progress."""
        return len(self._tracks) > 0

    def get_active_tracks(self) -> List[TouchTrack]:
        """Get currently active touch tracks."""
        return list(self._tracks.values())


def describe_gesture(gesture: Gesture) -> str:
    """
    Generate human-readable description of gesture.

    Args:
        gesture: Gesture to describe

    Returns:
        Description string
    """
    if gesture.type == "tap":
        return f"Tap at ({gesture.start[0]}, {gesture.start[1]})"

    elif gesture.type == "long_press":
        return f"Long press at ({gesture.start[0]}, {gesture.start[1]}) for {gesture.duration_ms}ms"

    elif gesture.type == "swipe":
        return (
            f"Swipe {gesture.direction} from ({gesture.start[0]}, {gesture.start[1]}) "
            f"to ({gesture.end[0]}, {gesture.end[1]}), {gesture.distance}px"
        )

    elif gesture.type == "scroll":
        return (
            f"Scroll {gesture.direction} from ({gesture.start[0]}, {gesture.start[1]}) "
            f"to ({gesture.end[0]}, {gesture.end[1]}), {gesture.distance}px"
        )

    elif gesture.type == "pinch":
        action = "zoom in" if gesture.scale > 1 else "zoom out"
        return (
            f"Pinch {action} at ({gesture.start[0]}, {gesture.start[1]}), scale={gesture.scale:.2f}"
        )

    return f"Unknown gesture: {gesture.type}"
