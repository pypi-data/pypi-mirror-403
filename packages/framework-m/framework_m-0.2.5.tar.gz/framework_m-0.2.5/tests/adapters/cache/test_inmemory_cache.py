"""Tests for InMemoryCacheAdapter - Comprehensive coverage tests."""

import time

import pytest

# =============================================================================
# Test: InMemoryCacheAdapter Import
# =============================================================================


class TestInMemoryCacheImport:
    """Tests for InMemoryCacheAdapter import."""

    def test_import_inmemory_cache_adapter(self) -> None:
        """InMemoryCacheAdapter should be importable."""
        from framework_m.adapters.cache import InMemoryCacheAdapter

        assert InMemoryCacheAdapter is not None


# =============================================================================
# Test: InMemoryCacheAdapter Instantiation
# =============================================================================


class TestInMemoryCacheInstantiation:
    """Tests for InMemoryCacheAdapter instantiation."""

    def test_init_creates_empty_cache(self) -> None:
        """__init__ should create empty cache dict."""
        from framework_m.adapters.cache import InMemoryCacheAdapter

        cache = InMemoryCacheAdapter()

        assert cache._cache == {}

    def test_init_is_isolated(self) -> None:
        """Each instance should have its own cache."""
        from framework_m.adapters.cache import InMemoryCacheAdapter

        cache1 = InMemoryCacheAdapter()
        cache2 = InMemoryCacheAdapter()

        assert cache1._cache is not cache2._cache


# =============================================================================
# Test: InMemoryCacheAdapter - Get
# =============================================================================


class TestInMemoryCacheGet:
    """Tests for get method."""

    @pytest.mark.asyncio
    async def test_get_returns_none_for_missing_key(self) -> None:
        """get should return None for missing key."""
        from framework_m.adapters.cache import InMemoryCacheAdapter

        cache = InMemoryCacheAdapter()

        result = await cache.get("missing")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_returns_cached_value(self) -> None:
        """get should return cached value."""
        from framework_m.adapters.cache import InMemoryCacheAdapter

        cache = InMemoryCacheAdapter()
        cache._cache["key"] = ({"data": "value"}, None)

        result = await cache.get("key")

        assert result == {"data": "value"}

    @pytest.mark.asyncio
    async def test_get_removes_expired_key(self) -> None:
        """get should remove and return None for expired key."""
        from framework_m.adapters.cache import InMemoryCacheAdapter

        cache = InMemoryCacheAdapter()
        # Set to already expired
        cache._cache["expired"] = ("old_value", time.time() - 10)

        result = await cache.get("expired")

        assert result is None
        assert "expired" not in cache._cache

    @pytest.mark.asyncio
    async def test_get_returns_value_before_expiry(self) -> None:
        """get should return value if not expired."""
        from framework_m.adapters.cache import InMemoryCacheAdapter

        cache = InMemoryCacheAdapter()
        # Set to expire in future
        cache._cache["fresh"] = ("value", time.time() + 1000)

        result = await cache.get("fresh")

        assert result == "value"


# =============================================================================
# Test: InMemoryCacheAdapter - Set
# =============================================================================


class TestInMemoryCacheSet:
    """Tests for set method."""

    @pytest.mark.asyncio
    async def test_set_stores_value(self) -> None:
        """set should store value in cache."""
        from framework_m.adapters.cache import InMemoryCacheAdapter

        cache = InMemoryCacheAdapter()

        await cache.set("key", {"data": "value"})

        assert "key" in cache._cache
        value, _ = cache._cache["key"]
        assert value == {"data": "value"}

    @pytest.mark.asyncio
    async def test_set_without_ttl(self) -> None:
        """set without TTL should have no expiry."""
        from framework_m.adapters.cache import InMemoryCacheAdapter

        cache = InMemoryCacheAdapter()

        await cache.set("key", "value")

        _, expires_at = cache._cache["key"]
        assert expires_at is None

    @pytest.mark.asyncio
    async def test_set_with_ttl(self) -> None:
        """set with TTL should set expiry time."""
        from framework_m.adapters.cache import InMemoryCacheAdapter

        cache = InMemoryCacheAdapter()
        before = time.time()

        await cache.set("key", "value", ttl=60)

        _, expires_at = cache._cache["key"]
        assert expires_at is not None
        assert expires_at >= before + 60

    @pytest.mark.asyncio
    async def test_set_overwrites_existing(self) -> None:
        """set should overwrite existing value."""
        from framework_m.adapters.cache import InMemoryCacheAdapter

        cache = InMemoryCacheAdapter()
        await cache.set("key", "old")
        await cache.set("key", "new")

        value, _ = cache._cache["key"]
        assert value == "new"


