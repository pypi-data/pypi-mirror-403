"""WorkflowTransition DocType for defining workflow transitions.

This DocType stores the allowed transitions between workflow states,
including permission requirements and optional conditions.
"""

from __future__ import annotations

from framework_m import DocType, Field


class WorkflowTransition(DocType):
    """Defines an allowed transition in a workflow.

    Attributes:
        workflow: Name of the workflow this transition belongs to
        from_state: Source state name
        to_state: Destination state name
        action: Action name that triggers this transition
        allowed_roles: List of roles permitted to perform this transition
        condition: Optional Python expression to evaluate before allowing transition
    """

    workflow: str = Field(description="Workflow name")
    from_state: str = Field(description="Source state")
    to_state: str = Field(description="Destination state")
    action: str = Field(description="Transition action name")
    allowed_roles: list[str] = Field(
        default_factory=list, description="Roles allowed to perform this transition"
    )
    condition: str | None = Field(
        None, description="Optional Python expression for conditional transitions"
    )

    class Meta:
        """Metadata configuration for WorkflowTransition."""

        indexes = [  # noqa: RUF012
            ["workflow", "from_state"],  # For finding available transitions
            ["workflow", "action"],  # For action-based lookups
        ]
        permissions = [  # noqa: RUF012
            {
                "role": "System Manager",
                "select": True,
                "insert": True,
                "update": True,
                "delete": True,
            },
            {
                "role": "Workflow Manager",
                "select": True,
                "insert": True,
                "update": True,
                "delete": True,
            },
        ]
