"""
Tests for ntlabs.middleware module.

Tests rate limiting, CORS, security headers, and logging middleware.
Note: Rate limiting tests require Redis instance.
"""

from ntlabs.middleware import (
    DEFAULT_TIER_CONFIG,
    CORSPresets,
    EndpointConfig,
    # Logging
    LoggingMiddleware,
    # Rate Limiting
    RateLimitMiddleware,
    RateLimitTier,
    # Security
    SecurityHeadersMiddleware,
    SecurityPresets,
    TierConfig,
    # CORS
    get_cors_origins_from_env,
    get_default_csp,
    rate_limit,
)

# =============================================================================
# Rate Limit Tier Tests
# =============================================================================


class TestRateLimitTiers:
    """Tests for rate limit tiers."""

    def test_tier_enum_values(self):
        """Test RateLimitTier enum values."""
        assert RateLimitTier.FREE.value == "free"
        assert RateLimitTier.BASIC.value == "basic"
        assert RateLimitTier.PRO.value == "pro"
        assert RateLimitTier.ENTERPRISE.value == "enterprise"
        assert RateLimitTier.UNLIMITED.value == "unlimited"

    def test_tier_config_defaults(self):
        """Test TierConfig defaults."""
        config = TierConfig()
        assert config.per_minute == 60
        assert config.per_hour == 1000
        assert config.per_day == 10000
        assert config.burst_limit == 10

    def test_tier_config_custom(self):
        """Test TierConfig custom values."""
        config = TierConfig(
            per_minute=120,
            per_hour=5000,
            per_day=50000,
            burst_limit=20,
        )
        assert config.per_minute == 120
        assert config.per_hour == 5000

    def test_default_tier_config_exists(self):
        """Test all tiers have default config."""
        for tier in RateLimitTier:
            assert tier in DEFAULT_TIER_CONFIG

    def test_default_tier_config_ordering(self):
        """Test tier limits increase with tier level."""
        free = DEFAULT_TIER_CONFIG[RateLimitTier.FREE]
        basic = DEFAULT_TIER_CONFIG[RateLimitTier.BASIC]
        pro = DEFAULT_TIER_CONFIG[RateLimitTier.PRO]
        enterprise = DEFAULT_TIER_CONFIG[RateLimitTier.ENTERPRISE]

        assert free.per_minute < basic.per_minute
        assert basic.per_minute < pro.per_minute
        assert pro.per_minute < enterprise.per_minute


class TestEndpointConfig:
    """Tests for endpoint-specific rate limit config."""

    def test_endpoint_config_defaults(self):
        """Test EndpointConfig defaults."""
        config = EndpointConfig()
        assert config.per_minute == 60
        assert config.cost == 1

    def test_endpoint_config_custom(self):
        """Test EndpointConfig custom values."""
        config = EndpointConfig(per_minute=10, cost=5)
        assert config.per_minute == 10
        assert config.cost == 5


# =============================================================================
# Rate Limit Middleware Tests (Mock)
# =============================================================================


class TestRateLimitMiddleware:
    """Tests for RateLimitMiddleware (without Redis)."""

    def test_middleware_initialization(self):
        """Test middleware initialization."""

        # Mock app
        class MockApp:
            pass

        middleware = RateLimitMiddleware(
            app=MockApp(),
            redis_url="redis://localhost:6379",
            default_tier=RateLimitTier.BASIC,
        )

        assert middleware.default_tier == RateLimitTier.BASIC
        assert "/health" in middleware.exclude_paths

    def test_middleware_custom_tier_config(self):
        """Test middleware with custom tier config."""

        class MockApp:
            pass

        middleware = RateLimitMiddleware(
            app=MockApp(),
            redis_url="redis://localhost:6379",
            tier_config={
                RateLimitTier.PRO: {"per_minute": 200},
            },
        )

        # Check that PRO tier was updated
        pro_config = middleware._tier_config[RateLimitTier.PRO]
        assert pro_config.per_minute == 200

    def test_middleware_endpoint_config(self):
        """Test middleware with endpoint config."""

        class MockApp:
            pass

        middleware = RateLimitMiddleware(
            app=MockApp(),
            redis_url="redis://localhost:6379",
            endpoint_config={
                "/api/chat": {"per_minute": 20, "cost": 5},
            },
        )

        assert "/api/chat" in middleware._endpoint_config
        config = middleware._endpoint_config["/api/chat"]
        assert config.per_minute == 20
        assert config.cost == 5

    def test_middleware_exclude_paths(self):
        """Test middleware exclude paths."""

        class MockApp:
            pass

        middleware = RateLimitMiddleware(
            app=MockApp(),
            redis_url="redis://localhost:6379",
            exclude_paths=["/health", "/docs", "/custom"],
        )

        assert "/custom" in middleware.exclude_paths


