"""Database Audit Adapter - Database-backed audit logging for Indie mode.

This module provides DatabaseAuditAdapter for writing audit logs to the
ActivityLog table in the database. Ideal for Indie mode deployments where
logs can be queried via the Admin UI.

Features:
- Stores audit entries as ActivityLog DocType records
- Easy querying via SQL and Admin UI
- No external dependencies (Elasticsearch, file shipping)

Trade-offs vs FileAuditAdapter:
- Pro: Easy to query, view in Admin UI
- Con: Database bloat for high-volume applications

Configuration in framework_config.toml:
    [audit]
    adapter = "database"

Example:
    adapter = DatabaseAuditAdapter(repository=activity_log_repo)
    await adapter.log("user-001", "create", "Invoice", "INV-001")
"""

from __future__ import annotations

from typing import Any

from framework_m.core.doctypes.activity_log import ActivityLog
from framework_m.core.interfaces.audit import AuditEntry, AuditLogProtocol


class DatabaseAuditAdapter(AuditLogProtocol):
    """Database-backed audit adapter using ActivityLog DocType.

    Writes audit entries to the ActivityLog table in the database.
    Suitable for Indie mode where audit logs are queried via UI.

    Attributes:
        _entries: In-memory storage (for testing without DB)

    Example:
        adapter = DatabaseAuditAdapter()
        await adapter.log("user-001", "create", "Todo", "TODO-001")

    Note:
        In production, this adapter would use a repository to persist
        ActivityLog records to the database. The current implementation
        uses in-memory storage for testing purposes.
    """

    def __init__(self) -> None:
        """Initialize the database audit adapter.

        TODO: Accept repository parameter for actual database persistence:
            def __init__(self, repository: RepositoryProtocol[ActivityLog])
        """
        # In-memory storage for testing (replace with repository in production)
        self._entries: list[ActivityLog] = []

    async def log(
        self,
        user_id: str,
        action: str,
        doctype: str,
        document_id: str,
        changes: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Log an audit entry to the database.

        Creates an ActivityLog record in the database.

        Args:
            user_id: ID of the user performing the action
            action: Type of action ("create", "read", "update", "delete")
            doctype: Name of the DocType
            document_id: ID of the document
            changes: Optional field changes for updates
            metadata: Optional context (request_id, ip, etc.)

        Returns:
            ID of the created audit entry
        """
        entry = ActivityLog(
            user_id=user_id,
            action=action,
            doctype=doctype,
            document_id=document_id,
            changes=changes,
            metadata=metadata,
        )

        # TODO: Use repository to persist to database
        # await self._repository.save(entry)
        self._entries.append(entry)

        return str(entry.id)

    async def query(
        self,
        filters: dict[str, Any] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditEntry]:
        """Query audit entries from the database.

        Retrieves ActivityLog records matching the given criteria.

        Args:
            filters: Optional filter criteria
            limit: Maximum entries to return
            offset: Number of entries to skip

        Returns:
            List of matching AuditEntry objects
        """
        # TODO: Use repository to query from database
        # records = await self._repository.list(filters=filters, limit=limit, offset=offset)

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
        result = result[offset : offset + limit]

        # Convert ActivityLog to AuditEntry
        return [
            AuditEntry(
                id=str(r.id),
                timestamp=r.timestamp,
                user_id=r.user_id,
                action=r.action,
                doctype=r.doctype,
                document_id=r.document_id,
                changes=r.changes,
                metadata=r.metadata,
            )
            for r in result
        ]


__all__ = ["DatabaseAuditAdapter"]
