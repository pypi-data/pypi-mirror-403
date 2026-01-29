"""Email Queue Protocol - Port for email queuing.

This module defines the EmailQueueProtocol for queuing outbound emails.

The port-adapter pattern allows:
- Default: DatabaseEmailQueueAdapter (uses EmailQueue DocType)
- External: NotificationServiceAdapter (calls external notification service)

Design Principles:
- Asynchronous: Emails queued, not sent inline
- Swappable: Change adapter via DI container
- Reliable: Queue-based processing with retries

Example:
    # Default - uses database queue
    adapter = DatabaseEmailQueueAdapter(repository)
    await adapter.queue_email(request)

    # External notification service
    adapter = NotificationServiceAdapter(http_client, url)
    await adapter.queue_email(request)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

# =============================================================================
# Email Request Model
# =============================================================================


@dataclass
class EmailRequest:
    """Request to queue an email.

    This is the input model for the email queue protocol.
    Adapters translate this to their specific format.

    Attributes:
        to: Recipient email addresses
        subject: Email subject line
        body: Email body (HTML)
        cc: Carbon copy recipients
        bcc: Blind carbon copy recipients
        text_body: Plain text alternative
        from_address: Sender email (uses default if not specified)
        reply_to: Reply-to address
        attachments: List of (filename, content, content_type) tuples
        template: Optional template name for rendering
        context: Template context variables
        priority: Email priority (low, normal, high)
        reference_doctype: Related DocType (e.g., Invoice)
        reference_id: Related document ID
        metadata: Additional custom metadata
    """

    to: list[str]
    subject: str
    body: str
    cc: list[str] | None = None
    bcc: list[str] | None = None
    text_body: str | None = None
    from_address: str | None = None
    reply_to: str | None = None
    attachments: list[tuple[str, bytes, str]] | None = None
    template: str | None = None
    context: dict[str, Any] | None = None
    priority: str = "normal"
    reference_doctype: str | None = None
    reference_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EmailQueueResult:
    """Result of queuing an email.

    Attributes:
        queue_id: Unique identifier for the queued email
        status: Current status (Queued, Accepted, etc.)
        queued_at: When the email was queued
    """

    queue_id: str
    status: str
    queued_at: datetime


# =============================================================================
# Email Queue Protocol (Port)
# =============================================================================


class EmailQueueProtocol(Protocol):
    """Protocol for email queue operations.

    This is the PORT in the ports-and-adapters pattern.
    Implementations (adapters) handle the actual queuing mechanism.

    Adapters:
    - DatabaseEmailQueueAdapter: Stores in EmailQueue DocType
    - NotificationServiceAdapter: Calls external notification service
    - InMemoryEmailQueueAdapter: For testing

    Example:
        # Get adapter from DI container
        queue: EmailQueueProtocol = container.email_queue()

        # Queue an email
        result = await queue.queue_email(EmailRequest(
            to=["user@example.com"],
            subject="Welcome!",
            body="<h1>Hello</h1>",
        ))
    """

    async def queue_email(self, request: EmailRequest) -> EmailQueueResult:
        """Queue an email for sending.

        Args:
            request: Email request with recipients, subject, body, etc.

        Returns:
            EmailQueueResult with queue_id and status

        Raises:
            EmailQueueError: If queuing fails
        """
        ...

    async def get_status(self, queue_id: str) -> str | None:
        """Get the status of a queued email.

        Args:
            queue_id: The queue ID from EmailQueueResult

        Returns:
            Status string (Queued, Sending, Sent, Failed) or None if not found
        """
        ...

    async def cancel(self, queue_id: str) -> bool:
        """Cancel a queued email (if not yet sent).

        Args:
            queue_id: The queue ID from EmailQueueResult

        Returns:
            True if cancelled, False if already sent or not found
        """
        ...


# =============================================================================
# Exceptions
# =============================================================================


class EmailQueueError(Exception):
    """Base exception for email queue errors."""

    pass


class EmailValidationError(EmailQueueError):
    """Email validation failed (invalid recipients, etc.)."""

    pass


class EmailQueueUnavailableError(EmailQueueError):
    """Email queue service is unavailable."""

    pass


__all__ = [
    "EmailQueueError",
    "EmailQueueProtocol",
    "EmailQueueResult",
    "EmailQueueUnavailableError",
    "EmailRequest",
    "EmailValidationError",
]
