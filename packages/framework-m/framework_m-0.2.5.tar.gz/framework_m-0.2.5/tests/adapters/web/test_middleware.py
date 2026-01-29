"""Tests for Authentication Middleware.

TDD tests for the AuthMiddleware that extracts user context from headers.
Tests written FIRST per CONTRIBUTING.md guidelines.
"""

from litestar import Litestar, Request, get
from litestar.testing import TestClient

from framework_m.adapters.web.middleware import create_auth_middleware
from framework_m.core.interfaces.auth_context import UserContext

# =============================================================================
# Test Route Handler (for testing middleware)
# =============================================================================


@get("/test-user")
async def get_test_user(request: Request) -> dict:
    """Test endpoint that returns user context from request state."""
    user: UserContext | None = getattr(request.state, "user", None)
    if user is None:
        return {"user": None}
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "roles": user.roles,
            "tenants": user.tenants,
        }
    }


class TestAuthMiddlewareExtraction:
    """Test that AuthMiddleware correctly extracts user context from headers."""

    def test_extracts_user_id_from_header(self) -> None:
        """Middleware should extract x-user-id header."""
        middleware = create_auth_middleware(require_auth=False)
        app = Litestar(
            route_handlers=[get_test_user],
            middleware=[middleware],
        )
        with TestClient(app) as client:
            response = client.get(
                "/test-user",
                headers={
                    "x-user-id": "user-123",
                    "x-user-email": "test@example.com",
                    "x-roles": "Employee",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["user"]["id"] == "user-123"

    def test_extracts_email_from_header(self) -> None:
        """Middleware should extract x-user-email header."""
        middleware = create_auth_middleware(require_auth=False)
        app = Litestar(
            route_handlers=[get_test_user],
            middleware=[middleware],
        )
        with TestClient(app) as client:
            response = client.get(
                "/test-user",
                headers={
                    "x-user-id": "user-123",
                    "x-user-email": "test@example.com",
                    "x-roles": "Employee",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["user"]["email"] == "test@example.com"

    def test_extracts_roles_from_comma_separated_header(self) -> None:
        """Middleware should parse x-roles as comma-separated list."""
        middleware = create_auth_middleware(require_auth=False)
        app = Litestar(
            route_handlers=[get_test_user],
            middleware=[middleware],
        )
        with TestClient(app) as client:
            response = client.get(
                "/test-user",
                headers={
                    "x-user-id": "user-123",
                    "x-user-email": "test@example.com",
                    "x-roles": "Employee,Manager,Admin",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["user"]["roles"] == ["Employee", "Manager", "Admin"]

    def test_extracts_tenants_from_comma_separated_header(self) -> None:
        """Middleware should parse x-tenants as comma-separated list."""
        middleware = create_auth_middleware(require_auth=False)
        app = Litestar(
            route_handlers=[get_test_user],
            middleware=[middleware],
        )
        with TestClient(app) as client:
            response = client.get(
                "/test-user",
                headers={
                    "x-user-id": "user-123",
                    "x-user-email": "test@example.com",
                    "x-roles": "Employee",
                    "x-tenants": "tenant-1,tenant-2",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["user"]["tenants"] == ["tenant-1", "tenant-2"]

    def test_tenants_optional_defaults_to_empty(self) -> None:
        """x-tenants header is optional and defaults to empty list."""
        middleware = create_auth_middleware(require_auth=False)
        app = Litestar(
            route_handlers=[get_test_user],
            middleware=[middleware],
        )
        with TestClient(app) as client:
            response = client.get(
                "/test-user",
                headers={
                    "x-user-id": "user-123",
                    "x-user-email": "test@example.com",
                    "x-roles": "Employee",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["user"]["tenants"] == []


class TestAuthMiddlewareRequireAuth:
    """Test AuthMiddleware authentication requirement behavior."""

    def test_returns_401_when_headers_missing_and_required(self) -> None:
        """When require_auth=True, missing headers should return 401."""
        middleware = create_auth_middleware(require_auth=True)
        app = Litestar(
            route_handlers=[get_test_user],
            middleware=[middleware],
        )
        with TestClient(app) as client:
            response = client.get("/test-user")
            assert response.status_code == 401
            data = response.json()
            assert "error" in data

    def test_returns_401_when_user_id_missing(self) -> None:
        """When require_auth=True, missing x-user-id should return 401."""
        middleware = create_auth_middleware(require_auth=True)
        app = Litestar(
            route_handlers=[get_test_user],
            middleware=[middleware],
        )
        with TestClient(app) as client:
            response = client.get(
                "/test-user",
                headers={
                    "x-user-email": "test@example.com",
                    "x-roles": "Employee",
                },
            )
            assert response.status_code == 401

    def test_allows_request_when_require_auth_false(self) -> None:
        """When require_auth=False, missing headers should still allow request."""
        middleware = create_auth_middleware(require_auth=False)
        app = Litestar(
            route_handlers=[get_test_user],
            middleware=[middleware],
        )
        with TestClient(app) as client:
            response = client.get("/test-user")
            assert response.status_code == 200
            data = response.json()
            assert data["user"] is None


class TestAuthMiddlewareUserContext:
    """Test that AuthMiddleware creates proper UserContext object."""

    def test_stores_user_context_in_request_state(self) -> None:
        """Middleware should store UserContext in request.state.user."""
        middleware = create_auth_middleware(require_auth=False)
        app = Litestar(
            route_handlers=[get_test_user],
            middleware=[middleware],
        )
        with TestClient(app) as client:
            response = client.get(
                "/test-user",
                headers={
                    "x-user-id": "user-123",
                    "x-user-email": "test@example.com",
                    "x-roles": "Employee",
                },
            )
            assert response.status_code == 200
            data = response.json()
            # User should be a proper UserContext representation
            assert data["user"] is not None
            assert "id" in data["user"]
            assert "email" in data["user"]
            assert "roles" in data["user"]

    def test_trims_whitespace_from_roles(self) -> None:
        """Middleware should trim whitespace from role names."""
        middleware = create_auth_middleware(require_auth=False)
        app = Litestar(
            route_handlers=[get_test_user],
            middleware=[middleware],
        )
        with TestClient(app) as client:
            response = client.get(
                "/test-user",
                headers={
                    "x-user-id": "user-123",
                    "x-user-email": "test@example.com",
                    "x-roles": " Employee , Manager , Admin ",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["user"]["roles"] == ["Employee", "Manager", "Admin"]


class TestAuthMiddlewareExcludedPaths:
    """Test path exclusion configuration for middleware."""

    def test_health_endpoint_excluded_by_default(self) -> None:
        """Health check endpoint should bypass auth check by default."""
        middleware = create_auth_middleware(require_auth=True)

        @get("/health")
        async def health() -> dict:
            return {"status": "healthy"}

        app = Litestar(
            route_handlers=[health, get_test_user],
            middleware=[middleware],
        )
        with TestClient(app) as client:
            # Health should work without auth
            response = client.get("/health")
            assert response.status_code == 200
            # Other endpoints should still require auth
            response = client.get("/test-user")
            assert response.status_code == 401

    def test_custom_excluded_paths(self) -> None:
        """Should support custom excluded paths."""
        middleware = create_auth_middleware(
            require_auth=True,
            excluded_paths=["/health", "/public"],
        )

        @get("/public")
        async def public_endpoint() -> dict:
            return {"public": True}

        app = Litestar(
            route_handlers=[public_endpoint, get_test_user],
            middleware=[middleware],
        )
        with TestClient(app) as client:
            response = client.get("/public")
            assert response.status_code == 200
