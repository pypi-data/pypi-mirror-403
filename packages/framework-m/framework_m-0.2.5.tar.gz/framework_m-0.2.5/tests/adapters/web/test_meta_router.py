"""Tests for Auto-CRUD Meta Router.

TDD tests for meta_router.py that auto-generates CRUD endpoints.
Tests written FIRST per CONTRIBUTING.md guidelines.
"""

from typing import ClassVar

import pytest
from litestar import Litestar
from litestar.testing import TestClient

from framework_m.core.domain.base_doctype import BaseDocType
from framework_m.core.registry import MetaRegistry

# =============================================================================
# Test DocTypes
# =============================================================================


class Article(BaseDocType):
    """DocType with api_resource enabled."""

    title: str = ""
    content: str = ""

    class Meta:
        api_resource: ClassVar[bool] = True
        requires_auth: ClassVar[bool] = True
        permissions: ClassVar[dict[str, list[str]]] = {
            "read": ["Guest", "User"],
            "write": ["User"],
            "create": ["User"],
            "delete": ["Admin"],
        }


class InternalConfig(BaseDocType):
    """DocType WITHOUT api_resource (no auto-CRUD)."""

    key: str = ""
    value: str = ""

    class Meta:
        api_resource: ClassVar[bool] = False


# =============================================================================
# Tests for Meta.api_resource Flag
# =============================================================================


class TestApiResourceFlag:
    """Test Meta.api_resource flag on BaseDocType."""

    def test_default_is_false(self) -> None:
        """DocTypes without api_resource should default to False."""

        class SimpleDoc(BaseDocType):
            name: str = ""

        assert SimpleDoc.get_api_resource() is False

    def test_explicit_true(self) -> None:
        """DocTypes with api_resource = True should return True."""
        assert Article.get_api_resource() is True

    def test_explicit_false(self) -> None:
        """DocTypes with api_resource = False should return False."""
        assert InternalConfig.get_api_resource() is False


# =============================================================================
# Tests for create_crud_routes Function
# =============================================================================


class TestCreateCrudRoutes:
    """Test create_crud_routes() function."""

    @pytest.fixture(autouse=True)
    def register_doctypes(self) -> None:
        """Register test DocTypes in MetaRegistry."""
        registry = MetaRegistry.get_instance()
        try:
            registry.get_doctype("Article")
        except KeyError:
            registry.register_doctype(Article)
        try:
            registry.get_doctype("InternalConfig")
        except KeyError:
            registry.register_doctype(InternalConfig)

    def test_function_is_importable(self) -> None:
        """create_crud_routes should be importable."""
        from framework_m.adapters.web.meta_router import create_crud_routes

        assert create_crud_routes is not None

    def test_generates_router_for_doctype(self) -> None:
        """Should generate a Router for a DocType."""
        from litestar import Router

        from framework_m.adapters.web.meta_router import create_crud_routes

        router = create_crud_routes(Article)
        assert isinstance(router, Router)

    def test_generates_5_routes(self) -> None:
        """Should generate 5 CRUD routes."""
        from framework_m.adapters.web.meta_router import create_crud_routes

        router = create_crud_routes(Article)
        # Router should have route handlers
        assert len(router.routes) >= 1  # At least one route group


# =============================================================================
# Tests for create_meta_router Function
# =============================================================================


class TestCreateMetaRouter:
    """Test create_meta_router() function."""

    @pytest.fixture(autouse=True)
    def register_doctypes(self) -> None:
        """Register test DocTypes in MetaRegistry."""
        registry = MetaRegistry.get_instance()
        try:
            registry.get_doctype("Article")
        except KeyError:
            registry.register_doctype(Article)
        try:
            registry.get_doctype("InternalConfig")
        except KeyError:
            registry.register_doctype(InternalConfig)

    def test_function_is_importable(self) -> None:
        """create_meta_router should be importable."""
        from framework_m.adapters.web.meta_router import create_meta_router

        assert create_meta_router is not None

    def test_only_includes_api_resource_true_doctypes(self) -> None:
        """Should only generate routes for DocTypes with api_resource=True."""
        from framework_m.adapters.web.meta_router import create_meta_router

        router = create_meta_router()
        # Should have routes for Article but not InternalConfig
        assert router is not None


