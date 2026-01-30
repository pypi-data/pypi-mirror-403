"""
DittoMation Replayer Module.

This module provides replay functionality for executing Android automation:
- Workflow replay with smart element location
- Natural language command execution
- Text-based command parsing and execution
- Gesture execution via ADB
- Smart element locators with fallback strategies

Usage:
    from replayer import GestureExecutor, ElementLocator, NaturalLanguageRunner

    # Execute gestures
    executor = GestureExecutor()
    executor.tap(100, 200)

    # Locate elements
    locator = ElementLocator()
    result = locator.find_element(text="Login")

    # Natural language commands
    runner = NaturalLanguageRunner()
    runner.execute("tap the Login button")
"""

from .executor import GestureExecutor
from .locator import ElementLocator, LocatorResult
from .main import ReplaySession
from .nl_runner import NaturalLanguageRunner
from .text_runner import TextRunner

__all__ = [
    # Main replay classes
    "ReplaySession",
    # Gesture execution
    "GestureExecutor",
    # Element location
    "LocatorResult",
    "ElementLocator",
    # Command runners
    "NaturalLanguageRunner",
    "TextRunner",
]
