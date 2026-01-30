"""
DittoMation Recorder Module.

This module provides recording functionality for capturing Android interactions:
- Interactive step-by-step recording
- Automated touch event recording via getevent
- Gesture classification (tap, swipe, long press, etc.)
- UI hierarchy capture and element matching
- Workflow storage and management

Usage:
    from recorder import InteractiveRecorder, WorkflowRecorder

    # Interactive recording
    recorder = InteractiveRecorder()
    recorder.start_recording("my_workflow.json")

    # Programmatic workflow recording
    workflow = WorkflowRecorder()
    workflow.add_step(...)
    workflow.save("my_workflow.json")
"""

# Lazy imports to avoid circular dependencies
__all__ = [
    # Main recording classes
    "InteractiveRecorder",
    "RecordingSession",
    # Workflow management
    "WorkflowStep",
    "WorkflowRecorder",
    # Gesture classification
    "TouchPoint",
    "TouchTrack",
    "Gesture",
    "GestureClassifier",
    # Event handling
    "TouchEvent",
    "TouchEventListener",
    "MultiTouchState",
]


def __getattr__(name):
    """Lazy import of submodules to avoid circular imports."""
    if name in ("TouchEvent", "TouchEventListener", "MultiTouchState"):
        from .event_listener import MultiTouchState, TouchEvent, TouchEventListener

        return {
            "TouchEvent": TouchEvent,
            "TouchEventListener": TouchEventListener,
            "MultiTouchState": MultiTouchState,
        }[name]

    if name in ("Gesture", "GestureClassifier", "TouchPoint", "TouchTrack"):
        from .gesture_classifier import Gesture, GestureClassifier, TouchPoint, TouchTrack

        return {
            "Gesture": Gesture,
            "GestureClassifier": GestureClassifier,
            "TouchPoint": TouchPoint,
            "TouchTrack": TouchTrack,
        }[name]

    if name == "InteractiveRecorder":
        from .interactive_recorder import InteractiveRecorder

        return InteractiveRecorder

    if name == "RecordingSession":
        from .main import RecordingSession

        return RecordingSession

    if name in ("WorkflowRecorder", "WorkflowStep"):
        from .workflow import WorkflowRecorder, WorkflowStep

        return {"WorkflowRecorder": WorkflowRecorder, "WorkflowStep": WorkflowStep}[name]

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
