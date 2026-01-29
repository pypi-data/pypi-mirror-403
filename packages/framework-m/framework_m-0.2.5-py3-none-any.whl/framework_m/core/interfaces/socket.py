"""SocketProtocol - Real-time communication interface.

This module defines the SocketProtocol for real-time WebSocket
communication, allowing switching between backplanes (Redis/NATS/Memory).

Example:
    >>> socket = InMemorySocket()
    >>> await socket.broadcast("doc.updated", {"doctype": "Invoice", "name": "INV-001"})
    >>> await socket.send_to_user("user-123", {"event": "notification", "message": "New invoice"})
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class SocketProtocol(Protocol):
    """Protocol for real-time WebSocket communication.

    Defines the interface for broadcasting messages and sending
    targeted messages to specific users. Implementations may use
    different backplanes (Redis, NATS, in-memory).

    Example:
        >>> class NatsSocket:
        ...     async def broadcast(self, topic: str, message: dict) -> None:
        ...         await self.nc.publish(f"ws.{topic}", json.dumps(message))
        ...
        ...     async def send_to_user(self, user_id: str, message: dict) -> None:
        ...         await self.nc.publish(f"ws.user.{user_id}", json.dumps(message))
    """

    async def broadcast(self, topic: str, message: dict[str, Any]) -> None:
        """Broadcast a message to all subscribers of a topic.

        Args:
            topic: The topic/channel to broadcast to (e.g., "doc.updated")
            message: The message payload to send
        """
        ...

    async def send_to_user(self, user_id: str, message: dict[str, Any]) -> None:
        """Send a message to a specific user.

        Args:
            user_id: The user ID to send to
            message: The message payload to send
        """
        ...


class InMemorySocket:
    """In-memory socket for development and testing.

    Stores broadcasts and user messages in memory for inspection.
    For production, use NatsSocketAdapter or RedisSocketAdapter.

    Example:
        >>> socket = InMemorySocket()
        >>> await socket.broadcast("test.topic", {"data": "value"})
        >>> socket.broadcasts
        [("test.topic", {"data": "value"})]
    """

    def __init__(self) -> None:
        """Initialize with empty message storage."""
        self.broadcasts: list[tuple[str, dict[str, Any]]] = []
        self.user_messages: list[tuple[str, dict[str, Any]]] = []

    async def broadcast(self, topic: str, message: dict[str, Any]) -> None:
        """Broadcast a message (stores in memory)."""
        self.broadcasts.append((topic, message))

    async def send_to_user(self, user_id: str, message: dict[str, Any]) -> None:
        """Send a message to a user (stores in memory)."""
        self.user_messages.append((user_id, message))

    def get_user_messages(self, user_id: str) -> list[dict[str, Any]]:
        """Get all messages sent to a specific user.

        Args:
            user_id: The user ID to get messages for

        Returns:
            List of messages sent to this user
        """
        return [msg for uid, msg in self.user_messages if uid == user_id]

    def clear(self) -> None:
        """Clear all stored messages."""
        self.broadcasts.clear()
        self.user_messages.clear()


__all__ = [
    "InMemorySocket",
    "SocketProtocol",
]
