"""Tests for Email Sender and Processor.

Tests cover:
- EmailSenderProtocol interface
- LogEmailSender adapter
- EmailProcessor
"""

import pytest

from framework_m.adapters.email.processor import EmailProcessor
from framework_m.adapters.email.sender_adapter import (
    LogEmailSender,
    SMTPConfig,
    SMTPEmailSender,
)
from framework_m.core.interfaces.email_sender import (
    EmailAuthenticationError,
    EmailConnectionError,
    EmailMessage,
    EmailSenderProtocol,
    EmailSendError,
    SendResult,
)

# =============================================================================
# Test: Imports
# =============================================================================


class TestEmailSenderImports:
    """Tests for email sender imports."""

    def test_import_protocol(self) -> None:
        """EmailSenderProtocol should be importable."""

        assert EmailSenderProtocol is not None

    def test_import_message(self) -> None:
        """EmailMessage should be importable."""
        from framework_m.core.interfaces.email_sender import EmailMessage

        assert EmailMessage is not None

    def test_import_result(self) -> None:
        """SendResult should be importable."""
        from framework_m.core.interfaces.email_sender import SendResult

        assert SendResult is not None

    def test_import_exceptions(self) -> None:
        """Exceptions should be importable."""
        from framework_m.core.interfaces.email_sender import (
            EmailAuthenticationError,
            EmailConnectionError,
            EmailSendError,
        )

        assert EmailSendError is not None
        assert EmailConnectionError is not None
        assert EmailAuthenticationError is not None


# =============================================================================
# Test: EmailMessage
# =============================================================================


class TestEmailMessage:
    """Tests for EmailMessage dataclass."""

    def test_create_minimal(self) -> None:
        """EmailMessage should work with required fields."""
        msg = EmailMessage(
            to=["user@example.com"],
            subject="Test",
            html_body="<p>Hello</p>",
        )

        assert msg.to == ["user@example.com"]
        assert msg.subject == "Test"
        assert msg.html_body == "<p>Hello</p>"

    def test_default_fields(self) -> None:
        """Optional fields should default to None."""
        msg = EmailMessage(
            to=["user@example.com"],
            subject="Test",
            html_body="<p>Hello</p>",
        )

        assert msg.text_body is None
        assert msg.from_address is None
        assert msg.cc is None
        assert msg.attachments is None

    def test_with_all_fields(self) -> None:
        """EmailMessage should accept all fields."""
        msg = EmailMessage(
            to=["user@example.com"],
            subject="Test",
            html_body="<p>Hello</p>",
            text_body="Hello",
            from_address="sender@example.com",
            reply_to="reply@example.com",
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
            attachments=[("file.pdf", b"content", "application/pdf")],
            headers={"X-Custom": "value"},
        )

        assert msg.from_address == "sender@example.com"
        assert len(msg.attachments) == 1
        assert msg.headers["X-Custom"] == "value"


# =============================================================================
# Test: SendResult
# =============================================================================


class TestSendResult:
    """Tests for SendResult dataclass."""

    def test_success_result(self) -> None:
        """SendResult should represent success."""
        result = SendResult(success=True, message_id="msg-123")

        assert result.success is True
        assert result.message_id == "msg-123"
        assert result.error is None

    def test_failure_result(self) -> None:
        """SendResult should represent failure."""
        result = SendResult(success=False, error="Connection failed")

        assert result.success is False
        assert result.error == "Connection failed"


# =============================================================================
# Test: LogEmailSender
# =============================================================================


class TestLogEmailSender:
    """Tests for LogEmailSender adapter."""

    def test_init(self) -> None:
        """LogEmailSender should initialize."""
        sender = LogEmailSender()
        assert sender.sent_emails == []

    @pytest.mark.asyncio
    async def test_send_logs_email(self) -> None:
        """send should store email and return success."""
        sender = LogEmailSender()
        msg = EmailMessage(
            to=["user@example.com"],
            subject="Test",
            html_body="<p>Hello</p>",
        )

        result = await sender.send(msg)

        assert result.success is True
        assert result.message_id is not None
        assert len(sender.sent_emails) == 1
        assert sender.sent_emails[0].subject == "Test"

    @pytest.mark.asyncio
    async def test_is_available_always_true(self) -> None:
        """LogEmailSender should always be available."""
        sender = LogEmailSender()
        available = await sender.is_available()
        assert available is True

    def test_clear(self) -> None:
        """clear should empty sent_emails."""
        sender = LogEmailSender()
        sender.sent_emails.append(
            EmailMessage(to=["test@example.com"], subject="T", html_body="B")
        )

        sender.clear()

        assert len(sender.sent_emails) == 0


