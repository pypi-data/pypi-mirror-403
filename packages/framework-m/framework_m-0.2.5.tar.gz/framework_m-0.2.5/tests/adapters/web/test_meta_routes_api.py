"""Tests for Metadata API.

TDD tests for GET /api/meta/{doctype} endpoint that returns
DocType metadata including JSON schema, layout, and permissions.
"""

from typing import ClassVar

import pytest
from litestar import Litestar
from litestar.testing import TestClient

from framework_m.core.domain.base_doctype import BaseDocType, Field
from framework_m.core.registry import MetaRegistry

# =============================================================================
# Test DocTypes
# =============================================================================


class MetaTestInvoice(BaseDocType):
    """Test DocType with full metadata for metadata API tests."""

    customer: str = Field(title="Customer Name", description="Name of the customer")
    total: float = Field(default=0.0, title="Total Amount", description="Invoice total")
    status: str = Field(default="draft", title="Status", description="Invoice status")

    class Meta:
        requires_auth: ClassVar[bool] = True
        apply_rls: ClassVar[bool] = True
        rls_field: ClassVar[str] = "owner"
        api_resource: ClassVar[bool] = True
        layout: ClassVar[dict[str, list[dict[str, list[str]]]]] = {
            "sections": [
                {"fields": ["customer", "total"]},
                {"fields": ["status"]},
            ]
        }
        permissions: ClassVar[dict[str, list[str]]] = {
            "read": ["Employee", "Manager"],
            "write": ["Manager"],
            "create": ["Manager"],
            "delete": ["Admin"],
        }


class MetaTestPublicConfig(BaseDocType):
    """Test DocType with minimal metadata (public, no layout)."""

    key: str = Field(title="Config Key", description="Configuration key")
    value: str = Field(
        default="", title="Config Value", description="Configuration value"
    )

    class Meta:
        requires_auth: ClassVar[bool] = False
        apply_rls: ClassVar[bool] = False


# =============================================================================
# Tests for Metadata Endpoint
# =============================================================================


class TestMetadataEndpoint:
    """Tests for GET /api/meta/{doctype} endpoint."""

    @pytest.fixture(autouse=True)
    def register_doctypes(self) -> None:
        """Register test DocTypes in MetaRegistry."""
        registry = MetaRegistry.get_instance()
        try:
            registry.get_doctype("MetaTestInvoice")
        except KeyError:
            registry.register_doctype(MetaTestInvoice)
        try:
            registry.get_doctype("MetaTestPublicConfig")
        except KeyError:
            registry.register_doctype(MetaTestPublicConfig)

    @pytest.fixture
    def app(self) -> Litestar:
        """Create test app with metadata routes."""
        from framework_m.adapters.web.meta_routes import meta_routes_router

        return Litestar(route_handlers=[meta_routes_router])

    @pytest.fixture
    def client(self, app: Litestar) -> TestClient[Litestar]:
        """Create test client."""
        return TestClient(app)

    def test_meta_routes_router_is_importable(self) -> None:
        """meta_routes_router should be importable."""
        from framework_m.adapters.web.meta_routes import meta_routes_router

        assert meta_routes_router is not None

    def test_get_doctype_metadata_returns_schema(
        self, client: TestClient[Litestar]
    ) -> None:
        """Should return JSON schema for DocType."""
        response = client.get("/api/meta/MetaTestInvoice")

        assert response.status_code == 200
        data = response.json()
        assert "schema" in data
        assert "properties" in data["schema"]
        # Should have our custom fields in schema
        assert "customer" in data["schema"]["properties"]
        assert "total" in data["schema"]["properties"]

    def test_get_doctype_metadata_returns_layout(
        self, client: TestClient[Litestar]
    ) -> None:
        """Should return layout configuration."""
        response = client.get("/api/meta/MetaTestInvoice")

        assert response.status_code == 200
        data = response.json()
        assert "layout" in data
        assert "sections" in data["layout"]
        assert len(data["layout"]["sections"]) == 2

    def test_get_doctype_metadata_returns_permissions(
        self, client: TestClient[Litestar]
    ) -> None:
        """Should return permissions configuration."""
        response = client.get("/api/meta/MetaTestInvoice")

        assert response.status_code == 200
        data = response.json()
        assert "permissions" in data
        assert "read" in data["permissions"]
        assert "Manager" in data["permissions"]["read"]

    def test_get_doctype_metadata_returns_metadata(
        self, client: TestClient[Litestar]
    ) -> None:
        """Should return additional metadata (requires_auth, apply_rls, etc.)."""
        response = client.get("/api/meta/MetaTestInvoice")

        assert response.status_code == 200
        data = response.json()
        assert "metadata" in data
        assert data["metadata"]["requires_auth"] is True
        assert data["metadata"]["apply_rls"] is True
        assert data["metadata"]["rls_field"] == "owner"
        assert data["metadata"]["api_resource"] is True

    def test_get_doctype_metadata_returns_field_titles(
        self, client: TestClient[Litestar]
    ) -> None:
        """Schema should include field titles from Field(title=...)."""
        response = client.get("/api/meta/MetaTestInvoice")

        assert response.status_code == 200
        data = response.json()
        customer_field = data["schema"]["properties"]["customer"]
        assert customer_field.get("title") == "Customer Name"

    def test_get_doctype_metadata_returns_field_descriptions(
        self, client: TestClient[Litestar]
    ) -> None:
        """Schema should include field descriptions from Field(description=...)."""
        response = client.get("/api/meta/MetaTestInvoice")

        assert response.status_code == 200
        data = response.json()
        customer_field = data["schema"]["properties"]["customer"]
        assert customer_field.get("description") == "Name of the customer"

    def test_get_doctype_metadata_404_for_unknown(
        self, client: TestClient[Litestar]
    ) -> None:
        """Should return 404 for unknown DocType."""
        response = client.get("/api/meta/UnknownDocType")

        assert response.status_code == 404

    def test_get_doctype_metadata_public_config(
        self, client: TestClient[Litestar]
    ) -> None:
        """Should return metadata for public DocType."""
        response = client.get("/api/meta/MetaTestPublicConfig")

        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["requires_auth"] is False
        assert data["metadata"]["apply_rls"] is False
        # Empty layout/permissions should be empty dicts
        assert data["layout"] == {}
        assert data["permissions"] == {}
