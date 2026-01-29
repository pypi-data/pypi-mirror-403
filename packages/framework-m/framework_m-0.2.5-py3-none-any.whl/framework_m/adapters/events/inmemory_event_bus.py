"""In-Memory Event Bus - Development/testing implementation.

This module provides an in-memory implementation of EventBusProtocol
for local development and testing without external dependencies.

For production, use NATS or Redis-backed implementations.
"""

from __future__ import annotations

import fnmatch
from collections import defaultdict
from typing import TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from framework_m.core.interfaces.event_bus import Event, EventHandler


class InMemoryEventBus:
    """In-memory event bus for development and testing.

    Implements EventBusProtocol using simple Python data structures.
    Events are delivered synchronously for simplicity.

    Note:
        This implementation is NOT suitable for production multi-process
        deployments. Use NATS or Redis for distributed systems.

    Example:
        >>> bus = InMemoryEventBus()
        >>> await bus.connect()
        >>> await bus.subscribe("doc.created", handler)
        >>> await bus.publish("doc.created", event)
        >>> await bus.disconnect()
    """

    def __init__(self) -> None:
        """Initialize the in-memory event bus."""
        self._connected = False
        self._subscriptions: dict[str, dict[str, EventHandler]] = defaultdict(dict)
        self._pattern_subscriptions: dict[str, dict[str, EventHandler]] = defaultdict(
            dict
        )

    async def connect(self) -> None:
        """Establish connection (no-op for in-memory)."""
        self._connected = True

    async def disconnect(self) -> None:
        """Close connection and clear subscriptions."""
        self._connected = False
        self._subscriptions.clear()
        self._pattern_subscriptions.clear()

    def is_connected(self) -> bool:
        """Check if the event bus is connected.

        Returns:
            True if connected
        """
        return self._connected

    async def publish(self, topic: str, event: Event) -> None:
        """Publish an event to a topic.

        Delivers to all exact-match subscribers and pattern subscribers.

        Args:
            topic: The topic to publish to
            event: The event to publish
        """
        if not self._connected:
            return

        # Deliver to exact topic subscribers
        for handler in self._subscriptions.get(topic, {}).values():
            await handler(event)

        # Deliver to pattern subscribers
        for pattern, handlers in self._pattern_subscriptions.items():
            if fnmatch.fnmatch(topic, pattern):
                for handler in handlers.values():
                    await handler(event)

    async def subscribe(self, topic: str, handler: EventHandler) -> str:
        """Subscribe to events on a specific topic.

        Args:
            topic: The exact topic to subscribe to
            handler: Async function to call when event is received

        Returns:
            Subscription ID
        """
        sub_id = str(uuid4())
        self._subscriptions[topic][sub_id] = handler
        return sub_id

    async def subscribe_pattern(self, pattern: str, handler: EventHandler) -> str:
        """Subscribe to events matching a pattern.

        Uses fnmatch for pattern matching (e.g., "doc.*" matches "doc.created").

        Args:
            pattern: Pattern to match (supports * and ? wildcards)
            handler: Async function to call when matching event is received

        Returns:
            Subscription ID
        """
        sub_id = str(uuid4())
        self._pattern_subscriptions[pattern][sub_id] = handler
        return sub_id

    async def unsubscribe(self, subscription_id: str) -> None:
        """Remove a subscription.

        Args:
            subscription_id: ID returned from subscribe/subscribe_pattern
        """
        # Check exact subscriptions
        for topic in list(self._subscriptions.keys()):
            if subscription_id in self._subscriptions[topic]:
                del self._subscriptions[topic][subscription_id]
                if not self._subscriptions[topic]:
                    del self._subscriptions[topic]
                return

        # Check pattern subscriptions
        for pattern in list(self._pattern_subscriptions.keys()):
            if subscription_id in self._pattern_subscriptions[pattern]:
                del self._pattern_subscriptions[pattern][subscription_id]
                if not self._pattern_subscriptions[pattern]:
                    del self._pattern_subscriptions[pattern]
                return


__all__ = ["InMemoryEventBus"]
