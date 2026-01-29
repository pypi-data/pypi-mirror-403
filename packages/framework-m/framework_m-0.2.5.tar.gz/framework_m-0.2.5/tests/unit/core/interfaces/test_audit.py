"""Tests for Audit Log Protocol.

Tests cover:
- AuditEntry model
- AuditLogProtocol signature
- InMemoryAuditAdapter implementation
"""

from datetime import UTC

import pytest

# =============================================================================
# Test: AuditEntry Model
# =============================================================================


class TestAuditEntry:
    """Tests for AuditEntry model."""

    def test_import_audit_entry(self) -> None:
        """AuditEntry should be importable."""
        from framework_m.core.interfaces.audit import AuditEntry

        assert AuditEntry is not None

    def test_create_minimal(self) -> None:
        """AuditEntry should work with required fields only."""
        from framework_m.core.interfaces.audit import AuditEntry

        entry = AuditEntry(
            user_id="user-001",
            action="create",
            doctype="Invoice",
            document_id="INV-001",
        )

        assert entry.user_id == "user-001"
        assert entry.action == "create"
        assert entry.doctype == "Invoice"
        assert entry.document_id == "INV-001"
        assert entry.id is not None
        assert entry.timestamp is not None

    def test_create_with_changes(self) -> None:
        """AuditEntry should accept changes dict."""
        from framework_m.core.interfaces.audit import AuditEntry

        entry = AuditEntry(
            user_id="user-001",
            action="update",
            doctype="Invoice",
            document_id="INV-001",
            changes={"status": {"old": "draft", "new": "submitted"}},
        )

        assert entry.changes is not None
        assert entry.changes["status"]["old"] == "draft"
        assert entry.changes["status"]["new"] == "submitted"

    def test_create_with_metadata(self) -> None:
        """AuditEntry should accept metadata dict."""
        from framework_m.core.interfaces.audit import AuditEntry

        entry = AuditEntry(
            user_id="user-001",
            action="read",
            doctype="Invoice",
            document_id="INV-001",
            metadata={"request_id": "req-123", "ip": "192.168.1.1"},
        )

        assert entry.metadata is not None
        assert entry.metadata["request_id"] == "req-123"

    def test_auto_generated_id(self) -> None:
        """AuditEntry should auto-generate unique IDs."""
        from framework_m.core.interfaces.audit import AuditEntry

        entry1 = AuditEntry(
            user_id="user-001",
            action="create",
            doctype="Todo",
            document_id="TODO-001",
        )
        entry2 = AuditEntry(
            user_id="user-001",
            action="create",
            doctype="Todo",
            document_id="TODO-002",
        )

        assert entry1.id != entry2.id

    def test_timestamp_is_utc(self) -> None:
        """AuditEntry timestamp should be UTC."""

        from framework_m.core.interfaces.audit import AuditEntry

        entry = AuditEntry(
            user_id="user-001",
            action="create",
            doctype="Todo",
            document_id="TODO-001",
        )

        assert entry.timestamp.tzinfo is not None
        assert entry.timestamp.tzinfo == UTC


# =============================================================================
# Test: AuditLogProtocol
# =============================================================================


class TestAuditLogProtocol:
    """Tests for AuditLogProtocol interface."""

    def test_import_protocol(self) -> None:
        """AuditLogProtocol should be importable."""
        from framework_m.core.interfaces.audit import AuditLogProtocol

        assert AuditLogProtocol is not None

    def test_protocol_has_log_method(self) -> None:
        """AuditLogProtocol should have log method."""
        from framework_m.core.interfaces.audit import AuditLogProtocol

        assert hasattr(AuditLogProtocol, "log")

    def test_protocol_has_query_method(self) -> None:
        """AuditLogProtocol should have query method."""
        from framework_m.core.interfaces.audit import AuditLogProtocol

        assert hasattr(AuditLogProtocol, "query")


