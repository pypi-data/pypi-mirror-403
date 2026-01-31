"""
NTLabs Cache - Redis caching utilities.

This module provides a high-level Redis cache interface with:
- Namespace support for multi-tenant applications
- Connection pooling
- Compression for large values
- Rate limiting
- Decorators for easy caching
- Various caching strategies (LRU, write-through, write-behind)

Quick Start:
    from ntlabs.cache import RedisCache, cached

    # Create cache instance
    cache = RedisCache(
        url="redis://localhost:6379",
        namespace="myapp",
        default_ttl=3600,
    )

    # Connect
    await cache.connect()

    # Basic operations
    await cache.set("user:123", {"name": "John"}, ttl=300)
    user = await cache.get("user:123")
    await cache.delete("user:123")

    # Rate limiting
    allowed, remaining = await cache.check_rate_limit(
        identifier="user:123",
        limit=100,
        window=60,
    )

    # With decorator
    @cached(cache=cache, prefix="users", ttl=3600)
    async def get_user(user_id: str):
        return await db.fetch_user(user_id)

    # Close when done
    await cache.close()

Context Manager:
    async with RedisCache(url="redis://localhost:6379") as cache:
        await cache.set("key", "value")
        value = await cache.get("key")
"""

from .decorators import (
    cache_aside,
    cache_invalidate,
    cached,
)
from .redis import RedisCache
from .strategies import (
    LRUCache,
    TieredCache,
    WriteBehind,
    WriteThrough,
)

# Global default cache (can be set by application)
_default_cache: RedisCache = None


def set_default_cache(cache: RedisCache) -> None:
    """
    Set the default cache instance for decorators.

    Args:
        cache: RedisCache instance to use as default

    Example:
        from ntlabs.cache import RedisCache, set_default_cache, cached

        cache = RedisCache(url="redis://localhost:6379")
        await cache.connect()
        set_default_cache(cache)

        # Now decorators will use this cache automatically
        @cached(prefix="users", ttl=3600)
        async def get_user(user_id: str):
            return await db.fetch_user(user_id)
    """
    global _default_cache
    _default_cache = cache


def get_default_cache() -> RedisCache:
    """Get the default cache instance."""
    return _default_cache


__all__ = [
    # Main class
    "RedisCache",
    # Decorators
    "cached",
    "cache_invalidate",
    "cache_aside",
    # Strategies
    "LRUCache",
    "TieredCache",
    "WriteThrough",
    "WriteBehind",
    # Global cache
    "set_default_cache",
    "get_default_cache",
]
