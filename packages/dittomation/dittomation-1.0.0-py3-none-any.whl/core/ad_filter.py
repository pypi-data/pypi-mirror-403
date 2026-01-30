"""
Ad Filter - Detects and filters sponsored/advertisement elements.

This module provides functionality to identify and skip advertisement elements
in the UI hierarchy, preventing accidental interaction with ads during
automation workflows.
"""

import re
from typing import Any, Dict, List, Optional, Set

from .config_manager import get_config_value
from .logging_config import get_logger

# Module logger
logger = get_logger("ad_filter")


# ============================================================================
# Ad Detection Patterns
# ============================================================================

# Resource ID patterns that typically indicate ads
AD_RESOURCE_ID_PATTERNS = [
    # Google Ads
    r".*google.*ad.*",
    r".*admob.*",
    r".*ad_container.*",
    r".*ad_view.*",
    r".*adview.*",
    r".*ad_frame.*",
    r".*ad_banner.*",
    r".*banner_ad.*",
    r".*native_ad.*",
    r".*interstitial.*ad.*",
    r".*rewarded.*ad.*",
    # Facebook Ads
    r".*facebook.*ad.*",
    r".*fb_ad.*",
    # Generic ad patterns
    r".*sponsored.*",
    r".*advertisement.*",
    r".*promo_banner.*",
    r".*promotion.*banner.*",
    r".*ad_slot.*",
    r".*ad_unit.*",
    r".*ad_placeholder.*",
    r".*ads_container.*",
    r".*adspace.*",
    r".*ad_wrapper.*",
]

# Text patterns that indicate sponsored content
AD_TEXT_PATTERNS = [
    # English
    r"^sponsored$",
    r"^ad$",
    r"^ads$",
    r"^advertisement$",
    r"^promoted$",
    r"^sponsored post$",
    r"^promoted content$",
    r"^install now$",
    r"^get the app$",
    r"^download now$",
    r"^learn more$",
    r"^shop now$",
    r"^buy now$",
    # With symbols
    r"^ad\s*[·•|]",
    r"[·•|]\s*ad$",
    r"^sponsored\s*[·•|]",
    r"[·•|]\s*sponsored$",
    # Common ad CTAs
    r"^install$",
    r"^open$",
    r"^play now$",
    r"^try now$",
    r"^sign up$",
    r"^register now$",
    # Multi-language support
    r"^広告$",  # Japanese: "advertisement"
    r"^스폰서$",  # Korean: "sponsor"
    r"^贊助$",  # Chinese Traditional: "sponsored"
    r"^赞助$",  # Chinese Simplified: "sponsored"
    r"^werbung$",  # German: "advertisement"
    r"^anzeige$",  # German: "ad"
    r"^publicité$",  # French: "advertisement"
    r"^annonce$",  # French: "ad"
    r"^patrocinado$",  # Spanish/Portuguese: "sponsored"
    r"^anuncio$",  # Spanish: "ad"
]

# Content description patterns
AD_CONTENT_DESC_PATTERNS = [
    r".*advertisement.*",
    r".*sponsored.*",
    r".*ad\s*banner.*",
    r".*promoted.*",
    r".*skip\s*ad.*",
    r".*close\s*ad.*",
]

# Package patterns for ad SDKs
AD_PACKAGE_PATTERNS = [
    r"com\.google\.android\.gms\.ads.*",
    r"com\.google\.ads.*",
    r"com\.facebook\.ads.*",
    r"com\.unity3d\.ads.*",
    r"com\.applovin.*",
    r"com\.mopub.*",
    r"com\.ironsource.*",
    r"com\.vungle.*",
    r"com\.chartboost.*",
    r"com\.inmobi.*",
    r"com\.startapp.*",
    r"com\.tapjoy.*",
]

# Class patterns that often contain ads
AD_CLASS_PATTERNS = [
    r".*AdView$",
    r".*AdContainer$",
    r".*BannerAd.*",
    r".*NativeAd.*",
    r".*InterstitialAd.*",
    r".*RewardedAd.*",
    r".*PromotedContent.*",
    r".*SponsoredView.*",
]

