"""
Neural LAB SDK - Authentication Resource.
OAuth and token management via Neural LAB Gateway.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-24
"""

from typing import Literal


class AuthResource:
    """
    Authentication resource for Neural LAB API.

    Provides centralized OAuth login via Neural LAB Gateway.
    Products (Hipocrates, Mercurius, Polis) can delegate auth to the gateway.

    Usage:
        client = NeuralLabClient(api_key="nl_xxx")

        # Get OAuth URL for GitHub/Google login
        oauth = client.auth.get_oauth_url("github")
        # Redirect user to: oauth["url"]

        # Exchange code for tokens (after callback)
        tokens = client.auth.exchange_code(code)

        # Refresh tokens
        new_tokens = client.auth.refresh(refresh_token)

        # Get current user
        user = client.auth.me(access_token)

        # Validate token
        is_valid = client.auth.validate(access_token)
    """

    def __init__(self, client):
        self._client = client

    def signup(
        self,
        email: str,
        password: str,
        full_name: str | None = None,
    ) -> dict:
        """
        Register a new user with email/password.

        Args:
            email: User email address
            password: User password (min 6 characters)
            full_name: Optional full name

        Returns:
            {
                "access_token": "...",
                "refresh_token": "...",
                "expires_in": 3600,
                "user": {...}
            }
        """
        return self._client.post(
            "/api/auth/signup",
            json={
                "email": email,
                "password": password,
                "full_name": full_name,
            },
        )

    def login(self, email: str, password: str) -> dict:
        """
        Login with email/password.

        Args:
            email: User email
            password: User password

        Returns:
            {
                "access_token": "...",
                "refresh_token": "...",
                "expires_in": 3600,
                "user": {...}
            }
        """
        return self._client.post(
            "/api/auth/login",
            json={"email": email, "password": password},
        )

    def get_oauth_url(
        self,
        provider: Literal["github", "google"],
        redirect_uri: str | None = None,
    ) -> dict:
        """
        Get OAuth login URL for the specified provider.

        Args:
            provider: OAuth provider ("github" or "google")
            redirect_uri: Optional custom redirect URI after auth

        Returns:
            {
                "url": "https://github.com/login/oauth/...",
                "provider": "github"
            }
        """
        params = {}
        if redirect_uri:
            params["redirect_uri"] = redirect_uri

        return self._client.get(
            f"/api/auth/login/{provider}",
            params=params if params else None,
        )

    def exchange_code(self, code: str) -> dict:
        """
        Exchange OAuth code for tokens.

        This is typically called by the OAuth callback endpoint.

        Args:
            code: OAuth authorization code from provider callback

        Returns:
            {
                "access_token": "...",
                "refresh_token": "...",
                "expires_in": 3600,
                "user": {...}
            }
        """
        return self._client.post(
            "/api/auth/exchange",
            json={"code": code},
        )

    def refresh(self, refresh_token: str) -> dict:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            {
                "access_token": "...",
                "refresh_token": "...",
                "expires_in": 3600,
                "user": {...}
            }
        """
        return self._client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )

    def me(self, access_token: str | None = None) -> dict:
        """
        Get current authenticated user.

        Args:
            access_token: Optional access token (uses client token if not provided)

        Returns:
            {
                "id": "uuid",
                "email": "user@example.com",
                "full_name": "John Doe",
                "avatar_url": "https://...",
                "provider": "github",
                "role": "user"
            }
        """
        headers = {}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        return self._client.get("/api/auth/me", headers=headers)

    def validate(self, access_token: str) -> dict:
        """
        Validate an access token.

        Args:
            access_token: Token to validate

        Returns:
            {
                "valid": true,
                "user_id": "uuid",
                "expires_at": "2026-01-25T00:00:00Z"
            }
        """
        return self._client.post(
            "/api/auth/validate",
            json={"token": access_token},
        )

    def logout(self) -> dict:
        """
        Logout current user (invalidate session).

        Returns:
            {"message": "Logged out successfully"}
        """
        return self._client.post("/api/auth/logout")

    # =========================================================================
    # OAuth v2 Methods (Secure flow with PKCE)
    # =========================================================================

    def initiate_oauth_v2(
        self,
        provider: Literal["github", "google"],
        redirect_uri: str,
        product: Literal["lab", "hipocrates", "mercurius", "argos", "polis"] = "lab",
    ) -> dict:
        """
        Initiate OAuth v2 flow with PKCE (secure).

        This is the recommended method for OAuth. Returns authorization URL
        and state token. Tokens are NEVER exposed in URLs.

        Args:
            provider: OAuth provider ("github" or "google")
            redirect_uri: Frontend callback URL after auth
            product: Product initiating the OAuth flow

        Returns:
            {
                "authorization_url": "https://github.com/login/oauth/...",
                "state": "abc123...",
                "provider": "github",
                "expires_in": 600
            }
        """
        return self._client.post(
            f"/api/v2/auth/initiate/{provider}",
            json={
                "redirect_uri": redirect_uri,
                "product": product,
            },
        )

    def claim_session(self, session_id: str, signature: str) -> dict:
        """
        Claim a pending session after OAuth callback.

        After OAuth callback, the frontend receives session_id and signature
        in the URL (not tokens). Call this method to exchange them for actual tokens.

        Args:
            session_id: Temporary session ID from callback
            signature: HMAC signature from callback

        Returns:
            {
                "access_token": "...",
                "refresh_token": "...",
                "expires_in": 1800,
                "session_id": "permanent_session_id",
                "user": {...}
            }
        """
        return self._client.post(
            "/api/v2/auth/session/claim",
            json={
                "session_id": session_id,
                "signature": signature,
            },
        )

    def validate_session(
        self,
        session_id: str | None = None,
        access_token: str | None = None,
        product: Literal["lab", "hipocrates", "mercurius", "argos", "polis"] = "lab",
    ) -> dict:
        """
        Validate a session or token via Gateway.

        Can validate by session_id (from SSO cookie) or access_token.
        Records product access for SSO tracking.

        Args:
            session_id: Session ID to validate (from cookie)
            access_token: Access token to validate
            product: Product requesting validation

        Returns:
            {
                "valid": true,
                "user": {...},
                "session_id": "...",
                "expires_at": "2026-02-01T00:00:00Z",
                "products_accessed": ["lab", "hipocrates"]
            }
        """
        return self._client.post(
            "/api/v2/auth/validate",
            json={
                "session_id": session_id,
                "access_token": access_token,
                "product": product,
            },
        )

    def refresh_v2(
        self,
        refresh_token: str,
        session_id: str | None = None,
    ) -> dict:
        """
        Refresh tokens using OAuth v2 endpoint.

        Implements refresh token rotation for security.

        Args:
            refresh_token: Current refresh token
            session_id: Optional session ID for tracking

        Returns:
            {
                "access_token": "...",
                "refresh_token": "...",  # New refresh token
                "expires_in": 1800
            }
        """
        return self._client.post(
            "/api/v2/auth/refresh",
            json={
                "refresh_token": refresh_token,
                "session_id": session_id,
            },
        )

    def revoke_session(
        self,
        session_id: str | None = None,
        revoke_all: bool = False,
        reason: str | None = None,
    ) -> dict:
        """
        Revoke session(s) for logout.

        Args:
            session_id: Specific session to revoke
            revoke_all: If True, revoke ALL user sessions (global logout)
            reason: Optional reason for revocation

        Returns:
            {
                "success": true,
                "sessions_revoked": 1,
                "message": "Session revoked"
            }
        """
        return self._client.post(
            "/api/v2/auth/revoke",
            json={
                "session_id": session_id,
                "revoke_all": revoke_all,
                "reason": reason,
            },
        )

    def check_sso(
        self,
        product: Literal["lab", "hipocrates", "mercurius", "argos", "polis"] = "lab",
    ) -> dict:
        """
        Check if user has valid SSO session.

        Used by products to check if user is already authenticated
        via shared session before showing login page.

        Args:
            product: Product checking SSO

        Returns:
            {
                "has_valid_session": true,
                "user": {...},
                "session_id": "...",
                "origin_product": "lab",
                "products_accessed": ["lab", "hipocrates"]
            }
        """
        return self._client.get(
            "/api/v2/auth/sso/check",
            params={"product": product},
        )

    def create_sso_ticket(
        self,
        target_product: Literal["lab", "hipocrates", "mercurius", "argos", "polis"],
    ) -> dict:
        """
        Create SSO ticket for cross-product navigation.

        Used when navigating between products that can't share cookies.

        Args:
            target_product: Product the user wants to access

        Returns:
            {
                "ticket": "abc123...",
                "expires_in": 60,
                "target_product": "hipocrates"
            }
        """
        return self._client.post(
            "/api/v2/auth/sso/create-ticket",
            params={"target_product": target_product},
        )

    def exchange_sso_ticket(
        self,
        ticket: str,
        target_product: Literal["lab", "hipocrates", "mercurius", "argos", "polis"],
    ) -> dict:
        """
        Exchange SSO ticket for session in target product.

        Args:
            ticket: SSO ticket from create_sso_ticket
            target_product: Product the user wants to access

        Returns:
            {
                "access_token": "...",
                "refresh_token": "...",
                "session_id": "...",
                "user": {...}
            }
        """
        return self._client.post(
            "/api/v2/auth/sso/exchange-ticket",
            json={
                "ticket": ticket,
                "target_product": target_product,
            },
        )