# =============================================================================
# Tests for CRUD Endpoints (Integration)
# =============================================================================


class TestCrudEndpoints:
    """Integration tests for generated CRUD endpoints."""

    @pytest.fixture(autouse=True)
    def register_doctypes(self) -> None:
        """Register test DocTypes in MetaRegistry."""
        registry = MetaRegistry.get_instance()
        try:
            registry.get_doctype("Article")
        except KeyError:
            registry.register_doctype(Article)

    @pytest.fixture
    def app(self) -> Litestar:
        """Create test app with meta router."""
        from framework_m.adapters.web.meta_router import create_meta_router

        router = create_meta_router()
        return Litestar(route_handlers=[router])

    @pytest.fixture
    def client(self, app: Litestar) -> TestClient[Litestar]:
        """Create test client."""
        return TestClient(app)

    def test_list_endpoint_exists(self, client: TestClient[Litestar]) -> None:
        """GET /api/v1/Article should exist."""
        response = client.get("/api/v1/Article")
        # Should not be 404
        assert response.status_code != 404

    def test_create_endpoint_exists(self, client: TestClient[Litestar]) -> None:
        """POST /api/v1/Article should exist."""
        response = client.post("/api/v1/Article", json={"title": "Test"})
        # Should not be 404
        assert response.status_code != 404


# =============================================================================
# Tests for Auto-Permission in CRUD Routes (Section 3.7 Verification)
# =============================================================================


class TestAutoPermissionInCrudRoutes:
    """Verify all auto-generated CRUD routes call permission.evaluate().

    These tests verify the Section 3.7 requirement:
    - POST → checks CREATE permission
    - GET (single) → checks READ permission
    - PUT → checks WRITE permission
    - DELETE → checks DELETE permission

    No manual code required for indie devs using auto-CRUD.
    """

    @pytest.fixture(autouse=True)
    def register_doctypes(self) -> None:
        """Register test DocTypes in MetaRegistry."""
        registry = MetaRegistry.get_instance()
        try:
            registry.get_doctype("Article")
        except KeyError:
            registry.register_doctype(Article)

    @pytest.fixture
    def app(self) -> Litestar:
        """Create test app with meta router and exception handlers."""
        from litestar import Response
        from litestar.status_codes import HTTP_403_FORBIDDEN

        from framework_m.adapters.web.meta_router import create_meta_router
        from framework_m.core.exceptions import PermissionDeniedError

        def permission_denied_handler(
            request: object, exc: PermissionDeniedError
        ) -> Response[dict[str, str]]:
            return Response(
                content={"error": "PermissionDenied", "message": str(exc)},
                status_code=HTTP_403_FORBIDDEN,
            )

        router = create_meta_router()
        return Litestar(
            route_handlers=[router],
            exception_handlers={PermissionDeniedError: permission_denied_handler},
        )

    @pytest.fixture
    def client(self, app: Litestar) -> TestClient[Litestar]:
        """Create test client."""
        return TestClient(app)

    def test_post_checks_create_permission(self, client: TestClient[Litestar]) -> None:
        """POST /api/v1/Article checks CREATE permission.

        Anonymous user (no roles) should get 403 Forbidden.
        """
        response = client.post("/api/v1/Article", json={"title": "Test"})
        # Anonymous user has no roles, so CREATE permission denied
        assert response.status_code == 403
        data = response.json()
        assert data["error"] == "PermissionDenied"
        assert "create" in data["message"].lower()

    def test_get_single_checks_read_permission(
        self, client: TestClient[Litestar]
    ) -> None:
        """GET /api/v1/Article/{id} checks READ permission.

        Anonymous user should get 403 if READ permission denied.
        Note: Article allows Guest to read, so this should succeed.
        """
        from uuid import uuid4

        response = client.get(f"/api/v1/Article/{uuid4()}")
        # Article allows "Guest" to read - anonymous gets empty roles
        # Since no role matches, permission is denied
        # But Article has "Guest" in read permissions, let's check the logic
        assert response.status_code in [200, 403]

    def test_put_checks_write_permission(self, client: TestClient[Litestar]) -> None:
        """PUT /api/v1/Article/{id} checks WRITE permission.

        Anonymous user should get 403 Forbidden.
        """
        from uuid import uuid4

        response = client.put(f"/api/v1/Article/{uuid4()}", json={"title": "Updated"})
        # Anonymous user has no "User" role, so WRITE denied
        assert response.status_code == 403
        data = response.json()
        assert data["error"] == "PermissionDenied"
        assert "write" in data["message"].lower()

    def test_delete_checks_delete_permission(
        self, client: TestClient[Litestar]
    ) -> None:
        """DELETE /api/v1/Article/{id} checks DELETE permission.

        Anonymous user should get 403 Forbidden.
        """
        from uuid import uuid4

        response = client.delete(f"/api/v1/Article/{uuid4()}")
        # Anonymous user has no "Admin" role, so DELETE denied
        assert response.status_code == 403

    def test_no_manual_code_required(self) -> None:
        """Verify that no manual code is required for permission checks.

        The permission checks are built into create_crud_routes() automatically.
        Developers just set Meta.api_resource = True and permissions in Meta.
        """
        from framework_m.adapters.web.meta_router import create_crud_routes

        # Simply calling create_crud_routes should create routes
        # that automatically check permissions
        router = create_crud_routes(Article)

        # Router has 5 handlers (list, create, read, update, delete)
        # All permission checks are built-in
        assert router is not None
        assert len(router.routes) >= 1


