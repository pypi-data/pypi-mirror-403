"""
Element Locator - Smart element location with fallback chain.

Finds elements in the current UI using various strategies,
falling back through the chain until a match is found.

Features:
- Confidence-based element location
- Multi-strategy element location with fallback chain
- Ad/sponsored content filtering
- Smart coordinate extraction
"""

import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ad_filter import get_ad_filter
from core.logging_config import get_logger
from recorder.element_matcher import (
    DEFAULT_MIN_CONFIDENCE,
    calculate_string_similarity,
    find_best_match,
)
from recorder.ui_dumper import get_center

# Module logger
logger = get_logger("locator")


class LocatorResult:
    """Result of element location attempt with confidence score."""

    def __init__(
        self,
        found: bool,
        element: Optional[Dict[str, Any]] = None,
        strategy_used: Optional[str] = None,
        coordinates: Optional[Tuple[int, int]] = None,
        fallback_level: int = 0,
        confidence: float = 0.0,
        match_details: Optional[Dict[str, float]] = None,
    ):
        """
        Initialize locator result.

        Args:
            found: Whether element was found
            element: Matched element dict (if found)
            strategy_used: Which strategy succeeded
            coordinates: Target coordinates for gesture
            fallback_level: How many fallbacks were tried (0 = primary worked)
            confidence: Confidence score (0.0-1.0)
            match_details: Breakdown of confidence score components
        """
        self.found = found
        self.element = element
        self.strategy_used = strategy_used
        self.coordinates = coordinates
        self.fallback_level = fallback_level
        self.confidence = confidence
        self.match_details = match_details or {}

    def __str__(self) -> str:
        if self.found:
            return (
                f"Found via {self.strategy_used} at {self.coordinates} "
                f"(confidence: {self.confidence:.0%}, fallback: {self.fallback_level})"
            )
        return "Element not found"

    @property
    def is_high_confidence(self) -> bool:
        """Check if match has high confidence (>= 80%)."""
        return self.confidence >= 0.8

    @property
    def is_low_confidence(self) -> bool:
        """Check if match has low confidence (< 50%)."""
        return self.confidence < 0.5


