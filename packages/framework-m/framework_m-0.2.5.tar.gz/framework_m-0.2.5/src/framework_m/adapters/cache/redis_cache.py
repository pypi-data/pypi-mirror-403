"""Redis Cache Adapter - Distributed caching with Redis.

This module provides the RedisCacheAdapter that implements CacheProtocol
using Redis as the backend for distributed deployments.

Example:
    >>> cache = RedisCacheAdapter(redis_url="redis://localhost:6379")
    >>> await cache.connect()
    >>> await cache.set("user:123", {"name": "John"}, ttl=300)
    >>> user = await cache.get("user:123")
    >>> await cache.disconnect()
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class CacheProtocol(Protocol):
    """Protocol for cache implementations.

    Defines the interface for caching with get/set/delete operations.
    Implementations may use Redis, Memcached, or in-memory storage.
    """

    async def get(self, key: str) -> Any | None:
        """Get a value from cache."""
        ...

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> None:
        """Set a value in cache with optional TTL."""
        ...

    async def delete(self, key: str) -> None:
        """Delete a key from cache."""
        ...

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        ...

    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        ...


class RedisCacheAdapter:
    """Redis-backed cache for distributed deployments.

    Implements CacheProtocol using Redis for multi-process and
    multi-node cache sharing.

    Example:
        >>> cache = RedisCacheAdapter(redis_url="redis://localhost:6379")
        >>> await cache.connect()
        >>> await cache.set("Invoice:123", data, ttl=300)
        >>> cached = await cache.get("Invoice:123")
    """

    def __init__(
        self,
        redis_url: str | None = None,
        key_prefix: str = "fm:",
    ) -> None:
        """Initialize the Redis cache adapter.

        Args:
            redis_url: Redis connection URL (defaults to REDIS_URL env var)
            key_prefix: Prefix for all cache keys (default: "fm:")
        """
        self._redis_url = redis_url or os.environ.get(
            "REDIS_URL", "redis://localhost:6379"
        )
        self._key_prefix = key_prefix
        self._redis: Any = None

    async def connect(self) -> None:
        """Connect to Redis server."""
        try:
            import redis.asyncio as redis

            self._redis = redis.from_url(self._redis_url)  # type: ignore[no-untyped-call]
            await self._redis.ping()
            logger.info("Connected to Redis at %s", self._redis_url)
        except ImportError:
            logger.error("redis package not installed. Run: pip install redis")
            raise
        except Exception as e:
            logger.error("Failed to connect to Redis: %s", str(e))
            raise

    async def disconnect(self) -> None:
        """Disconnect from Redis server."""
        if self._redis:
            await self._redis.close()
            logger.info("Disconnected from Redis")

    def _make_key(self, key: str) -> str:
        """Create prefixed cache key."""
        return f"{self._key_prefix}{key}"

    async def get(self, key: str) -> Any | None:
        """Get a value from cache."""
        if not self._redis:
            return None

        try:
            data = await self._redis.get(self._make_key(key))
            if data is None:
                return None
            return json.loads(data)
        except Exception as e:
            logger.warning("Cache get error for %s: %s", key, str(e))
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> None:
        """Set a value in cache with optional TTL."""
        if not self._redis:
            return

        try:
            data = json.dumps(value)
            if ttl:
                await self._redis.setex(self._make_key(key), ttl, data)
            else:
                await self._redis.set(self._make_key(key), data)
        except Exception as e:
            logger.warning("Cache set error for %s: %s", key, str(e))

    async def delete(self, key: str) -> None:
        """Delete a key from cache."""
        if not self._redis:
            return

        try:
            await self._redis.delete(self._make_key(key))
        except Exception as e:
            logger.warning("Cache delete error for %s: %s", key, str(e))

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        if not self._redis:
            return 0

        try:
            full_pattern = self._make_key(pattern)
            keys = await self._redis.keys(full_pattern)
            if keys:
                return int(await self._redis.delete(*keys))
            return 0
        except Exception as e:
            logger.warning("Cache delete_pattern error for %s: %s", pattern, str(e))
            return 0

    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        if not self._redis:
            return False

        try:
            return bool(await self._redis.exists(self._make_key(key)))
        except Exception as e:
            logger.warning("Cache exists error for %s: %s", key, str(e))
            return False

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values from cache."""
        if not self._redis:
            return {}

        try:
            prefixed_keys = [self._make_key(k) for k in keys]
            values = await self._redis.mget(prefixed_keys)
            results = {}
            for key, value in zip(keys, values, strict=False):
                if value is not None:
                    results[key] = json.loads(value)
            return results
        except Exception as e:
            logger.warning("Cache get_many error: %s", str(e))
            return {}

    async def set_many(
        self,
        items: dict[str, Any],
        ttl: int | None = None,
    ) -> None:
        """Set multiple values in cache."""
        if not self._redis:
            return

        try:
            pipe = self._redis.pipeline()
            for key, value in items.items():
                data = json.dumps(value)
                full_key = self._make_key(key)
                if ttl:
                    pipe.setex(full_key, ttl, data)
                else:
                    pipe.set(full_key, data)
            await pipe.execute()
        except Exception as e:
            logger.warning("Cache set_many error: %s", str(e))

    async def ttl(self, key: str) -> int | None:
        """Get remaining TTL for a key."""
        if not self._redis:
            return None

        try:
            result = await self._redis.ttl(self._make_key(key))
            return result if result >= 0 else None
        except Exception as e:
            logger.warning("Cache ttl error for %s: %s", key, str(e))
            return None

    async def clear(self) -> None:
        """Clear all keys with the cache prefix."""
        await self.delete_pattern("*")


__all__ = [
    "CacheProtocol",
    "RedisCacheAdapter",
]
