"""Email Queue Adapters - Implementations of EmailQueueProtocol.

This module provides adapters for the EmailQueueProtocol:
- DatabaseEmailQueueAdapter: Uses EmailQueue DocType (default)
- InMemoryEmailQueueAdapter: For testing

Future adapters (not implemented here):
- NotificationServiceAdapter: Calls external notification service

Example:
    # Default - uses database
    adapter = DatabaseEmailQueueAdapter()
    result = await adapter.queue_email(request)

    # Testing
    adapter = InMemoryEmailQueueAdapter()
    result = await adapter.queue_email(request)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from framework_m.core.doctypes.email_queue import (
    EmailQueue,
    EmailStatus,
)
from framework_m.core.interfaces.email_queue import (
    EmailQueueResult,
    EmailRequest,
    EmailValidationError,
)

# =============================================================================
# Database Email Queue Adapter (Default)
# =============================================================================


class DatabaseEmailQueueAdapter:
    """Email queue adapter using the EmailQueue DocType.

    This is the default adapter that stores emails in the database.
    A background job processes the queue and sends emails.

    Attributes:
        repository: Repository for EmailQueue DocType (optional, uses in-memory if None)

    Example:
        adapter = DatabaseEmailQueueAdapter()
        result = await adapter.queue_email(EmailRequest(
            to=["user@example.com"],
            subject="Welcome",
            body="<h1>Hello</h1>",
        ))
    """

    def __init__(self, repository: Any | None = None) -> None:
        """Initialize the adapter.

        Args:
            repository: Optional repository for EmailQueue DocType
        """
        self._repository = repository
        # In-memory fallback for when repository is not provided
        self._in_memory_queue: dict[str, EmailQueue] = {}

    async def queue_email(self, request: EmailRequest) -> EmailQueueResult:
        """Queue an email for sending.

        Creates an EmailQueue entry in the database.

        Args:
            request: Email request

        Returns:
            EmailQueueResult with queue_id

        Raises:
            EmailValidationError: If request is invalid
        """
        # Validate
        if not request.to:
            raise EmailValidationError("At least one recipient is required")

        # Create EmailQueue entry
        email = EmailQueue(
            to=request.to,
            subject=request.subject,
            body=request.body,
            cc=request.cc,
            bcc=request.bcc,
            text_body=request.text_body,
            from_address=request.from_address,
            reply_to=request.reply_to,
            priority=request.priority,
            reference_doctype=request.reference_doctype,
            reference_id=request.reference_id,
            status=EmailStatus.QUEUED,
            attachments=self._convert_attachments(request.attachments),
        )

        # Save to repository or in-memory
        if self._repository:
            saved = await self._repository.save(email)
            queue_id = str(saved.id)
        else:
            queue_id = str(email.id)
            self._in_memory_queue[queue_id] = email

        return EmailQueueResult(
            queue_id=queue_id,
            status=EmailStatus.QUEUED,
            queued_at=email.queued_at,
        )

    async def get_status(self, queue_id: str) -> str | None:
        """Get the status of a queued email."""
        if self._repository:
            from uuid import UUID

            try:
                email = await self._repository.get(UUID(queue_id))
                return email.status if email else None
            except ValueError:
                return None
        else:
            email = self._in_memory_queue.get(queue_id)
            return email.status if email else None

    async def cancel(self, queue_id: str) -> bool:
        """Cancel a queued email."""
        if self._repository:
            from uuid import UUID

            try:
                email = await self._repository.get(UUID(queue_id))
                if email and email.status == EmailStatus.QUEUED:
                    email.status = EmailStatus.CANCELLED
                    await self._repository.save(email)
                    return True
                return False
            except ValueError:
                return False
        else:
            email = self._in_memory_queue.get(queue_id)
            return email is not None and email.status == EmailStatus.QUEUED

    def _convert_attachments(
        self,
        attachments: list[tuple[str, bytes, str]] | None,
    ) -> list[dict[str, Any]] | None:
        """Convert attachment tuples to metadata format."""
        if not attachments:
            return None

        return [
            {
                "filename": filename,
                "content_type": content_type,
                "size": len(content),
            }
            for filename, content, content_type in attachments
        ]


# =============================================================================
# In-Memory Email Queue Adapter (Testing)
# =============================================================================


class InMemoryEmailQueueAdapter:
    """In-memory email queue adapter for testing.

    Stores emails in memory. Useful for unit tests.

    Example:
        adapter = InMemoryEmailQueueAdapter()
        result = await adapter.queue_email(request)

        # Check queued emails
        assert len(adapter.queued_emails) == 1
    """

    def __init__(self) -> None:
        """Initialize with empty queue."""
        self.queued_emails: list[tuple[str, EmailRequest]] = []
        self._statuses: dict[str, str] = {}

    async def queue_email(self, request: EmailRequest) -> EmailQueueResult:
        """Queue an email in memory."""
        if not request.to:
            raise EmailValidationError("At least one recipient is required")

        queue_id = str(uuid4())
        self.queued_emails.append((queue_id, request))
        self._statuses[queue_id] = EmailStatus.QUEUED

        return EmailQueueResult(
            queue_id=queue_id,
            status=EmailStatus.QUEUED,
            queued_at=datetime.now(UTC),
        )

    async def get_status(self, queue_id: str) -> str | None:
        """Get status of queued email."""
        return self._statuses.get(queue_id)

    async def cancel(self, queue_id: str) -> bool:
        """Cancel a queued email."""
        if (
            queue_id in self._statuses
            and self._statuses[queue_id] == EmailStatus.QUEUED
        ):
            self._statuses[queue_id] = EmailStatus.CANCELLED
            return True
        return False

    def clear(self) -> None:
        """Clear all queued emails."""
        self.queued_emails.clear()
        self._statuses.clear()


__all__ = [
    "DatabaseEmailQueueAdapter",
    "InMemoryEmailQueueAdapter",
]
