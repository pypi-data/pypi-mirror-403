"""
Neural LAB Python SDK - Test Suite

Author: Anderson Henrique da Silva
Date: 2026-01-28
Location: Minas Gerais, Brasil
Copyright: Neural Thinker | AI Engineering LTDA

Description: Comprehensive tests for Redis cache module
Version: 1.0.0
"""

import asyncio
import json
import zlib
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ntlabs.cache.redis import RedisCache


class TestRedisCacheInit:
    """Test RedisCache initialization."""

    def test_default_init(self):
        """Test initialization with default values."""
        cache = RedisCache()
        assert cache.url == "redis://localhost:6379"
        assert cache.namespace == ""
        assert cache.default_ttl == 3600
        assert cache.max_connections == 10
        assert cache.compression_threshold == 1024

    def test_custom_init(self):
        """Test initialization with custom values."""
        cache = RedisCache(
            url="redis://custom:6379",
            namespace="test",
            default_ttl=7200,
            max_connections=20,
            compression_threshold=512,
            compression_level=9,
        )
        assert cache.url == "redis://custom:6379"
        assert cache.namespace == "test"
        assert cache.default_ttl == 7200
        assert cache.max_connections == 20
        assert cache.compression_threshold == 512
        assert cache.compression_level == 9

    def test_make_key_without_namespace(self):
        """Test key generation without namespace."""
        cache = RedisCache()
        assert cache._make_key("mykey") == "mykey"

    def test_make_key_with_namespace(self):
        """Test key generation with namespace."""
        cache = RedisCache(namespace="app")
        assert cache._make_key("mykey") == "app:mykey"


class TestRedisCacheSerialization:
    """Test serialization/deserialization."""

    def test_serialize_simple_value(self):
        """Test serialization of simple value."""
        cache = RedisCache()
        data = cache._serialize({"key": "value"})
        assert data[0:1] == b"R"  # Raw prefix

    def test_serialize_large_value_compression(self):
        """Test compression of large values."""
        cache = RedisCache(compression_threshold=100)
        large_data = {"key": "x" * 200}
        data = cache._serialize(large_data)
        assert data[0:1] == b"Z"  # Compressed prefix

    def test_deserialize_raw_data(self):
        """Test deserialization of raw data."""
        cache = RedisCache()
        original = {"key": "value"}
        serialized = cache._serialize(original)
        deserialized = cache._deserialize(serialized)
        assert deserialized == original

    def test_deserialize_compressed_data(self):
        """Test deserialization of compressed data."""
        cache = RedisCache(compression_threshold=10)
        original = {"key": "x" * 100}
        serialized = cache._serialize(original)
        deserialized = cache._deserialize(serialized)
        assert deserialized == original

    def test_deserialize_none(self):
        """Test deserialization of None."""
        cache = RedisCache()
        result = cache._deserialize(None)
        assert result is None

    def test_deserialize_legacy_format(self):
        """Test deserialization of legacy format (no prefix)."""
        cache = RedisCache()
        data = json.dumps({"key": "value"}).encode("utf-8")
        deserialized = cache._deserialize(data)
        assert deserialized == {"key": "value"}

    def test_serialize_with_datetime(self):
        """Test serialization with datetime."""
        cache = RedisCache()
        original = {"date": datetime(2026, 1, 28, 12, 0, 0)}
        serialized = cache._serialize(original)
        deserialized = cache._deserialize(serialized)
        assert "date" in deserialized


