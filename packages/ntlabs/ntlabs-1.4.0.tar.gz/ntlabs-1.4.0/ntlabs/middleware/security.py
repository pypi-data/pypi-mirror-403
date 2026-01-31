"""
Security headers middleware for FastAPI.

Adds security-related HTTP headers to responses.
"""

import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to responses.

    Adds headers recommended by OWASP:
    - X-Content-Type-Options
    - X-Frame-Options
    - X-XSS-Protection
    - Strict-Transport-Security
    - Content-Security-Policy
    - Referrer-Policy
    - Permissions-Policy

    Example:
        from fastapi import FastAPI
        from ntlabs.middleware import SecurityHeadersMiddleware

        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)

        # With custom CSP
        app.add_middleware(
            SecurityHeadersMiddleware,
            content_security_policy="default-src 'self'; script-src 'self' 'unsafe-inline'",
        )
    """

    def __init__(
        self,
        app,
        # Header values
        x_content_type_options: str = "nosniff",
        x_frame_options: str = "DENY",
        x_xss_protection: str = "1; mode=block",
        strict_transport_security: str | None = "max-age=31536000; includeSubDomains",
        content_security_policy: str | None = None,
        referrer_policy: str = "strict-origin-when-cross-origin",
        permissions_policy: str | None = None,
        # Options
        exclude_paths: list[str] | None = None,
        enable_hsts: bool = True,
        custom_headers: dict[str, str] | None = None,
    ):
        """
        Initialize security headers middleware.

        Args:
            app: ASGI application
            x_content_type_options: X-Content-Type-Options header value
            x_frame_options: X-Frame-Options header value (DENY, SAMEORIGIN)
            x_xss_protection: X-XSS-Protection header value
            strict_transport_security: HSTS header value
            content_security_policy: CSP header value
            referrer_policy: Referrer-Policy header value
            permissions_policy: Permissions-Policy header value
            exclude_paths: Paths to exclude from header injection
            enable_hsts: Enable HSTS header (disable for non-HTTPS)
            custom_headers: Additional custom headers to add
        """
        self.app = app
        self.exclude_paths = exclude_paths or []
        self.enable_hsts = enable_hsts

        # Build headers dict
        self.headers: dict[str, str] = {}

        if x_content_type_options:
            self.headers["X-Content-Type-Options"] = x_content_type_options

        if x_frame_options:
            self.headers["X-Frame-Options"] = x_frame_options

        if x_xss_protection:
            self.headers["X-XSS-Protection"] = x_xss_protection

        if enable_hsts and strict_transport_security:
            self.headers["Strict-Transport-Security"] = strict_transport_security

        if content_security_policy:
            self.headers["Content-Security-Policy"] = content_security_policy

        if referrer_policy:
            self.headers["Referrer-Policy"] = referrer_policy

        if permissions_policy:
            self.headers["Permissions-Policy"] = permissions_policy

        if custom_headers:
            self.headers.update(custom_headers)

    async def __call__(self, scope, receive, send):
        """ASGI middleware handler."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")

        # Skip excluded paths
        if any(path.startswith(p) for p in self.exclude_paths):
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                existing_headers = list(message.get("headers", []))

                for key, value in self.headers.items():
                    existing_headers.append((key.encode(), value.encode()))

                message["headers"] = existing_headers

            await send(message)

        await self.app(scope, receive, send_with_headers)


def get_default_csp(
    script_src: list[str] = None,
    style_src: list[str] = None,
    img_src: list[str] = None,
    connect_src: list[str] = None,
    frame_ancestors: str = "'none'",
    upgrade_insecure_requests: bool = True,
) -> str:
    """
    Generate a Content-Security-Policy header value.

    Args:
        script_src: Allowed script sources
        style_src: Allowed style sources
        img_src: Allowed image sources
        connect_src: Allowed connect (XHR/fetch) sources
        frame_ancestors: Allowed frame ancestors
        upgrade_insecure_requests: Upgrade HTTP to HTTPS

    Returns:
        CSP header value string

    Example:
        csp = get_default_csp(
            script_src=["'self'", "https://cdn.example.com"],
            style_src=["'self'", "'unsafe-inline'"],
        )
    """
    directives = []

    # Default-src
    directives.append("default-src 'self'")

    # Script-src
    if script_src:
        directives.append(f"script-src {' '.join(script_src)}")
    else:
        directives.append("script-src 'self'")

    # Style-src
    if style_src:
        directives.append(f"style-src {' '.join(style_src)}")
    else:
        directives.append("style-src 'self' 'unsafe-inline'")

    # Img-src
    if img_src:
        directives.append(f"img-src {' '.join(img_src)}")
    else:
        directives.append("img-src 'self' data: https:")

    # Connect-src
    if connect_src:
        directives.append(f"connect-src {' '.join(connect_src)}")
    else:
        directives.append("connect-src 'self'")

    # Frame-ancestors
    directives.append(f"frame-ancestors {frame_ancestors}")

    # Upgrade insecure requests
    if upgrade_insecure_requests:
        directives.append("upgrade-insecure-requests")

    return "; ".join(directives)


# Pre-configured security presets
class SecurityPresets:
    """Pre-configured security header presets."""

    @staticmethod
    def strict(app):
        """Strict security headers (recommended for APIs)."""
        app.add_middleware(
            SecurityHeadersMiddleware,
            x_frame_options="DENY",
            content_security_policy="default-src 'none'; frame-ancestors 'none'",
        )

    @staticmethod
    def api(app):
        """Security headers for API servers."""
        app.add_middleware(
            SecurityHeadersMiddleware,
            x_frame_options="DENY",
            # APIs typically don't serve HTML, so minimal CSP
            content_security_policy="default-src 'none'",
        )

    @staticmethod
    def web_app(app, cdn_origins: list[str] = None):
        """Security headers for web applications."""
        csp = get_default_csp(
            script_src=["'self'"] + (cdn_origins or []),
            style_src=["'self'", "'unsafe-inline'"] + (cdn_origins or []),
            img_src=["'self'", "data:", "https:"],
            connect_src=["'self'"] + (cdn_origins or []),
        )
        app.add_middleware(
            SecurityHeadersMiddleware,
            x_frame_options="SAMEORIGIN",
            content_security_policy=csp,
        )

    @staticmethod
    def development(app):
        """Relaxed headers for development (NOT for production)."""
        app.add_middleware(
            SecurityHeadersMiddleware,
            enable_hsts=False,  # Don't enforce HTTPS in dev
            content_security_policy=None,  # No CSP in dev
        )
