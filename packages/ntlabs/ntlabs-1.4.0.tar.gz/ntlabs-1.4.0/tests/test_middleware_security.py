"""
Comprehensive tests for ntlabs.middleware.security module.

Tests security headers middleware for FastAPI.
"""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from ntlabs.middleware.security import (
    SecurityHeadersMiddleware,
    SecurityPresets,
    get_default_csp,
)


# =============================================================================
# Security Headers Middleware Initialization Tests
# =============================================================================


class TestSecurityHeadersMiddlewareInit:
    """Tests for SecurityHeadersMiddleware initialization."""

    def test_middleware_init_defaults(self):
        """Test middleware initialization with defaults."""

        class MockApp:
            pass

        middleware = SecurityHeadersMiddleware(app=MockApp())
        assert middleware.app is not None
        assert len(middleware.headers) > 0

    def test_middleware_init_default_headers(self):
        """Test default security headers are set."""

        class MockApp:
            pass

        middleware = SecurityHeadersMiddleware(app=MockApp())

        assert "X-Content-Type-Options" in middleware.headers
        assert "X-Frame-Options" in middleware.headers
        assert "X-XSS-Protection" in middleware.headers
        assert "Strict-Transport-Security" in middleware.headers
        assert "Referrer-Policy" in middleware.headers

        assert middleware.headers["X-Content-Type-Options"] == "nosniff"
        assert middleware.headers["X-Frame-Options"] == "DENY"
        assert middleware.headers["X-XSS-Protection"] == "1; mode=block"

    def test_middleware_init_custom_values(self):
        """Test middleware with custom header values."""

        class MockApp:
            pass

        middleware = SecurityHeadersMiddleware(
            app=MockApp(),
            x_content_type_options="custom",
            x_frame_options="SAMEORIGIN",
            x_xss_protection="0",
        )

        assert middleware.headers["X-Content-Type-Options"] == "custom"
        assert middleware.headers["X-Frame-Options"] == "SAMEORIGIN"
        assert middleware.headers["X-XSS-Protection"] == "0"

    def test_middleware_init_no_hsts(self):
        """Test middleware with HSTS disabled."""

        class MockApp:
            pass

        middleware = SecurityHeadersMiddleware(
            app=MockApp(),
            enable_hsts=False,
        )

        assert "Strict-Transport-Security" not in middleware.headers

    def test_middleware_init_custom_csp(self):
        """Test middleware with custom CSP."""

        class MockApp:
            pass

        custom_csp = "default-src 'self'; script-src 'self' 'unsafe-inline'"
        middleware = SecurityHeadersMiddleware(
            app=MockApp(),
            content_security_policy=custom_csp,
        )

        assert middleware.headers["Content-Security-Policy"] == custom_csp

    def test_middleware_init_custom_headers(self):
        """Test middleware with custom headers."""

        class MockApp:
            pass

        middleware = SecurityHeadersMiddleware(
            app=MockApp(),
            custom_headers={"X-Custom-Header": "custom-value"},
        )

        assert middleware.headers["X-Custom-Header"] == "custom-value"

    def test_middleware_init_exclude_paths(self):
        """Test middleware with excluded paths."""

        class MockApp:
            pass

        middleware = SecurityHeadersMiddleware(
            app=MockApp(),
            exclude_paths=["/health", "/metrics"],
        )

        assert "/health" in middleware.exclude_paths
        assert "/metrics" in middleware.exclude_paths


# =============================================================================
# Middleware Call Tests
# =============================================================================


