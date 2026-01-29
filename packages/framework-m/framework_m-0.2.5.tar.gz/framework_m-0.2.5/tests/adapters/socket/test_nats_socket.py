"""Tests for NATS Socket Adapter."""

from unittest.mock import AsyncMock, patch

import pytest

# =============================================================================
# Test: NatsSocketAdapter Import
# =============================================================================


class TestNatsSocketAdapterImport:
    """Tests for NatsSocketAdapter import."""

    def test_import_nats_socket_adapter(self) -> None:
        """NatsSocketAdapter should be importable."""
        from framework_m.adapters.socket.nats_socket import NatsSocketAdapter

        assert NatsSocketAdapter is not None

    def test_nats_socket_adapter_implements_protocol(self) -> None:
        """NatsSocketAdapter should implement SocketProtocol."""
        from framework_m.adapters.socket.nats_socket import NatsSocketAdapter
        from framework_m.core.interfaces.socket import SocketProtocol

        adapter = NatsSocketAdapter(nats_url="nats://localhost:4222")
        assert isinstance(adapter, SocketProtocol)


# =============================================================================
# Test: NatsSocketAdapter Connection
# =============================================================================


class TestNatsSocketAdapterConnection:
    """Tests for NatsSocketAdapter connection."""

    @pytest.mark.asyncio
    async def test_connect_creates_client(self) -> None:
        """connect should create NATS client."""
        from framework_m.adapters.socket.nats_socket import NatsSocketAdapter

        adapter = NatsSocketAdapter(nats_url="nats://localhost:4222")

        with patch("nats.connect", new_callable=AsyncMock) as mock_connect:
            mock_nc = AsyncMock()
            mock_connect.return_value = mock_nc

            await adapter.connect()

            mock_connect.assert_called_once_with("nats://localhost:4222")
            assert adapter._nc == mock_nc

    @pytest.mark.asyncio
    async def test_disconnect_closes_client(self) -> None:
        """disconnect should close NATS client."""
        from framework_m.adapters.socket.nats_socket import NatsSocketAdapter

        adapter = NatsSocketAdapter(nats_url="nats://localhost:4222")
        mock_nc = AsyncMock()
        adapter._nc = mock_nc

        await adapter.disconnect()

        mock_nc.close.assert_called_once()


# =============================================================================
# Test: NatsSocketAdapter Broadcast
# =============================================================================


class TestNatsSocketAdapterBroadcast:
    """Tests for NatsSocketAdapter broadcast."""

    @pytest.mark.asyncio
    async def test_broadcast_publishes_to_nats(self) -> None:
        """broadcast should publish message to NATS."""
        from framework_m.adapters.socket.nats_socket import NatsSocketAdapter

        adapter = NatsSocketAdapter(nats_url="nats://localhost:4222")
        mock_nc = AsyncMock()
        adapter._nc = mock_nc

        await adapter.broadcast("doc.updated", {"doctype": "Invoice"})

        mock_nc.publish.assert_called_once()
        call_args = mock_nc.publish.call_args
        assert call_args[0][0] == "ws.doc.updated"

    @pytest.mark.asyncio
    async def test_broadcast_encodes_message_as_json(self) -> None:
        """broadcast should encode message as JSON."""
        import json

        from framework_m.adapters.socket.nats_socket import NatsSocketAdapter

        adapter = NatsSocketAdapter(nats_url="nats://localhost:4222")
        mock_nc = AsyncMock()
        adapter._nc = mock_nc

        await adapter.broadcast("test", {"key": "value"})

        call_args = mock_nc.publish.call_args
        payload = call_args[0][1]
        assert json.loads(payload) == {"key": "value"}


# =============================================================================
# Test: NatsSocketAdapter Send to User
# =============================================================================


class TestNatsSocketAdapterSendToUser:
    """Tests for NatsSocketAdapter send_to_user."""

    @pytest.mark.asyncio
    async def test_send_to_user_publishes_to_user_channel(self) -> None:
        """send_to_user should publish to user-specific channel."""
        from framework_m.adapters.socket.nats_socket import NatsSocketAdapter

        adapter = NatsSocketAdapter(nats_url="nats://localhost:4222")
        mock_nc = AsyncMock()
        adapter._nc = mock_nc

        await adapter.send_to_user("user-123", {"event": "notification"})

        mock_nc.publish.assert_called_once()
        call_args = mock_nc.publish.call_args
        assert call_args[0][0] == "ws.user.user-123"


# =============================================================================
# Test: NatsSocketAdapter Subscription
# =============================================================================


class TestNatsSocketAdapterSubscription:
    """Tests for NatsSocketAdapter subscription."""

    @pytest.mark.asyncio
    async def test_subscribe_to_events(self) -> None:
        """subscribe should subscribe to framework events."""
        from framework_m.adapters.socket.nats_socket import NatsSocketAdapter

        adapter = NatsSocketAdapter(nats_url="nats://localhost:4222")
        mock_nc = AsyncMock()
        adapter._nc = mock_nc

        callback = AsyncMock()
        await adapter.subscribe("ws.>", callback)

        mock_nc.subscribe.assert_called_once()
