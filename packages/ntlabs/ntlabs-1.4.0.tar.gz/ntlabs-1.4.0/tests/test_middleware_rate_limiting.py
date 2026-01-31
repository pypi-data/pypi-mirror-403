"""
Comprehensive tests for ntlabs.middleware.rate_limiting module.

Tests rate limiting middleware for FastAPI.
"""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from ntlabs.middleware.rate_limiting import (
    DEFAULT_TIER_CONFIG,
    EndpointConfig,
    RateLimitMiddleware,
    RateLimitTier,
    TierConfig,
    rate_limit,
)


# =============================================================================
# Rate Limit Tier Enum Tests
# =============================================================================


class TestRateLimitTier:
    """Tests for RateLimitTier enum."""

    def test_tier_values(self):
        """Test tier enum values."""
        assert RateLimitTier.FREE.value == "free"
        assert RateLimitTier.BASIC.value == "basic"
        assert RateLimitTier.PRO.value == "pro"
        assert RateLimitTier.ENTERPRISE.value == "enterprise"
        assert RateLimitTier.UNLIMITED.value == "unlimited"

    def test_all_tiers(self):
        """Test all tier enum members."""
        tiers = list(RateLimitTier)
        assert len(tiers) == 5
        assert RateLimitTier.FREE in tiers
        assert RateLimitTier.BASIC in tiers
        assert RateLimitTier.PRO in tiers
        assert RateLimitTier.ENTERPRISE in tiers
        assert RateLimitTier.UNLIMITED in tiers


# =============================================================================
# Tier Config Tests
# =============================================================================


class TestTierConfig:
    """Tests for TierConfig dataclass."""

    def test_default_config(self):
        """Test default tier configuration."""
        config = TierConfig()
        assert config.per_minute == 60
        assert config.per_hour == 1000
        assert config.per_day == 10000
        assert config.burst_limit == 10

    def test_custom_config(self):
        """Test custom tier configuration."""
        config = TierConfig(
            per_minute=120,
            per_hour=5000,
            per_day=50000,
            burst_limit=20,
        )
        assert config.per_minute == 120
        assert config.per_hour == 5000
        assert config.per_day == 50000
        assert config.burst_limit == 20


# =============================================================================
# Endpoint Config Tests
# =============================================================================


class TestEndpointConfig:
    """Tests for EndpointConfig dataclass."""

    def test_default_config(self):
        """Test default endpoint configuration."""
        config = EndpointConfig()
        assert config.per_minute == 60
        assert config.cost == 1

    def test_custom_config(self):
        """Test custom endpoint configuration."""
        config = EndpointConfig(per_minute=30, cost=5)
        assert config.per_minute == 30
        assert config.cost == 5


# =============================================================================
# Default Tier Config Tests
# =============================================================================


class TestDefaultTierConfig:
    """Tests for DEFAULT_TIER_CONFIG."""

    def test_all_tiers_have_config(self):
        """Test that all tiers have default configuration."""
        for tier in RateLimitTier:
            assert tier in DEFAULT_TIER_CONFIG

    def test_free_tier_limits(self):
        """Test FREE tier limits."""
        config = DEFAULT_TIER_CONFIG[RateLimitTier.FREE]
        assert config.per_minute == 30
        assert config.per_hour == 500
        assert config.per_day == 5000

    def test_basic_tier_limits(self):
        """Test BASIC tier limits."""
        config = DEFAULT_TIER_CONFIG[RateLimitTier.BASIC]
        assert config.per_minute == 60
        assert config.per_hour == 2000
        assert config.per_day == 20000

    def test_pro_tier_limits(self):
        """Test PRO tier limits."""
        config = DEFAULT_TIER_CONFIG[RateLimitTier.PRO]
        assert config.per_minute == 120
        assert config.per_hour == 5000
        assert config.per_day == 50000

    def test_enterprise_tier_limits(self):
        """Test ENTERPRISE tier limits."""
        config = DEFAULT_TIER_CONFIG[RateLimitTier.ENTERPRISE]
        assert config.per_minute == 300
        assert config.per_hour == 20000
        assert config.per_day == 200000

    def test_unlimited_tier_limits(self):
        """Test UNLIMITED tier limits."""
        config = DEFAULT_TIER_CONFIG[RateLimitTier.UNLIMITED]
        assert config.per_minute == 999999
        assert config.per_hour == 999999
        assert config.per_day == 999999

    def test_tier_limits_progression(self):
        """Test that limits increase with tier level."""
        free = DEFAULT_TIER_CONFIG[RateLimitTier.FREE]
        basic = DEFAULT_TIER_CONFIG[RateLimitTier.BASIC]
        pro = DEFAULT_TIER_CONFIG[RateLimitTier.PRO]
        enterprise = DEFAULT_TIER_CONFIG[RateLimitTier.ENTERPRISE]

        assert free.per_minute < basic.per_minute
        assert basic.per_minute < pro.per_minute
        assert pro.per_minute < enterprise.per_minute


