"""Tests for EmailQueueProtocol (interface).

Tests cover:
- EmailRequest dataclass
- EmailQueueResult dataclass
- EmailQueueProtocol interface
- Exception types
"""

from datetime import UTC, datetime

from framework_m.core.interfaces.email_queue import (
    EmailQueueError,
    EmailQueueProtocol,
    EmailQueueResult,
    EmailQueueUnavailableError,
    EmailRequest,
    EmailValidationError,
)

# =============================================================================
# Test: Imports
# =============================================================================


class TestEmailQueueInterfaceImports:
    """Tests for email queue interface imports."""

    def test_import_protocol(self) -> None:
        """EmailQueueProtocol should be importable."""
        from framework_m.core.interfaces.email_queue import EmailQueueProtocol

        assert EmailQueueProtocol is not None

    def test_import_request(self) -> None:
        """EmailRequest should be importable."""
        from framework_m.core.interfaces.email_queue import EmailRequest

        assert EmailRequest is not None

    def test_import_result(self) -> None:
        """EmailQueueResult should be importable."""
        from framework_m.core.interfaces.email_queue import EmailQueueResult

        assert EmailQueueResult is not None

    def test_import_exceptions(self) -> None:
        """Exceptions should be importable."""
        from framework_m.core.interfaces.email_queue import (
            EmailQueueError,
            EmailQueueUnavailableError,
            EmailValidationError,
        )

        assert EmailQueueError is not None
        assert EmailValidationError is not None
        assert EmailQueueUnavailableError is not None


# =============================================================================
# Test: EmailRequest
# =============================================================================


class TestEmailRequest:
    """Tests for EmailRequest dataclass."""

    def test_create_minimal(self) -> None:
        """EmailRequest should work with required fields only."""
        request = EmailRequest(
            to=["user@example.com"],
            subject="Test Subject",
            body="<p>Hello World</p>",
        )

        assert request.to == ["user@example.com"]
        assert request.subject == "Test Subject"
        assert request.body == "<p>Hello World</p>"

    def test_default_priority(self) -> None:
        """Default priority should be 'normal'."""
        request = EmailRequest(
            to=["user@example.com"],
            subject="Test",
            body="Body",
        )

        assert request.priority == "normal"

    def test_default_none_fields(self) -> None:
        """Optional fields should default to None."""
        request = EmailRequest(
            to=["user@example.com"],
            subject="Test",
            body="Body",
        )

        assert request.cc is None
        assert request.bcc is None
        assert request.text_body is None
        assert request.from_address is None
        assert request.reply_to is None
        assert request.attachments is None
        assert request.template is None
        assert request.context is None
        assert request.reference_doctype is None
        assert request.reference_id is None

    def test_with_all_fields(self) -> None:
        """EmailRequest should accept all fields."""
        request = EmailRequest(
            to=["user@example.com", "user2@example.com"],
            subject="Test Subject",
            body="<p>Hello</p>",
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
            text_body="Hello plain",
            from_address="sender@example.com",
            reply_to="reply@example.com",
            attachments=[("file.pdf", b"content", "application/pdf")],
            template="welcome",
            context={"name": "John"},
            priority="high",
            reference_doctype="Invoice",
            reference_id="INV-001",
            metadata={"custom": "data"},
        )

        assert len(request.to) == 2
        assert request.cc == ["cc@example.com"]
        assert request.from_address == "sender@example.com"
        assert request.priority == "high"
        assert request.template == "welcome"
        assert request.metadata == {"custom": "data"}

    def test_multiple_recipients(self) -> None:
        """EmailRequest should accept multiple recipients."""
        request = EmailRequest(
            to=["a@example.com", "b@example.com", "c@example.com"],
            subject="Test",
            body="Body",
        )

        assert len(request.to) == 3


# =============================================================================
# Test: EmailQueueResult
# =============================================================================


class TestEmailQueueResult:
    """Tests for EmailQueueResult dataclass."""

    def test_create_result(self) -> None:
        """EmailQueueResult should store queue metadata."""
        result = EmailQueueResult(
            queue_id="queue-123",
            status="Queued",
            queued_at=datetime.now(UTC),
        )

        assert result.queue_id == "queue-123"
        assert result.status == "Queued"
        assert result.queued_at is not None

    def test_result_with_utc_timestamp(self) -> None:
        """EmailQueueResult timestamp should be timezone-aware."""
        now = datetime.now(UTC)
        result = EmailQueueResult(
            queue_id="queue-456",
            status="Sent",
            queued_at=now,
        )

        assert result.queued_at.tzinfo is not None


# =============================================================================
# Test: Exceptions
# =============================================================================


class TestExceptions:
    """Tests for exception hierarchy."""

    def test_validation_error_inherits_from_queue_error(self) -> None:
        """EmailValidationError should inherit from EmailQueueError."""
        assert issubclass(EmailValidationError, EmailQueueError)

    def test_unavailable_error_inherits_from_queue_error(self) -> None:
        """EmailQueueUnavailableError should inherit from EmailQueueError."""
        assert issubclass(EmailQueueUnavailableError, EmailQueueError)

    def test_validation_error_message(self) -> None:
        """EmailValidationError should accept message."""
        error = EmailValidationError("Invalid email format")
        assert str(error) == "Invalid email format"

    def test_unavailable_error_message(self) -> None:
        """EmailQueueUnavailableError should accept message."""
        error = EmailQueueUnavailableError("Queue service down")
        assert str(error) == "Queue service down"


# =============================================================================
# Test: Protocol Definition
# =============================================================================


class TestEmailQueueProtocol:
    """Tests for EmailQueueProtocol interface."""

    def test_protocol_has_queue_email_method(self) -> None:
        """Protocol should define queue_email method."""

        # Check that queue_email is in the protocol
        assert hasattr(EmailQueueProtocol, "queue_email")

        # Check that it's a method
        method = EmailQueueProtocol.queue_email
        assert callable(method)

    def test_protocol_has_get_status_method(self) -> None:
        """Protocol should define get_status method."""
        assert hasattr(EmailQueueProtocol, "get_status")

    def test_protocol_has_cancel_method(self) -> None:
        """Protocol should define cancel method."""
        assert hasattr(EmailQueueProtocol, "cancel")
