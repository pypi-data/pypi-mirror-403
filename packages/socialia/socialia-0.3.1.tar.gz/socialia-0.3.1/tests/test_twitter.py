"""Tests for Twitter client."""

from unittest.mock import MagicMock

from socialia.twitter import Twitter


class TestTwitter:
    """Test Twitter class."""

    def test_init_with_credentials(self, twitter_credentials):
        """Test initialization with explicit credentials."""
        client = Twitter(**twitter_credentials)
        assert client.consumer_key == "test_consumer_key"
        assert client.consumer_secret == "test_consumer_secret"
        assert client.access_token == "test_access_token"
        assert client.access_token_secret == "test_access_token_secret"

    def test_init_from_environment(self, monkeypatch):
        """Test initialization from environment variables."""
        # Clear any existing env vars first
        for prefix in ["SOCIALIA_", "SCITEX_"]:
            monkeypatch.delenv(f"{prefix}X_CONSUMER_KEY", raising=False)
            monkeypatch.delenv(f"{prefix}X_CONSUMER_KEY_SECRET", raising=False)
            monkeypatch.delenv(f"{prefix}X_ACCESSTOKEN", raising=False)
            monkeypatch.delenv(f"{prefix}X_ACCESSTOKEN_SECRET", raising=False)

        monkeypatch.setenv("SOCIALIA_X_CONSUMER_KEY", "env_consumer_key")
        monkeypatch.setenv("SOCIALIA_X_CONSUMER_KEY_SECRET", "env_consumer_secret")
        monkeypatch.setenv("SOCIALIA_X_ACCESSTOKEN", "env_access_token")
        monkeypatch.setenv("SOCIALIA_X_ACCESSTOKEN_SECRET", "env_access_secret")

        client = Twitter()
        assert client.consumer_key == "env_consumer_key"
        assert client.consumer_secret == "env_consumer_secret"

    def test_validate_credentials_valid(self, twitter_credentials):
        """Test credential validation with valid credentials."""
        client = Twitter(**twitter_credentials)
        assert client.validate_credentials() is True

    def test_validate_credentials_missing(self, monkeypatch):
        """Test credential validation with missing credentials."""
        # Clear environment variables for both prefixes
        for prefix in ["SOCIALIA_", "SCITEX_"]:
            monkeypatch.delenv(f"{prefix}X_CONSUMER_KEY", raising=False)
            monkeypatch.delenv(f"{prefix}X_CONSUMER_KEY_SECRET", raising=False)
            monkeypatch.delenv(f"{prefix}X_ACCESSTOKEN", raising=False)
            monkeypatch.delenv(f"{prefix}X_ACCESSTOKEN_SECRET", raising=False)
        client = Twitter(consumer_key="only_one")
        assert client.validate_credentials() is False

    def test_post_missing_credentials(self, monkeypatch):
        """Test post fails with missing credentials."""
        # Clear environment variables for both prefixes
        for prefix in ["SOCIALIA_", "SCITEX_"]:
            monkeypatch.delenv(f"{prefix}X_CONSUMER_KEY", raising=False)
            monkeypatch.delenv(f"{prefix}X_CONSUMER_KEY_SECRET", raising=False)
            monkeypatch.delenv(f"{prefix}X_ACCESSTOKEN", raising=False)
            monkeypatch.delenv(f"{prefix}X_ACCESSTOKEN_SECRET", raising=False)
        client = Twitter()
        result = client.post("Test")
        assert result["success"] is False
        assert "credentials" in result["error"].lower()

    def test_post_success(self, twitter_credentials, mock_oauth_session):
        """Test successful post."""
        mock_oauth_session.post.return_value = MagicMock(
            status_code=201,
            json=lambda: {"data": {"id": "12345"}},
        )

        client = Twitter(**twitter_credentials)
        result = client.post("Hello World!")

        assert result["success"] is True
        assert result["id"] == "12345"
        assert "x.com" in result["url"]

    def test_post_failure(self, twitter_credentials, mock_oauth_session):
        """Test failed post."""
        mock_oauth_session.post.return_value = MagicMock(
            status_code=403,
            text="Forbidden",
        )

        client = Twitter(**twitter_credentials)
        result = client.post("Hello World!")

        assert result["success"] is False
        assert "403" in result["error"]

    def test_post_with_reply(self, twitter_credentials, mock_oauth_session):
        """Test post with reply_to."""
        mock_oauth_session.post.return_value = MagicMock(
            status_code=201,
            json=lambda: {"data": {"id": "67890"}},
        )

        client = Twitter(**twitter_credentials)
        result = client.post("Reply text", reply_to="12345")

        assert result["success"] is True
        call_args = mock_oauth_session.post.call_args
        assert "reply" in call_args.kwargs["json"]

    def test_delete_success(self, twitter_credentials, mock_oauth_session):
        """Test successful delete."""
        mock_oauth_session.delete.return_value = MagicMock(status_code=200)

        client = Twitter(**twitter_credentials)
        result = client.delete("12345")

        assert result["success"] is True
        assert result["deleted"] is True

    def test_delete_failure(self, twitter_credentials, mock_oauth_session):
        """Test failed delete."""
        mock_oauth_session.delete.return_value = MagicMock(
            status_code=404,
            text="Not Found",
        )

        client = Twitter(**twitter_credentials)
        result = client.delete("invalid_id")

        assert result["success"] is False
        assert "404" in result["error"]

    def test_post_thread_success(self, twitter_credentials, mock_oauth_session):
        """Test successful thread posting."""
        mock_oauth_session.post.side_effect = [
            MagicMock(status_code=201, json=lambda: {"data": {"id": "1"}}),
            MagicMock(status_code=201, json=lambda: {"data": {"id": "2"}}),
            MagicMock(status_code=201, json=lambda: {"data": {"id": "3"}}),
        ]

        client = Twitter(**twitter_credentials)
        result = client.post_thread(["First", "Second", "Third"])

        assert result["success"] is True
        assert len(result["ids"]) == 3
        assert len(result["urls"]) == 3

    def test_post_thread_partial_failure(self, twitter_credentials, mock_oauth_session):
        """Test thread posting with partial failure."""
        mock_oauth_session.post.side_effect = [
            MagicMock(status_code=201, json=lambda: {"data": {"id": "1"}}),
            MagicMock(status_code=403, text="Rate limited"),
        ]

        client = Twitter(**twitter_credentials)
        result = client.post_thread(["First", "Second", "Third"])

        assert result["success"] is False
        assert "partial_ids" in result
        assert len(result["partial_ids"]) == 1