# =============================================================================
# Test: SMTPConfig
# =============================================================================


class TestSMTPConfig:
    """Tests for SMTPConfig dataclass."""

    def test_minimal_config(self) -> None:
        """SMTPConfig should work with host only."""
        config = SMTPConfig(host="smtp.example.com")

        assert config.host == "smtp.example.com"
        assert config.port == 587
        assert config.use_tls is True

    def test_full_config(self) -> None:
        """SMTPConfig should accept all options."""
        config = SMTPConfig(
            host="smtp.gmail.com",
            port=465,
            username="user@gmail.com",
            password="secret",
            use_tls=False,
            use_ssl=True,
            timeout=60,
            default_from="noreply@example.com",
        )

        assert config.port == 465
        assert config.use_ssl is True
        assert config.default_from == "noreply@example.com"


# =============================================================================
# Test: SMTPEmailSender
# =============================================================================


class TestSMTPEmailSender:
    """Tests for SMTPEmailSender adapter."""

    def test_init(self) -> None:
        """SMTPEmailSender should initialize with config."""
        config = SMTPConfig(host="smtp.example.com")
        sender = SMTPEmailSender(config)

        assert sender.config.host == "smtp.example.com"

    @pytest.mark.asyncio
    async def test_is_available_no_server(self) -> None:
        """is_available should return False for unreachable server."""
        config = SMTPConfig(host="nonexistent.invalid", port=587)
        sender = SMTPEmailSender(config)

        available = await sender.is_available()

        assert available is False

    @pytest.mark.asyncio
    async def test_send_with_tls_success(self) -> None:
        """send should use STARTTLS when use_tls is True."""
        from unittest.mock import MagicMock, patch

        config = SMTPConfig(
            host="smtp.example.com",
            port=587,
            username="user@example.com",
            password="password",
            use_tls=True,
            use_ssl=False,
        )
        sender = SMTPEmailSender(config)

        mock_smtp = MagicMock()
        mock_smtp.starttls = MagicMock()
        mock_smtp.login = MagicMock()
        mock_smtp.sendmail = MagicMock()
        mock_smtp.quit = MagicMock()

        with patch("smtplib.SMTP", return_value=mock_smtp):
            msg = EmailMessage(
                to=["user@example.com"],
                subject="Test",
                html_body="<p>Hello</p>",
            )
            result = await sender.send(msg)

        assert result.success is True
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once()
        mock_smtp.sendmail.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_with_ssl_success(self) -> None:
        """send should use SSL when use_ssl is True."""
        from unittest.mock import MagicMock, patch

        config = SMTPConfig(
            host="smtp.example.com",
            port=465,
            username="user@example.com",
            password="password",
            use_tls=False,
            use_ssl=True,
        )
        sender = SMTPEmailSender(config)

        mock_smtp_ssl = MagicMock()
        mock_smtp_ssl.login = MagicMock()
        mock_smtp_ssl.sendmail = MagicMock()
        mock_smtp_ssl.quit = MagicMock()

        with patch("smtplib.SMTP_SSL", return_value=mock_smtp_ssl):
            msg = EmailMessage(
                to=["user@example.com"],
                subject="Test SSL",
                html_body="<p>Hello</p>",
            )
            result = await sender.send(msg)

        assert result.success is True
        mock_smtp_ssl.login.assert_called_once()
        mock_smtp_ssl.sendmail.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_with_cc_and_bcc(self) -> None:
        """send should include CC and BCC recipients."""
        from unittest.mock import MagicMock, patch

        config = SMTPConfig(host="smtp.example.com", use_tls=False, use_ssl=False)
        sender = SMTPEmailSender(config)

        mock_smtp = MagicMock()
        mock_smtp.sendmail = MagicMock()
        mock_smtp.quit = MagicMock()

        with patch("smtplib.SMTP", return_value=mock_smtp):
            msg = EmailMessage(
                to=["to@example.com"],
                subject="Test",
                html_body="<p>Hello</p>",
                cc=["cc@example.com"],
                bcc=["bcc@example.com"],
            )
            result = await sender.send(msg)

        assert result.success is True
        # Check that all recipients were included
        call_args = mock_smtp.sendmail.call_args
        recipients = call_args[0][1]
        assert "to@example.com" in recipients
        assert "cc@example.com" in recipients
        assert "bcc@example.com" in recipients

    @pytest.mark.asyncio
    async def test_send_with_attachments(self) -> None:
        """send should include attachments."""
        from unittest.mock import MagicMock, patch

        config = SMTPConfig(host="smtp.example.com", use_tls=False, use_ssl=False)
        sender = SMTPEmailSender(config)

        mock_smtp = MagicMock()
        mock_smtp.sendmail = MagicMock()
        mock_smtp.quit = MagicMock()

        with patch("smtplib.SMTP", return_value=mock_smtp):
            msg = EmailMessage(
                to=["user@example.com"],
                subject="Test",
                html_body="<p>Hello</p>",
                attachments=[("file.pdf", b"PDF content", "application/pdf")],
            )
            result = await sender.send(msg)

        assert result.success is True

    @pytest.mark.asyncio
    async def test_send_with_text_body(self) -> None:
        """send should include text body."""
        from unittest.mock import MagicMock, patch

        config = SMTPConfig(host="smtp.example.com", use_tls=False, use_ssl=False)
        sender = SMTPEmailSender(config)

        mock_smtp = MagicMock()
        mock_smtp.sendmail = MagicMock()
        mock_smtp.quit = MagicMock()

        with patch("smtplib.SMTP", return_value=mock_smtp):
            msg = EmailMessage(
                to=["user@example.com"],
                subject="Test",
                html_body="<p>Hello</p>",
                text_body="Hello plain text",
            )
            result = await sender.send(msg)

        assert result.success is True

    @pytest.mark.asyncio
    async def test_send_with_reply_to(self) -> None:
        """send should include Reply-To header."""
        from unittest.mock import MagicMock, patch

        config = SMTPConfig(host="smtp.example.com", use_tls=False, use_ssl=False)
        sender = SMTPEmailSender(config)

        mock_smtp = MagicMock()
        mock_smtp.sendmail = MagicMock()
        mock_smtp.quit = MagicMock()

        with patch("smtplib.SMTP", return_value=mock_smtp):
            msg = EmailMessage(
                to=["user@example.com"],
                subject="Test",
                html_body="<p>Hello</p>",
                reply_to="reply@example.com",
            )
            result = await sender.send(msg)

        assert result.success is True

    @pytest.mark.asyncio
    async def test_send_with_custom_headers(self) -> None:
        """send should include custom headers."""
        from unittest.mock import MagicMock, patch

        config = SMTPConfig(host="smtp.example.com", use_tls=False, use_ssl=False)
        sender = SMTPEmailSender(config)

        mock_smtp = MagicMock()
        mock_smtp.sendmail = MagicMock()
        mock_smtp.quit = MagicMock()

        with patch("smtplib.SMTP", return_value=mock_smtp):
            msg = EmailMessage(
                to=["user@example.com"],
                subject="Test",
                html_body="<p>Hello</p>",
                headers={"X-Custom-Header": "custom-value"},
            )
            result = await sender.send(msg)

        assert result.success is True

    @pytest.mark.asyncio
    async def test_send_uses_default_from(self) -> None:
        """send should use default_from when from_address not set."""
        from unittest.mock import MagicMock, patch

        config = SMTPConfig(
            host="smtp.example.com",
            use_tls=False,
            use_ssl=False,
            default_from="noreply@example.com",
        )
        sender = SMTPEmailSender(config)

        mock_smtp = MagicMock()
        mock_smtp.sendmail = MagicMock()
        mock_smtp.quit = MagicMock()

        with patch("smtplib.SMTP", return_value=mock_smtp):
            msg = EmailMessage(
                to=["user@example.com"],
                subject="Test",
                html_body="<p>Hello</p>",
            )
            await sender.send(msg)

        call_args = mock_smtp.sendmail.call_args
        from_addr = call_args[0][0]
        assert from_addr == "noreply@example.com"

    @pytest.mark.asyncio
    async def test_send_connection_error(self) -> None:
        """send should raise EmailConnectionError on connection failure."""
        import smtplib
        from unittest.mock import patch

        config = SMTPConfig(host="smtp.example.com", use_tls=False, use_ssl=False)
        sender = SMTPEmailSender(config)

        with patch(
            "smtplib.SMTP",
            side_effect=smtplib.SMTPConnectError(421, "Connection failed"),
        ):
            msg = EmailMessage(
                to=["user@example.com"],
                subject="Test",
                html_body="<p>Hello</p>",
            )
            with pytest.raises(EmailConnectionError):
                await sender.send(msg)

    @pytest.mark.asyncio
    async def test_send_auth_error(self) -> None:
        """send should raise EmailAuthenticationError on auth failure."""
        import smtplib
        from unittest.mock import MagicMock, patch

        config = SMTPConfig(
            host="smtp.example.com",
            username="user",
            password="wrong",
            use_tls=False,
            use_ssl=False,
        )
        sender = SMTPEmailSender(config)

        mock_smtp = MagicMock()
        mock_smtp.login = MagicMock(
            side_effect=smtplib.SMTPAuthenticationError(535, "Auth failed")
        )
        mock_smtp.quit = MagicMock()

        with patch("smtplib.SMTP", return_value=mock_smtp):
            msg = EmailMessage(
                to=["user@example.com"],
                subject="Test",
                html_body="<p>Hello</p>",
            )
            with pytest.raises(EmailAuthenticationError):
                await sender.send(msg)

    @pytest.mark.asyncio
    async def test_send_generic_error_returns_failure(self) -> None:
        """send should return failure result for generic errors."""
        from unittest.mock import MagicMock, patch

        config = SMTPConfig(host="smtp.example.com", use_tls=False, use_ssl=False)
        sender = SMTPEmailSender(config)

        mock_smtp = MagicMock()
        mock_smtp.sendmail = MagicMock(side_effect=Exception("Unknown error"))
        mock_smtp.quit = MagicMock()

        with patch("smtplib.SMTP", return_value=mock_smtp):
            msg = EmailMessage(
                to=["user@example.com"],
                subject="Test",
                html_body="<p>Hello</p>",
            )
            result = await sender.send(msg)

        assert result.success is False
        assert "Unknown error" in result.error

    @pytest.mark.asyncio
    async def test_is_available_with_ssl(self) -> None:
        """is_available should check SSL server."""
        from unittest.mock import MagicMock, patch

        config = SMTPConfig(
            host="smtp.example.com",
            port=465,
            use_ssl=True,
        )
        sender = SMTPEmailSender(config)

        mock_smtp_ssl = MagicMock()
        mock_smtp_ssl.quit = MagicMock()

        with patch("smtplib.SMTP_SSL", return_value=mock_smtp_ssl):
            available = await sender.is_available()

        assert available is True

    @pytest.mark.asyncio
    async def test_is_available_with_tls(self) -> None:
        """is_available should check TLS server."""
        from unittest.mock import MagicMock, patch

        config = SMTPConfig(
            host="smtp.example.com",
            port=587,
            use_tls=True,
            use_ssl=False,
        )
        sender = SMTPEmailSender(config)

        mock_smtp = MagicMock()
        mock_smtp.quit = MagicMock()

        with patch("smtplib.SMTP", return_value=mock_smtp):
            available = await sender.is_available()

        assert available is True


