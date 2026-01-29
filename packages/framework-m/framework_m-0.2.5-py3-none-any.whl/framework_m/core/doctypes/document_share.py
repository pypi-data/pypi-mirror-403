"""DocumentShare DocType - Explicit document sharing.

This DocType enables sharing specific documents with specific users or roles,
providing fine-grained access control beyond owner-based RLS.

Use Cases:
- Share an Invoice with a specific colleague for review
- Grant a team leader access to all team members' reports
- Allow external auditors temporary read access to specific docs

Example:
    # Share INV-001 with user alice for read access
    share = DocumentShare(
        name="share-001",
        doctype_name="Invoice",
        doc_id="INV-001",
        shared_with="alice",
        share_type=ShareType.USER,
        granted_permissions=["read"],
    )

    # Share all Reports in the doc with Managers for read/write
    share = DocumentShare(
        name="share-002",
        doctype_name="Report",
        doc_id="RPT-123",
        shared_with="Manager",
        share_type=ShareType.ROLE,
        granted_permissions=["read", "write"],
    )
"""

from __future__ import annotations

from enum import StrEnum
from typing import ClassVar

from pydantic import Field

from framework_m.core.domain.base_doctype import BaseDocType


class ShareType(StrEnum):
    """Type of share target."""

    USER = "user"  # Shared with a specific user
    ROLE = "role"  # Shared with users having a specific role


class DocumentShare(BaseDocType):
    """Explicit share of a document with a user or role.

    Enables fine-grained document-level sharing beyond the default
    owner-based or team-based RLS.

    Attributes:
        doctype_name: The DocType being shared (e.g., "Invoice")
        doc_id: Document identifier (e.g., "INV-001" or UUID)
        shared_with: User ID or Role name to share with
        share_type: Whether sharing with USER or ROLE
        granted_permissions: List of permissions granted (e.g., ["read", "write"])
        note: Optional note explaining why the share was created
    """

    # Target document
    doctype_name: str = Field(
        description="DocType name of the shared document",
    )
    doc_id: str = Field(
        description="ID or name of the document being shared",
    )

    # Share recipient
    shared_with: str = Field(
        description="User ID or Role name to share with",
    )
    share_type: ShareType = Field(
        default=ShareType.USER,
        description="Whether sharing with a user or role",
    )

    # Permissions granted
    granted_permissions: list[str] = Field(
        default_factory=list,
        description="Permissions granted: read, write, delete, etc.",
    )

    # Optional metadata
    note: str | None = Field(
        default=None,
        description="Reason for sharing (for audit)",
    )

    class Meta:
        requires_auth: ClassVar[bool] = True
        apply_rls: ClassVar[bool] = True  # Users see shares they created
        permissions: ClassVar[dict[str, list[str]]] = {
            "read": ["Employee", "Manager", "Admin"],  # See own shares (RLS)
            "write": ["Employee", "Manager", "Admin"],  # Create own shares
            "create": ["Employee", "Manager", "Admin"],
            "delete": ["Admin"],  # Only admin can delete any share
        }

    def matches_user(self, user_id: str) -> bool:
        """Check if this share grants access to a specific user.

        Args:
            user_id: The user ID to check

        Returns:
            True if this is a USER share matching the given user ID
        """
        if self.share_type != ShareType.USER:
            return False
        return self.shared_with == user_id

    def matches_role(self, role: str) -> bool:
        """Check if this share grants access to users with a specific role.

        Args:
            role: The role name to check

        Returns:
            True if this is a ROLE share matching the given role
        """
        if self.share_type != ShareType.ROLE:
            return False
        return self.shared_with == role

    def has_permission(self, permission: str) -> bool:
        """Check if this share grants a specific permission.

        Args:
            permission: Permission to check (e.g., "read", "write")

        Returns:
            True if the share grants this permission
        """
        return permission in self.granted_permissions


__all__ = ["DocumentShare", "ShareType"]
