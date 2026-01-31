"""
Neural LAB Python SDK - Test Suite

Author: Anderson Henrique da Silva
Date: 2026-01-28
Location: Minas Gerais, Brasil
Copyright: Neural Thinker | AI Engineering LTDA

Description: Comprehensive tests for cache strategies module
Version: 1.0.0
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from ntlabs.cache.strategies import (
    LRUCache,
    TieredCache,
    WriteThrough,
    WriteBehind,
)


class TestLRUCache:
    """Test LRUCache implementation."""

    def test_init(self):
        """Test initialization."""
        cache = LRUCache(max_size=100, default_ttl=60)
        assert cache.max_size == 100
        assert cache.default_ttl == 60
        assert cache.size() == 0

    def test_get_existing_key(self):
        """Test getting existing key."""
        cache = LRUCache()
        cache.set("key", "value")
        assert cache.get("key") == "value"

    def test_get_nonexistent_key(self):
        """Test getting non-existent key."""
        cache = LRUCache()
        assert cache.get("key") is None

    def test_get_with_default(self):
        """Test getting with default value."""
        cache = LRUCache()
        assert cache.get("key", default="default") == "default"

    def test_set_and_overwrite(self):
        """Test setting and overwriting values."""
        cache = LRUCache()
        cache.set("key", "value1")
        cache.set("key", "value2")
        assert cache.get("key") == "value2"

    def test_set_with_ttl(self):
        """Test setting with custom TTL."""
        cache = LRUCache()
        cache.set("key", "value", ttl=1)
        assert cache.get("key") == "value"

    def test_expired_entry(self):
        """Test that expired entries are removed."""
        cache = LRUCache()
        # Set with negative TTL to simulate expiration
        cache.set("key", "value", ttl=-1)
        assert cache.get("key") is None

    def test_lru_eviction(self):
        """Test LRU eviction when max size reached."""
        cache = LRUCache(max_size=2)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")  # Should evict key1

        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"

    def test_lru_order_update(self):
        """Test that accessing updates LRU order."""
        cache = LRUCache(max_size=2)
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        # Access key1 to make it most recently used
        cache.get("key1")

        # Add key3, should evict key2 (least recently used)
        cache.set("key3", "value3")

        assert cache.get("key1") == "value1"
        assert cache.get("key2") is None
        assert cache.get("key3") == "value3"

    def test_delete_existing(self):
        """Test deleting existing key."""
        cache = LRUCache()
        cache.set("key", "value")
        assert cache.delete("key") is True
        assert cache.get("key") is None

    def test_delete_nonexistent(self):
        """Test deleting non-existent key."""
        cache = LRUCache()
        assert cache.delete("key") is False

    def test_clear(self):
        """Test clearing all entries."""
        cache = LRUCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert cache.size() == 0
        assert cache.get("key1") is None

    def test_exists_true(self):
        """Test exists when key exists."""
        cache = LRUCache()
        cache.set("key", "value")
        assert cache.exists("key") is True

    def test_exists_false(self):
        """Test exists when key doesn't exist."""
        cache = LRUCache()
        assert cache.exists("key") is False

    def test_exists_expired(self):
        """Test exists when key is expired."""
        cache = LRUCache()
        cache.set("key", "value", ttl=-1)
        assert cache.exists("key") is False

    def test_size(self):
        """Test getting cache size."""
        cache = LRUCache()
        assert cache.size() == 0
        cache.set("key1", "value1")
        assert cache.size() == 1
        cache.set("key2", "value2")
        assert cache.size() == 2

    def test_get_stats(self):
        """Test getting statistics."""
        cache = LRUCache()
        cache.get("nonexistent")
        cache.set("key", "value")
        cache.get("key")
        cache.get("key")

        stats = cache.get_stats()
        assert stats["size"] == 1
        assert stats["max_size"] == 1000
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert abs(stats["hit_rate"] - 66.67) < 0.01

    def test_cleanup_expired(self):
        """Test cleanup of expired entries."""
        cache = LRUCache()
        cache.set("key1", "value1", ttl=-1)  # Expired
        cache.set("key2", "value2")  # No TTL

        removed = cache.cleanup_expired()
        assert removed == 1
        assert cache.size() == 1

    def test_cleanup_expired_none(self):
        """Test cleanup when no expired entries."""
        cache = LRUCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        removed = cache.cleanup_expired()
        assert removed == 0
        assert cache.size() == 2

    def test_thread_safety(self):
        """Test basic thread safety with concurrent access."""
        import threading

        cache = LRUCache(max_size=100)
        results = []

        def worker(n):
            for i in range(10):
                cache.set(f"key_{n}_{i}", f"value_{i}")
                val = cache.get(f"key_{n}_{i}")
                results.append(val)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 50


