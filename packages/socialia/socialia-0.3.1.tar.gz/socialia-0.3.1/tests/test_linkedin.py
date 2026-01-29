"""Tests for LinkedIn client."""

from unittest.mock import MagicMock, patch

from socialia.linkedin import LinkedIn


class TestLinkedIn:
    """Test LinkedIn class."""

    def test_init_with_token(self, linkedin_credentials):
        """Test initialization with explicit token."""
        client = LinkedIn(**linkedin_credentials)
        assert client.access_token == "test_linkedin_token"

    def test_init_from_environment(self, monkeypatch):
        """Test initialization from environment variables."""
        # Clear any existing env vars first
        monkeypatch.delenv("SOCIALIA_LINKEDIN_ACCESS_TOKEN", raising=False)
        monkeypatch.delenv("SCITEX_LINKEDIN_ACCESS_TOKEN", raising=False)
        monkeypatch.setenv("SOCIALIA_LINKEDIN_ACCESS_TOKEN", "env_token")
        client = LinkedIn()
        assert client.access_token == "env_token"

    def test_validate_credentials_valid(self, linkedin_credentials):
        """Test credential validation with valid token."""
        client = LinkedIn(**linkedin_credentials)
        assert client.validate_credentials() is True

    def test_validate_credentials_missing(self, monkeypatch):
        """Test credential validation with missing token."""
        # Clear environment variables that might be set
        monkeypatch.delenv("SOCIALIA_LINKEDIN_ACCESS_TOKEN", raising=False)
        monkeypatch.delenv("SCITEX_LINKEDIN_ACCESS_TOKEN", raising=False)
        client = LinkedIn()
        assert client.validate_credentials() is False

    def test_post_missing_credentials(self, monkeypatch):
        """Test post fails with missing credentials."""
        # Clear environment variables that might be set
        monkeypatch.delenv("SOCIALIA_LINKEDIN_ACCESS_TOKEN", raising=False)
        monkeypatch.delenv("SCITEX_LINKEDIN_ACCESS_TOKEN", raising=False)
        client = LinkedIn()
        result = client.post("Test")
        assert result["success"] is False
        assert "token" in result["error"].lower()

    @patch("socialia.linkedin.requests")
    def test_get_user_urn_success(self, mock_requests, linkedin_credentials):
        """Test successful user URN retrieval."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "user123"}
        mock_requests.get.return_value = mock_response

        client = LinkedIn(**linkedin_credentials)
        user_urn = client._get_user_urn()

        assert user_urn == "urn:li:person:user123"

    @patch("socialia.linkedin.requests")
    def test_post_success(self, mock_requests, linkedin_credentials):
        """Test successful post."""
        # Mock user URN call
        mock_user_response = MagicMock()
        mock_user_response.status_code = 200
        mock_user_response.json.return_value = {"id": "user123"}

        # Mock post call
        mock_post_response = MagicMock()
        mock_post_response.status_code = 201
        mock_post_response.headers = {"X-RestLi-Id": "share123"}
        mock_post_response.json.return_value = {}

        mock_requests.get.return_value = mock_user_response
        mock_requests.post.return_value = mock_post_response

        client = LinkedIn(**linkedin_credentials)
        result = client.post("Hello LinkedIn!")

        assert result["success"] is True
        assert result["id"] == "share123"

    @patch("socialia.linkedin.requests")
    def test_post_failure(self, mock_requests, linkedin_credentials):
        """Test failed post."""
        # Mock user URN call
        mock_user_response = MagicMock()
        mock_user_response.status_code = 200
        mock_user_response.json.return_value = {"id": "user123"}

        # Mock failed post call
        mock_post_response = MagicMock()
        mock_post_response.status_code = 401
        mock_post_response.text = "Unauthorized"

        mock_requests.get.return_value = mock_user_response
        mock_requests.post.return_value = mock_post_response

        client = LinkedIn(**linkedin_credentials)
        result = client.post("Test post")

        assert result["success"] is False
        assert "401" in result["error"]

    @patch("socialia.linkedin.requests")
    def test_delete_success(self, mock_requests, linkedin_credentials):
        """Test successful delete."""
        mock_response = MagicMock()
        mock_response.status_code = 204

        mock_requests.delete.return_value = mock_response

        client = LinkedIn(**linkedin_credentials)
        result = client.delete("share123")

        assert result["success"] is True
        assert result["deleted"] is True

    @patch("socialia.linkedin.requests")
    def test_delete_failure(self, mock_requests, linkedin_credentials):
        """Test failed delete."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"

        mock_requests.delete.return_value = mock_response

        client = LinkedIn(**linkedin_credentials)
        result = client.delete("invalid_id")

        assert result["success"] is False
        assert "404" in result["error"]