class TestRedisCacheOperations:
    """Test basic cache operations."""

    @pytest.fixture
    async def cache(self):
        """Create a connected cache instance."""
        cache = RedisCache()
        mock_client = AsyncMock()
        cache._client = mock_client
        cache._connected = True
        return cache

    @pytest.mark.asyncio
    async def test_connect(self):
        """Test connection to Redis."""
        cache = RedisCache()
        with patch("redis.asyncio.from_url") as mock_from_url:
            mock_client = AsyncMock()
            mock_from_url.return_value = mock_client

            await cache.connect()
            assert cache._connected is True
            mock_from_url.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_import_error(self):
        """Test handling of missing redis package."""
        cache = RedisCache()
        with patch.dict("sys.modules", {"redis": None}):
            with pytest.raises(ImportError):
                await cache.connect()

    @pytest.mark.asyncio
    async def test_close(self):
        """Test closing connection."""
        cache = RedisCache()
        mock_client = AsyncMock()
        cache._client = mock_client
        cache._connected = True

        await cache.close()
        assert cache._connected is False
        mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test async context manager."""
        with patch("redis.asyncio.from_url") as mock_from_url:
            mock_client = AsyncMock()
            mock_from_url.return_value = mock_client

            async with RedisCache() as cache:
                assert cache._connected is True

    @pytest.mark.asyncio
    async def test_get_not_connected(self):
        """Test get when not connected."""
        cache = RedisCache()
        with pytest.raises(RuntimeError, match="not connected"):
            await cache.get("key")

    @pytest.mark.asyncio
    async def test_get_cache_hit(self):
        """Test cache hit."""
        cache = RedisCache()
        mock_client = AsyncMock()
        data = cache._serialize({"data": "value"})
        mock_client.get.return_value = data
        cache._client = mock_client
        cache._connected = True

        result = await cache.get("key")
        assert result == {"data": "value"}
        assert cache._hits == 1

    @pytest.mark.asyncio
    async def test_get_cache_miss(self):
        """Test cache miss."""
        cache = RedisCache()
        mock_client = AsyncMock()
        mock_client.get.return_value = None
        cache._client = mock_client
        cache._connected = True

        result = await cache.get("key")
        assert result is None
        assert cache._misses == 1

    @pytest.mark.asyncio
    async def test_get_with_default(self):
        """Test get with default value."""
        cache = RedisCache()
        mock_client = AsyncMock()
        mock_client.get.return_value = None
        cache._client = mock_client
        cache._connected = True

        result = await cache.get("key", default="default_value")
        assert result == "default_value"

    @pytest.mark.asyncio
    async def test_get_error(self):
        """Test error handling in get."""
        cache = RedisCache()
        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("Redis error")
        cache._client = mock_client
        cache._connected = True

        result = await cache.get("key", default="fallback")
        assert result == "fallback"
        assert cache._errors == 1

    @pytest.mark.asyncio
    async def test_set_success(self):
        """Test successful set."""
        cache = RedisCache()
        mock_client = AsyncMock()
        mock_client.set.return_value = True
        cache._client = mock_client
        cache._connected = True

        result = await cache.set("key", {"data": "value"}, ttl=300)
        assert result is True

    @pytest.mark.asyncio
    async def test_set_nx_xx(self):
        """Test set with nx and xx flags."""
        cache = RedisCache()
        mock_client = AsyncMock()
        mock_client.set.return_value = True
        cache._client = mock_client
        cache._connected = True

        await cache.set("key", "value", nx=True)
        call_kwargs = mock_client.set.call_args[1]
        assert call_kwargs["nx"] is True

        await cache.set("key", "value", xx=True)
        call_kwargs = mock_client.set.call_args[1]
        assert call_kwargs["xx"] is True

    @pytest.mark.asyncio
    async def test_set_error(self):
        """Test error handling in set."""
        cache = RedisCache()
        mock_client = AsyncMock()
        mock_client.set.side_effect = Exception("Redis error")
        cache._client = mock_client
        cache._connected = True

        result = await cache.set("key", "value")
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_success(self):
        """Test successful delete."""
        cache = RedisCache()
        mock_client = AsyncMock()
        mock_client.delete.return_value = 1
        cache._client = mock_client
        cache._connected = True

        result = await cache.delete("key")
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_not_found(self):
        """Test delete when key not found."""
        cache = RedisCache()
        mock_client = AsyncMock()
        mock_client.delete.return_value = 0
        cache._client = mock_client
        cache._connected = True

        result = await cache.delete("key")
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_pattern(self):
        """Test delete by pattern."""
        cache = RedisCache()
        mock_client = AsyncMock()
        mock_client.scan_iter = MagicMock(return_value=AsyncIterator(["key1", "key2"]))
        cache._client = mock_client
        cache._connected = True

        result = await cache.delete_pattern("user:*")
        assert result == 2

    @pytest.mark.asyncio
    async def test_exists_true(self):
        """Test exists when key exists."""
        cache = RedisCache()
        mock_client = AsyncMock()
        mock_client.exists.return_value = 1
        cache._client = mock_client
        cache._connected = True

        result = await cache.exists("key")
        assert result is True

    @pytest.mark.asyncio
    async def test_exists_false(self):
        """Test exists when key doesn't exist."""
        cache = RedisCache()
        mock_client = AsyncMock()
        mock_client.exists.return_value = 0
        cache._client = mock_client
        cache._connected = True

        result = await cache.exists("key")
        assert result is False

    @pytest.mark.asyncio
    async def test_expire(self):
        """Test setting expiration."""
        cache = RedisCache()
        mock_client = AsyncMock()
        mock_client.expire.return_value = True
        cache._client = mock_client
        cache._connected = True

        result = await cache.expire("key", 300)
        assert result is True

    @pytest.mark.asyncio
    async def test_ttl(self):
        """Test getting TTL."""
        cache = RedisCache()
        mock_client = AsyncMock()
        mock_client.ttl.return_value = 300
        cache._client = mock_client
        cache._connected = True

        result = await cache.ttl("key")
        assert result == 300


