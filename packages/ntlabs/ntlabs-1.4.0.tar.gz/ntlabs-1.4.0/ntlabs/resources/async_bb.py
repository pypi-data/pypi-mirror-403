"""
Neural LAB - AI Solutions Platform
Async Banco do Brasil Resource.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-25
"""

from decimal import Decimal
from typing import Any

from .bb import (
    OAuthAuthorizeResult,
    OAuthTokenResult,
    OAuthUserInfo,
    PixChargeResult,
    PixStatusResult,
)


class AsyncBBResource:
    """Async Banco do Brasil resource for OAuth and PIX operations."""

    def __init__(self, client):
        self._client = client

    # =========================================================================
    # OAuth
    # =========================================================================

    async def get_authorize_url(
        self,
        redirect_uri: str,
        scope: str = "openid-otp cpf",
    ) -> OAuthAuthorizeResult:
        """Get BB OAuth authorization URL."""
        response = await self._client.post(
            "/v1/bb/oauth/authorize",
            json={"redirect_uri": redirect_uri, "scope": scope},
        )
        return OAuthAuthorizeResult(
            authorize_url=response.get("authorize_url", ""),
            state=response.get("state", ""),
        )

    async def exchange_code(
        self,
        code: str,
        state: str,
        redirect_uri: str,
    ) -> OAuthTokenResult:
        """Exchange authorization code for tokens."""
        response = await self._client.post(
            "/v1/bb/oauth/callback",
            json={"code": code, "state": state, "redirect_uri": redirect_uri},
        )
        return OAuthTokenResult(
            access_token=response.get("access_token", ""),
            refresh_token=response.get("refresh_token"),
            token_type=response.get("token_type", "Bearer"),
            expires_in=response.get("expires_in", 3600),
            scope=response.get("scope"),
        )

    async def refresh_token(self, refresh_token: str) -> OAuthTokenResult:
        """Refresh access token."""
        response = await self._client.post(
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

    async def get_userinfo(self, access_token: str) -> OAuthUserInfo:
        """Get user info from BB."""
        response = await self._client.get(
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

    async def create_pix_charge(
        self,
        amount: Decimal,
        description: str,
        expiration_seconds: int = 3600,
        payer_cpf: str | None = None,
        payer_name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> PixChargeResult:
        """Create a PIX charge."""
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

        response = await self._client.post("/v1/bb/pix/charge", json=payload)

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

    async def get_pix_status(self, txid: str) -> PixStatusResult:
        """Get PIX charge status."""
        response = await self._client.get(f"/v1/bb/pix/charge/{txid}")
        return PixStatusResult(
            txid=response.get("txid", txid),
            status=response.get("status", ""),
            amount=Decimal(str(response.get("amount", 0))),
            e2eid=response.get("e2eid"),
            paid_at=response.get("paid_at"),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    async def cancel_pix_charge(self, txid: str) -> dict[str, Any]:
        """Cancel a PIX charge."""
        return await self._client.request("DELETE", f"/v1/bb/pix/charge/{txid}")

    async def health(self) -> dict[str, Any]:
        """Check BB API health."""
        return await self._client.get("/v1/bb/health")
