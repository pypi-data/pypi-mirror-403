"""Email Sender Adapters - Implementations of EmailSenderProtocol.

This module provides adapters for sending emails:
- SMTPEmailSender: Send via SMTP server
- LogEmailSender: Log to console (development/testing)

Example:
    # SMTP
    sender = SMTPEmailSender(
        host="smtp.gmail.com",
        port=587,
        username="user@gmail.com",
        password="app-password",
    )
    result = await sender.send(message)

    # Development
    sender = LogEmailSender()
    result = await sender.send(message)  # Logs instead of sending
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from uuid import uuid4

from framework_m.core.interfaces.email_sender import (
    EmailConnectionError,
    EmailMessage,
    SendResult,
)

logger = logging.getLogger(__name__)


# =============================================================================
# SMTP Email Sender
# =============================================================================


@dataclass
class SMTPConfig:
    """SMTP server configuration.

    Attributes:
        host: SMTP server hostname
        port: SMTP server port (587 for TLS, 465 for SSL)
        username: SMTP username (optional)
        password: SMTP password (optional)
        use_tls: Use STARTTLS (default True)
        use_ssl: Use SSL/TLS (for port 465)
        timeout: Connection timeout in seconds
        default_from: Default sender address
    """

    host: str
    port: int = 587
    username: str | None = None
    password: str | None = None
    use_tls: bool = True
    use_ssl: bool = False
    timeout: int = 30
    default_from: str | None = None


class SMTPEmailSender:
    """SMTP email sender adapter.

    Sends emails via SMTP server.

    Example:
        sender = SMTPEmailSender(SMTPConfig(
            host="smtp.gmail.com",
            port=587,
            username="user@gmail.com",
            password="app-password",
        ))
        result = await sender.send(message)
    """

    def __init__(self, config: SMTPConfig) -> None:
        """Initialize with SMTP configuration.

        Args:
            config: SMTP server configuration
        """
        self.config = config

    async def send(self, message: EmailMessage) -> SendResult:
        """Send an email via SMTP.

        Args:
            message: Email message to send

        Returns:
            SendResult with success status
        """
        import smtplib
        from email import encoders
        from email.mime.base import MIMEBase
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        try:
            # Build MIME message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = message.subject
            msg["From"] = message.from_address or self.config.default_from or ""
            msg["To"] = ", ".join(message.to)

            if message.cc:
                msg["Cc"] = ", ".join(message.cc)

            if message.reply_to:
                msg["Reply-To"] = message.reply_to

            # Add custom headers
            for key, value in message.headers.items():
                msg[key] = value

            # Add text body
            if message.text_body:
                msg.attach(MIMEText(message.text_body, "plain"))

            # Add HTML body
            msg.attach(MIMEText(message.html_body, "html"))

            # Add attachments
            if message.attachments:
                for filename, content, content_type in message.attachments:
                    part = MIMEBase(*content_type.split("/", 1))
                    part.set_payload(content)
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename={filename}",
                    )
                    msg.attach(part)

            # Build recipient list
            recipients = list(message.to)
            if message.cc:
                recipients.extend(message.cc)
            if message.bcc:
                recipients.extend(message.bcc)

            # Send via SMTP
            from_addr = msg["From"]
            msg_str = msg.as_string()

            if self.config.use_ssl:
                smtp_ssl = smtplib.SMTP_SSL(
                    self.config.host,
                    self.config.port,
                    timeout=self.config.timeout,
                )
                try:
                    if self.config.username and self.config.password:
                        smtp_ssl.login(self.config.username, self.config.password)
                    smtp_ssl.sendmail(from_addr, recipients, msg_str)
                finally:
                    smtp_ssl.quit()
            else:
                smtp_plain = smtplib.SMTP(
                    self.config.host,
                    self.config.port,
                    timeout=self.config.timeout,
                )
                try:
                    if self.config.use_tls:
                        smtp_plain.starttls()
                    if self.config.username and self.config.password:
                        smtp_plain.login(self.config.username, self.config.password)
                    smtp_plain.sendmail(from_addr, recipients, msg_str)
                finally:
                    smtp_plain.quit()

            message_id = msg.get("Message-ID") or str(uuid4())
            logger.info(
                "Email sent successfully",
                extra={"to": message.to, "subject": message.subject},
            )

            return SendResult(success=True, message_id=message_id)

        except smtplib.SMTPConnectError as e:
            logger.error("SMTP connection failed: %s", str(e))
            raise EmailConnectionError(f"Failed to connect: {e}") from e

        except smtplib.SMTPAuthenticationError as e:
            logger.error("SMTP authentication failed: %s", str(e))
            from framework_m.core.interfaces.email_sender import (
                EmailAuthenticationError,
            )

            raise EmailAuthenticationError(f"Authentication failed: {e}") from e

        except Exception as e:
            logger.error("Failed to send email: %s", str(e))
            return SendResult(success=False, error=str(e))

    async def is_available(self) -> bool:
        """Check if SMTP server is reachable."""
        import smtplib

        try:
            if self.config.use_ssl:
                smtp_ssl = smtplib.SMTP_SSL(
                    self.config.host,
                    self.config.port,
                    timeout=5,
                )
                smtp_ssl.quit()
            else:
                smtp_plain = smtplib.SMTP(
                    self.config.host,
                    self.config.port,
                    timeout=5,
                )
                smtp_plain.quit()
            return True
        except (smtplib.SMTPException, OSError):
            return False


# =============================================================================
# Log Email Sender (Development)
# =============================================================================


class LogEmailSender:
    """Log email sender for development/testing.

    Logs emails to console instead of sending.
    Useful for development and testing.

    Example:
        sender = LogEmailSender()
        result = await sender.send(message)
        # Logs: "EMAIL: To: user@example.com, Subject: Test"
    """

    def __init__(self, log_level: int = logging.INFO) -> None:
        """Initialize with log level.

        Args:
            log_level: Logging level for email output
        """
        self.log_level = log_level
        self.sent_emails: list[EmailMessage] = []

    async def send(self, message: EmailMessage) -> SendResult:
        """Log email instead of sending.

        Args:
            message: Email message to log

        Returns:
            SendResult (always success)
        """
        logger.log(
            self.log_level,
            "EMAIL: To: %s, Subject: %s",
            ", ".join(message.to),
            message.subject,
        )
        logger.debug("EMAIL BODY:\n%s", message.html_body)

        self.sent_emails.append(message)
        message_id = f"log-{uuid4()}"

        return SendResult(success=True, message_id=message_id)

    async def is_available(self) -> bool:
        """Log sender is always available."""
        return True

    def clear(self) -> None:
        """Clear sent emails (for testing)."""
        self.sent_emails.clear()


__all__ = [
    "LogEmailSender",
    "SMTPConfig",
    "SMTPEmailSender",
]
