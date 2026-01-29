"""Tests for DocumentShare DocType.

TDD tests for the DocumentShare DocType that enables explicit
sharing of specific documents with specific users or roles.
Tests written FIRST per CONTRIBUTING.md guidelines.
"""

from framework_m.core.doctypes.document_share import DocumentShare, ShareType
from framework_m.core.domain.base_doctype import BaseDocType

# =============================================================================
# Tests for DocumentShare DocType Structure
# =============================================================================


class TestDocumentShareDocType:
    """Test DocumentShare DocType structure."""

    def test_document_share_is_doctype(self) -> None:
        """DocumentShare should be a BaseDocType."""
        assert issubclass(DocumentShare, BaseDocType)

    def test_can_create_user_share(self) -> None:
        """Can create a share for a specific user."""
        share = DocumentShare(
            name="share-001",
            doctype_name="Invoice",
            doc_id="INV-001",
            shared_with="user-456",
            share_type=ShareType.USER,
            granted_permissions=["read"],
        )

        assert share.doctype_name == "Invoice"
        assert share.doc_id == "INV-001"
        assert share.shared_with == "user-456"
        assert share.share_type == ShareType.USER
        assert share.granted_permissions == ["read"]

    def test_can_create_role_share(self) -> None:
        """Can create a share for a role."""
        share = DocumentShare(
            name="share-002",
            doctype_name="Report",
            doc_id="RPT-123",
            shared_with="Manager",
            share_type=ShareType.ROLE,
            granted_permissions=["read", "write"],
        )

        assert share.share_type == ShareType.ROLE
        assert share.shared_with == "Manager"
        assert "write" in share.granted_permissions

    def test_requires_auth(self) -> None:
        """DocumentShare should require authentication."""
        assert DocumentShare.get_requires_auth() is True

    def test_applies_rls(self) -> None:
        """DocumentShare should apply RLS (users see own shares)."""
        assert DocumentShare.get_apply_rls() is True

    def test_only_admin_can_manage_all_shares(self) -> None:
        """Admin permissions for managing all shares."""
        permissions = DocumentShare.get_permissions()

        # Read should allow users to see their own shares (RLS enforced)
        assert "Employee" in permissions.get("read", []) or "read" in permissions
        # Create/delete by owner or admin
        assert "Admin" in permissions.get("delete", [])


class TestShareTypeEnum:
    """Test ShareType enum."""

    def test_user_share_type(self) -> None:
        """USER should have correct string value."""
        assert ShareType.USER == "user"

    def test_role_share_type(self) -> None:
        """ROLE should have correct string value."""
        assert ShareType.ROLE == "role"


# =============================================================================
# Tests for DocumentShare Validation
# =============================================================================


class TestDocumentShareValidation:
    """Test DocumentShare validation logic."""

    def test_granted_permissions_default_empty(self) -> None:
        """granted_permissions should default to empty list."""
        share = DocumentShare(
            name="share-test",
            doctype_name="Invoice",
            doc_id="INV-001",
            shared_with="user-123",
            share_type=ShareType.USER,
        )

        assert share.granted_permissions == []

    def test_can_set_multiple_permissions(self) -> None:
        """Can set multiple permissions on a share."""
        share = DocumentShare(
            name="share-full",
            doctype_name="Invoice",
            doc_id="INV-001",
            shared_with="user-123",
            share_type=ShareType.USER,
            granted_permissions=["read", "write", "delete"],
        )

        assert len(share.granted_permissions) == 3
        assert "delete" in share.granted_permissions


# =============================================================================
# Tests for Share Matching Logic
# =============================================================================


class TestDocumentShareMatching:
    """Test DocumentShare matching helpers."""

    def test_matches_user_share(self) -> None:
        """User share should match the specific user."""
        share = DocumentShare(
            name="share-001",
            doctype_name="Invoice",
            doc_id="INV-001",
            shared_with="user-123",
            share_type=ShareType.USER,
            granted_permissions=["read"],
        )

        # Can check if share matches a user
        assert share.matches_user("user-123") is True
        assert share.matches_user("user-456") is False

    def test_matches_role_share(self) -> None:
        """Role share should match users with that role."""
        share = DocumentShare(
            name="share-002",
            doctype_name="Invoice",
            doc_id="INV-001",
            shared_with="Manager",
            share_type=ShareType.ROLE,
            granted_permissions=["read"],
        )

        # Can check if share matches a role
        assert share.matches_role("Manager") is True
        assert share.matches_role("Employee") is False

    def test_has_permission_check(self) -> None:
        """Can check if share grants a specific permission."""
        share = DocumentShare(
            name="share-003",
            doctype_name="Invoice",
            doc_id="INV-001",
            shared_with="user-123",
            share_type=ShareType.USER,
            granted_permissions=["read", "write"],
        )

        assert share.has_permission("read") is True
        assert share.has_permission("write") is True
        assert share.has_permission("delete") is False
