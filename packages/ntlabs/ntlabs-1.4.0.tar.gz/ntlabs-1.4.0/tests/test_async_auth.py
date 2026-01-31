"""
NTLabs SDK - Async Authentication Resource Tests
Tests for the AsyncAuthResource class.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
"""

import pytest
from unittest.mock import AsyncMock

from ntlabs.resources.async_auth import AsyncAuthResource


@pytest.mark.asyncio
class TestAsyncAuthResourceBasic:
    """Tests for basic AsyncAuthResource operations."""

    async def test_initialization(self):
        """AsyncAuthResource initializes with client."""
        mock_client = AsyncMock()
        auth = AsyncAuthResource(mock_client)
        assert auth._client == mock_client


@pytest.mark.asyncio
class TestAsyncAuthResourceSignup:
    """Tests for async signup."""

    async def test_signup(self, auth_response):
        """Register a new user."""
        mock_client = AsyncMock()
        mock_client.post.return_value = auth_response

        auth = AsyncAuthResource(mock_client)
        result = await auth.signup(
            email="user@example.com",
            password="secure123",
            full_name="Test User",
        )

        assert result["access_token"] == auth_response["access_token"]
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/api/auth/signup"
        assert call_args[1]["json"]["email"] == "user@example.com"
        assert call_args[1]["json"]["password"] == "secure123"
        assert call_args[1]["json"]["full_name"] == "Test User"

    async def test_signup_without_full_name(self, auth_response):
        """Register without optional full_name."""
        mock_client = AsyncMock()
        mock_client.post.return_value = auth_response

        auth = AsyncAuthResource(mock_client)
        result = await auth.signup(
            email="user@example.com",
            password="secure123",
        )

        assert result["access_token"] == auth_response["access_token"]


@pytest.mark.asyncio
class TestAsyncAuthResourceLogin:
    """Tests for async login."""

    async def test_login(self, auth_response):
        """Login with email/password."""
        mock_client = AsyncMock()
        mock_client.post.return_value = auth_response

        auth = AsyncAuthResource(mock_client)
        result = await auth.login("user@example.com", "secure123")

        assert result["access_token"] == auth_response["access_token"]
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/api/auth/login"
        assert call_args[1]["json"]["email"] == "user@example.com"
        assert call_args[1]["json"]["password"] == "secure123"


@pytest.mark.asyncio
class TestAsyncAuthResourceOAuth:
    """Tests for async OAuth v1."""

    async def test_get_oauth_url(self):
        """Get OAuth URL."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "authorization_url": "https://github.com/login/oauth/authorize?client_id=...",
            "state": "xyz123",
        }

        auth = AsyncAuthResource(mock_client)
        result = await auth.get_oauth_url("github")

        assert "authorization_url" in result
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/api/auth/login/github"

    async def test_get_oauth_url_with_redirect(self):
        """Get OAuth URL with redirect URI."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {"authorization_url": "...", "state": "xyz"}

        auth = AsyncAuthResource(mock_client)
        result = await auth.get_oauth_url(
            "google",
            redirect_uri="https://example.com/callback",
        )

        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[1]["params"]["redirect_uri"] == "https://example.com/callback"

    async def test_exchange_code(self, auth_response):
        """Exchange OAuth code for tokens."""
        mock_client = AsyncMock()
        mock_client.post.return_value = auth_response

        auth = AsyncAuthResource(mock_client)
        result = await auth.exchange_code("auth_code_123")

        assert result["access_token"] == auth_response["access_token"]
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/api/auth/exchange"
        assert call_args[1]["json"]["code"] == "auth_code_123"


@pytest.mark.asyncio
class TestAsyncAuthResourceTokens:
    """Tests for async token operations."""

    async def test_refresh(self, auth_response):
        """Refresh access token."""
        mock_client = AsyncMock()
        mock_client.post.return_value = auth_response

        auth = AsyncAuthResource(mock_client)
        result = await auth.refresh("refresh_token_123")

        assert result["access_token"] == auth_response["access_token"]
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/api/auth/refresh"
        assert call_args[1]["json"]["refresh_token"] == "refresh_token_123"

    async def test_me(self):
        """Get current user."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "id": "user_123",
            "email": "user@example.com",
            "full_name": "Test User",
        }

        auth = AsyncAuthResource(mock_client)
        result = await auth.me()

        assert result["email"] == "user@example.com"
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/api/auth/me"

    async def test_me_with_token(self):
        """Get current user with explicit token."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {"id": "user_123", "email": "user@example.com"}

        auth = AsyncAuthResource(mock_client)
        result = await auth.me(access_token="bearer_token_123")

        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[1]["headers"]["Authorization"] == "Bearer bearer_token_123"

    async def test_validate(self):
        """Validate access token."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {"valid": True, "user_id": "user_123"}

        auth = AsyncAuthResource(mock_client)
        result = await auth.validate("access_token_123")

        assert result["valid"] is True
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/api/auth/validate"
        assert call_args[1]["json"]["token"] == "access_token_123"

    async def test_logout(self):
        """Logout current user."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {"success": True}

        auth = AsyncAuthResource(mock_client)
        result = await auth.logout()

        assert result["success"] is True
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/api/auth/logout"


