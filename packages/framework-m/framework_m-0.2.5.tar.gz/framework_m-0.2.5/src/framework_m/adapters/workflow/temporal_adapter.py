"""Temporal Workflow Adapter - Temporal.io integration for workflows.

This adapter implements WorkflowProtocol using Temporal.io for durable
workflow execution. Temporal provides:
- Durable execution with automatic retries
- Distributed tracing and visibility
- Long-running workflows (days/months)
- Event sourcing and replay

Note: This is an optional adapter. Most use cases are covered by
InternalWorkflowAdapter. Use Temporal for:
- Complex multi-step workflows spanning services
- Workflows requiring external system integration
- Long-running business processes
- Advanced failure recovery scenarios
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from framework_m.core.interfaces.auth_context import UserContext
    from framework_m.core.interfaces.workflow import (
        TransitionRequest,
        TransitionResult,
        WorkflowStateInfo,
    )


class TemporalWorkflowAdapter:
    """Temporal.io implementation of WorkflowProtocol.

    Integrates with Temporal server for durable workflow execution.
    Workflows run as Temporal workflows with automatic retry and recovery.

    Architecture:
        - Maps Framework M workflow concepts to Temporal workflows
        - Uses Temporal signals for state transitions
        - Queries Temporal for current workflow state
        - Maintains compatibility with WorkflowProtocol interface

    Configuration:
        - temporal_host: Temporal server address (default: localhost:7233)
        - temporal_namespace: Namespace for workflows (default: default)
        - temporal_task_queue: Task queue name (default: framework-m-workflows)

    Example:
        adapter = TemporalWorkflowAdapter(
            host="temporal.example.com:7233",
            namespace="production",
            task_queue="workflows",
        )
        await adapter.connect()
        await adapter.start_workflow("PurchaseOrder", "PO-001", "approval")
    """

    def __init__(
        self,
        host: str = "localhost:7233",
        namespace: str = "default",
        task_queue: str = "framework-m-workflows",
    ) -> None:
        """Initialize the Temporal workflow adapter.

        Args:
            host: Temporal server address
            namespace: Temporal namespace
            task_queue: Task queue for workflow workers
        """
        self._host = host
        self._namespace = namespace
        self._task_queue = task_queue
        self._client: Any = None  # temporalio.client.Client when connected

    async def connect(self) -> None:
        """Connect to Temporal server.

        Establishes connection to Temporal and prepares for workflow operations.
        Must be called before using other methods.

        Raises:
            ConnectionError: If unable to connect to Temporal server
        """
        try:
            from temporalio.client import Client  # type: ignore[import-not-found]

            self._client = await Client.connect(
                self._host,
                namespace=self._namespace,
            )
        except ImportError as e:
            raise ImportError(
                "Temporal SDK not installed. Install with: pip install temporalio"
            ) from e
        except Exception as e:
            raise ConnectionError(
                f"Failed to connect to Temporal at {self._host}: {e}"
            ) from e

    async def disconnect(self) -> None:
        """Disconnect from Temporal server.

        Closes the connection and cleans up resources.
        """
        if self._client:
            # Temporal Python SDK doesn't require explicit disconnect
            # Connection is managed by the client lifecycle
            self._client = None

    def is_connected(self) -> bool:
        """Check if connected to Temporal.

        Returns:
            True if connected and ready for operations
        """
        return self._client is not None

    async def start_workflow(
        self,
        doctype: str,
        doc_id: str,
        workflow_name: str,
        user: UserContext,
    ) -> WorkflowStateInfo:
        """Start a Temporal workflow for a document.

        Creates and starts a Temporal workflow. The workflow ID is derived
        from doctype and doc_id for idempotency.

        Args:
            doctype: The DocType name
            doc_id: The document ID
            workflow_name: Name of the workflow to start
            user: User context starting the workflow

        Returns:
            WorkflowStateInfo with initial state

        Raises:
            ValueError: If workflow_name is invalid
            ConnectionError: If not connected to Temporal
        """
        from framework_m.core.interfaces.workflow import WorkflowStateInfo

        if not self.is_connected():
            raise ConnectionError("Not connected to Temporal. Call connect() first.")

        # Workflow ID must be unique and deterministic
        workflow_id = f"{doctype}:{doc_id}"

        try:
            # Start the workflow (idempotent - will return existing if already started)
            handle = await self._client.start_workflow(
                workflow_name,
                args=[doctype, doc_id, user.id],
                id=workflow_id,
                task_queue=self._task_queue,
            )

            # Query for current state
            current_state = await handle.query("get_current_state")

            return WorkflowStateInfo(
                doctype=doctype,
                document_id=doc_id,
                workflow_name=workflow_name,
                current_state=current_state,
                updated_by=user.id,
            )

        except Exception as e:
            raise ValueError(f"Failed to start workflow '{workflow_name}': {e}") from e

    async def get_workflow_state(
        self, doctype: str, doc_id: str
    ) -> WorkflowStateInfo | None:
        """Get current workflow state from Temporal.

        Queries the Temporal workflow for its current state.

        Args:
            doctype: The DocType name
            doc_id: The document ID

        Returns:
            Current workflow state info, or None if no workflow active
        """
        from framework_m.core.interfaces.workflow import WorkflowStateInfo

        if not self.is_connected():
            raise ConnectionError("Not connected to Temporal. Call connect() first.")

        workflow_id = f"{doctype}:{doc_id}"

        try:
            # Get workflow handle
            handle = self._client.get_workflow_handle(workflow_id)

            # Query for current state
            current_state = await handle.query("get_current_state")
            workflow_name = await handle.query("get_workflow_name")

            # Get workflow description for metadata
            description = await handle.describe()

            return WorkflowStateInfo(
                doctype=doctype,
                document_id=doc_id,
                workflow_name=workflow_name,
                current_state=current_state,
                updated_by=description.raw_description.get("started_by", "system"),
            )

        except Exception:
            # Workflow not found or not running
            return None

    async def transition(self, request: TransitionRequest) -> TransitionResult:
        """Signal a Temporal workflow to perform a state transition.

        Sends a signal to the workflow to trigger the transition.
        The workflow validates permissions and performs the transition.

        Args:
            request: Transition request with action and user context

        Returns:
            TransitionResult indicating success/failure and new state
        """
        from framework_m.core.interfaces.workflow import TransitionResult

        if not self.is_connected():
            raise ConnectionError("Not connected to Temporal. Call connect() first.")

        workflow_id = f"{request.doctype}:{request.doc_id}"

        try:
            # Get workflow handle
            handle = self._client.get_workflow_handle(workflow_id)

            # Get current state before transition
            old_state = await handle.query("get_current_state")

            # Send transition signal
            await handle.signal(
                "perform_transition",
                request.action,
                request.user.id,
                request.user.roles,
                request.comment,
            )

            # Wait briefly for state update (Temporal processes signals asynchronously)
            import asyncio

            await asyncio.sleep(0.1)

            # Query new state
            new_state = await handle.query("get_current_state")

            # Check if transition succeeded
            if new_state == old_state:
                return TransitionResult(
                    success=False,
                    old_state=old_state,
                    new_state=old_state,
                    action=request.action,
                    message="Transition failed - check workflow logs for details",
                )

            return TransitionResult(
                success=True,
                old_state=old_state,
                new_state=new_state,
                action=request.action,
                message=f"Transitioned from {old_state} to {new_state}",
            )

        except Exception as e:
            return TransitionResult(
                success=False,
                old_state="",
                new_state="",
                action=request.action,
                message=f"Transition failed: {e}",
            )

    async def get_available_actions(
        self, doctype: str, doc_id: str, user: UserContext
    ) -> list[str]:
        """Query Temporal workflow for available actions.

        Asks the workflow what actions are available for the user
        in the current state.

        Args:
            doctype: The DocType name
            doc_id: The document ID
            user: User context to check permissions for

        Returns:
            List of action names user can perform
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to Temporal. Call connect() first.")

        workflow_id = f"{doctype}:{doc_id}"

        try:
            # Get workflow handle
            handle = self._client.get_workflow_handle(workflow_id)

            # Query for available actions given user roles
            actions: list[str] = await handle.query("get_available_actions", user.roles)

            return actions

        except Exception:
            # Workflow not found or error
            return []