class TestSecurityHeadersMiddlewareCall:
    """Tests for SecurityHeadersMiddleware __call__ method."""

    @pytest.mark.asyncio
    async def test_call_non_http_scope(self):
        """Test middleware ignores non-HTTP scopes."""

        class MockApp:
            async def __call__(self, scope, receive, send):
                await send({"type": "websocket.accept"})

        middleware = SecurityHeadersMiddleware(app=MockApp())
        scope = {"type": "websocket"}
        receive = AsyncMock()
        send = AsyncMock()

        await middleware(scope, receive, send)
        send.assert_called()

    @pytest.mark.asyncio
    async def test_call_excluded_path(self):
        """Test middleware skips excluded paths."""

        class MockApp:
            async def __call__(self, scope, receive, send):
                await send({"type": "http.response.start", "status": 200})

        middleware = SecurityHeadersMiddleware(
            app=MockApp(),
            exclude_paths=["/health"],
        )
        scope = {"type": "http", "path": "/health"}
        receive = AsyncMock()
        send = AsyncMock()

        await middleware(scope, receive, send)

    @pytest.mark.asyncio
    async def test_call_adds_headers(self):
        """Test middleware adds security headers."""

        class MockApp:
            async def __call__(self, scope, receive, send):
                await send({
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [],
                })

        middleware = SecurityHeadersMiddleware(app=MockApp())
        scope = {"type": "http", "path": "/api/test"}
        receive = AsyncMock()

        captured_headers = None

        async def capture_send(message):
            nonlocal captured_headers
            if message["type"] == "http.response.start":
                captured_headers = message.get("headers", [])

        await middleware(scope, receive, capture_send)

        # Check headers were added
        header_dict = {h[0].decode(): h[1].decode() for h in captured_headers or []}
        assert "X-Content-Type-Options" in header_dict
        assert "X-Frame-Options" in header_dict

    @pytest.mark.asyncio
    async def test_call_preserves_existing_headers(self):
        """Test middleware preserves existing headers."""

        class MockApp:
            async def __call__(self, scope, receive, send):
                await send({
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [(b"X-Existing", b"existing-value")],
                })

        middleware = SecurityHeadersMiddleware(app=MockApp())
        scope = {"type": "http", "path": "/api/test"}
        receive = AsyncMock()

        captured_headers = None

        async def capture_send(message):
            nonlocal captured_headers
            if message["type"] == "http.response.start":
                captured_headers = message.get("headers", [])

        await middleware(scope, receive, capture_send)

        # Check existing headers were preserved
        header_dict = {h[0].decode(): h[1].decode() for h in captured_headers or []}
        assert "X-Existing" in header_dict
        assert header_dict["X-Existing"] == "existing-value"
        assert "X-Content-Type-Options" in header_dict


# =============================================================================
# Get Default CSP Tests
# =============================================================================


class TestGetDefaultCSP:
    """Tests for get_default_csp function."""

    def test_default_csp_basic(self):
        """Test basic CSP generation."""
        csp = get_default_csp()

        assert "default-src 'self'" in csp
        assert "script-src 'self'" in csp
        assert "style-src 'self'" in csp
        assert "frame-ancestors" in csp
        assert "upgrade-insecure-requests" in csp

    def test_csp_custom_script_src(self):
        """Test CSP with custom script sources."""
        csp = get_default_csp(
            script_src=["'self'", "https://cdn.example.com"],
        )

        assert "script-src 'self' https://cdn.example.com" in csp

    def test_csp_custom_style_src(self):
        """Test CSP with custom style sources."""
        csp = get_default_csp(
            style_src=["'self'", "https://fonts.example.com"],
        )

        assert "style-src 'self' https://fonts.example.com" in csp

    def test_csp_custom_img_src(self):
        """Test CSP with custom image sources."""
        csp = get_default_csp(
            img_src=["'self'", "https://images.example.com"],
        )

        assert "img-src 'self' https://images.example.com" in csp

    def test_csp_custom_connect_src(self):
        """Test CSP with custom connect sources."""
        csp = get_default_csp(
            connect_src=["'self'", "https://api.example.com"],
        )

        assert "connect-src 'self' https://api.example.com" in csp

    def test_csp_custom_frame_ancestors(self):
        """Test CSP with custom frame ancestors."""
        csp = get_default_csp(
            frame_ancestors="'self'",
        )

        assert "frame-ancestors 'self'" in csp

    def test_csp_no_upgrade_insecure(self):
        """Test CSP without upgrade insecure requests."""
        csp = get_default_csp(
            upgrade_insecure_requests=False,
        )

        assert "upgrade-insecure-requests" not in csp


# =============================================================================
# Security Presets Tests
# =============================================================================


class TestSecurityPresets:
    """Tests for SecurityPresets class."""

    def test_strict_preset(self):
        """Test strict security preset."""
        mock_app = MagicMock()

        SecurityPresets.strict(mock_app)

        mock_app.add_middleware.assert_called_once()

    def test_api_preset(self):
        """Test API security preset."""
        mock_app = MagicMock()

        SecurityPresets.api(mock_app)

        mock_app.add_middleware.assert_called_once()

    def test_web_app_preset(self):
        """Test web app security preset."""
        mock_app = MagicMock()

        SecurityPresets.web_app(mock_app)

        mock_app.add_middleware.assert_called_once()

    def test_web_app_preset_with_cdn(self):
        """Test web app preset with CDN origins."""
        mock_app = MagicMock()
        cdn_origins = ["https://cdn.example.com"]

        SecurityPresets.web_app(mock_app, cdn_origins=cdn_origins)

        mock_app.add_middleware.assert_called_once()

    def test_development_preset(self):
        """Test development security preset."""
        mock_app = MagicMock()

        SecurityPresets.development(mock_app)

        mock_app.add_middleware.assert_called_once()


