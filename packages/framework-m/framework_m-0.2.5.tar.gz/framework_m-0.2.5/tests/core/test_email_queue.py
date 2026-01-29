"""Tests for Email Queue DocType and Protocol.

Tests cover:
- EmailQueue DocType creation
- EmailQueueProtocol and adapters
- Helper function
"""

from datetime import UTC

import pytest

from framework_m.core.doctypes.email_queue import (
    EmailPriority,
    EmailQueue,
    EmailStatus,
)
from framework_m.core.interfaces.email_queue import (
    EmailRequest,
    EmailValidationError,
)

# =============================================================================
# Test: EmailQueue DocType Import
# =============================================================================


class TestEmailQueueImport:
    """Tests for EmailQueue imports."""

    def test_import_email_queue(self) -> None:
        """EmailQueue should be importable."""
        from framework_m.core.doctypes.email_queue import EmailQueue

        assert EmailQueue is not None

    def test_import_status_constants(self) -> None:
        """EmailStatus should be importable."""
        from framework_m.core.doctypes.email_queue import EmailStatus

        assert EmailStatus.QUEUED == "Queued"
        assert EmailStatus.SENT == "Sent"
        assert EmailStatus.FAILED == "Failed"


# =============================================================================
# Test: EmailQueue DocType Creation
# =============================================================================


class TestEmailQueueCreation:
    """Tests for EmailQueue model creation."""

    def test_create_minimal(self) -> None:
        """EmailQueue should work with required fields only."""
        email = EmailQueue(
            to=["user@example.com"],
            subject="Test",
            body="<p>Hello</p>",
        )

        assert email.to == ["user@example.com"]
        assert email.subject == "Test"
        assert email.status == EmailStatus.QUEUED

    def test_create_with_cc_bcc(self) -> None:
        """EmailQueue should accept cc and bcc."""
        email = EmailQueue(
            to=["user@example.com"],
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
            subject="Test",
            body="<p>Hello</p>",
        )

        assert email.cc == ["cc@example.com"]
        assert email.bcc == ["bcc@example.com"]

    def test_default_priority(self) -> None:
        """EmailQueue should default to normal priority."""
        email = EmailQueue(
            to=["user@example.com"],
            subject="Test",
            body="<p>Hello</p>",
        )

        assert email.priority == EmailPriority.NORMAL

    def test_default_retry_count(self) -> None:
        """EmailQueue should default to 0 retries."""
        email = EmailQueue(
            to=["user@example.com"],
            subject="Test",
            body="<p>Hello</p>",
        )

        assert email.retry_count == 0
        assert email.max_retries == 3

    def test_queued_at_is_utc(self) -> None:
        """EmailQueue queued_at should be UTC."""
        email = EmailQueue(
            to=["user@example.com"],
            subject="Test",
            body="<p>Hello</p>",
        )

        assert email.queued_at.tzinfo is not None
        assert email.queued_at.tzinfo == UTC


# =============================================================================
# Test: EmailQueue Meta
# =============================================================================


class TestEmailQueueMeta:
    """Tests for EmailQueue Meta configuration."""

    def test_meta_table_name(self) -> None:
        """Meta should have correct table_name."""
        assert EmailQueue.Meta.table_name == "email_queue"

    def test_meta_admin_only(self) -> None:
        """Meta should restrict access to admins."""
        assert "System Manager" in EmailQueue.Meta.permissions["read"]
        assert "System Manager" in EmailQueue.Meta.permissions["write"]


# =============================================================================
# Test: EmailRequest
# =============================================================================


class TestEmailRequest:
    """Tests for EmailRequest dataclass."""

    def test_create_minimal(self) -> None:
        """EmailRequest should work with required fields."""
        request = EmailRequest(
            to=["user@example.com"],
            subject="Test",
            body="<p>Hello</p>",
        )

        assert request.to == ["user@example.com"]
        assert request.priority == "normal"

    def test_create_with_all_fields(self) -> None:
        """EmailRequest should accept all fields."""
        request = EmailRequest(
            to=["user@example.com"],
            subject="Test",
            body="<p>Hello</p>",
            cc=["cc@example.com"],
            from_address="sender@example.com",
            template="welcome",
            context={"name": "John"},
            reference_doctype="Invoice",
            reference_id="INV-001",
        )

        assert request.from_address == "sender@example.com"
        assert request.template == "welcome"
        assert request.reference_doctype == "Invoice"


