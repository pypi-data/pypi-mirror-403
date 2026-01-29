"""Event Bus Protocol - Core interface for publish/subscribe messaging.

This module defines the EventBusProtocol for event-driven architecture.
Supports various backends: Redis Pub/Sub, NATS, Kafka, etc.

Events follow CloudEvents specification format.
"""

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any, Protocol

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(UTC)


def _generate_id() -> str:
    """Generate a unique event ID."""
    from uuid import uuid4

    return str(uuid4())


class Event(BaseModel):
    """Event model following CloudEvents specification.

    Represents a domain event that can be published and subscribed to.
    Used for decoupled communication between system components.

    Attributes:
        id: Unique identifier for the event (auto-generated)
        type: Event type (e.g., "doc.created", "doc.updated")
        source: Origin of the event (defaults to "framework_m")
        timestamp: When the event occurred (defaults to now)
        subject: Optional subject/target (e.g., "Todo:TODO-001")
        data: Optional event payload data

    Example:
        event = Event(
            type="doc.created",
            data={"doctype": "Todo", "name": "TODO-001"}
        )
    """

    id: str = Field(default_factory=_generate_id)
    type: str
    source: str = Field(default="framework_m")
    timestamp: datetime = Field(default_factory=_utc_now)
    subject: str | None = None
    data: dict[str, Any] | None = None


# Type alias for event handlers
EventHandler = Callable[[Event], Awaitable[None]]


class EventBusProtocol(Protocol):
    """Protocol defining the contract for event bus implementations.

    This is the primary port for pub/sub messaging in the hexagonal architecture.
    Supports connection lifecycle, publishing, and subscribing with patterns.

    Implementations include:
    - RedisEventBus: Redis Pub/Sub for simple use cases
    - NatsEventBus: NATS for high-performance messaging
    - KafkaEventBus: Kafka for durable event streaming

    Example usage:
        bus: EventBusProtocol = container.get(EventBusProtocol)
        await bus.connect()

        async def handler(event: Event) -> None:
            print(f"Received: {event.type}")

        sub_id = await bus.subscribe("doc.created", handler)
        await bus.publish("doc.created", event)
        await bus.unsubscribe(sub_id)

        await bus.disconnect()
    """

    async def connect(self) -> None:
        """Establish connection to the message broker.

        Should be called before publishing or subscribing.
        For Redis Pub/Sub this is optional, but required for NATS/Kafka.
        """
        ...

    async def disconnect(self) -> None:
        """Close connection to the message broker.

        Should be called during application shutdown.
        Cleans up all subscriptions.
        """
        ...

    def is_connected(self) -> bool:
        """Check if connected to the message broker.

        Returns:
            True if connected and ready to publish/subscribe
        """
        ...

    async def publish(self, topic: str, event: Event) -> None:
        """Publish an event to a topic.

        Args:
            topic: The topic/channel to publish to (e.g., "doc.created")
            event: The event to publish
        """
        ...

    async def subscribe(
        self,
        topic: str,
        handler: EventHandler,
    ) -> str:
        """Subscribe to events on a specific topic.

        Args:
            topic: The exact topic to subscribe to
            handler: Async function to call when event is received

        Returns:
            Subscription ID for later unsubscribing
        """
        ...

    async def subscribe_pattern(
        self,
        pattern: str,
        handler: EventHandler,
    ) -> str:
        """Subscribe to events matching a pattern.

        Supports wildcards for flexible subscriptions.
        Pattern syntax depends on implementation (e.g., "doc.*" for Redis).

        Args:
            pattern: Pattern to match topics (e.g., "doc.*", "user.>")
            handler: Async function to call when matching event is received

        Returns:
            Subscription ID for later unsubscribing
        """
        ...

    async def unsubscribe(self, subscription_id: str) -> None:
        """Remove a subscription.

        Args:
            subscription_id: ID returned from subscribe/subscribe_pattern
        """
        ...


__all__ = [
    "Event",
    "EventBusProtocol",
    "EventHandler",
]
