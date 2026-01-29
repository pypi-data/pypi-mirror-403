"""Tests for File Audit Adapter.

Tests cover:
- FileAuditAdapter initialization
- Log and query operations
- JSONL format validation
"""

import tempfile
from pathlib import Path

import pytest

from framework_m.adapters.audit.file_audit import FileAuditAdapter

# =============================================================================
# Test: Import
# =============================================================================


class TestFileAuditImport:
    """Tests for FileAuditAdapter import."""

    def test_import_file_audit_adapter(self) -> None:
        """FileAuditAdapter should be importable."""
        from framework_m.adapters.audit import FileAuditAdapter

        assert FileAuditAdapter is not None


# =============================================================================
# Test: Initialization
# =============================================================================


class TestFileAuditInit:
    """Tests for FileAuditAdapter initialization."""

    def test_init_creates_directory(self) -> None:
        """Init should create parent directory if not exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "logs" / "audit.log"
            FileAuditAdapter(file_path=str(log_path))
            assert log_path.parent.exists()

    def test_init_with_existing_directory(self) -> None:
        """Init should work with existing directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.log"
            adapter = FileAuditAdapter(file_path=str(log_path))
            assert adapter._file_path == log_path


# =============================================================================
# Test: Log
# =============================================================================


class TestFileAuditLog:
    """Tests for log operation."""

    @pytest.mark.asyncio
    async def test_log_returns_id(self) -> None:
        """log() should return entry ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = FileAuditAdapter(file_path=f"{tmpdir}/audit.log")

            entry_id = await adapter.log(
                user_id="user-001",
                action="create",
                doctype="Todo",
                document_id="TODO-001",
            )

            assert entry_id is not None
            assert isinstance(entry_id, str)

    @pytest.mark.asyncio
    async def test_log_writes_to_file(self) -> None:
        """log() should append to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.log"
            adapter = FileAuditAdapter(file_path=str(log_path))

            await adapter.log("user-001", "create", "Todo", "TODO-001")

            assert log_path.exists()
            content = log_path.read_text()
            assert "user-001" in content
            assert "TODO-001" in content

    @pytest.mark.asyncio
    async def test_log_appends_jsonl(self) -> None:
        """log() should append one JSON line per entry."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.log"
            adapter = FileAuditAdapter(file_path=str(log_path))

            await adapter.log("user-001", "create", "Todo", "TODO-001")
            await adapter.log("user-002", "create", "Todo", "TODO-002")

            lines = log_path.read_text().strip().split("\n")
            assert len(lines) == 2

    @pytest.mark.asyncio
    async def test_log_with_changes(self) -> None:
        """log() should include changes in output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.log"
            adapter = FileAuditAdapter(file_path=str(log_path))

            await adapter.log(
                user_id="user-001",
                action="update",
                doctype="Todo",
                document_id="TODO-001",
                changes={"status": {"old": "open", "new": "closed"}},
            )

            content = log_path.read_text()
            assert "closed" in content


# =============================================================================
# Test: Query
# =============================================================================


class TestFileAuditQuery:
    """Tests for query operation."""

    @pytest.mark.asyncio
    async def test_query_returns_entries(self) -> None:
        """query() should return stored entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = FileAuditAdapter(file_path=f"{tmpdir}/audit.log")

            await adapter.log("user-001", "create", "Todo", "TODO-001")
            entries = await adapter.query()

            assert len(entries) == 1
            assert entries[0].user_id == "user-001"

    @pytest.mark.asyncio
    async def test_query_empty_file(self) -> None:
        """query() should return empty list for nonexistent file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = FileAuditAdapter(file_path=f"{tmpdir}/audit.log")

            entries = await adapter.query()

            assert entries == []

    @pytest.mark.asyncio
    async def test_query_filter_by_user(self) -> None:
        """query() should filter by user_id."""
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = FileAuditAdapter(file_path=f"{tmpdir}/audit.log")

            await adapter.log("user-001", "create", "Todo", "TODO-001")
            await adapter.log("user-002", "create", "Todo", "TODO-002")

            entries = await adapter.query(filters={"user_id": "user-001"})

            assert len(entries) == 1
            assert entries[0].user_id == "user-001"

    @pytest.mark.asyncio
    async def test_query_pagination(self) -> None:
        """query() should support limit and offset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = FileAuditAdapter(file_path=f"{tmpdir}/audit.log")

            for i in range(5):
                await adapter.log("user-001", "create", "Todo", f"TODO-{i:03d}")

            page1 = await adapter.query(limit=2, offset=0)
            page2 = await adapter.query(limit=2, offset=2)

            assert len(page1) == 2
            assert len(page2) == 2
            assert page1[0].document_id != page2[0].document_id

    @pytest.mark.asyncio
    async def test_query_ordered_by_timestamp_desc(self) -> None:
        """query() should return newest first."""
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = FileAuditAdapter(file_path=f"{tmpdir}/audit.log")

            await adapter.log("user-001", "create", "Todo", "TODO-001")
            await adapter.log("user-001", "create", "Todo", "TODO-002")
            await adapter.log("user-001", "create", "Todo", "TODO-003")

            entries = await adapter.query()

            assert entries[0].document_id == "TODO-003"
            assert entries[-1].document_id == "TODO-001"