class ElementLocator:
    """
    Smart element location with confidence scoring.

    Tries multiple strategies and uses confidence scores to find
    the best matching element. Automatically filters out ad/sponsored elements.
    """

    def __init__(
        self,
        filter_ads: bool = True,
        min_confidence: float = DEFAULT_MIN_CONFIDENCE,
    ):
        """
        Initialize element locator.

        Args:
            filter_ads: Whether to filter out ad elements
            min_confidence: Minimum confidence threshold (0.0-1.0)
        """
        self.filter_ads = filter_ads
        self.min_confidence = min_confidence
        self._ad_filter = get_ad_filter() if filter_ads else None

        # Strategy handlers (return element and confidence)
        self._strategies = {
            "id": self._find_by_id,
            "content_desc": self._find_by_content_desc,
            "text": self._find_by_text,
            "xpath": self._find_by_xpath,
            "bounds": self._find_by_bounds,
        }

    def find_element(
        self,
        locator: Dict[str, Any],
        elements: List[Dict[str, Any]],
        min_confidence: Optional[float] = None,
    ) -> LocatorResult:
        """
        Find element using locator with fallback chain and confidence scoring.

        Args:
            locator: Locator dict with primary and fallbacks
            elements: Current UI elements list
            min_confidence: Override minimum confidence threshold

        Returns:
            LocatorResult with match info and confidence score
        """
        threshold = min_confidence if min_confidence is not None else self.min_confidence

        # Filter ad elements if enabled
        if self.filter_ads and self._ad_filter:
            original_count = len(elements)
            elements = [e for e in elements if not self._ad_filter.is_ad(e)]
            if len(elements) < original_count:
                ad_count = original_count - len(elements)
                logger.debug(f"Filtered {ad_count} ad element(s) before location")

        # Build strategy list: primary first, then fallbacks
        strategies_to_try = []

        primary = locator.get("primary", {})
        if primary:
            strategies_to_try.append(primary)

        fallbacks = locator.get("fallbacks", [])
        strategies_to_try.extend(fallbacks)

        best_result: Optional[LocatorResult] = None
        best_confidence = 0.0

        # Try each strategy in order
        for level, strategy in enumerate(strategies_to_try):
            strategy_name = strategy.get("strategy")
            strategy_value = strategy.get("value")

            if strategy_name not in self._strategies:
                continue

            handler = self._strategies[strategy_name]
            element, confidence, details = handler(strategy_value, elements)

            if element and confidence >= threshold:
                # Double-check the element is not an ad
                if self.filter_ads and self._ad_filter and self._ad_filter.is_ad(element):
                    logger.debug(f"Skipping ad element found via {strategy_name}")
                    continue

                # Calculate center coordinates
                bounds = element.get("bounds", (0, 0, 0, 0))
                center = get_center(bounds)

                result = LocatorResult(
                    found=True,
                    element=element,
                    strategy_used=strategy_name,
                    coordinates=center,
                    fallback_level=level,
                    confidence=confidence,
                    match_details=details,
                )

                # If high confidence, return immediately
                if confidence >= 0.9:
                    logger.debug(f"Found via {strategy_name} with {confidence:.0%} confidence")
                    return result

                # Track best match so far
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_result = result

        # Return best match if found
        if best_result:
            logger.debug(
                f"Best match via {best_result.strategy_used} with {best_confidence:.0%} confidence"
            )
            return best_result

        # All strategies failed - use recorded bounds as last resort
        recorded_bounds = locator.get("bounds")
        if recorded_bounds:
            if len(recorded_bounds) == 4:
                center = get_center(tuple(recorded_bounds))
            elif len(recorded_bounds) >= 2:
                # Treat as point
                center = (recorded_bounds[0], recorded_bounds[1])
            else:
                # Invalid bounds, return failure
                return LocatorResult(found=False, confidence=0.0)

            return LocatorResult(
                found=False,
                element=None,
                strategy_used="coordinates",
                coordinates=center,
                fallback_level=len(strategies_to_try),
                confidence=0.0,
            )

        # Complete failure
        return LocatorResult(found=False, confidence=0.0)

    def find_with_confidence(
        self,
        elements: List[Dict[str, Any]],
        text: Optional[str] = None,
        resource_id: Optional[str] = None,
        content_desc: Optional[str] = None,
        class_name: Optional[str] = None,
        min_confidence: Optional[float] = None,
    ) -> LocatorResult:
        """
        Find element by attributes using confidence scoring.

        This is a direct way to find elements without a locator dict.

        Args:
            elements: UI elements list
            text: Text to match
            resource_id: Resource ID to match
            content_desc: Content description to match
            class_name: Class name to match
            min_confidence: Minimum confidence threshold

        Returns:
            LocatorResult with best match
        """
        threshold = min_confidence if min_confidence is not None else self.min_confidence

        # Filter ads
        if self.filter_ads and self._ad_filter:
            elements = [e for e in elements if not self._ad_filter.is_ad(e)]

        # Use confidence scoring to find best match
        match_result = find_best_match(
            elements,
            text=text,
            resource_id=resource_id,
            content_desc=content_desc,
            class_name=class_name,
            min_confidence=threshold,
            filter_ads=False,  # Already filtered
        )

        if match_result:
            bounds = match_result.element.get("bounds", (0, 0, 0, 0))
            center = get_center(bounds)

            # Determine which strategy matched best
            strategy = (
                "text"
                if text
                else "id" if resource_id else "content_desc" if content_desc else "class"
            )

            return LocatorResult(
                found=True,
                element=match_result.element,
                strategy_used=strategy,
                coordinates=center,
                fallback_level=0,
                confidence=match_result.confidence,
                match_details=match_result.match_details,
            )

        return LocatorResult(found=False, confidence=0.0)

    def _find_by_id(
        self, resource_id: str, elements: List[Dict[str, Any]]
    ) -> Tuple[Optional[Dict[str, Any]], float, Dict[str, float]]:
        """
        Find element by resource-id with confidence scoring.

        Args:
            resource_id: Full or partial resource ID
            elements: UI elements

        Returns:
            Tuple of (element, confidence, match_details)
        """
        best_match = None
        best_confidence = 0.0
        best_details = {}

        search_id = resource_id.split("/")[-1].lower()

        for elem in elements:
            elem_id = elem.get("resource_id", "")
            if not elem_id:
                continue

            elem_id_part = elem_id.split("/")[-1].lower()

            # Calculate confidence
            if elem_id == resource_id:
                # Exact full match
                confidence = 1.0
                details = {"id_exact_full": 1.0}
            elif elem_id_part == search_id:
                # Exact ID part match
                confidence = 0.95
                details = {"id_exact": 0.95}
            elif search_id in elem_id_part:
                # Partial match
                confidence = 0.8 * (len(search_id) / len(elem_id_part))
                details = {"id_contains": confidence}
            elif elem_id_part in search_id:
                # Reverse partial match
                confidence = 0.7 * (len(elem_id_part) / len(search_id))
                details = {"id_partial": confidence}
            else:
                # Fuzzy match
                similarity = calculate_string_similarity(search_id, elem_id_part)
                if similarity > 0.5:
                    confidence = similarity * 0.6
                    details = {"id_fuzzy": confidence}
                else:
                    continue

            if confidence > best_confidence:
                best_confidence = confidence
                best_match = elem
                best_details = details

        return best_match, best_confidence, best_details

    def _find_by_content_desc(
        self, content_desc: str, elements: List[Dict[str, Any]]
    ) -> Tuple[Optional[Dict[str, Any]], float, Dict[str, float]]:
        """
        Find element by content-description with confidence scoring.

        Args:
            content_desc: Accessibility description
            elements: UI elements

        Returns:
            Tuple of (element, confidence, match_details)
        """
        best_match = None
        best_confidence = 0.0
        best_details = {}

        search_desc = content_desc.lower()

        for elem in elements:
            elem_desc = elem.get("content_desc", "")
            if not elem_desc:
                continue

            elem_desc_lower = elem_desc.lower()

            # Calculate confidence
            if elem_desc == content_desc:
                confidence = 1.0
                details = {"desc_exact": 1.0}
            elif elem_desc_lower == search_desc:
                confidence = 0.95
                details = {"desc_exact_ci": 0.95}
            elif search_desc in elem_desc_lower:
                confidence = 0.8 * (len(search_desc) / len(elem_desc_lower))
                details = {"desc_contains": confidence}
            elif elem_desc_lower in search_desc:
                confidence = 0.7 * (len(elem_desc_lower) / len(search_desc))
                details = {"desc_partial": confidence}
            else:
                similarity = calculate_string_similarity(content_desc, elem_desc)
                if similarity > 0.4:
                    confidence = similarity * 0.7
                    details = {"desc_fuzzy": confidence}
                else:
                    continue

            if confidence > best_confidence:
                best_confidence = confidence
                best_match = elem
                best_details = details

        return best_match, best_confidence, best_details

    def _find_by_text(
        self, text: str, elements: List[Dict[str, Any]]
    ) -> Tuple[Optional[Dict[str, Any]], float, Dict[str, float]]:
        """
        Find element by visible text with confidence scoring.

        Args:
            text: Visible text
            elements: UI elements

        Returns:
            Tuple of (element, confidence, match_details)
        """
        best_match = None
        best_confidence = 0.0
        best_details = {}

        search_text = text.lower()

        for elem in elements:
            elem_text = elem.get("text", "")
            if not elem_text:
                continue

            elem_text_lower = elem_text.lower()

            # Calculate confidence
            if elem_text == text:
                # Exact match (case-sensitive)
                confidence = 1.0
                details = {"text_exact": 1.0}
            elif elem_text_lower == search_text:
                # Case-insensitive exact match
                confidence = 0.95
                details = {"text_exact_ci": 0.95}
            elif search_text in elem_text_lower:
                # Search text is substring
                ratio = len(search_text) / len(elem_text_lower)
                confidence = 0.7 + (ratio * 0.2)  # 0.7-0.9 based on how much matches
                details = {"text_contains": confidence}
            elif elem_text_lower in search_text:
                # Element text is substring of search
                ratio = len(elem_text_lower) / len(search_text)
                confidence = 0.6 + (ratio * 0.2)  # 0.6-0.8
                details = {"text_partial": confidence}
            else:
                # Fuzzy matching
                similarity = calculate_string_similarity(text, elem_text)
                if similarity > 0.4:
                    confidence = similarity * 0.7
                    details = {"text_fuzzy": confidence}
                else:
                    continue

            # Bonus for clickable elements
            if elem.get("clickable"):
                confidence = min(1.0, confidence + 0.05)
                details["clickable_bonus"] = 0.05

            if confidence > best_confidence:
                best_confidence = confidence
                best_match = elem
                best_details = details

        return best_match, best_confidence, best_details

    def _find_by_xpath(
        self, xpath: str, elements: List[Dict[str, Any]]
    ) -> Tuple[Optional[Dict[str, Any]], float, Dict[str, float]]:
        """
        Find element by XPath expression with confidence scoring.

        Supports simplified XPath matching:
        - //ClassName[@attr='value']
        - //ClassName[@attr1='v1' and @attr2='v2']

        Args:
            xpath: XPath expression
            elements: UI elements

        Returns:
            Tuple of (element, confidence, match_details)
        """
        # Parse simple XPath: //ClassName[@attr='value' and @attr2='value2']
        match = re.match(r"//([^\[]+)(?:\[(.*)\])?", xpath)
        if not match:
            return None, 0.0, {}

        class_name = match.group(1)
        conditions_str = match.group(2)

        # Parse conditions
        conditions = {}
        if conditions_str:
            # Match @attr='value' patterns
            for cond_match in re.finditer(r"@([\w-]+)='([^']*)'", conditions_str):
                attr = cond_match.group(1)
                value = cond_match.group(2)
                conditions[attr] = value

        best_match = None
        best_confidence = 0.0
        best_details = {}

        for elem in elements:
            # Check class name
            if elem.get("class") != class_name:
                continue

            # Score based on conditions matched
            matched_conditions = 0
            total_conditions = len(conditions)
            details = {"class_match": 0.3}
            confidence = 0.3  # Base for class match

            for attr, value in conditions.items():
                attr_key = attr.replace("-", "_")  # resource-id -> resource_id
                elem_value = elem.get(attr_key, "")

                if elem_value == value:
                    matched_conditions += 1
                    details[f"{attr}_exact"] = 0.7 / max(1, total_conditions)

            if total_conditions > 0:
                condition_score = (matched_conditions / total_conditions) * 0.7
                confidence += condition_score

            if matched_conditions == total_conditions and total_conditions > 0:
                # All conditions matched
                confidence = 1.0

            if confidence > best_confidence:
                best_confidence = confidence
                best_match = elem
                best_details = details

        return best_match, best_confidence, best_details

    def _find_by_bounds(
        self, bounds: Any, elements: List[Dict[str, Any]]
    ) -> Tuple[Optional[Dict[str, Any]], float, Dict[str, float]]:
        """
        Find element by bounds with confidence scoring.

        Args:
            bounds: Bounds tuple or list (x1, y1, x2, y2)
            elements: UI elements

        Returns:
            Tuple of (element, confidence, match_details)
        """
        if not bounds:
            return None, 0.0, {}

        target_bounds = tuple(bounds) if isinstance(bounds, list) else bounds
        if len(target_bounds) != 4:
            return None, 0.0, {}

        best_match = None
        best_confidence = 0.0
        best_details = {}

        tx1, ty1, tx2, ty2 = target_bounds

        for elem in elements:
            elem_bounds = elem.get("bounds", (0, 0, 0, 0))
            if len(elem_bounds) != 4:
                continue

            ex1, ey1, ex2, ey2 = elem_bounds

            # Exact match
            if elem_bounds == target_bounds:
                return elem, 1.0, {"bounds_exact": 1.0}

            # Calculate overlap ratio (IoU - Intersection over Union)
            inter_x1 = max(tx1, ex1)
            inter_y1 = max(ty1, ey1)
            inter_x2 = min(tx2, ex2)
            inter_y2 = min(ty2, ey2)

            if inter_x2 > inter_x1 and inter_y2 > inter_y1:
                intersection = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
                target_area = (tx2 - tx1) * (ty2 - ty1)
                elem_area = (ex2 - ex1) * (ey2 - ey1)
                union = target_area + elem_area - intersection

                if union > 0:
                    iou = intersection / union
                    # Also consider center distance
                    target_center = ((tx1 + tx2) / 2, (ty1 + ty2) / 2)
                    elem_center = ((ex1 + ex2) / 2, (ey1 + ey2) / 2)
                    center_dist = (
                        (target_center[0] - elem_center[0]) ** 2
                        + (target_center[1] - elem_center[1]) ** 2
                    ) ** 0.5
                    max_dist = max(tx2 - tx1, ty2 - ty1)
                    center_score = max(0, 1 - (center_dist / max_dist)) if max_dist > 0 else 0

                    confidence = (iou * 0.7) + (center_score * 0.3)

                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = elem
                        best_details = {"bounds_iou": iou, "center_proximity": center_score}

        return best_match, best_confidence, best_details


