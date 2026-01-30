"""Tests for recorder.element_matcher module."""

from unittest.mock import patch

from recorder.element_matcher import (
    DEFAULT_MIN_CONFIDENCE,
    SCORE_WEIGHTS,
    MatchResult,
    calculate_string_similarity,
    find_best_match,
    find_elements_with_confidence,
    score_element_match,
)


class TestCalculateStringSimilarity:
    """Tests for calculate_string_similarity function."""

    def test_exact_match(self):
        assert calculate_string_similarity("hello", "hello") == 1.0

    def test_case_insensitive_match(self):
        assert calculate_string_similarity("Hello", "hello") == 1.0

    def test_empty_strings(self):
        assert calculate_string_similarity("", "hello") == 0.0
        assert calculate_string_similarity("hello", "") == 0.0
        assert calculate_string_similarity("", "") == 0.0

    def test_substring_match(self):
        score = calculate_string_similarity("Login", "Login Button")
        # Algorithm: shorter/longer * 0.9 = 5/12 * 0.9 = 0.375
        assert score > 0.3

    def test_word_overlap(self):
        score = calculate_string_similarity("Hello World", "World Hello")
        assert score > 0.5

    def test_no_match(self):
        score = calculate_string_similarity("xyz", "abc")
        assert score < 0.5


class TestMatchResult:
    """Tests for MatchResult dataclass."""

    def test_create_match_result(self):
        element = {"text": "Login", "resource_id": "btn_login"}
        result = MatchResult(element=element, confidence=0.85, match_details={"text_exact": 1.0})
        assert result.element == element
        assert result.confidence == 0.85

    def test_repr(self):
        element = {"text": "Login Button", "resource_id": "btn"}
        result = MatchResult(element=element, confidence=0.9, match_details={})
        repr_str = repr(result)
        assert "Login Button" in repr_str or "btn" in repr_str
        assert "0.9" in repr_str


class TestScoreElementMatch:
    """Tests for score_element_match function."""

    def test_exact_text_match(self):
        element = {"text": "Login"}
        result = score_element_match(element, text="Login")
        assert result.confidence > 0.8
        assert "text_exact" in result.match_details

    def test_text_contains_match(self):
        element = {"text": "Login Button"}
        result = score_element_match(element, text="Login")
        assert result.confidence > 0.5
        assert "text_contains" in result.match_details

    def test_exact_resource_id_match(self):
        element = {"resource_id": "com.app:id/btn_login"}
        result = score_element_match(element, resource_id="btn_login")
        assert result.confidence > 0.8
        assert "id_exact" in result.match_details

    def test_resource_id_contains_match(self):
        element = {"resource_id": "com.app:id/button_login_primary"}
        result = score_element_match(element, resource_id="login")
        assert result.confidence > 0.5
        assert "id_contains" in result.match_details

    def test_exact_content_desc_match(self):
        element = {"content_desc": "Settings"}
        result = score_element_match(element, content_desc="Settings")
        assert result.confidence > 0.8
        assert "desc_exact" in result.match_details

    def test_class_name_match(self):
        element = {"class": "android.widget.Button"}
        result = score_element_match(element, class_name="Button")
        assert "class_match" in result.match_details

    def test_clickable_bonus(self):
        element = {"text": "Login", "clickable": True}
        result = score_element_match(element, text="Login")
        assert "clickable_bonus" in result.match_details

    def test_no_match(self):
        element = {"text": "Logout"}
        result = score_element_match(element, text="Settings")
        assert result.confidence < 0.5

    def test_multiple_criteria_combined(self):
        element = {
            "text": "Login",
            "resource_id": "com.app:id/btn_login",
            "content_desc": "Login button",
            "clickable": True,
            "enabled": True,
        }
        result = score_element_match(
            element, text="Login", resource_id="btn_login", content_desc="Login button"
        )
        # Should have high confidence with multiple matches
        assert result.confidence > 0.9


