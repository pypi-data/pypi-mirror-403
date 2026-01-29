"""Audit Log Protocol - Core interface for audit logging.

This module defines the AuditLogProtocol for recording and querying audit entries.
Supports various backends: Database (Indie), File (JSONL), Elasticsearch (Enterprise).

Audit entries are immutable records of user actions on documents.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Protocol

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(UTC)


def _generate_id() -> str:
    """Generate a unique audit entry ID."""
    from uuid import uuid4

    return str(uuid4())


class AuditEntry(BaseModel):
    """Immutable audit log entry.

    Represents a single audit record for a user action on a document.
    Once created, audit entries should never be modified or deleted.

    Attributes:
        id: Unique identifier for the entry (auto-generated)
        timestamp: When the action occurred (defaults to now, UTC)
        user_id: User who performed the action
        action: Type of action ("create", "read", "update", "delete")
        doctype: DocType name (e.g., "Invoice", "User")
        document_id: ID of the document acted upon
        changes: Field changes for updates ({"field": {"old": x, "new": y}})
        metadata: Additional context (request_id, ip_address, etc.)

    Example:
        entry = AuditEntry(
            user_id="user-001",
            action="update",
            doctype="Invoice",
            document_id="INV-001",
            changes={"status": {"old": "draft", "new": "submitted"}},
            metadata={"request_id": "req-abc", "ip": "192.168.1.1"},
        )
    """

    id: str = Field(default_factory=_generate_id)
    timestamp: datetime = Field(default_factory=_utc_now)
    user_id: str
    action: str
    doctype: str
    document_id: str
    changes: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


class AuditLogProtocol(Protocol):
    """Protocol defining the contract for audit log implementations.

    This is the primary port for audit logging in the hexagonal architecture.
    Implementations handle different storage backends.

    Implementations include:
    - DatabaseAuditAdapter: Writes to ActivityLog table (Indie mode)
    - FileAuditAdapter: Writes to JSONL file for Splunk/Filebeat
    - ElasticAuditAdapter: Writes directly to Elasticsearch

    Example usage:
        audit: AuditLogProtocol = container.get(AuditLogProtocol)

        # Log an action
        entry_id = await audit.log(
            user_id="user-001",
            action="create",
            doctype="Invoice",
            document_id="INV-001",
        )

        # Query recent actions
        entries = await audit.query(
            filters={"user_id": "user-001", "action": "update"},
            limit=50,
        )
    """

    async def log(
        self,
        user_id: str,
        action: str,
        doctype: str,
        document_id: str,
        changes: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Log an audit entry.

        Creates an immutable record of the action. This should never fail
        silently - audit logging failures should be treated seriously.

        Args:
            user_id: ID of the user performing the action
            action: Type of action ("create", "read", "update", "delete")
            doctype: Name of the DocType
            document_id: ID of the document
            changes: Optional field changes for updates
            metadata: Optional context (request_id, ip, user_agent, etc.)

        Returns:
            ID of the created audit entry
        """
        ...

    async def query(
        self,
        filters: dict[str, Any] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditEntry]:
        """Query audit entries with filters.

        Retrieves audit entries matching the given criteria.
        Results are ordered by timestamp descending (newest first).

        Args:
            filters: Optional filter criteria:
                - user_id: Filter by user
                - action: Filter by action type
                - doctype: Filter by DocType
                - document_id: Filter by specific document
                - from_timestamp: Filter entries after this time
                - to_timestamp: Filter entries before this time
            limit: Maximum entries to return (default 50, max 1000)
            offset: Number of entries to skip for pagination

        Returns:
            List of matching AuditEntry objects
        """
        ...


class InMemoryAuditAdapter:
    """In-memory implementation of AuditLogProtocol for testing.

    Stores audit entries in a list. Not suitable for production.

    Example:
        adapter = InMemoryAuditAdapter()
        entry_id = await adapter.log("user-1", "create", "Todo", "TODO-001")
    """

    def __init__(self) -> None:
        """Initialize empty audit log."""
        self._entries: list[AuditEntry] = []

    async def log(
        self,
        user_id: str,
        action: str,
        doctype: str,
        document_id: str,
        changes: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Log an audit entry to memory."""
        entry = AuditEntry(
            user_id=user_id,
            action=action,
            doctype=doctype,
            document_id=document_id,
            changes=changes,
            metadata=metadata,
        )
        self._entries.append(entry)
        return entry.id

    async def query(
        self,
        filters: dict[str, Any] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditEntry]:
        """Query audit entries from memory."""
        result = self._entries.copy()

        # Apply filters
        if filters:
            if "user_id" in filters:
                result = [e for e in result if e.user_id == filters["user_id"]]
            if "action" in filters:
                result = [e for e in result if e.action == filters["action"]]
            if "doctype" in filters:
                result = [e for e in result if e.doctype == filters["doctype"]]
            if "document_id" in filters:
                result = [e for e in result if e.document_id == filters["document_id"]]

        # Sort by timestamp descending (newest first)
        result.sort(key=lambda e: e.timestamp, reverse=True)

        # Apply pagination
        return result[offset : offset + limit]


__all__ = [
    "AuditEntry",
    "AuditLogProtocol",
    "InMemoryAuditAdapter",
]
