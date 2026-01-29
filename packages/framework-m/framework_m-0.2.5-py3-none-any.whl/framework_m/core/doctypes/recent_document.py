"""RecentDocument DocType - Track recently viewed documents.

Stores recently accessed documents for quick navigation in the Desk UI.
"""

from datetime import UTC, datetime

from pydantic import Field

from framework_m.core.domain.base_doctype import BaseDocType


class RecentDocument(BaseDocType):
    """RecentDocument DocType.

    Tracks recently viewed documents per user for quick navigation.

    Attributes:
        user_id: User who viewed the document
        doctype: DocType of the viewed document
        document_id: ID of the viewed document
        document_name: Display name of the document
        route: URL route to the document
        viewed_at: When the document was last viewed
    """

    user_id: str = Field(
        ...,
        description="User who viewed the document",
    )

    doctype: str = Field(
        ...,
        description="DocType of the viewed document",
    )

    document_id: str = Field(
        ...,
        description="ID of the viewed document",
    )

    document_name: str = Field(
        ...,
        description="Display name of the document",
    )

    route: str | None = Field(
        default=None,
        description="URL route to the document",
    )

    viewed_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the document was last viewed",
    )

    class Meta:
        """DocType metadata."""

        table_name = "recent_documents"
        requires_auth = True
        apply_rls = True
        rls_field = "user_id"
        api_resource = True  # Enable CRUD API
        show_in_desk = False  # Hide from Desk UI sidebar (internal system DocType)

        permissions = {  # noqa: RUF012
            "read": ["All"],
            "write": ["All"],
            "create": ["All"],
            "delete": ["All"],
        }


__all__ = ["RecentDocument"]
