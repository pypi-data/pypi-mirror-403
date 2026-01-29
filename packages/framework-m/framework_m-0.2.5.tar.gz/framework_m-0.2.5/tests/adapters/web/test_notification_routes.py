"""Tests for Notification API Routes.

Tests cover:
- NotificationController endpoint presence
- Response models
- Helper functions
- Integration tests with TestClient
"""

import pytest
from litestar import Litestar
from litestar.testing import TestClient

from framework_m.adapters.web.notification_routes import (
    NotificationController,
    NotificationListResponse,
    NotificationResponse,
    add_notification,
    clear_notifications,
)
from framework_m.core.doctypes.notification import Notification

# =============================================================================
# Test: Import
# =============================================================================


class TestNotificationRoutesImport:
    """Tests for Notification routes import."""

    def test_import_notification_controller(self) -> None:
        """NotificationController should be importable."""
        from framework_m.adapters.web.notification_routes import NotificationController

        assert NotificationController is not None

    def test_import_response_models(self) -> None:
        """Response models should be importable."""
        from framework_m.adapters.web.notification_routes import (
            NotificationListResponse,
            NotificationResponse,
        )

        assert NotificationListResponse is not None
        assert NotificationResponse is not None


# =============================================================================
# Test: NotificationController
# =============================================================================


class TestNotificationController:
    """Tests for NotificationController."""

    def test_controller_path(self) -> None:
        """Controller should have correct path."""
        assert NotificationController.path == "/api/v1/notifications"

    def test_controller_tags(self) -> None:
        """Controller should have Notifications tag."""
        assert "Notifications" in NotificationController.tags

    def test_controller_has_list_endpoint(self) -> None:
        """Controller should have list_notifications method."""
        assert hasattr(NotificationController, "list_notifications")

    def test_controller_has_mark_read_endpoint(self) -> None:
        """Controller should have mark_as_read method."""
        assert hasattr(NotificationController, "mark_as_read")

    def test_controller_has_delete_endpoint(self) -> None:
        """Controller should have delete_notification method."""
        assert hasattr(NotificationController, "delete_notification")


# =============================================================================
# Test: NotificationResponse
# =============================================================================


class TestNotificationResponse:
    """Tests for NotificationResponse model."""

    def test_from_notification(self) -> None:
        """from_notification should convert Notification."""
        notif = Notification(
            user_id="user-001",
            subject="Test Subject",
            message="Test message",
            doctype="Invoice",
            document_id="INV-001",
        )

        response = NotificationResponse.from_notification(notif)

        assert response.user_id == "user-001"
        assert response.subject == "Test Subject"
        assert response.message == "Test message"
        assert response.doctype == "Invoice"
        assert response.document_id == "INV-001"
        assert response.read is False


# =============================================================================
# Test: NotificationListResponse
# =============================================================================


class TestNotificationListResponse:
    """Tests for NotificationListResponse model."""

    def test_create_response(self) -> None:
        """NotificationListResponse should work."""
        response = NotificationListResponse(
            notifications=[],
            total=0,
            unread_count=0,
        )

        assert response.notifications == []
        assert response.total == 0
        assert response.unread_count == 0


# =============================================================================
# Test: Helper Functions
# =============================================================================


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_add_notification(self) -> None:
        """add_notification should be callable."""
        clear_notifications()  # Reset state
        notif = Notification(
            user_id="test",
            subject="Test",
            message="Test",
        )
        # Should not raise
        add_notification(notif)

    def test_clear_notifications(self) -> None:
        """clear_notifications should be callable."""
        # Should not raise
        clear_notifications()


# =============================================================================
# Test: WebSocket Features
# =============================================================================


class TestWebSocketFeatures:
    """Tests for WebSocket notification features."""

    def test_push_notification_exists(self) -> None:
        """push_notification should be importable."""
        from framework_m.adapters.web.notification_routes import push_notification

        assert push_notification is not None

    def test_create_websocket_router_exists(self) -> None:
        """create_notification_websocket_router should be importable."""
        from framework_m.adapters.web.notification_routes import (
            create_notification_websocket_router,
        )

        assert create_notification_websocket_router is not None

    def test_create_websocket_router_returns_router(self) -> None:
        """create_notification_websocket_router should return a Router."""
        from litestar import Router

        from framework_m.adapters.web.notification_routes import (
            create_notification_websocket_router,
        )

        router = create_notification_websocket_router()
        assert isinstance(router, Router)

    def test_websocket_router_path(self) -> None:
        """WebSocket router should have correct path."""
        from framework_m.adapters.web.notification_routes import (
            create_notification_websocket_router,
        )

        router = create_notification_websocket_router()
        assert router.path == "/api/v1/notifications"


