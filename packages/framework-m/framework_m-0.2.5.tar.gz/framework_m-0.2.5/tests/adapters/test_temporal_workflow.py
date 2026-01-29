"""Tests for TemporalWorkflowAdapter.

Tests the Temporal.io integration with mocked Temporal client.
Since Temporal requires external infrastructure, these tests use mocks
to validate the adapter logic without requiring a Temporal server.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock

import pytest

if TYPE_CHECKING:
    from framework_m.adapters.workflow.temporal_adapter import TemporalWorkflowAdapter
    from framework_m.core.interfaces.auth_context import UserContext


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def admin_user() -> UserContext:
    """Create an admin user context for testing."""
    from framework_m.core.interfaces.auth_context import UserContext

    return UserContext(
        id="admin-123",
        email="admin@example.com",
        roles=["Admin", "Manager"],
        tenants=["default"],
        attributes={"roles": ["Admin", "Manager"]},
    )


@pytest.fixture
def temporal_adapter() -> TemporalWorkflowAdapter:
    """Create a Temporal workflow adapter for testing."""
    from framework_m.adapters.workflow.temporal_adapter import TemporalWorkflowAdapter

    return TemporalWorkflowAdapter(
        host="localhost:7233",
        namespace="test",
        task_queue="test-workflows",
    )


# ============================================================================
# Connection Tests
# ============================================================================


class TestTemporalConnection:
    """Test Temporal server connection management."""

    async def test_connect_raises_on_import_error(
        self, temporal_adapter: TemporalWorkflowAdapter
    ) -> None:
        """Test that missing Temporal SDK raises helpful error."""
        # This will naturally fail since temporalio isn't installed
        with pytest.raises(ImportError, match="Temporal SDK not installed"):
            await temporal_adapter.connect()

    async def test_disconnect(self, temporal_adapter: TemporalWorkflowAdapter) -> None:
        """Test disconnection from Temporal."""
        # Simulate connected state
        temporal_adapter._client = AsyncMock()
        assert temporal_adapter.is_connected()

        await temporal_adapter.disconnect()
        assert not temporal_adapter.is_connected()

    async def test_is_connected_false_initially(
        self, temporal_adapter: TemporalWorkflowAdapter
    ) -> None:
        """Test that adapter is not connected initially."""
        assert not temporal_adapter.is_connected()


# ============================================================================
# Start Workflow Tests
# ============================================================================


class TestStartWorkflow:
    """Test starting workflows in Temporal."""

    async def test_start_workflow_success(
        self, temporal_adapter: TemporalWorkflowAdapter, admin_user: UserContext
    ) -> None:
        """Test starting a workflow in Temporal."""
        mock_client = AsyncMock()
        mock_handle = AsyncMock()

        # Mock query - use a plain async function
        async def mock_query(name: str) -> str:
            return "Draft"

        mock_handle.query = mock_query
        mock_client.start_workflow = AsyncMock(return_value=mock_handle)

        # Set up connected state
        temporal_adapter._client = mock_client

        result = await temporal_adapter.start_workflow(
            doctype="PurchaseOrder",
            doc_id="PO-001",
            workflow_name="purchase_approval",
            user=admin_user,
        )

        assert result.doctype == "PurchaseOrder"
        assert result.document_id == "PO-001"
        assert result.workflow_name == "purchase_approval"
        assert result.current_state == "Draft"

        # Verify workflow started with correct ID
        mock_client.start_workflow.assert_called_once()
        call_kwargs = mock_client.start_workflow.call_args[1]
        assert call_kwargs["id"] == "PurchaseOrder:PO-001"

    async def test_start_workflow_raises_when_not_connected(
        self, temporal_adapter: TemporalWorkflowAdapter, admin_user: UserContext
    ) -> None:
        """Test that starting workflow fails if not connected."""
        with pytest.raises(ConnectionError, match="Not connected to Temporal"):
            await temporal_adapter.start_workflow(
                doctype="PurchaseOrder",
                doc_id="PO-001",
                workflow_name="purchase_approval",
                user=admin_user,
            )


# ============================================================================
# Get Workflow State Tests
# ============================================================================


class TestGetWorkflowState:
    """Test querying workflow state from Temporal."""

    async def test_get_workflow_state_success(
        self, temporal_adapter: TemporalWorkflowAdapter
    ) -> None:
        """Test getting workflow state from Temporal."""
        mock_client = AsyncMock()
        mock_handle = AsyncMock()

        # Mock query - use a plain async function that returns different values
        query_results = {
            "get_current_state": "In Progress",
            "get_workflow_name": "purchase_approval",
        }

        async def mock_query(name: str) -> str:
            return query_results.get(name, "")

        mock_handle.query = mock_query

        # Mock describe
        describe_result = type(
            "obj", (), {"raw_description": {"started_by": "admin-123"}}
        )()

        async def mock_describe() -> Any:
            return describe_result

        mock_handle.describe = mock_describe

        # get_workflow_handle is synchronous, not async!
        mock_client.get_workflow_handle = lambda workflow_id: mock_handle

        # Set up connected state
        temporal_adapter._client = mock_client

        result = await temporal_adapter.get_workflow_state(
            doctype="PurchaseOrder",
            doc_id="PO-001",
        )

        assert result is not None
        assert result.doctype == "PurchaseOrder"
        assert result.document_id == "PO-001"
        assert result.workflow_name == "purchase_approval"
        assert result.current_state == "In Progress"

    async def test_get_workflow_state_returns_none_when_not_found(
        self, temporal_adapter: TemporalWorkflowAdapter
    ) -> None:
        """Test getting workflow state when workflow doesn't exist."""
        mock_client = AsyncMock()

        # get_workflow_handle is synchronous
        def raise_error(workflow_id: str) -> None:
            raise Exception("Workflow not found")

        mock_client.get_workflow_handle = raise_error

        # Set up connected state
        temporal_adapter._client = mock_client

        result = await temporal_adapter.get_workflow_state(
            doctype="PurchaseOrder",
            doc_id="PO-999",
        )

        assert result is None


