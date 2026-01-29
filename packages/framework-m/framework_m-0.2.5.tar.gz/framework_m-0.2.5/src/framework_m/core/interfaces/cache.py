"""Cache Protocol - Core interface for caching.

This module defines the CacheProtocol for key-value caching
with TTL support and pattern-based operations.

Supports various backends: Redis, Memcached, in-memory, etc.
"""

from typing import Any, Protocol


class CacheProtocol(Protocol):
    """Protocol defining the contract for cache implementations.

    This is the primary port for caching in the hexagonal architecture.
    Provides key-value storage with TTL and batch operations.

    Implementations include:
    - RedisCacheAdapter: Redis-backed distributed cache
    - MemoryCacheAdapter: In-process LRU cache for development

    Example usage:
        cache: CacheProtocol = container.get(CacheProtocol)

        # Simple get/set
        await cache.set("user:123", user_data, ttl=3600)
        data = await cache.get("user:123")

        # Batch operations
        await cache.set_many({"key1": val1, "key2": val2}, ttl=600)
        results = await cache.get_many(["key1", "key2"])

        # Pattern deletion for cache invalidation
        await cache.delete_pattern("user:*")
    """

    async def get(self, key: str) -> Any | None:
        """Get a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        ...

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> None:
        """Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache (must be serializable)
            ttl: Time-to-live in seconds (None for no expiry)
        """
        ...

    async def delete(self, key: str) -> None:
        """Delete a key from cache.

        Args:
            key: Cache key to delete
        """
        ...

    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache.

        Args:
            key: Cache key to check

        Returns:
            True if key exists and hasn't expired
        """
        ...

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values from cache.

        Args:
            keys: List of cache keys

        Returns:
            Dict of key -> value (missing keys omitted)
        """
        ...

    async def set_many(
        self,
        items: dict[str, Any],
        ttl: int | None = None,
    ) -> None:
        """Set multiple values in cache.

        Args:
            items: Dict of key -> value pairs
            ttl: Time-to-live in seconds for all items
        """
        ...

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern.

        Useful for cache invalidation (e.g., "user:*" to clear all user caches).

        Args:
            pattern: Glob-style pattern (e.g., "user:*", "doc:Todo:*")

        Returns:
            Number of keys deleted
        """
        ...

    async def ttl(self, key: str) -> int | None:
        """Get remaining TTL for a key.

        Args:
            key: Cache key

        Returns:
            Remaining TTL in seconds, None if no TTL or key doesn't exist
        """
        ...

    async def clear(self) -> None:
        """Clear all keys from cache.

        Use with caution in production.
        """
        ...


__all__ = [
    "CacheProtocol",
]
