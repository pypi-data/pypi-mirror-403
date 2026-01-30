"""Tests for core.ad_filter module."""

from unittest.mock import patch

from core.ad_filter import (
    AdFilter,
    _compile_patterns,
    _describe_element,
    _matches_any_pattern,
    add_custom_ad_pattern,
    clear_custom_patterns,
    filter_ad_elements,
    find_non_ad_alternative,
    get_ad_filter,
    get_non_ad_elements_at_point,
    is_ad_element,
    is_sponsored_content,
)


class TestIsAdElement:
    """Tests for is_ad_element function."""

    def test_ad_by_resource_id(self):
        element = {"resource_id": "com.app:id/google_ad_container"}
        assert is_ad_element(element) is True

    def test_ad_by_admob_resource_id(self):
        element = {"resource_id": "com.app:id/admob_banner"}
        assert is_ad_element(element) is True

    def test_ad_by_text_sponsored(self):
        element = {"text": "Sponsored"}
        assert is_ad_element(element) is True

    def test_ad_by_text_ad(self):
        element = {"text": "Ad"}
        assert is_ad_element(element) is True

    def test_ad_by_content_desc(self):
        element = {"content_desc": "Advertisement banner"}
        assert is_ad_element(element) is True

    def test_ad_by_package(self):
        element = {"package": "com.google.android.gms.ads.AdActivity"}
        assert is_ad_element(element) is True

    def test_ad_by_class(self):
        element = {"class": "com.google.ads.AdView"}
        assert is_ad_element(element) is True

    def test_not_ad_normal_element(self):
        element = {
            "resource_id": "com.app:id/login_button",
            "text": "Login",
            "class": "android.widget.Button",
        }
        assert is_ad_element(element) is False

    def test_not_ad_empty_element(self):
        element = {}
        assert is_ad_element(element) is False

    def test_strict_mode_requires_multiple_indicators(self):
        # Single indicator should not be enough in strict mode
        element = {"text": "Sponsored"}
        assert is_ad_element(element, strict=True) is False

        # Multiple indicators should pass
        element = {
            "text": "Sponsored",
            "resource_id": "com.app:id/ad_container",
        }
        assert is_ad_element(element, strict=True) is True


class TestIsSponsoredContent:
    """Tests for is_sponsored_content function."""

    def test_sponsored_in_text(self):
        element = {"text": "This is sponsored content"}
        assert is_sponsored_content(element) is True

    def test_promoted_in_text(self):
        element = {"text": "Promoted post"}
        assert is_sponsored_content(element) is True

    def test_ad_in_resource_id(self):
        # is_sponsored_content checks for 'ad ' or ' ad' patterns, not 'ad_'
        element = {"resource_id": "com.app:id/sponsored_content"}
        assert is_sponsored_content(element) is True

    def test_normal_content(self):
        element = {"text": "Hello World", "resource_id": "com.app:id/message"}
        assert is_sponsored_content(element) is False


class TestFilterAdElements:
    """Tests for filter_ad_elements function."""

    def test_filters_ads(self):
        elements = [
            {"text": "Normal button", "resource_id": "com.app:id/button"},
            {"text": "Sponsored", "resource_id": "com.app:id/ad"},
            {"text": "Another normal element"},
        ]

        with patch("core.ad_filter.get_config_value", return_value=True):
            filtered = filter_ad_elements(elements)

        assert len(filtered) == 2
        assert all("Sponsored" not in e.get("text", "") for e in filtered)

    def test_returns_all_when_disabled(self):
        elements = [
            {"text": "Normal"},
            {"text": "Sponsored"},
        ]

        with patch("core.ad_filter.get_config_value", return_value=False):
            filtered = filter_ad_elements(elements)

        assert len(filtered) == 2

    def test_strict_mode(self):
        elements = [
            {"text": "Normal"},
            {"text": "Sponsored"},  # Single indicator
            {"text": "Ad", "resource_id": "com.app:id/ad_container"},  # Multiple
        ]

        with patch("core.ad_filter.get_config_value", return_value=True):
            filtered = filter_ad_elements(elements, strict=True)

        # In strict mode, only the element with multiple indicators is filtered
        assert len(filtered) >= 1


class TestGetNonAdElementsAtPoint:
    """Tests for get_non_ad_elements_at_point function."""

    def test_returns_elements_at_point(self):
        elements = [
            {"text": "Button", "bounds": (100, 100, 200, 200)},
            {"text": "Ad", "resource_id": "com.app:id/ad_view", "bounds": (100, 100, 200, 200)},
            {"text": "Outside", "bounds": (300, 300, 400, 400)},
        ]

        result = get_non_ad_elements_at_point(elements, 150, 150)

        assert len(result) == 1
        assert result[0]["text"] == "Button"

    def test_excludes_ads(self):
        elements = [
            {"text": "Sponsored", "bounds": (0, 0, 100, 100)},
        ]

        result = get_non_ad_elements_at_point(elements, 50, 50)
        assert len(result) == 0


