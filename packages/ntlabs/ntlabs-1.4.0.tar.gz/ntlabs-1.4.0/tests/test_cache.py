"""
Tests for ntlabs.cache module.

Tests LRU cache, strategies, and decorators.
Note: Redis tests require a running Redis instance.
"""

import time

import pytest

from ntlabs.cache import (
    LRUCache,
)

# =============================================================================
# LRU Cache Tests
# =============================================================================


class TestLRUCache:
    """Tests for LRU cache."""

    def test_basic_set_get(self):
        """Test basic set and get."""
        cache = LRUCache(max_size=10)
        cache.set("key", "value")
        assert cache.get("key") == "value"

    def test_get_default(self):
        """Test get with default."""
        cache = LRUCache(max_size=10)
        assert cache.get("nonexistent", "default") == "default"

    def test_delete(self):
        """Test delete operation."""
        cache = LRUCache(max_size=10)
        cache.set("key", "value")
        assert cache.delete("key") is True
        assert cache.get("key") is None

    def test_delete_nonexistent(self):
        """Test deleting nonexistent key."""
        cache = LRUCache(max_size=10)
        assert cache.delete("nonexistent") is False

    def test_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = LRUCache(max_size=3)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)

        # Access 'a' to make it recently used
        cache.get("a")

        # Add new item, should evict 'b' (least recently used)
        cache.set("d", 4)

        assert cache.get("a") == 1  # Still exists
        assert cache.get("b") is None  # Evicted
        assert cache.get("c") == 3
        assert cache.get("d") == 4

    def test_ttl_expiry(self):
        """Test TTL expiration."""
        cache = LRUCache(max_size=10, default_ttl=1)
        cache.set("key", "value")

        # Should exist immediately
        assert cache.get("key") == "value"

        # Wait for expiry
        time.sleep(1.1)

        # Should be expired
        assert cache.get("key") is None

    def test_explicit_ttl(self):
        """Test explicit TTL override."""
        cache = LRUCache(max_size=10, default_ttl=10)
        cache.set("key", "value", ttl=1)

        # Wait for explicit TTL
        time.sleep(1.1)

        assert cache.get("key") is None

    def test_clear(self):
        """Test clear operation."""
        cache = LRUCache(max_size=10)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()

        assert cache.get("a") is None
        assert cache.get("b") is None
        assert cache.size() == 0

    def test_exists(self):
        """Test exists check."""
        cache = LRUCache(max_size=10)
        cache.set("key", "value")

        assert cache.exists("key") is True
        assert cache.exists("nonexistent") is False

    def test_size(self):
        """Test size tracking."""
        cache = LRUCache(max_size=10)
        assert cache.size() == 0

        cache.set("a", 1)
        cache.set("b", 2)
        assert cache.size() == 2

        cache.delete("a")
        assert cache.size() == 1

    def test_stats(self):
        """Test statistics tracking."""
        cache = LRUCache(max_size=10)

        cache.set("key", "value")
        cache.get("key")  # Hit
        cache.get("nonexistent")  # Miss

        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 50.0

    def test_cleanup_expired(self):
        """Test expired entry cleanup."""
        cache = LRUCache(max_size=10)
        cache.set("short", "value", ttl=1)
        cache.set("long", "value", ttl=10)

        time.sleep(1.1)

        removed = cache.cleanup_expired()
        assert removed == 1
        assert cache.get("short") is None
        assert cache.get("long") == "value"

    def test_thread_safety(self):
        """Test thread safety of LRU cache."""
        import threading

        cache = LRUCache(max_size=100)
        errors = []

        def writer():
            try:
                for i in range(100):
                    cache.set(f"key_{i}", i)
            except Exception as e:
                errors.append(e)

        def reader():
            try:
                for i in range(100):
                    cache.get(f"key_{i}")
            except Exception as e:
                errors.append(e)

        threads = []
        for _ in range(5):
            threads.append(threading.Thread(target=writer))
            threads.append(threading.Thread(target=reader))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


# =============================================================================
# Cache Decorator Tests (Mock)
# =============================================================================


class TestCacheDecorators:
    """Tests for cache decorators with mocked cache."""

    def test_make_cache_key(self):
        """Test cache key generation."""
        from ntlabs.cache.decorators import _make_cache_key

        def sample_func(a, b):
            pass

        key = _make_cache_key("prefix", sample_func, (1, 2), {})
        assert "prefix:" in key
        assert "sample_func" in key

    def test_make_cache_key_with_kwargs(self):
        """Test cache key with kwargs."""
        from ntlabs.cache.decorators import _make_cache_key

        def sample_func(a, b=None):
            pass

        key1 = _make_cache_key("prefix", sample_func, (1,), {"b": 2})
        key2 = _make_cache_key("prefix", sample_func, (1,), {"b": 3})

        # Different kwargs should produce different keys
        assert key1 != key2

    def test_custom_key_builder(self):
        """Test custom key builder."""
        from ntlabs.cache.decorators import _make_cache_key

        def sample_func(user_id):
            pass

        def key_builder(user_id):
            return f"user:{user_id}"

        key = _make_cache_key("prefix", sample_func, ("123",), {}, key_builder)
        assert key == "prefix:user:123"


# =============================================================================
# Note: Redis integration tests would require a running Redis instance
# and would be marked with @pytest.mark.integration
# =============================================================================


class TestRedisCache:
    """Tests for Redis cache (require Redis instance)."""

    @pytest.mark.skip(reason="Requires Redis instance")
    async def test_redis_basic_operations(self):
        """Test basic Redis operations."""
        from ntlabs.cache import RedisCache

        async with RedisCache(url="redis://localhost:6379", namespace="test") as cache:
            await cache.set("key", {"data": "value"})
            result = await cache.get("key")
            assert result == {"data": "value"}

            await cache.delete("key")
            assert await cache.get("key") is None

    @pytest.mark.skip(reason="Requires Redis instance")
    async def test_redis_rate_limiting(self):
        """Test Redis rate limiting."""
        from ntlabs.cache import RedisCache

        async with RedisCache(url="redis://localhost:6379", namespace="test") as cache:
            # Should be allowed
            allowed, remaining = await cache.check_rate_limit(
                "user:123", limit=5, window=60
            )
            assert allowed is True
            assert remaining == 4

            # Use up remaining
            for _ in range(4):
                await cache.check_rate_limit("user:123", limit=5, window=60)

            # Should be blocked
            allowed, remaining = await cache.check_rate_limit(
                "user:123", limit=5, window=60
            )
            assert allowed is False
