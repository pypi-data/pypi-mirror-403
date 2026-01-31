"""
NTLabs SDK - BB Resource Tests
Tests for the BBResource class (Banco do Brasil OAuth and PIX).

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
"""

from decimal import Decimal

from ntlabs.resources.bb import (
    BBResource,
    OAuthAuthorizeResult,
    OAuthTokenResult,
    OAuthUserInfo,
    PixChargeResult,
    PixStatusResult,
)


class TestOAuthAuthorizeResult:
    """Tests for OAuthAuthorizeResult dataclass."""

    def test_create_result(self):
        """Create OAuth authorize result."""
        result = OAuthAuthorizeResult(
            authorize_url="https://oauth.bb.com.br/authorize?...",
            state="abc123",
        )
        assert "oauth.bb.com.br" in result.authorize_url
        assert result.state == "abc123"


class TestOAuthTokenResult:
    """Tests for OAuthTokenResult dataclass."""

    def test_create_result(self):
        """Create OAuth token result."""
        result = OAuthTokenResult(
            access_token="eyJ...",
            refresh_token="refresh...",
            token_type="Bearer",
            expires_in=3600,
            scope="openid cpf",
        )
        assert result.access_token == "eyJ..."
        assert result.token_type == "Bearer"


class TestOAuthUserInfo:
    """Tests for OAuthUserInfo dataclass."""

    def test_create_userinfo(self):
        """Create user info."""
        info = OAuthUserInfo(
            sub="user-123",
            cpf="12345678909",
            nome="João Silva",
        )
        assert info.cpf == "12345678909"


class TestPixChargeResult:
    """Tests for PixChargeResult dataclass."""

    def test_create_charge(self):
        """Create PIX charge result."""
        charge = PixChargeResult(
            txid="txid-123",
            status="ATIVA",
            qr_code="00020126...",
            qr_code_base64="data:image/png;base64,...",
            amount=Decimal("99.90"),
            expires_at="2026-01-25T23:59:59Z",
            latency_ms=250,
            cost_brl=0.01,
        )
        assert charge.txid == "txid-123"
        assert charge.amount == Decimal("99.90")


class TestPixStatusResult:
    """Tests for PixStatusResult dataclass."""

    def test_create_status(self):
        """Create PIX status result."""
        status = PixStatusResult(
            txid="txid-123",
            status="CONCLUIDA",
            amount=Decimal("99.90"),
            e2eid="E12345678901234567890123456789012",
            paid_at="2026-01-25T10:00:00Z",
            latency_ms=150,
            cost_brl=0.01,
        )
        assert status.status == "CONCLUIDA"
        assert status.e2eid is not None


