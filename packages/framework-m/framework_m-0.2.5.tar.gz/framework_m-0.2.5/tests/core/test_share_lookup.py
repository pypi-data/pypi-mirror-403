"""Tests for DocumentShare lookup integration.

TDD tests for looking up shares from the database and integrating
them with the RLS filtering system.
Tests written FIRST per CONTRIBUTING.md guidelines.
"""

from typing import ClassVar

import pytest

from framework_m.core.doctypes.document_share import DocumentShare, ShareType
from framework_m.core.domain.base_doctype import BaseDocType
from framework_m.core.interfaces.auth_context import UserContext
from framework_m.core.rls import get_rls_filters_with_shares

# =============================================================================
# Test DocTypes
# =============================================================================


class Invoice(BaseDocType):
    """Test DocType for share integration."""

    amount: float = 0.0

    class Meta:
        requires_auth: ClassVar[bool] = True
        apply_rls: ClassVar[bool] = True
        permissions: ClassVar[dict[str, list[str]]] = {
            "read": ["Employee"],
        }


# =============================================================================
# Tests for get_rls_filters_with_shares
# =============================================================================


class TestGetRlsFiltersWithShares:
    """Test RLS filters that include document shares."""

    @pytest.mark.asyncio
    async def test_includes_shared_doc_ids_for_user_share(self) -> None:
        """Should include doc IDs from user shares in filters."""
        user = UserContext(
            id="user-123",
            email="test@example.com",
            roles=["Employee"],
        )

        # Create shares that grant access
        shares = [
            DocumentShare(
                doctype_name="Invoice",
                doc_id="INV-001",
                shared_with="user-123",
                share_type=ShareType.USER,
                granted_permissions=["read"],
            ),
            DocumentShare(
                doctype_name="Invoice",
                doc_id="INV-002",
                shared_with="user-123",
                share_type=ShareType.USER,
                granted_permissions=["read"],
            ),
        ]

        filters = await get_rls_filters_with_shares(
            user=user,
            doctype="Invoice",
            shares=shares,
            action="read",
        )

        # Should have owner filter and shared_doc_ids
        assert "owner" in filters or "_shared_doc_ids" in filters
        assert filters.get("_shared_doc_ids") == ["INV-001", "INV-002"]

    @pytest.mark.asyncio
    async def test_includes_shared_doc_ids_for_role_share(self) -> None:
        """Should include doc IDs from role shares in filters."""
        user = UserContext(
            id="user-123",
            email="test@example.com",
            roles=["Manager"],
        )

        # Create role share
        shares = [
            DocumentShare(
                doctype_name="Invoice",
                doc_id="INV-003",
                shared_with="Manager",
                share_type=ShareType.ROLE,
                granted_permissions=["read"],
            ),
        ]

        filters = await get_rls_filters_with_shares(
            user=user,
            doctype="Invoice",
            shares=shares,
            action="read",
        )

        assert filters.get("_shared_doc_ids") == ["INV-003"]

    @pytest.mark.asyncio
    async def test_filters_by_action_permission(self) -> None:
        """Should only include shares that grant the requested action."""
        user = UserContext(
            id="user-123",
            email="test@example.com",
            roles=["Employee"],
        )

        shares = [
            DocumentShare(
                doctype_name="Invoice",
                doc_id="INV-001",
                shared_with="user-123",
                share_type=ShareType.USER,
                granted_permissions=["read"],  # Only read
            ),
            DocumentShare(
                doctype_name="Invoice",
                doc_id="INV-002",
                shared_with="user-123",
                share_type=ShareType.USER,
                granted_permissions=["read", "write"],  # read and write
            ),
        ]

        # Request write permission - only INV-002 should be included
        filters = await get_rls_filters_with_shares(
            user=user,
            doctype="Invoice",
            shares=shares,
            action="write",
        )

        assert filters.get("_shared_doc_ids") == ["INV-002"]

    @pytest.mark.asyncio
    async def test_empty_shares_returns_owner_filter_only(self) -> None:
        """With no shares, should return standard owner filter."""
        user = UserContext(
            id="user-123",
            email="test@example.com",
            roles=["Employee"],
        )

        filters = await get_rls_filters_with_shares(
            user=user,
            doctype="Invoice",
            shares=[],
            action="read",
        )

        # Should have owner filter, no shared_doc_ids
        assert filters.get("owner") == "user-123"
        assert "_shared_doc_ids" not in filters or filters.get("_shared_doc_ids") == []

    @pytest.mark.asyncio
    async def test_admin_bypasses_all_filters(self) -> None:
        """Admin should bypass all RLS filters."""
        user = UserContext(
            id="admin-123",
            email="admin@example.com",
            roles=["Admin"],
        )

        filters = await get_rls_filters_with_shares(
            user=user,
            doctype="Invoice",
            shares=[],
            action="read",
        )

        # Admin should have empty filters (no RLS)
        assert filters == {}
