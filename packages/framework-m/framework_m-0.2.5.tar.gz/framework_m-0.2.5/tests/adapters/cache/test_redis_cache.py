"""Tests for RedisCacheAdapter - Comprehensive coverage tests."""

from unittest.mock import AsyncMock, patch

import pytest

# =============================================================================
# Test: CacheProtocol Import
# =============================================================================


class TestCacheProtocolImport:
    """Tests for CacheProtocol import."""

    def test_import_cache_protocol(self) -> None:
        """CacheProtocol should be importable."""
        from framework_m.adapters.cache.redis_cache import CacheProtocol

        assert CacheProtocol is not None

    def test_import_redis_cache_adapter(self) -> None:
        """RedisCacheAdapter should be importable."""
        from framework_m.adapters.cache.redis_cache import RedisCacheAdapter

        assert RedisCacheAdapter is not None


# =============================================================================
# Test: RedisCacheAdapter Instantiation
# =============================================================================


class TestRedisCacheAdapterInstantiation:
    """Tests for RedisCacheAdapter instantiation."""

    def test_instantiate_with_defaults(self) -> None:
        """RedisCacheAdapter should be instantiable with defaults."""
        from framework_m.adapters.cache.redis_cache import RedisCacheAdapter

        cache = RedisCacheAdapter()
        assert cache is not None
        assert cache._key_prefix == "fm:"

    def test_instantiate_with_custom_url(self) -> None:
        """RedisCacheAdapter should accept custom URL."""
        from framework_m.adapters.cache.redis_cache import RedisCacheAdapter

        cache = RedisCacheAdapter(redis_url="redis://custom:6379")
        assert cache._redis_url == "redis://custom:6379"

    def test_instantiate_with_custom_prefix(self) -> None:
        """RedisCacheAdapter should accept custom key prefix."""
        from framework_m.adapters.cache.redis_cache import RedisCacheAdapter

        cache = RedisCacheAdapter(key_prefix="myapp:")
        assert cache._key_prefix == "myapp:"

    def test_redis_initially_none(self) -> None:
        """Redis client should be None before connect."""
        from framework_m.adapters.cache.redis_cache import RedisCacheAdapter

        cache = RedisCacheAdapter()
        assert cache._redis is None


# =============================================================================
# Test: RedisCacheAdapter Make Key
# =============================================================================


class TestRedisCacheAdapterMakeKey:
    """Tests for _make_key method."""

    def test_make_key_adds_prefix(self) -> None:
        """_make_key should add prefix to key."""
        from framework_m.adapters.cache.redis_cache import RedisCacheAdapter

        cache = RedisCacheAdapter(key_prefix="test:")
        assert cache._make_key("mykey") == "test:mykey"

    def test_make_key_default_prefix(self) -> None:
        """_make_key should use default fm: prefix."""
        from framework_m.adapters.cache.redis_cache import RedisCacheAdapter

        cache = RedisCacheAdapter()
        assert cache._make_key("user:123") == "fm:user:123"


# =============================================================================
# Test: RedisCacheAdapter Connect/Disconnect
# =============================================================================


class TestRedisCacheAdapterConnect:
    """Tests for connect and disconnect methods."""

    @pytest.mark.asyncio
    async def test_connect_creates_client(self) -> None:
        """connect should create Redis client."""
        from framework_m.adapters.cache.redis_cache import RedisCacheAdapter

        cache = RedisCacheAdapter()

        with patch("redis.asyncio.from_url") as mock_from_url:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock()
            mock_from_url.return_value = mock_client

            await cache.connect()

            mock_from_url.assert_called_once()
            mock_client.ping.assert_called_once()
            assert cache._redis is mock_client

    @pytest.mark.asyncio
    async def test_disconnect_closes_client(self) -> None:
        """disconnect should close Redis client."""
        from framework_m.adapters.cache.redis_cache import RedisCacheAdapter

        cache = RedisCacheAdapter()
        mock_redis = AsyncMock()
        mock_redis.close = AsyncMock()
        cache._redis = mock_redis

        await cache.disconnect()

        mock_redis.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_no_client(self) -> None:
        """disconnect should not error without client."""
        from framework_m.adapters.cache.redis_cache import RedisCacheAdapter

        cache = RedisCacheAdapter()
        cache._redis = None

        # Should not raise
        await cache.disconnect()


# =============================================================================
# Test: RedisCacheAdapter Get
# =============================================================================