@pytest.mark.asyncio
class TestAsyncAuthResourceOAuthV2:
    """Tests for async OAuth v2 (PKCE)."""

    async def test_initiate_oauth_v2(self, oauth_v2_response):
        """Initiate OAuth v2 flow."""
        mock_client = AsyncMock()
        mock_client.post.return_value = oauth_v2_response

        auth = AsyncAuthResource(mock_client)
        result = await auth.initiate_oauth_v2(
            provider="github",
            redirect_uri="https://example.com/callback",
        )

        assert result["session_id"] == oauth_v2_response["session_id"]
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/api/v2/auth/initiate/github"
        assert call_args[1]["json"]["redirect_uri"] == "https://example.com/callback"
        assert call_args[1]["json"]["product"] == "lab"

    async def test_initiate_oauth_v2_with_product(self, oauth_v2_response):
        """Initiate OAuth v2 with specific product."""
        mock_client = AsyncMock()
        mock_client.post.return_value = oauth_v2_response

        auth = AsyncAuthResource(mock_client)
        result = await auth.initiate_oauth_v2(
            provider="google",
            redirect_uri="https://example.com/callback",
            product="hipocrates",
        )

        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["product"] == "hipocrates"

    async def test_claim_session(self):
        """Claim pending session."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {"success": True, "access_token": "new_token"}

        auth = AsyncAuthResource(mock_client)
        result = await auth.claim_session("sess_123", "signature_xyz")

        assert result["success"] is True
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/api/v2/auth/session/claim"
        assert call_args[1]["json"]["session_id"] == "sess_123"
        assert call_args[1]["json"]["signature"] == "signature_xyz"

    async def test_validate_session(self):
        """Validate session."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {"valid": True, "session_id": "sess_123"}

        auth = AsyncAuthResource(mock_client)
        result = await auth.validate_session(
            session_id="sess_123",
            access_token="token_123",
            product="hipocrates",
        )

        assert result["valid"] is True
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/api/v2/auth/validate"
        assert call_args[1]["json"]["session_id"] == "sess_123"
        assert call_args[1]["json"]["access_token"] == "token_123"
        assert call_args[1]["json"]["product"] == "hipocrates"

    async def test_refresh_v2(self):
        """Refresh tokens using v2."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "access_token": "new_access",
            "refresh_token": "new_refresh",
        }

        auth = AsyncAuthResource(mock_client)
        result = await auth.refresh_v2("refresh_token_123", "sess_123")

        assert result["access_token"] == "new_access"
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/api/v2/auth/refresh"
        assert call_args[1]["json"]["refresh_token"] == "refresh_token_123"
        assert call_args[1]["json"]["session_id"] == "sess_123"

    async def test_revoke_session(self):
        """Revoke session."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {"success": True}

        auth = AsyncAuthResource(mock_client)
        result = await auth.revoke_session(
            session_id="sess_123",
            revoke_all=False,
            reason="User logout",
        )

        assert result["success"] is True
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/api/v2/auth/revoke"
        assert call_args[1]["json"]["session_id"] == "sess_123"
        assert call_args[1]["json"]["revoke_all"] is False
        assert call_args[1]["json"]["reason"] == "User logout"


@pytest.mark.asyncio
class TestAsyncAuthResourceSSO:
    """Tests for async SSO operations."""

    async def test_check_sso(self):
        """Check SSO status."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {"valid": True, "product": "lab"}

        auth = AsyncAuthResource(mock_client)
        result = await auth.check_sso(product="lab")

        assert result["valid"] is True
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/api/v2/auth/sso/check"
        assert call_args[1]["params"]["product"] == "lab"

    async def test_create_sso_ticket(self):
        """Create SSO ticket."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {"ticket": "ticket_abc123", "expires_at": "2026-01-28T20:00:00Z"}

        auth = AsyncAuthResource(mock_client)
        result = await auth.create_sso_ticket(target_product="hipocrates")

        assert result["ticket"] == "ticket_abc123"
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/api/v2/auth/sso/create-ticket"
        assert call_args[1]["params"]["target_product"] == "hipocrates"

    async def test_exchange_sso_ticket(self):
        """Exchange SSO ticket."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {"session_id": "new_sess_123", "access_token": "new_token"}

        auth = AsyncAuthResource(mock_client)
        result = await auth.exchange_sso_ticket("ticket_abc123", "hipocrates")

        assert result["session_id"] == "new_sess_123"
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/api/v2/auth/sso/exchange-ticket"
        assert call_args[1]["json"]["ticket"] == "ticket_abc123"
        assert call_args[1]["json"]["target_product"] == "hipocrates"