# ============================================================================
# Transition Tests
# ============================================================================


class TestTransition:
    """Test workflow state transitions in Temporal."""

    async def test_transition_success(
        self, temporal_adapter: TemporalWorkflowAdapter, admin_user: UserContext
    ) -> None:
        """Test transitioning workflow state in Temporal."""
        from framework_m.core.interfaces.workflow import TransitionRequest

        mock_client = AsyncMock()
        mock_handle = type("obj", (), {})()

        # Mock signal - use a plain async function
        async def mock_signal(*args: Any) -> None:
            pass

        mock_handle.signal = mock_signal

        # Mock query - returns old state first, then new state
        query_call_count = [0]

        async def mock_query(name: str) -> str:
            query_call_count[0] += 1
            if query_call_count[0] == 1:
                return "Draft"  # Old state
            return "Approved"  # New state after transition

        mock_handle.query = mock_query
        mock_client.get_workflow_handle = lambda workflow_id: mock_handle

        # Set up connected state
        temporal_adapter._client = mock_client

        request = TransitionRequest(
            doctype="PurchaseOrder",
            doc_id="PO-001",
            action="approve",
            user=admin_user,
        )

        result = await temporal_adapter.transition(request)

        assert result.success
        assert result.new_state == "Approved"
        assert result.action == "approve"

    async def test_transition_fails_when_state_unchanged(
        self, temporal_adapter: TemporalWorkflowAdapter, admin_user: UserContext
    ) -> None:
        """Test transition failure when state doesn't change."""
        from framework_m.core.interfaces.workflow import TransitionRequest

        mock_client = AsyncMock()
        mock_handle = AsyncMock()

        # Mock signal
        async def mock_signal(*args: Any) -> None:
            pass

        mock_handle.signal = mock_signal

        # State remains the same before and after signal
        async def mock_query(name: str) -> str:
            return "Draft"  # State unchanged

        mock_handle.query = mock_query
        mock_client.get_workflow_handle = lambda workflow_id: mock_handle

        # Set up connected state
        temporal_adapter._client = mock_client

        request = TransitionRequest(
            doctype="PurchaseOrder",
            doc_id="PO-001",
            action="invalid_action",
            user=admin_user,
        )

        result = await temporal_adapter.transition(request)

        assert not result.success
        assert result.message  # Should have error message


# ============================================================================
# Get Available Actions Tests
# ============================================================================


class TestGetAvailableActions:
    """Test getting available workflow actions from Temporal."""

    async def test_get_available_actions_success(
        self, temporal_adapter: TemporalWorkflowAdapter, admin_user: UserContext
    ) -> None:
        """Test getting available actions from Temporal workflow."""
        mock_client = AsyncMock()
        mock_handle = AsyncMock()

        # Mock query
        async def mock_query(name: str, *args: Any) -> list[str]:
            return ["approve", "reject", "send_back"]

        mock_handle.query = mock_query
        mock_client.get_workflow_handle = lambda workflow_id: mock_handle

        # Set up connected state
        temporal_adapter._client = mock_client

        actions = await temporal_adapter.get_available_actions(
            doctype="PurchaseOrder",
            doc_id="PO-001",
            user=admin_user,
        )

        assert len(actions) == 3
        assert "approve" in actions
        assert "reject" in actions
        assert "send_back" in actions

    async def test_get_available_actions_returns_empty_on_error(
        self, temporal_adapter: TemporalWorkflowAdapter, admin_user: UserContext
    ) -> None:
        """Test that errors return empty list of actions."""
        mock_client = AsyncMock()

        def raise_error(workflow_id: str) -> None:
            raise Exception("Workflow not found")

        mock_client.get_workflow_handle = raise_error

        # Set up connected state
        temporal_adapter._client = mock_client

        actions = await temporal_adapter.get_available_actions(
            doctype="PurchaseOrder",
            doc_id="PO-999",
            user=admin_user,
        )

        assert len(actions) == 0
