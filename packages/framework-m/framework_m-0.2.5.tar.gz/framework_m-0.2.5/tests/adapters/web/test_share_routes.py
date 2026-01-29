"""Tests for Share API Routes.

TDD tests for the share management API endpoints.
Tests written FIRST per CONTRIBUTING.md guidelines.
"""

import pytest
from litestar import Litestar
from litestar.testing import TestClient

from framework_m.adapters.web.share_routes import (
    CreateShareRequest,
    ShareController,
    ShareResponse,
)
from framework_m.core.doctypes.document_share import ShareType

# =============================================================================
# Test Share Controller Structure
# =============================================================================


class TestShareControllerStructure:
    """Test ShareController route structure."""

    def test_share_controller_has_correct_path(self) -> None:
        """ShareController should have /api/v1 base path."""
        assert ShareController.path == "/api/v1"

    def test_share_controller_has_share_tag(self) -> None:
        """ShareController should have 'Shares' tag for OpenAPI."""
        assert "Shares" in ShareController.tags


class TestCreateShareRequest:
    """Test CreateShareRequest DTO."""

    def test_create_share_request_minimal(self) -> None:
        """Can create request with minimal fields."""
        request = CreateShareRequest(
            doctype_name="Invoice",
            doc_id="INV-001",
            shared_with="alice",
        )

        assert request.doctype_name == "Invoice"
        assert request.doc_id == "INV-001"
        assert request.shared_with == "alice"
        assert request.share_type == ShareType.USER
        assert request.granted_permissions == ["read"]

    def test_create_share_request_full(self) -> None:
        """Can create request with all fields."""
        request = CreateShareRequest(
            doctype_name="Report",
            doc_id="RPT-123",
            shared_with="Manager",
            share_type=ShareType.ROLE,
            granted_permissions=["read", "write"],
            note="Sharing for Q4 review",
        )

        assert request.share_type == ShareType.ROLE
        assert "write" in request.granted_permissions
        assert request.note == "Sharing for Q4 review"


class TestShareResponse:
    """Test ShareResponse DTO."""

    def test_share_response_from_share(self) -> None:
        """Can create ShareResponse from DocumentShare."""
        from framework_m.core.doctypes.document_share import DocumentShare

        share = DocumentShare(
            name="share-001",
            doctype_name="Invoice",
            doc_id="INV-001",
            shared_with="bob",
            share_type=ShareType.USER,
            granted_permissions=["read"],
            owner="alice",
        )

        response = ShareResponse.from_share(share)

        assert response.doctype_name == "Invoice"
        assert response.doc_id == "INV-001"
        assert response.shared_with == "bob"
        assert response.share_type == "user"
        assert response.owner == "alice"


# =============================================================================
# Test Share API Endpoints
# =============================================================================


class TestShareAPIEndpoints:
    """Test Share API endpoints with Litestar test client."""

    @pytest.fixture
    def test_app(self) -> Litestar:
        """Create test app with share routes."""
        from litestar import Litestar

        return Litestar(route_handlers=[ShareController])

    @pytest.fixture
    def test_client(self, test_app: Litestar) -> TestClient[Litestar]:
        """Create test client."""
        return TestClient(test_app)

    def test_create_share_endpoint(self, test_client: TestClient[Litestar]) -> None:
        """POST /api/v1/share should create a share."""
        response = test_client.post(
            "/api/v1/share",
            json={
                "doctype_name": "Invoice",
                "doc_id": "INV-001",
                "shared_with": "bob",
                "share_type": "user",
                "granted_permissions": ["read"],
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["doctype_name"] == "Invoice"
        assert data["doc_id"] == "INV-001"
        assert data["shared_with"] == "bob"

    def test_list_shares_endpoint(self, test_client: TestClient[Litestar]) -> None:
        """GET /api/v1/{doctype}/{id}/shares should list shares."""
        response = test_client.get("/api/v1/Invoice/INV-001/shares")

        assert response.status_code == 200
        data = response.json()
        assert "shares" in data
        assert "total" in data


# =============================================================================
# Test Import
# =============================================================================


class TestShareRoutesImport:
    """Test share routes can be imported."""

    def test_import_share_router(self) -> None:
        """share_router should be importable."""
        from framework_m.adapters.web import share_router

        assert share_router is not None

    def test_import_share_controller(self) -> None:
        """ShareController should be importable."""
        from framework_m.adapters.web import ShareController

        assert ShareController is not None
