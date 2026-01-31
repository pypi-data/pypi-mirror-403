"""
NTLabs SDK - Async Banco do Brasil Resource Tests
Tests for the AsyncBBResource class.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock

from ntlabs.resources.async_bb import AsyncBBResource
from ntlabs.resources.bb import OAuthAuthorizeResult, OAuthTokenResult, OAuthUserInfo, PixChargeResult, PixStatusResult


@pytest.mark.asyncio
class TestAsyncBBResource:
    """Tests for AsyncBBResource."""

    async def test_initialization(self):
        """AsyncBBResource initializes with client."""
        mock_client = AsyncMock()
        bb = AsyncBBResource(mock_client)
        assert bb._client == mock_client


@pytest.mark.asyncio
class TestAsyncBBOAuth:
    """Tests for async BB OAuth."""

    async def test_get_authorize_url(self, bb_oauth_response):
        """Get authorization URL."""
        mock_client = AsyncMock()
        mock_client.post.return_value = bb_oauth_response

        bb = AsyncBBResource(mock_client)
        result = await bb.get_authorize_url("https://example.com/callback")

        assert isinstance(result, OAuthAuthorizeResult)
        assert result.authorize_url == bb_oauth_response["authorize_url"]
        assert result.state == bb_oauth_response["state"]
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/bb/oauth/authorize"
        assert call_args[1]["json"]["redirect_uri"] == "https://example.com/callback"

    async def test_get_authorize_url_with_scope(self, bb_oauth_response):
        """Get authorization URL with custom scope."""
        mock_client = AsyncMock()
        mock_client.post.return_value = bb_oauth_response

        bb = AsyncBBResource(mock_client)
        result = await bb.get_authorize_url(
            "https://example.com/callback",
            scope="openid-otp cpf email",
        )

        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["scope"] == "openid-otp cpf email"

    async def test_exchange_code(self, bb_token_response):
        """Exchange authorization code."""
        mock_client = AsyncMock()
        mock_client.post.return_value = bb_token_response

        bb = AsyncBBResource(mock_client)
        result = await bb.exchange_code("code_123", "state_abc", "https://example.com/callback")

        assert isinstance(result, OAuthTokenResult)
        assert result.access_token == bb_token_response["access_token"]
        assert result.refresh_token == bb_token_response["refresh_token"]
        assert result.token_type == "Bearer"
        assert result.expires_in == 3600
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/bb/oauth/callback"
        assert call_args[1]["json"]["code"] == "code_123"
        assert call_args[1]["json"]["state"] == "state_abc"

    async def test_refresh_token(self, bb_token_response):
        """Refresh access token."""
        mock_client = AsyncMock()
        mock_client.post.return_value = bb_token_response

        bb = AsyncBBResource(mock_client)
        result = await bb.refresh_token("refresh_123")

        assert isinstance(result, OAuthTokenResult)
        assert result.access_token == bb_token_response["access_token"]
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/bb/oauth/refresh"
        assert call_args[1]["json"]["refresh_token"] == "refresh_123"

    async def test_get_userinfo(self):
        """Get user info."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "sub": "user_123",
            "cpf": "12345678909",
            "nome": "João Silva",
        }

        bb = AsyncBBResource(mock_client)
        result = await bb.get_userinfo("access_token_123")

        assert isinstance(result, OAuthUserInfo)
        assert result.sub == "user_123"
        assert result.cpf == "12345678909"
        assert result.nome == "João Silva"
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/bb/oauth/userinfo"
        assert call_args[1]["params"]["access_token"] == "access_token_123"


@pytest.mark.asyncio
class TestAsyncBBPix:
    """Tests for async BB PIX."""

    async def test_create_pix_charge(self, pix_charge_response):
        """Create PIX charge."""
        mock_client = AsyncMock()
        mock_client.post.return_value = pix_charge_response

        bb = AsyncBBResource(mock_client)
        result = await bb.create_pix_charge(
            amount=Decimal("100.00"),
            description="Test payment",
            expiration_seconds=3600,
        )

        assert isinstance(result, PixChargeResult)
        assert result.txid == pix_charge_response["txid"]
        assert result.status == "ATIVA"
        assert result.qr_code == pix_charge_response["qr_code"]
        assert result.amount == Decimal("100.00")
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/bb/pix/charge"
        assert call_args[1]["json"]["amount"] == "100.00"
        assert call_args[1]["json"]["description"] == "Test payment"

    async def test_create_pix_charge_with_payer(self, pix_charge_response):
        """Create PIX charge with payer info."""
        mock_client = AsyncMock()
        mock_client.post.return_value = pix_charge_response

        bb = AsyncBBResource(mock_client)
        result = await bb.create_pix_charge(
            amount=Decimal("50.00"),
            description="Payment",
            payer_cpf="12345678909",
            payer_name="João Silva",
        )

        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["payer_cpf"] == "12345678909"
        assert call_args[1]["json"]["payer_name"] == "João Silva"

    async def test_create_pix_charge_with_metadata(self, pix_charge_response):
        """Create PIX charge with metadata."""
        mock_client = AsyncMock()
        mock_client.post.return_value = pix_charge_response

        bb = AsyncBBResource(mock_client)
        metadata = {"order_id": "123", "customer_id": "456"}
        result = await bb.create_pix_charge(
            amount=Decimal("75.00"),
            description="Order payment",
            metadata=metadata,
        )

        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["metadata"] == metadata

    async def test_get_pix_status(self):
        """Get PIX charge status."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "txid": "txid_abc123",
            "status": "CONCLUIDA",
            "amount": "100.00",
            "e2eid": "E123456789",
            "paid_at": "2026-01-27T20:00:00Z",
            "latency_ms": 100,
            "cost_brl": 0.01,
        }

        bb = AsyncBBResource(mock_client)
        result = await bb.get_pix_status("txid_abc123")

        assert isinstance(result, PixStatusResult)
        assert result.txid == "txid_abc123"
        assert result.status == "CONCLUIDA"
        assert result.amount == Decimal("100.00")
        assert result.e2eid == "E123456789"
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/bb/pix/charge/txid_abc123"

    async def test_cancel_pix_charge(self):
        """Cancel PIX charge."""
        mock_client = AsyncMock()
        mock_client.request.return_value = {"success": True}

        bb = AsyncBBResource(mock_client)
        result = await bb.cancel_pix_charge("txid_abc123")

        assert result["success"] is True
        mock_client.request.assert_called_once()
        call_args = mock_client.request.call_args
        assert call_args[0][0] == "DELETE"
        assert call_args[0][1] == "/v1/bb/pix/charge/txid_abc123"

    async def test_health(self):
        """Check BB API health."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {"status": "healthy", "pix": "up", "oauth": "up"}

        bb = AsyncBBResource(mock_client)
        result = await bb.health()

        assert result["status"] == "healthy"
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/bb/health"
