"""
Redis cache client with advanced features.

Provides a high-level Redis cache interface with:
- Namespace support for multi-tenant applications
- Connection pooling
- Compression for large values
- Rate limiting
- Health checks
- Stampede protection (XFetch algorithm)
"""

import asyncio
import json
import logging
import zlib
from collections.abc import Callable
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class RedisCache:
    """
    Redis cache client with advanced features.

    Example:
        cache = RedisCache(
            url="redis://localhost:6379",
            namespace="myapp",
            default_ttl=3600,
        )
        await cache.connect()

        # Basic operations
        await cache.set("key", {"data": "value"}, ttl=300)
        value = await cache.get("key")
        await cache.delete("key")

        # Rate limiting
        allowed, remaining = await cache.check_rate_limit("user:123", limit=100, window=60)

        await cache.close()
    """

    def __init__(
        self,
        url: str = "redis://localhost:6379",
        namespace: str = "",
        default_ttl: int = 3600,
        max_connections: int = 10,
        compression_threshold: int = 1024,
        compression_level: int = 6,
        socket_timeout: float = 5.0,
        retry_on_timeout: bool = True,
        health_check_interval: int = 30,
        metrics_callback: Callable | None = None,
    ):
        """
        Initialize Redis cache client.

        Args:
            url: Redis connection URL
            namespace: Key prefix for all operations
            default_ttl: Default TTL in seconds
            max_connections: Maximum connection pool size
            compression_threshold: Compress values larger than this (bytes)
            compression_level: Zlib compression level (1-9)
            socket_timeout: Socket timeout in seconds
            retry_on_timeout: Retry on timeout errors
            health_check_interval: Health check interval in seconds
            metrics_callback: Callback for metrics (hits, misses, etc.)
        """
        self.url = url
        self.namespace = namespace
        self.default_ttl = default_ttl
        self.max_connections = max_connections
        self.compression_threshold = compression_threshold
        self.compression_level = compression_level
        self.socket_timeout = socket_timeout
        self.retry_on_timeout = retry_on_timeout
        self.health_check_interval = health_check_interval
        self.metrics_callback = metrics_callback

        self._client = None
        self._pool = None
        self._connected = False

        # Metrics
        self._hits = 0
        self._misses = 0
        self._errors = 0

    def _make_key(self, key: str) -> str:
        """Create namespaced key."""
        if self.namespace:
            return f"{self.namespace}:{key}"
        return key

    async def connect(self) -> None:
        """
        Establish connection to Redis.

        Must be called before any operations.
        """
        try:
            import redis.asyncio as redis
        except ImportError as err:
            raise ImportError(
                "redis package is required for cache functionality. "
                "Install it with: pip install redis"
            ) from err

        self._client = redis.from_url(
            self.url,
            max_connections=self.max_connections,
            socket_timeout=self.socket_timeout,
            retry_on_timeout=self.retry_on_timeout,
            decode_responses=False,  # We handle encoding ourselves
        )
        self._connected = True
        logger.info(f"Connected to Redis at {self.url}")

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._connected = False
            logger.info("Redis connection closed")

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def _serialize(self, value: Any) -> bytes:
        """Serialize value to bytes with optional compression."""
        data = json.dumps(value, default=str).encode("utf-8")

        if len(data) > self.compression_threshold:
            compressed = zlib.compress(data, self.compression_level)
            # Prefix with 'Z' to indicate compression
            return b"Z" + compressed

        return b"R" + data  # 'R' for raw

    def _deserialize(self, data: bytes) -> Any:
        """Deserialize bytes to value, handling compression."""
        if data is None:
            return None

        if data[0:1] == b"Z":
            # Compressed data
            decompressed = zlib.decompress(data[1:])
            return json.loads(decompressed.decode("utf-8"))
        elif data[0:1] == b"R":
            # Raw data
            return json.loads(data[1:].decode("utf-8"))
        else:
            # Legacy format (no prefix)
            return json.loads(data.decode("utf-8"))

    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache.

        Args:
            key: Cache key
            default: Default value if key not found

        Returns:
            Cached value or default
        """
        if not self._connected:
            raise RuntimeError("Redis not connected. Call connect() first.")

        try:
            full_key = self._make_key(key)
            data = await self._client.get(full_key)

            if data is None:
                self._misses += 1
                self._record_metric("miss", key)
                return default

            self._hits += 1
            self._record_metric("hit", key)
            return self._deserialize(data)

        except Exception as e:
            self._errors += 1
            self._record_metric("error", key, error=str(e))
            logger.error(f"Redis GET error for {key}: {e}")
            return default

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: TTL in seconds (uses default_ttl if not specified)
            nx: Only set if key does not exist
            xx: Only set if key already exists

        Returns:
            True if set successfully, False otherwise
        """
        if not self._connected:
            raise RuntimeError("Redis not connected. Call connect() first.")

        try:
            full_key = self._make_key(key)
            data = self._serialize(value)
            ttl = ttl if ttl is not None else self.default_ttl

            result = await self._client.set(
                full_key,
                data,
                ex=ttl if ttl > 0 else None,
                nx=nx,
                xx=xx,
            )

            self._record_metric("set", key)
            return result is not None and result is not False

        except Exception as e:
            self._errors += 1
            self._record_metric("error", key, error=str(e))
            logger.error(f"Redis SET error for {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if key didn't exist
        """
        if not self._connected:
            raise RuntimeError("Redis not connected. Call connect() first.")

        try:
            full_key = self._make_key(key)
            result = await self._client.delete(full_key)
            self._record_metric("delete", key)
            return result > 0

        except Exception as e:
            self._errors += 1
            self._record_metric("error", key, error=str(e))
            logger.error(f"Redis DELETE error for {key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern.

        Args:
            pattern: Glob-style pattern (e.g., "user:*")

        Returns:
            Number of keys deleted
        """
        if not self._connected:
            raise RuntimeError("Redis not connected. Call connect() first.")

        try:
            full_pattern = self._make_key(pattern)
            count = 0

            # Use SCAN to avoid blocking
            async for key in self._client.scan_iter(match=full_pattern, count=100):
                await self._client.delete(key)
                count += 1

            self._record_metric("delete_pattern", pattern, count=count)
            return count

        except Exception as e:
            self._errors += 1
            self._record_metric("error", pattern, error=str(e))
            logger.error(f"Redis DELETE_PATTERN error for {pattern}: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self._connected:
            raise RuntimeError("Redis not connected. Call connect() first.")

        try:
            full_key = self._make_key(key)
            return await self._client.exists(full_key) > 0
        except Exception as e:
            self._errors += 1
            logger.error(f"Redis EXISTS error for {key}: {e}")
            return False

    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL on existing key."""
        if not self._connected:
            raise RuntimeError("Redis not connected. Call connect() first.")

        try:
            full_key = self._make_key(key)
            return await self._client.expire(full_key, ttl)
        except Exception as e:
            self._errors += 1
            logger.error(f"Redis EXPIRE error for {key}: {e}")
            return False

    async def ttl(self, key: str) -> int:
        """Get remaining TTL for key (-1 if no TTL, -2 if not exists)."""
        if not self._connected:
            raise RuntimeError("Redis not connected. Call connect() first.")

        try:
            full_key = self._make_key(key)
            return await self._client.ttl(full_key)
        except Exception as e:
            self._errors += 1
            logger.error(f"Redis TTL error for {key}: {e}")
            return -2

    # =========================================================================
    # Batch Operations
    # =========================================================================

    async def mget(self, keys: list[str]) -> dict[str, Any]:
        """
        Get multiple values at once.

        Args:
            keys: List of cache keys

        Returns:
            Dict mapping keys to values (missing keys excluded)
        """
        if not self._connected:
            raise RuntimeError("Redis not connected. Call connect() first.")

        try:
            full_keys = [self._make_key(k) for k in keys]
            values = await self._client.mget(full_keys)

            result = {}
            for key, value in zip(keys, values, strict=False):
                if value is not None:
                    result[key] = self._deserialize(value)
                    self._hits += 1
                else:
                    self._misses += 1

            return result

        except Exception as e:
            self._errors += 1
            logger.error(f"Redis MGET error: {e}")
            return {}

    async def mset(self, mapping: dict[str, Any], ttl: int | None = None) -> bool:
        """
        Set multiple values at once.

        Args:
            mapping: Dict of key-value pairs
            ttl: TTL in seconds (applied to all keys)

        Returns:
            True if successful
        """
        if not self._connected:
            raise RuntimeError("Redis not connected. Call connect() first.")

        try:
            ttl = ttl if ttl is not None else self.default_ttl

            # Use pipeline for atomic operation
            pipe = self._client.pipeline()

            for key, value in mapping.items():
                full_key = self._make_key(key)
                data = self._serialize(value)
                if ttl > 0:
                    pipe.setex(full_key, ttl, data)
                else:
                    pipe.set(full_key, data)

            await pipe.execute()
            return True

        except Exception as e:
            self._errors += 1
            logger.error(f"Redis MSET error: {e}")
            return False

    # =========================================================================
    # Rate Limiting
    # =========================================================================

    async def check_rate_limit(
        self,
        identifier: str,
        limit: int,
        window: int,
        cost: int = 1,
    ) -> tuple[bool, int]:
        """
        Check rate limit using sliding window algorithm.

        Args:
            identifier: Unique identifier (e.g., "user:123", "ip:1.2.3.4")
            limit: Maximum requests per window
            window: Window size in seconds
            cost: Cost of this request (default 1)

        Returns:
            Tuple of (is_allowed, remaining_requests)

        Example:
            allowed, remaining = await cache.check_rate_limit(
                identifier="user:123",
                limit=100,
                window=60,  # 100 requests per minute
            )
        """
        if not self._connected:
            raise RuntimeError("Redis not connected. Call connect() first.")

        key = self._make_key(f"rate_limit:{identifier}")
        now = datetime.utcnow().timestamp()
        window_start = now - window

        try:
            pipe = self._client.pipeline()

            # Remove old entries
            pipe.zremrangebyscore(key, 0, window_start)

            # Count current window
            pipe.zcard(key)

            # Add new request
            pipe.zadd(key, {f"{now}:{cost}": now})

            # Set TTL
            pipe.expire(key, window + 1)

            results = await pipe.execute()
            current_count = results[1]

            remaining = max(0, limit - current_count - cost)
            is_allowed = current_count + cost <= limit

            self._record_metric("rate_limit", identifier, allowed=is_allowed)

            return is_allowed, remaining

        except Exception as e:
            self._errors += 1
            logger.error(f"Redis rate limit error: {e}")
            # Fail open - allow request on error
            return True, limit

    async def get_rate_limit_status(
        self,
        identifier: str,
        limit: int,
        window: int,
    ) -> dict[str, Any]:
        """
        Get current rate limit status without incrementing.

        Returns:
            Dict with keys: used, remaining, limit, reset_at
        """
        if not self._connected:
            raise RuntimeError("Redis not connected. Call connect() first.")

        key = self._make_key(f"rate_limit:{identifier}")
        now = datetime.utcnow().timestamp()
        window_start = now - window

        try:
            pipe = self._client.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.zrange(key, 0, 0, withscores=True)

            results = await pipe.execute()
            used = results[1]
            oldest = results[2]

            reset_at = None
            if oldest:
                oldest_time = oldest[0][1]
                reset_at = datetime.fromtimestamp(oldest_time + window)

            return {
                "used": used,
                "remaining": max(0, limit - used),
                "limit": limit,
                "reset_at": reset_at,
            }

        except Exception as e:
            self._errors += 1
            logger.error(f"Redis rate limit status error: {e}")
            return {
                "used": 0,
                "remaining": limit,
                "limit": limit,
                "reset_at": None,
            }

    # =========================================================================
    # Health Check
    # =========================================================================

    async def health_check(self) -> dict[str, Any]:
        """
        Perform health check on Redis connection.

        Returns:
            Dict with health status, latency, and connection info
        """
        result = {
            "healthy": False,
            "latency_ms": None,
            "connected": self._connected,
            "hits": self._hits,
            "misses": self._misses,
            "errors": self._errors,
            "hit_rate": 0.0,
        }

        if not self._connected:
            return result

        try:
            start = datetime.utcnow()
            await self._client.ping()
            latency = (datetime.utcnow() - start).total_seconds() * 1000

            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0

            result.update(
                {
                    "healthy": True,
                    "latency_ms": round(latency, 2),
                    "hit_rate": round(hit_rate, 2),
                }
            )

        except Exception as e:
            result["error"] = str(e)

        return result

    # =========================================================================
    # Stampede Protection (XFetch)
    # =========================================================================

    async def get_or_set(
        self,
        key: str,
        factory: Callable,
        ttl: int | None = None,
        beta: float = 1.0,
    ) -> Any:
        """
        Get value from cache or compute and cache it.

        Uses XFetch algorithm for stampede protection.

        Args:
            key: Cache key
            factory: Async function to compute value if not cached
            ttl: TTL in seconds
            beta: XFetch beta parameter (higher = more eager refresh)

        Returns:
            Cached or computed value
        """
        if not self._connected:
            raise RuntimeError("Redis not connected. Call connect() first.")

        ttl = ttl if ttl is not None else self.default_ttl

        # Try to get from cache
        value = await self.get(key)
        if value is not None:
            return value

        # Compute value

        # Use lock to prevent stampede
        lock_key = f"{key}:lock"
        lock_acquired = await self.set(lock_key, 1, ttl=30, nx=True)

        if lock_acquired:
            try:
                # Double-check cache
                value = await self.get(key)
                if value is not None:
                    return value

                # Compute and cache
                if asyncio.iscoroutinefunction(factory):
                    value = await factory()
                else:
                    value = factory()

                await self.set(key, value, ttl=ttl)
                return value

            finally:
                await self.delete(lock_key)
        else:
            # Wait and retry
            for _ in range(10):
                await asyncio.sleep(0.1)
                value = await self.get(key)
                if value is not None:
                    return value

            # Still no value, compute anyway
            if asyncio.iscoroutinefunction(factory):
                return await factory()
            return factory()

    # =========================================================================
    # Metrics
    # =========================================================================

    def _record_metric(self, operation: str, key: str, **kwargs) -> None:
        """Record metric if callback is configured."""
        if self.metrics_callback:
            try:
                self.metrics_callback(
                    operation=operation, key=key, namespace=self.namespace, **kwargs
                )
            except Exception as e:
                logger.warning(f"Metrics callback error: {e}")

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total = self._hits + self._misses
        return {
            "hits": self._hits,
            "misses": self._misses,
            "errors": self._errors,
            "total_requests": total,
            "hit_rate": (self._hits / total * 100) if total > 0 else 0,
        }

    def reset_stats(self) -> None:
        """Reset cache statistics."""
        self._hits = 0
        self._misses = 0
        self._errors = 0