class AsyncIterator:
    """Helper class for async iteration in tests."""

    def __init__(self, items):
        self.items = items

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self.items:
            raise StopAsyncIteration
        return self.items.pop(0)


class TestRedisCacheBatchOperations:
    """Test batch operations."""

    @pytest.mark.asyncio
    async def test_mget(self):
        """Test multi-get."""
        cache = RedisCache()
        mock_client = AsyncMock()
        data1 = cache._serialize({"key": "value1"})
        data2 = cache._serialize({"key": "value2"})
        mock_client.mget.return_value = [data1, None, data2]
        cache._client = mock_client
        cache._connected = True

        result = await cache.mget(["key1", "key2", "key3"])
        assert "key1" in result
        assert "key2" not in result
        assert "key3" in result

    @pytest.mark.asyncio
    async def test_mget_error(self):
        """Test error handling in mget."""
        cache = RedisCache()
        mock_client = AsyncMock()
        mock_client.mget.side_effect = Exception("Redis error")
        cache._client = mock_client
        cache._connected = True

        result = await cache.mget(["key1", "key2"])
        assert result == {}

    @pytest.mark.asyncio
    async def test_mset(self):
        """Test multi-set."""
        cache = RedisCache()
        mock_client = AsyncMock()
        mock_pipeline = AsyncMock()
        # Mock setex and set as AsyncMock (coroutines)
        mock_pipeline.setex = AsyncMock(return_value=True)
        mock_pipeline.set = AsyncMock(return_value=True)
        mock_pipeline.execute = AsyncMock(return_value=[True, True])
        # pipeline() should return the mock_pipeline (use MagicMock, not AsyncMock)
        mock_client.pipeline = MagicMock(return_value=mock_pipeline)
        cache._client = mock_client
        cache._connected = True

        result = await cache.mset({"key1": "value1", "key2": "value2"}, ttl=300)
        assert result is True
        mock_pipeline.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_mset_error(self):
        """Test error handling in mset."""
        cache = RedisCache()
        mock_client = AsyncMock()
        mock_pipeline = AsyncMock()
        mock_pipeline.execute = AsyncMock(side_effect=Exception("Redis error"))
        mock_client.pipeline.return_value = mock_pipeline
        cache._client = mock_client
        cache._connected = True

        result = await cache.mset({"key1": "value1"})
        assert result is False


