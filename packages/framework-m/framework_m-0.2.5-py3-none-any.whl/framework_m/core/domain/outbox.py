"""Outbox Pattern - Reliable multi-source coordination.

The Outbox Pattern ensures reliable coordination between SQL database
operations and external systems (MongoDB, APIs, message queues, etc.)
by storing pending operations in the same SQL transaction.

Use Case:
    When a service needs to update both SQL and another data source,
    write to Outbox in the same transaction. A background worker
    (Phase 04) processes entries and forwards to external systems.

Example:
    async with UnitOfWork(session_factory) as uow:
        # Primary SQL operation
        await repo.save(uow.session, entity)

        # Queue external operation in same transaction
        outbox_entry = OutboxEntry(
            target="mongodb.audit_log",
            payload={"action": "create", "entity_id": str(entity.id)}
        )
        await outbox_repo.add(uow.session, outbox_entry)

        await uow.commit()  # Both saved atomically
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(UTC)


class OutboxStatus(str, Enum):
    """Status of an outbox entry.

    Attributes:
        PENDING: Entry waiting to be processed
        PROCESSED: Entry successfully processed
        FAILED: Entry failed to process (may be retried)
    """

    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"


class OutboxEntry(BaseModel):
    """An entry in the transactional outbox.

    Outbox entries represent pending operations to external systems
    that are stored in SQL for reliable, transactional delivery.

    Attributes:
        id: Unique identifier for the entry
        target: Target system identifier (e.g., "mongodb.audit_log")
        payload: JSON payload to deliver to target
        status: Current processing status
        created_at: When the entry was created
        processed_at: When the entry was processed (None if pending)
        error_message: Error message if failed (None otherwise)
        retry_count: Number of retry attempts
    """

    id: UUID = Field(default_factory=uuid4)
    target: str = Field(description="Target system (e.g., 'mongodb.audit_log')")
    payload: dict[str, Any] = Field(description="JSON payload for target")
    status: OutboxStatus = Field(default=OutboxStatus.PENDING)
    created_at: datetime = Field(default_factory=_utc_now)
    processed_at: datetime | None = Field(default=None)
    error_message: str | None = Field(default=None)
    retry_count: int = Field(default=0)

    model_config = {"frozen": False}


__all__ = ["OutboxEntry", "OutboxStatus"]
