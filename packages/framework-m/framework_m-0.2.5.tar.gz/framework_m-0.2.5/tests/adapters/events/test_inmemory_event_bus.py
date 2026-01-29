"""Tests for InMemoryEventBus adapter."""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from framework_m.core.interfaces.event_bus import Event

# =============================================================================
# Test: InMemoryEventBus Implementation
# =============================================================================


class TestInMemoryEventBusConnection:
    """Tests for connection lifecycle."""

    def test_implements_protocol(self) -> None:
        """InMemoryEventBus should implement EventBusProtocol."""
        from framework_m.adapters.events.inmemory_event_bus import InMemoryEventBus

        bus = InMemoryEventBus()
        # Duck typing check - should have all protocol methods
        assert hasattr(bus, "connect")
        assert hasattr(bus, "disconnect")
        assert hasattr(bus, "is_connected")
        assert hasattr(bus, "publish")
        assert hasattr(bus, "subscribe")
        assert hasattr(bus, "unsubscribe")

    @pytest.mark.asyncio
    async def test_connect_sets_connected_state(self) -> None:
        """connect() should set is_connected to True."""
        from framework_m.adapters.events.inmemory_event_bus import InMemoryEventBus

        bus = InMemoryEventBus()
        assert not bus.is_connected()

        await bus.connect()
        assert bus.is_connected()

    @pytest.mark.asyncio
    async def test_disconnect_clears_connected_state(self) -> None:
        """disconnect() should set is_connected to False."""
        from framework_m.adapters.events.inmemory_event_bus import InMemoryEventBus

        bus = InMemoryEventBus()
        await bus.connect()
        assert bus.is_connected()

        await bus.disconnect()
        assert not bus.is_connected()


class TestInMemoryEventBusPublishSubscribe:
    """Tests for publish/subscribe functionality."""

    @pytest.mark.asyncio
    async def test_publish_to_subscriber(self) -> None:
        """Published events should be received by subscribers."""
        from framework_m.adapters.events.inmemory_event_bus import InMemoryEventBus

        bus = InMemoryEventBus()
        await bus.connect()

        received_events: list[Event] = []

        async def handler(event: Event) -> None:
            received_events.append(event)

        await bus.subscribe("test.topic", handler)

        event = Event(
            id=str(uuid4()),
            type="test.topic",
            source="test",
            data={"key": "value"},
        )
        await bus.publish("test.topic", event)

        # Give time for async delivery
        await asyncio.sleep(0.01)

        assert len(received_events) == 1
        assert received_events[0].type == "test.topic"
        assert received_events[0].data == {"key": "value"}

        await bus.disconnect()

    @pytest.mark.asyncio
    async def test_unsubscribe_stops_receiving(self) -> None:
        """unsubscribe() should stop receiving events."""
        from framework_m.adapters.events.inmemory_event_bus import InMemoryEventBus

        bus = InMemoryEventBus()
        await bus.connect()

        received_events: list[Event] = []

        async def handler(event: Event) -> None:
            received_events.append(event)

        sub_id = await bus.subscribe("test.topic", handler)

        # Unsubscribe
        await bus.unsubscribe(sub_id)

        # Publish after unsubscribe
        event = Event(
            id=str(uuid4()),
            type="test.topic",
            source="test",
        )
        await bus.publish("test.topic", event)

        await asyncio.sleep(0.01)

        assert len(received_events) == 0

        await bus.disconnect()

    @pytest.mark.asyncio
    async def test_multiple_subscribers_same_topic(self) -> None:
        """Multiple subscribers should all receive events."""
        from framework_m.adapters.events.inmemory_event_bus import InMemoryEventBus

        bus = InMemoryEventBus()
        await bus.connect()

        received_a: list[Event] = []
        received_b: list[Event] = []

        async def handler_a(event: Event) -> None:
            received_a.append(event)

        async def handler_b(event: Event) -> None:
            received_b.append(event)

        await bus.subscribe("test.topic", handler_a)
        await bus.subscribe("test.topic", handler_b)

        event = Event(
            id=str(uuid4()),
            type="test.topic",
            source="test",
        )
        await bus.publish("test.topic", event)

        await asyncio.sleep(0.01)

        assert len(received_a) == 1
        assert len(received_b) == 1

        await bus.disconnect()

    @pytest.mark.asyncio
    async def test_subscribe_pattern_wildcard(self) -> None:
        """subscribe_pattern() should match topics with wildcards."""
        from framework_m.adapters.events.inmemory_event_bus import InMemoryEventBus

        bus = InMemoryEventBus()
        await bus.connect()

        received_events: list[Event] = []

        async def handler(event: Event) -> None:
            received_events.append(event)

        # Subscribe to all doc.* events
        await bus.subscribe_pattern("doc.*", handler)

        # Publish different doc events
        await bus.publish(
            "doc.created",
            Event(id="1", type="doc.created", source="test"),
        )
        await bus.publish(
            "doc.updated",
            Event(id="2", type="doc.updated", source="test"),
        )
        await bus.publish(
            "other.topic",
            Event(id="3", type="other.topic", source="test"),
        )

        await asyncio.sleep(0.01)

        # Should receive 2 events (doc.created and doc.updated)
        assert len(received_events) == 2

        await bus.disconnect()


