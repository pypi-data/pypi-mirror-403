"""Integration tests for full workflow lifecycle.

Tests end-to-end workflow functionality including:
- Document creation and persistence
- Workflow state management
- State transitions with role-based permissions
- Workflow state persistence across save/load cycles
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar

import pytest
from pydantic import Field

from framework_m.core.domain.base_doctype import BaseDocType
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
# Test DocTypes
# ============================================================================


class PurchaseOrder(BaseDocType):
    """Purchase Order DocType for workflow testing."""

    __doctype_name__: ClassVar[str] = "PurchaseOrder"

    name: str = Field(description="Purchase order number")
    amount: float = Field(description="Order amount", ge=0)
    supplier: str = Field(description="Supplier name")
    description: str | None = Field(default=None, description="Order description")

    class Meta:
        """DocType metadata."""

        name_pattern: ClassVar[str] = "PO-.####"


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def admin_user() -> UserContext:
    """Create an admin user context."""
    return UserContext(
        id="admin-123",
        email="admin@example.com",
        roles=["Admin", "Manager"],
        tenants=["default"],
        attributes={"roles": ["Admin", "Manager"]},
    )


@pytest.fixture
def employee_user() -> UserContext:
    """Create an employee user context."""
    return UserContext(
        id="emp-456",
        email="employee@example.com",
        roles=["Employee"],
        tenants=["default"],
        attributes={"roles": ["Employee"]},
    )


@pytest.fixture
def workflow_adapter() -> WorkflowProtocol:
    """Create an in-memory workflow adapter."""
    return InMemoryWorkflowAdapter()


# ============================================================================
# Integration Tests
# ============================================================================


class TestWorkflowDocumentLifecycle:
    """Test complete workflow lifecycle with document persistence."""

    async def test_create_document_and_start_workflow(
        self,
        workflow_adapter: WorkflowProtocol,
        admin_user: UserContext,
    ) -> None:
        """Test creating a document and starting a workflow on it."""
        # Create a purchase order
        po = PurchaseOrder(
            name="PO-0001",
            amount=1000.00,
            supplier="Acme Corp",
            description="Office supplies",
        )

        # Start workflow
        state = await workflow_adapter.start_workflow(
            doctype="PurchaseOrder",
            doc_id=po.name,
            workflow_name="purchase_approval",
            user=admin_user,
        )

        assert state.current_state == "Draft"
        assert state.doctype == "PurchaseOrder"
        assert state.document_id == po.name

    async def test_workflow_state_persists_across_transitions(
        self,
        workflow_adapter: WorkflowProtocol,
        admin_user: UserContext,
    ) -> None:
        """Test that workflow state persists through multiple transitions."""
        po = PurchaseOrder(
            name="PO-0002",
            amount=5000.00,
            supplier="Tech Supplies Inc",
        )

        # Start workflow
        await workflow_adapter.start_workflow(
            doctype="PurchaseOrder",
            doc_id=po.name,
            workflow_name="purchase_approval",
            user=admin_user,
        )

        # Transition: Draft → Pending Approval
        submit_request = TransitionRequest(
            doctype="PurchaseOrder",
            doc_id=po.name,
            action="submit",
            user=admin_user,
        )
        submit_result = await workflow_adapter.transition(submit_request)

        assert submit_result.success is True
        assert submit_result.new_state == "Pending Approval"

        # Verify state persisted
        state = await workflow_adapter.get_workflow_state("PurchaseOrder", po.name)
        assert state is not None
        assert state.current_state == "Pending Approval"

        # Transition: Pending Approval → Approved
        approve_request = TransitionRequest(
            doctype="PurchaseOrder",
            doc_id=po.name,
            action="approve",
            user=admin_user,
        )
        approve_result = await workflow_adapter.transition(approve_request)

        assert approve_result.success is True
        assert approve_result.new_state == "Approved"

        # Verify final state
        final_state = await workflow_adapter.get_workflow_state(
            "PurchaseOrder", po.name
        )
        assert final_state is not None
        assert final_state.current_state == "Approved"

    async def test_workflow_with_role_based_permissions(
        self,
        workflow_adapter: WorkflowProtocol,
        admin_user: UserContext,
        employee_user: UserContext,
    ) -> None:
        """Test workflow transitions respect role-based permissions."""
        po = PurchaseOrder(
            name="PO-0003",
            amount=2500.00,
            supplier="Office Depot",
        )

        # Employee starts workflow
        await workflow_adapter.start_workflow(
            doctype="PurchaseOrder",
            doc_id=po.name,
            workflow_name="purchase_approval",
            user=employee_user,
        )

        # Employee can submit (Employee role allowed)
        submit_request = TransitionRequest(
            doctype="PurchaseOrder",
            doc_id=po.name,
            action="submit",
            user=employee_user,
        )
        submit_result = await workflow_adapter.transition(submit_request)

        assert submit_result.success is True

        # Employee CANNOT approve (requires Manager role)
        approve_request = TransitionRequest(
            doctype="PurchaseOrder",
            doc_id=po.name,
            action="approve",
            user=employee_user,
        )
        approve_result = await workflow_adapter.transition(approve_request)

        assert approve_result.success is False
        assert "role" in approve_result.message.lower()

        # Admin CAN approve (has Manager role)
        admin_approve_request = TransitionRequest(
            doctype="PurchaseOrder",
            doc_id=po.name,
            action="approve",
            user=admin_user,
        )
        admin_approve_result = await workflow_adapter.transition(admin_approve_request)

        assert admin_approve_result.success is True
        assert admin_approve_result.new_state == "Approved"

    async def test_available_actions_change_with_state_and_role(
        self,
        workflow_adapter: WorkflowProtocol,
        admin_user: UserContext,
        employee_user: UserContext,
    ) -> None:
        """Test that available actions depend on both state and user role."""
        po = PurchaseOrder(
            name="PO-0004",
            amount=1500.00,
            supplier="Staples",
        )

        # Start workflow
        await workflow_adapter.start_workflow(
            doctype="PurchaseOrder",
            doc_id=po.name,
            workflow_name="purchase_approval",
            user=admin_user,
        )

        # In Draft state, both can submit
        admin_draft_actions = await workflow_adapter.get_available_actions(
            "PurchaseOrder", po.name, admin_user
        )
        employee_draft_actions = await workflow_adapter.get_available_actions(
            "PurchaseOrder", po.name, employee_user
        )

        assert "submit" in admin_draft_actions
        assert "submit" in employee_draft_actions

        # Transition to Pending Approval
        submit_request = TransitionRequest(
            doctype="PurchaseOrder",
            doc_id=po.name,
            action="submit",
            user=admin_user,
        )
        await workflow_adapter.transition(submit_request)

        # In Pending Approval, only admin can approve/reject
        admin_pending_actions = await workflow_adapter.get_available_actions(
            "PurchaseOrder", po.name, admin_user
        )
        employee_pending_actions = await workflow_adapter.get_available_actions(
            "PurchaseOrder", po.name, employee_user
        )

        assert "approve" in admin_pending_actions or "reject" in admin_pending_actions
        assert len(employee_pending_actions) == 0  # Employee has no actions

    async def test_workflow_rejection_path(
        self,
        workflow_adapter: WorkflowProtocol,
        admin_user: UserContext,
    ) -> None:
        """Test workflow rejection path."""
        po = PurchaseOrder(
            name="PO-0005",
            amount=10000.00,
            supplier="Expensive Vendor",
        )

        # Start and submit
        await workflow_adapter.start_workflow(
            doctype="PurchaseOrder",
            doc_id=po.name,
            workflow_name="purchase_approval",
            user=admin_user,
        )

        submit_request = TransitionRequest(
            doctype="PurchaseOrder",
            doc_id=po.name,
            action="submit",
            user=admin_user,
        )
        await workflow_adapter.transition(submit_request)

        # Reject the order
        reject_request = TransitionRequest(
            doctype="PurchaseOrder",
            doc_id=po.name,
            action="reject",
            user=admin_user,
        )
        reject_result = await workflow_adapter.transition(reject_request)

        assert reject_result.success is True
        assert reject_result.new_state == "Rejected"

        # Verify final state
        state = await workflow_adapter.get_workflow_state("PurchaseOrder", po.name)
        assert state is not None
        assert state.current_state == "Rejected"

    async def test_workflow_metadata_tracking(
        self,
        workflow_adapter: WorkflowProtocol,
        admin_user: UserContext,
    ) -> None:
        """Test that workflow tracks metadata like timestamps and user."""
        po = PurchaseOrder(
            name="PO-0006",
            amount=750.00,
            supplier="Quick Supplies",
        )

        # Start workflow
        start_time = datetime.now(UTC)
        state = await workflow_adapter.start_workflow(
            doctype="PurchaseOrder",
            doc_id=po.name,
            workflow_name="purchase_approval",
            user=admin_user,
        )

        # Verify metadata
        assert state.updated_by == admin_user.id
        assert state.updated_at >= start_time
        assert state.updated_at <= datetime.now(UTC)

        # Transition and verify metadata updates
        submit_request = TransitionRequest(
            doctype="PurchaseOrder",
            doc_id=po.name,
            action="submit",
            user=admin_user,
        )
        await workflow_adapter.transition(submit_request)

        updated_state = await workflow_adapter.get_workflow_state(
            "PurchaseOrder", po.name
        )
        assert updated_state is not None
        assert updated_state.updated_at > state.updated_at
