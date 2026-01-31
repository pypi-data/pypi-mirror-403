"""
Neural LAB - AI Solutions Platform
Banco do Brasil Resource - OAuth and PIX operations.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-24
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from ..base import DataclassMixin


@dataclass
class OAuthAuthorizeResult(DataclassMixin):
    """OAuth authorization URL result."""

    authorize_url: str
    state: str


@dataclass
class OAuthTokenResult(DataclassMixin):
    """OAuth token result."""

    access_token: str
    refresh_token: str | None
    token_type: str
    expires_in: int
    scope: str | None


@dataclass
class OAuthUserInfo(DataclassMixin):
    """User info from BB."""

    sub: str
    cpf: str | None
    nome: str | None


@dataclass
class PixChargeResult(DataclassMixin):
    """PIX charge result."""

    txid: str
    status: str
    qr_code: str
    qr_code_base64: str | None
    amount: Decimal
    expires_at: str
    latency_ms: int
    cost_brl: float


@dataclass
class PixStatusResult(DataclassMixin):
    """PIX status result."""

    txid: str
    status: str
    amount: Decimal
    e2eid: str | None
    paid_at: str | None
    latency_ms: int
    cost_brl: float


class BBResource:
    """
    Banco do Brasil resource for OAuth and PIX operations.

    Usage:
        # OAuth - Get authorization URL
        auth = client.bb.get_authorize_url(
            redirect_uri="https://myapp.com/callback"
        )
        # Redirect user to auth.authorize_url

        # OAuth - Exchange code for token
        tokens = client.bb.exchange_code(
            code="abc123",
            state="xyz",
            redirect_uri="https://myapp.com/callback"
        )

        # PIX - Create charge
        charge = client.bb.create_pix_charge(
            amount=Decimal("99.90"),
            description="Assinatura Pro"
        )
        print(charge.qr_code)
    """

    def __init__(self, client):
        self._client = client

    # =========================================================================
    # OAuth
    # =========================================================================

    def get_authorize_url(
        self,
        redirect_uri: str,
        scope: str = "openid-otp cpf",
    ) -> OAuthAuthorizeResult:
        """
        Get BB OAuth authorization URL.

        Args:
            redirect_uri: URL to redirect after authorization
            scope: OAuth scopes to request

        Returns:
            OAuthAuthorizeResult with authorize_url and state
        """
        response = self._client.post(
            "/v1/bb/oauth/authorize",
            json={
                "redirect_uri": redirect_uri,
                "scope": scope,
            },
        )

        return OAuthAuthorizeResult(
            authorize_url=response.get("authorize_url", ""),
            state=response.get("state", ""),
        )

    def exchange_code(
        self,
        code: str,
        state: str,
        redirect_uri: str,
    ) -> OAuthTokenResult:
        """
        Exchange authorization code for tokens.

        Args:
            code: Authorization code from BB callback
            state: State token for CSRF validation
            redirect_uri: Same redirect_uri used in authorize

        Returns:
            OAuthTokenResult with access_token, refresh_token, etc.
        """
        response = self._client.post(
            "/v1/bb/oauth/callback",
            json={
                "code": code,
                "state": state,
                "redirect_uri": redirect_uri,
            },
        )

        return OAuthTokenResult(
            access_token=response.get("access_token", ""),
            refresh_token=response.get("refresh_token"),
            token_type=response.get("token_type", "Bearer"),
            expires_in=response.get("expires_in", 3600),
            scope=response.get("scope"),
        )

    def refresh_token(self, refresh_token: str) -> OAuthTokenResult:
        """
        Refresh access token.

        Args:
            refresh_token: Refresh token from previous exchange

        Returns:
            OAuthTokenResult with new tokens
        """
        response = self._client.post(
            "/v1/bb/oauth/refresh",
            json={"refresh_token": refresh_token},
        )

        return OAuthTokenResult(
            access_token=response.get("access_token", ""),
            refresh_token=response.get("refresh_token"),
            token_type=response.get("token_type", "Bearer"),
            expires_in=response.get("expires_in", 3600),
            scope=response.get("scope"),
        )

    def get_userinfo(self, access_token: str) -> OAuthUserInfo:
        """
        Get user info from BB.

        Args:
            access_token: User's BB access token

        Returns:
            OAuthUserInfo with sub, cpf, nome
        """
        response = self._client.get(
            "/v1/bb/oauth/userinfo",
            params={"access_token": access_token},
        )

        return OAuthUserInfo(
            sub=response.get("sub", ""),
            cpf=response.get("cpf"),
            nome=response.get("nome"),
        )

    # =========================================================================
    # PIX
    # =========================================================================

    def create_pix_charge(
        self,
        amount: Decimal,
        description: str,
        expiration_seconds: int = 3600,
        payer_cpf: str | None = None,
        payer_name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> PixChargeResult:
        """
        Create a PIX charge.

        Args:
            amount: Amount in BRL
            description: Payment description
            expiration_seconds: Expiration time (default 1 hour)
            payer_cpf: Optional payer CPF
            payer_name: Optional payer name
            metadata: Custom metadata

        Returns:
            PixChargeResult with txid, qr_code, etc.
        """
        payload = {
            "amount": str(amount),
            "description": description,
            "expiration_seconds": expiration_seconds,
        }

        if payer_cpf:
            payload["payer_cpf"] = payer_cpf
        if payer_name:
            payload["payer_name"] = payer_name
        if metadata:
            payload["metadata"] = metadata

        response = self._client.post("/v1/bb/pix/charge", json=payload)

        return PixChargeResult(
            txid=response.get("txid", ""),
            status=response.get("status", ""),
            qr_code=response.get("qr_code", ""),
            qr_code_base64=response.get("qr_code_base64"),
            amount=Decimal(str(response.get("amount", 0))),
            expires_at=response.get("expires_at", ""),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    def get_pix_status(self, txid: str) -> PixStatusResult:
        """
        Get PIX charge status.

        Args:
            txid: Transaction ID

        Returns:
            PixStatusResult with status, e2eid if paid, etc.
        """
        response = self._client.get(f"/v1/bb/pix/charge/{txid}")

        return PixStatusResult(
            txid=response.get("txid", txid),
            status=response.get("status", ""),
            amount=Decimal(str(response.get("amount", 0))),
            e2eid=response.get("e2eid"),
            paid_at=response.get("paid_at"),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    def cancel_pix_charge(self, txid: str) -> dict[str, Any]:
        """
        Cancel a PIX charge.

        Args:
            txid: Transaction ID to cancel

        Returns:
            Cancellation result
        """
        return self._client.request("DELETE", f"/v1/bb/pix/charge/{txid}")

    def health(self) -> dict[str, Any]:
        """
        Check BB API health.

        Returns:
            Health status with environment info
        """
        return self._client.get("/v1/bb/health")
