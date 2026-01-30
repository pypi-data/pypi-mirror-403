"""
UI Dumper - Captures and parses UI hierarchy from Android device.

Uses uiautomator to dump the view hierarchy and parses it into
a structured format for element matching.
"""

import os
import re
import sys
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from recorder.adb_wrapper import dump_ui
except ImportError:
    from adb_wrapper import dump_ui

from core.exceptions import UIHierarchyError
from core.logging_config import get_logger

# Module logger
logger = get_logger("ui_dumper")


def parse_bounds(bounds_str: str) -> Tuple[int, int, int, int]:
    """
    Parse bounds string to tuple.

    Args:
        bounds_str: Bounds in format "[x1,y1][x2,y2]"

    Returns:
        Tuple of (x1, y1, x2, y2)
    """
    if not bounds_str:
        return (0, 0, 0, 0)

    match = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds_str)
    if match:
        try:
            return tuple(int(x) for x in match.groups())
        except ValueError:
            return (0, 0, 0, 0)
    return (0, 0, 0, 0)


def get_center(bounds: Tuple[int, int, int, int]) -> Tuple[int, int]:
    """
    Get center point of bounds.

    Args:
        bounds: Tuple of (x1, y1, x2, y2)

    Returns:
        Tuple of (center_x, center_y)
    """
    if not bounds or len(bounds) != 4:
        return (0, 0)

    x1, y1, x2, y2 = bounds
    # Ensure valid bounds (x2 >= x1, y2 >= y1)
    if x2 < x1:
        x1, x2 = x2, x1
    if y2 < y1:
        y1, y2 = y2, y1

    return (x1 + x2) // 2, (y1 + y2) // 2


def element_to_dict(element: ET.Element, parent_path: str = "") -> Dict[str, Any]:
    """
    Convert XML element to dictionary representation.

    Args:
        element: XML element from UI hierarchy
        parent_path: XPath of parent element

    Returns:
        Dictionary with element properties
    """
    # Get all attributes
    attrib = element.attrib

    # Parse bounds
    bounds_str = attrib.get("bounds", "[0,0][0,0]")
    bounds = parse_bounds(bounds_str)

    # Build xpath
    class_name = attrib.get("class", "node")
    index_str = attrib.get("index", "0")

    # Safely parse index
    try:
        index = int(index_str)
    except (ValueError, TypeError):
        index = 0

    if parent_path:
        xpath = f"{parent_path}/{class_name}[{index + 1}]"
    else:
        xpath = f"//{class_name}"

    return {
        "class": class_name,
        "resource_id": attrib.get("resource-id", ""),
        "content_desc": attrib.get("content-desc", ""),
        "text": attrib.get("text", ""),
        "bounds": bounds,
        "bounds_str": bounds_str,
        "clickable": attrib.get("clickable", "false") == "true",
        "scrollable": attrib.get("scrollable", "false") == "true",
        "long_clickable": attrib.get("long-clickable", "false") == "true",
        "focusable": attrib.get("focusable", "false") == "true",
        "enabled": attrib.get("enabled", "true") == "true",
        "selected": attrib.get("selected", "false") == "true",
        "checkable": attrib.get("checkable", "false") == "true",
        "checked": attrib.get("checked", "false") == "true",
        "package": attrib.get("package", ""),
        "index": index,
        "xpath": xpath,
    }


