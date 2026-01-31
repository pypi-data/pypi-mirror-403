"""
Cache decorators for easy function result caching.

Provides decorators for:
- @cached: Cache function results
- @cache_invalidate: Invalidate cache on function call
- @cache_aside: Cache-aside pattern with automatic refresh
"""

import asyncio
import functools
import hashlib
import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


def _make_cache_key(
    prefix: str,
    func: Callable,
    args: tuple,
    kwargs: dict,
    key_builder: Callable | None = None,
) -> str:
    """Generate cache key from function and arguments."""
    if key_builder:
        return f"{prefix}:{key_builder(*args, **kwargs)}"

    # Default key builder
    func_name = f"{func.__module__}.{func.__qualname__}"

    # Create hash of arguments
    key_parts = [func_name]

    for arg in args:
        try:
            key_parts.append(str(arg))
        except Exception:
            key_parts.append(hashlib.md5(str(id(arg)).encode()).hexdigest()[:8])

    for k, v in sorted(kwargs.items()):
        try:
            key_parts.append(f"{k}={v}")
        except Exception:
            key_parts.append(f"{k}={hashlib.md5(str(id(v)).encode()).hexdigest()[:8]}")

    key_string = ":".join(key_parts)

    # Hash if too long
    if len(key_string) > 200:
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"{prefix}:{func_name}:{key_hash}"

    return f"{prefix}:{key_string}"


