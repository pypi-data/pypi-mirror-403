"""Tests for WorkflowProtocol.

TDD tests for the workflow system interface. This module tests the protocol
definition and validates that implementations correctly handle:
- Workflow state management
- State transitions with permission checks
- Action availability based on current state
- Event emission for state changes
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from framework_m.core.interfaces.auth_context import UserContext
    from framework_m.core.interfaces.workflow import (
        TransitionRequest,
        TransitionResult,
        WorkflowProtocol,
        WorkflowStateInfo,
    )


# ============================================================================
# Test Helper - In-Memory Workflow Adapter
# ============================================================================


class InMemoryWorkflowAdapter:
    """In-memory implementation of WorkflowProtocol for testing.

    Uses a simple purchase approval workflow:
    - States: Draft → Pending Approval → Approved/Rejected
    - Transitions:
        - submit (Draft → Pending Approval): Employee role
        - approve (Pending Approval → Approved): Manager/Admin role
        - reject (Pending Approval → Rejected): Manager/Admin role
    """

    def __init__(self) -> None:
        """Initialize the in-memory workflow storage."""

        self._states: dict[tuple[str, str], WorkflowStateInfo] = {}
        self._workflow_config = {
            "purchase_approval": {
                "states": ["Draft", "Pending Approval", "Approved", "Rejected"],
                "transitions": [
                    {
                        "from": "Draft",
                        "to": "Pending Approval",
                        "action": "submit",
                        "allowed_roles": ["Employee", "Manager", "Admin"],
                    },
                    {
                        "from": "Pending Approval",
                        "to": "Approved",
                        "action": "approve",
                        "allowed_roles": ["Manager", "Admin"],
                    },
                    {
                        "from": "Pending Approval",
                        "to": "Rejected",
                        "action": "reject",
                        "allowed_roles": ["Manager", "Admin"],
                    },
                ],
            }
        }

    async def start_workflow(
        self,
        doctype: str,
        doc_id: str,
        workflow_name: str,
        user: UserContext,
    ) -> WorkflowStateInfo:
        """Start a workflow on a document."""
        from framework_m.core.interfaces.workflow import WorkflowStateInfo

        if workflow_name not in self._workflow_config:
            raise ValueError(f"Unknown workflow: {workflow_name}")

        key = (doctype, doc_id)

        # If workflow already started, return current state (idempotent)
        if key in self._states:
            return self._states[key]

        # Create initial state
        initial_state = self._workflow_config[workflow_name]["states"][0]
        state_info = WorkflowStateInfo(
            doctype=doctype,
            document_id=doc_id,
            workflow_name=workflow_name,
            current_state=initial_state,
            updated_at=datetime.now(UTC),
            updated_by=user.id,
        )

        self._states[key] = state_info
        return state_info

    async def get_workflow_state(
        self, doctype: str, doc_id: str
    ) -> WorkflowStateInfo | None:
        """Get current workflow state for a document."""
        key = (doctype, doc_id)
        return self._states.get(key)

    async def transition(self, request: TransitionRequest) -> TransitionResult:
        """Attempt to transition a document to a new workflow state."""
        from framework_m.core.interfaces.workflow import (
            TransitionResult,
        )

        key = (request.doctype, request.doc_id)

        # Check if workflow exists
        if key not in self._states:
            return TransitionResult(
                success=False,
                old_state="",
                new_state="",
                action=request.action,
                message=f"No workflow found for {request.doctype} {request.doc_id}",
            )

        current_state_info = self._states[key]
        workflow_config = self._workflow_config[current_state_info.workflow_name]

        # Find matching transition
        transition = None
        for trans in workflow_config["transitions"]:
            if (
                trans["from"] == current_state_info.current_state
                and trans["action"] == request.action
            ):
                transition = trans
                break

        # No valid transition found
        if transition is None:
            return TransitionResult(
                success=False,
                old_state=current_state_info.current_state,
                new_state=current_state_info.current_state,
                action=request.action,
                message=f"Invalid action '{request.action}' from state '{current_state_info.current_state}'",
            )

        # Check user role permission
        user_roles = request.user.roles
        allowed_roles = transition["allowed_roles"]

        if not any(role in allowed_roles for role in user_roles):
            return TransitionResult(
                success=False,
                old_state=current_state_info.current_state,
                new_state=current_state_info.current_state,
                action=request.action,
                message=f"User does not have required role. Required: {allowed_roles}, User has: {user_roles}",
            )

        # Perform transition
        old_state = current_state_info.current_state
        new_state = transition["to"]

        self._states[key] = current_state_info.model_copy(
            update={
                "current_state": new_state,
                "updated_at": datetime.now(UTC),
                "updated_by": request.user.id,
            }
        )

        return TransitionResult(
            success=True,
            old_state=old_state,
            new_state=new_state,
            action=request.action,
            message=f"Transitioned from {old_state} to {new_state}",
        )

    async def get_available_actions(
        self, doctype: str, doc_id: str, user: UserContext
    ) -> list[str]:
        """Get list of actions available to user in current state."""
        key = (doctype, doc_id)

        if key not in self._states:
            return []

        current_state_info = self._states[key]
        workflow_config = self._workflow_config[current_state_info.workflow_name]

        available_actions = []
        user_roles = user.roles

        for transition in workflow_config["transitions"]:
            # Check if transition is from current state
            if transition["from"] != current_state_info.current_state:
                continue

            # Check if user has required role
            allowed_roles = transition["allowed_roles"]
            if any(role in allowed_roles for role in user_roles):
                available_actions.append(transition["action"])

        return available_actions


# ============================================================================
# Test Data & Fixtures
# ============================================================================


@pytest.fixture
def admin_user() -> UserContext:
    """Create an admin user context for testing."""
    from framework_m.core.interfaces.auth_context import UserContext

    return UserContext(
        id="admin-123",
        email="admin@example.com",
        roles=["Admin"],
        tenants=["default"],
        attributes={"roles": ["Admin"]},
    )


@pytest.fixture
def employee_user() -> UserContext:
    """Create an employee user context for testing."""
    from framework_m.core.interfaces.auth_context import UserContext

    return UserContext(
        id="emp-456",
        email="employee@example.com",
        roles=["Employee"],
        tenants=["default"],
        attributes={"roles": ["Employee"]},
    )


@pytest.fixture
def workflow_adapter() -> WorkflowProtocol:
    """Create an in-memory workflow adapter for testing."""
    return InMemoryWorkflowAdapter()


# ============================================================================
# Protocol Compliance Tests
# ============================================================================


class TestWorkflowProtocol:
    """Test that workflow implementations comply with the protocol."""

    async def test_protocol_has_required_methods(
        self, workflow_adapter: WorkflowProtocol
    ) -> None:
        """Verify the protocol defines all required methods."""
        assert hasattr(workflow_adapter, "start_workflow")
        assert hasattr(workflow_adapter, "get_workflow_state")
        assert hasattr(workflow_adapter, "transition")
        assert hasattr(workflow_adapter, "get_available_actions")

    async def test_start_workflow_returns_state_info(
        self, workflow_adapter: WorkflowProtocol, admin_user: UserContext
    ) -> None:
        """Test that start_workflow returns WorkflowStateInfo."""
        result = await workflow_adapter.start_workflow(
            doctype="PurchaseOrder",
            doc_id="PO-001",
            workflow_name="purchase_approval",
            user=admin_user,
        )

        assert result is not None
        assert hasattr(result, "current_state")
        assert hasattr(result, "workflow_name")
        assert hasattr(result, "doctype")
        assert hasattr(result, "document_id")
        assert isinstance(result.current_state, str)

    async def test_get_workflow_state_returns_state_info(
        self, workflow_adapter: WorkflowProtocol, admin_user: UserContext
    ) -> None:
        """Test that get_workflow_state returns current state info."""
        # Start a workflow first
        await workflow_adapter.start_workflow(
            doctype="PurchaseOrder",
            doc_id="PO-002",
            workflow_name="purchase_approval",
            user=admin_user,
        )

        # Get the state
        state = await workflow_adapter.get_workflow_state(
            doctype="PurchaseOrder", doc_id="PO-002"
        )

        assert state is not None
        assert hasattr(state, "current_state")
        assert isinstance(state.current_state, str)

    async def test_transition_returns_transition_result(
        self, workflow_adapter: WorkflowProtocol, admin_user: UserContext
    ) -> None:
        """Test that transition returns TransitionResult."""
        # Start workflow
        await workflow_adapter.start_workflow(
            doctype="PurchaseOrder",
            doc_id="PO-003",
            workflow_name="purchase_approval",
            user=admin_user,
        )

        # Perform transition
        from framework_m.core.interfaces.workflow import TransitionRequest

        request = TransitionRequest(
            doctype="PurchaseOrder",
            doc_id="PO-003",
            action="submit",
            user=admin_user,
        )

        result = await workflow_adapter.transition(request)

        assert result is not None
        assert hasattr(result, "success")
        assert hasattr(result, "old_state")
        assert hasattr(result, "new_state")
        assert isinstance(result.success, bool)

    async def test_get_available_actions_returns_list(
        self, workflow_adapter: WorkflowProtocol, admin_user: UserContext
    ) -> None:
        """Test that get_available_actions returns list of action names."""
        # Start workflow
        await workflow_adapter.start_workflow(
            doctype="PurchaseOrder",
            doc_id="PO-004",
            workflow_name="purchase_approval",
            user=admin_user,
        )

        # Get available actions
        actions = await workflow_adapter.get_available_actions(
            doctype="PurchaseOrder", doc_id="PO-004", user=admin_user
        )

        assert isinstance(actions, list)
        assert all(isinstance(action, str) for action in actions)


# ============================================================================
# Workflow Lifecycle Tests
# ============================================================================


class TestWorkflowLifecycle:
    """Test workflow lifecycle from start to completion."""

    async def test_start_workflow_creates_initial_state(
        self, workflow_adapter: WorkflowProtocol, admin_user: UserContext
    ) -> None:
        """Test that starting a workflow creates initial state."""
        result = await workflow_adapter.start_workflow(
            doctype="PurchaseOrder",
            doc_id="PO-100",
            workflow_name="purchase_approval",
            user=admin_user,
        )

        assert result.current_state == "Draft"
        assert result.workflow_name == "purchase_approval"
        assert result.doctype == "PurchaseOrder"
        assert result.document_id == "PO-100"

    async def test_get_state_for_nonexistent_document_returns_none(
        self, workflow_adapter: WorkflowProtocol
    ) -> None:
        """Test that getting state for non-existent doc returns None."""
        state = await workflow_adapter.get_workflow_state(
            doctype="PurchaseOrder", doc_id="NONEXISTENT"
        )

        assert state is None

    async def test_transition_changes_state(
        self, workflow_adapter: WorkflowProtocol, admin_user: UserContext
    ) -> None:
        """Test that transition successfully changes workflow state."""
        from framework_m.core.interfaces.workflow import TransitionRequest

        # Start workflow
        await workflow_adapter.start_workflow(
            doctype="PurchaseOrder",
            doc_id="PO-101",
            workflow_name="purchase_approval",
            user=admin_user,
        )

        # Transition to next state
        request = TransitionRequest(
            doctype="PurchaseOrder",
            doc_id="PO-101",
            action="submit",
            user=admin_user,
        )

        result = await workflow_adapter.transition(request)

        assert result.success is True
        assert result.old_state == "Draft"
        assert result.new_state == "Pending Approval"

        # Verify state was updated
        state = await workflow_adapter.get_workflow_state(
            doctype="PurchaseOrder", doc_id="PO-101"
        )
        assert state is not None
        assert state.current_state == "Pending Approval"

    async def test_available_actions_change_with_state(
        self, workflow_adapter: WorkflowProtocol, admin_user: UserContext
    ) -> None:
        """Test that available actions depend on current state."""
        from framework_m.core.interfaces.workflow import TransitionRequest

        # Start workflow (Draft state)
        await workflow_adapter.start_workflow(
            doctype="PurchaseOrder",
            doc_id="PO-102",
            workflow_name="purchase_approval",
            user=admin_user,
        )

        # Get actions in Draft state
        draft_actions = await workflow_adapter.get_available_actions(
            doctype="PurchaseOrder", doc_id="PO-102", user=admin_user
        )

        assert "submit" in draft_actions

        # Transition to Pending Approval
        request = TransitionRequest(
            doctype="PurchaseOrder",
            doc_id="PO-102",
            action="submit",
            user=admin_user,
        )
        await workflow_adapter.transition(request)

        # Get actions in Pending Approval state
        pending_actions = await workflow_adapter.get_available_actions(
            doctype="PurchaseOrder", doc_id="PO-102", user=admin_user
        )

        # Actions should be different now
        assert "submit" not in pending_actions
        assert "approve" in pending_actions or "reject" in pending_actions


# ============================================================================
# Permission & Role Tests
# ============================================================================


class TestWorkflowPermissions:
    """Test workflow permission enforcement based on user roles."""

    async def test_transition_blocked_for_unauthorized_user(
        self,
        workflow_adapter: WorkflowProtocol,
        admin_user: UserContext,
        employee_user: UserContext,
    ) -> None:
        """Test that unauthorized users cannot perform transitions."""
        from framework_m.core.interfaces.workflow import TransitionRequest

        # Admin starts workflow
        await workflow_adapter.start_workflow(
            doctype="PurchaseOrder",
            doc_id="PO-200",
            workflow_name="purchase_approval",
            user=admin_user,
        )

        # Transition to Pending Approval (requires Manager role)
        request = TransitionRequest(
            doctype="PurchaseOrder",
            doc_id="PO-200",
            action="submit",
            user=admin_user,
        )
        await workflow_adapter.transition(request)

        # Employee tries to approve (should fail - requires Manager role)
        approve_request = TransitionRequest(
            doctype="PurchaseOrder",
            doc_id="PO-200",
            action="approve",
            user=employee_user,
        )

        result = await workflow_adapter.transition(approve_request)

        assert result.success is False
        assert (
            "permission" in result.message.lower() or "role" in result.message.lower()
        )

    async def test_available_actions_filtered_by_role(
        self,
        workflow_adapter: WorkflowProtocol,
        admin_user: UserContext,
        employee_user: UserContext,
    ) -> None:
        """Test that available actions are filtered by user role."""
        from framework_m.core.interfaces.workflow import TransitionRequest

        # Start and submit workflow
        await workflow_adapter.start_workflow(
            doctype="PurchaseOrder",
            doc_id="PO-201",
            workflow_name="purchase_approval",
            user=admin_user,
        )

        request = TransitionRequest(
            doctype="PurchaseOrder",
            doc_id="PO-201",
            action="submit",
            user=admin_user,
        )
        await workflow_adapter.transition(request)

        # Admin sees approve/reject actions
        admin_actions = await workflow_adapter.get_available_actions(
            doctype="PurchaseOrder", doc_id="PO-201", user=admin_user
        )

        # Employee sees no actions (requires Manager role)
        employee_actions = await workflow_adapter.get_available_actions(
            doctype="PurchaseOrder", doc_id="PO-201", user=employee_user
        )

        assert len(admin_actions) > 0
        assert len(employee_actions) == 0


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestWorkflowErrors:
    """Test error handling in workflow operations."""

    async def test_invalid_action_returns_failed_result(
        self, workflow_adapter: WorkflowProtocol, admin_user: UserContext
    ) -> None:
        """Test that invalid action returns failed transition result."""
        from framework_m.core.interfaces.workflow import TransitionRequest

        # Start workflow
        await workflow_adapter.start_workflow(
            doctype="PurchaseOrder",
            doc_id="PO-300",
            workflow_name="purchase_approval",
            user=admin_user,
        )

        # Try invalid action
        request = TransitionRequest(
            doctype="PurchaseOrder",
            doc_id="PO-300",
            action="invalid_action",
            user=admin_user,
        )

        result = await workflow_adapter.transition(request)

        assert result.success is False
        assert result.message is not None
        assert len(result.message) > 0

    async def test_transition_without_starting_workflow_fails(
        self, workflow_adapter: WorkflowProtocol, admin_user: UserContext
    ) -> None:
        """Test that transition fails if workflow not started."""
        from framework_m.core.interfaces.workflow import TransitionRequest

        request = TransitionRequest(
            doctype="PurchaseOrder",
            doc_id="PO-NOSTART",
            action="submit",
            user=admin_user,
        )

        result = await workflow_adapter.transition(request)

        assert result.success is False
        assert (
            "not found" in result.message.lower()
            or "no workflow" in result.message.lower()
        )


# ============================================================================
# Metadata Tests
# ============================================================================


class TestWorkflowMetadata:
    """Test workflow metadata tracking."""

    async def test_state_info_includes_timestamps(
        self, workflow_adapter: WorkflowProtocol, admin_user: UserContext
    ) -> None:
        """Test that state info includes timestamp metadata."""
        result = await workflow_adapter.start_workflow(
            doctype="PurchaseOrder",
            doc_id="PO-400",
            workflow_name="purchase_approval",
            user=admin_user,
        )

        assert hasattr(result, "updated_at")
        assert isinstance(result.updated_at, datetime)

    async def test_transition_result_includes_metadata(
        self, workflow_adapter: WorkflowProtocol, admin_user: UserContext
    ) -> None:
        """Test that transition result includes complete metadata."""
        from framework_m.core.interfaces.workflow import TransitionRequest

        await workflow_adapter.start_workflow(
            doctype="PurchaseOrder",
            doc_id="PO-401",
            workflow_name="purchase_approval",
            user=admin_user,
        )

        request = TransitionRequest(
            doctype="PurchaseOrder",
            doc_id="PO-401",
            action="submit",
            user=admin_user,
        )

        result = await workflow_adapter.transition(request)

        assert hasattr(result, "old_state")
        assert hasattr(result, "new_state")
        assert hasattr(result, "action")
        assert result.action == "submit"
