"""Tests for SocketProtocol interface."""

from typing import Protocol

import pytest

# =============================================================================
# Test: SocketProtocol Import
# =============================================================================


class TestSocketProtocolImport:
    """Tests for SocketProtocol import."""

    def test_import_socket_protocol(self) -> None:
        """SocketProtocol should be importable."""
        from framework_m.core.interfaces.socket import SocketProtocol

        assert SocketProtocol is not None

    def test_socket_protocol_is_protocol(self) -> None:
        """SocketProtocol should be a Protocol class."""
        from framework_m.core.interfaces.socket import SocketProtocol

        assert hasattr(SocketProtocol, "__protocol_attrs__") or issubclass(
            SocketProtocol, Protocol
        )

    def test_socket_protocol_is_runtime_checkable(self) -> None:
        """SocketProtocol should be runtime checkable."""
        from framework_m.core.interfaces.socket import SocketProtocol

        # RuntimeCheckable protocols can be used with isinstance()
        assert hasattr(SocketProtocol, "_is_runtime_protocol")


# =============================================================================
# Test: SocketProtocol Methods
# =============================================================================


class TestSocketProtocolMethods:
    """Tests for SocketProtocol methods."""

    def test_socket_protocol_has_broadcast(self) -> None:
        """SocketProtocol should have broadcast method."""
        from framework_m.core.interfaces.socket import SocketProtocol

        assert hasattr(SocketProtocol, "broadcast")

    def test_socket_protocol_has_send_to_user(self) -> None:
        """SocketProtocol should have send_to_user method."""
        from framework_m.core.interfaces.socket import SocketProtocol

        assert hasattr(SocketProtocol, "send_to_user")


# =============================================================================
# Test: InMemorySocket Implementation
# =============================================================================


class TestInMemorySocket:
    """Tests for InMemorySocket adapter."""

    def test_import_in_memory_socket(self) -> None:
        """InMemorySocket should be importable."""
        from framework_m.core.interfaces.socket import InMemorySocket

        assert InMemorySocket is not None

    def test_in_memory_socket_implements_protocol(self) -> None:
        """InMemorySocket should implement SocketProtocol."""
        from framework_m.core.interfaces.socket import InMemorySocket, SocketProtocol

        socket = InMemorySocket()
        assert isinstance(socket, SocketProtocol)

    @pytest.mark.asyncio
    async def test_broadcast_stores_message(self) -> None:
        """broadcast should store message."""
        from framework_m.core.interfaces.socket import InMemorySocket

        socket = InMemorySocket()
        await socket.broadcast("test.topic", {"data": "value"})

        assert len(socket.broadcasts) == 1
        assert socket.broadcasts[0] == ("test.topic", {"data": "value"})

    @pytest.mark.asyncio
    async def test_send_to_user_stores_message(self) -> None:
        """send_to_user should store message."""
        from framework_m.core.interfaces.socket import InMemorySocket

        socket = InMemorySocket()
        await socket.send_to_user("user-123", {"event": "update"})

        assert len(socket.user_messages) == 1
        assert socket.user_messages[0] == ("user-123", {"event": "update"})

    @pytest.mark.asyncio
    async def test_get_user_messages(self) -> None:
        """get_user_messages should return messages for user."""
        from framework_m.core.interfaces.socket import InMemorySocket

        socket = InMemorySocket()
        await socket.send_to_user("user-123", {"event": "one"})
        await socket.send_to_user("user-456", {"event": "two"})
        await socket.send_to_user("user-123", {"event": "three"})

        msgs = socket.get_user_messages("user-123")
        assert len(msgs) == 2
        assert msgs[0] == {"event": "one"}
        assert msgs[1] == {"event": "three"}


# =============================================================================
# Test: Module Exports
# =============================================================================


class TestSocketModuleExports:
    """Tests for socket module exports."""

    def test_socket_protocol_in_all(self) -> None:
        """SocketProtocol should be in __all__."""
        from framework_m.core.interfaces import socket

        assert "SocketProtocol" in socket.__all__

    def test_in_memory_socket_in_all(self) -> None:
        """InMemorySocket should be in __all__."""
        from framework_m.core.interfaces import socket

        assert "InMemorySocket" in socket.__all__