class TestRedisCacheAdapterGet:
    """Tests for get method."""

    @pytest.mark.asyncio
    async def test_get_returns_cached_value(self) -> None:
        """get should return cached value."""
        from framework_m.adapters.cache.redis_cache import RedisCacheAdapter

        cache = RedisCacheAdapter()
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value='{"name": "test"}')
        cache._redis = mock_redis

        result = await cache.get("key")

        assert result == {"name": "test"}
        mock_redis.get.assert_called_once_with("fm:key")

    @pytest.mark.asyncio
    async def test_get_returns_none_for_miss(self) -> None:
        """get should return None for cache miss."""
        from framework_m.adapters.cache.redis_cache import RedisCacheAdapter

        cache = RedisCacheAdapter()
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        cache._redis = mock_redis

        result = await cache.get("missing")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_no_connection(self) -> None:
        """get should return None without connection."""
        from framework_m.adapters.cache.redis_cache import RedisCacheAdapter

        cache = RedisCacheAdapter()
        cache._redis = None

        result = await cache.get("key")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_handles_error(self) -> None:
        """get should handle errors gracefully."""
        from framework_m.adapters.cache.redis_cache import RedisCacheAdapter

        cache = RedisCacheAdapter()
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(side_effect=Exception("Connection error"))
        cache._redis = mock_redis

        result = await cache.get("key")

        assert result is None


# =============================================================================
# Test: RedisCacheAdapter Set
# =============================================================================


class TestRedisCacheAdapterSet:
    """Tests for set method."""

    @pytest.mark.asyncio
    async def test_set_stores_value(self) -> None:
        """set should store value in Redis."""
        from framework_m.adapters.cache.redis_cache import RedisCacheAdapter

        cache = RedisCacheAdapter()
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock()
        cache._redis = mock_redis

        await cache.set("key", {"data": "value"})

        mock_redis.set.assert_called_once_with("fm:key", '{"data": "value"}')

    @pytest.mark.asyncio
    async def test_set_with_ttl_uses_setex(self) -> None:
        """set with TTL should use setex."""
        from framework_m.adapters.cache.redis_cache import RedisCacheAdapter

        cache = RedisCacheAdapter()
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock()
        cache._redis = mock_redis

        await cache.set("key", {"data": "value"}, ttl=300)

        mock_redis.setex.assert_called_once_with("fm:key", 300, '{"data": "value"}')

    @pytest.mark.asyncio
    async def test_set_no_connection(self) -> None:
        """set should do nothing without connection."""
        from framework_m.adapters.cache.redis_cache import RedisCacheAdapter

        cache = RedisCacheAdapter()
        cache._redis = None

        # Should not raise
        await cache.set("key", {"data": "value"})

    @pytest.mark.asyncio
    async def test_set_handles_error(self) -> None:
        """set should handle errors gracefully."""
        from framework_m.adapters.cache.redis_cache import RedisCacheAdapter

        cache = RedisCacheAdapter()
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(side_effect=Exception("Connection error"))
        cache._redis = mock_redis

        # Should not raise
        await cache.set("key", {"data": "value"})


# =============================================================================
# Test: RedisCacheAdapter Delete
# =============================================================================


class TestRedisCacheAdapterDelete:
    """Tests for delete method."""

    @pytest.mark.asyncio
    async def test_delete_removes_key(self) -> None:
        """delete should remove key from Redis."""
        from framework_m.adapters.cache.redis_cache import RedisCacheAdapter

        cache = RedisCacheAdapter()
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock()
        cache._redis = mock_redis

        await cache.delete("key")

        mock_redis.delete.assert_called_once_with("fm:key")

    @pytest.mark.asyncio
    async def test_delete_no_connection(self) -> None:
        """delete should do nothing without connection."""
        from framework_m.adapters.cache.redis_cache import RedisCacheAdapter

        cache = RedisCacheAdapter()
        cache._redis = None

        # Should not raise
        await cache.delete("key")

    @pytest.mark.asyncio
    async def test_delete_handles_error(self) -> None:
        """delete should handle errors gracefully."""
        from framework_m.adapters.cache.redis_cache import RedisCacheAdapter

        cache = RedisCacheAdapter()
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(side_effect=Exception("Error"))
        cache._redis = mock_redis

        # Should not raise
        await cache.delete("key")


# =============================================================================
# Test: RedisCacheAdapter Delete Pattern
# =============================================================================


