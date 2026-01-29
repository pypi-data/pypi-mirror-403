"""Outbox Repository - SQL-backed repository for outbox entries.

This repository handles CRUD operations for OutboxEntry records,
enabling reliable multi-source coordination via the Outbox Pattern.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    UUID as SQLUUID,
)
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON

from framework_m.core.domain.outbox import OutboxEntry, OutboxStatus

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


# Outbox table definition
def create_outbox_table(metadata: MetaData) -> Table:
    """Create the outbox table schema.

    Args:
        metadata: SQLAlchemy MetaData instance

    Returns:
        Configured Table for outbox entries
    """
    return Table(
        "_outbox",
        metadata,
        Column("id", SQLUUID, primary_key=True),
        Column("target", String(255), nullable=False, index=True),
        Column("payload", JSON().with_variant(JSONB, "postgresql"), nullable=False),
        Column("status", String(20), nullable=False, default="pending", index=True),
        Column("created_at", DateTime(timezone=True), nullable=False),
        Column("processed_at", DateTime(timezone=True), nullable=True),
        Column("error_message", Text, nullable=True),
        Column("retry_count", Integer, nullable=False, default=0),
    )


class OutboxRepository:
    """Repository for OutboxEntry CRUD operations.

    Provides methods for adding entries to the outbox (in the same
    SQL transaction) and processing them via background workers.

    Example:
        >>> outbox_repo = OutboxRepository(outbox_table)
        >>> async with uow:
        ...     entry = OutboxEntry(target="api.webhook", payload=data)
        ...     await outbox_repo.add(uow.session, entry)
        ...     await uow.commit()  # Entry saved atomically
    """

    def __init__(self, table: Table) -> None:
        """Initialize the repository.

        Args:
            table: The outbox SQLAlchemy Table
        """
        self._table = table

    async def add(self, session: AsyncSession, entry: OutboxEntry) -> OutboxEntry:
        """Add an entry to the outbox.

        Should be called within the same transaction as primary operations.

        Args:
            session: SQLAlchemy async session
            entry: The outbox entry to add

        Returns:
            The added entry
        """
        data = {
            "id": entry.id,
            "target": entry.target,
            "payload": entry.payload,
            "status": entry.status.value,
            "created_at": entry.created_at,
            "processed_at": entry.processed_at,
            "error_message": entry.error_message,
            "retry_count": entry.retry_count,
        }
        stmt = self._table.insert().values(**data)
        await session.execute(stmt)
        return entry

    async def get_pending(
        self, session: AsyncSession, limit: int = 100
    ) -> list[OutboxEntry]:
        """Get pending outbox entries for processing.

        Args:
            session: SQLAlchemy async session
            limit: Maximum entries to retrieve

        Returns:
            List of pending outbox entries
        """
        stmt = (
            select(self._table)
            .where(self._table.c.status == OutboxStatus.PENDING.value)
            .order_by(self._table.c.created_at)
            .limit(limit)
        )
        result = await session.execute(stmt)
        rows = result.fetchall()

        entries = []
        for row in rows:
            entries.append(
                OutboxEntry(
                    id=row.id,
                    target=row.target,
                    payload=row.payload,
                    status=OutboxStatus(row.status),
                    created_at=row.created_at,
                    processed_at=row.processed_at,
                    error_message=row.error_message,
                    retry_count=row.retry_count,
                )
            )
        return entries

    async def mark_processed(self, session: AsyncSession, entry_id: UUID) -> None:
        """Mark an entry as successfully processed.

        Args:
            session: SQLAlchemy async session
            entry_id: ID of the entry to mark
        """
        stmt = (
            update(self._table)
            .where(self._table.c.id == entry_id)
            .values(
                status=OutboxStatus.PROCESSED.value,
                processed_at=datetime.now(UTC),
            )
        )
        await session.execute(stmt)

    async def mark_failed(
        self,
        session: AsyncSession,
        entry_id: UUID,
        error_message: str,
    ) -> None:
        """Mark an entry as failed with error message.

        Args:
            session: SQLAlchemy async session
            entry_id: ID of the entry to mark
            error_message: Description of the failure
        """
        # Get current retry count
        select_stmt = select(self._table.c.retry_count).where(
            self._table.c.id == entry_id
        )
        result = await session.execute(select_stmt)
        row = result.first()
        current_count = row.retry_count if row else 0

        update_stmt = (
            update(self._table)
            .where(self._table.c.id == entry_id)
            .values(
                status=OutboxStatus.FAILED.value,
                error_message=error_message,
                retry_count=current_count + 1,
            )
        )
        await session.execute(update_stmt)


__all__ = ["OutboxRepository", "create_outbox_table"]
