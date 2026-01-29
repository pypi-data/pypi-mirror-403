"""Tests for Database Audit Adapter.

Tests cover:
- DatabaseAuditAdapter initialization
- Log and query operations
- ActivityLog integration
"""

import pytest

from framework_m.adapters.audit.database_audit import DatabaseAuditAdapter
from framework_m.core.interfaces.audit import AuditEntry

# =============================================================================
# Test: Import
# =============================================================================


class TestDatabaseAuditImport:
    """Tests for DatabaseAuditAdapter import."""

    def test_import_database_audit_adapter(self) -> None:
        """DatabaseAuditAdapter should be importable."""
        from framework_m.adapters.audit import DatabaseAuditAdapter

        assert DatabaseAuditAdapter is not None


# =============================================================================
# Test: Log
# =============================================================================


class TestDatabaseAuditLog:
    """Tests for log operation."""

    @pytest.mark.asyncio
    async def test_log_returns_id(self) -> None:
        """log() should return entry ID."""
        adapter = DatabaseAuditAdapter()

        entry_id = await adapter.log(
            user_id="user-001",
            action="create",
            doctype="Todo",
            document_id="TODO-001",
        )

        assert entry_id is not None
        assert isinstance(entry_id, str)

    @pytest.mark.asyncio
    async def test_log_stores_entry(self) -> None:
        """log() should store entry."""
        adapter = DatabaseAuditAdapter()

        await adapter.log("user-001", "create", "Todo", "TODO-001")

        entries = await adapter.query()
        assert len(entries) == 1
        assert entries[0].user_id == "user-001"

    @pytest.mark.asyncio
    async def test_log_with_changes(self) -> None:
        """log() should store changes."""
        adapter = DatabaseAuditAdapter()

        await adapter.log(
            user_id="user-001",
            action="update",
            doctype="Todo",
            document_id="TODO-001",
            changes={"status": {"old": "open", "new": "closed"}},
        )

        entries = await adapter.query()
        assert entries[0].changes is not None
        assert entries[0].changes["status"]["new"] == "closed"

    @pytest.mark.asyncio
    async def test_log_with_metadata(self) -> None:
        """log() should store metadata."""
        adapter = DatabaseAuditAdapter()

        await adapter.log(
            user_id="user-001",
            action="read",
            doctype="Todo",
            document_id="TODO-001",
            metadata={"request_id": "req-123"},
        )

        entries = await adapter.query()
        assert entries[0].metadata is not None
        assert entries[0].metadata["request_id"] == "req-123"


# =============================================================================
# Test: Query
# =============================================================================


class TestDatabaseAuditQuery:
    """Tests for query operation."""

    @pytest.mark.asyncio
    async def test_query_returns_audit_entries(self) -> None:
        """query() should return AuditEntry objects."""
        adapter = DatabaseAuditAdapter()

        await adapter.log("user-001", "create", "Todo", "TODO-001")
        entries = await adapter.query()

        assert len(entries) == 1
        assert isinstance(entries[0], AuditEntry)

    @pytest.mark.asyncio
    async def test_query_filter_by_user(self) -> None:
        """query() should filter by user_id."""
        adapter = DatabaseAuditAdapter()

        await adapter.log("user-001", "create", "Todo", "TODO-001")
        await adapter.log("user-002", "create", "Todo", "TODO-002")

        entries = await adapter.query(filters={"user_id": "user-001"})

        assert len(entries) == 1
        assert entries[0].user_id == "user-001"

    @pytest.mark.asyncio
    async def test_query_filter_by_action(self) -> None:
        """query() should filter by action."""
        adapter = DatabaseAuditAdapter()

        await adapter.log("user-001", "create", "Todo", "TODO-001")
        await adapter.log("user-001", "update", "Todo", "TODO-001")

        entries = await adapter.query(filters={"action": "update"})

        assert len(entries) == 1
        assert entries[0].action == "update"

    @pytest.mark.asyncio
    async def test_query_pagination(self) -> None:
        """query() should support limit and offset."""
        adapter = DatabaseAuditAdapter()

        for i in range(5):
            await adapter.log("user-001", "create", "Todo", f"TODO-{i:03d}")

        page1 = await adapter.query(limit=2, offset=0)
        page2 = await adapter.query(limit=2, offset=2)

        assert len(page1) == 2
        assert len(page2) == 2

    @pytest.mark.asyncio
    async def test_query_ordered_by_timestamp_desc(self) -> None:
        """query() should return newest first."""
        adapter = DatabaseAuditAdapter()

        await adapter.log("user-001", "create", "Todo", "TODO-001")
        await adapter.log("user-001", "create", "Todo", "TODO-002")
        await adapter.log("user-001", "create", "Todo", "TODO-003")

        entries = await adapter.query()

        assert entries[0].document_id == "TODO-003"
        assert entries[-1].document_id == "TODO-001"
