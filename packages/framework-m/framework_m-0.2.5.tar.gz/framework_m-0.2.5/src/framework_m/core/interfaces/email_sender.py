"""Email Sender Protocol - Port for email delivery.

This module defines the EmailSenderProtocol for sending emails.

The port-adapter pattern allows:
- SMTPEmailSender: Send via SMTP
- LogEmailSender: Log to console (development)
- Future: SendGrid, SES, Mailgun adapters

Example:
    sender = SMTPEmailSender(host="smtp.example.com", port=587)
    await sender.send(email)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

# =============================================================================
# Email Message Model
# =============================================================================


@dataclass
class EmailMessage:
    """Email message for sending.

    Attributes:
        to: Recipient email addresses
        subject: Email subject line
        html_body: HTML body content
        text_body: Plain text alternative
        from_address: Sender email
        reply_to: Reply-to address
        cc: Carbon copy recipients
        bcc: Blind carbon copy recipients
        attachments: List of (filename, content, content_type)
        headers: Additional email headers
    """

    to: list[str]
    subject: str
    html_body: str
    text_body: str | None = None
    from_address: str | None = None
    reply_to: str | None = None
    cc: list[str] | None = None
    bcc: list[str] | None = None
    attachments: list[tuple[str, bytes, str]] | None = None
    headers: dict[str, str] = field(default_factory=dict)


@dataclass
class SendResult:
    """Result of sending an email.

    Attributes:
        success: Whether sending succeeded
        message_id: Email message ID (if available)
        error: Error message if failed
    """

    success: bool
    message_id: str | None = None
    error: str | None = None


# =============================================================================
# Email Sender Protocol (Port)
# =============================================================================


class EmailSenderProtocol(Protocol):
    """Protocol for email sending operations.

    This is the PORT for sending emails.
    Implementations (adapters) handle actual delivery.

    Adapters:
    - SMTPEmailSender: Send via SMTP server
    - LogEmailSender: Log to console (development)
    - ExternalServiceSender: Via notification service

    Example:
        sender: EmailSenderProtocol = container.email_sender()
        result = await sender.send(EmailMessage(...))
    """

    async def send(self, message: EmailMessage) -> SendResult:
        """Send an email message.

        Args:
            message: Email message to send

        Returns:
            SendResult with success status

        Raises:
            EmailSendError: If sending fails
        """
        ...

    async def is_available(self) -> bool:
        """Check if the sender is available.

        Returns:
            True if ready to send, False otherwise
        """
        ...


# =============================================================================
# Exceptions
# =============================================================================


class EmailSendError(Exception):
    """Base exception for email sending errors."""

    pass


class EmailConnectionError(EmailSendError):
    """Failed to connect to email server."""

    pass


class EmailAuthenticationError(EmailSendError):
    """Email server authentication failed."""

    pass


__all__ = [
    "EmailAuthenticationError",
    "EmailConnectionError",
    "EmailMessage",
    "EmailSendError",
    "EmailSenderProtocol",
    "SendResult",
]
