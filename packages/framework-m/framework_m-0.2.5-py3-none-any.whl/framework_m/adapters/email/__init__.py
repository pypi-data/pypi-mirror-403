"""Email Adapters - Email queue, sender, and processor implementations.

This module provides complete email functionality:
- Queue: DatabaseEmailQueueAdapter, InMemoryEmailQueueAdapter
- Sender: SMTPEmailSender, LogEmailSender
- Processor: EmailProcessor for background job

Example:
    from framework_m.adapters.email import (
        queue_email,
        SMTPEmailSender,
        EmailProcessor,
    )

    # Queue an email
    result = await queue_email(
        to="user@example.com",
        subject="Welcome!",
        body="<h1>Hello</h1>",
    )

    # Process queue (background job)
    sender = SMTPEmailSender(SMTPConfig(host="smtp.example.com"))
    processor = EmailProcessor(sender=sender)
    await processor.process_queue()
"""

from typing import Any

from framework_m.adapters.email.processor import (
    EmailProcessor,
    send_queued_email,
)
from framework_m.adapters.email.queue_adapter import (
    DatabaseEmailQueueAdapter,
    InMemoryEmailQueueAdapter,
)
from framework_m.adapters.email.sender_adapter import (
    LogEmailSender,
    SMTPConfig,
    SMTPEmailSender,
)
from framework_m.core.interfaces.email_queue import (
    EmailQueueError,
    EmailQueueProtocol,
    EmailQueueResult,
    EmailRequest,
    EmailValidationError,
)
from framework_m.core.interfaces.email_sender import (
    EmailAuthenticationError,
    EmailConnectionError,
    EmailMessage,
    EmailSenderProtocol,
    EmailSendError,
    SendResult,
)

# Module-level adapter for the helper function
_email_queue_adapter: EmailQueueProtocol | None = None


def configure_email_queue(adapter: EmailQueueProtocol) -> None:
    """Configure the email queue adapter."""
    global _email_queue_adapter
    _email_queue_adapter = adapter


def get_email_queue_adapter() -> EmailQueueProtocol:
    """Get the configured email queue adapter."""
    global _email_queue_adapter
    if _email_queue_adapter is None:
        _email_queue_adapter = DatabaseEmailQueueAdapter()
    return _email_queue_adapter


async def queue_email(
    to: list[str] | str,
    subject: str,
    body: str,
    *,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    from_address: str | None = None,
    reply_to: str | None = None,
    template: str | None = None,
    context: dict[str, Any] | None = None,
    priority: str = "normal",
    reference_doctype: str | None = None,
    reference_id: str | None = None,
) -> EmailQueueResult:
    """Queue an email for sending."""
    recipients = [to] if isinstance(to, str) else to

    request = EmailRequest(
        to=recipients,
        subject=subject,
        body=body,
        cc=cc,
        bcc=bcc,
        from_address=from_address,
        reply_to=reply_to,
        template=template,
        context=context,
        priority=priority,
        reference_doctype=reference_doctype,
        reference_id=reference_id,
    )

    adapter = get_email_queue_adapter()
    return await adapter.queue_email(request)


__all__ = [
    "DatabaseEmailQueueAdapter",
    "EmailAuthenticationError",
    "EmailConnectionError",
    "EmailMessage",
    "EmailProcessor",
    "EmailQueueError",
    "EmailQueueProtocol",
    "EmailQueueResult",
    "EmailRequest",
    "EmailSendError",
    "EmailSenderProtocol",
    "EmailValidationError",
    "InMemoryEmailQueueAdapter",
    "LogEmailSender",
    "SMTPConfig",
    "SMTPEmailSender",
    "SendResult",
    "configure_email_queue",
    "get_email_queue_adapter",
    "queue_email",
    "send_queued_email",
]
