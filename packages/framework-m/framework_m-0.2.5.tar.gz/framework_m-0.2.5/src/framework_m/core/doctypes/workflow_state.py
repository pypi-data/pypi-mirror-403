"""WorkflowState DocType for tracking document workflow states.

This DocType stores the current workflow state of documents.
Each document in a workflow has one WorkflowState record.
"""

from __future__ import annotations

from datetime import UTC, datetime

from framework_m import DocType, Field


class WorkflowState(DocType):
    """Tracks the current workflow state of a document.

    Attributes:
        workflow: Name of the workflow
        doctype: The DocType of the document in workflow
        document_name: The name/ID of the document
        current_state: Current state name in the workflow
        updated_at: When the state was last updated
    """

    workflow: str = Field(description="Workflow name")
    doctype: str = Field(description="Target DocType")
    document_name: str = Field(description="Document ID")
    current_state: str = Field(description="Current workflow state")
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Last state update timestamp",
    )

    class Meta:
        """Metadata configuration for WorkflowState."""

        indexes = [  # noqa: RUF012
            ["doctype", "document_name"],  # Composite index for lookups
            ["workflow", "current_state"],  # For workflow state queries
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
                "delete": False,
            },
        ]
