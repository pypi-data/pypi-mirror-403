"""
Neural LAB Python SDK - Test Suite

Author: Anderson Henrique da Silva
Date: 2026-01-28
Location: Minas Gerais, Brasil
Copyright: Neural Thinker | AI Engineering LTDA

Description: Extended tests for rate limiting middleware
Version: 1.0.0
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ntlabs.middleware.rate_limiting import (
    RateLimitTier,
    TierConfig,
    EndpointConfig,
    RateLimitMiddleware,
    rate_limit,
    DEFAULT_TIER_CONFIG,
)


class TestRateLimitTier:
    """Test RateLimitTier enum."""

    def test_tier_values(self):
        """Test tier enum values."""
        assert RateLimitTier.FREE.value == "free"
        assert RateLimitTier.BASIC.value == "basic"
        assert RateLimitTier.PRO.value == "pro"
        assert RateLimitTier.ENTERPRISE.value == "enterprise"
        assert RateLimitTier.UNLIMITED.value == "unlimited"


class TestTierConfig:
    """Test TierConfig dataclass."""

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
            per_minute=100,
            per_hour=5000,
            per_day=50000,
            burst_limit=20,
        )
        assert config.per_minute == 100
        assert config.per_hour == 5000
        assert config.per_day == 50000
        assert config.burst_limit == 20


class TestEndpointConfig:
    """Test EndpointConfig dataclass."""

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


class TestDefaultTierConfig:
    """Test default tier configurations."""

    def test_free_tier(self):
        """Test FREE tier defaults."""
        config = DEFAULT_TIER_CONFIG[RateLimitTier.FREE]
        assert config.per_minute == 30
        assert config.per_hour == 500
        assert config.per_day == 5000

    def test_basic_tier(self):
        """Test BASIC tier defaults."""
        config = DEFAULT_TIER_CONFIG[RateLimitTier.BASIC]
        assert config.per_minute == 60
        assert config.per_hour == 2000
        assert config.per_day == 20000

    def test_pro_tier(self):
        """Test PRO tier defaults."""
        config = DEFAULT_TIER_CONFIG[RateLimitTier.PRO]
        assert config.per_minute == 120
        assert config.per_hour == 5000
        assert config.per_day == 50000

    def test_enterprise_tier(self):
        """Test ENTERPRISE tier defaults."""
        config = DEFAULT_TIER_CONFIG[RateLimitTier.ENTERPRISE]
        assert config.per_minute == 300
        assert config.per_hour == 20000
        assert config.per_day == 200000

    def test_unlimited_tier(self):
        """Test UNLIMITED tier defaults."""
        config = DEFAULT_TIER_CONFIG[RateLimitTier.UNLIMITED]
        assert config.per_minute == 999999


class TestRateLimitMiddlewareInit:
    """Test RateLimitMiddleware initialization."""

    @pytest.fixture
    def mock_app(self):
        """Create a mock ASGI app."""
        return MagicMock()

    def test_default_init(self, mock_app):
        """Test initialization with defaults."""
        middleware = RateLimitMiddleware(mock_app)
        assert middleware.app is mock_app
        assert middleware.redis_url == "redis://localhost:6379"
        assert middleware.default_tier == RateLimitTier.BASIC
        assert middleware.namespace == "rate_limit"

    def test_custom_init(self, mock_app):
        """Test initialization with custom values."""
        middleware = RateLimitMiddleware(
            app=mock_app,
            redis_url="redis://custom:6379",
            default_tier=RateLimitTier.PRO,
            namespace="custom_ns",
        )
        assert middleware.redis_url == "redis://custom:6379"
        assert middleware.default_tier == RateLimitTier.PRO
        assert middleware.namespace == "custom_ns"

    def test_init_with_tier_config(self, mock_app):
        """Test initialization with custom tier config."""
        tier_config = {
            RateLimitTier.FREE: {"per_minute": 10},
            RateLimitTier.PRO: {"per_minute": 200},
        }
        middleware = RateLimitMiddleware(
            app=mock_app,
            tier_config=tier_config,
        )
        assert middleware._tier_config[RateLimitTier.FREE].per_minute == 10
        assert middleware._tier_config[RateLimitTier.PRO].per_minute == 200

    def test_init_with_endpoint_config(self, mock_app):
        """Test initialization with endpoint config."""
        endpoint_config = {
            "/api/expensive": {"per_minute": 10, "cost": 5},
        }
        middleware = RateLimitMiddleware(
            app=mock_app,
            endpoint_config=endpoint_config,
        )
        assert "/api/expensive" in middleware._endpoint_config
        assert middleware._endpoint_config["/api/expensive"].per_minute == 10
        assert middleware._endpoint_config["/api/expensive"].cost == 5

    def test_init_with_exclude_paths(self, mock_app):
        """Test initialization with excluded paths."""
        middleware = RateLimitMiddleware(
            app=mock_app,
            exclude_paths=["/health", "/metrics"],
        )
        assert "/health" in middleware.exclude_paths
        assert "/metrics" in middleware.exclude_paths

    def test_default_exclude_paths(self, mock_app):
        """Test default excluded paths."""
        middleware = RateLimitMiddleware(app=mock_app)
        assert "/health" in middleware.exclude_paths
        assert "/docs" in middleware.exclude_paths
        assert "/openapi.json" in middleware.exclude_paths


class TestRateLimitMiddlewareRedis:
    """Test Redis client management."""

    @pytest.fixture
    def middleware(self):
        """Create a middleware instance."""
        app = MagicMock()
        return RateLimitMiddleware(app)

    @pytest.mark.asyncio
    async def test_get_redis(self, middleware):
        """Test getting Redis client."""
        with patch("redis.asyncio.from_url") as mock_from_url:
            mock_redis = AsyncMock()
            mock_from_url.return_value = mock_redis

            redis = await middleware._get_redis()
            assert redis is mock_redis
            mock_from_url.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_redis_cached(self, middleware):
        """Test that Redis client is cached."""
        with patch("redis.asyncio.from_url") as mock_from_url:
            mock_redis = AsyncMock()
            mock_from_url.return_value = mock_redis

            redis1 = await middleware._get_redis()
            redis2 = await middleware._get_redis()
            assert redis1 is redis2
            mock_from_url.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_redis_import_error(self, middleware):
        """Test handling of missing redis package."""
        with patch.dict("sys.modules", {"redis": None}):
            with patch("builtins.__import__", side_effect=ImportError("No module named 'redis'")):
                with pytest.raises(ImportError):
                    await middleware._get_redis()


class TestRateLimitMiddlewareCall:
    """Test ASGI call handling."""

    @pytest.fixture
    def middleware(self):
        """Create a middleware instance."""
        app = AsyncMock()
        return RateLimitMiddleware(app)

    @pytest.mark.asyncio
    async def test_non_http_request(self, middleware):
        """Test handling non-HTTP requests."""
        scope = {"type": "websocket"}
        receive = AsyncMock()
        send = AsyncMock()

        await middleware(scope, receive, send)
        middleware.app.assert_called_once_with(scope, receive, send)

    @pytest.mark.asyncio
    async def test_excluded_path(self, middleware):
        """Test handling excluded paths."""
        scope = {"type": "http", "path": "/health"}
        receive = AsyncMock()
        send = AsyncMock()

        await middleware(scope, receive, send)
        middleware.app.assert_called_once_with(scope, receive, send)

    @pytest.mark.asyncio
    async def test_no_identifier(self, middleware):
        """Test handling when no identifier can be extracted."""
        scope = {"type": "http", "path": "/api/test", "headers": []}
        receive = AsyncMock()
        send = AsyncMock()

        await middleware(scope, receive, send)
        middleware.app.assert_called_once_with(scope, receive, send)


class TestRateLimitMiddlewareIdentifier:
    """Test identifier extraction."""

    @pytest.fixture
    def middleware(self):
        """Create a middleware instance."""
        app = MagicMock()
        return RateLimitMiddleware(app)

    @pytest.mark.asyncio
    async def test_identifier_from_x_forwarded_for(self, middleware):
        """Test extracting identifier from X-Forwarded-For header."""
        scope = {
            "type": "http",
            "headers": [(b"x-forwarded-for", b"1.2.3.4, 5.6.7.8")],
        }

        identifier = await middleware._get_identifier(scope)
        assert identifier == "1.2.3.4"

    @pytest.mark.asyncio
    async def test_identifier_from_client(self, middleware):
        """Test extracting identifier from client info."""
        scope = {
            "type": "http",
            "headers": [],
            "client": ("192.168.1.1", 12345),
        }

        identifier = await middleware._get_identifier(scope)
        assert identifier == "192.168.1.1"

    @pytest.mark.asyncio
    async def test_identifier_no_source(self, middleware):
        """Test when no identifier source available."""
        scope = {
            "type": "http",
            "headers": [],
        }

        identifier = await middleware._get_identifier(scope)
        assert identifier is None

    @pytest.mark.asyncio
    async def test_identifier_custom_func(self):
        """Test custom identifier function."""
        def custom_identifier(request):
            return "custom_id"

        app = MagicMock()
        middleware = RateLimitMiddleware(
            app=app,
            identifier_func=custom_identifier,
        )

        scope = {"type": "http", "headers": []}

        with patch("starlette.requests.Request") as mock_request:
            identifier = await middleware._get_identifier(scope)
            assert identifier == "custom_id"

    @pytest.mark.skip(reason="Async identifier functions not fully supported")
    @pytest.mark.asyncio
    async def test_identifier_custom_func_async(self):
        """Test async custom identifier function."""
        pass


class TestRateLimitMiddlewareTier:
    """Test tier extraction."""

    @pytest.fixture
    def middleware(self):
        """Create a middleware instance."""
        app = MagicMock()
        return RateLimitMiddleware(
            app=app,
            default_tier=RateLimitTier.BASIC,
        )

    @pytest.mark.asyncio
    async def test_default_tier(self, middleware):
        """Test default tier when no custom function."""
        scope = {"type": "http"}
        tier = await middleware._get_tier(scope)
        assert tier == RateLimitTier.BASIC

    @pytest.mark.asyncio
    async def test_custom_tier_func(self):
        """Test custom tier function."""
        def get_tier(request):
            return RateLimitTier.PRO

        app = MagicMock()
        middleware = RateLimitMiddleware(
            app=app,
            tier_func=get_tier,
        )

        scope = {"type": "http"}

        with patch("starlette.requests.Request"):
            tier = await middleware._get_tier(scope)
            assert tier == RateLimitTier.PRO

    @pytest.mark.skip(reason="Async tier functions not fully supported")
    @pytest.mark.asyncio
    async def test_custom_tier_func_async(self):
        """Test async custom tier function."""
        pass


class TestRateLimitMiddlewareCheck:
    """Test rate limit checking."""

    @pytest.fixture
    def middleware(self):
        """Create a middleware instance."""
        app = MagicMock()
        return RateLimitMiddleware(app)

    @pytest.mark.asyncio
    async def test_rate_limit_allowed(self, middleware):
        """Test rate limit check when allowed."""
        mock_redis = AsyncMock()
        mock_pipeline = AsyncMock()
        mock_pipeline.execute = AsyncMock(return_value=[0, 5, 1, 1])  # removed, count, added, expire
        mock_redis.pipeline = MagicMock(return_value=mock_pipeline)
        middleware._redis = mock_redis

        allowed, headers = await middleware._check_rate_limit(
            "user:123",
            RateLimitTier.BASIC,
            "/api/test",
        )

        assert allowed is True
        assert "X-RateLimit-Limit" in headers
        assert "X-RateLimit-Remaining" in headers

    @pytest.mark.asyncio
    async def test_rate_limit_denied(self, middleware):
        """Test rate limit check when denied."""
        mock_redis = AsyncMock()
        mock_pipeline = AsyncMock()
        mock_pipeline.execute = AsyncMock(return_value=[0, 100, 1, 1])  # At limit
        mock_redis.pipeline = MagicMock(return_value=mock_pipeline)
        middleware._redis = mock_redis

        allowed, headers = await middleware._check_rate_limit(
            "user:123",
            RateLimitTier.BASIC,
            "/api/test",
        )

        assert allowed is False
        assert "Retry-After" in headers

    @pytest.mark.asyncio
    async def test_rate_limit_with_endpoint_config(self, middleware):
        """Test rate limit with endpoint-specific config."""
        middleware._endpoint_config["/api/expensive"] = EndpointConfig(
            per_minute=10,
            cost=5,
        )

        mock_redis = AsyncMock()
        mock_pipeline = AsyncMock()
        mock_pipeline.execute = AsyncMock(return_value=[0, 2, 1, 1])
        mock_redis.pipeline = MagicMock(return_value=mock_pipeline)
        middleware._redis = mock_redis

        allowed, headers = await middleware._check_rate_limit(
            "user:123",
            RateLimitTier.BASIC,
            "/api/expensive",
        )

        assert headers["X-RateLimit-Limit"] == 10

    @pytest.mark.asyncio
    async def test_rate_limit_error(self, middleware):
        """Test rate limit check with Redis error."""
        mock_redis = AsyncMock()
        mock_redis.pipeline = MagicMock(side_effect=Exception("Redis error"))
        middleware._redis = mock_redis

        allowed, headers = await middleware._check_rate_limit(
            "user:123",
            RateLimitTier.BASIC,
            "/api/test",
        )

        # Fail open
        assert allowed is True
        assert headers == {}


class TestRateLimitMiddlewareSend429:
    """Test 429 response sending."""

    @pytest.fixture
    def middleware(self):
        """Create a middleware instance."""
        app = MagicMock()
        return RateLimitMiddleware(app)

    @pytest.mark.asyncio
    async def test_send_429(self, middleware):
        """Test sending 429 response."""
        send = AsyncMock()
        headers = {
            "X-RateLimit-Limit": 60,
            "X-RateLimit-Remaining": 0,
            "Retry-After": 60,
        }

        await middleware._send_429(send, headers)

        assert send.call_count == 2

        # Check response start
        start_call = send.call_args_list[0][0][0]
        assert start_call["type"] == "http.response.start"
        assert start_call["status"] == 429

        # Check response body
        body_call = send.call_args_list[1][0][0]
        assert body_call["type"] == "http.response.body"
        assert b"Too Many Requests" in body_call["body"]


class TestRateLimitDecorator:
    """Test rate limit decorator."""

    @pytest.mark.asyncio
    async def test_rate_limit_decorator(self):
        """Test rate limit decorator function."""

        @rate_limit(limit=10, window=60)
        async def test_endpoint():
            return {"result": "success"}

        # The decorator is a placeholder, so it should just call the function
        result = await test_endpoint()
        assert result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_rate_limit_decorator_with_identifier(self):
        """Test rate limit decorator with custom identifier."""

        @rate_limit(limit=10, window=60, identifier="user:123")
        async def test_endpoint():
            return {"result": "success"}

        result = await test_endpoint()
        assert result == {"result": "success"}