# =============================================================================
# Test: InMemoryAuditAdapter
# =============================================================================


class TestInMemoryAuditAdapter:
    """Tests for InMemoryAuditAdapter."""

    def test_import_adapter(self) -> None:
        """InMemoryAuditAdapter should be importable."""
        from framework_m.core.interfaces.audit import InMemoryAuditAdapter

        assert InMemoryAuditAdapter is not None

    @pytest.mark.asyncio
    async def test_log_returns_id(self) -> None:
        """log() should return entry ID."""
        from framework_m.core.interfaces.audit import InMemoryAuditAdapter

        adapter = InMemoryAuditAdapter()
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
        """log() should store entry in memory."""
        from framework_m.core.interfaces.audit import InMemoryAuditAdapter

        adapter = InMemoryAuditAdapter()
        await adapter.log(
            user_id="user-001",
            action="create",
            doctype="Todo",
            document_id="TODO-001",
        )

        entries = await adapter.query()
        assert len(entries) == 1
        assert entries[0].user_id == "user-001"

    @pytest.mark.asyncio
    async def test_query_filter_by_user(self) -> None:
        """query() should filter by user_id."""
        from framework_m.core.interfaces.audit import InMemoryAuditAdapter

        adapter = InMemoryAuditAdapter()
        await adapter.log("user-001", "create", "Todo", "TODO-001")
        await adapter.log("user-002", "create", "Todo", "TODO-002")

        entries = await adapter.query(filters={"user_id": "user-001"})

        assert len(entries) == 1
        assert entries[0].user_id == "user-001"

    @pytest.mark.asyncio
    async def test_query_filter_by_action(self) -> None:
        """query() should filter by action."""
        from framework_m.core.interfaces.audit import InMemoryAuditAdapter

        adapter = InMemoryAuditAdapter()
        await adapter.log("user-001", "create", "Todo", "TODO-001")
        await adapter.log("user-001", "update", "Todo", "TODO-001")

        entries = await adapter.query(filters={"action": "update"})

        assert len(entries) == 1
        assert entries[0].action == "update"

    @pytest.mark.asyncio
    async def test_query_filter_by_doctype(self) -> None:
        """query() should filter by doctype."""
        from framework_m.core.interfaces.audit import InMemoryAuditAdapter

        adapter = InMemoryAuditAdapter()
        await adapter.log("user-001", "create", "Todo", "TODO-001")
        await adapter.log("user-001", "create", "Invoice", "INV-001")

        entries = await adapter.query(filters={"doctype": "Invoice"})

        assert len(entries) == 1
        assert entries[0].doctype == "Invoice"

    @pytest.mark.asyncio
    async def test_query_pagination(self) -> None:
        """query() should support limit and offset."""
        from framework_m.core.interfaces.audit import InMemoryAuditAdapter

        adapter = InMemoryAuditAdapter()
        for i in range(10):
            await adapter.log("user-001", "create", "Todo", f"TODO-{i:03d}")

        # Get first 3
        page1 = await adapter.query(limit=3, offset=0)
        assert len(page1) == 3

        # Get next 3
        page2 = await adapter.query(limit=3, offset=3)
        assert len(page2) == 3

        # Pages should be different
        assert page1[0].document_id != page2[0].document_id

    @pytest.mark.asyncio
    async def test_query_ordered_by_timestamp_desc(self) -> None:
        """query() should return newest entries first."""
        from framework_m.core.interfaces.audit import InMemoryAuditAdapter

        adapter = InMemoryAuditAdapter()
        await adapter.log("user-001", "create", "Todo", "TODO-001")
        await adapter.log("user-001", "create", "Todo", "TODO-002")
        await adapter.log("user-001", "create", "Todo", "TODO-003")

        entries = await adapter.query()

        # Newest (TODO-003) should be first
        assert entries[0].document_id == "TODO-003"
        assert entries[-1].document_id == "TODO-001"
