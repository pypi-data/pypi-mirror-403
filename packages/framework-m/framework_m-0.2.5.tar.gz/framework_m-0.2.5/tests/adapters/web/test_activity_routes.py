"""Tests for Activity Feed API Routes.

Tests cover:
- ActivityController endpoint presence
- Response models
- Query parameters
- Integration tests with TestClient
"""

import pytest
from litestar import Litestar
from litestar.testing import TestClient

from framework_m.adapters.web.activity_routes import (
    ActivityController,
    ActivityEntryResponse,
    ActivityFeedResponse,
    ActivityQueryParams,
)
from framework_m.core.interfaces.audit import AuditEntry

# =============================================================================
# Test: Import
# =============================================================================


class TestActivityRoutesImport:
    """Tests for Activity routes import."""

    def test_import_activity_controller(self) -> None:
        """ActivityController should be importable."""
        from framework_m.adapters.web.activity_routes import ActivityController

        assert ActivityController is not None

    def test_import_response_models(self) -> None:
        """Response models should be importable."""
        from framework_m.adapters.web.activity_routes import (
            ActivityEntryResponse,
            ActivityFeedResponse,
        )

        assert ActivityEntryResponse is not None
        assert ActivityFeedResponse is not None

    def test_import_query_params(self) -> None:
        """ActivityQueryParams should be importable."""
        from framework_m.adapters.web.activity_routes import ActivityQueryParams

        assert ActivityQueryParams is not None


# =============================================================================
# Test: ActivityController
# =============================================================================


class TestActivityController:
    """Tests for ActivityController."""

    def test_controller_path(self) -> None:
        """Controller should have correct path."""
        assert ActivityController.path == "/api/v1/activity"

    def test_controller_tags(self) -> None:
        """Controller should have Activity tag."""
        assert "Activity" in ActivityController.tags

    def test_controller_has_list_endpoint(self) -> None:
        """Controller should have list_activities method."""
        assert hasattr(ActivityController, "list_activities")


# =============================================================================
# Test: Response Models
# =============================================================================


class TestActivityEntryResponse:
    """Tests for ActivityEntryResponse model."""

    def test_create_from_audit_entry(self) -> None:
        """from_audit_entry should convert AuditEntry."""
        entry = AuditEntry(
            user_id="user-001",
            action="create",
            doctype="Invoice",
            document_id="INV-001",
            changes={"status": {"old": None, "new": "draft"}},
            metadata={"request_id": "req-123"},
        )

        response = ActivityEntryResponse.from_audit_entry(entry)

        assert response.id == entry.id
        assert response.user_id == "user-001"
        assert response.action == "create"
        assert response.doctype == "Invoice"
        assert response.document_id == "INV-001"
        assert response.changes is not None
        assert response.metadata is not None

    def test_from_audit_entry_without_changes(self) -> None:
        """from_audit_entry should handle None changes."""
        entry = AuditEntry(
            user_id="user-001",
            action="read",
            doctype="Invoice",
            document_id="INV-001",
        )

        response = ActivityEntryResponse.from_audit_entry(entry)

        assert response.changes is None
        assert response.metadata is None


class TestActivityFeedResponse:
    """Tests for ActivityFeedResponse model."""

    def test_create_response(self) -> None:
        """ActivityFeedResponse should hold list of entries."""
        response = ActivityFeedResponse(
            activities=[],
            total=0,
            limit=50,
            offset=0,
        )

        assert response.activities == []
        assert response.total == 0
        assert response.limit == 50
        assert response.offset == 0

    def test_response_with_entries(self) -> None:
        """ActivityFeedResponse should accept entries."""
        entry = AuditEntry(
            user_id="user-001",
            action="create",
            doctype="Todo",
            document_id="TODO-001",
        )
        activity = ActivityEntryResponse.from_audit_entry(entry)

        response = ActivityFeedResponse(
            activities=[activity],
            total=1,
            limit=50,
            offset=0,
        )

        assert len(response.activities) == 1
        assert response.activities[0].user_id == "user-001"


# =============================================================================
# Test: ActivityQueryParams
# =============================================================================


class TestActivityQueryParams:
    """Tests for ActivityQueryParams model."""

    def test_default_values(self) -> None:
        """QueryParams should have default values."""
        params = ActivityQueryParams()

        assert params.user_id is None
        assert params.action is None
        assert params.doctype is None
        assert params.document_id is None
        assert params.limit == 50
        assert params.offset == 0

    def test_validation_limit_max(self) -> None:
        """QueryParams should enforce limit max."""
        params = ActivityQueryParams(limit=1000)

        assert params.limit == 1000

    def test_validation_limit_min(self) -> None:
        """QueryParams should enforce limit min."""
        params = ActivityQueryParams(limit=1)

        assert params.limit == 1


# =============================================================================
# Test: Integration Tests with TestClient
# =============================================================================


class TestActivityControllerIntegration:
    """Integration tests for ActivityController using TestClient."""

    @pytest.fixture
    def app(self) -> Litestar:
        """Create test app with activity controller."""
        return Litestar(route_handlers=[ActivityController])

    @pytest.fixture
    def client(self, app: Litestar) -> TestClient:
        """Create test client."""
        return TestClient(app)

    def test_list_activities_endpoint(self, client: TestClient) -> None:
        """GET /activity should return activity feed."""
        response = client.get("/api/v1/activity/")

        assert response.status_code == 200
        data = response.json()
        assert "activities" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data

    def test_list_activities_with_filters(self, client: TestClient) -> None:
        """GET /activity should accept filter params."""
        response = client.get("/api/v1/activity/?user_id=user-001&action=create")

        assert response.status_code == 200
        data = response.json()
        assert "activities" in data

    def test_list_activities_with_pagination(self, client: TestClient) -> None:
        """GET /activity should accept limit and offset."""
        response = client.get("/api/v1/activity/?limit=10&offset=5")

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 10
        assert data["offset"] == 5

    def test_list_activities_limit_clamped(self, client: TestClient) -> None:
        """GET /activity should clamp limit to max 1000."""
        response = client.get("/api/v1/activity/?limit=2000")

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 1000

    def test_list_activities_doctype_filter(self, client: TestClient) -> None:
        """GET /activity should filter by doctype."""
        response = client.get("/api/v1/activity/?doctype=Invoice")

        assert response.status_code == 200

    def test_list_activities_document_id_filter(self, client: TestClient) -> None:
        """GET /activity should filter by document_id."""
        response = client.get("/api/v1/activity/?document_id=INV-001")

        assert response.status_code == 200
