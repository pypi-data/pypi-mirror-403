"""Tests for socialia analytics module."""

from unittest.mock import patch, MagicMock

from socialia.analytics import GoogleAnalytics


class TestGoogleAnalyticsInit:
    """Test GoogleAnalytics initialization."""

    def test_init_without_credentials(self):
        """Test initialization without credentials."""
        with patch.dict("os.environ", {}, clear=True):
            ga = GoogleAnalytics()
            assert ga.measurement_id is None
            assert ga.api_secret is None

    def test_init_with_credentials(self):
        """Test initialization with credentials from env."""
        env_vars = {
            "SOCIALIA_GOOGLE_ANALYTICS_MEASUREMENT_ID": "G-TEST123",
            "SOCIALIA_GOOGLE_ANALYTICS_API_SECRET": "secret123",
        }
        with patch.dict("os.environ", env_vars, clear=True):
            ga = GoogleAnalytics()
            assert ga.measurement_id == "G-TEST123"
            assert ga.api_secret == "secret123"

    def test_init_with_scitex_prefix(self):
        """Test initialization with SCITEX_ prefix."""
        env_vars = {
            "SCITEX_GOOGLE_ANALYTICS_MEASUREMENT_ID": "G-SCITEX",
            "SCITEX_GOOGLE_ANALYTICS_API_SECRET": "scitex_secret",
        }
        with patch.dict("os.environ", env_vars, clear=True):
            ga = GoogleAnalytics()
            assert ga.measurement_id == "G-SCITEX"
            assert ga.api_secret == "scitex_secret"


class TestGoogleAnalyticsValidation:
    """Test GoogleAnalytics validation methods."""

    def test_validate_no_credentials(self):
        """Test validate_credentials returns false when no credentials."""
        with patch.dict("os.environ", {}, clear=True):
            ga = GoogleAnalytics()
            result = ga.validate_credentials()
            assert result["measurement_protocol"] is False

    def test_validate_with_credentials(self):
        """Test validate_credentials with valid credentials format."""
        env_vars = {
            "SOCIALIA_GOOGLE_ANALYTICS_MEASUREMENT_ID": "G-TEST123",
            "SOCIALIA_GOOGLE_ANALYTICS_API_SECRET": "secret123",
        }
        with patch.dict("os.environ", env_vars, clear=True):
            ga = GoogleAnalytics()
            result = ga.validate_credentials()
            assert result["measurement_protocol"] is True


class TestGoogleAnalyticsTrackEvent:
    """Test GoogleAnalytics track_event method."""

    def test_track_event_no_credentials(self):
        """Test track_event without credentials."""
        with patch.dict("os.environ", {}, clear=True):
            ga = GoogleAnalytics()
            result = ga.track_event("test_event")
            assert result["success"] is False
            assert "error" in result

    @patch("requests.post")
    def test_track_event_success(self, mock_post):
        """Test successful event tracking."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response

        env_vars = {
            "SOCIALIA_GOOGLE_ANALYTICS_MEASUREMENT_ID": "G-TEST123",
            "SOCIALIA_GOOGLE_ANALYTICS_API_SECRET": "secret123",
        }
        with patch.dict("os.environ", env_vars, clear=True):
            ga = GoogleAnalytics()
            result = ga.track_event("test_event", {"key": "value"})
            assert result["success"] is True
            mock_post.assert_called_once()

    @patch("requests.post")
    def test_track_event_failure(self, mock_post):
        """Test failed event tracking."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        env_vars = {
            "SOCIALIA_GOOGLE_ANALYTICS_MEASUREMENT_ID": "G-TEST123",
            "SOCIALIA_GOOGLE_ANALYTICS_API_SECRET": "secret123",
        }
        with patch.dict("os.environ", env_vars, clear=True):
            ga = GoogleAnalytics()
            result = ga.track_event("test_event")
            assert result["success"] is False


class TestAnalyticsCLI:
    """Test analytics CLI commands."""

    def test_analytics_track_parsing(self):
        """Test analytics track command parsing."""
        from socialia.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["analytics", "track", "page_view"])
        assert args.command == "analytics"
        assert args.analytics_command == "track"
        assert args.event_name == "page_view"

    def test_analytics_track_with_params(self):
        """Test analytics track with parameters."""
        from socialia.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(
            ["analytics", "track", "event", "--param", "key1", "value1"]
        )
        assert args.param == [["key1", "value1"]]

    def test_analytics_realtime_parsing(self):
        """Test analytics realtime command parsing."""
        from socialia.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["analytics", "realtime"])
        assert args.analytics_command == "realtime"

    def test_analytics_pageviews_parsing(self):
        """Test analytics pageviews command parsing."""
        from socialia.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(
            ["analytics", "pageviews", "--start", "30daysAgo", "--end", "today"]
        )
        assert args.analytics_command == "pageviews"
        assert args.start == "30daysAgo"
        assert args.end == "today"

    def test_analytics_sources_parsing(self):
        """Test analytics sources command parsing."""
        from socialia.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["analytics", "sources"])
        assert args.analytics_command == "sources"