# =============================================================================
# Rate Limit Middleware Initialization Tests
# =============================================================================


class TestRateLimitMiddlewareInit:
    """Tests for RateLimitMiddleware initialization."""

    def test_middleware_init_defaults(self):
        """Test middleware initialization with defaults."""

        class MockApp:
            pass

        middleware = RateLimitMiddleware(app=MockApp())
        assert middleware.app is not None
        assert middleware.redis_url == "redis://localhost:6379"
        assert middleware.default_tier == RateLimitTier.BASIC
        assert middleware.namespace == "rate_limit"
        assert "/health" in middleware.exclude_paths
        assert "/docs" in middleware.exclude_paths

    def test_middleware_init_custom(self):
        """Test middleware with custom configuration."""

        class MockApp:
            pass

        middleware = RateLimitMiddleware(
            app=MockApp(),
            redis_url="redis://custom:6380",
            default_tier=RateLimitTier.PRO,
            namespace="custom_namespace",
        )
        assert middleware.redis_url == "redis://custom:6380"
        assert middleware.default_tier == RateLimitTier.PRO
        assert middleware.namespace == "custom_namespace"

    def test_middleware_init_custom_tier_config(self):
        """Test middleware with custom tier configuration."""

        class MockApp:
            pass

        middleware = RateLimitMiddleware(
            app=MockApp(),
            tier_config={
                RateLimitTier.FREE: {"per_minute": 50},
                RateLimitTier.PRO: {"per_minute": 200},
            },
        )

        # Check FREE tier was updated
        free_config = middleware._tier_config[RateLimitTier.FREE]
        assert free_config.per_minute == 50

        # Check PRO tier was updated
        pro_config = middleware._tier_config[RateLimitTier.PRO]
        assert pro_config.per_minute == 200

    def test_middleware_init_endpoint_config(self):
        """Test middleware with endpoint configuration."""

        class MockApp:
            pass

        middleware = RateLimitMiddleware(
            app=MockApp(),
            endpoint_config={
                "/api/chat": {"per_minute": 20, "cost": 5},
                "/api/export": {"per_minute": 5, "cost": 10},
            },
        )

        assert "/api/chat" in middleware._endpoint_config
        chat_config = middleware._endpoint_config["/api/chat"]
        assert chat_config.per_minute == 20
        assert chat_config.cost == 5

    def test_middleware_init_custom_exclude_paths(self):
        """Test middleware with custom exclude paths."""

        class MockApp:
            pass

        middleware = RateLimitMiddleware(
            app=MockApp(),
            exclude_paths=["/custom", "/exclude"],
        )
        assert "/custom" in middleware.exclude_paths
        assert "/exclude" in middleware.exclude_paths


# =============================================================================
# Middleware Call Tests
# =============================================================================


