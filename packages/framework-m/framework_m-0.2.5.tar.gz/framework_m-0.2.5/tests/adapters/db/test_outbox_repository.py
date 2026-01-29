"""Tests for OutboxRepository.

Tests the SQL-backed repository for outbox entries used in
the Outbox Pattern for reliable multi-source coordination.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from sqlalchemy import MetaData, create_engine
from sqlalchemy.pool import NullPool

from framework_m.adapters.db.outbox_repository import (
    OutboxRepository,
    create_outbox_table,
)
from framework_m.core.domain.outbox import OutboxEntry, OutboxStatus

if TYPE_CHECKING:
    pass


class TestCreateOutboxTable:
    """Tests for create_outbox_table function."""

    def test_creates_table_with_correct_name(self) -> None:
        """Table should be named '_outbox'."""
        metadata = MetaData()
        table = create_outbox_table(metadata)
        assert table.name == "_outbox"

    def test_table_has_required_columns(self) -> None:
        """Table should have all required columns."""
        metadata = MetaData()
        table = create_outbox_table(metadata)

        column_names = {c.name for c in table.columns}
        expected = {
            "id",
            "target",
            "payload",
            "status",
            "created_at",
            "processed_at",
            "error_message",
            "retry_count",
        }
        assert column_names == expected

    def test_id_is_primary_key(self) -> None:
        """The id column should be primary key."""
        metadata = MetaData()
        table = create_outbox_table(metadata)
        assert table.c.id.primary_key

    def test_target_is_indexed(self) -> None:
        """The target column should be indexed."""
        metadata = MetaData()
        table = create_outbox_table(metadata)
        assert table.c.target.index

    def test_status_is_indexed(self) -> None:
        """The status column should be indexed."""
        metadata = MetaData()
        table = create_outbox_table(metadata)
        assert table.c.status.index


class TestOutboxRepositoryImport:
    """Tests for module imports."""

    def test_import_outbox_repository(self) -> None:
        """OutboxRepository should be importable."""
        from framework_m.adapters.db.outbox_repository import OutboxRepository

        assert OutboxRepository is not None

    def test_import_create_outbox_table(self) -> None:
        """create_outbox_table should be importable."""
        from framework_m.adapters.db.outbox_repository import create_outbox_table

        assert create_outbox_table is not None


class TestOutboxRepositorySync:
    """Synchronous tests for OutboxRepository basic functionality."""

    @pytest.fixture
    def metadata(self) -> MetaData:
        """Create fresh metadata."""
        return MetaData()

    @pytest.fixture
    def outbox_table(self, metadata: MetaData) -> None:
        """Create outbox table in metadata."""
        return create_outbox_table(metadata)

    @pytest.fixture
    def repository(self, outbox_table: None, metadata: MetaData) -> OutboxRepository:
        """Create repository with table."""
        table = metadata.tables["_outbox"]
        return OutboxRepository(table)

    def test_repository_creation(self, repository: OutboxRepository) -> None:
        """Repository should be creatable with table."""
        assert repository is not None

    def test_repository_has_table(self, repository: OutboxRepository) -> None:
        """Repository should store the table."""
        assert repository._table is not None
        assert repository._table.name == "_outbox"


@pytest.mark.asyncio
class TestOutboxRepositoryCRUD:
    """Integration tests for OutboxRepository CRUD operations."""

    @pytest.fixture
    def sync_engine(self, tmp_path):
        """Create sync SQLite engine with outbox table."""
        db_path = tmp_path / "test_outbox.db"
        engine = create_engine(f"sqlite:///{db_path}", poolclass=NullPool)

        metadata = MetaData()
        create_outbox_table(metadata)
        metadata.create_all(engine)

        yield engine
        engine.dispose()

    @pytest.fixture
    async def async_engine(self, tmp_path):
        """Create async SQLite engine with outbox table."""
        from sqlalchemy.ext.asyncio import create_async_engine

        db_path = tmp_path / "test_outbox_async.db"
        engine = create_async_engine(
            f"sqlite+aiosqlite:///{db_path}", poolclass=NullPool
        )

        metadata = MetaData()
        create_outbox_table(metadata)

        async with engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

        yield engine
        await engine.dispose()

    @pytest.fixture
    def repository_with_engine(self, sync_engine):
        """Create repository using sync engine."""
        # Reflect the table from the engine
        metadata = MetaData()
        metadata.reflect(bind=sync_engine)
        table = metadata.tables["_outbox"]
        return OutboxRepository(table)

    async def test_add_entry(self, async_engine) -> None:
        """add() should insert entry into database."""
        from sqlalchemy import select
        from sqlalchemy.ext.asyncio import AsyncSession

        # Setup
        metadata = MetaData()
        create_outbox_table(metadata)
        table = metadata.tables["_outbox"]
        repo = OutboxRepository(table)

        entry = OutboxEntry(
            target="test.target",
            payload={"key": "value"},
        )

        async with AsyncSession(async_engine) as session:
            result = await repo.add(session, entry)
            await session.commit()

            # Verify
            assert result.id == entry.id
            assert result.target == "test.target"

            # Check in database
            stmt = select(table).where(table.c.id == entry.id)
            db_result = await session.execute(stmt)
            row = db_result.fetchone()
            assert row is not None
            assert row.target == "test.target"

    async def test_get_pending_returns_pending_entries(self, async_engine) -> None:
        """get_pending() should return only pending entries."""
        from sqlalchemy.ext.asyncio import AsyncSession

        metadata = MetaData()
        create_outbox_table(metadata)
        table = metadata.tables["_outbox"]
        repo = OutboxRepository(table)

        # Add pending and processed entries
        pending_entry = OutboxEntry(
            target="pending.target",
            payload={"type": "pending"},
            status=OutboxStatus.PENDING,
        )
        processed_entry = OutboxEntry(
            target="processed.target",
            payload={"type": "processed"},
            status=OutboxStatus.PROCESSED,
        )

        async with AsyncSession(async_engine) as session:
            await repo.add(session, pending_entry)
            await repo.add(session, processed_entry)
            await session.commit()

            # Get pending
            pending = await repo.get_pending(session)

            assert len(pending) == 1
            assert pending[0].target == "pending.target"
            assert pending[0].status == OutboxStatus.PENDING

    async def test_mark_processed_updates_status(self, async_engine) -> None:
        """mark_processed() should update status and set processed_at."""
        from sqlalchemy import select
        from sqlalchemy.ext.asyncio import AsyncSession

        metadata = MetaData()
        create_outbox_table(metadata)
        table = metadata.tables["_outbox"]
        repo = OutboxRepository(table)

        entry = OutboxEntry(
            target="to.process",
            payload={"action": "test"},
        )

        async with AsyncSession(async_engine) as session:
            await repo.add(session, entry)
            await session.commit()

            # Mark as processed
            await repo.mark_processed(session, entry.id)
            await session.commit()

            # Verify
            stmt = select(table).where(table.c.id == entry.id)
            result = await session.execute(stmt)
            row = result.fetchone()

            assert row.status == OutboxStatus.PROCESSED.value
            assert row.processed_at is not None

    async def test_mark_failed_updates_status_and_error(self, async_engine) -> None:
        """mark_failed() should update status, error_message, and increment retry_count."""
        from sqlalchemy import select
        from sqlalchemy.ext.asyncio import AsyncSession

        metadata = MetaData()
        create_outbox_table(metadata)
        table = metadata.tables["_outbox"]
        repo = OutboxRepository(table)

        entry = OutboxEntry(
            target="to.fail",
            payload={"action": "test"},
        )

        async with AsyncSession(async_engine) as session:
            await repo.add(session, entry)
            await session.commit()

            # Mark as failed
            await repo.mark_failed(session, entry.id, "Connection timeout")
            await session.commit()

            # Verify
            stmt = select(table).where(table.c.id == entry.id)
            result = await session.execute(stmt)
            row = result.fetchone()

            assert row.status == OutboxStatus.FAILED.value
            assert row.error_message == "Connection timeout"
            assert row.retry_count == 1

    async def test_get_pending_respects_limit(self, async_engine) -> None:
        """get_pending() should respect the limit parameter."""
        from sqlalchemy.ext.asyncio import AsyncSession

        metadata = MetaData()
        create_outbox_table(metadata)
        table = metadata.tables["_outbox"]
        repo = OutboxRepository(table)

        # Add 5 pending entries
        async with AsyncSession(async_engine) as session:
            for i in range(5):
                entry = OutboxEntry(
                    target=f"target.{i}",
                    payload={"index": i},
                )
                await repo.add(session, entry)
            await session.commit()

            # Get only 2
            pending = await repo.get_pending(session, limit=2)
            assert len(pending) == 2
