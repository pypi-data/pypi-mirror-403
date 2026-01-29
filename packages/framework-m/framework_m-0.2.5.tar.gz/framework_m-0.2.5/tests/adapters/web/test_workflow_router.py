"""Tests for Workflow Router.

TDD tests for the workflow API routes that expose workflow state and transitions.
Tests written FIRST per CONTRIBUTING.md guidelines.

Covers:
- GET /api/v1/workflow/{doctype}/{id}/state - Get workflow state
- GET /api/v1/workflow/{doctype}/{id}/actions - Get available actions
- POST /api/v1/workflow/{doctype}/{id}/transition - Execute transition
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from litestar import Litestar
from litestar.testing import TestClient

from framework_m.adapters.web.workflow_router import (
    TransitionRequestDTO,
    TransitionResponse,
    WorkflowActionsResponse,
    WorkflowStateResponse,
    execute_transition,
    get_available_actions,
    get_workflow_state,
    workflow_router,
)

if TYPE_CHECKING:
    from litestar.testing import TestClient as TestClientType


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def test_app() -> Litestar:
    """Create a test Litestar app with workflow router."""
    return Litestar(route_handlers=[workflow_router])


@pytest.fixture
def client(test_app: Litestar) -> TestClientType[Litestar]:
    """Create a test client for the workflow router."""
    return TestClient(test_app)


# =============================================================================
# Test Workflow Router Registration
# =============================================================================


class TestWorkflowRouterRegistration:
    """Test that workflow router is properly configured."""

    def test_workflow_router_has_correct_path(self) -> None:
        """Workflow router should have /api/v1/workflow prefix."""
        assert workflow_router.path == "/api/v1/workflow"

    def test_workflow_router_has_correct_tags(self) -> None:
        """Workflow router should have 'workflow' tag."""
        assert "workflow" in workflow_router.tags

    def test_state_endpoint_exists(self, client: TestClientType[Litestar]) -> None:
        """Workflow router should expose /{doctype}/{id}/state endpoint."""
        response = client.get("/api/v1/workflow/TestDoc/123/state")
        assert response.status_code == 200

    def test_actions_endpoint_exists(self, client: TestClientType[Litestar]) -> None:
        """Workflow router should expose /{doctype}/{id}/actions endpoint."""
        response = client.get("/api/v1/workflow/TestDoc/123/actions")
        assert response.status_code == 200

    def test_transition_endpoint_exists(self, client: TestClientType[Litestar]) -> None:
        """Workflow router should expose POST /{doctype}/{id}/transition endpoint."""
        response = client.post(
            "/api/v1/workflow/TestDoc/123/transition",
            json={"action": "Submit"},
        )
        # POST endpoints return 201 Created by default in Litestar
        assert response.status_code in (200, 201)


# =============================================================================
# Test Response Models
# =============================================================================


class TestResponseModels:
    """Test Pydantic response models."""

    def test_workflow_state_response_model(self) -> None:
        """WorkflowStateResponse should have expected fields."""
        response = WorkflowStateResponse(
            doctype="Invoice",
            document_id="INV-001",
            workflow_name="invoice_approval",
            current_state="Draft",
            updated_at="2024-01-01T00:00:00",
            updated_by="user-1",
        )
        assert response.doctype == "Invoice"
        assert response.document_id == "INV-001"
        assert response.workflow_name == "invoice_approval"
        assert response.current_state == "Draft"
        assert response.updated_at == "2024-01-01T00:00:00"
        assert response.updated_by == "user-1"

    def test_workflow_state_response_optional_fields(self) -> None:
        """WorkflowStateResponse should allow None for optional fields."""
        response = WorkflowStateResponse(
            doctype="Invoice",
            document_id="INV-001",
            workflow_name="default",
            current_state="Draft",
        )
        assert response.updated_at is None
        assert response.updated_by is None

    def test_workflow_actions_response_model(self) -> None:
        """WorkflowActionsResponse should have expected fields."""
        response = WorkflowActionsResponse(
            doctype="Invoice",
            document_id="INV-001",
            current_state="Draft",
            actions=["Submit", "Cancel"],
        )
        assert response.doctype == "Invoice"
        assert response.document_id == "INV-001"
        assert response.current_state == "Draft"
        assert response.actions == ["Submit", "Cancel"]

    def test_workflow_actions_response_empty_actions(self) -> None:
        """WorkflowActionsResponse should allow empty actions list."""
        response = WorkflowActionsResponse(
            doctype="Invoice",
            document_id="INV-001",
            current_state="Approved",
            actions=[],
        )
        assert response.actions == []

    def test_transition_request_dto(self) -> None:
        """TransitionRequestDTO should have expected fields."""
        dto = TransitionRequestDTO(
            action="Submit",
            comment="Ready for approval",
        )
        assert dto.action == "Submit"
        assert dto.comment == "Ready for approval"

    def test_transition_request_dto_optional_comment(self) -> None:
        """TransitionRequestDTO should allow None comment."""
        dto = TransitionRequestDTO(action="Submit")
        assert dto.action == "Submit"
        assert dto.comment is None

    def test_transition_response_model(self) -> None:
        """TransitionResponse should have expected fields."""
        response = TransitionResponse(
            success=True,
            old_state="Draft",
            new_state="Pending",
            action="Submit",
            message="Transitioned successfully",
        )
        assert response.success is True
        assert response.old_state == "Draft"
        assert response.new_state == "Pending"
        assert response.action == "Submit"
        assert response.message == "Transitioned successfully"

    def test_transition_response_default_message(self) -> None:
        """TransitionResponse should have default empty message."""
        response = TransitionResponse(
            success=False,
            old_state="Draft",
            new_state="Draft",
            action="Approve",
        )
        assert response.message == ""


# =============================================================================
# Test GET /api/v1/workflow/{doctype}/{id}/state Endpoint
# =============================================================================


class TestGetWorkflowStateEndpoint:
    """Test the /api/v1/workflow/{doctype}/{id}/state endpoint."""

    def test_returns_state_for_document(self, client: TestClientType[Litestar]) -> None:
        """Should return workflow state for a document."""
        response = client.get("/api/v1/workflow/Customer/123/state")
        assert response.status_code == 200
        data = response.json()
        assert data["doctype"] == "Customer"
        assert data["document_id"] == "123"
        assert "current_state" in data
        assert "workflow_name" in data

    def test_returns_default_state_in_dev_mode(
        self, client: TestClientType[Litestar]
    ) -> None:
        """Should return Draft state in dev mode (no workflow service)."""
        response = client.get("/api/v1/workflow/Invoice/456/state")
        assert response.status_code == 200
        data = response.json()
        assert data["current_state"] == "Draft"
        assert data["workflow_name"] == "default"

    def test_state_includes_document_identifiers(
        self, client: TestClientType[Litestar]
    ) -> None:
        """Should include doctype and document_id in response."""
        response = client.get("/api/v1/workflow/Order/my-order-id/state")
        assert response.status_code == 200
        data = response.json()
        assert data["doctype"] == "Order"
        assert data["document_id"] == "my-order-id"


# =============================================================================
# Test GET /api/v1/workflow/{doctype}/{id}/actions Endpoint
# =============================================================================


class TestGetAvailableActionsEndpoint:
    """Test the /api/v1/workflow/{doctype}/{id}/actions endpoint."""

    def test_returns_actions_for_document(
        self, client: TestClientType[Litestar]
    ) -> None:
        """Should return available actions for a document."""
        response = client.get("/api/v1/workflow/Customer/123/actions")
        assert response.status_code == 200
        data = response.json()
        assert data["doctype"] == "Customer"
        assert data["document_id"] == "123"
        assert "actions" in data
        assert isinstance(data["actions"], list)

    def test_returns_default_actions_in_dev_mode(
        self, client: TestClientType[Litestar]
    ) -> None:
        """Should return Submit/Cancel actions in dev mode."""
        response = client.get("/api/v1/workflow/Invoice/456/actions")
        assert response.status_code == 200
        data = response.json()
        assert "Submit" in data["actions"]
        assert "Cancel" in data["actions"]

    def test_actions_include_current_state(
        self, client: TestClientType[Litestar]
    ) -> None:
        """Should include current state in actions response."""
        response = client.get("/api/v1/workflow/Order/789/actions")
        assert response.status_code == 200
        data = response.json()
        assert "current_state" in data
        assert data["current_state"] == "Draft"


# =============================================================================
# Test POST /api/v1/workflow/{doctype}/{id}/transition Endpoint
# =============================================================================


class TestExecuteTransitionEndpoint:
    """Test the POST /api/v1/workflow/{doctype}/{id}/transition endpoint."""

    def test_executes_transition_successfully(
        self, client: TestClientType[Litestar]
    ) -> None:
        """Should execute a valid transition."""
        response = client.post(
            "/api/v1/workflow/Customer/123/transition",
            json={"action": "Submit"},
        )
        assert response.status_code in (200, 201)
        data = response.json()
        assert data["success"] is True
        assert data["action"] == "Submit"

    def test_transition_returns_old_and_new_state(
        self, client: TestClientType[Litestar]
    ) -> None:
        """Should return old and new state after transition."""
        response = client.post(
            "/api/v1/workflow/Invoice/456/transition",
            json={"action": "Submit"},
        )
        assert response.status_code in (200, 201)
        data = response.json()
        assert "old_state" in data
        assert "new_state" in data
        assert data["old_state"] == "Draft"
        assert data["new_state"] == "Pending"

    def test_transition_with_comment(self, client: TestClientType[Litestar]) -> None:
        """Should accept optional comment with transition."""
        response = client.post(
            "/api/v1/workflow/Order/789/transition",
            json={"action": "Approve", "comment": "Looks good!"},
        )
        assert response.status_code in (200, 201)
        data = response.json()
        assert data["success"] is True

    def test_transition_requires_action_field(
        self, client: TestClientType[Litestar]
    ) -> None:
        """Should require 'action' field in request body."""
        response = client.post(
            "/api/v1/workflow/Customer/123/transition",
            json={},
        )
        # Pydantic validation should fail
        assert response.status_code == 400

    def test_transition_approve_action(self, client: TestClientType[Litestar]) -> None:
        """Should handle Approve action."""
        response = client.post(
            "/api/v1/workflow/Customer/123/transition",
            json={"action": "Approve"},
        )
        assert response.status_code in (200, 201)
        data = response.json()
        assert data["action"] == "Approve"
        assert data["new_state"] == "Approved"

    def test_transition_reject_action(self, client: TestClientType[Litestar]) -> None:
        """Should handle Reject action."""
        response = client.post(
            "/api/v1/workflow/Customer/123/transition",
            json={"action": "Reject"},
        )
        assert response.status_code in (200, 201)
        data = response.json()
        assert data["action"] == "Reject"
        assert data["new_state"] == "Rejected"

    def test_transition_cancel_action(self, client: TestClientType[Litestar]) -> None:
        """Should handle Cancel action."""
        response = client.post(
            "/api/v1/workflow/Customer/123/transition",
            json={"action": "Cancel"},
        )
        assert response.status_code in (200, 201)
        data = response.json()
        assert data["action"] == "Cancel"
        assert data["new_state"] == "Cancelled"

    def test_transition_message_included(
        self, client: TestClientType[Litestar]
    ) -> None:
        """Should include message in transition response."""
        response = client.post(
            "/api/v1/workflow/Invoice/123/transition",
            json={"action": "Submit"},
        )
        assert response.status_code in (200, 201)
        data = response.json()
        assert "message" in data
        assert len(data["message"]) > 0


# =============================================================================
# Test Functions Directly
# =============================================================================


class TestWorkflowFunctions:
    """Test workflow functions directly."""

    def test_get_workflow_state_is_async(self) -> None:
        """get_workflow_state should be an async function."""
        import inspect

        fn = getattr(get_workflow_state, "fn", get_workflow_state)
        assert inspect.iscoroutinefunction(fn)

    def test_get_available_actions_is_async(self) -> None:
        """get_available_actions should be an async function."""
        import inspect

        fn = getattr(get_available_actions, "fn", get_available_actions)
        assert inspect.iscoroutinefunction(fn)

    def test_execute_transition_is_async(self) -> None:
        """execute_transition should be an async function."""
        import inspect

        fn = getattr(execute_transition, "fn", execute_transition)
        assert inspect.iscoroutinefunction(fn)


# =============================================================================
# Test Edge Cases
# =============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_handles_special_characters_in_doctype(
        self, client: TestClientType[Litestar]
    ) -> None:
        """Should handle special characters in doctype name."""
        response = client.get("/api/v1/workflow/Purchase-Order/123/state")
        assert response.status_code == 200
        data = response.json()
        assert data["doctype"] == "Purchase-Order"

    def test_handles_uuid_document_id(self, client: TestClientType[Litestar]) -> None:
        """Should handle UUID format document IDs."""
        doc_id = "550e8400-e29b-41d4-a716-446655440000"
        response = client.get(f"/api/v1/workflow/Invoice/{doc_id}/state")
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == doc_id

    def test_handles_long_document_id(self, client: TestClientType[Litestar]) -> None:
        """Should handle long document IDs."""
        doc_id = "a" * 100
        response = client.get(f"/api/v1/workflow/Customer/{doc_id}/actions")
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == doc_id

    def test_unknown_action_returns_default_transition(
        self, client: TestClientType[Litestar]
    ) -> None:
        """Should handle unknown action with default transition."""
        response = client.post(
            "/api/v1/workflow/Customer/123/transition",
            json={"action": "UnknownAction"},
        )
        assert response.status_code in (200, 201)
        data = response.json()
        assert data["success"] is True
        # Default fallback for unknown actions
        assert data["new_state"] == "Submitted"