# =============================================================================
# Test: Integration Tests with TestClient
# =============================================================================


class TestNotificationControllerIntegration:
    """Integration tests for NotificationController using TestClient."""

    @pytest.fixture(autouse=True)
    def reset_notifications(self) -> None:
        """Reset notification store before each test."""
        clear_notifications()

    @pytest.fixture
    def app(self) -> Litestar:
        """Create test app with notification controller."""
        return Litestar(route_handlers=[NotificationController])

    @pytest.fixture
    def client(self, app: Litestar) -> TestClient:
        """Create test client."""
        return TestClient(app)

    def test_list_notifications_empty(self, client: TestClient) -> None:
        """GET /notifications should return empty list."""
        response = client.get("/api/v1/notifications/")

        assert response.status_code == 200
        data = response.json()
        assert data["notifications"] == []
        assert data["total"] == 0
        assert data["unread_count"] == 0

    def test_list_notifications_with_data(self, client: TestClient) -> None:
        """GET /notifications should return added notifications."""
        # Add a notification for current_user
        notif = Notification(
            user_id="current_user",
            subject="Test Subject",
            message="Test message",
        )
        add_notification(notif)

        response = client.get("/api/v1/notifications/")

        assert response.status_code == 200
        data = response.json()
        assert len(data["notifications"]) == 1
        assert data["notifications"][0]["subject"] == "Test Subject"

    def test_list_notifications_filter_by_read(self, client: TestClient) -> None:
        """GET /notifications?read=false should filter unread."""
        # Add notifications
        add_notification(
            Notification(user_id="current_user", subject="Unread 1", message="m")
        )

        response = client.get("/api/v1/notifications/?read=false")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    def test_list_notifications_pagination(self, client: TestClient) -> None:
        """GET /notifications should support limit and offset."""
        response = client.get("/api/v1/notifications/?limit=10&offset=0")

        assert response.status_code == 200

    def test_mark_notification_as_read(self, client: TestClient) -> None:
        """PATCH /notifications/{id}/read should mark as read."""
        # Add a notification
        notif = Notification(
            user_id="current_user",
            subject="To Read",
            message="m",
        )
        add_notification(notif)

        response = client.patch(f"/api/v1/notifications/{notif.id}/read")

        assert response.status_code == 200
        data = response.json()
        assert data["read"] is True

    def test_mark_notification_not_found(self, client: TestClient) -> None:
        """PATCH /notifications/{id}/read should return 404 for unknown."""
        response = client.patch("/api/v1/notifications/unknown-id/read")

        assert response.status_code == 404

    def test_delete_notification(self, client: TestClient) -> None:
        """DELETE /notifications/{id} should return 204."""
        response = client.delete("/api/v1/notifications/some-id")

        assert response.status_code == 204


# =============================================================================
# Test: push_notification
# =============================================================================


class TestPushNotification:
    """Tests for push_notification function."""

    @pytest.fixture(autouse=True)
    def reset_notifications(self) -> None:
        """Reset notification store before each test."""
        clear_notifications()

    @pytest.mark.asyncio
    async def test_push_notification_adds_to_store(self) -> None:
        """push_notification should add to notification store."""
        from unittest.mock import AsyncMock, MagicMock, patch

        from framework_m.adapters.web.notification_routes import push_notification

        # Mock the connection manager - patch in the socket module where it's defined
        mock_manager = MagicMock()
        mock_manager.send_to_user = AsyncMock()

        with patch(
            "framework_m.adapters.web.socket.get_connection_manager",
            return_value=mock_manager,
        ):
            notif = Notification(
                user_id="user-001",
                subject="Push Test",
                message="m",
            )
            await push_notification("user-001", notif)

        mock_manager.send_to_user.assert_called_once()
