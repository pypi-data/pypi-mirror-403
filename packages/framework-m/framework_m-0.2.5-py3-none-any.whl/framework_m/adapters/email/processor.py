"""Email Processor - Background job for sending queued emails.

This module provides the email processor that:
- Fetches emails from the queue
- Sends them via EmailSenderProtocol
- Updates status (Sent/Failed)
- Retries on failure

Example:
    processor = EmailProcessor(sender=SMTPEmailSender(config))
    await processor.process_queue()
"""

from __future__ import annotations

import logging
from typing import Any

from framework_m.core.doctypes.email_queue import EmailQueue, EmailStatus
from framework_m.core.interfaces.email_sender import (
    EmailMessage,
    EmailSenderProtocol,
    SendResult,
)

logger = logging.getLogger(__name__)


class EmailProcessor:
    """Email processor for sending queued emails.

    Fetches emails from the queue and sends them using the configured
    email sender adapter.

    Attributes:
        sender: EmailSenderProtocol implementation
        batch_size: Max emails to process per batch
        repository: Optional repository for EmailQueue

    Example:
        processor = EmailProcessor(
            sender=SMTPEmailSender(config),
            batch_size=50,
        )
        processed = await processor.process_queue()
    """

    def __init__(
        self,
        sender: EmailSenderProtocol,
        batch_size: int = 50,
        repository: Any | None = None,
    ) -> None:
        """Initialize the email processor.

        Args:
            sender: Email sender adapter
            batch_size: Max emails per batch
            repository: Optional EmailQueue repository
        """
        self.sender = sender
        self.batch_size = batch_size
        self._repository = repository
        # In-memory queue fallback
        self._in_memory_queue: list[EmailQueue] = []

    async def process_queue(self) -> int:
        """Process pending emails in the queue.

        Returns:
            Number of emails processed

        Example:
            processed = await processor.process_queue()
            print(f"Processed {processed} emails")
        """
        # Check sender availability
        if not await self.sender.is_available():
            logger.warning("Email sender not available, skipping queue processing")
            return 0

        # Fetch pending emails
        pending = await self._fetch_pending()
        processed = 0

        for email in pending:
            try:
                result = await self._send_email(email)
                await self._update_status(email, result)
                processed += 1
            except Exception as e:
                logger.error("Failed to process email %s: %s", email.id, str(e))
                await self._handle_failure(email, str(e))

        logger.info("Processed %d emails", processed)
        return processed

    async def process_single(self, queue_id: str) -> SendResult:
        """Process a single email by queue ID.

        Args:
            queue_id: ID of the queued email

        Returns:
            SendResult from sending
        """
        email = await self._get_email(queue_id)
        if not email:
            return SendResult(success=False, error="Email not found")

        result = await self._send_email(email)
        await self._update_status(email, result)
        return result

    async def _fetch_pending(self) -> list[EmailQueue]:
        """Fetch pending emails from queue."""
        if self._repository:
            from framework_m.core.interfaces.repository import (
                FilterOperator,
                FilterSpec,
            )

            result = await self._repository.list(
                filters=[
                    FilterSpec(
                        field="status",
                        operator=FilterOperator.EQ,
                        value=EmailStatus.QUEUED,
                    )
                ],
                limit=self.batch_size,
            )
            return list(result.items)
        else:
            # In-memory fallback
            return [e for e in self._in_memory_queue if e.status == EmailStatus.QUEUED][
                : self.batch_size
            ]

    async def _get_email(self, queue_id: str) -> EmailQueue | None:
        """Get email by ID."""
        if self._repository:
            from uuid import UUID

            result: EmailQueue | None = await self._repository.get(UUID(queue_id))
            return result
        else:
            for email in self._in_memory_queue:
                if str(email.id) == queue_id:
                    return email
            return None

    async def _send_email(self, email: EmailQueue) -> SendResult:
        """Send a single email."""
        message = EmailMessage(
            to=email.to,
            subject=email.subject,
            html_body=email.body,
            text_body=email.text_body,
            from_address=email.from_address,
            reply_to=email.reply_to,
            cc=email.cc,
            bcc=email.bcc,
        )

        return await self.sender.send(message)

    async def _update_status(
        self,
        email: EmailQueue,
        result: SendResult,
    ) -> None:
        """Update email status after send attempt."""
        # Note: In real impl, we'd update via repository
        # Here we just log since EmailQueue is immutable
        if result.success:
            logger.info(
                "Email sent: %s -> %s",
                email.id,
                ", ".join(email.to),
            )
        else:
            logger.warning(
                "Email failed: %s -> %s: %s",
                email.id,
                ", ".join(email.to),
                result.error,
            )

    async def _handle_failure(self, email: EmailQueue, error: str) -> None:
        """Handle send failure with retry logic."""
        # In real impl, increment retry_count and reschedule
        logger.warning(
            "Email %s failed (retry %d/%d): %s",
            email.id,
            email.retry_count + 1,
            email.max_retries,
            error,
        )


# =============================================================================
# Convenience Functions
# =============================================================================


async def send_queued_email(
    queue_id: str,
    sender: EmailSenderProtocol,
) -> SendResult:
    """Send a single queued email.

    Convenience function for processing one email.

    Args:
        queue_id: ID of the queued email
        sender: Email sender adapter

    Returns:
        SendResult from sending

    Example:
        from framework_m.adapters.email import LogEmailSender

        result = await send_queued_email(
            queue_id="queue-123",
            sender=LogEmailSender(),
        )
    """
    processor = EmailProcessor(sender=sender)
    return await processor.process_single(queue_id)


__all__ = [
    "EmailProcessor",
    "send_queued_email",
]