class TestRateLimitDecorator:
    """Tests for rate_limit decorator."""

    def test_decorator_basic(self):
        """Test rate_limit decorator application."""

        @rate_limit(limit=10, window=60)
        async def my_endpoint():
            return {"data": "result"}

        # Decorator should wrap the function
        assert callable(my_endpoint)


# =============================================================================
# CORS Tests
# =============================================================================


class TestCORSConfig:
    """Tests for CORS configuration."""

    def test_get_cors_origins_from_env(self):
        """Test getting CORS origins from environment."""

        # Test empty env var
        origins = get_cors_origins_from_env("TEST_CORS_ORIGINS")
        assert origins == []

        # Test with default
        origins = get_cors_origins_from_env(
            "TEST_CORS_ORIGINS", default=["https://default.com"]
        )
        assert origins == ["https://default.com"]

    def test_cors_presets_exist(self):
        """Test CORS presets class exists."""
        assert hasattr(CORSPresets, "development")
        assert hasattr(CORSPresets, "api_gateway")
        assert hasattr(CORSPresets, "public_api")


# =============================================================================
# Security Headers Tests
# =============================================================================


class TestSecurityHeaders:
    """Tests for security headers middleware."""

    def test_middleware_initialization(self):
        """Test SecurityHeadersMiddleware initialization."""

        class MockApp:
            pass

        middleware = SecurityHeadersMiddleware(app=MockApp())
        assert middleware.app is not None
        assert len(middleware.headers) > 0

    def test_middleware_default_headers(self):
        """Test SecurityHeadersMiddleware default headers."""

        class MockApp:
            pass

        middleware = SecurityHeadersMiddleware(app=MockApp())

        assert "X-Content-Type-Options" in middleware.headers
        assert "X-Frame-Options" in middleware.headers
        assert middleware.headers["X-Content-Type-Options"] == "nosniff"

    def test_middleware_custom_headers(self):
        """Test SecurityHeadersMiddleware with custom headers."""

        class MockApp:
            pass

        middleware = SecurityHeadersMiddleware(
            app=MockApp(),
            custom_headers={"X-Custom-Header": "custom-value"},
        )

        assert "X-Custom-Header" in middleware.headers

    def test_middleware_override_default(self):
        """Test overriding default security header."""

        class MockApp:
            pass

        middleware = SecurityHeadersMiddleware(
            app=MockApp(),
            x_frame_options="SAMEORIGIN",
        )

        assert middleware.headers["X-Frame-Options"] == "SAMEORIGIN"

    def test_get_default_csp(self):
        """Test generating default CSP."""
        csp = get_default_csp()
        assert "default-src 'self'" in csp
        assert "script-src" in csp

    def test_get_custom_csp(self):
        """Test generating custom CSP."""
        csp = get_default_csp(
            script_src=["'self'", "https://cdn.example.com"],
            frame_ancestors="'self'",
        )
        assert "https://cdn.example.com" in csp
        assert "frame-ancestors 'self'" in csp

    def test_security_presets_exist(self):
        """Test SecurityPresets class exists."""
        assert hasattr(SecurityPresets, "strict")
        assert hasattr(SecurityPresets, "api")
        assert hasattr(SecurityPresets, "web_app")
        assert hasattr(SecurityPresets, "development")


# =============================================================================
# Logging Middleware Tests
# =============================================================================


class TestLoggingMiddleware:
    """Tests for logging middleware."""

    def test_middleware_initialization(self):
        """Test LoggingMiddleware initialization."""
        import logging

        class MockApp:
            pass

        middleware = LoggingMiddleware(
            app=MockApp(),
            logger=logging.getLogger("test"),
        )

        assert middleware.app is not None
        assert middleware.logger is not None

    def test_middleware_default_logger(self):
        """Test LoggingMiddleware with default logger."""

        class MockApp:
            pass

        middleware = LoggingMiddleware(app=MockApp())
        assert middleware.logger is not None

    def test_middleware_exclude_paths(self):
        """Test LoggingMiddleware exclude paths."""

        class MockApp:
            pass

        middleware = LoggingMiddleware(
            app=MockApp(),
            exclude_paths=["/health", "/metrics"],
        )

        assert "/health" in middleware.exclude_paths
        assert "/metrics" in middleware.exclude_paths

    def test_middleware_log_body_flag(self):
        """Test LoggingMiddleware log body flag."""

        class MockApp:
            pass

        middleware = LoggingMiddleware(
            app=MockApp(),
            log_request_body=True,
            log_response_body=False,
        )

        assert middleware.log_request_body is True
        assert middleware.log_response_body is False
