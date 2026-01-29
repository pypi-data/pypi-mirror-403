"""Tests for NatsEventBusAdapter."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from framework_m.core.interfaces.event_bus import Event

# =============================================================================
# Test: NatsEventBusAdapter Import and Instantiation
# =============================================================================


class TestNatsEventBusImport:
    """Tests for NatsEventBusAdapter module import."""

    def test_import_nats_event_bus(self) -> None:
        """NatsEventBusAdapter should be importable."""
        from framework_m.adapters.events.nats_event_bus import NatsEventBusAdapter

        assert NatsEventBusAdapter is not None

    def test_nats_event_bus_instantiation(self) -> None:
        """NatsEventBusAdapter should be instantiable."""
        from framework_m.adapters.events.nats_event_bus import NatsEventBusAdapter

        bus = NatsEventBusAdapter(nats_url="nats://localhost:4222")
        assert bus is not None

    def test_nats_event_bus_default_url_from_env(self) -> None:
        """NatsEventBusAdapter should use NATS_URL env var."""
        from framework_m.adapters.events.nats_event_bus import NatsEventBusAdapter

        with patch.dict("os.environ", {"NATS_URL": "nats://test:4222"}):
            bus = NatsEventBusAdapter()
            assert bus._nats_url == "nats://test:4222"


# =============================================================================
# Test: Connection Lifecycle
# =============================================================================


class TestNatsEventBusConnection:
    """Tests for NatsEventBusAdapter connection lifecycle."""

    def test_is_connected_initially_false(self) -> None:
        """Bus should not be connected initially."""
        from framework_m.adapters.events.nats_event_bus import NatsEventBusAdapter

        bus = NatsEventBusAdapter(nats_url="nats://localhost:4222")
        assert bus.is_connected() is False

    @pytest.mark.asyncio
    async def test_connect_sets_connected(self) -> None:
        """connect() should establish connection."""
        from framework_m.adapters.events.nats_event_bus import NatsEventBusAdapter

        bus = NatsEventBusAdapter(nats_url="nats://localhost:4222")

        mock_js = Mock()
        mock_js.add_stream = AsyncMock()

        mock_nc = Mock()
        mock_nc.jetstream = Mock(return_value=mock_js)
        mock_nc.close = AsyncMock()

        with patch("nats.connect", new_callable=AsyncMock, return_value=mock_nc):
            await bus.connect()
            assert bus.is_connected() is True

    @pytest.mark.asyncio
    async def test_disconnect_closes_connection(self) -> None:
        """disconnect() should close connection."""
        from framework_m.adapters.events.nats_event_bus import NatsEventBusAdapter

        bus = NatsEventBusAdapter(nats_url="nats://localhost:4222")

        mock_js = Mock()
        mock_js.add_stream = AsyncMock()

        mock_nc = Mock()
        mock_nc.jetstream = Mock(return_value=mock_js)
        mock_nc.close = AsyncMock()

        with patch("nats.connect", new_callable=AsyncMock, return_value=mock_nc):
            await bus.connect()
            await bus.disconnect()

            mock_nc.close.assert_called_once()
            assert bus.is_connected() is False


# =============================================================================
# Test: Publish
# =============================================================================


class TestNatsEventBusPublish:
    """Tests for NatsEventBusAdapter publish functionality."""

    @pytest.mark.asyncio
    async def test_publish_serializes_event(self) -> None:
        """publish() should serialize event to JSON."""
        from framework_m.adapters.events.nats_event_bus import NatsEventBusAdapter

        bus = NatsEventBusAdapter(nats_url="nats://localhost:4222")

        mock_js = Mock()
        mock_js.add_stream = AsyncMock()
        mock_js.publish = AsyncMock()

        mock_nc = Mock()
        mock_nc.jetstream = Mock(return_value=mock_js)
        mock_nc.close = AsyncMock()

        with patch("nats.connect", new_callable=AsyncMock, return_value=mock_nc):
            await bus.connect()

            event = Event(
                id="evt-001",
                type="doc.created",
                source="test",
                timestamp=datetime.now(UTC),
            )

            await bus.publish("doc.created", event)

            # Should call js.publish with serialized data
            mock_js.publish.assert_called_once()
            call_args = mock_js.publish.call_args
            assert "events.doc.created" in call_args[0][0]


# =============================================================================
# Test: Subscribe
# =============================================================================


class TestNatsEventBusSubscribe:
    """Tests for NatsEventBusAdapter subscribe functionality."""

    @pytest.mark.asyncio
    async def test_subscribe_returns_subscription_id(self) -> None:
        """subscribe() should return subscription ID."""
        from framework_m.adapters.events.nats_event_bus import NatsEventBusAdapter

        bus = NatsEventBusAdapter(nats_url="nats://localhost:4222")

        mock_sub = Mock()
        mock_js = Mock()
        mock_js.add_stream = AsyncMock()
        mock_js.subscribe = AsyncMock(return_value=mock_sub)

        mock_nc = Mock()
        mock_nc.jetstream = Mock(return_value=mock_js)
        mock_nc.close = AsyncMock()

        with patch("nats.connect", new_callable=AsyncMock, return_value=mock_nc):
            await bus.connect()

            async def handler(event: Event) -> None:
                pass

            sub_id = await bus.subscribe("doc.created", handler)

            assert sub_id is not None
            assert isinstance(sub_id, str)

    @pytest.mark.asyncio
    async def test_unsubscribe_removes_subscription(self) -> None:
        """unsubscribe() should remove subscription."""
        from framework_m.adapters.events.nats_event_bus import NatsEventBusAdapter

        bus = NatsEventBusAdapter(nats_url="nats://localhost:4222")

        mock_sub = Mock()
        mock_sub.unsubscribe = AsyncMock()
        mock_js = Mock()
        mock_js.add_stream = AsyncMock()
        mock_js.subscribe = AsyncMock(return_value=mock_sub)

        mock_nc = Mock()
        mock_nc.jetstream = Mock(return_value=mock_js)
        mock_nc.close = AsyncMock()

        with patch("nats.connect", new_callable=AsyncMock, return_value=mock_nc):
            await bus.connect()

            async def handler(event: Event) -> None:
                pass

            sub_id = await bus.subscribe("doc.created", handler)
            await bus.unsubscribe(sub_id)

            mock_sub.unsubscribe.assert_called_once()