def cached(
    cache: Any = None,
    prefix: str = "cache",
    ttl: int | None = None,
    key_builder: Callable[..., str] | None = None,
    unless: Callable[..., bool] | None = None,
    cache_none: bool = False,
):
    """
    Decorator to cache function results.

    Args:
        cache: RedisCache instance (or will look for global cache)
        prefix: Cache key prefix
        ttl: Time-to-live in seconds
        key_builder: Custom function to build cache key from args
        unless: Callable that returns True to skip caching
        cache_none: Whether to cache None results

    Example:
        from ntlabs.cache import RedisCache, cached

        cache = RedisCache(url="redis://localhost:6379")

        @cached(cache=cache, prefix="users", ttl=3600)
        async def get_user(user_id: str):
            return await db.fetch_user(user_id)

        # With custom key builder
        @cached(cache=cache, key_builder=lambda u: f"user:{u.id}")
        async def get_user_profile(user):
            return await fetch_profile(user)
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Get cache instance
            cache_instance = cache
            if cache_instance is None:
                # Try to get from global
                import ntlabs.cache as cache_module

                cache_instance = getattr(cache_module, "_default_cache", None)

            if cache_instance is None:
                # No cache available, just call function
                return await func(*args, **kwargs)

            # Check unless condition
            if unless and unless(*args, **kwargs):
                return await func(*args, **kwargs)

            # Generate cache key
            cache_key = _make_cache_key(prefix, func, args, kwargs, key_builder)

            # Try to get from cache
            try:
                cached_value = await cache_instance.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"Cache hit for {cache_key}")
                    return cached_value
            except Exception as e:
                logger.warning(f"Cache get error: {e}")

            # Call function
            result = await func(*args, **kwargs)

            # Cache result
            if result is not None or cache_none:
                try:
                    await cache_instance.set(cache_key, result, ttl=ttl)
                    logger.debug(f"Cached {cache_key}")
                except Exception as e:
                    logger.warning(f"Cache set error: {e}")

            return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we need an event loop
            cache_instance = cache
            if cache_instance is None:
                import ntlabs.cache as cache_module

                cache_instance = getattr(cache_module, "_default_cache", None)

            if cache_instance is None:
                return func(*args, **kwargs)

            if unless and unless(*args, **kwargs):
                return func(*args, **kwargs)

            cache_key = _make_cache_key(prefix, func, args, kwargs, key_builder)

            # Try to run async operations
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, can't use sync wrapper properly
                    logger.warning(
                        f"Sync cached function {func.__name__} called from async context"
                    )
                    return func(*args, **kwargs)

                cached_value = loop.run_until_complete(cache_instance.get(cache_key))
                if cached_value is not None:
                    return cached_value

                result = func(*args, **kwargs)

                if result is not None or cache_none:
                    loop.run_until_complete(
                        cache_instance.set(cache_key, result, ttl=ttl)
                    )

                return result

            except RuntimeError:
                # No event loop available
                return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def cache_invalidate(
    cache: Any = None,
    prefix: str = "cache",
    key_builder: Callable[..., str] | None = None,
    keys: list[str] | None = None,
    patterns: list[str] | None = None,
):
    """
    Decorator to invalidate cache on function call.

    Args:
        cache: RedisCache instance
        prefix: Cache key prefix (used with key_builder)
        key_builder: Function to build cache key to invalidate
        keys: Specific keys to invalidate
        patterns: Patterns to invalidate (e.g., "user:*")

    Example:
        @cache_invalidate(cache=cache, prefix="users", key_builder=lambda uid: uid)
        async def update_user(user_id: str, data: dict):
            return await db.update_user(user_id, data)

        @cache_invalidate(cache=cache, patterns=["users:*"])
        async def clear_all_users():
            pass
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Call function first
            result = await func(*args, **kwargs)

            # Get cache instance
            cache_instance = cache
            if cache_instance is None:
                import ntlabs.cache as cache_module

                cache_instance = getattr(cache_module, "_default_cache", None)

            if cache_instance is None:
                return result

            # Invalidate specific keys
            if key_builder:
                cache_key = f"{prefix}:{key_builder(*args, **kwargs)}"
                try:
                    await cache_instance.delete(cache_key)
                    logger.debug(f"Invalidated {cache_key}")
                except Exception as e:
                    logger.warning(f"Cache invalidate error: {e}")

            # Invalidate specific keys
            if keys:
                for key in keys:
                    try:
                        await cache_instance.delete(key)
                        logger.debug(f"Invalidated {key}")
                    except Exception as e:
                        logger.warning(f"Cache invalidate error: {e}")

            # Invalidate patterns
            if patterns:
                for pattern in patterns:
                    try:
                        count = await cache_instance.delete_pattern(pattern)
                        logger.debug(f"Invalidated {count} keys matching {pattern}")
                    except Exception as e:
                        logger.warning(f"Cache pattern invalidate error: {e}")

            return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            cache_instance = cache
            if cache_instance is None:
                import ntlabs.cache as cache_module

                cache_instance = getattr(cache_module, "_default_cache", None)

            if cache_instance is None:
                return result

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    return result

                if key_builder:
                    cache_key = f"{prefix}:{key_builder(*args, **kwargs)}"
                    loop.run_until_complete(cache_instance.delete(cache_key))

                if keys:
                    for key in keys:
                        loop.run_until_complete(cache_instance.delete(key))

                if patterns:
                    for pattern in patterns:
                        loop.run_until_complete(cache_instance.delete_pattern(pattern))

            except RuntimeError:
                pass

            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def cache_aside(
    cache: Any = None,
    prefix: str = "cache",
    ttl: int | None = None,
    key_builder: Callable[..., str] | None = None,
    refresh_ttl: int | None = None,
    stale_ttl: int | None = None,
):
    """
    Cache-aside pattern with stale-while-revalidate support.

    This decorator implements the cache-aside pattern with optional
    stale-while-revalidate behavior:

    1. Check cache for value
    2. If found and fresh, return it
    3. If found but stale, return it AND refresh in background
    4. If not found, compute, cache, and return

    Args:
        cache: RedisCache instance
        prefix: Cache key prefix
        ttl: Fresh TTL in seconds
        key_builder: Custom key builder function
        refresh_ttl: Time before TTL to start background refresh
        stale_ttl: Additional time to serve stale data while refreshing

    Example:
        @cache_aside(
            cache=cache,
            prefix="products",
            ttl=300,
            stale_ttl=60,  # Serve stale for 60s while refreshing
        )
        async def get_product(product_id: str):
            return await db.fetch_product(product_id)
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            cache_instance = cache
            if cache_instance is None:
                import ntlabs.cache as cache_module

                cache_instance = getattr(cache_module, "_default_cache", None)

            if cache_instance is None:
                return await func(*args, **kwargs)

            cache_key = _make_cache_key(prefix, func, args, kwargs, key_builder)

            # Try to get from cache
            try:
                cached_value = await cache_instance.get(cache_key)
                if cached_value is not None:
                    # Check if we should refresh in background
                    if refresh_ttl and stale_ttl:
                        remaining_ttl = await cache_instance.ttl(cache_key)
                        if 0 < remaining_ttl < refresh_ttl:
                            # Start background refresh
                            asyncio.create_task(
                                _refresh_cache(
                                    cache_instance, cache_key, func, args, kwargs, ttl
                                )
                            )
                    return cached_value

            except Exception as e:
                logger.warning(f"Cache get error: {e}")

            # Compute value
            result = await func(*args, **kwargs)

            # Cache result
            try:
                effective_ttl = (ttl or 3600) + (stale_ttl or 0)
                await cache_instance.set(cache_key, result, ttl=effective_ttl)
            except Exception as e:
                logger.warning(f"Cache set error: {e}")

            return result

        return wrapper

    return decorator


async def _refresh_cache(
    cache_instance,
    cache_key: str,
    func: Callable,
    args: tuple,
    kwargs: dict,
    ttl: int | None,
) -> None:
    """Background task to refresh cache."""
    try:
        logger.debug(f"Background refresh for {cache_key}")
        result = await func(*args, **kwargs)
        await cache_instance.set(cache_key, result, ttl=ttl)
    except Exception as e:
        logger.warning(f"Background refresh error for {cache_key}: {e}")
