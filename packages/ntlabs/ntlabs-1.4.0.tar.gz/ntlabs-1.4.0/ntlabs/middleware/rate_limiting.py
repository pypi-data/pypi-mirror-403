"""
Rate limiting middleware for FastAPI.

Provides configurable rate limiting with:
- Multiple tier support (FREE, BASIC, PRO)
- Per-endpoint configuration
- Redis-based storage
- Sliding window algorithm
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class RateLimitTier(Enum):
    """Rate limit tiers."""

    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    UNLIMITED = "unlimited"


@dataclass
class TierConfig:
    """Configuration for a rate limit tier."""

    per_minute: int = 60
    per_hour: int = 1000
    per_day: int = 10000
    burst_limit: int = 10  # Max requests in quick succession


@dataclass
class EndpointConfig:
    """Rate limit configuration for specific endpoint."""

    per_minute: int = 60
    cost: int = 1  # Request cost (for weighted limits)


# Default tier configurations
DEFAULT_TIER_CONFIG: dict[RateLimitTier, TierConfig] = {
    RateLimitTier.FREE: TierConfig(per_minute=30, per_hour=500, per_day=5000),
    RateLimitTier.BASIC: TierConfig(per_minute=60, per_hour=2000, per_day=20000),
    RateLimitTier.PRO: TierConfig(per_minute=120, per_hour=5000, per_day=50000),
    RateLimitTier.ENTERPRISE: TierConfig(
        per_minute=300, per_hour=20000, per_day=200000
    ),
    RateLimitTier.UNLIMITED: TierConfig(
        per_minute=999999, per_hour=999999, per_day=999999
    ),
}


class RateLimitMiddleware:
    """
    FastAPI rate limiting middleware.

    Example:
        from fastapi import FastAPI
        from ntlabs.middleware import RateLimitMiddleware, RateLimitTier

        app = FastAPI()

        # Simple setup
        app.add_middleware(
            RateLimitMiddleware,
            redis_url="redis://localhost:6379",
        )

        # Advanced setup
        app.add_middleware(
            RateLimitMiddleware,
            redis_url="redis://localhost:6379",
            default_tier=RateLimitTier.BASIC,
            tier_config={
                RateLimitTier.FREE: {"per_minute": 30},
                RateLimitTier.PRO: {"per_minute": 120},
            },
            endpoint_config={
                "/api/chat": {"per_minute": 20, "cost": 5},
                "/api/export": {"per_minute": 5, "cost": 10},
            },
            identifier_func=lambda request: request.headers.get("X-API-Key"),
            tier_func=lambda request: get_user_tier(request),
        )
    """

    def __init__(
        self,
        app,
        redis_url: str = "redis://localhost:6379",
        default_tier: RateLimitTier = RateLimitTier.BASIC,
        tier_config: dict[RateLimitTier, dict[str, int]] | None = None,
        endpoint_config: dict[str, dict[str, int]] | None = None,
        identifier_func: Callable | None = None,
        tier_func: Callable | None = None,
        exclude_paths: list[str] | None = None,
        namespace: str = "rate_limit",
    ):
        """
        Initialize rate limiting middleware.

        Args:
            app: FastAPI application
            redis_url: Redis connection URL
            default_tier: Default rate limit tier
            tier_config: Override tier configurations
            endpoint_config: Per-endpoint rate limit overrides
            identifier_func: Function to extract identifier from request
            tier_func: Function to get user's tier from request
            exclude_paths: Paths to exclude from rate limiting
            namespace: Redis key namespace
        """
        self.app = app
        self.redis_url = redis_url
        self.default_tier = default_tier
        self.namespace = namespace
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/openapi.json"]

        # Build tier config
        self._tier_config = dict(DEFAULT_TIER_CONFIG)
        if tier_config:
            for tier, config in tier_config.items():
                if tier in self._tier_config:
                    current = self._tier_config[tier]
                    self._tier_config[tier] = TierConfig(
                        per_minute=config.get("per_minute", current.per_minute),
                        per_hour=config.get("per_hour", current.per_hour),
                        per_day=config.get("per_day", current.per_day),
                        burst_limit=config.get("burst_limit", current.burst_limit),
                    )

        # Build endpoint config
        self._endpoint_config: dict[str, EndpointConfig] = {}
        if endpoint_config:
            for path, config in endpoint_config.items():
                self._endpoint_config[path] = EndpointConfig(
                    per_minute=config.get("per_minute", 60),
                    cost=config.get("cost", 1),
                )

        # Custom functions
        self._identifier_func = identifier_func
        self._tier_func = tier_func

        # Redis client (initialized on first request)
        self._redis = None

    async def _get_redis(self):
        """Get or create Redis client."""
        if self._redis is None:
            try:
                import redis.asyncio as redis

                self._redis = redis.from_url(
                    self.redis_url,
                    decode_responses=False,
                )
            except ImportError as err:
                raise ImportError(
                    "redis package is required for rate limiting. "
                    "Install it with: pip install redis"
                ) from err
        return self._redis

    async def __call__(self, scope, receive, send):
        """ASGI middleware handler."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Build request-like object for path checking
        path = scope.get("path", "")

        # Skip excluded paths
        if any(path.startswith(p) for p in self.exclude_paths):
            await self.app(scope, receive, send)
            return

        # Extract identifier
        identifier = await self._get_identifier(scope)
        if not identifier:
            await self.app(scope, receive, send)
            return

        # Get tier
        tier = await self._get_tier(scope)

        # Check rate limit
        allowed, headers = await self._check_rate_limit(identifier, tier, path)

        if not allowed:
            # Return 429 Too Many Requests
            await self._send_429(send, headers)
            return

        # Add rate limit headers to response
        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                existing_headers = list(message.get("headers", []))
                for key, value in headers.items():
                    existing_headers.append((key.encode(), str(value).encode()))
                message["headers"] = existing_headers
            await send(message)

        await self.app(scope, receive, send_with_headers)

    async def _get_identifier(self, scope) -> str | None:
        """Extract identifier from request."""
        if self._identifier_func:
            # Build minimal request for custom function
            from starlette.requests import Request

            request = Request(scope)
            result = self._identifier_func(request)
            if callable(result) and hasattr(result, "__await__"):
                return await result
            return result

        # Default: use IP address
        headers = dict(scope.get("headers", []))
        forwarded = headers.get(b"x-forwarded-for", b"").decode()
        if forwarded:
            return forwarded.split(",")[0].strip()

        client = scope.get("client")
        if client:
            return client[0]

        return None

    async def _get_tier(self, scope) -> RateLimitTier:
        """Get user's rate limit tier."""
        if self._tier_func:
            from starlette.requests import Request

            request = Request(scope)
            result = self._tier_func(request)
            if callable(result) and hasattr(result, "__await__"):
                return await result
            return result

        return self.default_tier

    async def _check_rate_limit(
        self,
        identifier: str,
        tier: RateLimitTier,
        path: str,
    ) -> tuple[bool, dict[str, Any]]:
        """Check rate limit and return result with headers."""
        redis = await self._get_redis()
        tier_config = self._tier_config.get(
            tier, DEFAULT_TIER_CONFIG[RateLimitTier.BASIC]
        )

        # Get endpoint-specific config
        endpoint_config = self._endpoint_config.get(path)
        limit = tier_config.per_minute
        cost = 1

        if endpoint_config:
            limit = endpoint_config.per_minute
            cost = endpoint_config.cost

        # Check rate limit
        key = f"{self.namespace}:{identifier}:minute"
        now = datetime.utcnow().timestamp()
        window_start = now - 60

        try:
            pipe = redis.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.zadd(key, {f"{now}:{cost}": now})
            pipe.expire(key, 61)
            results = await pipe.execute()

            current_count = results[1]
            remaining = max(0, limit - current_count - cost)
            allowed = current_count + cost <= limit

            headers = {
                "X-RateLimit-Limit": limit,
                "X-RateLimit-Remaining": remaining,
                "X-RateLimit-Reset": int(now + 60),
            }

            if not allowed:
                headers["Retry-After"] = 60

            return allowed, headers

        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # Fail open
            return True, {}

    async def _send_429(self, send, headers: dict[str, Any]):
        """Send 429 response."""
        response_headers = [
            (b"content-type", b"application/json"),
        ]
        for key, value in headers.items():
            response_headers.append((key.encode(), str(value).encode()))

        await send(
            {
                "type": "http.response.start",
                "status": 429,
                "headers": response_headers,
            }
        )

        import json

        body = json.dumps(
            {
                "error": "Too Many Requests",
                "message": "Rate limit exceeded. Please try again later.",
                "retry_after": headers.get("Retry-After", 60),
            }
        ).encode()

        await send(
            {
                "type": "http.response.body",
                "body": body,
            }
        )


def rate_limit(
    limit: int = 60,
    window: int = 60,
    identifier: str | None = None,
):
    """
    Rate limit decorator for individual endpoints.

    Example:
        @app.get("/api/expensive")
        @rate_limit(limit=10, window=60)
        async def expensive_endpoint():
            return {"result": "data"}
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Implementation would use dependency injection
            # This is a placeholder for the pattern
            return await func(*args, **kwargs)

        return wrapper

    return decorator
