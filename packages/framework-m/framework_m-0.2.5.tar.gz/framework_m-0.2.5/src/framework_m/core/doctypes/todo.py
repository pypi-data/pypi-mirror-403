"""Todo DocType - Example for testing and demos.

This is a simple Todo DocType used for E2E tests and demonstrations.
"""

from typing import ClassVar

from pydantic import Field

from framework_m.core.domain.base_doctype import BaseDocType


class Todo(BaseDocType):
    """A simple todo item.

    Attributes:
        title: The title/name of the todo item
        description: Optional description of the todo
        completed: Whether the todo is completed
        priority: Priority level (Low, Medium, High)
    """

    title: str = Field(
        description="Title of the todo item",
        min_length=1,
        max_length=200,
    )
    description: str | None = Field(
        default=None,
        description="Optional description",
        max_length=1000,
    )
    completed: bool = Field(
        default=False,
        description="Whether the todo is completed",
    )
    priority: str = Field(
        default="Medium",
        description="Priority level",
        pattern=r"^(Low|Medium|High)$",
    )

    class Meta:
        """DocType metadata."""

        # Enable API access
        api_resource: ClassVar[bool] = True

        # Hide from Desk UI (test DocType only)
        show_in_desk: ClassVar[bool] = False

        # Naming rule
        naming_rule: ClassVar[str] = "autoincrement"

        # Display in list views
        title_field: ClassVar[str] = "title"


__all__ = ["Todo"]
