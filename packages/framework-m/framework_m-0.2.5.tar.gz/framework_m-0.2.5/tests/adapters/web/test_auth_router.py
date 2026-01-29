"""Tests for Auth Router.

TDD tests for the authentication API routes.
Tests written FIRST per CONTRIBUTING.md guidelines.
"""

from litestar import Litestar
from litestar.testing import TestClient

from framework_m.adapters.web.auth_router import auth_router, get_current_user
from framework_m.adapters.web.middleware import create_auth_middleware

# =============================================================================
# Test Auth Router Registration
# =============================================================================


class TestAuthRouterRegistration:
    """Test that auth router is properly configured."""

    def test_auth_router_has_correct_path(self) -> None:
        """Auth router should have /api/v1 prefix."""
        assert auth_router.path == "/api/v1"

    def test_auth_router_includes_me_endpoint(self) -> None:
        """Auth router should include the /auth/me endpoint."""
        app = Litestar(route_handlers=[auth_router])
        with TestClient(app) as client:
            response = client.get("/api/v1/auth/me")
            # Should not return 404
            assert response.status_code != 404


# =============================================================================
# Test GET /api/v1/auth/me Endpoint
# =============================================================================


class TestGetCurrentUserEndpoint:
    """Test the /api/v1/auth/me endpoint."""

    def test_returns_guest_when_no_user(self) -> None:
        """Should return unauthenticated user when no headers provided."""
        app = Litestar(route_handlers=[auth_router])
        with TestClient(app) as client:
            response = client.get("/api/v1/auth/me")
            assert response.status_code == 200
            data = response.json()
            assert data["authenticated"] is False
            assert data["id"] is None

    def test_returns_authenticated_user_with_middleware(self) -> None:
        """Should return authenticated user when headers provided via middleware."""
        middleware = create_auth_middleware(require_auth=False)
        app = Litestar(
            route_handlers=[auth_router],
            middleware=[middleware],
        )
        with TestClient(app) as client:
            response = client.get(
                "/api/v1/auth/me",
                headers={
                    "x-user-id": "user-123",
                    "x-user-email": "test@example.com",
                    "x-roles": "Employee,Manager",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["authenticated"] is True
            assert data["id"] == "user-123"
            assert data["email"] == "test@example.com"
            assert data["roles"] == ["Employee", "Manager"]

    def test_returns_empty_roles_when_not_provided(self) -> None:
        """Should return empty roles list when x-roles header not provided."""
        middleware = create_auth_middleware(require_auth=False)
        app = Litestar(
            route_handlers=[auth_router],
            middleware=[middleware],
        )
        with TestClient(app) as client:
            response = client.get(
                "/api/v1/auth/me",
                headers={
                    "x-user-id": "user-123",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["authenticated"] is True
            assert data["roles"] == []

    def test_returns_empty_tenants_by_default(self) -> None:
        """Should return empty tenants list when x-tenants header not provided."""
        middleware = create_auth_middleware(require_auth=False)
        app = Litestar(
            route_handlers=[auth_router],
            middleware=[middleware],
        )
        with TestClient(app) as client:
            response = client.get(
                "/api/v1/auth/me",
                headers={
                    "x-user-id": "user-123",
                    "x-roles": "Employee",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["tenants"] == []

    def test_returns_tenants_when_provided(self) -> None:
        """Should return tenants list from x-tenants header."""
        middleware = create_auth_middleware(require_auth=False)
        app = Litestar(
            route_handlers=[auth_router],
            middleware=[middleware],
        )
        with TestClient(app) as client:
            response = client.get(
                "/api/v1/auth/me",
                headers={
                    "x-user-id": "user-123",
                    "x-roles": "Employee",
                    "x-tenants": "tenant-1,tenant-2",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["tenants"] == ["tenant-1", "tenant-2"]


# =============================================================================
# Test get_current_user Function Directly
# =============================================================================


class TestGetCurrentUserFunction:
    """Test the get_current_user function directly."""

    def test_function_is_async(self) -> None:
        """get_current_user should be an async function."""
        import inspect

        # Litestar decorates handlers, so check the underlying function
        fn = getattr(get_current_user, "fn", get_current_user)
        assert inspect.iscoroutinefunction(fn)