def describe_location_result(result: LocatorResult, step_id: int) -> str:
    """
    Generate human-readable description of location result.

    Args:
        result: LocatorResult
        step_id: Step number for context

    Returns:
        Description string
    """
    if result.found:
        elem = result.element
        class_name = elem.get("class", "").split(".")[-1]

        parts = [f"Step {step_id}: Found"]
        parts.append(f"{class_name}")

        if elem.get("resource_id"):
            rid = elem["resource_id"].split("/")[-1]
            parts.append(f"#{rid}")
        elif elem.get("text"):
            text = elem["text"][:20]
            if len(elem["text"]) > 20:
                text += "..."
            parts.append(f'"{text}"')

        parts.append(f"via {result.strategy_used}")
        parts.append(f"({result.confidence:.0%} confidence)")

        if result.fallback_level > 0:
            parts.append(f"[fallback #{result.fallback_level}]")

        return " ".join(parts)
    else:
        if result.coordinates:
            return f"Step {step_id}: Element not found (0% confidence), using coordinates {result.coordinates}"
        return f"Step {step_id}: Element not found, no fallback available"


def format_confidence(confidence: float) -> str:
    """Format confidence as a descriptive string."""
    if confidence >= 0.9:
        return f"{confidence:.0%} (excellent)"
    elif confidence >= 0.7:
        return f"{confidence:.0%} (good)"
    elif confidence >= 0.5:
        return f"{confidence:.0%} (fair)"
    elif confidence >= 0.3:
        return f"{confidence:.0%} (low)"
    else:
        return f"{confidence:.0%} (very low)"