class TestTieredCache:
    """Test TieredCache implementation."""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis cache."""
        redis = AsyncMock()
        redis.get = AsyncMock(return_value=None)
        redis.set = AsyncMock(return_value=True)
        redis.delete = AsyncMock(return_value=True)
        redis.get_stats = MagicMock(return_value={"hits": 0})
        return redis

    @pytest.mark.asyncio
    async def test_get_from_local(self, mock_redis):
        """Test getting from local cache."""
        tiered = TieredCache(redis_cache=mock_redis, local_size=10, local_ttl=60)
        tiered.local.set("key", "local_value")

        result = await tiered.get("key")
        assert result == "local_value"
        mock_redis.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_from_redis(self, mock_redis):
        """Test getting from Redis when not in local."""
        mock_redis.get.return_value = "redis_value"
        tiered = TieredCache(redis_cache=mock_redis, local_size=10, local_ttl=60)

        result = await tiered.get("key")
        assert result == "redis_value"
        # Should populate local cache
        assert tiered.local.get("key") == "redis_value"

    @pytest.mark.asyncio
    async def test_get_not_found(self, mock_redis):
        """Test when key not found in either cache."""
        mock_redis.get.return_value = None
        tiered = TieredCache(redis_cache=mock_redis)

        result = await tiered.get("key")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_with_default(self, mock_redis):
        """Test getting with default value."""
        mock_redis.get.return_value = None
        tiered = TieredCache(redis_cache=mock_redis)

        result = await tiered.get("key", default="default")
        assert result == "default"

    @pytest.mark.asyncio
    async def test_set_both_caches(self, mock_redis):
        """Test setting in both caches."""
        tiered = TieredCache(redis_cache=mock_redis, local_ttl=30)

        result = await tiered.set("key", "value", ttl=60)
        assert result is True
        mock_redis.set.assert_called_once()
        assert tiered.local.get("key") == "value"

    @pytest.mark.asyncio
    async def test_delete_both_caches(self, mock_redis):
        """Test deleting from both caches."""
        tiered = TieredCache(redis_cache=mock_redis)
        tiered.local.set("key", "value")

        result = await tiered.delete("key")
        assert result is True
        mock_redis.delete.assert_called_once()
        assert tiered.local.get("key") is None

    @pytest.mark.asyncio
    async def test_invalidate_local(self, mock_redis):
        """Test invalidating only local cache."""
        tiered = TieredCache(redis_cache=mock_redis)
        tiered.local.set("key", "value")

        await tiered.invalidate_local("key")
        assert tiered.local.get("key") is None

    def test_get_stats(self, mock_redis):
        """Test getting statistics."""
        tiered = TieredCache(redis_cache=mock_redis)
        tiered.local.set("key", "value")
        tiered.local.get("key")

        stats = tiered.get_stats()
        assert "local" in stats
        assert "redis" in stats


class TestWriteThrough:
    """Test WriteThrough implementation."""

    @pytest.fixture
    def mock_cache(self):
        """Create a mock cache."""
        cache = AsyncMock()
        cache.set = AsyncMock(return_value=True)
        cache.delete = AsyncMock(return_value=True)
        return cache

    @pytest.mark.asyncio
    async def test_write_success_async_db(self, mock_cache):
        """Test successful write with async DB writer."""
        db_calls = []

        async def db_writer(key, value):
            db_calls.append((key, value))

        wt = WriteThrough(cache=mock_cache, db_writer=db_writer, ttl=300)
        result = await wt.write("key", "value")

        assert result is True
        assert db_calls == [("key", "value")]
        mock_cache.set.assert_called_once_with("key", "value", ttl=300)

    @pytest.mark.asyncio
    async def test_write_success_sync_db(self, mock_cache):
        """Test successful write with sync DB writer."""
        db_calls = []

        def sync_db_writer(key, value):
            db_calls.append((key, value))

        wt = WriteThrough(cache=mock_cache, db_writer=sync_db_writer)
        result = await wt.write("key", "value")

        assert result is True
        assert db_calls == [("key", "value")]

    @pytest.mark.asyncio
    async def test_write_db_error(self, mock_cache):
        """Test handling DB write error."""
        async def failing_db_writer(key, value):
            raise ValueError("DB error")

        wt = WriteThrough(cache=mock_cache, db_writer=failing_db_writer)

        with pytest.raises(ValueError):
            await wt.write("key", "value")

        # Should delete from cache on error
        mock_cache.delete.assert_called_once_with("key")

    @pytest.mark.asyncio
    async def test_read_cache_hit(self, mock_cache):
        """Test read when value in cache."""
        mock_cache.get.return_value = "cached_value"

        wt = WriteThrough(cache=mock_cache, db_writer=None)
        result = await wt.read("key", db_reader=None)

        assert result == "cached_value"

    @pytest.mark.asyncio
    async def test_read_cache_miss_async(self, mock_cache):
        """Test read with cache miss and async DB reader."""
        mock_cache.get.return_value = None

        async def db_reader(key):
            return f"db_value_for_{key}"

        wt = WriteThrough(cache=mock_cache, db_writer=None, ttl=300)
        result = await wt.read("key", db_reader=db_reader)

        assert result == "db_value_for_key"
        mock_cache.set.assert_called_once_with("key", "db_value_for_key", ttl=300)

    @pytest.mark.asyncio
    async def test_read_cache_miss_sync(self, mock_cache):
        """Test read with cache miss and sync DB reader."""
        mock_cache.get.return_value = None

        def sync_db_reader(key):
            return f"db_value_for_{key}"

        wt = WriteThrough(cache=mock_cache, db_writer=None)
        result = await wt.read("key", db_reader=sync_db_reader)

        assert result == "db_value_for_key"

    @pytest.mark.asyncio
    async def test_read_db_returns_none(self, mock_cache):
        """Test read when DB returns None."""
        mock_cache.get.return_value = None

        async def db_reader(key):
            return None

        wt = WriteThrough(cache=mock_cache, db_writer=None)
        result = await wt.read("key", db_reader=db_reader)

        assert result is None
        # Should not cache None
        mock_cache.set.assert_not_called()


class TestWriteBehind:
    """Test WriteBehind implementation."""

    @pytest.fixture
    def mock_cache(self):
        """Create a mock cache."""
        cache = AsyncMock()
        cache.set = AsyncMock(return_value=True)
        return cache

    @pytest.fixture
    async def write_behind(self, mock_cache):
        """Create a WriteBehind instance."""
        async def db_writer(items):
            pass

        wb = WriteBehind(
            cache=mock_cache,
            db_writer=db_writer,
            flush_interval=1.0,
            max_batch_size=10,
        )
        return wb

    @pytest.mark.asyncio
    async def test_start_stop(self, mock_cache):
        """Test starting and stopping write-behind."""
        async def db_writer(items):
            pass

        wb = WriteBehind(cache=mock_cache, db_writer=db_writer)
        await wb.start()
        assert wb._running is True
        assert wb._task is not None

        await wb.stop()
        assert wb._running is False

    @pytest.mark.asyncio
    async def test_write_queues_data(self, mock_cache):
        """Test that write queues data."""
        async def db_writer(items):
            pass

        wb = WriteBehind(cache=mock_cache, db_writer=db_writer)
        await wb.start()

        await wb.write("key1", "value1")
        assert "key1" in wb._queue

        await wb.stop()

    @pytest.mark.asyncio
    async def test_write_triggers_flush(self, mock_cache):
        """Test that write triggers flush when batch is full."""
        flushed_items = []

        async def db_writer(items):
            flushed_items.extend(items)

        wb = WriteBehind(
            cache=mock_cache,
            db_writer=db_writer,
            max_batch_size=2,
        )

        await wb.write("key1", "value1")
        assert len(wb._queue) == 1

        await wb.write("key2", "value2")  # Should trigger flush
        assert len(wb._queue) == 0
        assert len(flushed_items) == 2

    @pytest.mark.asyncio
    async def test_flush_async_writer(self, mock_cache):
        """Test flushing with async DB writer."""
        flushed_items = []

        async def async_db_writer(items):
            flushed_items.extend(items)

        wb = WriteBehind(cache=mock_cache, db_writer=async_db_writer)
        await wb.write("key1", "value1")
        await wb._flush()

        assert len(flushed_items) == 1
        assert flushed_items[0] == ("key1", "value1")

    @pytest.mark.asyncio
    async def test_flush_sync_writer(self, mock_cache):
        """Test flushing with sync DB writer."""
        flushed_items = []

        def sync_db_writer(items):
            flushed_items.extend(items)

        wb = WriteBehind(cache=mock_cache, db_writer=sync_db_writer)
        await wb.write("key1", "value1")
        await wb._flush()

        assert len(flushed_items) == 1

    @pytest.mark.asyncio
    async def test_flush_error_requeue(self, mock_cache):
        """Test that failed items are re-queued."""
        call_count = 0

        async def failing_db_writer(items):
            nonlocal call_count
            call_count += 1
            raise ValueError("DB error")

        wb = WriteBehind(cache=mock_cache, db_writer=failing_db_writer)
        await wb.write("key1", "value1")
        await wb._flush()

        # Item should be re-queued
        assert "key1" in wb._queue

    @pytest.mark.asyncio
    async def test_flush_empty_queue(self, mock_cache):
        """Test flushing empty queue."""
        async def db_writer(items):
            pass

        wb = WriteBehind(cache=mock_cache, db_writer=db_writer)
        # Should not raise
        await wb._flush()

    @pytest.mark.asyncio
    async def test_flush_loop(self, mock_cache):
        """Test flush loop."""
        flushed_items = []

        async def db_writer(items):
            flushed_items.extend(items)

        wb = WriteBehind(
            cache=mock_cache,
            db_writer=db_writer,
            flush_interval=0.01,
        )

        await wb.start()
        await wb.write("key1", "value1")

        # Wait for flush loop
        await asyncio.sleep(0.05)

        await wb.stop()

        assert len(flushed_items) >= 1

    @pytest.mark.asyncio
    async def test_stop_final_flush(self, mock_cache):
        """Test final flush on stop."""
        flushed_items = []

        async def db_writer(items):
            flushed_items.extend(items)

        wb = WriteBehind(cache=mock_cache, db_writer=db_writer)
        await wb.write("key1", "value1")
        await wb.stop()

        assert len(flushed_items) == 1