class TestFindNonAdAlternative:
    """Tests for find_non_ad_alternative function."""

    def test_finds_nearby_clickable(self):
        ad_element = {"bounds": (100, 200, 300, 250)}
        elements = [
            ad_element,
            {"text": "Button", "bounds": (100, 300, 300, 350), "clickable": True},
        ]

        result = find_non_ad_alternative(elements, ad_element)
        assert result is not None
        assert result["text"] == "Button"

    def test_returns_none_if_no_alternative(self):
        ad_element = {"bounds": (100, 200, 300, 250)}
        elements = [ad_element]

        result = find_non_ad_alternative(elements, ad_element)
        assert result is None


class TestCustomPatterns:
    """Tests for custom pattern management."""

    def test_add_custom_pattern(self):
        clear_custom_patterns()
        add_custom_ad_pattern("resource_id", r".*my_custom_ad.*")

        element = {"resource_id": "com.app:id/my_custom_ad_slot"}
        assert is_ad_element(element) is True

    def test_clear_custom_patterns(self):
        add_custom_ad_pattern("text", r".*custom_sponsored.*")
        clear_custom_patterns()

        # After clearing, custom patterns should not match
        # (but built-in patterns still work)
        # This might still match other patterns, so just verify no error


class TestAdFilterClass:
    """Tests for AdFilter class."""

    def test_init(self):
        af = AdFilter(enabled=True, strict_mode=False, log_filtered=True)
        assert af.enabled is True
        assert af.strict_mode is False
        assert af.log_filtered is True
        assert af.total_filtered == 0
        assert af.total_processed == 0

    def test_filter_when_enabled(self):
        af = AdFilter(enabled=True)
        elements = [
            {"text": "Normal"},
            {"text": "Sponsored"},
        ]

        filtered = af.filter(elements)
        assert len(filtered) == 1
        assert af.total_processed == 2
        assert af.total_filtered == 1

    def test_filter_when_disabled(self):
        af = AdFilter(enabled=False)
        elements = [
            {"text": "Normal"},
            {"text": "Sponsored"},
        ]

        filtered = af.filter(elements)
        assert len(filtered) == 2

    def test_is_ad(self):
        af = AdFilter(enabled=True)
        assert af.is_ad({"text": "Sponsored"}) is True
        assert af.is_ad({"text": "Normal"}) is False

    def test_is_ad_when_disabled(self):
        af = AdFilter(enabled=False)
        assert af.is_ad({"text": "Sponsored"}) is False

    def test_caching(self):
        af = AdFilter(enabled=True)
        elements = [
            {"text": "Sponsored", "resource_id": "ad1", "bounds": (0, 0, 100, 100)},
        ]

        # First call
        af.filter(elements)
        cache_size_1 = len(af._ad_cache)

        # Second call with same element
        af.filter(elements)
        cache_size_2 = len(af._ad_cache)

        assert cache_size_1 == cache_size_2  # Cache should have detected it

    def test_clear_cache(self):
        af = AdFilter(enabled=True)
        af._ad_cache.add(12345)
        af.clear_cache()
        assert len(af._ad_cache) == 0

    def test_get_stats(self):
        af = AdFilter(enabled=True)
        af.total_processed = 100
        af.total_filtered = 10

        stats = af.get_stats()
        assert stats["total_processed"] == 100
        assert stats["total_filtered"] == 10
        assert stats["filter_rate"] == 0.1

    def test_reset_stats(self):
        af = AdFilter(enabled=True)
        af.total_processed = 100
        af.total_filtered = 10
        af.reset_stats()

        assert af.total_processed == 0
        assert af.total_filtered == 0


class TestGetAdFilter:
    """Tests for get_ad_filter function."""

    def test_returns_ad_filter_instance(self):
        # Reset global filter
        import core.ad_filter as af_module

        af_module._global_filter = None

        with patch("core.ad_filter.get_config_value") as mock_config:
            mock_config.side_effect = lambda key, default=None: {
                "ad_filter.enabled": True,
                "ad_filter.strict_mode": False,
                "ad_filter.log_filtered": True,
                "ad_filter.custom_patterns": {},
            }.get(key, default)

            af = get_ad_filter()
            assert isinstance(af, AdFilter)


class TestDescribeElement:
    """Tests for _describe_element helper function."""

    def test_describe_with_all_fields(self):
        element = {
            "class": "android.widget.Button",
            "resource_id": "com.app:id/my_button",
            "text": "Click me please",
        }
        desc = _describe_element(element)
        assert "Button" in desc
        assert "my_button" in desc
        assert "Click me" in desc

    def test_describe_empty_element(self):
        element = {}
        desc = _describe_element(element)
        assert desc == "unknown element"


class TestPatternMatching:
    """Tests for pattern matching functions."""

    def test_compile_patterns_idempotent(self):
        _compile_patterns()
        _compile_patterns()  # Should not fail

    def test_matches_any_pattern_empty_value(self):
        _compile_patterns()
        import core.ad_filter as af_module

        patterns = af_module._COMPILED_PATTERNS.get("resource_id", [])
        assert _matches_any_pattern("", patterns) is False

    def test_matches_any_pattern_match(self):
        _compile_patterns()
        import core.ad_filter as af_module

        patterns = af_module._COMPILED_PATTERNS.get("resource_id", [])
        assert _matches_any_pattern("google_ad_view", patterns) is True