# Compile regex patterns for efficiency
_COMPILED_PATTERNS: Dict[str, List[re.Pattern]] = {}


def _compile_patterns() -> None:
    """Compile all regex patterns for efficient matching."""
    global _COMPILED_PATTERNS

    if _COMPILED_PATTERNS:
        return

    _COMPILED_PATTERNS = {
        "resource_id": [re.compile(p, re.IGNORECASE) for p in AD_RESOURCE_ID_PATTERNS],
        "text": [re.compile(p, re.IGNORECASE) for p in AD_TEXT_PATTERNS],
        "content_desc": [re.compile(p, re.IGNORECASE) for p in AD_CONTENT_DESC_PATTERNS],
        "package": [re.compile(p, re.IGNORECASE) for p in AD_PACKAGE_PATTERNS],
        "class": [re.compile(p, re.IGNORECASE) for p in AD_CLASS_PATTERNS],
    }


def _matches_any_pattern(value: str, patterns: List[re.Pattern]) -> bool:
    """Check if value matches any of the compiled patterns."""
    if not value:
        return False

    for pattern in patterns:
        if pattern.search(value):
            return True

    return False


# ============================================================================
# Ad Detection Functions
# ============================================================================


def is_ad_element(element: Dict[str, Any], strict: bool = False) -> bool:
    """
    Check if an element appears to be an advertisement.

    Args:
        element: UI element dictionary
        strict: If True, require multiple indicators for positive match

    Returns:
        True if element is likely an ad
    """
    _compile_patterns()

    ad_indicators = 0

    # Check resource ID
    resource_id = element.get("resource_id", "")
    if _matches_any_pattern(resource_id, _COMPILED_PATTERNS["resource_id"]):
        ad_indicators += 2
        logger.debug(f"Ad indicator: resource_id '{resource_id}'")

    # Check text
    text = element.get("text", "")
    if _matches_any_pattern(text, _COMPILED_PATTERNS["text"]):
        ad_indicators += 2
        logger.debug(f"Ad indicator: text '{text}'")

    # Check content description
    content_desc = element.get("content_desc", "")
    if _matches_any_pattern(content_desc, _COMPILED_PATTERNS["content_desc"]):
        ad_indicators += 2
        logger.debug(f"Ad indicator: content_desc '{content_desc}'")

    # Check package
    package = element.get("package", "")
    if _matches_any_pattern(package, _COMPILED_PATTERNS["package"]):
        ad_indicators += 3
        logger.debug(f"Ad indicator: package '{package}'")

    # Check class name
    class_name = element.get("class", "")
    if _matches_any_pattern(class_name, _COMPILED_PATTERNS["class"]):
        ad_indicators += 2
        logger.debug(f"Ad indicator: class '{class_name}'")

    # Determine threshold
    threshold = 3 if strict else 1

    is_ad = ad_indicators >= threshold

    if is_ad:
        logger.debug(
            f"Element identified as ad (score: {ad_indicators}): {_describe_element(element)}"
        )

    return is_ad


def is_sponsored_content(element: Dict[str, Any]) -> bool:
    """
    Check if element is sponsored content (less strict than full ad detection).

    Args:
        element: UI element dictionary

    Returns:
        True if element appears to be sponsored content
    """
    text = element.get("text", "").lower()
    content_desc = element.get("content_desc", "").lower()
    resource_id = element.get("resource_id", "").lower()

    # Quick checks for common sponsored indicators
    sponsored_keywords = ["sponsored", "promoted", "advertisement", "ad ", " ad"]

    for keyword in sponsored_keywords:
        if keyword in text or keyword in content_desc or keyword in resource_id:
            logger.debug(f"Sponsored content detected: {_describe_element(element)}")
            return True

    return False


