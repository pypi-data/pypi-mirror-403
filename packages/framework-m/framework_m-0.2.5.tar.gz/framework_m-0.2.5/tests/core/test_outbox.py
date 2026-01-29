"""Tests for Outbox Pattern implementation."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from framework_m.core.domain.outbox import OutboxEntry, OutboxStatus

# =============================================================================
# Test: OutboxStatus Enum
# =============================================================================


class TestOutboxStatus:
    """Tests for OutboxStatus enum."""

    def test_pending_status_exists(self) -> None:
        """PENDING status should be available."""
        assert OutboxStatus.PENDING == "pending"

    def test_processed_status_exists(self) -> None:
        """PROCESSED status should be available."""
        assert OutboxStatus.PROCESSED == "processed"

    def test_failed_status_exists(self) -> None:
        """FAILED status should be available."""
        assert OutboxStatus.FAILED == "failed"


# =============================================================================
# Test: OutboxEntry Model
# =============================================================================


class TestOutboxEntryCreation:
    """Tests for OutboxEntry model creation."""

    def test_create_outbox_entry_minimal(self) -> None:
        """Should create OutboxEntry with minimal required fields."""
        entry = OutboxEntry(
            target="mongodb.audit_log",
            payload={"action": "create", "doctype": "Todo"},
        )

        assert entry.target == "mongodb.audit_log"
        assert entry.payload == {"action": "create", "doctype": "Todo"}
        assert entry.status == OutboxStatus.PENDING  # Default
        assert entry.id is not None
        assert isinstance(entry.id, UUID)

    def test_create_outbox_entry_all_fields(self) -> None:
        """Should create OutboxEntry with all fields specified."""
        now = datetime.now(UTC)
        entry = OutboxEntry(
            target="api.payment_gateway",
            payload={"amount": 100, "currency": "USD"},
            status=OutboxStatus.PROCESSED,
            created_at=now,
            processed_at=now,
            error_message=None,
            retry_count=0,
        )

        assert entry.target == "api.payment_gateway"
        assert entry.status == OutboxStatus.PROCESSED
        assert entry.created_at == now
        assert entry.processed_at == now


class TestOutboxEntryDefaults:
    """Tests for OutboxEntry default values."""

    def test_default_status_is_pending(self) -> None:
        """Default status should be PENDING."""
        entry = OutboxEntry(target="test", payload={})
        assert entry.status == OutboxStatus.PENDING

    def test_default_processed_at_is_none(self) -> None:
        """Default processed_at should be None."""
        entry = OutboxEntry(target="test", payload={})
        assert entry.processed_at is None

    def test_default_error_message_is_none(self) -> None:
        """Default error_message should be None."""
        entry = OutboxEntry(target="test", payload={})
        assert entry.error_message is None

    def test_default_retry_count_is_zero(self) -> None:
        """Default retry_count should be 0."""
        entry = OutboxEntry(target="test", payload={})
        assert entry.retry_count == 0

    def test_created_at_auto_generated(self) -> None:
        """created_at should be auto-generated."""
        entry = OutboxEntry(target="test", payload={})
        assert entry.created_at is not None
        assert isinstance(entry.created_at, datetime)


class TestOutboxEntryImport:
    """Tests for module imports."""

    def test_import_outbox_entry(self) -> None:
        """OutboxEntry should be importable."""
        from framework_m.core.domain.outbox import OutboxEntry

        assert OutboxEntry is not None

    def test_import_outbox_status(self) -> None:
        """OutboxStatus should be importable."""
        from framework_m.core.domain.outbox import OutboxStatus

        assert OutboxStatus is not None
