"""Workflow API Routes.

This module provides REST endpoints for workflow management:
- GET /api/workflow/{doctype}/{id}/state - Get current workflow state
- GET /api/workflow/{doctype}/{id}/actions - Get available actions
- POST /api/workflow/{doctype}/{id}/transition - Execute a transition

These endpoints enable the frontend to render workflow UI and execute
state transitions.
"""

from __future__ import annotations

from typing import Any

from litestar import Router, get, post
from litestar.connection import Request
from litestar.exceptions import NotFoundException
from pydantic import BaseModel, Field

# =============================================================================
# Request/Response DTOs
# =============================================================================


class TransitionRequestDTO(BaseModel):
    """Request body for workflow transition.

    Attributes:
        action: The transition action to execute
        comment: Optional comment for the transition
    """

    action: str = Field(..., description="Transition action name")
    comment: str | None = Field(None, description="Optional comment")


class WorkflowStateResponse(BaseModel):
    """Workflow state response.

    Attributes:
        doctype: DocType name
        document_id: Document ID
        workflow_name: Name of the active workflow
        current_state: Current state name
        updated_at: Last update timestamp
    """

    doctype: str
    document_id: str
    workflow_name: str
    current_state: str
    updated_at: str | None = None
    updated_by: str | None = None


class WorkflowActionsResponse(BaseModel):
    """Available workflow actions response.

    Attributes:
        doctype: DocType name
        document_id: Document ID
        current_state: Current workflow state
        actions: List of available action names
    """

    doctype: str
    document_id: str
    current_state: str
    actions: list[str]


class TransitionResponse(BaseModel):
    """Workflow transition result.

    Attributes:
        success: Whether transition succeeded
        old_state: State before transition
        new_state: State after transition
        action: Action that was executed
        message: Success/error message
    """

    success: bool
    old_state: str
    new_state: str
    action: str
    message: str = ""


# =============================================================================
# Route Handlers
# =============================================================================


@get("/{doctype:str}/{doc_id:str}/state")
async def get_workflow_state(
    doctype: str,
    doc_id: str,
    request: Request[Any, Any, Any],
) -> WorkflowStateResponse:
    """Get current workflow state for a document.

    Args:
        doctype: DocType name
        doc_id: Document ID
        request: HTTP request

    Returns:
        Current workflow state

    Raises:
        NotFoundException: If document has no active workflow
    """
    # Get workflow service from app state (when wired)
    workflow_service = getattr(request.app.state, "workflow_service", None)

    if workflow_service is None:
        # Dev mode: Return mock workflow state
        return WorkflowStateResponse(
            doctype=doctype,
            document_id=doc_id,
            workflow_name="default",
            current_state="Draft",
            updated_at=None,
            updated_by=None,
        )

    state = await workflow_service.get_workflow_state(doctype, doc_id)
    if state is None:
        raise NotFoundException(f"No workflow found for {doctype}/{doc_id}")

    return WorkflowStateResponse(
        doctype=state.doctype,
        document_id=state.document_id,
        workflow_name=state.workflow_name,
        current_state=state.current_state,
        updated_at=state.updated_at.isoformat() if state.updated_at else None,
        updated_by=state.updated_by,
    )


@get("/{doctype:str}/{doc_id:str}/actions")
async def get_available_actions(
    doctype: str,
    doc_id: str,
    request: Request[Any, Any, Any],
) -> WorkflowActionsResponse:
    """Get available workflow actions for current user.

    Args:
        doctype: DocType name
        doc_id: Document ID
        request: HTTP request

    Returns:
        List of available actions based on current state and user permissions
    """
    # Get workflow service and user from app state
    workflow_service = getattr(request.app.state, "workflow_service", None)
    user = getattr(request.state, "user", None)

    if workflow_service is None:
        # Dev mode: Return mock actions based on common workflow patterns
        return WorkflowActionsResponse(
            doctype=doctype,
            document_id=doc_id,
            current_state="Draft",
            actions=["Submit", "Cancel"],
        )

    # Get current state
    state = await workflow_service.get_workflow_state(doctype, doc_id)
    current_state = state.current_state if state else "Draft"

    # Get available actions
    if user is None:
        actions: list[str] = []
    else:
        actions = await workflow_service.get_available_actions(doctype, doc_id, user)

    return WorkflowActionsResponse(
        doctype=doctype,
        document_id=doc_id,
        current_state=current_state,
        actions=actions,
    )


@post("/{doctype:str}/{doc_id:str}/transition")
async def execute_transition(
    doctype: str,
    doc_id: str,
    data: TransitionRequestDTO,
    request: Request[Any, Any, Any],
) -> TransitionResponse:
    """Execute a workflow transition.

    Args:
        doctype: DocType name
        doc_id: Document ID
        data: Transition request with action and optional comment
        request: HTTP request

    Returns:
        Transition result indicating success/failure

    Raises:
        NotFoundException: If document has no active workflow
    """
    workflow_service = getattr(request.app.state, "workflow_service", None)
    user = getattr(request.state, "user", None)

    if workflow_service is None:
        # Dev mode: Simulate successful transition
        # Map common actions to state changes
        state_transitions = {
            "Submit": ("Draft", "Pending"),
            "Approve": ("Pending", "Approved"),
            "Reject": ("Pending", "Rejected"),
            "Cancel": ("Draft", "Cancelled"),
        }
        old_state, new_state = state_transitions.get(
            data.action, ("Draft", "Submitted")
        )
        return TransitionResponse(
            success=True,
            old_state=old_state,
            new_state=new_state,
            action=data.action,
            message=f"Transitioned from {old_state} to {new_state}",
        )

    if user is None:
        return TransitionResponse(
            success=False,
            old_state="Unknown",
            new_state="Unknown",
            action=data.action,
            message="Authentication required for workflow transitions",
        )

    # Import here to avoid circular imports
    from framework_m.core.interfaces.workflow import TransitionRequest

    transition_request = TransitionRequest(
        doctype=doctype,
        doc_id=doc_id,
        action=data.action,
        user=user,
        comment=data.comment,
    )

    result = await workflow_service.transition(transition_request)

    return TransitionResponse(
        success=result.success,
        old_state=result.old_state,
        new_state=result.new_state,
        action=result.action,
        message=result.message,
    )


# =============================================================================
# Router
# =============================================================================


workflow_router = Router(
    path="/api/v1/workflow",
    route_handlers=[get_workflow_state, get_available_actions, execute_transition],
    tags=["workflow"],
)


__all__ = [
    "TransitionRequestDTO",
    "TransitionResponse",
    "WorkflowActionsResponse",
    "WorkflowStateResponse",
    "execute_transition",
    "get_available_actions",
    "get_workflow_state",
    "workflow_router",
]
