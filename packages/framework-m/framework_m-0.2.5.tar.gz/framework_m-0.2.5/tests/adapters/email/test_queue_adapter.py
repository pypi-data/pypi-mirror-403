"""Tests for Email Queue Adapters.

Tests cover:
- DatabaseEmailQueueAdapter
- InMemoryEmailQueueAdapter
- Adapter behavior
"""

from datetime import UTC

import pytest

from framework_m.adapters.email.queue_adapter import (
    DatabaseEmailQueueAdapter,
    InMemoryEmailQueueAdapter,
)
from framework_m.core.doctypes.email_queue import EmailStatus
from framework_m.core.interfaces.email_queue import (
    EmailRequest,
    EmailValidationError,
)

# =============================================================================
# Test: Imports
# =============================================================================


class TestQueueAdapterImports:
    """Tests for queue adapter imports."""

    def test_import_database_adapter(self) -> None:
        """DatabaseEmailQueueAdapter should be importable."""
        from framework_m.adapters.email.queue_adapter import DatabaseEmailQueueAdapter

        assert DatabaseEmailQueueAdapter is not None

    def test_import_inmemory_adapter(self) -> None:
        """InMemoryEmailQueueAdapter should be importable."""
        from framework_m.adapters.email.queue_adapter import InMemoryEmailQueueAdapter

        assert InMemoryEmailQueueAdapter is not None


# =============================================================================
# Test: DatabaseEmailQueueAdapter
# =============================================================================


class TestDatabaseEmailQueueAdapter:
    """Tests for DatabaseEmailQueueAdapter."""

    def test_init_without_repository(self) -> None:
        """Adapter should work without repository (in-memory fallback)."""
        adapter = DatabaseEmailQueueAdapter()
        assert adapter._repository is None

    def test_init_with_repository(self) -> None:
        """Adapter should accept repository."""
        mock_repo = object()  # Placeholder
        adapter = DatabaseEmailQueueAdapter(repository=mock_repo)
        assert adapter._repository is mock_repo

    @pytest.mark.asyncio
    async def test_queue_email_success(self) -> None:
        """queue_email should return result with queue_id."""
        adapter = DatabaseEmailQueueAdapter()
        request = EmailRequest(
            to=["user@example.com"],
            subject="Test",
            body="<p>Hello</p>",
        )

        result = await adapter.queue_email(request)

        assert result.queue_id is not None
        assert result.status == EmailStatus.QUEUED
        assert result.queued_at is not None
        assert result.queued_at.tzinfo == UTC

    @pytest.mark.asyncio
    async def test_queue_email_validation_empty_to(self) -> None:
        """queue_email should reject empty recipients."""
        adapter = DatabaseEmailQueueAdapter()
        request = EmailRequest(
            to=[],
            subject="Test",
            body="Body",
        )

        with pytest.raises(EmailValidationError, match="recipient"):
            await adapter.queue_email(request)

    @pytest.mark.asyncio
    async def test_get_status_existing(self) -> None:
        """get_status should return status for queued email."""
        adapter = DatabaseEmailQueueAdapter()
        request = EmailRequest(
            to=["user@example.com"],
            subject="Test",
            body="Body",
        )
        result = await adapter.queue_email(request)

        status = await adapter.get_status(result.queue_id)

        assert status == EmailStatus.QUEUED

    @pytest.mark.asyncio
    async def test_get_status_nonexistent(self) -> None:
        """get_status should return None for unknown queue_id."""
        adapter = DatabaseEmailQueueAdapter()

        status = await adapter.get_status("nonexistent-id")

        assert status is None

    @pytest.mark.asyncio
    async def test_cancel_queued_email(self) -> None:
        """cancel should return True for queued email."""
        adapter = DatabaseEmailQueueAdapter()
        request = EmailRequest(
            to=["user@example.com"],
            subject="Test",
            body="Body",
        )
        result = await adapter.queue_email(request)

        cancelled = await adapter.cancel(result.queue_id)

        assert cancelled is True

    @pytest.mark.asyncio
    async def test_cancel_nonexistent(self) -> None:
        """cancel should return False for unknown queue_id."""
        adapter = DatabaseEmailQueueAdapter()

        cancelled = await adapter.cancel("nonexistent-id")

        assert cancelled is False

    @pytest.mark.asyncio
    async def test_converts_attachments_to_metadata(self) -> None:
        """Attachments should be converted to metadata format."""
        adapter = DatabaseEmailQueueAdapter()
        request = EmailRequest(
            to=["user@example.com"],
            subject="Test",
            body="Body",
            attachments=[
                ("doc.pdf", b"pdf content", "application/pdf"),
                ("image.png", b"png content", "image/png"),
            ],
        )

        result = await adapter.queue_email(request)

        # Check the stored email
        email = adapter._in_memory_queue.get(result.queue_id)
        assert email is not None
        assert email.attachments is not None
        assert len(email.attachments) == 2
        assert email.attachments[0]["filename"] == "doc.pdf"
        assert email.attachments[1]["content_type"] == "image/png"


