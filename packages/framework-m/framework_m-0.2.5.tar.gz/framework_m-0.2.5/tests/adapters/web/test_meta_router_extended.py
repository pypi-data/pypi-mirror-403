"""Extended tests for meta_router.py to increase coverage.

These tests cover previously untested code paths and edge cases.
"""

from typing import ClassVar
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from litestar import Litestar, Response
from litestar.exceptions import NotFoundException
from litestar.status_codes import HTTP_403_FORBIDDEN
from litestar.testing import TestClient

from framework_m.core.domain.base_doctype import BaseDocType
from framework_m.core.exceptions import PermissionDeniedError
from framework_m.core.registry import MetaRegistry

# =============================================================================
# Test DocType
# =============================================================================


class Product(BaseDocType):
    """Test DocType with api_resource enabled."""

    name: str = ""
    price: float = 0.0
    docstatus: int = 0  # Add docstatus field for testing

    class Meta:
        api_resource: ClassVar[bool] = True
        table_name: ClassVar[str] = "products"  # Test custom table name
        permissions: ClassVar[dict[str, list[str]]] = {
            "read": ["*"],
            "write": ["User"],
            "create": ["User"],
            "delete": ["Admin"],
        }


# =============================================================================
# Tests for _get_table_name Helper
# =============================================================================


class TestGetTableNameHelper:
    """Test _get_table_name helper function."""

    def test_get_table_name_with_custom_table_name(self) -> None:
        """_get_table_name should return custom table_name from Meta."""
        from framework_m.adapters.web.meta_router import _get_table_name

        table_name = _get_table_name(Product)
        assert table_name == "products"

    def test_get_table_name_without_custom_table_name(self) -> None:
        """_get_table_name should return lowercase class name if no Meta.table_name."""
        from framework_m.adapters.web.meta_router import _get_table_name

        class SimpleDoc(BaseDocType):
            name: str = ""

        table_name = _get_table_name(SimpleDoc)
        assert table_name == "simpledoc"

    def test_get_table_name_with_meta_but_no_table_name(self) -> None:
        """_get_table_name should return lowercase class name if Meta exists but no table_name."""
        from framework_m.adapters.web.meta_router import _get_table_name

        class DocWithMeta(BaseDocType):
            name: str = ""

            class Meta:
                api_resource: ClassVar[bool] = True

        table_name = _get_table_name(DocWithMeta)
        assert table_name == "docwithmeta"


# =============================================================================
# Tests for CRUD Routes with Mock Repository
# =============================================================================


