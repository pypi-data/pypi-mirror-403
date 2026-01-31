"""Tests for input validation utilities."""

from pincho.validation import normalize_tags


class TestNormalizeTags:
    """Test tag normalization functionality."""

    def test_none_input(self):
        """Test that None input returns empty list."""
        assert normalize_tags(None) == []

    def test_empty_list(self):
        """Test that empty list returns empty list."""
        assert normalize_tags([]) == []

    def test_single_tag(self):
        """Test normalization of single tag."""
        assert normalize_tags(["Production"]) == ["production"]

    def test_lowercase_conversion(self):
        """Test tags are converted to lowercase."""
        assert normalize_tags(["PROD", "STAGING", "Test"]) == ["prod", "staging", "test"]

    def test_whitespace_trimming(self):
        """Test whitespace is trimmed from tags."""
        assert normalize_tags(["  production  ", "release  ", "  deploy"]) == [
            "production",
            "release",
            "deploy",
        ]

    def test_duplicate_removal(self):
        """Test duplicate tags are removed (case-insensitive)."""
        assert normalize_tags(["production", "Production", "PRODUCTION"]) == ["production"]
        assert normalize_tags(["deploy", "release", "deploy"]) == ["deploy", "release"]

    def test_empty_string_removal(self):
        """Test empty strings are filtered out."""
        assert normalize_tags(["", "production", "  ", "release"]) == [
            "production",
            "release",
        ]

    def test_invalid_characters_stripped(self):
        """Test invalid characters are stripped from tags (not entire tag rejected)."""
        # Valid: alphanumeric, hyphens, underscores
        assert normalize_tags(["prod-1", "staging_2", "test123"]) == [
            "prod-1",
            "staging_2",
            "test123",
        ]

        # Invalid chars stripped: special characters removed
        assert normalize_tags(["prod@", "test!", "deploy#"]) == ["prod", "test", "deploy"]
        assert normalize_tags(["prod.env", "test(1)", "deploy[2]"]) == [
            "prodenv",
            "test1",
            "deploy2",
        ]

    def test_mixed_valid_invalid(self):
        """Test stripping when mixing valid and invalid chars."""
        assert normalize_tags(["production", "test@invalid", "release", "bad!"]) == [
            "production",
            "testinvalid",
            "release",
            "bad",
        ]

    def test_non_string_values_filtered(self):
        """Test non-string values are filtered out."""
        assert normalize_tags([123, "production", None, "release"]) == [  # type: ignore
            "production",
            "release",
        ]

    def test_all_filtered_returns_empty_list(self):
        """Test that if all tags are filtered out, empty list is returned."""
        assert normalize_tags(["", "  ", "@#$"]) == []
        assert normalize_tags([123, None, 456]) == []  # type: ignore

    def test_order_preserved(self):
        """Test that order of tags is preserved."""
        assert normalize_tags(["zebra", "alpha", "beta"]) == ["zebra", "alpha", "beta"]

    def test_duplicates_keep_first(self):
        """Test that duplicates keep the first occurrence."""
        assert normalize_tags(["production", "release", "production"]) == [
            "production",
            "release",
        ]

    def test_complex_scenario(self):
        """Test complex real-world scenario."""
        tags = [
            "  PRODUCTION  ",
            "Release",
            "production",  # duplicate
            "deploy-v2",
            "test@invalid",
            "",
            "  ",
            "RELEASE",  # duplicate
            "v1_0_0",
            "bad!tag",
        ]
        # Invalid chars stripped, not entire tag rejected
        expected = ["production", "release", "deploy-v2", "testinvalid", "v1_0_0", "badtag"]
        assert normalize_tags(tags) == expected

    def test_hyphen_underscore_allowed(self):
        """Test that hyphens and underscores are allowed."""
        assert normalize_tags(["feature-branch", "version_1_0", "test-123_abc"]) == [
            "feature-branch",
            "version_1_0",
            "test-123_abc",
        ]

    def test_numbers_allowed(self):
        """Test that numbers are allowed."""
        assert normalize_tags(["v123", "2024", "release-2"]) == ["v123", "2024", "release-2"]

    def test_unicode_stripped(self):
        """Test that unicode characters are stripped from tags."""
        # Unicode chars stripped, keeping valid ASCII chars
        assert normalize_tags(["production", "test-émoji", "release"]) == [
            "production",
            "test-moji",
            "release",
        ]

    def test_special_chars_completely_stripped(self):
        """Test tags with only special chars become empty and are removed."""
        assert normalize_tags(["@#$", "!!!", "..."]) == []
        assert normalize_tags(["valid", "@#$", "also-valid"]) == ["valid", "also-valid"]
