"""Audit Adapters - Audit logging implementations.

This module provides audit adapters for different backends:
- DatabaseAuditAdapter: SQL table for Indie mode (easy UI querying)
- FileAuditAdapter: JSONL file for Splunk/Filebeat/Loki (Enterprise)

Configuration in framework_config.toml:
    [audit]
    adapter = "database"  # or "file"
    file_path = "/var/log/audit.log"

Example:
    from framework_m.adapters.audit import DatabaseAuditAdapter, FileAuditAdapter

    # Indie - write to database
    audit = DatabaseAuditAdapter()

    # Enterprise - write to file for log shipping
    audit = FileAuditAdapter(file_path="/var/log/audit.log")
"""

from framework_m.adapters.audit.database_audit import DatabaseAuditAdapter
from framework_m.adapters.audit.file_audit import FileAuditAdapter

__all__ = [
    "DatabaseAuditAdapter",
    "FileAuditAdapter",
]
