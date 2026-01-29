"""Tests for CacheProtocol interface."""

from typing import Any


class TestCacheProtocol:
    """Tests for CacheProtocol interface definition."""

    def test_import_cache_protocol(self) -> None:
        """CacheProtocol should be importable."""
        from framework_m.core.interfaces.cache import CacheProtocol

        assert CacheProtocol is not None

    def test_cache_protocol_is_protocol(self) -> None:
        """CacheProtocol should be a Protocol class."""

        from framework_m.core.interfaces.cache import CacheProtocol

        # Protocols have _is_protocol attribute
        assert hasattr(CacheProtocol, "_is_protocol")

    def test_cache_protocol_has_get(self) -> None:
        """CacheProtocol should define get method."""
        from framework_m.core.interfaces.cache import CacheProtocol

        assert hasattr(CacheProtocol, "get")

    def test_cache_protocol_has_set(self) -> None:
        """CacheProtocol should define set method."""
        from framework_m.core.interfaces.cache import CacheProtocol

        assert hasattr(CacheProtocol, "set")

    def test_cache_protocol_has_delete(self) -> None:
        """CacheProtocol should define delete method."""
        from framework_m.core.interfaces.cache import CacheProtocol

        assert hasattr(CacheProtocol, "delete")

    def test_cache_protocol_has_exists(self) -> None:
        """CacheProtocol should define exists method."""
        from framework_m.core.interfaces.cache import CacheProtocol

        assert hasattr(CacheProtocol, "exists")

    def test_cache_protocol_has_get_many(self) -> None:
        """CacheProtocol should define get_many method."""
        from framework_m.core.interfaces.cache import CacheProtocol

        assert hasattr(CacheProtocol, "get_many")

    def test_cache_protocol_has_set_many(self) -> None:
        """CacheProtocol should define set_many method."""
        from framework_m.core.interfaces.cache import CacheProtocol

        assert hasattr(CacheProtocol, "set_many")

    def test_cache_protocol_has_delete_pattern(self) -> None:
        """CacheProtocol should define delete_pattern method."""
        from framework_m.core.interfaces.cache import CacheProtocol

        assert hasattr(CacheProtocol, "delete_pattern")

    def test_cache_protocol_has_ttl(self) -> None:
        """CacheProtocol should define ttl method."""
        from framework_m.core.interfaces.cache import CacheProtocol

        assert hasattr(CacheProtocol, "ttl")

    def test_cache_protocol_has_clear(self) -> None:
        """CacheProtocol should define clear method."""
        from framework_m.core.interfaces.cache import CacheProtocol

        assert hasattr(CacheProtocol, "clear")

    def test_cache_protocol_exports(self) -> None:
        """CacheProtocol should be in __all__."""
        from framework_m.core.interfaces import cache

        assert "CacheProtocol" in cache.__all__


class TestCacheProtocolImplementation:
    """Tests for implementing CacheProtocol."""

    def test_can_implement_protocol(self) -> None:
        """A class implementing all methods should satisfy CacheProtocol."""
        from framework_m.core.interfaces.cache import CacheProtocol

        class MockCache:
            async def get(self, key: str) -> Any | None:
                return None

            async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
                pass

            async def delete(self, key: str) -> None:
                pass

            async def exists(self, key: str) -> bool:
                return False

            async def get_many(self, keys: list[str]) -> dict[str, Any]:
                return {}

            async def set_many(
                self, items: dict[str, Any], ttl: int | None = None
            ) -> None:
                pass

            async def delete_pattern(self, pattern: str) -> int:
                return 0

            async def ttl(self, key: str) -> int | None:
                return None

            async def clear(self) -> None:
                pass

        # Should be valid implementation
        cache: CacheProtocol = MockCache()
        assert cache is not None
