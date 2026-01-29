"""Adapter Factory - Auto-selects adapters based on environment.

This module provides factory functions that automatically select
the appropriate adapter based on environment configuration.

For local development without external dependencies:
- If NATS_URL not set → InMemoryJobQueue, InMemoryEventBus
- If REDIS_URL not set → InMemoryCacheAdapter

For production:
- Set NATS_URL → TaskiqJobQueue, NatsEventBus
- Set REDIS_URL → RedisCacheAdapter
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from framework_m.core.interfaces.cache import CacheProtocol
    from framework_m.core.interfaces.event_bus import EventBusProtocol
    from framework_m.core.interfaces.job_queue import JobQueueProtocol


def get_job_queue() -> JobQueueProtocol:
    """Get the appropriate job queue based on environment.

    Returns:
        InMemoryJobQueue if NATS_URL not set,
        otherwise TaskiqJobQueue (future implementation)

    Example:
        >>> queue = get_job_queue()
        >>> job_id = await queue.enqueue("send_email", to="user@example.com")
    """
    nats_url = os.environ.get("NATS_URL")

    if nats_url:
        from framework_m.adapters.jobs.taskiq_adapter import TaskiqJobQueueAdapter

        return TaskiqJobQueueAdapter(nats_url=nats_url)

    from framework_m.adapters.jobs import InMemoryJobQueue

    return InMemoryJobQueue()


def get_event_bus() -> EventBusProtocol:
    """Get the appropriate event bus based on environment.

    Returns:
        InMemoryEventBus if NATS_URL not set,
        otherwise NatsEventBusAdapter

    Example:
        >>> bus = get_event_bus()
        >>> await bus.connect()
        >>> await bus.publish("doc.created", event)
    """
    nats_url = os.environ.get("NATS_URL")

    if nats_url:
        from framework_m.adapters.events.nats_event_bus import NatsEventBusAdapter

        return NatsEventBusAdapter(nats_url=nats_url)

    from framework_m.adapters.events.inmemory_event_bus import InMemoryEventBus

    return InMemoryEventBus()


def get_cache() -> CacheProtocol:
    """Get the appropriate cache adapter based on environment.

    Returns:
        InMemoryCacheAdapter if REDIS_URL not set,
        otherwise RedisCacheAdapter (future implementation)

    Example:
        >>> cache = get_cache()
        >>> await cache.set("key", "value", ttl=3600)
        >>> value = await cache.get("key")
    """
    redis_url = os.environ.get("REDIS_URL")

    if redis_url:
        # TODO: Return RedisCacheAdapter when implemented
        # from framework_m.adapters.cache.redis_cache import RedisCacheAdapter
        # return RedisCacheAdapter(redis_url)
        raise NotImplementedError(
            "RedisCacheAdapter not yet implemented. Unset REDIS_URL to use InMemoryCacheAdapter."
        )

    from framework_m.adapters.cache import InMemoryCacheAdapter

    return InMemoryCacheAdapter()


def is_dev_mode() -> bool:
    """Check if running in development mode (no external dependencies).

    Returns:
        True if neither NATS_URL nor REDIS_URL are set
    """
    return not os.environ.get("NATS_URL") and not os.environ.get("REDIS_URL")


__all__ = [
    "get_cache",
    "get_event_bus",
    "get_job_queue",
    "is_dev_mode",
]