# =============================================================================
# Test: InMemoryCacheAdapter - Delete
# =============================================================================


class TestInMemoryCacheDelete:
    """Tests for delete method."""

    @pytest.mark.asyncio
    async def test_delete_removes_key(self) -> None:
        """delete should remove key from cache."""
        from framework_m.adapters.cache import InMemoryCacheAdapter

        cache = InMemoryCacheAdapter()
        cache._cache["key"] = ("value", None)

        await cache.delete("key")

        assert "key" not in cache._cache

    @pytest.mark.asyncio
    async def test_delete_nonexistent_key(self) -> None:
        """delete should not error for nonexistent key."""
        from framework_m.adapters.cache import InMemoryCacheAdapter

        cache = InMemoryCacheAdapter()

        # Should not raise
        await cache.delete("nonexistent")


# =============================================================================
# Test: InMemoryCacheAdapter - Exists
# =============================================================================


class TestInMemoryCacheExists:
    """Tests for exists method."""

    @pytest.mark.asyncio
    async def test_exists_returns_true(self) -> None:
        """exists should return True for existing key."""
        from framework_m.adapters.cache import InMemoryCacheAdapter

        cache = InMemoryCacheAdapter()
        cache._cache["key"] = ("value", None)

        result = await cache.exists("key")

        assert result is True

    @pytest.mark.asyncio
    async def test_exists_returns_false(self) -> None:
        """exists should return False for missing key."""
        from framework_m.adapters.cache import InMemoryCacheAdapter

        cache = InMemoryCacheAdapter()

        result = await cache.exists("missing")

        assert result is False

    @pytest.mark.asyncio
    async def test_exists_returns_false_for_expired(self) -> None:
        """exists should return False for expired key."""
        from framework_m.adapters.cache import InMemoryCacheAdapter

        cache = InMemoryCacheAdapter()
        cache._cache["expired"] = ("value", time.time() - 10)

        result = await cache.exists("expired")

        assert result is False


# =============================================================================
# Test: InMemoryCacheAdapter - Get Many
# =============================================================================


class TestInMemoryCacheGetMany:
    """Tests for get_many method."""

    @pytest.mark.asyncio
    async def test_get_many_returns_existing(self) -> None:
        """get_many should return existing values."""
        from framework_m.adapters.cache import InMemoryCacheAdapter

        cache = InMemoryCacheAdapter()
        cache._cache["key1"] = ("value1", None)
        cache._cache["key2"] = ("value2", None)

        result = await cache.get_many(["key1", "key2", "key3"])

        assert result == {"key1": "value1", "key2": "value2"}

    @pytest.mark.asyncio
    async def test_get_many_empty_keys(self) -> None:
        """get_many should return empty dict for empty keys."""
        from framework_m.adapters.cache import InMemoryCacheAdapter

        cache = InMemoryCacheAdapter()

        result = await cache.get_many([])

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_many_all_missing(self) -> None:
        """get_many should return empty dict if all missing."""
        from framework_m.adapters.cache import InMemoryCacheAdapter

        cache = InMemoryCacheAdapter()

        result = await cache.get_many(["a", "b", "c"])

        assert result == {}


# =============================================================================
# Test: InMemoryCacheAdapter - Set Many
# =============================================================================


