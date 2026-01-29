"""EmailQueue DocType - Email queue for outbound emails.

This module defines the EmailQueue DocType for Framework M's email system.

The EmailQueue DocType stores outbound emails for asynchronous processing:
- Emails are queued for later sending
- Background job processes the queue
- Status tracking (Queued, Sent, Failed)
- Retry support for failures

Design Principles:
- Asynchronous: Emails queued, not sent inline (per anti-pattern #25)
- Auditable: All emails tracked with status and timestamps
- Retryable: Failed emails can be retried

Security:
- Only admins can view email queue
- System creates entries via send_email() helper

Example:
    email = EmailQueue(
        to=["user@example.com"],
        subject="Welcome!",
        body="<h1>Welcome to the platform</h1>",
    )
    # Background job will process and send
"""

from datetime import datetime
from typing import Any

from pydantic import Field

from framework_m.core.domain.base_doctype import BaseDocType


class EmailStatus:
    """Email queue status constants."""

    QUEUED = "Queued"
    SENDING = "Sending"
    SENT = "Sent"
    FAILED = "Failed"
    CANCELLED = "Cancelled"


class EmailPriority:
    """Email priority constants."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class EmailQueue(BaseDocType):
    """Email queue DocType.

    Stores outbound emails for asynchronous processing.

    Attributes:
        to: List of recipient email addresses
        cc: Carbon copy recipients
        bcc: Blind carbon copy recipients
        subject: Email subject line
        body: Email body (HTML)
        text_body: Plain text alternative
        status: Queue status (Queued, Sending, Sent, Failed)
        priority: Email priority (low, normal, high)
        error: Error message if failed
        retry_count: Number of retry attempts
        max_retries: Maximum retry attempts
        queued_at: When the email was queued
        sent_at: When the email was sent
        from_address: Sender email address
        reply_to: Reply-to address
        attachments: Attachment metadata
        reference_doctype: Related DocType (optional)
        reference_id: Related document ID (optional)

    Example:
        email = EmailQueue(
            to=["user@example.com"],
            subject="Invoice",
            body="<p>Your invoice is attached.</p>",
        )
    """

    # Required fields
    to: list[str] = Field(
        ...,
        description="Recipient email addresses",
        min_length=1,
    )

    subject: str = Field(
        ...,
        description="Email subject line",
        max_length=500,
    )

    body: str = Field(
        ...,
        description="Email body (HTML)",
    )

    # Optional recipients
    cc: list[str] | None = Field(
        default=None,
        description="Carbon copy recipients",
    )

    bcc: list[str] | None = Field(
        default=None,
        description="Blind carbon copy recipients",
    )

    # Optional text body
    text_body: str | None = Field(
        default=None,
        description="Plain text alternative",
    )

    # Status tracking
    status: str = Field(
        default=EmailStatus.QUEUED,
        description="Queue status (Queued, Sending, Sent, Failed)",
    )

    priority: str = Field(
        default=EmailPriority.NORMAL,
        description="Email priority (low, normal, high)",
    )

    error: str | None = Field(
        default=None,
        description="Error message if failed",
    )

    retry_count: int = Field(
        default=0,
        description="Number of retry attempts",
        ge=0,
    )

    max_retries: int = Field(
        default=3,
        description="Maximum retry attempts",
        ge=0,
        le=10,
    )

    # Timestamps
    queued_at: datetime = Field(
        default_factory=lambda: __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ),
        description="When the email was queued (UTC)",
    )

    sent_at: datetime | None = Field(
        default=None,
        description="When the email was sent (UTC)",
    )

    # Sender info
    from_address: str | None = Field(
        default=None,
        description="Sender email address (uses default if not specified)",
    )

    reply_to: str | None = Field(
        default=None,
        description="Reply-to address",
    )

    # Attachments (stored as metadata)
    attachments: list[dict[str, Any]] | None = Field(
        default=None,
        description="Attachment metadata (file_id, filename, content_type)",
    )

    # Reference to related document
    reference_doctype: str | None = Field(
        default=None,
        description="Related DocType (e.g., Invoice)",
    )

    reference_id: str | None = Field(
        default=None,
        description="Related document ID",
    )

    class Meta:
        """DocType metadata."""

        table_name = "email_queue"
        requires_auth = True
        apply_rls = False  # Only admins access

        # Permissions - system creates, admins manage
        permissions = {  # noqa: RUF012
            "read": ["System Manager"],
            "write": ["System Manager"],
            "create": ["System Manager"],  # System creates via helper
            "delete": ["System Manager"],
        }


__all__ = ["EmailPriority", "EmailQueue", "EmailStatus"]
