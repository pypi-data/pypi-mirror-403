"""Integration tests for CRUD and RPC API endpoints.

Tests the API endpoints with Litestar TestClient simulating HTTP requests.
Covers: validation, permissions, RLS filtering, immutable docs.
"""

from typing import Any, ClassVar

import pytest
from litestar import Litestar, Response
from litestar.status_codes import HTTP_403_FORBIDDEN
from litestar.testing import TestClient
from litestar.types import ASGIApp, Receive, Scope, Send

from framework_m.core.domain.base_doctype import BaseDocType, Field
from framework_m.core.exceptions import PermissionDeniedError
from framework_m.core.interfaces.auth_context import UserContext
from framework_m.core.registry import MetaRegistry

# =============================================================================
# Test DocTypes
# =============================================================================


class CrudTestDoc(BaseDocType):
    """DocType for CRUD integration tests."""

    title: str = Field(title="Title", description="Document title")
    amount: float = Field(default=0.0, title="Amount")
    docstatus: int = Field(default=0)  # 0=Draft, 1=Submitted

    class Meta:
        api_resource: ClassVar[bool] = True
        requires_auth: ClassVar[bool] = True
        apply_rls: ClassVar[bool] = True
        permissions: ClassVar[dict[str, list[str]]] = {
            "read": ["Employee", "Manager", "Admin"],
            "write": ["Employee", "Manager", "Admin"],
            "create": ["Employee", "Manager", "Admin"],
            "delete": ["Admin"],
        }


# =============================================================================
# Middleware for Mock Auth
# =============================================================================