class TestInMemoryCacheSetMany:
    """Tests for set_many method."""

    @pytest.mark.asyncio
    async def test_set_many_stores_all(self) -> None:
        """set_many should store all items."""
        from framework_m.adapters.cache import InMemoryCacheAdapter

        cache = InMemoryCacheAdapter()

        await cache.set_many({"key1": "value1", "key2": "value2"})

        assert "key1" in cache._cache
        assert "key2" in cache._cache

    @pytest.mark.asyncio
    async def test_set_many_with_ttl(self) -> None:
        """set_many should apply TTL to all items."""
        from framework_m.adapters.cache import InMemoryCacheAdapter

        cache = InMemoryCacheAdapter()

        await cache.set_many({"k1": "v1", "k2": "v2"}, ttl=60)

        _, expires1 = cache._cache["k1"]
        _, expires2 = cache._cache["k2"]
        assert expires1 is not None
        assert expires2 is not None


# =============================================================================
# Test: InMemoryCacheAdapter - Delete Pattern
# =============================================================================


class TestInMemoryCacheDeletePattern:
    """Tests for delete_pattern method."""

    @pytest.mark.asyncio
    async def test_delete_pattern_removes_matching(self) -> None:
        """delete_pattern should remove matching keys."""
        from framework_m.adapters.cache import InMemoryCacheAdapter

        cache = InMemoryCacheAdapter()
        cache._cache["user:1"] = ("data1", None)
        cache._cache["user:2"] = ("data2", None)
        cache._cache["order:1"] = ("data3", None)

        count = await cache.delete_pattern("user:*")

        assert count == 2
        assert "user:1" not in cache._cache
        assert "user:2" not in cache._cache
        assert "order:1" in cache._cache

    @pytest.mark.asyncio
    async def test_delete_pattern_no_matches(self) -> None:
        """delete_pattern should return 0 for no matches."""
        from framework_m.adapters.cache import InMemoryCacheAdapter

        cache = InMemoryCacheAdapter()
        cache._cache["key"] = ("value", None)

        count = await cache.delete_pattern("nomatch:*")

        assert count == 0


# =============================================================================
# Test: InMemoryCacheAdapter - TTL
# =============================================================================


class TestInMemoryCacheTTL:
    """Tests for ttl method."""

    @pytest.mark.asyncio
    async def test_ttl_returns_none_for_missing(self) -> None:
        """ttl should return None for missing key."""
        from framework_m.adapters.cache import InMemoryCacheAdapter

        cache = InMemoryCacheAdapter()

        result = await cache.ttl("missing")

        assert result is None

    @pytest.mark.asyncio
    async def test_ttl_returns_none_for_no_expiry(self) -> None:
        """ttl should return None for key without expiry."""
        from framework_m.adapters.cache import InMemoryCacheAdapter

        cache = InMemoryCacheAdapter()
        cache._cache["key"] = ("value", None)

        result = await cache.ttl("key")

        assert result is None

    @pytest.mark.asyncio
    async def test_ttl_returns_remaining_time(self) -> None:
        """ttl should return remaining seconds."""
        from framework_m.adapters.cache import InMemoryCacheAdapter

        cache = InMemoryCacheAdapter()
        cache._cache["key"] = ("value", time.time() + 100)

        result = await cache.ttl("key")

        assert result is not None
        assert result >= 99  # Allow for small timing difference

    @pytest.mark.asyncio
    async def test_ttl_returns_zero_for_expired(self) -> None:
        """ttl should return 0 for expired key."""
        from framework_m.adapters.cache import InMemoryCacheAdapter

        cache = InMemoryCacheAdapter()
        cache._cache["expired"] = ("value", time.time() - 10)

        result = await cache.ttl("expired")

        assert result == 0


# =============================================================================
# Test: InMemoryCacheAdapter - Clear
# =============================================================================


class TestInMemoryCacheClear:
    """Tests for clear method."""

    @pytest.mark.asyncio
    async def test_clear_removes_all_keys(self) -> None:
        """clear should remove all keys."""
        from framework_m.adapters.cache import InMemoryCacheAdapter

        cache = InMemoryCacheAdapter()
        cache._cache["key1"] = ("v1", None)
        cache._cache["key2"] = ("v2", None)

        await cache.clear()

        assert cache._cache == {}
