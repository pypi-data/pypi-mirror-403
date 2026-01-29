"""Notification DocType - User notifications.

This module defines the Notification DocType for Framework M's notification system.

The Notification DocType stores in-app notifications for users:
- Subject and message content
- Read/unread status
- Optional link to related document
- Timestamp for ordering

Security:
- Users can only see their own notifications
- RLS applied on user_id field

Example:
    notification = Notification(
        user_id="user-001",
        subject="Invoice Approved",
        message="Invoice INV-001 has been approved.",
        doctype="Invoice",
        document_id="INV-001",
    )
"""

from datetime import datetime
from typing import Any

from pydantic import Field

from framework_m.core.domain.base_doctype import BaseDocType


class NotificationType:
    """Notification type constants."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    MENTION = "mention"
    ASSIGNMENT = "assignment"
    SHARE = "share"


class Notification(BaseDocType):
    """Notification DocType.

    Stores in-app notifications for users.

    Attributes:
        user_id: Recipient user ID
        subject: Notification subject/title
        message: Full notification message
        notification_type: Type of notification (info, success, etc.)
        read: Whether the notification has been read
        doctype: Related DocType (optional)
        document_id: Related document ID (optional)
        timestamp: When the notification was created
        from_user: User who triggered the notification (optional)
        metadata: Additional notification data

    Example:
        notification = Notification(
            user_id="user-001",
            subject="New Comment",
            message="John commented on your invoice.",
        )
    """

    # Required fields
    user_id: str = Field(
        ...,
        description="Recipient user ID",
    )

    subject: str = Field(
        ...,
        description="Notification subject/title",
        max_length=255,
    )

    message: str = Field(
        ...,
        description="Full notification message",
    )

    # Type and status
    notification_type: str = Field(
        default=NotificationType.INFO,
        description="Notification type (info, success, warning, error, etc.)",
    )

    read: bool = Field(
        default=False,
        description="Whether the notification has been read",
    )

    # Related document
    doctype: str | None = Field(
        default=None,
        description="Related DocType (e.g., Invoice)",
    )

    document_id: str | None = Field(
        default=None,
        description="Related document ID",
    )

    # Metadata
    timestamp: datetime = Field(
        default_factory=lambda: __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ),
        description="When the notification was created (UTC)",
    )

    from_user: str | None = Field(
        default=None,
        description="User who triggered the notification",
    )

    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Additional notification data",
    )

    class Meta:
        """DocType metadata."""

        table_name = "notifications"
        requires_auth = True
        apply_rls = True
        rls_field = "user_id"
        api_resource = True  # Enable CRUD API
        show_in_desk = False  # Hide from Desk UI sidebar (internal system DocType)

        # Permissions - users manage their own notifications
        permissions = {  # noqa: RUF012
            "read": ["All"],  # RLS limits to own
            "write": ["All"],  # For marking as read
            "create": ["System Manager"],  # Only system creates
            "delete": ["All"],  # Users can delete their own
        }


__all__ = ["Notification", "NotificationType"]
