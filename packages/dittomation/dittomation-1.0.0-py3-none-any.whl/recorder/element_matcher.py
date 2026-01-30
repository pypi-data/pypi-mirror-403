"""
Element Matcher - Matches tap coordinates to UI elements.

Finds UI elements at given coordinates and builds locator chains
with fallback strategies for robust element identification.

Features:
- Confidence scoring for fuzzy element matching
- Smart element selection based on clickability and area
- Ad/sponsored content filtering
- Fallback locator chain generation
"""

import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.logging_config import get_logger

# Module logger
logger = get_logger("element_matcher")


# =============================================================================
# Confidence Scoring System
# =============================================================================


@dataclass
class MatchResult:
    """Result of element matching with confidence score."""

    element: Dict[str, Any]
    confidence: float  # 0.0 to 1.0
    match_details: Dict[str, float]  # Individual score components

    def __repr__(self) -> str:
        text = self.element.get("text", "")[:20] or self.element.get("resource_id", "")
        return f"MatchResult({text!r}, confidence={self.confidence:.2f})"


# Scoring weights for different match types
SCORE_WEIGHTS = {
    "text_exact": 1.0,
    "text_contains": 0.7,
    "text_fuzzy": 0.5,
    "id_exact": 1.0,
    "id_contains": 0.8,
    "id_suffix": 0.7,
    "desc_exact": 1.0,
    "desc_contains": 0.7,
    "desc_fuzzy": 0.5,
    "class_match": 0.3,
    "clickable_bonus": 0.1,
    "enabled_bonus": 0.05,
    "visible_bonus": 0.05,
}

# Default minimum confidence threshold
DEFAULT_MIN_CONFIDENCE = 0.3


def calculate_string_similarity(s1: str, s2: str) -> float:
    """
    Calculate similarity between two strings using multiple methods.

    Returns a score between 0.0 and 1.0.
    """
    if not s1 or not s2:
        return 0.0

    s1_lower = s1.lower()
    s2_lower = s2.lower()

    # Exact match
    if s1_lower == s2_lower:
        return 1.0

    # One contains the other
    if s1_lower in s2_lower or s2_lower in s1_lower:
        shorter = min(len(s1), len(s2))
        longer = max(len(s1), len(s2))
        return shorter / longer * 0.9

    # Word overlap (for multi-word strings)
    words1 = set(s1_lower.split())
    words2 = set(s2_lower.split())
    if words1 and words2:
        overlap = len(words1 & words2)
        total = len(words1 | words2)
        if overlap > 0:
            return overlap / total * 0.8

    # Character-level similarity (Jaccard on character bigrams)
    def get_bigrams(s):
        return set(s[i : i + 2] for i in range(len(s) - 1)) if len(s) > 1 else {s}

    bigrams1 = get_bigrams(s1_lower)
    bigrams2 = get_bigrams(s2_lower)
    if bigrams1 and bigrams2:
        intersection = len(bigrams1 & bigrams2)
        union = len(bigrams1 | bigrams2)
        return intersection / union * 0.6

    return 0.0