class TestRedisCacheRateLimiting:
    """Test rate limiting functionality."""

    @pytest.mark.asyncio
    async def test_check_rate_limit_allowed(self):
        """Test rate limit check when allowed."""
        cache = RedisCache()
        mock_client = AsyncMock()
        mock_pipeline = AsyncMock()
        mock_pipeline.execute = AsyncMock(return_value=[0, 5, 1, 1])  # removed, count, added, expire
        mock_client.pipeline = MagicMock(return_value=mock_pipeline)
        cache._client = mock_client
        cache._connected = True

        allowed, remaining = await cache.check_rate_limit("user:123", limit=100, window=60)
        assert allowed is True
        assert remaining == 94  # 100 - 5 - 1

    @pytest.mark.asyncio
    async def test_check_rate_limit_denied(self):
        """Test rate limit check when denied."""
        cache = RedisCache()
        mock_client = AsyncMock()
        mock_pipeline = AsyncMock()
        mock_pipeline.execute = AsyncMock(return_value=[0, 100, 1, 1])  # At limit
        mock_client.pipeline = MagicMock(return_value=mock_pipeline)
        cache._client = mock_client
        cache._connected = True

        allowed, remaining = await cache.check_rate_limit("user:123", limit=100, window=60)
        assert allowed is False
        assert remaining == 0

    @pytest.mark.asyncio
    async def test_check_rate_limit_with_cost(self):
        """Test rate limit with custom cost."""
        cache = RedisCache()
        mock_client = AsyncMock()
        mock_pipeline = AsyncMock()
        mock_pipeline.execute = AsyncMock(return_value=[0, 5, 1, 1])
        mock_client.pipeline = MagicMock(return_value=mock_pipeline)
        cache._client = mock_client
        cache._connected = True

        allowed, remaining = await cache.check_rate_limit(
            "user:123", limit=100, window=60, cost=10
        )
        assert remaining == 85  # 100 - 5 - 10

    @pytest.mark.asyncio
    async def test_check_rate_limit_error(self):
        """Test rate limit error handling."""
        cache = RedisCache()
        mock_client = AsyncMock()
        mock_client.pipeline.side_effect = Exception("Redis error")
        cache._client = mock_client
        cache._connected = True

        allowed, remaining = await cache.check_rate_limit("user:123", limit=100, window=60)
        # Fail open
        assert allowed is True
        assert remaining == 100

    @pytest.mark.asyncio
    async def test_get_rate_limit_status(self):
        """Test getting rate limit status."""
        cache = RedisCache()
        mock_client = AsyncMock()
        mock_pipeline = AsyncMock()
        mock_pipeline.execute = AsyncMock(return_value=[0, 50, [("123:1", 1234567890)]])
        mock_client.pipeline = MagicMock(return_value=mock_pipeline)
        cache._client = mock_client
        cache._connected = True

        status = await cache.get_rate_limit_status("user:123", limit=100, window=60)
        assert status["used"] == 50
        assert status["remaining"] == 50
        assert status["limit"] == 100

    @pytest.mark.asyncio
    async def test_get_rate_limit_status_error(self):
        """Test error handling in get_rate_limit_status."""
        cache = RedisCache()
        mock_client = AsyncMock()
        mock_client.pipeline.side_effect = Exception("Redis error")
        cache._client = mock_client
        cache._connected = True

        status = await cache.get_rate_limit_status("user:123", limit=100, window=60)
        assert status["remaining"] == 100


class TestRedisCacheHealthCheck:
    """Test health check functionality."""

    @pytest.mark.asyncio
    async def test_health_check_healthy(self):
        """Test healthy status."""
        cache = RedisCache()
        mock_client = AsyncMock()
        cache._client = mock_client
        cache._connected = True
        cache._hits = 80
        cache._misses = 20

        result = await cache.health_check()
        assert result["healthy"] is True
        assert result["latency_ms"] is not None
        assert result["hit_rate"] == 80.0

    @pytest.mark.asyncio
    async def test_health_check_not_connected(self):
        """Test health check when not connected."""
        cache = RedisCache()
        result = await cache.health_check()
        assert result["healthy"] is False
        assert result["connected"] is False

    @pytest.mark.asyncio
    async def test_health_check_ping_error(self):
        """Test health check when ping fails."""
        cache = RedisCache()
        mock_client = AsyncMock()
        mock_client.ping.side_effect = Exception("Ping failed")
        cache._client = mock_client
        cache._connected = True

        result = await cache.health_check()
        assert result["healthy"] is False
        assert "error" in result


