"""WebSocket Endpoint - Real-time streaming with ConnectionManager.

This module provides the WebSocket endpoint and ConnectionManager
for real-time communication with clients.

Example:
    >>> from litestar import Litestar
    >>> from framework_m.adapters.web.socket import create_websocket_router
    >>> router = create_websocket_router()
    >>> app = Litestar(route_handlers=[router])
"""

from __future__ import annotations

import logging
from typing import Any

from litestar import Router, websocket
from litestar.connection import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections.

    Stores connections by user ID, allowing targeted messaging
    and broadcast to all connected clients.

    Example:
        >>> manager = ConnectionManager()
        >>> manager.register("user-123", websocket)
        >>> await manager.send_to_user("user-123", {"event": "update"})
        >>> manager.unregister("user-123", websocket)
    """

    def __init__(self) -> None:
        """Initialize with empty connection storage."""
        self._connections: dict[str, list[WebSocket]] = {}  # type: ignore[type-arg]

    def register(self, user_id: str, websocket: WebSocket) -> None:  # type: ignore[type-arg]
        """Register a WebSocket connection for a user.

        Args:
            user_id: The user's ID
            websocket: The WebSocket connection
        """
        if user_id not in self._connections:
            self._connections[user_id] = []
        self._connections[user_id].append(websocket)
        logger.info("Registered connection for user %s", user_id)

    def unregister(self, user_id: str, websocket: WebSocket) -> None:  # type: ignore[type-arg]
        """Unregister a WebSocket connection for a user.

        Args:
            user_id: The user's ID
            websocket: The WebSocket connection to remove
        """
        if user_id in self._connections:
            try:
                self._connections[user_id].remove(websocket)
                if not self._connections[user_id]:
                    del self._connections[user_id]
                logger.info("Unregistered connection for user %s", user_id)
            except ValueError:
                pass  # Connection not in list

    async def send_to_user(self, user_id: str, message: dict[str, Any]) -> None:
        """Send a message to all connections for a user.

        Args:
            user_id: The user's ID
            message: The message to send
        """
        connections = self._connections.get(user_id, [])
        for ws in connections:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.error("Failed to send to user %s: %s", user_id, str(e))

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast a message to all connected clients.

        Args:
            message: The message to send
        """
        for user_id, connections in self._connections.items():
            for ws in connections:
                try:
                    await ws.send_json(message)
                except Exception as e:
                    logger.error("Failed to broadcast to %s: %s", user_id, str(e))

    def get_connected_users(self) -> list[str]:
        """Get list of connected user IDs.

        Returns:
            List of user IDs with active connections
        """
        return list(self._connections.keys())


# Global connection manager singleton
_connection_manager: ConnectionManager | None = None


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager singleton.

    Returns:
        The ConnectionManager instance
    """
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager


@websocket("/stream")
async def stream_handler(socket: WebSocket) -> None:  # type: ignore[type-arg]
    """WebSocket endpoint for real-time streaming.

    Clients connect with a token query parameter for authentication.
    Once connected, they receive real-time events.

    Args:
        socket: The WebSocket connection

    Query Params:
        token: Authentication token (JWT or API key)
    """
    # Get token from query params
    token = socket.query_params.get("token")
    if not token:
        await socket.close(code=4001, reason="Missing authentication token")
        return

    # TODO: Validate token and extract user_id
    # For now, use token as user_id for development
    user_id = token

    await socket.accept()
    manager = get_connection_manager()
    manager.register(user_id, socket)

    try:
        # Keep connection alive, listen for messages
        while True:
            data = await socket.receive_json()
            # Handle client messages if needed
            logger.debug("Received from %s: %s", user_id, data)
    except Exception as e:
        logger.info("Connection closed for %s: %s", user_id, str(e))
    finally:
        manager.unregister(user_id, socket)


def create_websocket_router() -> Router:
    """Create the WebSocket router.

    Returns:
        Litestar Router with WebSocket endpoints
    """
    return Router(
        path="/api/v1",
        route_handlers=[stream_handler],
        tags=["websocket"],
    )


__all__ = [
    "ConnectionManager",
    "create_websocket_router",
    "get_connection_manager",
    "stream_handler",
]
