"""Tests for InternalWorkflowAdapter.

Tests the database-backed workflow implementation with:
- Workflow state persistence
- Transition validation
- Permission checks
- Event emission
- Database operations
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

import pytest

if TYPE_CHECKING:
    from framework_m.adapters.workflow.internal_workflow import InternalWorkflowAdapter
    from framework_m.core.doctypes.workflow import Workflow
    from framework_m.core.doctypes.workflow_transition import WorkflowTransition
    from framework_m.core.interfaces.auth_context import UserContext
    from framework_m.core.interfaces.event_bus import EventBusProtocol
    from framework_m.core.interfaces.repository import RepositoryProtocol


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_repository() -> RepositoryProtocol:
    """Create a mock repository for testing."""
    return AsyncMock()


@pytest.fixture
def mock_event_bus() -> EventBusProtocol:
    """Create a mock event bus for testing."""
    return AsyncMock()


@pytest.fixture
def admin_user() -> UserContext:
    """Create an admin user context for testing."""
    from framework_m.core.interfaces.auth_context import UserContext

    return UserContext(
        id="admin-123",
        email="admin@example.com",
        roles=["Admin", "System Manager"],
        tenants=["default"],
        attributes={"roles": ["Admin", "System Manager"]},
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
def workflow_adapter(
    mock_repository: RepositoryProtocol, mock_event_bus: EventBusProtocol
) -> InternalWorkflowAdapter:
    """Create an internal workflow adapter for testing."""
    from framework_m.adapters.workflow.internal_workflow import InternalWorkflowAdapter

    return InternalWorkflowAdapter(
        repository=mock_repository,
        event_bus=mock_event_bus,
    )


@pytest.fixture
def sample_workflow() -> Workflow:
    """Create a sample workflow definition."""
    from framework_m.core.doctypes.workflow import Workflow

    return Workflow(
        name="purchase_approval",
        doctype="PurchaseOrder",
        initial_state="Draft",
        states=[
            {"name": "Draft"},
            {"name": "Pending Approval"},
            {"name": "Approved"},
            {"name": "Rejected"},
        ],
        is_active=True,
        owner="admin@example.com",
        modified_by="admin@example.com",
    )


@pytest.fixture
def sample_transitions() -> list[WorkflowTransition]:
    """Create sample workflow transitions."""
    from framework_m.core.doctypes.workflow_transition import WorkflowTransition

    return [
        WorkflowTransition(
            name="transition-1",
            workflow="purchase_approval",
            from_state="Draft",
            to_state="Pending Approval",
            action="submit",
            allowed_roles=["Employee", "Manager", "Admin"],
            owner="admin@example.com",
            modified_by="admin@example.com",
        ),
        WorkflowTransition(
            name="transition-2",
            workflow="purchase_approval",
            from_state="Pending Approval",
            to_state="Approved",
            action="approve",
            allowed_roles=["Manager", "Admin"],
            owner="admin@example.com",
            modified_by="admin@example.com",
        ),
        WorkflowTransition(
            name="transition-3",
            workflow="purchase_approval",
            from_state="Pending Approval",
            to_state="Rejected",
            action="reject",
            allowed_roles=["Manager", "Admin"],
            owner="admin@example.com",
            modified_by="admin@example.com",
        ),
    ]


# ============================================================================
# Start Workflow Tests
# ============================================================================


class TestStartWorkflow:
    """Test starting workflows on documents."""

    async def test_start_workflow_creates_initial_state(
        self,
        workflow_adapter: InternalWorkflowAdapter,
        mock_repository: RepositoryProtocol,
        mock_event_bus: EventBusProtocol,
        admin_user: UserContext,
        sample_workflow: Workflow,
    ) -> None:
        """Test that starting a workflow creates initial state."""
        from framework_m.core.doctypes.workflow_state import WorkflowState

        # Mock: No existing workflow state
        mock_repository.find.side_effect = [
            [],  # First call: check existing state (none found)
            [sample_workflow],  # Second call: load workflow definition
        ]

        # Mock: Insert returns the new state
        mock_repository.insert.return_value = WorkflowState(
            name="ws-001",
            workflow="purchase_approval",
            doctype="PurchaseOrder",
            document_name="PO-001",
            current_state="Draft",
            updated_at=datetime.now(UTC),
            owner=admin_user.id,
            modified_by=admin_user.id,
        )

        # Start workflow
        result = await workflow_adapter.start_workflow(
            doctype="PurchaseOrder",
            doc_id="PO-001",
            workflow_name="purchase_approval",
            user=admin_user,
        )

        # Verify state created
        assert result.workflow_name == "purchase_approval"
        assert result.doctype == "PurchaseOrder"
        assert result.document_id == "PO-001"
        assert result.current_state == "Draft"

        # Verify event emitted
        mock_event_bus.publish.assert_called_once()
        call_args = mock_event_bus.publish.call_args
        assert call_args[0][0] == "workflow.started"
        event = call_args[0][1]
        assert event.type == "workflow.started"
        assert event.data is not None
        assert event.data["workflow_name"] == "purchase_approval"

    async def test_start_workflow_idempotent_when_exists(
        self,
        workflow_adapter: InternalWorkflowAdapter,
        mock_repository: RepositoryProtocol,
        mock_event_bus: EventBusProtocol,
        admin_user: UserContext,
    ) -> None:
        """Test that starting workflow is idempotent if already started."""
        from framework_m.core.doctypes.workflow_state import WorkflowState

        # Mock: Existing workflow state found
        existing_state = WorkflowState(
            name="ws-001",
            workflow="purchase_approval",
            doctype="PurchaseOrder",
            document_name="PO-001",
            current_state="Pending Approval",
            updated_at=datetime.now(UTC),
            owner=admin_user.id,
            modified_by=admin_user.id,
        )
        mock_repository.find.return_value = [existing_state]

        # Start workflow (should return existing)
        result = await workflow_adapter.start_workflow(
            doctype="PurchaseOrder",
            doc_id="PO-001",
            workflow_name="purchase_approval",
            user=admin_user,
        )

        # Verify returned existing state
        assert result.current_state == "Pending Approval"

        # Verify no insert or event
        mock_repository.insert.assert_not_called()
        mock_event_bus.publish.assert_not_called()

    async def test_start_workflow_raises_for_invalid_workflow(
        self,
        workflow_adapter: InternalWorkflowAdapter,
        mock_repository: RepositoryProtocol,
        admin_user: UserContext,
    ) -> None:
        """Test that starting invalid workflow raises ValueError."""
        # Mock: No existing state, no workflow definition found
        mock_repository.find.side_effect = [
            [],  # No existing state
            [],  # No workflow definition
        ]

        # Should raise ValueError
        with pytest.raises(ValueError, match="No active workflow"):
            await workflow_adapter.start_workflow(
                doctype="PurchaseOrder",
                doc_id="PO-001",
                workflow_name="nonexistent_workflow",
                user=admin_user,
            )


# ============================================================================
# Get Workflow State Tests
# ============================================================================


class TestGetWorkflowState:
    """Test retrieving workflow states."""

    async def test_get_workflow_state_returns_current_state(
        self,
        workflow_adapter: InternalWorkflowAdapter,
        mock_repository: RepositoryProtocol,
    ) -> None:
        """Test getting workflow state for existing document."""
        from framework_m.core.doctypes.workflow_state import WorkflowState

        # Mock: State exists
        mock_repository.find.return_value = [
            WorkflowState(
                name="ws-001",
                workflow="purchase_approval",
                doctype="PurchaseOrder",
                document_name="PO-001",
                current_state="Pending Approval",
                updated_at=datetime.now(UTC),
                owner="admin@example.com",
                modified_by="admin@example.com",
            )
        ]

        result = await workflow_adapter.get_workflow_state(
            doctype="PurchaseOrder", doc_id="PO-001"
        )

        assert result is not None
        assert result.current_state == "Pending Approval"
        assert result.workflow_name == "purchase_approval"

    async def test_get_workflow_state_returns_none_when_not_found(
        self,
        workflow_adapter: InternalWorkflowAdapter,
        mock_repository: RepositoryProtocol,
    ) -> None:
        """Test getting state for document without workflow."""
        # Mock: No state found
        mock_repository.find.return_value = []

        result = await workflow_adapter.get_workflow_state(
            doctype="PurchaseOrder", doc_id="NONEXISTENT"
        )

        assert result is None


# ============================================================================
# Transition Tests
# ============================================================================


class TestTransition:
    """Test workflow state transitions."""

    async def test_transition_successful(
        self,
        workflow_adapter: InternalWorkflowAdapter,
        mock_repository: RepositoryProtocol,
        mock_event_bus: EventBusProtocol,
        admin_user: UserContext,
        sample_transitions: list[WorkflowTransition],
    ) -> None:
        """Test successful state transition."""
        from framework_m.core.doctypes.workflow_state import WorkflowState
        from framework_m.core.interfaces.workflow import TransitionRequest

        # Mock: Current state
        current_state = WorkflowState(
            name="ws-001",
            workflow="purchase_approval",
            doctype="PurchaseOrder",
            document_name="PO-001",
            current_state="Draft",
            updated_at=datetime.now(UTC),
            owner=admin_user.id,
            modified_by=admin_user.id,
        )

        mock_repository.find.side_effect = [
            [current_state],  # Find current state
            [sample_transitions[0]],  # Find transition
        ]

        # Perform transition
        request = TransitionRequest(
            doctype="PurchaseOrder",
            doc_id="PO-001",
            action="submit",
            user=admin_user,
        )

        result = await workflow_adapter.transition(request)

        # Verify success
        assert result.success is True
        assert result.old_state == "Draft"
        assert result.new_state == "Pending Approval"
        assert result.action == "submit"

        # Verify state updated
        mock_repository.update.assert_called_once()

        # Verify event emitted
        mock_event_bus.publish.assert_called_once()
        call_args = mock_event_bus.publish.call_args
        assert call_args[0][0] == "workflow.transitioned"

    async def test_transition_fails_for_invalid_action(
        self,
        workflow_adapter: InternalWorkflowAdapter,
        mock_repository: RepositoryProtocol,
        admin_user: UserContext,
    ) -> None:
        """Test transition fails with invalid action."""
        from framework_m.core.doctypes.workflow_state import WorkflowState
        from framework_m.core.interfaces.workflow import TransitionRequest

        # Mock: Current state exists, but no matching transition
        mock_repository.find.side_effect = [
            [
                WorkflowState(
                    name="ws-001",
                    workflow="purchase_approval",
                    doctype="PurchaseOrder",
                    document_name="PO-001",
                    current_state="Draft",
                    updated_at=datetime.now(UTC),
                    owner=admin_user.id,
                    modified_by=admin_user.id,
                )
            ],
            [],  # No transition found
        ]

        request = TransitionRequest(
            doctype="PurchaseOrder",
            doc_id="PO-001",
            action="invalid_action",
            user=admin_user,
        )

        result = await workflow_adapter.transition(request)

        assert result.success is False
        assert "Invalid action" in result.message

    async def test_transition_blocked_for_unauthorized_user(
        self,
        workflow_adapter: InternalWorkflowAdapter,
        mock_repository: RepositoryProtocol,
        employee_user: UserContext,
        sample_transitions: list[WorkflowTransition],
    ) -> None:
        """Test transition blocked when user lacks required role."""
        from framework_m.core.doctypes.workflow_state import WorkflowState
        from framework_m.core.interfaces.workflow import TransitionRequest

        # Mock: State in Pending Approval, transition requires Manager/Admin
        mock_repository.find.side_effect = [
            [
                WorkflowState(
                    name="ws-001",
                    workflow="purchase_approval",
                    doctype="PurchaseOrder",
                    document_name="PO-001",
                    current_state="Pending Approval",
                    updated_at=datetime.now(UTC),
                    owner="admin@example.com",
                    modified_by="admin@example.com",
                )
            ],
            [sample_transitions[1]],  # approve transition (requires Manager/Admin)
        ]

        request = TransitionRequest(
            doctype="PurchaseOrder",
            doc_id="PO-001",
            action="approve",
            user=employee_user,  # Employee doesn't have Manager role
        )

        result = await workflow_adapter.transition(request)

        assert result.success is False
        assert "does not have required role" in result.message


# ============================================================================
# Get Available Actions Tests
# ============================================================================


class TestGetAvailableActions:
    """Test getting available actions for users."""

    async def test_get_available_actions_filtered_by_role(
        self,
        workflow_adapter: InternalWorkflowAdapter,
        mock_repository: RepositoryProtocol,
        admin_user: UserContext,
        employee_user: UserContext,
        sample_transitions: list[WorkflowTransition],
    ) -> None:
        """Test that available actions are filtered by user role."""
        from framework_m.core.doctypes.workflow_state import WorkflowState

        # Mock: State in Pending Approval
        current_state = WorkflowState(
            name="ws-001",
            workflow="purchase_approval",
            doctype="PurchaseOrder",
            document_name="PO-001",
            current_state="Pending Approval",
            updated_at=datetime.now(UTC),
            owner="admin@example.com",
            modified_by="admin@example.com",
        )

        mock_repository.find.side_effect = [
            [current_state],  # State lookup for admin
            [sample_transitions[1], sample_transitions[2]],  # Transitions from Pending
            [current_state],  # State lookup for employee
            [sample_transitions[1], sample_transitions[2]],  # Same transitions
        ]

        # Admin should see approve/reject
        admin_actions = await workflow_adapter.get_available_actions(
            doctype="PurchaseOrder", doc_id="PO-001", user=admin_user
        )

        assert "approve" in admin_actions
        assert "reject" in admin_actions

        # Employee should see no actions (requires Manager/Admin)
        employee_actions = await workflow_adapter.get_available_actions(
            doctype="PurchaseOrder", doc_id="PO-001", user=employee_user
        )

        assert len(employee_actions) == 0

    async def test_get_available_actions_returns_empty_for_no_workflow(
        self,
        workflow_adapter: InternalWorkflowAdapter,
        mock_repository: RepositoryProtocol,
        admin_user: UserContext,
    ) -> None:
        """Test getting actions for document without workflow."""
        # Mock: No workflow state
        mock_repository.find.return_value = []

        actions = await workflow_adapter.get_available_actions(
            doctype="PurchaseOrder", doc_id="NONEXISTENT", user=admin_user
        )

        assert actions == []