class TestRedisCacheGetOrSet:
    """Test get_or_set functionality."""

    @pytest.mark.asyncio
    async def test_get_or_set_cache_hit(self):
        """Test get_or_set when value is cached."""
        cache = RedisCache()
        mock_client = AsyncMock()
        data = cache._serialize({"data": "cached"})
        mock_client.get.return_value = data
        cache._client = mock_client
        cache._connected = True

        async def factory():
            return {"data": "new"}

        result = await cache.get_or_set("key", factory)
        assert result == {"data": "cached"}

    @pytest.mark.asyncio
    async def test_get_or_set_cache_miss(self):
        """Test get_or_set when value is not cached."""
        cache = RedisCache()
        mock_client = AsyncMock()
        mock_client.get.return_value = None
        mock_client.set.side_effect = [True, True]  # lock, value
        mock_client.delete.return_value = True
        cache._client = mock_client
        cache._connected = True

        async def factory():
            return {"data": "new"}

        result = await cache.get_or_set("key", factory)
        assert result == {"data": "new"}

    @pytest.mark.asyncio
    async def test_get_or_set_sync_factory(self):
        """Test get_or_set with sync factory function."""
        cache = RedisCache()
        mock_client = AsyncMock()
        mock_client.get.return_value = None
        mock_client.set.side_effect = [True, True]
        mock_client.delete.return_value = True
        cache._client = mock_client
        cache._connected = True

        def sync_factory():
            return {"data": "sync"}

        result = await cache.get_or_set("key", sync_factory)
        assert result == {"data": "sync"}

    @pytest.mark.asyncio
    async def test_get_or_set_lock_wait(self):
        """Test get_or_set waiting for lock."""
        cache = RedisCache()
        mock_client = AsyncMock()
        # First get returns None, second returns value (simulating another process)
        data = cache._serialize({"data": "other_process"})
        mock_client.get.side_effect = [None, None, None, data]
        mock_client.set.return_value = False  # Lock not acquired
        cache._client = mock_client
        cache._connected = True

        async def factory():
            return {"data": "new"}

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await cache.get_or_set("key", factory)
            assert result == {"data": "other_process"}


class TestRedisCacheMetrics:
    """Test metrics functionality."""

    def test_get_stats(self):
        """Test getting statistics."""
        cache = RedisCache()
        cache._hits = 80
        cache._misses = 20

        stats = cache.get_stats()
        assert stats["hits"] == 80
        assert stats["misses"] == 20
        assert stats["total_requests"] == 100
        assert stats["hit_rate"] == 80.0

    def test_get_stats_no_requests(self):
        """Test stats when no requests made."""
        cache = RedisCache()
        stats = cache.get_stats()
        assert stats["hit_rate"] == 0

    def test_reset_stats(self):
        """Test resetting statistics."""
        cache = RedisCache()
        cache._hits = 80
        cache._misses = 20
        cache._errors = 5

        cache.reset_stats()
        assert cache._hits == 0
        assert cache._misses == 0
        assert cache._errors == 0

    @pytest.mark.asyncio
    async def test_metrics_callback(self):
        """Test custom metrics callback."""
        callback_calls = []

        def metrics_callback(**kwargs):
            callback_calls.append(kwargs)

        cache = RedisCache(
            namespace="test",
            metrics_callback=metrics_callback,
        )
        mock_client = AsyncMock()
        data = cache._serialize({"key": "value"})
        mock_client.get.return_value = data
        cache._client = mock_client
        cache._connected = True

        await cache.get("mykey")
        assert len(callback_calls) == 1
        assert callback_calls[0]["operation"] == "hit"

    @pytest.mark.asyncio
    async def test_metrics_callback_error(self):
        """Test error handling in metrics callback."""
        def failing_callback(**kwargs):
            raise ValueError("Callback error")

        cache = RedisCache(
            namespace="test",
            metrics_callback=failing_callback,
        )
        mock_client = AsyncMock()
        data = cache._serialize({"key": "value"})
        mock_client.get.return_value = data
        cache._client = mock_client
        cache._connected = True

        # Should not raise
        await cache.get("mykey")
