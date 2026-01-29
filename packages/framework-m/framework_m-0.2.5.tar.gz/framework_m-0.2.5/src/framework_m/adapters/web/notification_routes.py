"""Notification API Routes - User notification endpoints.

This module provides REST API endpoints for notifications:
- GET /api/v1/notifications - List user's notifications
- PATCH /api/v1/notifications/{id}/read - Mark as read
- DELETE /api/v1/notifications/{id} - Delete notification

Example:
    GET /api/v1/notifications?read=false
    PATCH /api/v1/notifications/notif-001/read
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from litestar import Controller, Response, delete, get, patch
from litestar.status_codes import HTTP_200_OK, HTTP_204_NO_CONTENT
from pydantic import BaseModel

from framework_m.core.doctypes.notification import Notification

# =============================================================================
# Response Models
# =============================================================================


class NotificationResponse(BaseModel):
    """Single notification in response."""

    id: str
    user_id: str
    subject: str
    message: str
    notification_type: str
    read: bool
    doctype: str | None = None
    document_id: str | None = None
    timestamp: datetime
    from_user: str | None = None

    @classmethod
    def from_notification(cls, notif: Notification) -> NotificationResponse:
        """Create from Notification DocType."""
        return cls(
            id=str(notif.id),
            user_id=notif.user_id,
            subject=notif.subject,
            message=notif.message,
            notification_type=notif.notification_type,
            read=notif.read,
            doctype=notif.doctype,
            document_id=notif.document_id,
            timestamp=notif.timestamp,
            from_user=notif.from_user,
        )


class NotificationListResponse(BaseModel):
    """Response for notification list."""

    notifications: list[NotificationResponse]
    total: int
    unread_count: int


# =============================================================================
# Notification Controller
# =============================================================================


# In-memory storage for testing
_notifications: list[Notification] = []


class NotificationController(Controller):
    """Notification API controller.

    Provides endpoints for managing user notifications.

    Attributes:
        path: Base path for all endpoints
        tags: OpenAPI tags for documentation
    """

    path = "/api/v1/notifications"
    tags = ["Notifications"]  # noqa: RUF012

    @get("/")
    async def list_notifications(
        self,
        read: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Response[Any]:
        """List user's notifications.

        Args:
            read: Filter by read status (True/False/None for all)
            limit: Maximum results (default 50)
            offset: Pagination offset

        Returns:
            NotificationListResponse with notifications
        """
        # TODO: Get current user from auth context
        user_id = "current_user"

        # Filter notifications
        filtered = [n for n in _notifications if n.user_id == user_id]

        if read is not None:
            filtered = [n for n in filtered if n.read == read]

        # Sort by timestamp descending (newest first)
        filtered.sort(key=lambda n: n.timestamp, reverse=True)

        # Calculate unread count
        unread_count = len(
            [n for n in _notifications if n.user_id == user_id and not n.read]
        )

        # Apply pagination
        total = len(filtered)
        filtered = filtered[offset : offset + limit]

        response = NotificationListResponse(
            notifications=[NotificationResponse.from_notification(n) for n in filtered],
            total=total,
            unread_count=unread_count,
        )

        return Response(
            content=response.model_dump_json(),
            status_code=HTTP_200_OK,
            media_type="application/json",
        )

    @patch("/{notification_id:str}/read")
    async def mark_as_read(
        self,
        notification_id: str,
    ) -> Response[Any]:
        """Mark a notification as read.

        Args:
            notification_id: ID of the notification to mark

        Returns:
            Updated notification
        """
        # Find notification
        for notif in _notifications:
            if str(notif.id) == notification_id:
                # Mark as read (in real impl, update via repository)
                # notif.read = True  # Would need mutable model
                response = NotificationResponse.from_notification(notif)
                response.read = True

                return Response(
                    content=response.model_dump_json(),
                    status_code=HTTP_200_OK,
                    media_type="application/json",
                )

        # Not found - return empty success for idempotency
        return Response(
            content='{"error": "Not found"}',
            status_code=404,
            media_type="application/json",
        )

    @delete("/{notification_id:str}")
    async def delete_notification(
        self,
        notification_id: str,
    ) -> Response[None]:
        """Delete a notification.

        Args:
            notification_id: ID of the notification to delete

        Returns:
            204 No Content on success
        """
        # TODO: Delete via repository
        # For now, just return success
        return Response(
            content=None,
            status_code=HTTP_204_NO_CONTENT,
        )


# =============================================================================
# Helper Functions
# =============================================================================


def add_notification(notification: Notification) -> None:
    """Add a notification to the store.

    Used for creating notifications from events/hooks.
    """
    _notifications.append(notification)


def clear_notifications() -> None:
    """Clear all notifications (for testing)."""
    _notifications.clear()


# =============================================================================
# WebSocket Notification Stream
# =============================================================================


async def push_notification(user_id: str, notification: Notification) -> None:
    """Push a notification to a connected user via WebSocket.

    If the user has an active WebSocket connection, the notification
    is sent immediately. Otherwise, it's stored for later retrieval.

    Args:
        user_id: Target user ID
        notification: The notification to push

    Example:
        await push_notification("user-001", notification)
    """
    from framework_m.adapters.web.socket import get_connection_manager

    # Add to storage
    _notifications.append(notification)

    # Push via WebSocket if connected
    manager = get_connection_manager()
    await manager.send_to_user(
        user_id,
        {
            "type": "notification",
            "data": NotificationResponse.from_notification(notification).model_dump(
                mode="json"
            ),
        },
    )


def create_notification_websocket_router() -> Any:
    """Create a WebSocket router for notifications.

    Returns a Litestar Router that handles the notification stream endpoint.
    Clients connect to /api/v1/notifications/stream with a token.

    Returns:
        Litestar Router with notification WebSocket endpoint

    Example:
        router = create_notification_websocket_router()
        app = Litestar(route_handlers=[router])
    """
    import logging

    from litestar import Router, websocket
    from litestar.connection import WebSocket

    from framework_m.adapters.web.socket import get_connection_manager

    logger = logging.getLogger(__name__)

    @websocket("/stream")
    async def notification_stream(socket: WebSocket) -> None:  # type: ignore[type-arg]
        """WebSocket endpoint for real-time notifications.

        Clients connect with a token query parameter for authentication.
        Once connected, they receive real-time notifications.

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

        logger.info("Notification stream connected: %s", user_id)

        try:
            # Keep connection alive
            while True:
                # Wait for client messages (ping/pong, etc.)
                data = await socket.receive_json()
                logger.debug("Notification stream message from %s: %s", user_id, data)
        except Exception as e:
            logger.info("Notification stream closed for %s: %s", user_id, str(e))
        finally:
            manager.unregister(user_id, socket)

    return Router(
        path="/api/v1/notifications",
        route_handlers=[notification_stream],
        tags=["Notifications"],
    )


__all__ = [
    "NotificationController",
    "NotificationListResponse",
    "NotificationResponse",
    "add_notification",
    "clear_notifications",
    "create_notification_websocket_router",
    "push_notification",
]
