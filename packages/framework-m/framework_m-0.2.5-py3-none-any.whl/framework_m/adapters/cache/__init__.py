"""In-memory cache adapter for testing and development.

Implements CacheProtocol with a simple dict-based storage.
"""

from __future__ import annotations

import fnmatch
import time
from typing import Any


class InMemoryCacheAdapter:
    """In-memory implementation of CacheProtocol.

    Uses a simple dict to store cached values with TTL support.
    Suitable for testing and single-process development.

    Example:
        cache = InMemoryCacheAdapter()
        await cache.set("key", "value", ttl=60)
        value = await cache.get("key")
    """

    def __init__(self) -> None:
        """Initialize empty cache."""
        self._cache: dict[str, tuple[Any, float | None]] = {}

    async def get(self, key: str) -> Any | None:
        """Get a value from cache.

        Returns None if key doesn't exist or has expired.
        """
        if key not in self._cache:
            return None

        value, expires_at = self._cache[key]
        if expires_at is not None and time.time() > expires_at:
            del self._cache[key]
            return None

        return value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> None:
        """Set a value in cache with optional TTL."""
        expires_at = time.time() + ttl if ttl else None
        self._cache[key] = (value, expires_at)

    async def delete(self, key: str) -> None:
        """Delete a key from cache."""
        self._cache.pop(key, None)

    async def exists(self, key: str) -> bool:
        """Check if a key exists and hasn't expired."""
        result = await self.get(key)
        return result is not None

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values from cache."""
        results = {}
        for key in keys:
            value = await self.get(key)
            if value is not None:
                results[key] = value
        return results

    async def set_many(
        self,
        items: dict[str, Any],
        ttl: int | None = None,
    ) -> None:
        """Set multiple values in cache."""
        for key, value in items.items():
            await self.set(key, value, ttl)

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a glob pattern."""
        keys_to_delete = [key for key in self._cache if fnmatch.fnmatch(key, pattern)]
        for key in keys_to_delete:
            del self._cache[key]
        return len(keys_to_delete)

    async def ttl(self, key: str) -> int | None:
        """Get remaining TTL for a key."""
        if key not in self._cache:
            return None

        _, expires_at = self._cache[key]
        if expires_at is None:
            return None

        remaining = int(expires_at - time.time())
        return max(0, remaining)

    async def clear(self) -> None:
        """Clear all keys from cache."""
        self._cache.clear()
