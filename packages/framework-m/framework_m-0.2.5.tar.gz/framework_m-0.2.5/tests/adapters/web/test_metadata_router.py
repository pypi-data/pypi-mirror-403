"""Tests for Metadata Router.

TDD tests for the metadata API routes that expose DocType information.
Tests written FIRST per CONTRIBUTING.md guidelines.
"""

import pytest
from litestar import Litestar
from litestar.testing import TestClient

from framework_m.adapters.web.metadata_router import (
    DocTypeInfo,
    DocTypeListResponse,
    get_doctype_schema,
    list_doctypes,
    metadata_router,
)
from framework_m.core.domain.base_doctype import BaseDocType, Field
from framework_m.core.registry import MetaRegistry

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def clear_registry():
    """Clear the MetaRegistry before and after each test."""
    registry = MetaRegistry.get_instance()
    registry.clear()
    yield
    registry.clear()


# =============================================================================
# Test Data
# =============================================================================


class SampleDocType(BaseDocType):
    """Sample DocType for testing."""

    title: str = Field(description="Title of the document")

    class Meta:
        label = "Sample"
        is_child_table = False
        api_resource = True
        requires_auth = True
        apply_rls = True


class ChildDocType(BaseDocType):
    """Sample child table DocType for testing."""

    parent_id: str = Field(description="Parent document ID")
    value: str = Field(description="Value")

    class Meta:
        label = "Child Item"
        is_child_table = True
        api_resource = False


# =============================================================================
# Test Metadata Router Registration
# =============================================================================


class TestMetadataRouterRegistration:
    """Test that metadata router is properly configured."""

    def test_metadata_router_has_correct_path(self) -> None:
        """Metadata router should have /api/meta prefix."""
        assert metadata_router.path == "/api/meta"

    def test_doctypes_endpoint_exists(self) -> None:
        """Metadata router should expose /doctypes endpoint."""
        app = Litestar(route_handlers=[metadata_router])
        with TestClient(app) as client:
            response = client.get("/api/meta/doctypes")
            assert response.status_code == 200


# =============================================================================
# Test Response Models
# =============================================================================


class TestResponseModels:
    """Test Pydantic response models."""

    def test_doctype_info_model(self) -> None:
        """DocTypeInfo should have expected fields."""
        info = DocTypeInfo(
            name="Test",
            module="myapp.doctypes",
            label="Test Label",
            is_child_table=False,
            api_resource=True,
        )
        assert info.name == "Test"
        assert info.module == "myapp.doctypes"
        assert info.label == "Test Label"
        assert info.is_child_table is False
        assert info.api_resource is True

    def test_doctype_list_response_model(self) -> None:
        """DocTypeListResponse should contain list and count."""
        info = DocTypeInfo(name="Test", api_resource=True)
        response = DocTypeListResponse(doctypes=[info], count=1)
        assert len(response.doctypes) == 1
        assert response.count == 1


# =============================================================================
# Test GET /api/meta/doctypes Endpoint
# =============================================================================


class TestListDocTypesEndpoint:
    """Test the /api/meta/doctypes endpoint."""

    def test_returns_empty_list_when_no_doctypes(self) -> None:
        """Should return empty list when no DocTypes registered."""
        app = Litestar(route_handlers=[metadata_router])
        with TestClient(app) as client:
            response = client.get("/api/meta/doctypes")
            assert response.status_code == 200
            data = response.json()
            assert data["doctypes"] == []
            assert data["count"] == 0

    def test_returns_registered_doctypes(self) -> None:
        """Should return list of registered DocTypes."""
        registry = MetaRegistry.get_instance()
        registry.register_doctype(SampleDocType)

        app = Litestar(route_handlers=[metadata_router])
        with TestClient(app) as client:
            response = client.get("/api/meta/doctypes")
            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 1
            assert len(data["doctypes"]) == 1
            assert data["doctypes"][0]["name"] == "SampleDocType"

    def test_includes_doctype_metadata(self) -> None:
        """Should include metadata like label and api_resource."""
        registry = MetaRegistry.get_instance()
        registry.register_doctype(SampleDocType)

        app = Litestar(route_handlers=[metadata_router])
        with TestClient(app) as client:
            response = client.get("/api/meta/doctypes")
            assert response.status_code == 200
            data = response.json()
            doctype = data["doctypes"][0]
            assert doctype["label"] == "Sample"
            assert doctype["api_resource"] is True
            assert doctype["is_child_table"] is False

    def test_includes_child_table_doctypes(self) -> None:
        """Should include child table DocTypes with is_child_table=True."""
        registry = MetaRegistry.get_instance()
        registry.register_doctype(ChildDocType)

        app = Litestar(route_handlers=[metadata_router])
        with TestClient(app) as client:
            response = client.get("/api/meta/doctypes")
            assert response.status_code == 200
            data = response.json()
            doctype = data["doctypes"][0]
            assert doctype["is_child_table"] is True
            assert doctype["api_resource"] is False

    def test_returns_multiple_doctypes(self) -> None:
        """Should return all registered DocTypes."""
        registry = MetaRegistry.get_instance()
        registry.register_doctype(SampleDocType)
        registry.register_doctype(ChildDocType)

        app = Litestar(route_handlers=[metadata_router])
        with TestClient(app) as client:
            response = client.get("/api/meta/doctypes")
            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 2
            names = [d["name"] for d in data["doctypes"]]
            assert "SampleDocType" in names
            assert "ChildDocType" in names