class TestRedisCacheAdapterDeletePattern:
    """Tests for delete_pattern method."""

    @pytest.mark.asyncio
    async def test_delete_pattern_removes_matching(self) -> None:
        """delete_pattern should remove matching keys."""
        from framework_m.adapters.cache.redis_cache import RedisCacheAdapter

        cache = RedisCacheAdapter()
        mock_redis = AsyncMock()
        mock_redis.keys = AsyncMock(return_value=["fm:user:1", "fm:user:2"])
        mock_redis.delete = AsyncMock(return_value=2)
        cache._redis = mock_redis

        count = await cache.delete_pattern("user:*")

        assert count == 2
        mock_redis.keys.assert_called_once_with("fm:user:*")
        mock_redis.delete.assert_called_once_with("fm:user:1", "fm:user:2")

    @pytest.mark.asyncio
    async def test_delete_pattern_no_matches(self) -> None:
        """delete_pattern should return 0 for no matches."""
        from framework_m.adapters.cache.redis_cache import RedisCacheAdapter

        cache = RedisCacheAdapter()
        mock_redis = AsyncMock()
        mock_redis.keys = AsyncMock(return_value=[])
        cache._redis = mock_redis

        count = await cache.delete_pattern("nomatch:*")

        assert count == 0

    @pytest.mark.asyncio
    async def test_delete_pattern_no_connection(self) -> None:
        """delete_pattern should return 0 without connection."""
        from framework_m.adapters.cache.redis_cache import RedisCacheAdapter

        cache = RedisCacheAdapter()
        cache._redis = None

        count = await cache.delete_pattern("user:*")

        assert count == 0

    @pytest.mark.asyncio
    async def test_delete_pattern_handles_error(self) -> None:
        """delete_pattern should handle errors gracefully."""
        from framework_m.adapters.cache.redis_cache import RedisCacheAdapter

        cache = RedisCacheAdapter()
        mock_redis = AsyncMock()
        mock_redis.keys = AsyncMock(side_effect=Exception("Error"))
        cache._redis = mock_redis

        count = await cache.delete_pattern("user:*")

        assert count == 0


# =============================================================================
# Test: RedisCacheAdapter Exists
# =============================================================================


class TestRedisCacheAdapterExists:
    """Tests for exists method."""

    @pytest.mark.asyncio
    async def test_exists_returns_true(self) -> None:
        """exists should return True for existing key."""
        from framework_m.adapters.cache.redis_cache import RedisCacheAdapter

        cache = RedisCacheAdapter()
        mock_redis = AsyncMock()
        mock_redis.exists = AsyncMock(return_value=1)
        cache._redis = mock_redis

        result = await cache.exists("key")

        assert result is True
        mock_redis.exists.assert_called_once_with("fm:key")

    @pytest.mark.asyncio
    async def test_exists_returns_false(self) -> None:
        """exists should return False for missing key."""
        from framework_m.adapters.cache.redis_cache import RedisCacheAdapter

        cache = RedisCacheAdapter()
        mock_redis = AsyncMock()
        mock_redis.exists = AsyncMock(return_value=0)
        cache._redis = mock_redis

        result = await cache.exists("missing")

        assert result is False

    @pytest.mark.asyncio
    async def test_exists_no_connection(self) -> None:
        """exists should return False without connection."""
        from framework_m.adapters.cache.redis_cache import RedisCacheAdapter

        cache = RedisCacheAdapter()
        cache._redis = None

        result = await cache.exists("key")

        assert result is False

    @pytest.mark.asyncio
    async def test_exists_handles_error(self) -> None:
        """exists should handle errors gracefully."""
        from framework_m.adapters.cache.redis_cache import RedisCacheAdapter

        cache = RedisCacheAdapter()
        mock_redis = AsyncMock()
        mock_redis.exists = AsyncMock(side_effect=Exception("Error"))
        cache._redis = mock_redis

        result = await cache.exists("key")

        assert result is False


# =============================================================================
# Test: RedisCacheAdapter Get Many
# =============================================================================


class TestRedisCacheAdapterGetMany:
    """Tests for get_many method."""

    @pytest.mark.asyncio
    async def test_get_many_returns_values(self) -> None:
        """get_many should return multiple values."""
        from framework_m.adapters.cache.redis_cache import RedisCacheAdapter

        cache = RedisCacheAdapter()
        mock_redis = AsyncMock()
        mock_redis.mget = AsyncMock(return_value=['{"a": 1}', '{"b": 2}', None])
        cache._redis = mock_redis

        result = await cache.get_many(["key1", "key2", "key3"])

        assert result == {"key1": {"a": 1}, "key2": {"b": 2}}

    @pytest.mark.asyncio
    async def test_get_many_no_connection(self) -> None:
        """get_many should return empty dict without connection."""
        from framework_m.adapters.cache.redis_cache import RedisCacheAdapter

        cache = RedisCacheAdapter()
        cache._redis = None

        result = await cache.get_many(["key1", "key2"])

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_many_handles_error(self) -> None:
        """get_many should handle errors gracefully."""
        from framework_m.adapters.cache.redis_cache import RedisCacheAdapter

        cache = RedisCacheAdapter()
        mock_redis = AsyncMock()
        mock_redis.mget = AsyncMock(side_effect=Exception("Error"))
        cache._redis = mock_redis

        result = await cache.get_many(["key1"])

        assert result == {}


# =============================================================================
# Test: InMemoryCacheAdapter implements protocol
# =============================================================================


class TestInMemoryCacheAdapterProtocol:
    """Tests for InMemoryCacheAdapter protocol compliance."""

    def test_inmemory_implements_cache_protocol(self) -> None:
        """InMemoryCacheAdapter should implement CacheProtocol."""
        from framework_m.adapters.cache import InMemoryCacheAdapter
        from framework_m.adapters.cache.redis_cache import CacheProtocol

        cache = InMemoryCacheAdapter()
        assert isinstance(cache, CacheProtocol)
