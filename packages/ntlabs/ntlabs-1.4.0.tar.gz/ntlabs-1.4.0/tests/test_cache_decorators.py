"""
Neural LAB Python SDK - Test Suite

Author: Anderson Henrique da Silva
Date: 2026-01-28
Location: Minas Gerais, Brasil
Copyright: Neural Thinker | AI Engineering LTDA

Description: Comprehensive tests for cache decorators module
Version: 1.0.0
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ntlabs.cache.decorators import (
    _make_cache_key,
    cached,
    cache_invalidate,
    cache_aside,
    _refresh_cache,
)


class TestMakeCacheKey:
    """Test cache key generation."""

    def test_simple_key(self):
        """Test simple cache key generation."""
        def func():
            pass

        key = _make_cache_key("prefix", func, (), {})
        assert key.startswith("prefix:")
        assert "test_cache_decorators" in key

    def test_with_args(self):
        """Test key generation with positional arguments."""
        def func():
            pass

        key = _make_cache_key("prefix", func, ("arg1", 123), {})
        assert "arg1" in key
        assert "123" in key

    def test_with_kwargs(self):
        """Test key generation with keyword arguments."""
        def func():
            pass

        key = _make_cache_key("prefix", func, (), {"key1": "value1", "key2": 456})
        assert "key1=value1" in key
        assert "key2=456" in key

    def test_custom_key_builder(self):
        """Test custom key builder function."""
        def func():
            pass

        def custom_builder(arg1, arg2):
            return f"custom:{arg1}:{arg2}"

        key = _make_cache_key("prefix", func, ("a", "b"), {}, custom_builder)
        assert key == "prefix:custom:a:b"

    def test_long_key_hashing(self):
        """Test that long keys are hashed."""
        def func():
            pass

        long_arg = "x" * 300
        key = _make_cache_key("prefix", func, (long_arg,), {})
        # Should be hashed due to length
        assert len(key) < 250

    def test_unhashable_args(self):
        """Test handling of unhashable arguments."""
        def func():
            pass

        # Object without proper string representation
        class Unhashable:
            def __str__(self):
                raise ValueError("Cannot convert")

        obj = Unhashable()
        key = _make_cache_key("prefix", func, (obj,), {})
        assert key.startswith("prefix:")


class TestCachedDecorator:
    """Test @cached decorator."""

    @pytest.fixture
    def mock_cache(self):
        """Create a mock cache."""
        cache = AsyncMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock(return_value=True)
        return cache

    @pytest.mark.asyncio
    async def test_async_cache_hit(self, mock_cache):
        """Test async function with cache hit."""
        mock_cache.get.return_value = "cached_value"

        @cached(cache=mock_cache, prefix="test")
        async def test_func(x):
            return f"computed_{x}"

        result = await test_func("arg")
        assert result == "cached_value"
        mock_cache.get.assert_called_once()
        mock_cache.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_cache_miss(self, mock_cache):
        """Test async function with cache miss."""
        mock_cache.get.return_value = None

        @cached(cache=mock_cache, prefix="test", ttl=300)
        async def test_func(x):
            return f"computed_{x}"

        result = await test_func("arg")
        assert result == "computed_arg"
        mock_cache.get.assert_called_once()
        mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_cache_error_fallback(self, mock_cache):
        """Test async function when cache fails."""
        mock_cache.get.side_effect = Exception("Redis error")

        @cached(cache=mock_cache, prefix="test")
        async def test_func(x):
            return f"computed_{x}"

        result = await test_func("arg")
        assert result == "computed_arg"

    @pytest.mark.asyncio
    async def test_async_cache_set_error(self, mock_cache):
        """Test async function when cache set fails."""
        mock_cache.get.return_value = None
        mock_cache.set.side_effect = Exception("Redis error")

        @cached(cache=mock_cache, prefix="test")
        async def test_func(x):
            return f"computed_{x}"

        result = await test_func("arg")
        assert result == "computed_arg"

    @pytest.mark.asyncio
    async def test_cache_unless_condition(self, mock_cache):
        """Test unless parameter to skip caching."""

        @cached(cache=mock_cache, prefix="test", unless=lambda x: x == "skip")
        async def test_func(x):
            return f"computed_{x}"

        # Should skip cache
        result = await test_func("skip")
        assert result == "computed_skip"
        mock_cache.get.assert_not_called()

        # Should use cache
        mock_cache.get.return_value = None
        result = await test_func("normal")
        mock_cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_none_values(self, mock_cache):
        """Test caching of None values."""
        mock_cache.get.return_value = None

        @cached(cache=mock_cache, prefix="test", cache_none=True)
        async def test_func():
            return None

        result = await test_func()
        assert result is None
        mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_cache_none_by_default(self, mock_cache):
        """Test that None is not cached by default."""
        mock_cache.get.return_value = None

        @cached(cache=mock_cache, prefix="test")
        async def test_func():
            return None

        result = await test_func()
        assert result is None
        mock_cache.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_global_cache_fallback(self, mock_cache):
        """Test fallback to global cache."""
        with patch("ntlabs.cache._default_cache", mock_cache):
            mock_cache.get.return_value = None

            @cached(prefix="test")  # No cache parameter
            async def test_func():
                return "result"

            result = await test_func()
            assert result == "result"
            mock_cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_cache_available(self):
        """Test when no cache is available."""
        with patch("ntlabs.cache._default_cache", None):

            @cached(prefix="test")
            async def test_func():
                return "result"

            result = await test_func()
            assert result == "result"


class TestSyncCachedDecorator:
    """Test sync function caching."""

    @pytest.fixture
    def mock_cache(self):
        """Create a mock cache."""
        cache = AsyncMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock(return_value=True)
        return cache

    def test_sync_cache_miss(self, mock_cache):
        """Test sync function with cache miss."""
        mock_cache.get.return_value = None

        @cached(cache=mock_cache, prefix="test")
        def test_func(x):
            return f"computed_{x}"

        with patch("asyncio.get_event_loop") as mock_loop:
            loop = MagicMock()
            loop.is_running.return_value = False
            loop.run_until_complete = MagicMock(side_effect=[
                None,  # cache.get
                True,  # cache.set
            ])
            mock_loop.return_value = loop

            result = test_func("arg")
            assert result == "computed_arg"

    def test_sync_called_from_async_context(self, mock_cache):
        """Test sync function called from async context."""

        @cached(cache=mock_cache, prefix="test")
        def test_func(x):
            return f"computed_{x}"

        with patch("asyncio.get_event_loop") as mock_loop:
            loop = MagicMock()
            loop.is_running.return_value = True
            mock_loop.return_value = loop

            result = test_func("arg")
            assert result == "computed_arg"

    def test_sync_no_event_loop(self, mock_cache):
        """Test sync function when no event loop available."""

        @cached(cache=mock_cache, prefix="test")
        def test_func(x):
            return f"computed_{x}"

        with patch("asyncio.get_event_loop", side_effect=RuntimeError):
            result = test_func("arg")
            assert result == "computed_arg"


class TestCacheInvalidateDecorator:
    """Test @cache_invalidate decorator."""

    @pytest.fixture
    def mock_cache(self):
        """Create a mock cache."""
        cache = AsyncMock()
        cache.delete = AsyncMock(return_value=True)
        cache.delete_pattern = AsyncMock(return_value=5)
        return cache

    @pytest.mark.asyncio
    async def test_invalidate_by_key_builder(self, mock_cache):
        """Test invalidation with custom key builder."""

        @cache_invalidate(
            cache=mock_cache,
            prefix="users",
            key_builder=lambda user_id: f"user:{user_id}",
        )
        async def update_user(user_id):
            return f"updated_{user_id}"

        result = await update_user("123")
        assert result == "updated_123"
        mock_cache.delete.assert_called_once_with("users:user:123")

    @pytest.mark.asyncio
    async def test_invalidate_specific_keys(self, mock_cache):
        """Test invalidation with specific keys."""

        @cache_invalidate(
            cache=mock_cache,
            keys=["cache:user:123", "cache:user:123:profile"],
        )
        async def clear_user_cache():
            return "done"

        result = await clear_user_cache()
        assert result == "done"
        assert mock_cache.delete.call_count == 2

    @pytest.mark.asyncio
    async def test_invalidate_by_pattern(self, mock_cache):
        """Test invalidation with pattern."""

        @cache_invalidate(
            cache=mock_cache,
            patterns=["users:*"],
        )
        async def clear_all_users():
            return "done"

        result = await clear_all_users()
        assert result == "done"
        mock_cache.delete_pattern.assert_called_once_with("users:*")

    @pytest.mark.asyncio
    async def test_invalidate_error_handling(self, mock_cache):
        """Test error handling during invalidation."""
        mock_cache.delete.side_effect = Exception("Redis error")

        @cache_invalidate(
            cache=mock_cache,
            keys=["key1"],
        )
        async def clear_cache():
            return "done"

        # Should not raise, just log warning
        result = await clear_cache()
        assert result == "done"

    def test_sync_invalidate(self, mock_cache):
        """Test sync function invalidation."""

        @cache_invalidate(
            cache=mock_cache,
            keys=["key1"],
        )
        def clear_cache():
            return "done"

        with patch("asyncio.get_event_loop") as mock_loop:
            loop = MagicMock()
            loop.is_running.return_value = False
            mock_loop.return_value = loop

            result = clear_cache()
            assert result == "done"


class TestCacheAsideDecorator:
    """Test @cache_aside decorator."""

    @pytest.fixture
    def mock_cache(self):
        """Create a mock cache."""
        cache = AsyncMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock(return_value=True)
        cache.ttl = AsyncMock(return_value=300)
        return cache

    @pytest.mark.asyncio
    async def test_cache_hit(self, mock_cache):
        """Test cache-aside with cache hit."""
        mock_cache.get.return_value = "cached_value"

        @cache_aside(cache=mock_cache, prefix="test")
        async def test_func():
            return "computed_value"

        result = await test_func()
        assert result == "cached_value"

    @pytest.mark.asyncio
    async def test_cache_miss(self, mock_cache):
        """Test cache-aside with cache miss."""
        mock_cache.get.return_value = None

        @cache_aside(cache=mock_cache, prefix="test", ttl=300)
        async def test_func():
            return "computed_value"

        result = await test_func()
        assert result == "computed_value"
        mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_background_refresh(self, mock_cache):
        """Test background refresh when TTL is low."""
        mock_cache.get.return_value = "cached_value"
        mock_cache.ttl.return_value = 10  # Low TTL triggers refresh

        @cache_aside(
            cache=mock_cache,
            prefix="test",
            ttl=300,
            refresh_ttl=30,
            stale_ttl=60,
        )
        async def test_func():
            return "new_value"

        with patch("asyncio.create_task") as mock_create_task:
            result = await test_func()
            assert result == "cached_value"
            mock_create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_refresh_when_ttl_high(self, mock_cache):
        """Test no background refresh when TTL is sufficient."""
        mock_cache.get.return_value = "cached_value"
        mock_cache.ttl.return_value = 100  # High TTL, no refresh

        @cache_aside(
            cache=mock_cache,
            prefix="test",
            ttl=300,
            refresh_ttl=30,
            stale_ttl=60,
        )
        async def test_func():
            return "new_value"

        with patch("asyncio.create_task") as mock_create_task:
            result = await test_func()
            assert result == "cached_value"
            mock_create_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_global_cache(self):
        """Test when no global cache available."""
        with patch("ntlabs.cache._default_cache", None):

            @cache_aside(prefix="test")
            async def test_func():
                return "result"

            result = await test_func()
            assert result == "result"


class TestRefreshCache:
    """Test _refresh_cache function."""

    @pytest.mark.asyncio
    async def test_successful_refresh(self):
        """Test successful background refresh."""
        cache = AsyncMock()
        cache.set = AsyncMock(return_value=True)

        async def factory():
            return "new_value"

        await _refresh_cache(cache, "test_key", factory, (), {}, 300)
        cache.set.assert_called_once_with("test_key", "new_value", ttl=300)

    @pytest.mark.asyncio
    async def test_refresh_error(self):
        """Test error handling in background refresh."""
        cache = AsyncMock()

        async def failing_factory():
            raise ValueError("Factory error")

        # Should not raise
        await _refresh_cache(cache, "test_key", failing_factory, (), {}, 300)


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.mark.asyncio
    async def test_decorator_preserves_function_metadata(self):
        """Test that decorator preserves function metadata."""
        @cached(prefix="test")
        async def my_function():
            """My docstring."""
            return "result"

        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "My docstring."

    @pytest.mark.asyncio
    async def test_multiple_decorators_same_function(self):
        """Test applying multiple cache decorators."""
        cache = AsyncMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock(return_value=True)
        cache.delete = AsyncMock(return_value=True)

        call_count = 0

        @cache_invalidate(cache=cache, keys=["related"])
        @cached(cache=cache, prefix="test")
        async def test_func():
            nonlocal call_count
            call_count += 1
            return f"result_{call_count}"

        result = await test_func()
        assert result == "result_1"
        assert call_count == 1