# =============================================================================
# Test: Email Queue Adapters
# =============================================================================


class TestEmailQueueAdapters:
    """Tests for email queue adapters."""

    def test_import_adapters(self) -> None:
        """Adapters should be importable."""
        from framework_m.adapters.email import (
            DatabaseEmailQueueAdapter,
            InMemoryEmailQueueAdapter,
        )

        assert DatabaseEmailQueueAdapter is not None
        assert InMemoryEmailQueueAdapter is not None

    @pytest.mark.asyncio
    async def test_in_memory_adapter_queue(self) -> None:
        """InMemoryEmailQueueAdapter should queue emails."""
        from framework_m.adapters.email import InMemoryEmailQueueAdapter

        adapter = InMemoryEmailQueueAdapter()
        request = EmailRequest(
            to=["user@example.com"],
            subject="Test",
            body="<p>Hello</p>",
        )

        result = await adapter.queue_email(request)

        assert result.queue_id is not None
        assert result.status == EmailStatus.QUEUED
        assert len(adapter.queued_emails) == 1

    @pytest.mark.asyncio
    async def test_in_memory_adapter_get_status(self) -> None:
        """InMemoryEmailQueueAdapter should track status."""
        from framework_m.adapters.email import InMemoryEmailQueueAdapter

        adapter = InMemoryEmailQueueAdapter()
        result = await adapter.queue_email(
            EmailRequest(to=["test@example.com"], subject="Test", body="Body")
        )

        status = await adapter.get_status(result.queue_id)
        assert status == EmailStatus.QUEUED

    @pytest.mark.asyncio
    async def test_in_memory_adapter_validation(self) -> None:
        """InMemoryEmailQueueAdapter should validate requests."""
        from framework_m.adapters.email import InMemoryEmailQueueAdapter

        adapter = InMemoryEmailQueueAdapter()

        with pytest.raises(EmailValidationError):
            await adapter.queue_email(EmailRequest(to=[], subject="Test", body="Body"))

    @pytest.mark.asyncio
    async def test_database_adapter_queue(self) -> None:
        """DatabaseEmailQueueAdapter should queue emails (in-memory fallback)."""
        from framework_m.adapters.email import DatabaseEmailQueueAdapter

        adapter = DatabaseEmailQueueAdapter()
        result = await adapter.queue_email(
            EmailRequest(to=["test@example.com"], subject="Test", body="Body")
        )

        assert result.queue_id is not None
        assert result.status == EmailStatus.QUEUED


# =============================================================================
# Test: Helper Function
# =============================================================================


class TestQueueEmailHelper:
    """Tests for queue_email helper function."""

    @pytest.mark.asyncio
    async def test_queue_email_simple(self) -> None:
        """queue_email should queue with minimal args."""
        from framework_m.adapters.email import (
            InMemoryEmailQueueAdapter,
            configure_email_queue,
            queue_email,
        )

        # Configure with test adapter
        adapter = InMemoryEmailQueueAdapter()
        configure_email_queue(adapter)

        result = await queue_email(
            to="user@example.com",
            subject="Test",
            body="<p>Hello</p>",
        )

        assert result.queue_id is not None
        assert len(adapter.queued_emails) == 1

    @pytest.mark.asyncio
    async def test_queue_email_with_reference(self) -> None:
        """queue_email should accept reference params."""
        from framework_m.adapters.email import (
            InMemoryEmailQueueAdapter,
            configure_email_queue,
            queue_email,
        )

        adapter = InMemoryEmailQueueAdapter()
        configure_email_queue(adapter)

        await queue_email(
            to=["finance@example.com"],
            subject="Invoice",
            body="<p>Invoice attached</p>",
            reference_doctype="Invoice",
            reference_id="INV-001",
        )

        _, request = adapter.queued_emails[0]
        assert request.reference_doctype == "Invoice"
        assert request.reference_id == "INV-001"