def score_element_match(
    element: Dict[str, Any],
    text: Optional[str] = None,
    resource_id: Optional[str] = None,
    content_desc: Optional[str] = None,
    class_name: Optional[str] = None,
) -> MatchResult:
    """
    Calculate confidence score for how well an element matches the criteria.

    Args:
        element: Element dict from UI tree
        text: Text to match against element's text
        resource_id: Resource ID to match (supports partial matching)
        content_desc: Content description to match
        class_name: Class name to match

    Returns:
        MatchResult with confidence score and details
    """
    scores = {}
    max_possible = 0.0

    # Text matching
    if text:
        max_possible += SCORE_WEIGHTS["text_exact"]
        elem_text = element.get("text", "")

        if elem_text:
            if text.lower() == elem_text.lower():
                scores["text_exact"] = SCORE_WEIGHTS["text_exact"]
            elif text.lower() in elem_text.lower() or elem_text.lower() in text.lower():
                scores["text_contains"] = SCORE_WEIGHTS["text_contains"]
            else:
                similarity = calculate_string_similarity(text, elem_text)
                if similarity > 0.3:
                    scores["text_fuzzy"] = SCORE_WEIGHTS["text_fuzzy"] * similarity

    # Resource ID matching
    if resource_id:
        max_possible += SCORE_WEIGHTS["id_exact"]
        elem_id = element.get("resource_id", "")

        if elem_id:
            # Extract just the ID part if full resource ID provided
            search_id = resource_id.split("/")[-1].lower()
            elem_id_part = elem_id.split("/")[-1].lower()

            if search_id == elem_id_part:
                scores["id_exact"] = SCORE_WEIGHTS["id_exact"]
            elif search_id in elem_id_part or elem_id_part in search_id:
                scores["id_contains"] = SCORE_WEIGHTS["id_contains"]
            elif elem_id_part.endswith(search_id) or search_id.endswith(elem_id_part):
                scores["id_suffix"] = SCORE_WEIGHTS["id_suffix"]

    # Content description matching
    if content_desc:
        max_possible += SCORE_WEIGHTS["desc_exact"]
        elem_desc = element.get("content_desc", "")

        if elem_desc:
            if content_desc.lower() == elem_desc.lower():
                scores["desc_exact"] = SCORE_WEIGHTS["desc_exact"]
            elif (
                content_desc.lower() in elem_desc.lower()
                or elem_desc.lower() in content_desc.lower()
            ):
                scores["desc_contains"] = SCORE_WEIGHTS["desc_contains"]
            else:
                similarity = calculate_string_similarity(content_desc, elem_desc)
                if similarity > 0.3:
                    scores["desc_fuzzy"] = SCORE_WEIGHTS["desc_fuzzy"] * similarity

    # Class name matching
    if class_name:
        max_possible += SCORE_WEIGHTS["class_match"]
        elem_class = element.get("class", "")

        if elem_class:
            class_simple = class_name.split(".")[-1].lower()
            elem_class_simple = elem_class.split(".")[-1].lower()

            if class_simple == elem_class_simple or class_simple in elem_class_simple:
                scores["class_match"] = SCORE_WEIGHTS["class_match"]

    # Bonus points for interactive elements
    if element.get("clickable") or element.get("long_clickable"):
        scores["clickable_bonus"] = SCORE_WEIGHTS["clickable_bonus"]

    if element.get("enabled", True):
        scores["enabled_bonus"] = SCORE_WEIGHTS["enabled_bonus"]

    # Calculate final confidence
    total_score = sum(scores.values())

    # Normalize to 0.0-1.0 range
    if max_possible > 0:
        confidence = min(1.0, total_score / max_possible)
    else:
        confidence = 0.0

    return MatchResult(element=element, confidence=confidence, match_details=scores)


def find_elements_with_confidence(
    elements: List[Dict[str, Any]],
    text: Optional[str] = None,
    resource_id: Optional[str] = None,
    content_desc: Optional[str] = None,
    class_name: Optional[str] = None,
    min_confidence: float = DEFAULT_MIN_CONFIDENCE,
    filter_ads: bool = True,
) -> List[MatchResult]:
    """
    Find elements matching criteria with confidence scores.

    Args:
        elements: List of element dicts from UI tree
        text: Text to match
        resource_id: Resource ID to match
        content_desc: Content description to match
        class_name: Class name to match
        min_confidence: Minimum confidence threshold (0.0-1.0)
        filter_ads: Whether to filter out ad elements

    Returns:
        List of MatchResult sorted by confidence (highest first)
    """
    if not any([text, resource_id, content_desc, class_name]):
        return []

    ad_filter = None
    if filter_ads:
        from core.ad_filter import get_ad_filter

        ad_filter = get_ad_filter()
    results = []

    for elem in elements:
        # Skip ad elements
        if ad_filter and ad_filter.is_ad(elem):
            continue

        # Score the element
        result = score_element_match(
            elem,
            text=text,
            resource_id=resource_id,
            content_desc=content_desc,
            class_name=class_name,
        )

        # Include if above threshold
        if result.confidence >= min_confidence:
            results.append(result)

    # Sort by confidence (highest first)
    results.sort(key=lambda r: r.confidence, reverse=True)

    logger.debug(f"Found {len(results)} elements above {min_confidence:.0%} confidence")
    return results


def find_best_match(
    elements: List[Dict[str, Any]],
    text: Optional[str] = None,
    resource_id: Optional[str] = None,
    content_desc: Optional[str] = None,
    class_name: Optional[str] = None,
    min_confidence: float = DEFAULT_MIN_CONFIDENCE,
    filter_ads: bool = True,
) -> Optional[MatchResult]:
    """
    Find the single best matching element.

    Args:
        elements: List of element dicts from UI tree
        text: Text to match
        resource_id: Resource ID to match
        content_desc: Content description to match
        class_name: Class name to match
        min_confidence: Minimum confidence threshold
        filter_ads: Whether to filter out ad elements

    Returns:
        Best MatchResult or None if no match above threshold
    """
    results = find_elements_with_confidence(
        elements,
        text=text,
        resource_id=resource_id,
        content_desc=content_desc,
        class_name=class_name,
        min_confidence=min_confidence,
        filter_ads=filter_ads,
    )

    if results:
        best = results[0]
        logger.debug(f"Best match: {best.confidence:.0%} confidence")
        return best

    return None


