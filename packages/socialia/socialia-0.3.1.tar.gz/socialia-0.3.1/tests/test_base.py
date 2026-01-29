"""Tests for socialia base module."""

import pytest
from unittest.mock import patch

from socialia.base import BasePoster


class ConcretePoster(BasePoster):
    """Concrete implementation for testing."""

    platform_name = "test"

    def post(self, text: str, **kwargs) -> dict:
        return {"success": True, "id": "123", "text": text}

    def delete(self, post_id: str) -> dict:
        return {"success": True, "deleted": post_id}


class TestBasePoster:
    """Test BasePoster base class."""

    def test_base_poster_is_abstract(self):
        """Test that BasePoster cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BasePoster()

    def test_concrete_poster_works(self):
        """Test concrete implementation works."""
        poster = ConcretePoster()
        result = poster.post("test")
        assert result["success"] is True

    def test_feed_default_implementation(self):
        """Test default feed returns not implemented."""
        poster = ConcretePoster()
        result = poster.feed()
        assert result["success"] is False
        assert "not implemented" in result["error"].lower()

    def test_mentions_default_implementation(self):
        """Test default mentions returns not implemented."""
        poster = ConcretePoster()
        result = poster.mentions()
        assert result["success"] is False

    def test_me_default_implementation(self):
        """Test default me returns not implemented."""
        poster = ConcretePoster()
        result = poster.me()
        assert result["success"] is False

    def test_check_default_implementation(self):
        """Test default check uses me()."""
        poster = ConcretePoster()
        result = poster.check()
        # Should fail because me() returns not implemented
        assert result["platform"] == "test"


class TestBranding:
    """Test branding module."""

    def test_get_env_var_name_format(self):
        """Test env var naming format."""
        from socialia._branding import get_env_var_name, ENV_PREFIX

        result = get_env_var_name("X_CONSUMER_KEY")
        # Should be PREFIX_KEY format using current ENV_PREFIX
        assert result == f"{ENV_PREFIX}_X_CONSUMER_KEY"
        assert "X_CONSUMER_KEY" in result

    def test_get_env_default(self):
        """Test getting env var with default."""
        from socialia._branding import get_env

        # Use a unique var name that won't exist
        result = get_env("TOTALLY_UNIQUE_NONEXISTENT_VAR_XYZ123", "default_value")
        assert result == "default_value"

    def test_get_env_with_value(self):
        """Test getting env var with SOCIALIA prefix."""
        from socialia._branding import get_env

        with patch.dict("os.environ", {"SOCIALIA_TEST_UNIQUE_VAR": "test_value"}):
            result = get_env("TEST_UNIQUE_VAR")
            assert result == "test_value"

    def test_get_mcp_server_name(self):
        """Test MCP server name generation."""
        from socialia._branding import get_mcp_server_name

        name = get_mcp_server_name()
        assert isinstance(name, str)
        assert len(name) > 0


class TestPlatformImports:
    """Test that all platform classes can be imported."""

    def test_import_twitter(self):
        """Test Twitter import."""
        from socialia import Twitter

        assert Twitter is not None

    def test_import_linkedin(self):
        """Test LinkedIn import."""
        from socialia import LinkedIn

        assert LinkedIn is not None

    def test_import_reddit(self):
        """Test Reddit import."""
        from socialia import Reddit

        assert Reddit is not None

    def test_import_youtube(self):
        """Test YouTube import."""
        from socialia import YouTube

        assert YouTube is not None

    def test_import_google_analytics(self):
        """Test GoogleAnalytics import."""
        from socialia import GoogleAnalytics

        assert GoogleAnalytics is not None

    def test_backward_compat_aliases(self):
        """Test backward compatibility aliases."""
        from socialia import TwitterPoster, LinkedInPoster, RedditPoster, YouTubePoster

        assert TwitterPoster is not None
        assert LinkedInPoster is not None
        assert RedditPoster is not None
        assert YouTubePoster is not None


class TestVersion:
    """Test version information."""

    def test_version_exists(self):
        """Test __version__ is defined."""
        from socialia import __version__

        assert __version__ is not None
        assert isinstance(__version__, str)
        assert len(__version__) > 0

    def test_version_format(self):
        """Test version follows semver-like format."""
        from socialia import __version__

        parts = __version__.split(".")
        assert len(parts) >= 2
        # First two parts should be numeric
        assert parts[0].isdigit()
        assert parts[1].isdigit()
