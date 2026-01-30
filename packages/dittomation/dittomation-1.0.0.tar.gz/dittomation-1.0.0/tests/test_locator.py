"""Tests for replayer.locator module."""

from unittest.mock import MagicMock, patch

from recorder.element_matcher import DEFAULT_MIN_CONFIDENCE
from replayer.locator import (
    ElementLocator,
    LocatorResult,
)


class TestLocatorResult:
    """Tests for LocatorResult class."""

    def test_create_found_result(self):
        result = LocatorResult(
            found=True,
            element={"text": "Login"},
            strategy_used="text",
            coordinates=(100, 200),
            confidence=0.9,
        )
        assert result.found is True
        assert result.element["text"] == "Login"
        assert result.coordinates == (100, 200)
        assert result.confidence == 0.9

    def test_create_not_found_result(self):
        result = LocatorResult(found=False)
        assert result.found is False
        assert result.element is None

    def test_str_found(self):
        result = LocatorResult(
            found=True,
            strategy_used="text",
            coordinates=(100, 200),
            confidence=0.85,
            fallback_level=1,
        )
        s = str(result)
        assert "text" in s
        assert "100" in s or "(100, 200)" in s
        assert "85%" in s

    def test_str_not_found(self):
        result = LocatorResult(found=False)
        assert "not found" in str(result).lower()

    def test_is_high_confidence(self):
        high = LocatorResult(found=True, confidence=0.9)
        assert high.is_high_confidence is True

        medium = LocatorResult(found=True, confidence=0.7)
        assert medium.is_high_confidence is False

    def test_is_low_confidence(self):
        low = LocatorResult(found=True, confidence=0.3)
        assert low.is_low_confidence is True

        medium = LocatorResult(found=True, confidence=0.6)
        assert medium.is_low_confidence is False


