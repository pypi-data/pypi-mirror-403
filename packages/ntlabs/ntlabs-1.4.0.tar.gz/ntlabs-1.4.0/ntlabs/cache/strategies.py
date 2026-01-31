"""
Cache strategies and utilities.

Provides various caching strategies:
- LRU (Least Recently Used) - in-memory fallback
- TTL-based expiration
- Write-through and write-behind patterns
"""

import asyncio
import logging
import threading
from collections import OrderedDict
from collections import OrderedDict as OD
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


class LRUCache:
    """
    Thread-safe in-memory LRU cache.

    Useful as a local cache layer in front of Redis to reduce
    network calls for frequently accessed data.

    Example:
        cache = LRUCache(max_size=1000, default_ttl=60)

        cache.set("key", "value")
        value = cache.get("key")
        cache.delete("key")
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: int | None = None,
    ):
        """
        Initialize LRU cache.

        Args:
            max_size: Maximum number of items to store
            default_ttl: Default TTL in seconds (None = no expiry)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict = OD()
        self._expiry: dict[str, datetime] = {}
        self._lock = threading.RLock()

        # Stats
        self._hits = 0
        self._misses = 0

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        with self._lock:
            # Check if key exists
            if key not in self._cache:
                self._misses += 1
                return default

            # Check expiry
            if key in self._expiry:
                if datetime.utcnow() > self._expiry[key]:
                    # Expired, remove and return default
                    self._remove(key)
                    self._misses += 1
                    return default

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            return self._cache[key]

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache."""
        with self._lock:
            # Remove if exists (to update position)
            if key in self._cache:
                self._remove(key)

            # Add to cache
            self._cache[key] = value

            # Set expiry
            effective_ttl = ttl if ttl is not None else self.default_ttl
            if effective_ttl:
                self._expiry[key] = datetime.utcnow() + timedelta(seconds=effective_ttl)

            # Evict if over capacity
            while len(self._cache) > self.max_size:
                # Remove oldest (first item)
                oldest_key = next(iter(self._cache))
                self._remove(oldest_key)

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        with self._lock:
            if key in self._cache:
                self._remove(key)
                return True
            return False

    def _remove(self, key: str) -> None:
        """Remove key (internal, assumes lock held)."""
        if key in self._cache:
            del self._cache[key]
        if key in self._expiry:
            del self._expiry[key]

    def clear(self) -> None:
        """Clear all items from cache."""
        with self._lock:
            self._cache.clear()
            self._expiry.clear()

    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        return self.get(key) is not None

    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total = self._hits + self._misses
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": (self._hits / total * 100) if total > 0 else 0,
        }

    def cleanup_expired(self) -> int:
        """Remove all expired entries. Returns count of removed entries."""
        now = datetime.utcnow()
        removed = 0

        with self._lock:
            expired_keys = [k for k, expiry in self._expiry.items() if now > expiry]
            for key in expired_keys:
                self._remove(key)
                removed += 1

        return removed


class TieredCache:
    """
    Two-tier cache: local LRU + remote Redis.

    Checks local cache first, falls back to Redis.
    Useful for reducing Redis calls for hot data.

    Example:
        tiered = TieredCache(
            local_size=100,
            local_ttl=60,
            redis_cache=redis_cache,
        )

        value = await tiered.get("key")
        await tiered.set("key", "value")
    """

    def __init__(
        self,
        redis_cache: Any,
        local_size: int = 1000,
        local_ttl: int = 60,
    ):
        """
        Initialize tiered cache.

        Args:
            redis_cache: RedisCache instance
            local_size: Max items in local cache
            local_ttl: TTL for local cache (should be < Redis TTL)
        """
        self.redis = redis_cache
        self.local = LRUCache(max_size=local_size, default_ttl=local_ttl)
        self.local_ttl = local_ttl

    async def get(self, key: str, default: Any = None) -> Any:
        """Get from local cache, fallback to Redis."""
        # Check local first
        value = self.local.get(key)
        if value is not None:
            return value

        # Check Redis
        value = await self.redis.get(key)
        if value is not None:
            # Populate local cache
            self.local.set(key, value, ttl=self.local_ttl)
            return value

        return default

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Set in both local and Redis cache."""
        # Set in Redis first
        result = await self.redis.set(key, value, ttl=ttl)

        # Set in local cache with shorter TTL
        local_ttl = min(self.local_ttl, ttl) if ttl else self.local_ttl
        self.local.set(key, value, ttl=local_ttl)

        return result

    async def delete(self, key: str) -> bool:
        """Delete from both caches."""
        self.local.delete(key)
        return await self.redis.delete(key)

    async def invalidate_local(self, key: str) -> None:
        """Invalidate only local cache (useful for pub/sub invalidation)."""
        self.local.delete(key)

    def get_stats(self) -> dict[str, Any]:
        """Get statistics for both cache layers."""
        return {
            "local": self.local.get_stats(),
            "redis": self.redis.get_stats(),
        }