class TestBBResource:
    """Tests for BBResource."""

    def test_initialization(self, mock_client):
        """BBResource initializes with client."""
        bb = BBResource(mock_client)
        assert bb._client == mock_client

    def test_get_authorize_url(self, mock_client, mock_response):
        """Get BB OAuth authorization URL."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "authorize_url": "https://oauth.bb.com.br/oauth/authorize?client_id=...",
                "state": "state-abc123",
            }
        )

        result = mock_client.bb.get_authorize_url(
            redirect_uri="https://myapp.com/callback",
        )

        assert isinstance(result, OAuthAuthorizeResult)
        assert "oauth.bb.com.br" in result.authorize_url
        assert result.state == "state-abc123"

    def test_get_authorize_url_with_scope(self, mock_client, mock_response):
        """Get OAuth URL with custom scope."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "authorize_url": "https://oauth.bb.com.br/oauth/authorize?...",
                "state": "state-123",
            }
        )

        result = mock_client.bb.get_authorize_url(
            redirect_uri="https://myapp.com/callback",
            scope="openid cpf pix.read",
        )

        assert isinstance(result, OAuthAuthorizeResult)

    def test_exchange_code(self, mock_client, mock_response):
        """Exchange authorization code for tokens."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "refresh-token-123",
                "token_type": "Bearer",
                "expires_in": 3600,
                "scope": "openid cpf",
            }
        )

        result = mock_client.bb.exchange_code(
            code="auth-code-123",
            state="state-abc123",
            redirect_uri="https://myapp.com/callback",
        )

        assert isinstance(result, OAuthTokenResult)
        assert result.access_token.startswith("eyJ")
        assert result.expires_in == 3600

    def test_refresh_token(self, mock_client, mock_response):
        """Refresh access token."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "access_token": "new-access-token",
                "refresh_token": "new-refresh-token",
                "token_type": "Bearer",
                "expires_in": 3600,
            }
        )

        result = mock_client.bb.refresh_token(refresh_token="old-refresh-token")

        assert isinstance(result, OAuthTokenResult)
        assert result.access_token == "new-access-token"

    def test_get_userinfo(self, mock_client, mock_response):
        """Get user info from BB."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "sub": "12345678909",
                "cpf": "12345678909",
                "nome": "JOAO DA SILVA",
            }
        )

        result = mock_client.bb.get_userinfo(access_token="valid-token")

        assert isinstance(result, OAuthUserInfo)
        assert result.cpf == "12345678909"
        assert result.nome == "JOAO DA SILVA"

    def test_create_pix_charge(self, mock_client, mock_response):
        """Create PIX charge."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "txid": "txid-abc123",
                "status": "ATIVA",
                "qr_code": "00020126580014br.gov.bcb.pix...",
                "qr_code_base64": "data:image/png;base64,iVBORw0KGgo...",
                "amount": "99.90",
                "expires_at": "2026-01-26T00:00:00Z",
                "latency_ms": 350,
                "cost_brl": 0.01,
            }
        )

        result = mock_client.bb.create_pix_charge(
            amount=Decimal("99.90"),
            description="Assinatura Pro Mensal",
        )

        assert isinstance(result, PixChargeResult)
        assert result.txid == "txid-abc123"
        assert result.status == "ATIVA"
        assert result.amount == Decimal("99.90")
        assert result.qr_code.startswith("00020126")

    def test_create_pix_charge_with_payer(self, mock_client, mock_response):
        """Create PIX charge with payer info."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "txid": "txid-123",
                "status": "ATIVA",
                "qr_code": "00020126...",
                "amount": "150.00",
                "expires_at": "2026-01-26T00:00:00Z",
                "latency_ms": 200,
                "cost_brl": 0.01,
            }
        )

        result = mock_client.bb.create_pix_charge(
            amount=Decimal("150.00"),
            description="Consulta médica",
            payer_cpf="12345678909",
            payer_name="João Silva",
        )

        assert isinstance(result, PixChargeResult)

    def test_create_pix_charge_with_metadata(self, mock_client, mock_response):
        """Create PIX charge with custom metadata."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "txid": "txid-123",
                "status": "ATIVA",
                "qr_code": "00020126...",
                "amount": "50.00",
                "expires_at": "2026-01-26T00:00:00Z",
                "latency_ms": 180,
                "cost_brl": 0.01,
            }
        )

        result = mock_client.bb.create_pix_charge(
            amount=Decimal("50.00"),
            description="Produto X",
            metadata={"order_id": "order-123", "customer_id": "cust-456"},
        )

        assert isinstance(result, PixChargeResult)

    def test_get_pix_status_pending(self, mock_client, mock_response):
        """Get pending PIX status."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "txid": "txid-123",
                "status": "ATIVA",
                "amount": "99.90",
                "latency_ms": 100,
                "cost_brl": 0.005,
            }
        )

        result = mock_client.bb.get_pix_status("txid-123")

        assert isinstance(result, PixStatusResult)
        assert result.status == "ATIVA"
        assert result.e2eid is None
        assert result.paid_at is None

    def test_get_pix_status_paid(self, mock_client, mock_response):
        """Get paid PIX status."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "txid": "txid-123",
                "status": "CONCLUIDA",
                "amount": "99.90",
                "e2eid": "E12345678901234567890123456789012",
                "paid_at": "2026-01-25T14:30:00Z",
                "latency_ms": 120,
                "cost_brl": 0.005,
            }
        )

        result = mock_client.bb.get_pix_status("txid-123")

        assert result.status == "CONCLUIDA"
        assert result.e2eid is not None
        assert result.paid_at is not None

    def test_cancel_pix_charge(self, mock_client, mock_response):
        """Cancel PIX charge."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "txid": "txid-123",
                "status": "REMOVIDA_PELO_USUARIO_RECEBEDOR",
                "message": "Charge cancelled successfully",
            }
        )

        result = mock_client.bb.cancel_pix_charge("txid-123")

        assert result["status"] == "REMOVIDA_PELO_USUARIO_RECEBEDOR"

    def test_health(self, mock_client, mock_response):
        """Check BB API health."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "status": "healthy",
                "environment": "production",
                "oauth_status": "up",
                "pix_status": "up",
            }
        )

        health = mock_client.bb.health()

        assert health["status"] == "healthy"
        assert health["pix_status"] == "up"

    def test_empty_response_handling(self, mock_client, mock_response):
        """Handle empty responses gracefully."""
        mock_client._mock_http.request.return_value = mock_response({})

        # OAuth authorize
        result = mock_client.bb.get_authorize_url(redirect_uri="https://app.com/cb")
        assert result.authorize_url == ""
        assert result.state == ""

        # Exchange code
        result = mock_client.bb.exchange_code(
            code="abc", state="xyz", redirect_uri="https://app.com/cb"
        )
        assert result.access_token == ""
        assert result.token_type == "Bearer"

        # PIX charge
        result = mock_client.bb.create_pix_charge(
            amount=Decimal("10.00"),
            description="Test",
        )
        assert result.txid == ""
        assert result.status == ""

        # PIX status
        result = mock_client.bb.get_pix_status("txid-123")
        assert result.status == ""
        assert result.amount == Decimal("0")
