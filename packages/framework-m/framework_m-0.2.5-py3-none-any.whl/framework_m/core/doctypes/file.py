"""File DocType - File attachment and storage management.

This module defines the File DocType for Framework M's file management system.

The File DocType tracks metadata about uploaded files:
- Original filename and MIME type
- Storage URL (local path or S3/cloud URL)
- Attachment relationships to other DocTypes
- Privacy settings (public vs private)

Files are stored externally (never in the database) via StorageAdapter.
The File DocType only stores metadata and the storage URL.

Security:
- Private files require authentication
- Public files can be accessed without authentication
- RLS applies to private files based on owner

Example:
    file = File(
        file_name="invoice.pdf",
        file_url="/files/2024/01/05/abc123.pdf",
        file_size=102400,
        content_type="application/pdf",
        attached_to_doctype="Invoice",
        attached_to_name="INV-001",
        is_private=True,
    )
"""

from pydantic import Field

from framework_m.core.domain.base_doctype import BaseDocType


class File(BaseDocType):
    """File attachment DocType.

    Stores metadata about uploaded files. Actual file content
    is stored via StorageAdapter (local, S3, GCS, etc.).

    Attributes:
        file_name: Original filename as uploaded
        file_url: Storage URL/path for retrieval
        file_size: Size in bytes
        content_type: MIME type (e.g., "application/pdf")
        attached_to_doctype: DocType this file is attached to
        attached_to_name: Document ID this file is attached to
        is_private: If True, requires authentication to access

    Example:
        file = File(
            file_name="report.pdf",
            file_url="/files/2024/01/report-abc123.pdf",
            file_size=51200,
            content_type="application/pdf",
            is_private=True,
        )
    """

    file_name: str = Field(description="Original filename")
    file_url: str = Field(description="Storage URL/path")
    file_size: int = Field(description="File size in bytes")
    content_type: str = Field(
        default="application/octet-stream",
        description="MIME type",
    )
    attached_to_doctype: str | None = Field(
        default=None,
        description="DocType this file is attached to",
    )
    attached_to_name: str | None = Field(
        default=None,
        description="Document ID this file is attached to",
    )
    is_private: bool = Field(
        default=True,
        description="If True, requires authentication",
    )

    class Meta:
        """File DocType metadata."""

        table_name = "files"
        requires_auth = False  # Public files don't require auth
        apply_rls = True  # RLS for private files
        rls_field = "owner"

        permissions = {  # noqa: RUF012
            "read": ["Guest", "User"],  # Anyone can attempt (checked at runtime)
            "write": ["User"],
            "create": ["User"],
            "delete": ["User"],  # Can only delete own files via RLS
        }


__all__ = ["File"]