class WriteThrough:
    """
    Write-through cache strategy.

    Writes go to both cache and database synchronously.

    Example:
        wt = WriteThrough(
            cache=redis_cache,
            db_writer=lambda k, v: db.update(k, v),
        )

        await wt.write("user:123", user_data)
    """

    def __init__(
        self,
        cache: Any,
        db_writer: Callable,
        ttl: int | None = None,
    ):
        """
        Initialize write-through cache.

        Args:
            cache: Cache instance (RedisCache or similar)
            db_writer: Async function to write to database
            ttl: Cache TTL
        """
        self.cache = cache
        self.db_writer = db_writer
        self.ttl = ttl

    async def write(self, key: str, value: Any) -> bool:
        """Write to both cache and database."""
        try:
            # Write to database first
            if asyncio.iscoroutinefunction(self.db_writer):
                await self.db_writer(key, value)
            else:
                self.db_writer(key, value)

            # Write to cache
            await self.cache.set(key, value, ttl=self.ttl)
            return True

        except Exception as e:
            logger.error(f"Write-through error for {key}: {e}")
            # Try to invalidate cache on DB write failure
            await self.cache.delete(key)
            raise

    async def read(self, key: str, db_reader: Callable) -> Any:
        """Read from cache, fallback to database."""
        value = await self.cache.get(key)
        if value is not None:
            return value

        # Read from database
        if asyncio.iscoroutinefunction(db_reader):
            value = await db_reader(key)
        else:
            value = db_reader(key)

        # Populate cache
        if value is not None:
            await self.cache.set(key, value, ttl=self.ttl)

        return value


class WriteBehind:
    """
    Write-behind (write-back) cache strategy.

    Writes go to cache immediately, database writes are queued
    and executed asynchronously.

    Example:
        wb = WriteBehind(
            cache=redis_cache,
            db_writer=lambda items: db.bulk_update(items),
            flush_interval=5,
            max_batch_size=100,
        )

        await wb.start()
        await wb.write("user:123", user_data)
        # ... database write happens in background
        await wb.stop()
    """

    def __init__(
        self,
        cache: Any,
        db_writer: Callable,
        ttl: int | None = None,
        flush_interval: float = 5.0,
        max_batch_size: int = 100,
    ):
        """
        Initialize write-behind cache.

        Args:
            cache: Cache instance
            db_writer: Async function that accepts list of (key, value) tuples
            ttl: Cache TTL
            flush_interval: Seconds between database flushes
            max_batch_size: Max items before forced flush
        """
        self.cache = cache
        self.db_writer = db_writer
        self.ttl = ttl
        self.flush_interval = flush_interval
        self.max_batch_size = max_batch_size

        self._queue: dict[str, Any] = {}
        self._lock = asyncio.Lock()
        self._task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        """Start background flush task."""
        self._running = True
        self._task = asyncio.create_task(self._flush_loop())
        logger.info("Write-behind cache started")

    async def stop(self) -> None:
        """Stop background flush task and flush remaining items."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        # Final flush
        await self._flush()
        logger.info("Write-behind cache stopped")

    async def write(self, key: str, value: Any) -> bool:
        """Write to cache and queue for database."""
        # Write to cache immediately
        await self.cache.set(key, value, ttl=self.ttl)

        # Queue for database
        async with self._lock:
            self._queue[key] = value

            # Force flush if queue is full
            if len(self._queue) >= self.max_batch_size:
                await self._flush()

        return True

    async def _flush_loop(self) -> None:
        """Background task to periodically flush queue."""
        while self._running:
            await asyncio.sleep(self.flush_interval)
            await self._flush()

    async def _flush(self) -> None:
        """Flush queued items to database."""
        async with self._lock:
            if not self._queue:
                return

            items = list(self._queue.items())
            self._queue.clear()

        try:
            if asyncio.iscoroutinefunction(self.db_writer):
                await self.db_writer(items)
            else:
                self.db_writer(items)
            logger.debug(f"Flushed {len(items)} items to database")

        except Exception as e:
            logger.error(f"Write-behind flush error: {e}")
            # Re-queue failed items
            async with self._lock:
                for key, value in items:
                    if key not in self._queue:
                        self._queue[key] = value