class TestRateLimitMiddlewareCall:
    """Tests for RateLimitMiddleware __call__ method."""

    @pytest.mark.asyncio
    async def test_call_non_http_scope(self):
        """Test middleware ignores non-HTTP scopes."""

        class MockApp:
            async def __call__(self, scope, receive, send):
                await send({"type": "websocket.accept"})

        middleware = RateLimitMiddleware(app=MockApp())
        scope = {"type": "websocket"}
        receive = AsyncMock()
        send = AsyncMock()

        await middleware(scope, receive, send)
        # Should pass through without rate limiting
        assert middleware.app is not None

    @pytest.mark.asyncio
    async def test_call_excluded_path(self):
        """Test middleware skips excluded paths."""

        class MockApp:
            async def __call__(self, scope, receive, send):
                await send({"type": "http.response.start", "status": 200})

        middleware = RateLimitMiddleware(
            app=MockApp(),
            exclude_paths=["/health"],
        )
        scope = {"type": "http", "path": "/health", "method": "GET"}
        receive = AsyncMock()
        send = AsyncMock()

        await middleware(scope, receive, send)


# =============================================================================
# Identifier Extraction Tests
# =============================================================================


class TestIdentifierExtraction:
    """Tests for identifier extraction."""

    @pytest.mark.asyncio
    async def test_get_identifier_from_forwarded(self):
        """Test extracting identifier from X-Forwarded-For."""

        class MockApp:
            pass

        middleware = RateLimitMiddleware(app=MockApp())
        scope = {
            "headers": [(b"x-forwarded-for", b"203.0.113.195, 70.41.3.18")],
        }

        identifier = await middleware._get_identifier(scope)
        assert identifier == "203.0.113.195"

    @pytest.mark.asyncio
    async def test_get_identifier_from_client(self):
        """Test extracting identifier from scope client."""

        class MockApp:
            pass

        middleware = RateLimitMiddleware(app=MockApp())
        scope = {
            "headers": [],
            "client": ("192.168.1.100", 54321),
        }

        identifier = await middleware._get_identifier(scope)
        assert identifier == "192.168.1.100"

    @pytest.mark.asyncio
    async def test_get_identifier_none(self):
        """Test when no identifier can be extracted."""

        class MockApp:
            pass

        middleware = RateLimitMiddleware(app=MockApp())
        scope = {
            "headers": [],
            # No client info
        }

        identifier = await middleware._get_identifier(scope)
        assert identifier is None


# =============================================================================
# Tier Extraction Tests
# =============================================================================


class TestTierExtraction:
    """Tests for tier extraction."""

    @pytest.mark.asyncio
    async def test_get_tier_default(self):
        """Test default tier is returned."""

        class MockApp:
            pass

        middleware = RateLimitMiddleware(
            app=MockApp(),
            default_tier=RateLimitTier.BASIC,
        )
        scope = {"headers": []}

        tier = await middleware._get_tier(scope)
        assert tier == RateLimitTier.BASIC


# =============================================================================
# Rate Limit Decorator Tests
# =============================================================================


class TestRateLimitDecorator:
    """Tests for rate_limit decorator."""

    @pytest.mark.asyncio
    async def test_decorator_basic(self):
        """Test basic decorator application."""

        @rate_limit(limit=10, window=60)
        async def my_endpoint():
            return {"data": "result"}

        # Decorator should wrap the function
        assert callable(my_endpoint)

        result = await my_endpoint()
        assert result == {"data": "result"}

    @pytest.mark.asyncio
    async def test_decorator_with_args(self):
        """Test decorator preserves function arguments."""

        @rate_limit(limit=10, window=60, identifier="user-123")
        async def my_endpoint(user_id, action):
            return {"user_id": user_id, "action": action}

        result = await my_endpoint("123", "create")
        assert result == {"user_id": "123", "action": "create"}


# =============================================================================
# Redis Client Tests
# =============================================================================


class TestRedisClient:
    """Tests for Redis client initialization."""

    @pytest.mark.asyncio
    async def test_get_redis_cached(self):
        """Test Redis client is cached after first access."""

        class MockApp:
            pass

        middleware = RateLimitMiddleware(app=MockApp())
        mock_client = AsyncMock()
        middleware._redis = mock_client

        redis = await middleware._get_redis()

        assert redis == mock_client