def filter_ad_elements(
    elements: List[Dict[str, Any]], strict: bool = False
) -> List[Dict[str, Any]]:
    """
    Filter out advertisement elements from a list.

    Args:
        elements: List of UI elements
        strict: If True, use stricter ad detection

    Returns:
        Filtered list without ad elements
    """
    if not get_config_value("ad_filter.enabled", True):
        return elements

    filtered = []
    ad_count = 0

    for elem in elements:
        if is_ad_element(elem, strict=strict):
            ad_count += 1
        else:
            filtered.append(elem)

    if ad_count > 0:
        logger.info(f"Filtered {ad_count} ad element(s) from {len(elements)} total")

    return filtered


def get_non_ad_elements_at_point(
    elements: List[Dict[str, Any]], x: int, y: int
) -> List[Dict[str, Any]]:
    """
    Get elements at a point, excluding ads.

    Args:
        elements: List of UI elements
        x: X coordinate
        y: Y coordinate

    Returns:
        List of non-ad elements containing the point
    """
    matching = []

    for elem in elements:
        x1, y1, x2, y2 = elem.get("bounds", (0, 0, 0, 0))

        # Check if point is within bounds
        if x1 <= x <= x2 and y1 <= y <= y2:
            if not is_ad_element(elem):
                matching.append(elem)

    return matching