class TestCrudRoutesWithMockRepo:
    """Test CRUD routes with mock repository for complete coverage."""

    @pytest.fixture(autouse=True)
    def register_product(self) -> None:
        """Register Product DocType."""
        registry = MetaRegistry.get_instance()
        try:
            registry.get_doctype("Product")
        except KeyError:
            registry.register_doctype(Product)

    @pytest.fixture
    def mock_repo_factory(self) -> MagicMock:
        """Create mock repository factory."""
        mock_factory = MagicMock()
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_factory.session_factory.get_session.return_value = mock_session
        return mock_factory

    @pytest.fixture
    def app_with_repo_factory(self, mock_repo_factory: MagicMock) -> Litestar:
        """Create app with mock repository factory in state."""
        from framework_m.adapters.web.meta_router import create_meta_router

        def permission_denied_handler(
            request: object, exc: PermissionDeniedError
        ) -> Response[dict[str, str]]:
            return Response(
                content={"error": "PermissionDenied", "message": str(exc)},
                status_code=HTTP_403_FORBIDDEN,
            )

        def not_found_handler(
            request: object, exc: NotFoundException
        ) -> Response[dict[str, str]]:
            return Response(
                content={"error": "NotFound", "message": str(exc.detail)},
                status_code=404,
            )

        router = create_meta_router()
        app = Litestar(
            route_handlers=[router],
            exception_handlers={
                PermissionDeniedError: permission_denied_handler,
                NotFoundException: not_found_handler,
            },
        )
        app.state.repository_factory = mock_repo_factory
        return app

    @pytest.fixture
    def client_with_repo(self, app_with_repo_factory: Litestar) -> TestClient[Litestar]:
        """Create test client with repository."""
        return TestClient(app_with_repo_factory)

    @pytest.mark.asyncio
    async def test_list_with_repo_factory_and_results(
        self, client_with_repo: TestClient[Litestar], mock_repo_factory: MagicMock
    ) -> None:
        """Test list endpoint with repository returning results."""
        # Setup mock repository
        mock_repo = AsyncMock()
        mock_result = MagicMock()
        mock_result.items = [
            Product(name="Product1", price=10.0),
            Product(name="Product2", price=20.0),
        ]
        mock_result.total = 2
        mock_repo.list_entities.return_value = mock_result
        mock_repo_factory.get_repository.return_value = mock_repo

        response = client_with_repo.get("/api/v1/Product?limit=10&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 2
        assert data["has_more"] is False

    @pytest.mark.asyncio
    async def test_list_with_field_selection(
        self, client_with_repo: TestClient[Litestar], mock_repo_factory: MagicMock
    ) -> None:
        """Test list endpoint with field selection."""
        mock_repo = AsyncMock()
        mock_result = MagicMock()
        mock_result.items = [
            Product(name="Product1", price=10.0),
        ]
        mock_result.total = 1
        mock_repo.list_entities.return_value = mock_result
        mock_repo_factory.get_repository.return_value = mock_repo

        response = client_with_repo.get("/api/v1/Product?fields=name,price")

        assert response.status_code == 200
        data = response.json()
        # Items should only have selected fields
        assert "name" in data["items"][0]
        assert "price" in data["items"][0]

    @pytest.mark.asyncio
    async def test_list_with_has_more_true(
        self, client_with_repo: TestClient[Litestar], mock_repo_factory: MagicMock
    ) -> None:
        """Test list endpoint with has_more=True."""
        mock_repo = AsyncMock()
        mock_result = MagicMock()
        # Return 10 items with total of 20
        mock_result.items = [Product(name=f"Product{i}") for i in range(10)]
        mock_result.total = 20
        mock_repo.list_entities.return_value = mock_result
        mock_repo_factory.get_repository.return_value = mock_repo

        response = client_with_repo.get("/api/v1/Product?limit=10&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert data["has_more"] is True

    @pytest.mark.asyncio
    async def test_create_with_repo_saves_document(
        self, client_with_repo: TestClient[Litestar], mock_repo_factory: MagicMock
    ) -> None:
        """Test create endpoint saves document via repository."""
        mock_repo = AsyncMock()
        saved_product = Product(name="NewProduct", price=15.0)
        mock_repo.save.return_value = saved_product
        mock_repo_factory.get_repository.return_value = mock_repo

        # Mock permission to allow creation
        with patch(
            "framework_m.adapters.web.meta_router._check_permission"
        ) as mock_perm:
            mock_perm.return_value = None  # Authorized

            response = client_with_repo.post(
                "/api/v1/Product",
                json={"name": "NewProduct", "price": 15.0},
            )

            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "NewProduct"

    @pytest.mark.asyncio
    async def test_get_entity_not_found(
        self, client_with_repo: TestClient[Litestar], mock_repo_factory: MagicMock
    ) -> None:
        """Test get entity returns 404 when not found."""
        mock_repo = AsyncMock()
        mock_repo.get.return_value = None  # Not found
        mock_repo_factory.get_repository.return_value = mock_repo

        # Mock permission to allow reading
        with patch(
            "framework_m.adapters.web.meta_router._check_permission"
        ) as mock_perm:
            mock_perm.return_value = None

            entity_id = uuid4()
            response = client_with_repo.get(f"/api/v1/Product/{entity_id}")

            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_update_entity_success(
        self, client_with_repo: TestClient[Litestar], mock_repo_factory: MagicMock
    ) -> None:
        """Test update entity successfully."""
        mock_repo = AsyncMock()
        existing_product = Product(name="OldName", price=10.0, docstatus=0)
        updated_product = Product(name="NewName", price=10.0, docstatus=0)
        mock_repo.get.return_value = existing_product
        mock_repo.save.return_value = updated_product
        mock_repo_factory.get_repository.return_value = mock_repo

        with patch(
            "framework_m.adapters.web.meta_router._check_permission"
        ) as mock_perm:
            mock_perm.return_value = None

            entity_id = existing_product.id
            response = client_with_repo.put(
                f"/api/v1/Product/{entity_id}",
                json={"name": "NewName"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "NewName"

    @pytest.mark.asyncio
    async def test_update_submitted_document_fails(
        self, client_with_repo: TestClient[Litestar], mock_repo_factory: MagicMock
    ) -> None:
        """Test updating submitted document raises error."""
        mock_repo = AsyncMock()
        submitted_product = Product(name="Product", price=10.0, docstatus=1)
        mock_repo.get.return_value = submitted_product
        mock_repo_factory.get_repository.return_value = mock_repo

        with patch(
            "framework_m.adapters.web.meta_router._check_permission"
        ) as mock_perm:
            mock_perm.return_value = None

            entity_id = submitted_product.id
            response = client_with_repo.put(
                f"/api/v1/Product/{entity_id}",
                json={"name": "NewName"},
            )

            assert response.status_code == 403
            data = response.json()
            assert "submitted" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_delete_entity_success(
        self, client_with_repo: TestClient[Litestar], mock_repo_factory: MagicMock
    ) -> None:
        """Test delete entity successfully."""
        mock_repo = AsyncMock()
        existing_product = Product(name="Product", price=10.0, docstatus=0)
        mock_repo.get.return_value = existing_product
        mock_repo.delete.return_value = None
        mock_repo_factory.get_repository.return_value = mock_repo

        with patch(
            "framework_m.adapters.web.meta_router._check_permission"
        ) as mock_perm:
            mock_perm.return_value = None

            entity_id = existing_product.id
            response = client_with_repo.delete(f"/api/v1/Product/{entity_id}")

            assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_submitted_document_fails(
        self, client_with_repo: TestClient[Litestar], mock_repo_factory: MagicMock
    ) -> None:
        """Test deleting submitted document raises error."""
        mock_repo = AsyncMock()
        submitted_product = Product(name="Product", price=10.0, docstatus=1)
        mock_repo.get.return_value = submitted_product
        mock_repo_factory.get_repository.return_value = mock_repo

        with patch(
            "framework_m.adapters.web.meta_router._check_permission"
        ) as mock_perm:
            mock_perm.return_value = None

            entity_id = submitted_product.id
            response = client_with_repo.delete(f"/api/v1/Product/{entity_id}")

            assert response.status_code == 403


# =============================================================================
# Tests for Routes Without Repository Factory
# =============================================================================


class TestCrudRoutesWithoutRepoFactory:
    """Test CRUD routes when no repository factory is available (mock mode)."""

    @pytest.fixture(autouse=True)
    def register_product(self) -> None:
        """Register Product DocType."""
        registry = MetaRegistry.get_instance()
        try:
            registry.get_doctype("Product")
        except KeyError:
            registry.register_doctype(Product)

    @pytest.fixture
    def app_without_repo(self) -> Litestar:
        """Create app without repository factory."""
        from framework_m.adapters.web.meta_router import create_meta_router

        def permission_denied_handler(
            request: object, exc: PermissionDeniedError
        ) -> Response[dict[str, str]]:
            return Response(
                content={"error": "PermissionDenied", "message": str(exc)},
                status_code=HTTP_403_FORBIDDEN,
            )

        router = create_meta_router()
        app = Litestar(
            route_handlers=[router],
            exception_handlers={PermissionDeniedError: permission_denied_handler},
        )
        # No repository_factory in state
        return app

    @pytest.fixture
    def client_no_repo(self, app_without_repo: Litestar) -> TestClient[Litestar]:
        """Create test client without repository."""
        return TestClient(app_without_repo)

    def test_list_without_repo_returns_empty(
        self, client_no_repo: TestClient[Litestar]
    ) -> None:
        """Test list endpoint returns empty result when no repo factory."""
        response = client_no_repo.get("/api/v1/Product")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_create_without_repo_returns_mock(
        self, client_no_repo: TestClient[Litestar]
    ) -> None:
        """Test create endpoint returns mock response when no repo factory."""
        with patch(
            "framework_m.adapters.web.meta_router._check_permission"
        ) as mock_perm:
            mock_perm.return_value = None

            response = client_no_repo.post(
                "/api/v1/Product",
                json={"name": "Product", "price": 10.0},
            )

            assert response.status_code == 201
            data = response.json()
            assert "id" in data
            assert data["doctype"] == "Product"

    def test_get_without_repo_returns_mock(
        self, client_no_repo: TestClient[Litestar]
    ) -> None:
        """Test get endpoint returns mock response when no repo factory."""
        with patch(
            "framework_m.adapters.web.meta_router._check_permission"
        ) as mock_perm:
            mock_perm.return_value = None

            entity_id = uuid4()
            response = client_no_repo.get(f"/api/v1/Product/{entity_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == str(entity_id)

    def test_update_without_repo_returns_mock(
        self, client_no_repo: TestClient[Litestar]
    ) -> None:
        """Test update endpoint returns mock response when no repo factory."""
        with patch(
            "framework_m.adapters.web.meta_router._check_permission"
        ) as mock_perm:
            mock_perm.return_value = None

            entity_id = uuid4()
            response = client_no_repo.put(
                f"/api/v1/Product/{entity_id}",
                json={"name": "Updated"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated"

    def test_delete_without_repo_succeeds(
        self, client_no_repo: TestClient[Litestar]
    ) -> None:
        """Test delete endpoint succeeds when no repo factory."""
        with patch(
            "framework_m.adapters.web.meta_router._check_permission"
        ) as mock_perm:
            mock_perm.return_value = None

            entity_id = uuid4()
            response = client_no_repo.delete(f"/api/v1/Product/{entity_id}")

            assert response.status_code == 204


# =============================================================================
# Tests for Repository Factory with None Repository
# =============================================================================


class TestCrudRoutesWithNoneRepository:
    """Test CRUD routes when repository_factory returns None."""

    @pytest.fixture(autouse=True)
    def register_product(self) -> None:
        """Register Product DocType."""
        registry = MetaRegistry.get_instance()
        try:
            registry.get_doctype("Product")
        except KeyError:
            registry.register_doctype(Product)

    @pytest.fixture
    def app_with_none_repo(self) -> Litestar:
        """Create app with repository factory that returns None."""
        from framework_m.adapters.web.meta_router import create_meta_router

        def permission_denied_handler(
            request: object, exc: PermissionDeniedError
        ) -> Response[dict[str, str]]:
            return Response(
                content={"error": "PermissionDenied", "message": str(exc)},
                status_code=HTTP_403_FORBIDDEN,
            )

        router = create_meta_router()
        app = Litestar(
            route_handlers=[router],
            exception_handlers={PermissionDeniedError: permission_denied_handler},
        )

        # Mock factory that returns None
        mock_factory = MagicMock()
        mock_factory.get_repository.return_value = None
        app.state.repository_factory = mock_factory
        return app

    @pytest.fixture
    def client_none_repo(self, app_with_none_repo: Litestar) -> TestClient[Litestar]:
        """Create test client with None repository."""
        return TestClient(app_with_none_repo)

    def test_list_with_none_repo_returns_empty(
        self, client_none_repo: TestClient[Litestar]
    ) -> None:
        """Test list endpoint returns empty when repository is None."""
        response = client_none_repo.get("/api/v1/Product")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0


# =============================================================================
# Tests for create_meta_router with KeyError
# =============================================================================


class TestCreateMetaRouterKeyError:
    """Test create_meta_router handles KeyError gracefully."""

    def test_meta_router_handles_key_error(self) -> None:
        """Test that create_meta_router skips DocTypes that raise KeyError."""
        from framework_m.adapters.web.meta_router import create_meta_router

        registry = MetaRegistry.get_instance()

        # Mock list_doctypes to return a name that will cause KeyError in get_doctype
        with (
            patch.object(registry, "list_doctypes", return_value=["NonExistent"]),
            patch.object(registry, "get_doctype", side_effect=KeyError),
        ):
            router = create_meta_router()
            # Should create router successfully despite KeyError
            assert router is not None


# =============================================================================
# Tests for _check_permission with resource_id
# =============================================================================


class TestCheckPermissionWithResourceId:
    """Test _check_permission with resource_id parameter."""

    @pytest.mark.asyncio
    async def test_check_permission_with_resource_id(self) -> None:
        """Test _check_permission includes resource_id in request."""
        from unittest.mock import AsyncMock, patch

        from framework_m.adapters.web.meta_router import _check_permission

        mock_result = AsyncMock()
        mock_result.authorized = True

        with patch(
            "framework_m.adapters.web.meta_router.RbacPermissionAdapter"
        ) as mock_adapter:
            mock_instance = AsyncMock()
            mock_instance.evaluate = AsyncMock(return_value=mock_result)
            mock_adapter.return_value = mock_instance

            await _check_permission(
                user_id="user1",
                user_roles=["User"],
                user_teams=["team1"],
                action="read",
                doctype_name="Product",
                resource_id="123",
            )

            # Verify resource_id was passed
            call_args = mock_instance.evaluate.call_args
            assert call_args[0][0].resource_id == "123"
