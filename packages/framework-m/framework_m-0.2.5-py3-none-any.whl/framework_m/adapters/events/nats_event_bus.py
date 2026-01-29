"""NATS Event Bus - Production implementation using NATS JetStream.

This module provides a production-ready implementation of EventBusProtocol
using NATS JetStream for reliable, distributed pub/sub messaging.

For local development without NATS, use InMemoryEventBus instead.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
from typing import TYPE_CHECKING, Any
from uuid import uuid4

import nats

from framework_m.core.interfaces.event_bus import Event

if TYPE_CHECKING:
    from nats.aio.client import Client
    from nats.js import JetStreamContext

    from framework_m.core.interfaces.event_bus import EventHandler


class NatsEventBusAdapter:
    """NATS JetStream implementation of EventBusProtocol.

    Provides reliable pub/sub messaging for distributed systems.
    Uses JetStream for message persistence and delivery guarantees.

    Example:
        >>> bus = NatsEventBusAdapter(nats_url="nats://localhost:4222")
        >>> await bus.connect()
        >>> await bus.subscribe("doc.created", handler)
        >>> await bus.publish("doc.created", event)
        >>> await bus.disconnect()
    """

    def __init__(self, nats_url: str | None = None) -> None:
        """Initialize the NATS event bus.

        Args:
            nats_url: NATS server URL (defaults to NATS_URL env var)
        """
        self._nats_url = nats_url or os.environ.get("NATS_URL", "nats://localhost:4222")
        self._nc: Client | None = None
        self._js: JetStreamContext | None = None
        self._connected = False
        self._subscriptions: dict[str, Any] = {}
        self._consumer_tasks: dict[str, asyncio.Task[None]] = {}

    async def connect(self) -> None:
        """Establish connection to NATS and create JetStream context.

        Creates the 'events' stream if it doesn't exist.
        """
        self._nc = await nats.connect(self._nats_url)
        self._js = self._nc.jetstream()

        # Ensure events stream exists
        with contextlib.suppress(Exception):
            await self._js.add_stream(
                name="events",
                subjects=["events.*", "events.>"],
            )

        self._connected = True

    async def disconnect(self) -> None:
        """Close connection to NATS.

        Cancels all consumer tasks and subscriptions.
        """
        # Cancel consumer tasks
        for task in self._consumer_tasks.values():
            task.cancel()
        self._consumer_tasks.clear()

        # Clear subscriptions
        self._subscriptions.clear()

        # Close NATS connection
        if self._nc:
            await self._nc.close()
            self._nc = None
            self._js = None

        self._connected = False

    def is_connected(self) -> bool:
        """Check if connected to NATS.

        Returns:
            True if connected
        """
        return self._connected

    async def publish(self, topic: str, event: Event) -> None:
        """Publish an event to a topic.

        Args:
            topic: Topic to publish to (e.g., "doc.created")
            event: Event to publish
        """
        if not self._connected or not self._js:
            return

        # Serialize event to JSON bytes
        data = event.model_dump_json().encode()

        # Publish to JetStream
        await self._js.publish(f"events.{topic}", data)

    async def subscribe(self, topic: str, handler: EventHandler) -> str:
        """Subscribe to events on a topic.

        Args:
            topic: Topic to subscribe to
            handler: Async function to call when event is received

        Returns:
            Subscription ID
        """
        if not self._js:
            raise RuntimeError("Not connected to NATS")

        # Create push subscription
        sub = await self._js.subscribe(f"events.{topic}")

        sub_id = str(uuid4())
        self._subscriptions[sub_id] = sub

        # Start consumer task
        task = asyncio.create_task(self._consume(sub, handler))
        self._consumer_tasks[sub_id] = task

        return sub_id

    async def subscribe_pattern(self, pattern: str, handler: EventHandler) -> str:
        """Subscribe to events matching a pattern.

        Uses NATS wildcard syntax:
        - '*' matches single token
        - '>' matches multiple tokens

        Args:
            pattern: Pattern to match (e.g., "doc.*")
            handler: Async function to call

        Returns:
            Subscription ID
        """
        if not self._js:
            raise RuntimeError("Not connected to NATS")

        # Create subscription with pattern
        sub = await self._js.subscribe(f"events.{pattern}")

        sub_id = str(uuid4())
        self._subscriptions[sub_id] = sub

        # Start consumer task
        task = asyncio.create_task(self._consume(sub, handler))
        self._consumer_tasks[sub_id] = task

        return sub_id

    async def unsubscribe(self, subscription_id: str) -> None:
        """Remove a subscription.

        Args:
            subscription_id: ID returned from subscribe
        """
        if subscription_id in self._subscriptions:
            sub = self._subscriptions.pop(subscription_id)
            await sub.unsubscribe()

        if subscription_id in self._consumer_tasks:
            task = self._consumer_tasks.pop(subscription_id)
            task.cancel()

    async def _consume(self, sub: Any, handler: EventHandler) -> None:
        """Consume messages from subscription and call handler.

        Args:
            sub: NATS subscription
            handler: Event handler function
        """
        try:
            async for msg in sub.messages:
                try:
                    # Deserialize event
                    event = Event.model_validate_json(msg.data)
                    await handler(event)
                    await msg.ack()
                except Exception:
                    # Log error but continue consuming
                    pass
        except asyncio.CancelledError:
            pass


__all__ = ["NatsEventBusAdapter"]