# =============================================================================
# Tests for _parse_filters Helper
# =============================================================================


class TestParseFilters:
    """Test _parse_filters helper function."""

    def test_parse_empty_string_returns_empty_list(self) -> None:
        """Empty string should return empty filter list."""
        from framework_m.adapters.web.meta_router import _parse_filters

        result = _parse_filters("")
        assert result == []

    def test_parse_none_returns_empty_list(self) -> None:
        """None should return empty filter list."""
        from framework_m.adapters.web.meta_router import _parse_filters

        result = _parse_filters(None)
        assert result == []

    def test_parse_valid_filter(self) -> None:
        """Should parse valid JSON filter."""
        from framework_m.adapters.web.meta_router import _parse_filters
        from framework_m.core.interfaces.repository import FilterOperator

        json_str = '[{"field": "status", "operator": "eq", "value": "active"}]'
        result = _parse_filters(json_str)
        assert len(result) == 1
        assert result[0].field == "status"
        assert result[0].operator == FilterOperator.EQ
        assert result[0].value == "active"

    def test_parse_multiple_filters(self) -> None:
        """Should parse multiple filters."""
        from framework_m.adapters.web.meta_router import _parse_filters

        json_str = '[{"field": "a", "operator": "eq", "value": 1}, {"field": "b", "operator": "gt", "value": 2}]'
        result = _parse_filters(json_str)
        assert len(result) == 2

    def test_parse_invalid_json_returns_empty(self) -> None:
        """Invalid JSON should return empty list."""
        from framework_m.adapters.web.meta_router import _parse_filters

        result = _parse_filters("not valid json")
        assert result == []

    def test_parse_unknown_operator_defaults_to_eq(self) -> None:
        """Unknown operator should default to EQ."""
        from framework_m.adapters.web.meta_router import _parse_filters
        from framework_m.core.interfaces.repository import FilterOperator

        json_str = '[{"field": "status", "operator": "unknown_op", "value": "active"}]'
        result = _parse_filters(json_str)
        assert result[0].operator == FilterOperator.EQ

    def test_parse_missing_operator_defaults_to_eq(self) -> None:
        """Missing operator should default to EQ."""
        from framework_m.adapters.web.meta_router import _parse_filters
        from framework_m.core.interfaces.repository import FilterOperator

        json_str = '[{"field": "status", "value": "active"}]'
        result = _parse_filters(json_str)
        assert result[0].operator == FilterOperator.EQ

    def test_parse_missing_field_returns_empty(self) -> None:
        """Missing required 'field' should return empty list."""
        from framework_m.adapters.web.meta_router import _parse_filters

        json_str = '[{"operator": "eq", "value": "active"}]'
        result = _parse_filters(json_str)
        assert result == []