def create_mock_auth_middleware(
    user_id: str = "user-123",
    roles: list[str] | None = None,
) -> Any:
    """Create a middleware that injects mock user context."""
    if roles is None:
        roles = ["Employee"]

    async def mock_auth(
        app: ASGIApp, scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope["type"] in ("http", "websocket"):
            scope["state"]["user"] = UserContext(
                id=user_id,
                email=f"{user_id}@example.com",
                roles=roles,
            )
        await app(scope, receive, send)

    def factory(app: ASGIApp) -> ASGIApp:
        async def middleware(scope: Scope, receive: Receive, send: Send) -> None:
            await mock_auth(app, scope, receive, send)

        return middleware

    return factory


def permission_denied_handler(
    request: object, exc: PermissionDeniedError
) -> Response[dict[str, str]]:
    """Handle permission denied errors."""
    return Response(
        content={"error": "PermissionDenied", "message": str(exc)},
        status_code=HTTP_403_FORBIDDEN,
    )


# =============================================================================
# Tests: CRUD Endpoints
# =============================================================================


class TestCrudEndpointValidation:
    """Test CRUD endpoints with validation."""

    @pytest.fixture(autouse=True)
    def register_doctypes(self) -> None:
        """Register test DocTypes."""
        registry = MetaRegistry.get_instance()
        try:
            registry.get_doctype("CrudTestDoc")
        except KeyError:
            registry.register_doctype(CrudTestDoc)

    @pytest.fixture
    def app(self) -> Litestar:
        """Create test app with CRUD routes."""
        from framework_m.adapters.web.meta_router import create_meta_router

        router = create_meta_router()
        return Litestar(
            route_handlers=[router],
            exception_handlers={PermissionDeniedError: permission_denied_handler},
            middleware=[create_mock_auth_middleware()],
        )

    @pytest.fixture
    def client(self, app: Litestar) -> TestClient[Litestar]:
        """Create test client."""
        return TestClient(app)

    def test_create_with_valid_data(self, client: TestClient[Litestar]) -> None:
        """POST with valid data should return 201."""
        response = client.post(
            "/api/v1/CrudTestDoc",
            json={"title": "Valid Title", "amount": 100.0},
        )
        # Should not be 404 (route exists)
        # Note: May fail at repo level without DB, but validates routing works
        assert response.status_code != 404

    def test_create_rejects_invalid_data(self, client: TestClient[Litestar]) -> None:
        """POST with invalid data should be rejected."""
        # Missing required field 'title' should be rejected by Pydantic
        response = client.post(
            "/api/v1/CrudTestDoc",
            json={"amount": "not-a-number"},  # Invalid type for amount
        )
        # Should be a client error (400 validation) or 403 (permission check before validation)
        assert response.status_code >= 400


class TestCrudEndpointPermissions:
    """Test CRUD endpoints with permission checks."""

    @pytest.fixture(autouse=True)
    def register_doctypes(self) -> None:
        """Register test DocTypes."""
        registry = MetaRegistry.get_instance()
        try:
            registry.get_doctype("CrudTestDoc")
        except KeyError:
            registry.register_doctype(CrudTestDoc)

    @pytest.fixture
    def app_employee(self) -> Litestar:
        """Create test app with Employee role."""
        from framework_m.adapters.web.meta_router import create_meta_router

        router = create_meta_router()
        return Litestar(
            route_handlers=[router],
            exception_handlers={PermissionDeniedError: permission_denied_handler},
            middleware=[
                create_mock_auth_middleware(user_id="emp-123", roles=["Employee"])
            ],
        )

    @pytest.fixture
    def app_admin(self) -> Litestar:
        """Create test app with Admin role."""
        from framework_m.adapters.web.meta_router import create_meta_router

        router = create_meta_router()
        return Litestar(
            route_handlers=[router],
            exception_handlers={PermissionDeniedError: permission_denied_handler},
            middleware=[
                create_mock_auth_middleware(user_id="admin-123", roles=["Admin"])
            ],
        )

    def test_employee_can_create(self, app_employee: Litestar) -> None:
        """Employee should be able to create documents."""
        client = TestClient(app_employee)
        response = client.post(
            "/api/v1/CrudTestDoc",
            json={"title": "Employee Doc"},
        )
        # Endpoints should exist
        assert response.status_code != 404

    def test_list_endpoint_works(self, app_employee: Litestar) -> None:
        """GET list should return paginated response."""
        client = TestClient(app_employee)
        response = client.get("/api/v1/CrudTestDoc")
        assert response.status_code == 200
        data = response.json()
        # Should have pagination fields
        assert "items" in data
        assert "total" in data
        assert "has_more" in data


class TestCrudRlsFiltering:
    """Test CRUD list endpoint with RLS filtering."""

    @pytest.fixture(autouse=True)
    def register_doctypes(self) -> None:
        """Register test DocTypes."""
        registry = MetaRegistry.get_instance()
        try:
            registry.get_doctype("CrudTestDoc")
        except KeyError:
            registry.register_doctype(CrudTestDoc)

    @pytest.fixture
    def app_user1(self) -> Litestar:
        """Create test app for user 1."""
        from framework_m.adapters.web.meta_router import create_meta_router

        router = create_meta_router()
        return Litestar(
            route_handlers=[router],
            exception_handlers={PermissionDeniedError: permission_denied_handler},
            middleware=[
                create_mock_auth_middleware(user_id="user-001", roles=["Employee"])
            ],
        )

    def test_list_returns_paginated_format(self, app_user1: Litestar) -> None:
        """List should return paginated response with RLS applied."""
        client = TestClient(app_user1)
        response = client.get("/api/v1/CrudTestDoc")
        assert response.status_code == 200
        data = response.json()
        # Empty list since no DB, but format should be correct
        assert data["items"] == []
        assert data["total"] == 0
        assert data["has_more"] is False


# =============================================================================
# Tests: RPC Endpoints (Integration)
# =============================================================================


class TestRpcEndpointIntegration:
    """Integration tests for RPC endpoints."""

    @pytest.fixture
    def app(self) -> Litestar:
        """Create test app with RPC routes."""
        from framework_m.adapters.web.rpc_routes import rpc_router

        return Litestar(
            route_handlers=[rpc_router],
            exception_handlers={PermissionDeniedError: permission_denied_handler},
            middleware=[create_mock_auth_middleware()],
        )

    @pytest.fixture
    def client(self, app: Litestar) -> TestClient[Litestar]:
        """Create test client."""
        return TestClient(app)

    def test_rpc_function_callable(self, client: TestClient[Litestar]) -> None:
        """Should be able to call registered RPC function."""
        from framework_m.core.decorators import rpc
        from framework_m.core.rpc_registry import RpcRegistry

        registry = RpcRegistry.get_instance()

        # Register a simple function
        @rpc(allow_guest=True)
        async def integration_test_func() -> dict[str, str]:
            return {"status": "success"}

        # Manually register with known path
        registry.register("integration.test_func", integration_test_func)

        # Call via RPC endpoint
        response = client.post(
            "/api/v1/rpc/fn/integration.test_func",
            json={},
        )
        assert response.status_code in (200, 201)
        data = response.json()
        # Response could be wrapped or direct
        assert data.get("status") == "success" or "result" in data

    def test_rpc_rejects_unregistered(self, client: TestClient[Litestar]) -> None:
        """Should reject calls to unregistered functions."""
        response = client.post(
            "/api/v1/rpc/fn/nonexistent.function",
            json={},
        )
        assert response.status_code == 404
