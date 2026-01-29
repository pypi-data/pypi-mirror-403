"""Tests for WebSocket Socket Endpoint - Extended coverage."""

from unittest.mock import AsyncMock, MagicMock

import pytest

# =============================================================================
# Test: Socket Module Import
# =============================================================================


class TestSocketImport:
    """Tests for socket module import."""

    def test_import_connection_manager(self) -> None:
        """ConnectionManager should be importable."""
        from framework_m.adapters.web.socket import ConnectionManager

        assert ConnectionManager is not None

    def test_import_get_connection_manager(self) -> None:
        """get_connection_manager should be importable."""
        from framework_m.adapters.web.socket import get_connection_manager

        assert get_connection_manager is not None

    def test_import_stream_handler(self) -> None:
        """stream_handler should be importable."""
        from framework_m.adapters.web.socket import stream_handler

        assert stream_handler is not None

    def test_import_create_websocket_router(self) -> None:
        """create_websocket_router should be importable."""
        from framework_m.adapters.web.socket import create_websocket_router

        assert create_websocket_router is not None


# =============================================================================
# Test: ConnectionManager
# =============================================================================


class TestConnectionManager:
    """Tests for ConnectionManager class."""

    def test_init_creates_empty_connections(self) -> None:
        """ConnectionManager should initialize with empty connections."""
        from framework_m.adapters.web.socket import ConnectionManager

        manager = ConnectionManager()

        assert manager._connections == {}

    def test_register_adds_connection(self) -> None:
        """register should add connection for user."""
        from framework_m.adapters.web.socket import ConnectionManager

        manager = ConnectionManager()
        mock_ws = MagicMock()

        manager.register("user-123", mock_ws)

        assert "user-123" in manager._connections
        assert mock_ws in manager._connections["user-123"]

    def test_register_multiple_connections(self) -> None:
        """register should support multiple connections per user."""
        from framework_m.adapters.web.socket import ConnectionManager

        manager = ConnectionManager()
        mock_ws1 = MagicMock()
        mock_ws2 = MagicMock()

        manager.register("user-123", mock_ws1)
        manager.register("user-123", mock_ws2)

        assert len(manager._connections["user-123"]) == 2

    def test_unregister_removes_connection(self) -> None:
        """unregister should remove connection for user."""
        from framework_m.adapters.web.socket import ConnectionManager

        manager = ConnectionManager()
        mock_ws = MagicMock()

        manager.register("user-123", mock_ws)
        manager.unregister("user-123", mock_ws)

        assert "user-123" not in manager._connections

    def test_unregister_nonexistent_user(self) -> None:
        """unregister should handle nonexistent user gracefully."""
        from framework_m.adapters.web.socket import ConnectionManager

        manager = ConnectionManager()

        # Should not raise
        manager.unregister("nonexistent", MagicMock())

    def test_unregister_nonexistent_websocket(self) -> None:
        """unregister should handle nonexistent websocket gracefully."""
        from framework_m.adapters.web.socket import ConnectionManager

        manager = ConnectionManager()
        mock_ws1 = MagicMock()
        mock_ws2 = MagicMock()

        manager.register("user-123", mock_ws1)

        # Should not raise when removing non-registered websocket
        manager.unregister("user-123", mock_ws2)

        # Original should still be there
        assert mock_ws1 in manager._connections["user-123"]

    def test_get_connected_users(self) -> None:
        """get_connected_users should return list of user IDs."""
        from framework_m.adapters.web.socket import ConnectionManager

        manager = ConnectionManager()
        manager.register("user-1", MagicMock())
        manager.register("user-2", MagicMock())

        users = manager.get_connected_users()

        assert "user-1" in users
        assert "user-2" in users

    @pytest.mark.asyncio
    async def test_send_to_user(self) -> None:
        """send_to_user should send message to user's connections."""
        from framework_m.adapters.web.socket import ConnectionManager

        manager = ConnectionManager()
        mock_ws = AsyncMock()
        manager.register("user-123", mock_ws)

        await manager.send_to_user("user-123", {"event": "test"})

        mock_ws.send_json.assert_called_once_with({"event": "test"})

    @pytest.mark.asyncio
    async def test_send_to_user_handles_error(self) -> None:
        """send_to_user should handle send errors gracefully."""
        from framework_m.adapters.web.socket import ConnectionManager

        manager = ConnectionManager()
        mock_ws = AsyncMock()
        mock_ws.send_json.side_effect = Exception("Connection closed")
        manager.register("user-123", mock_ws)

        # Should not raise
        await manager.send_to_user("user-123", {"event": "test"})

    @pytest.mark.asyncio
    async def test_broadcast(self) -> None:
        """broadcast should send to all connected users."""
        from framework_m.adapters.web.socket import ConnectionManager

        manager = ConnectionManager()
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        manager.register("user-1", mock_ws1)
        manager.register("user-2", mock_ws2)

        await manager.broadcast({"event": "global"})

        mock_ws1.send_json.assert_called_once_with({"event": "global"})
        mock_ws2.send_json.assert_called_once_with({"event": "global"})

    @pytest.mark.asyncio
    async def test_broadcast_handles_error(self) -> None:
        """broadcast should handle errors for individual connections."""
        from framework_m.adapters.web.socket import ConnectionManager

        manager = ConnectionManager()
        mock_ws1 = AsyncMock()
        mock_ws1.send_json.side_effect = Exception("Error")
        mock_ws2 = AsyncMock()
        manager.register("user-1", mock_ws1)
        manager.register("user-2", mock_ws2)

        # Should not raise, should continue to next user
        await manager.broadcast({"event": "global"})

        # Second user should still receive
        mock_ws2.send_json.assert_called_once()


# =============================================================================
# Test: Global Connection Manager
# =============================================================================


class TestGlobalConnectionManager:
    """Tests for get_connection_manager singleton."""

    def test_returns_connection_manager(self) -> None:
        """get_connection_manager should return ConnectionManager instance."""
        from framework_m.adapters.web.socket import (
            ConnectionManager,
            get_connection_manager,
        )

        manager = get_connection_manager()

        assert isinstance(manager, ConnectionManager)

    def test_returns_singleton(self) -> None:
        """get_connection_manager should return same instance."""
        from framework_m.adapters.web.socket import get_connection_manager

        manager1 = get_connection_manager()
        manager2 = get_connection_manager()

        assert manager1 is manager2


# =============================================================================
# Test: WebSocket Router Creation
# =============================================================================


class TestWebSocketRouter:
    """Tests for create_websocket_router."""

    def test_creates_router(self) -> None:
        """create_websocket_router should return Router."""
        from litestar import Router

        from framework_m.adapters.web.socket import create_websocket_router

        router = create_websocket_router()

        assert isinstance(router, Router)

    def test_router_path(self) -> None:
        """Router should have correct path."""
        from framework_m.adapters.web.socket import create_websocket_router

        router = create_websocket_router()

        assert router.path == "/api/v1"

    def test_router_has_tags(self) -> None:
        """Router should have websocket tag."""
        from framework_m.adapters.web.socket import create_websocket_router

        router = create_websocket_router()

        assert "websocket" in router.tags
