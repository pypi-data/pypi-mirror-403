"""Tests for Auth API routes.

TDD: This test file is created BEFORE the implementation.

Tests cover:
- GET /api/v1/auth/me - returns current user context
- POST /api/v1/auth/login - authenticates and returns token
- POST /api/v1/auth/logout - clears session
"""

from unittest.mock import AsyncMock

import pytest

# =============================================================================
# Test: Auth Routes Import
# =============================================================================


class TestAuthRoutesImport:
    """Tests for auth_routes module import."""

    def test_import_auth_routes_router(self) -> None:
        """auth_routes_router should be importable."""
        from framework_m.adapters.web.auth_routes import auth_routes_router

        assert auth_routes_router is not None

    def test_import_create_auth_router(self) -> None:
        """create_auth_router should be importable."""
        from framework_m.adapters.web.auth_routes import create_auth_router

        assert create_auth_router is not None


# =============================================================================
# Test: GET /api/v1/auth/me
# =============================================================================


class TestGetCurrentUser:
    """Tests for GET /api/v1/auth/me endpoint."""

    def test_import_get_current_user(self) -> None:
        """get_current_user handler should be importable."""
        from framework_m.adapters.web.auth_routes import get_current_user

        assert get_current_user is not None

    @pytest.mark.asyncio
    async def test_get_current_user_returns_user_context(self) -> None:
        """get_current_user should return user context dict."""
        from unittest.mock import MagicMock

        from framework_m.adapters.web.auth_routes import get_current_user
        from framework_m.core.interfaces.auth_context import UserContext

        user = UserContext(
            id="user-123",
            email="test@example.com",
            name="Test User",
            roles=["Employee"],
            tenants=["tenant-001"],
        )

        # Create mock request with user in state
        mock_request = MagicMock()
        mock_request.state.user = user

        # Access underlying function via .fn for Litestar route handlers
        result = await get_current_user.fn(request=mock_request)

        assert result["id"] == "user-123"
        assert result["email"] == "test@example.com"
        assert result["name"] == "Test User"
        assert result["roles"] == ["Employee"]
        assert result["tenants"] == ["tenant-001"]


# =============================================================================
# Test: POST /api/v1/auth/login
# =============================================================================


class TestLogin:
    """Tests for POST /api/v1/auth/login endpoint."""

    def test_import_login(self) -> None:
        """login handler should be importable."""
        from framework_m.adapters.web.auth_routes import login

        assert login is not None

    def test_import_login_request_dto(self) -> None:
        """LoginRequest DTO should be importable."""
        from framework_m.adapters.web.auth_routes import LoginRequest

        assert LoginRequest is not None

    def test_login_request_validation(self) -> None:
        """LoginRequest should validate username and password."""
        from framework_m.adapters.web.auth_routes import LoginRequest

        request = LoginRequest(username="user@example.com", password="secret123")
        assert request.username == "user@example.com"
        assert request.password == "secret123"

    @pytest.mark.asyncio
    async def test_login_returns_token(self) -> None:
        """login should return token on success in dev mode."""
        from framework_m.adapters.web.auth_routes import LoginRequest, login

        request = LoginRequest(username="user@example.com", password="secret")

        # Dev mode returns token without UserManager
        result = await login.fn(data=request)

        # Dev mode token format: dev-token-{login_id with @ replaced}
        assert result["access_token"] == "dev-token-user-at-example.com"
        assert result["token_type"] == "bearer"
        assert result["expires_in"] == 86400

    @pytest.mark.asyncio
    async def test_login_with_mocked_user_manager_raises_for_invalid_credentials(
        self,
    ) -> None:
        """login should raise 401 when UserManager returns AuthenticationError."""
        from litestar.exceptions import NotAuthorizedException

        import framework_m.adapters.web.auth_routes as auth_module
        from framework_m.adapters.web.auth_routes import LoginRequest, login
        from framework_m.core.exceptions import AuthenticationError

        # Temporarily set a mock UserManager
        mock_user_manager = AsyncMock()
        mock_user_manager.authenticate.side_effect = AuthenticationError("Invalid")

        original_user_manager = auth_module._user_manager
        auth_module._user_manager = mock_user_manager

        try:
            request = LoginRequest(username="user@example.com", password="wrong")
            with pytest.raises(NotAuthorizedException):
                await login.fn(data=request)
        finally:
            auth_module._user_manager = original_user_manager


# =============================================================================
# Test: POST /api/v1/auth/logout
# =============================================================================


class TestLogout:
    """Tests for POST /api/v1/auth/logout endpoint."""

    def test_import_logout(self) -> None:
        """logout handler should be importable."""
        from framework_m.adapters.web.auth_routes import logout

        assert logout is not None

    @pytest.mark.asyncio
    async def test_logout_returns_success(self) -> None:
        """logout should return success message."""
        from framework_m.adapters.web.auth_routes import logout

        # Access underlying function via .fn
        result = await logout.fn()

        assert result["message"] == "Logged out successfully"


# =============================================================================
# Test: Router Configuration
# =============================================================================


class TestAuthRouterConfig:
    """Tests for auth router configuration."""

    def test_router_has_correct_path(self) -> None:
        """Auth router should be mounted at /api/v1/auth."""
        from framework_m.adapters.web.auth_routes import auth_routes_router

        assert auth_routes_router.path == "/api/v1/auth"

    def test_router_has_auth_tag(self) -> None:
        """Auth router should have 'auth' tag."""
        from framework_m.adapters.web.auth_routes import auth_routes_router

        assert "auth" in auth_routes_router.tags