def find_non_ad_alternative(
    elements: List[Dict[str, Any]], ad_element: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Find a non-ad alternative near an ad element.

    Useful when user accidentally taps on an ad - find nearby content instead.

    Args:
        elements: All UI elements
        ad_element: The ad element to find alternative for

    Returns:
        Alternative element or None
    """
    ad_bounds = ad_element.get("bounds", (0, 0, 0, 0))
    ad_x1, ad_y1, ad_x2, ad_y2 = ad_bounds
    ad_center_y = (ad_y1 + ad_y2) // 2

    # Look for clickable non-ad elements above or below the ad
    candidates = []

    for elem in elements:
        if is_ad_element(elem):
            continue

        if not elem.get("clickable"):
            continue

        x1, y1, x2, y2 = elem.get("bounds", (0, 0, 0, 0))
        center_y = (y1 + y2) // 2

        # Check if element is within reasonable horizontal range
        if x2 < ad_x1 or x1 > ad_x2:
            continue

        # Calculate vertical distance
        distance = abs(center_y - ad_center_y)

        if distance < 500:  # Within 500px vertically
            candidates.append((distance, elem))

    if candidates:
        # Return closest non-ad element
        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]

    return None


def _describe_element(element: Dict[str, Any]) -> str:
    """Generate brief description of element for logging."""
    parts = []

    class_name = element.get("class", "").split(".")[-1]
    if class_name:
        parts.append(class_name)

    if element.get("resource_id"):
        rid = element["resource_id"].split("/")[-1]
        parts.append(f"#{rid}")

    if element.get("text"):
        text = element["text"][:20]
        parts.append(f'"{text}"')

    return " ".join(parts) or "unknown element"


# ============================================================================
# Custom Pattern Management
# ============================================================================

_custom_patterns: Dict[str, Set[str]] = {
    "resource_id": set(),
    "text": set(),
    "content_desc": set(),
    "package": set(),
    "class": set(),
}


def add_custom_ad_pattern(pattern_type: str, pattern: str) -> None:
    """
    Add a custom ad detection pattern.

    Args:
        pattern_type: Type of pattern ('resource_id', 'text', 'content_desc', 'package', 'class')
        pattern: Regex pattern string
    """
    if pattern_type not in _custom_patterns:
        logger.warning(f"Unknown pattern type: {pattern_type}")
        return

    _custom_patterns[pattern_type].add(pattern)

    # Recompile patterns to include custom ones
    global _COMPILED_PATTERNS
    _COMPILED_PATTERNS = {}
    _compile_patterns()

    # Add custom patterns
    if pattern_type in _COMPILED_PATTERNS:
        _COMPILED_PATTERNS[pattern_type].append(re.compile(pattern, re.IGNORECASE))

    logger.info(f"Added custom ad pattern ({pattern_type}): {pattern}")


def clear_custom_patterns() -> None:
    """Clear all custom ad patterns."""
    global _custom_patterns, _COMPILED_PATTERNS

    _custom_patterns = {
        "resource_id": set(),
        "text": set(),
        "content_desc": set(),
        "package": set(),
        "class": set(),
    }

    _COMPILED_PATTERNS = {}

    logger.info("Cleared custom ad patterns")


def load_custom_patterns_from_config() -> None:
    """Load custom ad patterns from configuration."""
    custom_config = get_config_value("ad_filter.custom_patterns", {})

    for pattern_type, patterns in custom_config.items():
        if isinstance(patterns, list):
            for pattern in patterns:
                add_custom_ad_pattern(pattern_type, pattern)


# ============================================================================
# AdFilter Class (Stateful)
# ============================================================================


class AdFilter:
    """
    Stateful ad filter with configurable behavior.

    Provides methods for filtering ads from UI elements with
    caching and statistics tracking.
    """

    def __init__(self, enabled: bool = True, strict_mode: bool = False, log_filtered: bool = True):
        """
        Initialize ad filter.

        Args:
            enabled: Whether filtering is enabled
            strict_mode: Use stricter detection (fewer false positives)
            log_filtered: Log when elements are filtered
        """
        self.enabled = enabled
        self.strict_mode = strict_mode
        self.log_filtered = log_filtered

        # Statistics
        self.total_filtered = 0
        self.total_processed = 0

        # Cache of detected ad element hashes
        self._ad_cache: Set[int] = set()

    def filter(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter ad elements from list.

        Args:
            elements: UI elements to filter

        Returns:
            Filtered elements
        """
        if not self.enabled:
            return elements

        filtered = []
        filtered_count = 0

        for elem in elements:
            elem_hash = self._element_hash(elem)

            # Check cache first
            if elem_hash in self._ad_cache:
                filtered_count += 1
                continue

            # Run detection
            if is_ad_element(elem, strict=self.strict_mode):
                self._ad_cache.add(elem_hash)
                filtered_count += 1
            else:
                filtered.append(elem)

        self.total_processed += len(elements)
        self.total_filtered += filtered_count

        if filtered_count > 0 and self.log_filtered:
            logger.debug(f"Filtered {filtered_count} ad(s) from {len(elements)} elements")

        return filtered

    def is_ad(self, element: Dict[str, Any]) -> bool:
        """
        Check if a single element is an ad.

        Args:
            element: UI element to check

        Returns:
            True if element is an ad
        """
        if not self.enabled:
            return False

        return is_ad_element(element, strict=self.strict_mode)

    def _element_hash(self, element: Dict[str, Any]) -> int:
        """Generate hash for element caching."""
        key_parts = [
            element.get("resource_id", ""),
            element.get("text", ""),
            str(element.get("bounds", "")),
            element.get("class", ""),
        ]
        return hash(tuple(key_parts))

    def clear_cache(self) -> None:
        """Clear the ad element cache."""
        self._ad_cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get filtering statistics."""
        return {
            "total_processed": self.total_processed,
            "total_filtered": self.total_filtered,
            "filter_rate": (
                self.total_filtered / self.total_processed if self.total_processed > 0 else 0
            ),
            "cache_size": len(self._ad_cache),
        }

    def reset_stats(self) -> None:
        """Reset statistics counters."""
        self.total_filtered = 0
        self.total_processed = 0


# Global filter instance
_global_filter: Optional[AdFilter] = None


def get_ad_filter() -> AdFilter:
    """
    Get the global ad filter instance.

    Returns:
        Global AdFilter instance
    """
    global _global_filter

    if _global_filter is None:
        _global_filter = AdFilter(
            enabled=get_config_value("ad_filter.enabled", True),
            strict_mode=get_config_value("ad_filter.strict_mode", False),
            log_filtered=get_config_value("ad_filter.log_filtered", True),
        )
        load_custom_patterns_from_config()

    return _global_filter
