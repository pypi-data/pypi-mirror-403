"""Tests for EventBusProtocol interface compliance."""

from datetime import UTC, datetime

from framework_m.core.interfaces.event_bus import (
    Event,
    EventBusProtocol,
)


class TestEvent:
    """Tests for Event model."""

    def test_event_creation(self) -> None:
        """Event should create with all required fields."""
        event = Event(
            id="evt-001",
            type="doc.created",
            source="framework_m",
            data={"doctype": "Todo", "name": "TODO-001"},
        )
        assert event.id == "evt-001"
        assert event.type == "doc.created"
        assert event.source == "framework_m"
        assert event.data == {"doctype": "Todo", "name": "TODO-001"}

    def test_event_has_timestamp(self) -> None:
        """Event should have timestamp defaulting to now."""
        event = Event(
            id="evt-001",
            type="doc.created",
            source="test",
        )
        assert event.timestamp is not None
        assert isinstance(event.timestamp, datetime)

    def test_event_with_explicit_timestamp(self) -> None:
        """Event should accept explicit timestamp."""
        ts = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        event = Event(
            id="evt-001",
            type="doc.created",
            source="test",
            timestamp=ts,
        )
        assert event.timestamp == ts

    def test_event_data_optional(self) -> None:
        """Event data should be optional (default to None)."""
        event = Event(
            id="evt-001",
            type="doc.created",
            source="test",
        )
        assert event.data is None

    def test_event_subject_optional(self) -> None:
        """Event subject should be optional."""
        event = Event(
            id="evt-001",
            type="doc.created",
            source="test",
            subject="Todo:TODO-001",
        )
        assert event.subject == "Todo:TODO-001"


class TestEventBusProtocol:
    """Tests for EventBusProtocol interface."""

    def test_protocol_has_connect_method(self) -> None:
        """EventBusProtocol should define connect method."""
        assert hasattr(EventBusProtocol, "connect")

    def test_protocol_has_disconnect_method(self) -> None:
        """EventBusProtocol should define disconnect method."""
        assert hasattr(EventBusProtocol, "disconnect")

    def test_protocol_has_is_connected_method(self) -> None:
        """EventBusProtocol should define is_connected method."""
        assert hasattr(EventBusProtocol, "is_connected")

    def test_protocol_has_publish_method(self) -> None:
        """EventBusProtocol should define publish method."""
        assert hasattr(EventBusProtocol, "publish")

    def test_protocol_has_subscribe_method(self) -> None:
        """EventBusProtocol should define subscribe method."""
        assert hasattr(EventBusProtocol, "subscribe")

    def test_protocol_has_subscribe_pattern_method(self) -> None:
        """EventBusProtocol should define subscribe_pattern method."""
        assert hasattr(EventBusProtocol, "subscribe_pattern")

    def test_protocol_has_unsubscribe_method(self) -> None:
        """EventBusProtocol should define unsubscribe method."""
        assert hasattr(EventBusProtocol, "unsubscribe")