# =============================================================================
# Header Value Tests
# =============================================================================


class TestHeaderValues:
    """Tests for specific header values."""

    def test_x_content_type_options_values(self):
        """Test common X-Content-Type-Options values."""

        class MockApp:
            pass

        # nosniff
        middleware = SecurityHeadersMiddleware(
            app=MockApp(),
            x_content_type_options="nosniff",
        )
        assert middleware.headers["X-Content-Type-Options"] == "nosniff"

    def test_x_frame_options_values(self):
        """Test X-Frame-Options values."""

        class MockApp:
            pass

        # DENY
        middleware1 = SecurityHeadersMiddleware(
            app=MockApp(),
            x_frame_options="DENY",
        )
        assert middleware1.headers["X-Frame-Options"] == "DENY"

        # SAMEORIGIN
        middleware2 = SecurityHeadersMiddleware(
            app=MockApp(),
            x_frame_options="SAMEORIGIN",
        )
        assert middleware2.headers["X-Frame-Options"] == "SAMEORIGIN"

    def test_x_xss_protection_values(self):
        """Test X-XSS-Protection values."""

        class MockApp:
            pass

        # Default
        middleware1 = SecurityHeadersMiddleware(app=MockApp())
        assert middleware1.headers["X-XSS-Protection"] == "1; mode=block"

        # Disabled
        middleware2 = SecurityHeadersMiddleware(
            app=MockApp(),
            x_xss_protection="0",
        )
        assert middleware2.headers["X-XSS-Protection"] == "0"

    def test_hsts_values(self):
        """Test HSTS header values."""

        class MockApp:
            pass

        # Default
        middleware1 = SecurityHeadersMiddleware(app=MockApp())
        assert "max-age=31536000" in middleware1.headers["Strict-Transport-Security"]

        # Custom
        middleware2 = SecurityHeadersMiddleware(
            app=MockApp(),
            strict_transport_security="max-age=86400",
        )
        assert middleware2.headers["Strict-Transport-Security"] == "max-age=86400"

    def test_referrer_policy_values(self):
        """Test Referrer-Policy values."""

        class MockApp:
            pass

        # Default
        middleware1 = SecurityHeadersMiddleware(app=MockApp())
        assert middleware1.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

        # Custom values
        for value in [
            "no-referrer",
            "no-referrer-when-downgrade",
            "origin",
            "origin-when-cross-origin",
            "same-origin",
            "strict-origin",
            "unsafe-url",
        ]:
            middleware = SecurityHeadersMiddleware(
                app=MockApp(),
                referrer_policy=value,
            )
            assert middleware.headers["Referrer-Policy"] == value


# =============================================================================
# Integration Tests
# =============================================================================


class TestSecurityIntegration:
    """Integration tests for security middleware."""

    @pytest.mark.asyncio
    async def test_full_security_headers(self):
        """Test all security headers are added."""

        class MockApp:
            async def __call__(self, scope, receive, send):
                await send({
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [],
                })

        middleware = SecurityHeadersMiddleware(
            app=MockApp(),
            content_security_policy="default-src 'self'",
            permissions_policy="camera=()",
        )
        scope = {"type": "http", "path": "/api/test"}
        receive = AsyncMock()

        captured_headers = None

        async def capture_send(message):
            nonlocal captured_headers
            if message["type"] == "http.response.start":
                captured_headers = message.get("headers", [])

        await middleware(scope, receive, capture_send)

        header_dict = {h[0].decode(): h[1].decode() for h in captured_headers or []}

        # All expected headers should be present
        assert "X-Content-Type-Options" in header_dict
        assert "X-Frame-Options" in header_dict
        assert "X-XSS-Protection" in header_dict
        assert "Strict-Transport-Security" in header_dict
        assert "Content-Security-Policy" in header_dict
        assert "Referrer-Policy" in header_dict
        assert "Permissions-Policy" in header_dict

    def test_multiple_presets_can_be_defined(self):
        """Test that multiple presets can be defined on same app."""
        mock_app = MagicMock()

        # Apply multiple presets
        SecurityPresets.api(mock_app)
        SecurityPresets.development(mock_app)

        # Both should be called
        assert mock_app.add_middleware.call_count == 2