# =============================================================================
# Test GET /api/meta/{doctype} Endpoint
# =============================================================================


class TestGetDocTypeSchemaEndpoint:
    """Test the /api/meta/{doctype} endpoint."""

    def test_returns_404_for_unknown_doctype(self) -> None:
        """Should return 404 for unregistered DocType."""
        app = Litestar(route_handlers=[metadata_router])
        with TestClient(app) as client:
            response = client.get("/api/meta/UnknownDocType")
            assert response.status_code == 404

    def test_returns_schema_for_registered_doctype(self) -> None:
        """Should return schema for registered DocType."""
        registry = MetaRegistry.get_instance()
        registry.register_doctype(SampleDocType)

        app = Litestar(route_handlers=[metadata_router])
        with TestClient(app) as client:
            response = client.get("/api/meta/SampleDocType")
            assert response.status_code == 200
            data = response.json()
            assert data["doctype"] == "SampleDocType"
            assert "schema" in data

    def test_schema_contains_json_schema(self) -> None:
        """Should include JSON Schema from Pydantic model."""
        registry = MetaRegistry.get_instance()
        registry.register_doctype(SampleDocType)

        app = Litestar(route_handlers=[metadata_router])
        with TestClient(app) as client:
            response = client.get("/api/meta/SampleDocType")
            assert response.status_code == 200
            data = response.json()
            schema = data["schema"]
            assert "properties" in schema
            assert "id" in schema["properties"]
            assert "name" in schema["properties"]
            assert "title" in schema["properties"]

    def test_includes_permissions_metadata(self) -> None:
        """Should include permissions from Meta class."""
        registry = MetaRegistry.get_instance()
        registry.register_doctype(SampleDocType)

        app = Litestar(route_handlers=[metadata_router])
        with TestClient(app) as client:
            response = client.get("/api/meta/SampleDocType")
            assert response.status_code == 200
            data = response.json()
            assert "permissions" in data
            assert "metadata" in data
            assert data["metadata"]["requires_auth"] is True
            assert data["metadata"]["apply_rls"] is True

    def test_includes_api_resource_flag(self) -> None:
        """Should include api_resource flag in metadata."""
        registry = MetaRegistry.get_instance()
        registry.register_doctype(SampleDocType)

        app = Litestar(route_handlers=[metadata_router])
        with TestClient(app) as client:
            response = client.get("/api/meta/SampleDocType")
            assert response.status_code == 200
            data = response.json()
            assert data["metadata"]["api_resource"] is True


# =============================================================================
# Test Functions Directly
# =============================================================================


class TestMetadataFunctions:
    """Test metadata functions directly."""

    def test_list_doctypes_is_async(self) -> None:
        """list_doctypes should be an async function."""
        import inspect

        # Litestar decorates handlers, so check the underlying function
        fn = getattr(list_doctypes, "fn", list_doctypes)
        assert inspect.iscoroutinefunction(fn)

    def test_get_doctype_schema_is_async(self) -> None:
        """get_doctype_schema should be an async function."""
        import inspect

        # Litestar decorates handlers, so check the underlying function
        fn = getattr(get_doctype_schema, "fn", get_doctype_schema)
        assert inspect.iscoroutinefunction(fn)