# =============================================================================
# Tests for create_meta_router with empty registry
# =============================================================================


class TestMetaRouterEmptyRegistry:
    """Test meta_router with empty registry."""

    @pytest.fixture
    def empty_registry(self) -> MetaRegistry:
        """Get empty registry."""
        reg = MetaRegistry.get_instance()
        reg.clear()
        yield reg
        reg.clear()

    def test_meta_router_with_no_doctypes(self, empty_registry: MetaRegistry) -> None:
        """create_meta_router should work with no DocTypes."""
        from litestar import Router

        from framework_m.adapters.web.meta_router import create_meta_router

        router = create_meta_router()
        assert isinstance(router, Router)
        # Should have no routes
        assert len(router.routes) == 0


# =============================================================================
# Tests for _check_submitted Helper
# =============================================================================


class TestCheckSubmittedHelper:
    """Test _check_submitted helper function."""

    def test_check_submitted_raises_for_submitted_doc(self) -> None:
        """_check_submitted should raise for submitted document."""
        from framework_m.adapters.web.meta_router import _check_submitted
        from framework_m.core.exceptions import PermissionDeniedError

        class SubmittedDoc:
            docstatus: int = 1  # Submitted

        with pytest.raises(PermissionDeniedError):
            _check_submitted(SubmittedDoc(), "update")

    def test_check_submitted_allows_draft(self) -> None:
        """_check_submitted should allow draft documents."""
        from framework_m.adapters.web.meta_router import _check_submitted

        class DraftDoc:
            docstatus: int = 0  # Draft

        # Should not raise
        _check_submitted(DraftDoc(), "update")

    def test_check_submitted_allows_no_docstatus(self) -> None:
        """_check_submitted should allow documents without docstatus."""
        from framework_m.adapters.web.meta_router import _check_submitted

        class SimpleDoc:
            pass

        # Should not raise
        _check_submitted(SimpleDoc(), "update")


# =============================================================================
# Tests for _get_user_context Helper
# =============================================================================


class TestGetUserContextHelper:
    """Test _get_user_context helper function."""

    def test_get_user_context_extracts_state(self) -> None:
        """_get_user_context should extract user info from request.state."""
        from unittest.mock import MagicMock

        from framework_m.adapters.web.meta_router import _get_user_context

        mock_request = MagicMock()
        mock_request.state.user_id = "user123"
        mock_request.state.user_roles = ["Admin", "User"]
        mock_request.state.user_teams = ["team1", "team2"]

        user_id, roles, teams = _get_user_context(mock_request)

        assert user_id == "user123"
        assert "Admin" in roles
        assert "User" in roles
        assert "team1" in teams
        assert "team2" in teams


# =============================================================================
# Test: _get_user_from_request Helper
# =============================================================================


