"""
NTLabs SDK - Auth Resource Tests
Tests for the AuthResource class.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
"""

from ntlabs.resources.auth import AuthResource


class TestAuthResource:
    """Tests for AuthResource."""

    def test_initialization(self, mock_client):
        """AuthResource initializes with client."""
        auth = AuthResource(mock_client)
        assert auth._client == mock_client

    def test_signup(self, mock_client, mock_response):
        """Sign up new user."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "access_token": "eyJ...",
                "refresh_token": "refresh...",
                "expires_in": 3600,
                "user": {
                    "id": "user-123",
                    "email": "user@example.com",
                    "full_name": "Test User",
                },
            }
        )

        result = mock_client.auth.signup(
            email="user@example.com",
            password="secure123",
            full_name="Test User",
        )

        assert result["access_token"] == "eyJ..."
        assert result["user"]["email"] == "user@example.com"

    def test_signup_minimal(self, mock_client, mock_response):
        """Sign up with minimal info."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "access_token": "eyJ...",
                "refresh_token": "refresh...",
                "expires_in": 3600,
                "user": {"id": "user-123", "email": "user@example.com"},
            }
        )

        result = mock_client.auth.signup(
            email="user@example.com",
            password="secure123",
        )

        assert result["access_token"] is not None

    def test_login(self, mock_client, mock_response):
        """Login with email/password."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "access_token": "eyJ...",
                "refresh_token": "refresh...",
                "expires_in": 3600,
                "user": {
                    "id": "user-123",
                    "email": "user@example.com",
                },
            }
        )

        result = mock_client.auth.login(
            email="user@example.com",
            password="secure123",
        )

        assert result["access_token"] == "eyJ..."
        assert result["expires_in"] == 3600

    def test_get_oauth_url_github(self, mock_client, mock_response):
        """Get GitHub OAuth URL."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "url": "https://github.com/login/oauth/authorize?...",
                "provider": "github",
            }
        )

        result = mock_client.auth.get_oauth_url("github")

        assert "github.com" in result["url"]
        assert result["provider"] == "github"

    def test_get_oauth_url_google(self, mock_client, mock_response):
        """Get Google OAuth URL."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "url": "https://accounts.google.com/o/oauth2/auth?...",
                "provider": "google",
            }
        )

        result = mock_client.auth.get_oauth_url("google")

        assert "google.com" in result["url"]
        assert result["provider"] == "google"

    def test_get_oauth_url_with_redirect(self, mock_client, mock_response):
        """Get OAuth URL with custom redirect."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "url": "https://github.com/login/oauth/authorize?redirect_uri=...",
                "provider": "github",
            }
        )

        result = mock_client.auth.get_oauth_url(
            "github",
            redirect_uri="https://myapp.com/callback",
        )

        assert "url" in result

    def test_exchange_code(self, mock_client, mock_response):
        """Exchange OAuth code for tokens."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "access_token": "eyJ...",
                "refresh_token": "refresh...",
                "expires_in": 3600,
                "user": {
                    "id": "user-123",
                    "email": "user@github.com",
                    "full_name": "GitHub User",
                },
            }
        )

        result = mock_client.auth.exchange_code(code="abc123")

        assert result["access_token"] == "eyJ..."
        assert result["user"]["id"] == "user-123"

    def test_refresh(self, mock_client, mock_response):
        """Refresh access token."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "access_token": "new_token...",
                "refresh_token": "new_refresh...",
                "expires_in": 3600,
                "user": {"id": "user-123"},
            }
        )

        result = mock_client.auth.refresh(refresh_token="old_refresh...")

        assert result["access_token"] == "new_token..."
        assert result["refresh_token"] == "new_refresh..."

    def test_me(self, mock_client, mock_response):
        """Get current user."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "id": "user-123",
                "email": "user@example.com",
                "full_name": "Test User",
                "avatar_url": "https://...",
                "provider": "github",
                "role": "user",
            }
        )

        result = mock_client.auth.me()

        assert result["id"] == "user-123"
        assert result["email"] == "user@example.com"
        assert result["role"] == "user"

    def test_me_with_token(self, mock_client, mock_response):
        """Get user with explicit token."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "id": "user-456",
                "email": "other@example.com",
            }
        )

        result = mock_client.auth.me(access_token="custom_token")

        assert result["id"] == "user-456"

    def test_validate(self, mock_client, mock_response):
        """Validate access token."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "valid": True,
                "user_id": "user-123",
                "expires_at": "2026-01-25T00:00:00Z",
            }
        )

        result = mock_client.auth.validate(access_token="eyJ...")

        assert result["valid"] is True
        assert result["user_id"] == "user-123"

    def test_validate_invalid_token(self, mock_client, mock_response):
        """Validate invalid token."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "valid": False,
                "error": "Token expired",
            }
        )

        result = mock_client.auth.validate(access_token="expired_token")

        assert result["valid"] is False

    def test_logout(self, mock_client, mock_response):
        """Logout user."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "message": "Logged out successfully",
            }
        )

        result = mock_client.auth.logout()

        assert result["message"] == "Logged out successfully"