def get_all_elements(
    tree: ET.Element, parent_path: str = "", elements: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Flatten UI tree to list of element dicts.

    Args:
        tree: Root element or subtree
        parent_path: XPath prefix for current tree level
        elements: Accumulator for recursive calls

    Returns:
        List of element dictionaries
    """
    if elements is None:
        elements = []

    # Process current element
    elem_dict = element_to_dict(tree, parent_path)
    elements.append(elem_dict)

    # Process children
    child_counts = {}  # Track sibling indices by class
    for child in tree:
        child_class = child.attrib.get("class", "node")
        child_counts[child_class] = child_counts.get(child_class, 0) + 1

        child_xpath = elem_dict["xpath"]
        get_all_elements(child, child_xpath, elements)

    return elements


def capture_ui(output_path: Optional[str] = None) -> Tuple[ET.Element, List[Dict[str, Any]]]:
    """
    Capture UI hierarchy and return both tree and flattened elements.

    Args:
        output_path: Optional path to save raw XML

    Returns:
        Tuple of (root_element, list_of_element_dicts)
    """
    root = dump_ui(output_path)
    elements = get_all_elements(root)
    return root, elements


def capture_ui_fast(
    max_retries: int = 5, retry_delay: float = 1.0
) -> Tuple[Optional[ET.Element], List[Dict[str, Any]]]:
    """
    Capture UI hierarchy with retry logic for loading screens.

    Args:
        max_retries: Number of retries if UI dump fails
        retry_delay: Seconds to wait between retries

    Returns:
        Tuple of (root_element, list_of_element_dicts)
    """
    try:
        root = dump_ui(max_retries=max_retries, retry_delay=retry_delay)
        elements = get_all_elements(root)
        logger.debug(f"Captured UI with {len(elements)} elements")
        return root, elements
    except UIHierarchyError as e:
        logger.warning(f"UI dump failed: {e.message}")
        return None, []
    except Exception as e:
        logger.warning(f"UI dump failed: {e}")
        return None, []


def find_scrollable_parent(
    elements: List[Dict[str, Any]], x: int, y: int
) -> Optional[Dict[str, Any]]:
    """
    Find scrollable container at given coordinates.

    Args:
        elements: List of element dicts
        x: X coordinate
        y: Y coordinate

    Returns:
        Scrollable element dict or None
    """
    candidates = []

    for elem in elements:
        if not elem["scrollable"]:
            continue

        x1, y1, x2, y2 = elem["bounds"]
        if x1 <= x <= x2 and y1 <= y <= y2:
            # Calculate area for prioritizing smaller containers
            area = (x2 - x1) * (y2 - y1)
            candidates.append((area, elem))

    if candidates:
        # Return smallest scrollable container
        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]

    return None


def get_element_hierarchy(
    tree: ET.Element, target_bounds: Tuple[int, int, int, int]
) -> List[Dict[str, Any]]:
    """
    Get parent chain for element with given bounds.

    Args:
        tree: Root element
        target_bounds: Bounds tuple to find

    Returns:
        List of element dicts from root to target
    """

    def find_path(element: ET.Element, path: List) -> Optional[List]:
        elem_dict = element_to_dict(element)
        current_path = path + [elem_dict]

        if elem_dict["bounds"] == target_bounds:
            return current_path

        for child in element:
            result = find_path(child, current_path)
            if result:
                return result

        return None

    return find_path(tree, []) or []


def get_siblings(elements: List[Dict[str, Any]], element: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Get sibling elements (same class and parent).

    Args:
        elements: All elements
        element: Target element

    Returns:
        List of sibling elements
    """
    # Find elements with same class and overlapping parent xpath
    target_class = element["class"]
    target_xpath = element["xpath"]

    # Extract parent path
    parent_path = "/".join(target_xpath.split("/")[:-1])

    siblings = []
    for elem in elements:
        if elem["class"] == target_class and elem["xpath"] != target_xpath:
            elem_parent = "/".join(elem["xpath"].split("/")[:-1])
            if elem_parent == parent_path:
                siblings.append(elem)

    return siblings


def pretty_print_element(element: Dict[str, Any]) -> str:
    """
    Format element for display.

    Args:
        element: Element dict

    Returns:
        Formatted string representation
    """
    parts = []

    # Class name (simplified)
    class_name = element["class"].split(".")[-1]
    parts.append(class_name)

    # Resource ID (without package)
    if element["resource_id"]:
        rid = element["resource_id"].split("/")[-1]
        parts.append(f"id={rid}")

    # Text (truncated)
    if element["text"]:
        text = element["text"][:20]
        if len(element["text"]) > 20:
            text += "..."
        parts.append(f'text="{text}"')

    # Content description
    if element["content_desc"]:
        desc = element["content_desc"][:20]
        parts.append(f'desc="{desc}"')

    # Bounds
    x1, y1, x2, y2 = element["bounds"]
    parts.append(f"[{x1},{y1}][{x2},{y2}]")

    return " ".join(parts)
