"""Workflow Protocol for state machine management.

This module defines the protocol for workflow state management in Framework M.
Workflows enable documents to move through defined states with permission-based
transitions.

Example:
    Define a workflow in a DocType's Meta class:

    ```python
    class PurchaseOrder(BaseDocType):
        class Meta:
            workflow = {
                "name": "purchase_approval",
                "states": ["Draft", "Pending Approval", "Approved", "Rejected"],
                "transitions": [
                    {
                        "from": "Draft",
                        "to": "Pending Approval",
                        "action": "submit",
                        "allowed_roles": ["Employee"]
                    },
                    {
                        "from": "Pending Approval",
                        "to": "Approved",
                        "action": "approve",
                        "allowed_roles": ["Manager"]
                    }
                ]
            }
    ```

Architecture:
    - Core protocol (this file): Database-agnostic interface
    - Adapters: Implement workflow logic with specific backends
    - No database-specific code in protocol layer
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from pydantic import BaseModel, Field

from framework_m.core.interfaces.auth_context import UserContext

# ============================================================================
# Request/Result Models
# ============================================================================


class WorkflowStateInfo(BaseModel):
    """Information about a document's current workflow state.

    Attributes:
        doctype: The DocType name of the document
        document_id: The ID of the document in workflow
        workflow_name: Name of the active workflow
        current_state: Current state name
        updated_at: Timestamp of last state change
        updated_by: User ID who last updated the state
    """

    doctype: str = Field(..., description="DocType name")
    document_id: str = Field(..., description="Document ID")
    workflow_name: str = Field(..., description="Workflow name")
    current_state: str = Field(..., description="Current state name")
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Last update timestamp"
    )
    updated_by: str | None = Field(None, description="User ID of last updater")


class TransitionRequest(BaseModel):
    """Request to transition a document to a new workflow state.

    Attributes:
        doctype: The DocType name
        doc_id: The document ID
        action: The transition action name
        user: User context performing the transition
        comment: Optional comment for the transition
    """

    doctype: str = Field(..., description="DocType name")
    doc_id: str = Field(..., description="Document ID")
    action: str = Field(..., description="Transition action name")
    user: UserContext = Field(..., description="User performing transition")
    comment: str | None = Field(None, description="Optional transition comment")


class TransitionResult(BaseModel):
    """Result of a workflow transition attempt.

    Attributes:
        success: Whether the transition succeeded
        old_state: State before transition
        new_state: State after transition (same as old_state if failed)
        action: The action that was attempted
        message: Success/error message
        timestamp: When the transition was attempted
    """

    success: bool = Field(..., description="Whether transition succeeded")
    old_state: str = Field(..., description="Previous state")
    new_state: str = Field(..., description="New state")
    action: str = Field(..., description="Action attempted")
    message: str = Field(default="", description="Success/error message")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Transition timestamp"
    )


# ============================================================================
# Workflow Protocol
# ============================================================================


class WorkflowProtocol(Protocol):
    """Protocol for workflow state management.

    Implementations must handle:
    - Starting workflows on documents
    - Tracking current workflow state
    - Validating and executing state transitions
    - Checking available actions based on user permissions

    Thread Safety:
        Implementations must be thread-safe. Multiple concurrent transitions
        on the same document should be handled correctly (e.g., using locks
        or optimistic concurrency control).

    Database Compatibility:
        Implementations must work with both SQLite (testing) and PostgreSQL
        (production). Use SQLAlchemy's database-agnostic features.
    """

    async def start_workflow(
        self,
        doctype: str,
        doc_id: str,
        workflow_name: str,
        user: UserContext,
    ) -> WorkflowStateInfo:
        """Start a workflow on a document.

        Creates initial workflow state record. If workflow already exists,
        this operation is idempotent and returns current state.

        Args:
            doctype: The DocType name
            doc_id: The document ID
            workflow_name: Name of the workflow to start
            user: User context starting the workflow

        Returns:
            WorkflowStateInfo with initial state

        Raises:
            ValueError: If workflow_name is invalid for this doctype
        """
        ...

    async def get_workflow_state(
        self, doctype: str, doc_id: str
    ) -> WorkflowStateInfo | None:
        """Get current workflow state for a document.

        Args:
            doctype: The DocType name
            doc_id: The document ID

        Returns:
            Current workflow state info, or None if no workflow active
        """
        ...

    async def transition(self, request: TransitionRequest) -> TransitionResult:
        """Attempt to transition a document to a new workflow state.

        Validates:
        - Workflow exists for document
        - Transition action is valid from current state
        - User has required role for this transition
        - Any custom validation hooks pass

        Args:
            request: Transition request with action and user context

        Returns:
            TransitionResult indicating success/failure and new state
        """
        ...

    async def get_available_actions(
        self, doctype: str, doc_id: str, user: UserContext
    ) -> list[str]:
        """Get list of actions available to user in current state.

        Filters actions based on:
        - Current workflow state
        - User's roles
        - Any custom permission logic

        Args:
            doctype: The DocType name
            doc_id: The document ID
            user: User context to check permissions for

        Returns:
            List of action names user can perform
        """
        ...
