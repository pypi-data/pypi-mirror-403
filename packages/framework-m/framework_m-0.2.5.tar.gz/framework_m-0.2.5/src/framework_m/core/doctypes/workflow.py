"""Workflow DocType for defining workflow configurations.

This DocType stores the complete workflow definition including
states, transitions, and the target DocType.
"""

from __future__ import annotations

from framework_m import DocType, Field


class Workflow(DocType):
    """Defines a complete workflow configuration.

    Attributes:
        doctype: The target DocType this workflow applies to
        initial_state: The starting state for new documents
        states: List of state definitions with metadata
        is_active: Whether this workflow is currently active
    """

    doctype: str = Field(description="Target DocType for this workflow")
    initial_state: str = Field(description="Initial state for new documents")
    states: list[dict[str, str]] = Field(
        default_factory=list,
        description="State definitions with name and optional metadata",
    )
    is_active: bool = Field(default=True, description="Whether workflow is active")

    class Meta:
        """Metadata configuration for Workflow."""

        indexes = [  # noqa: RUF012
            ["doctype", "is_active"],  # For finding active workflow for a DocType
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
