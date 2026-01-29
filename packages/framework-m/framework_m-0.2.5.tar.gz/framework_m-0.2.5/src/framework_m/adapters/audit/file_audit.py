"""File Audit Adapter - JSONL file-based audit logging.

This module provides FileAuditAdapter for writing audit logs to JSONL files.
Ideal for Enterprise mode where logs are shipped to Splunk/Filebeat/Loki.

Features:
- Append-only JSONL format (one JSON object per line)
- Async file writes with buffering
- Log rotation support via external tools (logrotate)
- No database bloat

Configuration in framework_config.toml:
    [audit]
    adapter = "file"
    file_path = "/var/log/framework_m/audit.log"

Example:
    adapter = FileAuditAdapter(file_path="/var/log/audit.log")
    await adapter.log("user-001", "create", "Invoice", "INV-001")
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import aiofiles  # type: ignore[import-untyped]

from framework_m.core.interfaces.audit import AuditEntry, AuditLogProtocol


class FileAuditAdapter(AuditLogProtocol):
    """JSONL file-based audit adapter.

    Writes audit entries as JSON lines to a file. Each line is a complete
    JSON object representing one AuditEntry.

    Format (JSONL):
        {"id": "...", "timestamp": "...", "user_id": "...", ...}
        {"id": "...", "timestamp": "...", "user_id": "...", ...}

    Attributes:
        file_path: Path to the audit log file

    Example:
        adapter = FileAuditAdapter(file_path="./audit.log")
        await adapter.log("user-001", "create", "Todo", "TODO-001")

    Note:
        Query operations require reading the entire file and are
        inefficient for large logs. Use Elasticsearch for query-heavy
        workloads.
    """

    def __init__(self, file_path: str = "./audit.log") -> None:
        """Initialize the file audit adapter.

        Args:
            file_path: Path to the log file (created if not exists)
        """
        self._file_path = Path(file_path)
        # Ensure parent directory exists
        self._file_path.parent.mkdir(parents=True, exist_ok=True)

    async def log(
        self,
        user_id: str,
        action: str,
        doctype: str,
        document_id: str,
        changes: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Log an audit entry to the file.

        Appends a JSON line to the audit log file.

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
        entry = AuditEntry(
            user_id=user_id,
            action=action,
            doctype=doctype,
            document_id=document_id,
            changes=changes,
            metadata=metadata,
        )

        # Convert to JSON line (timestamp as ISO format)
        json_line = entry.model_dump_json() + "\n"

        # Append to file
        async with aiofiles.open(self._file_path, mode="a", encoding="utf-8") as f:
            await f.write(json_line)

        return entry.id

    async def query(
        self,
        filters: dict[str, Any] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditEntry]:
        """Query audit entries from the file.

        Reads and filters entries from the log file.
        Note: This is inefficient for large files - use Elasticsearch
        adapter for query-heavy workloads.

        Args:
            filters: Optional filter criteria
            limit: Maximum entries to return
            offset: Number of entries to skip

        Returns:
            List of matching AuditEntry objects
        """
        if not self._file_path.exists():
            return []

        entries: list[AuditEntry] = []

        # Read all entries
        async with aiofiles.open(self._file_path, encoding="utf-8") as f:
            async for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    entries.append(AuditEntry.model_validate(data))
                except (json.JSONDecodeError, ValueError):
                    # Skip malformed lines
                    continue

        # Apply filters
        if filters:
            if "user_id" in filters:
                entries = [e for e in entries if e.user_id == filters["user_id"]]
            if "action" in filters:
                entries = [e for e in entries if e.action == filters["action"]]
            if "doctype" in filters:
                entries = [e for e in entries if e.doctype == filters["doctype"]]
            if "document_id" in filters:
                entries = [
                    e for e in entries if e.document_id == filters["document_id"]
                ]

        # Sort by timestamp descending (newest first)
        entries.sort(key=lambda e: e.timestamp, reverse=True)

        # Apply pagination
        return entries[offset : offset + limit]


__all__ = ["FileAuditAdapter"]