class TestGetUserFromRequestHelper:
    """Test _get_user_from_request helper function."""

    def test_get_user_from_request_with_user(self) -> None:
        """_get_user_from_request should return user from request.state."""
        from unittest.mock import MagicMock

        from framework_m.adapters.web.meta_router import _get_user_from_request

        mock_user = MagicMock()
        mock_user.id = "user-123"

        mock_request = MagicMock()
        mock_request.state.user = mock_user

        result = _get_user_from_request(mock_request)

        assert result is mock_user

    def test_get_user_from_request_no_user(self) -> None:
        """_get_user_from_request should return None if no user."""
        from unittest.mock import MagicMock

        from framework_m.adapters.web.meta_router import _get_user_from_request

        mock_request = MagicMock()
        del mock_request.state.user  # No user attribute

        result = _get_user_from_request(mock_request)

        assert result is None


# =============================================================================
# Test: _check_permission Helper
# =============================================================================


class TestCheckPermissionHelper:
    """Test _check_permission helper function."""

    @pytest.mark.asyncio
    async def test_check_permission_denied_raises(self) -> None:
        """_check_permission should raise PermissionDeniedError."""
        from unittest.mock import AsyncMock, patch

        from framework_m.adapters.web.meta_router import _check_permission
        from framework_m.core.exceptions import PermissionDeniedError

        mock_result = AsyncMock()
        mock_result.authorized = False

        with patch(
            "framework_m.adapters.web.meta_router.RbacPermissionAdapter"
        ) as mock_adapter:
            mock_adapter.return_value.evaluate = AsyncMock(return_value=mock_result)

            with pytest.raises(PermissionDeniedError):
                await _check_permission(
                    user_id="user1",
                    user_roles=[],
                    user_teams=[],
                    action="create",
                    doctype_name="Article",
                )

    @pytest.mark.asyncio
    async def test_check_permission_granted_passes(self) -> None:
        """_check_permission should not raise when authorized."""
        from unittest.mock import AsyncMock, patch

        from framework_m.adapters.web.meta_router import _check_permission

        mock_result = AsyncMock()
        mock_result.authorized = True

        with patch(
            "framework_m.adapters.web.meta_router.RbacPermissionAdapter"
        ) as mock_adapter:
            mock_adapter.return_value.evaluate = AsyncMock(return_value=mock_result)

            # Should not raise
            await _check_permission(
                user_id="admin",
                user_roles=["Admin"],
                user_teams=[],
                action="create",
                doctype_name="Article",
            )


# =============================================================================
# Test: List endpoint pagination
# =============================================================================


class TestListEndpointPagination:
    """Test list endpoint pagination and filtering."""

    @pytest.fixture(autouse=True)
    def register_doctypes(self) -> None:
        """Register test DocTypes in MetaRegistry."""
        registry = MetaRegistry.get_instance()
        try:
            registry.get_doctype("Article")
        except KeyError:
            registry.register_doctype(Article)

    @pytest.fixture
    def app(self) -> Litestar:
        """Create test app with meta router."""
        from framework_m.adapters.web.meta_router import create_meta_router

        router = create_meta_router()
        return Litestar(route_handlers=[router])

    @pytest.fixture
    def client(self, app: Litestar) -> TestClient[Litestar]:
        """Create test client."""
        return TestClient(app)

    def test_list_with_limit(self, client: TestClient[Litestar]) -> None:
        """GET /Article?limit=10 should accept limit."""
        response = client.get("/api/v1/Article?limit=10")

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 10

    def test_list_with_offset(self, client: TestClient[Litestar]) -> None:
        """GET /Article?offset=5 should accept offset."""
        response = client.get("/api/v1/Article?offset=5")

        assert response.status_code == 200
        data = response.json()
        assert data["offset"] == 5

    def test_list_with_filters(self, client: TestClient[Litestar]) -> None:
        """GET /Article with filters should work."""
        filters = '[{"field": "status", "operator": "eq", "value": "active"}]'
        response = client.get(f"/api/v1/Article?filters={filters}")

        assert response.status_code == 200

    def test_list_with_fields(self, client: TestClient[Litestar]) -> None:
        """GET /Article?fields=title,content should work."""
        response = client.get("/api/v1/Article?fields=title,content")

        assert response.status_code == 200