# =============================================================================
# Test: EmailProcessor
# =============================================================================


class TestEmailProcessor:
    """Tests for EmailProcessor."""

    def test_init(self) -> None:
        """EmailProcessor should initialize with sender."""
        sender = LogEmailSender()
        processor = EmailProcessor(sender=sender)

        assert processor.sender is sender
        assert processor.batch_size == 50

    def test_init_custom_batch_size(self) -> None:
        """EmailProcessor should accept custom batch size."""
        sender = LogEmailSender()
        processor = EmailProcessor(sender=sender, batch_size=10)

        assert processor.batch_size == 10

    @pytest.mark.asyncio
    async def test_process_queue_empty(self) -> None:
        """process_queue should handle empty queue."""
        sender = LogEmailSender()
        processor = EmailProcessor(sender=sender)

        processed = await processor.process_queue()

        assert processed == 0


# =============================================================================
# Test: Exceptions
# =============================================================================


class TestEmailSenderExceptions:
    """Tests for exception hierarchy."""

    def test_connection_error_inherits(self) -> None:
        """EmailConnectionError should inherit from EmailSendError."""
        assert issubclass(EmailConnectionError, EmailSendError)

    def test_auth_error_inherits(self) -> None:
        """EmailAuthenticationError should inherit from EmailSendError."""
        assert issubclass(EmailAuthenticationError, EmailSendError)

    def test_exception_message(self) -> None:
        """Exceptions should accept message."""
        error = EmailConnectionError("Failed to connect")
        assert str(error) == "Failed to connect"