class TestInMemoryEventBusImport:
    """Tests for module imports."""

    def test_import_inmemory_event_bus(self) -> None:
        """InMemoryEventBus should be importable."""
        from framework_m.adapters.events.inmemory_event_bus import InMemoryEventBus

        assert InMemoryEventBus is not None


# =============================================================================
# Test: Edge Cases
# =============================================================================


class TestInMemoryEventBusEdgeCases:
    """Tests for edge cases in InMemoryEventBus."""

    @pytest.mark.asyncio
    async def test_publish_when_not_connected(self) -> None:
        """Publish should be no-op when not connected."""
        from framework_m.adapters.events.inmemory_event_bus import InMemoryEventBus

        bus = InMemoryEventBus()
        received_events: list[Event] = []

        async def handler(event: Event) -> None:
            received_events.append(event)

        await bus.subscribe("test.topic", handler)

        # Publish without connecting - should be no-op
        event = Event(id="1", type="test.topic", source="test")
        await bus.publish("test.topic", event)

        await asyncio.sleep(0.01)
        assert len(received_events) == 0

    @pytest.mark.asyncio
    async def test_disconnect_clears_all_subscriptions(self) -> None:
        """disconnect() should clear all subscriptions."""
        from framework_m.adapters.events.inmemory_event_bus import InMemoryEventBus

        bus = InMemoryEventBus()
        await bus.connect()

        received_events: list[Event] = []

        async def handler(event: Event) -> None:
            received_events.append(event)

        await bus.subscribe("test.topic", handler)

        # Disconnect clears subscriptions
        await bus.disconnect()

        # Reconnect and publish - handler should NOT receive
        await bus.connect()
        event = Event(id="1", type="test.topic", source="test")
        await bus.publish("test.topic", event)

        await asyncio.sleep(0.01)
        assert len(received_events) == 0

        await bus.disconnect()

    @pytest.mark.asyncio
    async def test_unsubscribe_with_invalid_id(self) -> None:
        """unsubscribe() with invalid ID should be no-op."""
        from framework_m.adapters.events.inmemory_event_bus import InMemoryEventBus

        bus = InMemoryEventBus()
        await bus.connect()

        # Should not raise - just no-op
        await bus.unsubscribe("nonexistent-subscription-id")

        await bus.disconnect()

    @pytest.mark.asyncio
    async def test_unsubscribe_pattern_subscription(self) -> None:
        """unsubscribe() should work for pattern subscriptions."""
        from framework_m.adapters.events.inmemory_event_bus import InMemoryEventBus

        bus = InMemoryEventBus()
        await bus.connect()

        received_events: list[Event] = []

        async def handler(event: Event) -> None:
            received_events.append(event)

        sub_id = await bus.subscribe_pattern("doc.*", handler)
        await bus.unsubscribe(sub_id)

        # Publish after unsubscribe - should not receive
        event = Event(id="1", type="doc.created", source="test")
        await bus.publish("doc.created", event)

        await asyncio.sleep(0.01)
        assert len(received_events) == 0

        await bus.disconnect()

    @pytest.mark.asyncio
    async def test_publish_to_no_subscribers(self) -> None:
        """Publish to topic with no subscribers should not raise."""
        from framework_m.adapters.events.inmemory_event_bus import InMemoryEventBus

        bus = InMemoryEventBus()
        await bus.connect()

        # Should not raise
        event = Event(id="1", type="some.topic", source="test")
        await bus.publish("some.topic", event)

        await bus.disconnect()