class TestFindElementsWithConfidence:
    """Tests for find_elements_with_confidence function."""

    def test_find_by_text(self):
        elements = [
            {"text": "Login", "bounds": (0, 0, 100, 50)},
            {"text": "Register", "bounds": (0, 60, 100, 110)},
            {"text": "Forgot Password", "bounds": (0, 120, 100, 170)},
        ]

        results = find_elements_with_confidence(elements, text="Login")

        assert len(results) >= 1
        assert results[0].element["text"] == "Login"

    def test_find_by_resource_id(self):
        elements = [
            {"resource_id": "com.app:id/btn_login", "bounds": (0, 0, 100, 50)},
            {"resource_id": "com.app:id/btn_register", "bounds": (0, 60, 100, 110)},
        ]

        results = find_elements_with_confidence(elements, resource_id="btn_login")

        assert len(results) >= 1
        assert "btn_login" in results[0].element["resource_id"]

    def test_respects_min_confidence(self):
        elements = [
            {"text": "Login", "bounds": (0, 0, 100, 50)},
            {"text": "Logout", "bounds": (0, 60, 100, 110)},
        ]

        results = find_elements_with_confidence(elements, text="Login", min_confidence=0.9)

        # Only exact match should pass high threshold
        assert len(results) >= 1
        for r in results:
            assert r.confidence >= 0.9

    def test_sorted_by_confidence(self):
        elements = [
            {"text": "Login Button", "bounds": (0, 0, 100, 50)},
            {"text": "Login", "bounds": (0, 60, 100, 110)},  # Better match
            {"text": "Click to Login", "bounds": (0, 120, 100, 170)},
        ]

        results = find_elements_with_confidence(elements, text="Login")

        if len(results) > 1:
            # Should be sorted by confidence descending
            assert results[0].confidence >= results[1].confidence

    def test_filters_ads(self):
        elements = [
            {"text": "Login", "bounds": (0, 0, 100, 50)},
            {
                "text": "Sponsored",
                "resource_id": "com.app:id/ad_banner",
                "bounds": (0, 60, 100, 110),
            },
        ]

        # Mock get_ad_filter to return a filter that detects ad_banner as an ad
        from unittest.mock import MagicMock

        mock_ad_filter = MagicMock()
        mock_ad_filter.is_ad.side_effect = lambda e: "ad_banner" in e.get("resource_id", "")

        with patch("core.ad_filter.get_ad_filter", return_value=mock_ad_filter):
            results = find_elements_with_confidence(elements, text="Login", filter_ads=True)

            # Ad should be filtered out
            for r in results:
                assert "ad_banner" not in r.element.get("resource_id", "")


class TestFindBestMatch:
    """Tests for find_best_match function."""

    def test_returns_best_match(self):
        elements = [
            {"text": "Login Button", "bounds": (0, 0, 100, 50)},
            {"text": "Login", "bounds": (0, 60, 100, 110)},  # Exact match
        ]

        result = find_best_match(elements, text="Login")

        assert result is not None
        assert result.element["text"] == "Login"

    def test_returns_none_below_threshold(self):
        elements = [
            {"text": "Something completely different", "bounds": (0, 0, 100, 50)},
        ]

        result = find_best_match(elements, text="Login", min_confidence=0.9)

        assert result is None

    def test_empty_elements(self):
        result = find_best_match([], text="Login")
        assert result is None

    def test_no_criteria(self):
        elements = [
            {"text": "Login", "bounds": (0, 0, 100, 50)},
        ]

        find_best_match(elements)
        # No search criteria, should return None or first element depending on impl
        # At minimum, should not crash


class TestScoreWeights:
    """Tests for SCORE_WEIGHTS configuration."""

    def test_weights_are_positive(self):
        for key, weight in SCORE_WEIGHTS.items():
            assert weight > 0, f"Weight for {key} should be positive"

    def test_exact_match_weights_are_highest(self):
        assert SCORE_WEIGHTS["text_exact"] >= SCORE_WEIGHTS["text_contains"]
        assert SCORE_WEIGHTS["id_exact"] >= SCORE_WEIGHTS["id_contains"]
        assert SCORE_WEIGHTS["desc_exact"] >= SCORE_WEIGHTS["desc_contains"]


class TestDefaultMinConfidence:
    """Tests for DEFAULT_MIN_CONFIDENCE."""

    def test_default_confidence_is_reasonable(self):
        assert 0.0 < DEFAULT_MIN_CONFIDENCE < 1.0
        assert DEFAULT_MIN_CONFIDENCE == 0.3  # Current default
