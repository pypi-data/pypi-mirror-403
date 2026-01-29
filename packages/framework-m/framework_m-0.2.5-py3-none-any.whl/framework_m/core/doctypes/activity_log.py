"""ActivityLog DocType - Audit trail for document operations.

This module defines the ActivityLog DocType for Framework M's audit system.

The ActivityLog DocType stores a complete audit trail of user actions:
- Who performed the action (user_id)
- What action was performed (create, read, update, delete)
- Which document was affected (doctype + document_id)
- What changes were made (for updates)
- Additional context (request_id, IP address, etc.)

This DocType is used by DatabaseAuditAdapter for Indie mode deployments
where audit logs are stored in the database for easy querying via UI.

Security:
- Read-only after creation (immutable audit trail)
- Only admins can view all logs
- Users can view their own activity

Example:
    log = ActivityLog(
        user_id="user-001",
        action="update",
        doctype="Invoice",
        document_id="INV-001",
        changes={"status": {"old": "draft", "new": "submitted"}},
    )
"""

from datetime import datetime
from typing import Any

from pydantic import Field

from framework_m.core.domain.base_doctype import BaseDocType


class ActivityLog(BaseDocType):
    """Activity log entry DocType.

    Stores an immutable audit record of a user action on a document.
    Once created, activity logs should never be modified or deleted.

    Attributes:
        user_id: ID of the user who performed the action
        action: Type of action ("create", "read", "update", "delete")
        doctype: Name of the affected DocType
        document_id: ID of the affected document
        timestamp: When the action occurred (auto-set)
        changes: Field changes for updates (old/new values)
        metadata: Additional context (request_id, ip, user_agent)

    Example:
        log = ActivityLog(
            user_id="user-001",
            action="create",
            doctype="Todo",
            document_id="TODO-001",
        )
    """

    # Required fields
    user_id: str = Field(
        ...,
        description="ID of the user who performed the action",
        min_length=1,
    )

    action: str = Field(
        ...,
        description="Type of action: create, read, update, delete",
        pattern=r"^(create|read|update|delete)$",
    )

    doctype: str = Field(
        ...,
        description="Name of the affected DocType",
        min_length=1,
    )

    document_id: str = Field(
        ...,
        description="ID of the affected document",
        min_length=1,
    )

    # Auto-generated timestamp
    timestamp: datetime = Field(
        default_factory=lambda: __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ),
        description="When the action occurred (UTC)",
    )

    # Optional fields
    changes: dict[str, Any] | None = Field(
        default=None,
        description="Field changes for updates: {field: {old: x, new: y}}",
    )

    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Additional context: request_id, ip, user_agent, etc.",
    )

    class Meta:
        """DocType metadata."""

        table_name = "activity_logs"
        requires_auth = True
        apply_rls = True
        rls_field = "user_id"

        # Permissions - read-only for users, full access for admins
        permissions = {  # noqa: RUF012
            "read": ["System Manager", "All"],
            "write": [],  # No updates allowed
            "create": ["System Manager"],  # Only system can create
            "delete": [],  # No deletions allowed
        }


__all__ = ["ActivityLog"]
