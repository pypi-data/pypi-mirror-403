"""
Neural LAB SDK - Async Authentication Resource.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-25
"""

from typing import Literal


class AsyncAuthResource:
    """Async authentication resource for Neural LAB API."""

    def __init__(self, client):
        self._client = client

    async def signup(
        self,
        email: str,
        password: str,
        full_name: str | None = None,
    ) -> dict:
        """Register a new user with email/password."""
        return await self._client.post(
            "/api/auth/signup",
            json={
                "email": email,
                "password": password,
                "full_name": full_name,
            },
        )

    async def login(self, email: str, password: str) -> dict:
        """Login with email/password."""
        return await self._client.post(
            "/api/auth/login",
            json={"email": email, "password": password},
        )

    async def get_oauth_url(
        self,
        provider: Literal["github", "google"],
        redirect_uri: str | None = None,
    ) -> dict:
        """Get OAuth login URL for the specified provider."""
        params = {}
        if redirect_uri:
            params["redirect_uri"] = redirect_uri

        return await self._client.get(
            f"/api/auth/login/{provider}",
            params=params if params else None,
        )

    async def exchange_code(self, code: str) -> dict:
        """Exchange OAuth code for tokens."""
        return await self._client.post(
            "/api/auth/exchange",
            json={"code": code},
        )

    async def refresh(self, refresh_token: str) -> dict:
        """Refresh access token using refresh token."""
        return await self._client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )

    async def me(self, access_token: str | None = None) -> dict:
        """Get current authenticated user."""
        headers = {}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        return await self._client.get("/api/auth/me", headers=headers)

    async def validate(self, access_token: str) -> dict:
        """Validate an access token."""
        return await self._client.post(
            "/api/auth/validate",
            json={"token": access_token},
        )

    async def logout(self) -> dict:
        """Logout current user (invalidate session)."""
        return await self._client.post("/api/auth/logout")

    # =========================================================================
    # OAuth v2 Methods (Secure flow with PKCE)
    # =========================================================================

    async def initiate_oauth_v2(
        self,
        provider: Literal["github", "google"],
        redirect_uri: str,
        product: Literal["lab", "hipocrates", "mercurius", "argos", "polis"] = "lab",
    ) -> dict:
        """Initiate OAuth v2 flow with PKCE (secure)."""
        return await self._client.post(
            f"/api/v2/auth/initiate/{provider}",
            json={
                "redirect_uri": redirect_uri,
                "product": product,
            },
        )

    async def claim_session(self, session_id: str, signature: str) -> dict:
        """Claim a pending session after OAuth callback."""
        return await self._client.post(
            "/api/v2/auth/session/claim",
            json={
                "session_id": session_id,
                "signature": signature,
            },
        )

    async def validate_session(
        self,
        session_id: str | None = None,
        access_token: str | None = None,
        product: Literal["lab", "hipocrates", "mercurius", "argos", "polis"] = "lab",
    ) -> dict:
        """Validate a session or token via Gateway."""
        return await self._client.post(
            "/api/v2/auth/validate",
            json={
                "session_id": session_id,
                "access_token": access_token,
                "product": product,
            },
        )

    async def refresh_v2(
        self,
        refresh_token: str,
        session_id: str | None = None,
    ) -> dict:
        """Refresh tokens using OAuth v2 endpoint."""
        return await self._client.post(
            "/api/v2/auth/refresh",
            json={
                "refresh_token": refresh_token,
                "session_id": session_id,
            },
        )

    async def revoke_session(
        self,
        session_id: str | None = None,
        revoke_all: bool = False,
        reason: str | None = None,
    ) -> dict:
        """Revoke session(s) for logout."""
        return await self._client.post(
            "/api/v2/auth/revoke",
            json={
                "session_id": session_id,
                "revoke_all": revoke_all,
                "reason": reason,
            },
        )

    async def check_sso(
        self,
        product: Literal["lab", "hipocrates", "mercurius", "argos", "polis"] = "lab",
    ) -> dict:
        """Check if user has valid SSO session."""
        return await self._client.get(
            "/api/v2/auth/sso/check",
            params={"product": product},
        )

    async def create_sso_ticket(
        self,
        target_product: Literal["lab", "hipocrates", "mercurius", "argos", "polis"],
    ) -> dict:
        """Create SSO ticket for cross-product navigation."""
        return await self._client.post(
            "/api/v2/auth/sso/create-ticket",
            params={"target_product": target_product},
        )

    async def exchange_sso_ticket(
        self,
        ticket: str,
        target_product: Literal["lab", "hipocrates", "mercurius", "argos", "polis"],
    ) -> dict:
        """Exchange SSO ticket for session in target product."""
        return await self._client.post(
            "/api/v2/auth/sso/exchange-ticket",
            json={
                "ticket": ticket,
                "target_product": target_product,
            },
        )