# =============================================================================
# Test: InMemoryEmailQueueAdapter
# =============================================================================


class TestInMemoryEmailQueueAdapter:
    """Tests for InMemoryEmailQueueAdapter."""

    def test_init_empty_queue(self) -> None:
        """Adapter should start with empty queue."""
        adapter = InMemoryEmailQueueAdapter()
        assert len(adapter.queued_emails) == 0

    @pytest.mark.asyncio
    async def test_queue_email_stores_request(self) -> None:
        """queue_email should store the request."""
        adapter = InMemoryEmailQueueAdapter()
        request = EmailRequest(
            to=["user@example.com"],
            subject="Test",
            body="<p>Hello</p>",
        )

        await adapter.queue_email(request)

        assert len(adapter.queued_emails) == 1
        _queue_id, stored_request = adapter.queued_emails[0]
        assert stored_request.to == ["user@example.com"]

    @pytest.mark.asyncio
    async def test_queue_multiple_emails(self) -> None:
        """Adapter should queue multiple emails."""
        adapter = InMemoryEmailQueueAdapter()

        await adapter.queue_email(
            EmailRequest(to=["a@example.com"], subject="A", body="A")
        )
        await adapter.queue_email(
            EmailRequest(to=["b@example.com"], subject="B", body="B")
        )
        await adapter.queue_email(
            EmailRequest(to=["c@example.com"], subject="C", body="C")
        )

        assert len(adapter.queued_emails) == 3

    @pytest.mark.asyncio
    async def test_queue_email_validation(self) -> None:
        """queue_email should validate request."""
        adapter = InMemoryEmailQueueAdapter()

        with pytest.raises(EmailValidationError):
            await adapter.queue_email(EmailRequest(to=[], subject="Test", body="Body"))

    @pytest.mark.asyncio
    async def test_get_status_queued(self) -> None:
        """get_status should return Queued for new emails."""
        adapter = InMemoryEmailQueueAdapter()
        result = await adapter.queue_email(
            EmailRequest(to=["user@example.com"], subject="Test", body="Body")
        )

        status = await adapter.get_status(result.queue_id)

        assert status == EmailStatus.QUEUED

    @pytest.mark.asyncio
    async def test_cancel_updates_status(self) -> None:
        """cancel should update status to Cancelled."""
        adapter = InMemoryEmailQueueAdapter()
        result = await adapter.queue_email(
            EmailRequest(to=["user@example.com"], subject="Test", body="Body")
        )

        await adapter.cancel(result.queue_id)

        status = await adapter.get_status(result.queue_id)
        assert status == EmailStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_returns_false_for_cancelled(self) -> None:
        """cancel should return False for already cancelled emails."""
        adapter = InMemoryEmailQueueAdapter()
        result = await adapter.queue_email(
            EmailRequest(to=["user@example.com"], subject="Test", body="Body")
        )

        # First cancel succeeds
        first = await adapter.cancel(result.queue_id)
        assert first is True

        # Second cancel fails (already cancelled)
        second = await adapter.cancel(result.queue_id)
        assert second is False

    def test_clear_empties_queue(self) -> None:
        """clear should empty the queue."""
        adapter = InMemoryEmailQueueAdapter()
        adapter.queued_emails.append(
            ("id", EmailRequest(to=["test@example.com"], subject="T", body="B"))
        )
        adapter._statuses["id"] = EmailStatus.QUEUED

        adapter.clear()

        assert len(adapter.queued_emails) == 0
        assert len(adapter._statuses) == 0


# =============================================================================
# Test: Adapter Protocol Compliance
# =============================================================================


class TestAdapterProtocolCompliance:
    """Tests that adapters implement EmailQueueProtocol."""

    def test_database_adapter_has_queue_email(self) -> None:
        """DatabaseEmailQueueAdapter should have queue_email method."""
        adapter = DatabaseEmailQueueAdapter()
        assert hasattr(adapter, "queue_email")
        assert callable(adapter.queue_email)

    def test_database_adapter_has_get_status(self) -> None:
        """DatabaseEmailQueueAdapter should have get_status method."""
        adapter = DatabaseEmailQueueAdapter()
        assert hasattr(adapter, "get_status")

    def test_database_adapter_has_cancel(self) -> None:
        """DatabaseEmailQueueAdapter should have cancel method."""
        adapter = DatabaseEmailQueueAdapter()
        assert hasattr(adapter, "cancel")

    def test_inmemory_adapter_has_queue_email(self) -> None:
        """InMemoryEmailQueueAdapter should have queue_email method."""
        adapter = InMemoryEmailQueueAdapter()
        assert hasattr(adapter, "queue_email")

    def test_inmemory_adapter_has_get_status(self) -> None:
        """InMemoryEmailQueueAdapter should have get_status method."""
        adapter = InMemoryEmailQueueAdapter()
        assert hasattr(adapter, "get_status")

    def test_inmemory_adapter_has_cancel(self) -> None:
        """InMemoryEmailQueueAdapter should have cancel method."""
        adapter = InMemoryEmailQueueAdapter()
        assert hasattr(adapter, "cancel")