def find_elements_at_point(
    elements: List[Dict[str, Any]], x: int, y: int, filter_ads: bool = True
) -> List[Dict[str, Any]]:
    """
    Find all elements containing the given point.

    Args:
        elements: List of element dicts from UI tree
        x: X coordinate
        y: Y coordinate
        filter_ads: Whether to filter out ad elements

    Returns:
        List of elements whose bounds contain the point
    """
    matching = []
    ad_filter = None
    if filter_ads:
        from core.ad_filter import get_ad_filter

        ad_filter = get_ad_filter()

    for elem in elements:
        x1, y1, x2, y2 = elem["bounds"]

        # Check if point is within bounds
        if x1 <= x <= x2 and y1 <= y <= y2:
            # Skip ad elements if filtering is enabled
            if ad_filter and ad_filter.is_ad(elem):
                logger.debug(f"Skipping ad element at ({x}, {y})")
                continue
            matching.append(elem)

    return matching


def calculate_element_area(element: Dict[str, Any]) -> int:
    """
    Calculate area of element bounds.

    Args:
        element: Element dict

    Returns:
        Area in pixels squared
    """
    x1, y1, x2, y2 = element["bounds"]
    return (x2 - x1) * (y2 - y1)


def select_best_match(
    candidates: List[Dict[str, Any]], filter_ads: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Pick the best element from candidates.

    Strategy:
    1. Filter out ad/sponsored elements
    2. Prefer clickable/long-clickable elements
    3. Among those, prefer smaller elements (more specific)
    4. If no clickable, pick smallest element overall

    Args:
        candidates: List of candidate elements
        filter_ads: Whether to filter out ad elements

    Returns:
        Best matching element or None
    """
    if not candidates:
        return None

    # Filter out ad elements first
    if filter_ads:
        from core.ad_filter import get_ad_filter

        ad_filter = get_ad_filter()
        filtered_candidates = [e for e in candidates if not ad_filter.is_ad(e)]

        if len(filtered_candidates) < len(candidates):
            ad_count = len(candidates) - len(filtered_candidates)
            logger.debug(f"Filtered {ad_count} ad element(s) from candidates")

        candidates = filtered_candidates

    if not candidates:
        return None

    # Separate clickable and non-clickable
    clickable = [e for e in candidates if e.get("clickable") or e.get("long_clickable")]
    non_clickable = [e for e in candidates if e not in clickable]

    # Sort by area (ascending - smaller first)
    clickable.sort(key=calculate_element_area)
    non_clickable.sort(key=calculate_element_area)

    # Prefer clickable elements
    if clickable:
        return clickable[0]

    # Fall back to smallest non-clickable
    if non_clickable:
        return non_clickable[0]

    return None


def build_xpath(element: Dict[str, Any]) -> str:
    """
    Build a robust XPath selector for an element.

    Uses multiple attributes for better matching.

    Args:
        element: Element dict

    Returns:
        XPath expression string
    """
    class_name = element.get("class", "node")
    parts = [f"//{class_name}"]

    conditions = []

    # Add resource-id condition
    if element.get("resource_id"):
        # Escape single quotes for XPath
        rid = element["resource_id"].replace("'", "&apos;")
        conditions.append(f"@resource-id='{rid}'")

    # Add text condition
    if element.get("text"):
        # Escape quotes in text for XPath
        text = element["text"].replace("'", "&apos;").replace('"', "&quot;")
        conditions.append(f"@text='{text}'")

    # Add content-desc condition
    if element.get("content_desc"):
        # Escape quotes for XPath
        desc = element["content_desc"].replace("'", "&apos;").replace('"', "&quot;")
        conditions.append(f"@content-desc='{desc}'")

    if conditions:
        return f"{parts[0]}[{' and '.join(conditions)}]"

    # Fall back to class + index
    return f"({parts[0]})[{element.get('index', 0) + 1}]"


def build_locator(element: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate locator with fallback chain.

    Creates a primary locator and a list of fallbacks ordered by reliability.

    Strategy order:
    1. resource-id (most reliable)
    2. content-desc (accessibility)
    3. text (visible label)
    4. xpath (structural)
    5. bounds (last resort)

    Args:
        element: Element dict

    Returns:
        Locator dict with primary strategy and fallbacks
    """
    if not element:
        return {
            "primary": {"strategy": "bounds", "value": (0, 0, 0, 0)},
            "fallbacks": [],
            "bounds": (0, 0, 0, 0),
        }

    locators = []

    # Strategy 1: Resource ID
    if element.get("resource_id"):
        locators.append({"strategy": "id", "value": element["resource_id"]})

    # Strategy 2: Content Description
    if element.get("content_desc"):
        locators.append({"strategy": "content_desc", "value": element["content_desc"]})

    # Strategy 3: Text
    if element.get("text"):
        locators.append({"strategy": "text", "value": element["text"]})

    # Strategy 4: XPath
    xpath = build_xpath(element)
    locators.append({"strategy": "xpath", "value": xpath})

    # Strategy 5: Bounds (always included as final fallback)
    bounds = element.get("bounds", (0, 0, 0, 0))
    locators.append({"strategy": "bounds", "value": bounds})

    # First locator is primary, rest are fallbacks
    if len(locators) > 1:
        return {"primary": locators[0], "fallbacks": locators[1:], "bounds": bounds}
    else:
        return {"primary": locators[0], "fallbacks": [], "bounds": bounds}


def match_element_at_point(
    elements: List[Dict[str, Any]], x: int, y: int
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    """
    Find and match element at given coordinates.

    Convenience function combining find and select.

    Args:
        elements: List of element dicts
        x: X coordinate
        y: Y coordinate

    Returns:
        Tuple of (element_dict, locator_dict)
        If no element found, returns (None, bounds_only_locator)
    """
    candidates = find_elements_at_point(elements, x, y)
    element = select_best_match(candidates)

    if element:
        locator = build_locator(element)
        return element, locator
    else:
        # No element found - use coordinates as locator
        return None, {
            "primary": {"strategy": "bounds", "value": (x, y, x, y)},
            "fallbacks": [],
            "bounds": (x, y, x, y),
        }


def describe_match(element: Optional[Dict[str, Any]], locator: Dict[str, Any]) -> str:
    """
    Generate human-readable description of match.

    Args:
        element: Matched element (or None)
        locator: Generated locator

    Returns:
        Description string
    """
    if not element:
        coords = locator["bounds"]
        return f"No element found at ({coords[0]}, {coords[1]})"

    parts = []

    # Element class (simplified)
    class_name = element["class"].split(".")[-1]
    parts.append(class_name)

    # Primary identifier
    primary = locator["primary"]
    if primary["strategy"] == "id":
        rid = primary["value"].split("/")[-1]
        parts.append(f"#{rid}")
    elif primary["strategy"] == "text":
        parts.append(f'"{primary["value"]}"')
    elif primary["strategy"] == "content_desc":
        parts.append(f'[{primary["value"]}]')

    # Bounds
    x1, y1, x2, y2 = element["bounds"]
    center_x = (x1 + x2) // 2
    center_y = (y1 + y2) // 2
    parts.append(f"@({center_x}, {center_y})")

    return " ".join(parts)


def find_similar_elements(
    elements: List[Dict[str, Any]],
    target: Dict[str, Any],
    min_confidence: float = 0.2,
) -> List[MatchResult]:
    """
    Find elements similar to target with confidence scores.

    Uses the confidence scoring system to find elements that match
    the target's attributes (text, ID, description, class).

    Args:
        elements: All elements
        target: Target element to match
        min_confidence: Minimum confidence threshold

    Returns:
        List of MatchResult sorted by confidence (highest first)
    """
    results = find_elements_with_confidence(
        elements,
        text=target.get("text"),
        resource_id=target.get("resource_id"),
        content_desc=target.get("content_desc"),
        class_name=target.get("class"),
        min_confidence=min_confidence,
        filter_ads=True,
    )

    # Add size similarity bonus
    target_area = calculate_element_area(target)
    if target_area > 0:
        for result in results:
            elem_area = calculate_element_area(result.element)
            size_ratio = min(elem_area, target_area) / max(elem_area, target_area)
            if size_ratio > 0.8:
                # Boost confidence slightly for similar-sized elements
                result.confidence = min(1.0, result.confidence + 0.05)
                result.match_details["size_similarity"] = 0.05

    # Re-sort after bonus
    results.sort(key=lambda r: r.confidence, reverse=True)

    return results


def find_similar_elements_legacy(
    elements: List[Dict[str, Any]], target: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Legacy function: Find elements similar to target.

    Deprecated: Use find_similar_elements() which returns MatchResult with confidence.

    Returns:
        List of similar element dicts (without confidence scores)
    """
    results = find_similar_elements(elements, target)
    return [r.element for r in results]