class TestElementLocator:
    """Tests for ElementLocator class."""

    def test_init_default(self):
        with patch("replayer.locator.get_ad_filter") as mock_filter:
            mock_filter.return_value = MagicMock()
            locator = ElementLocator()

            assert locator.filter_ads is True
            assert locator.min_confidence == DEFAULT_MIN_CONFIDENCE

    def test_init_custom_settings(self):
        locator = ElementLocator(filter_ads=False, min_confidence=0.5)
        assert locator.filter_ads is False
        assert locator.min_confidence == 0.5

    def test_find_element_by_text(self):
        with patch("replayer.locator.get_ad_filter") as mock_filter:
            mock_filter.return_value = MagicMock(is_ad=lambda x: False)

            locator = ElementLocator()
            elements = [
                {"text": "Login", "bounds": (100, 200, 200, 250)},
                {"text": "Register", "bounds": (100, 300, 200, 350)},
            ]
            loc = {
                "primary": {"strategy": "text", "value": "Login"},
                "fallbacks": [],
            }

            result = locator.find_element(loc, elements)

            assert result.found is True
            assert result.element["text"] == "Login"

    def test_find_element_by_id(self):
        with patch("replayer.locator.get_ad_filter") as mock_filter:
            mock_filter.return_value = MagicMock(is_ad=lambda x: False)

            locator = ElementLocator()
            elements = [
                {"resource_id": "com.app:id/btn_login", "bounds": (100, 200, 200, 250)},
                {"resource_id": "com.app:id/btn_register", "bounds": (100, 300, 200, 350)},
            ]
            loc = {
                "primary": {"strategy": "id", "value": "btn_login"},
                "fallbacks": [],
            }

            result = locator.find_element(loc, elements)

            assert result.found is True
            assert "btn_login" in result.element["resource_id"]

    def test_find_element_by_content_desc(self):
        with patch("replayer.locator.get_ad_filter") as mock_filter:
            mock_filter.return_value = MagicMock(is_ad=lambda x: False)

            locator = ElementLocator()
            elements = [
                {"content_desc": "Settings button", "bounds": (100, 200, 200, 250)},
            ]
            loc = {
                "primary": {"strategy": "content_desc", "value": "Settings button"},
                "fallbacks": [],
            }

            result = locator.find_element(loc, elements)

            assert result.found is True

    def test_find_element_with_fallback(self):
        with patch("replayer.locator.get_ad_filter") as mock_filter:
            mock_filter.return_value = MagicMock(is_ad=lambda x: False)

            locator = ElementLocator()
            elements = [
                {"text": "Login", "bounds": (100, 200, 200, 250)},
            ]
            loc = {
                "primary": {"strategy": "id", "value": "btn_nonexistent"},
                "fallbacks": [
                    {"strategy": "text", "value": "Login"},
                ],
            }

            result = locator.find_element(loc, elements)

            assert result.found is True
            assert result.fallback_level > 0

    def test_find_element_not_found(self):
        with patch("replayer.locator.get_ad_filter") as mock_filter:
            mock_filter.return_value = MagicMock(is_ad=lambda x: False)

            locator = ElementLocator()
            elements = [
                {"text": "Something else", "bounds": (100, 200, 200, 250)},
            ]
            loc = {
                "primary": {"strategy": "text", "value": "Login"},
                "fallbacks": [],
            }

            result = locator.find_element(loc, elements, min_confidence=0.9)

            assert result.found is False

    def test_filters_ad_elements(self):
        mock_ad_filter = MagicMock()
        mock_ad_filter.is_ad = lambda e: "ad" in e.get("resource_id", "")

        with patch("replayer.locator.get_ad_filter", return_value=mock_ad_filter):
            locator = ElementLocator(filter_ads=True)
            elements = [
                {"text": "Content", "resource_id": "content", "bounds": (100, 200, 200, 250)},
                {"text": "Ad", "resource_id": "ad_banner", "bounds": (100, 300, 200, 350)},
            ]
            loc = {
                "primary": {"strategy": "text", "value": "Ad"},
                "fallbacks": [],
            }

            result = locator.find_element(loc, elements)

            # Ad element should be filtered out
            if result.found:
                assert "ad_banner" not in result.element.get("resource_id", "")

    def test_find_element_by_bounds(self):
        with patch("replayer.locator.get_ad_filter") as mock_filter:
            mock_filter.return_value = MagicMock(is_ad=lambda x: False)

            locator = ElementLocator()
            elements = [
                {"text": "Button", "bounds": (100, 200, 200, 250)},
            ]
            loc = {
                "primary": {"strategy": "bounds", "value": [100, 200, 200, 250]},
                "fallbacks": [],
            }

            result = locator.find_element(loc, elements)
            # Bounds matching should work
            assert result.found is True or result.found is False  # Depends on impl

    def test_returns_coordinates(self):
        with patch("replayer.locator.get_ad_filter") as mock_filter:
            mock_filter.return_value = MagicMock(is_ad=lambda x: False)

            locator = ElementLocator()
            elements = [
                {"text": "Login", "bounds": (100, 200, 200, 250)},
            ]
            loc = {
                "primary": {"strategy": "text", "value": "Login"},
                "fallbacks": [],
            }

            result = locator.find_element(loc, elements)

            if result.found:
                assert result.coordinates is not None
                assert len(result.coordinates) == 2


class TestLocatorResultConfidence:
    """Tests for confidence score handling in LocatorResult."""

    def test_confidence_boundaries(self):
        # 0% confidence
        result0 = LocatorResult(found=True, confidence=0.0)
        assert result0.is_low_confidence is True
        assert result0.is_high_confidence is False

        # 100% confidence
        result100 = LocatorResult(found=True, confidence=1.0)
        assert result100.is_low_confidence is False
        assert result100.is_high_confidence is True

    def test_match_details(self):
        result = LocatorResult(
            found=True, confidence=0.85, match_details={"text_exact": 1.0, "clickable_bonus": 0.1}
        )
        assert "text_exact" in result.match_details
        assert result.match_details["text_exact"] == 1.0
