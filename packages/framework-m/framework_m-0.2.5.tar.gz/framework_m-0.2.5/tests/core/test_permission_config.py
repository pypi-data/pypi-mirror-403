"""Tests for Permission Configuration.

TDD tests for the permission configuration Meta flags and has_permission helper.
Tests written FIRST per CONTRIBUTING.md guidelines.
"""

from typing import ClassVar

import pytest

from framework_m.core.domain.base_doctype import BaseDocType
from framework_m.core.interfaces.auth_context import UserContext
from framework_m.core.interfaces.permission import PermissionAction
from framework_m.core.permissions import has_permission
from framework_m.core.registry import MetaRegistry

# =============================================================================
# Test DocTypes
# =============================================================================


class DefaultDocType(BaseDocType):
    """DocType with default Meta settings (no Meta class)."""

    title: str = ""


class ProtectedInvoice(BaseDocType):
    """DocType requiring auth with RLS."""

    amount: float = 0.0

    class Meta:
        requires_auth: ClassVar[bool] = True
        apply_rls: ClassVar[bool] = True
        permissions: ClassVar[dict[str, list[str]]] = {
            "read": ["Employee", "Manager"],
            "write": ["Manager"],
            "create": ["Manager"],
            "delete": ["Admin"],
        }


class PublicConfig(BaseDocType):
    """Public DocType (no auth, no RLS)."""

    key: str = ""
    value: str = ""

    class Meta:
        requires_auth: ClassVar[bool] = False
        apply_rls: ClassVar[bool] = False
        permissions: ClassVar[dict[str, list[str]]] = {}


class LookupTable(BaseDocType):
    """Auth required but no RLS (everyone sees everything)."""

    code: str = ""
    name: str = ""

    class Meta:
        requires_auth: ClassVar[bool] = True
        apply_rls: ClassVar[bool] = False
        permissions: ClassVar[dict[str, list[str]]] = {
            "read": ["Employee", "Manager", "Admin"],
            "write": ["Admin"],
        }


class PublicProfile(BaseDocType):
    """Public read but owner-filtered (no auth but RLS applies)."""

    username: str = ""

    class Meta:
        requires_auth: ClassVar[bool] = False
        apply_rls: ClassVar[bool] = True
        permissions: ClassVar[dict[str, list[str]]] = {
            "read": [],  # Empty means public
            "write": ["Manager"],
        }


# =============================================================================
# Tests for DocType Meta Flags
# =============================================================================


class TestDocTypeMetaFlags:
    """Test the requires_auth and apply_rls Meta flags."""

    def test_default_requires_auth_is_true(self) -> None:
        """Default value for requires_auth should be True."""
        assert DefaultDocType.get_requires_auth() is True

    def test_default_apply_rls_is_true(self) -> None:
        """Default value for apply_rls should be True."""
        assert DefaultDocType.get_apply_rls() is True

    def test_requires_auth_can_be_true(self) -> None:
        """DocType can explicitly set requires_auth=True."""
        assert ProtectedInvoice.get_requires_auth() is True

    def test_requires_auth_can_be_false(self) -> None:
        """DocType can set requires_auth=False for public access."""
        assert PublicConfig.get_requires_auth() is False

    def test_apply_rls_can_be_true(self) -> None:
        """DocType can explicitly set apply_rls=True."""
        assert ProtectedInvoice.get_apply_rls() is True

    def test_apply_rls_can_be_false(self) -> None:
        """DocType can set apply_rls=False for no row filtering."""
        assert LookupTable.get_apply_rls() is False

    def test_public_with_rls_combination(self) -> None:
        """requires_auth=False with apply_rls=True is valid."""
        assert PublicProfile.get_requires_auth() is False
        assert PublicProfile.get_apply_rls() is True


# =============================================================================
# Tests for has_permission Helper
# =============================================================================


class TestHasPermissionHelper:
    """Test the has_permission() helper function."""

    @pytest.fixture(autouse=True)
    def setup_registry(self) -> None:
        """Register test DocTypes before each test."""
        registry = MetaRegistry.get_instance()
        registry.clear()
        registry.register_doctype(ProtectedInvoice)
        registry.register_doctype(PublicConfig)
        registry.register_doctype(LookupTable)
        registry.register_doctype(PublicProfile)

    @pytest.mark.asyncio
    async def test_allows_if_role_matches(self) -> None:
        """has_permission returns True if user has matching role."""
        user = UserContext(
            id="user-123",
            email="test@example.com",
            roles=["Employee"],
        )

        result = await has_permission(
            user=user,
            doctype="ProtectedInvoice",
            action=PermissionAction.READ,
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_denies_if_role_not_matching(self) -> None:
        """has_permission returns False if user lacks required role."""
        user = UserContext(
            id="user-123",
            email="test@example.com",
            roles=["Guest"],
        )

        result = await has_permission(
            user=user,
            doctype="ProtectedInvoice",
            action=PermissionAction.READ,
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_public_doctype_allows_without_user(self) -> None:
        """Public DocType (requires_auth=False) allows access without user."""
        result = await has_permission(
            user=None,
            doctype="PublicConfig",
            action=PermissionAction.READ,
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_protected_doctype_denies_without_user(self) -> None:
        """Protected DocType (requires_auth=True) denies access without user."""
        result = await has_permission(
            user=None,
            doctype="ProtectedInvoice",
            action=PermissionAction.READ,
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_admin_always_allowed(self) -> None:
        """Admin users are always allowed."""
        user = UserContext(
            id="admin-123",
            email="admin@example.com",
            roles=["Admin"],
        )

        result = await has_permission(
            user=user,
            doctype="ProtectedInvoice",
            action=PermissionAction.DELETE,  # Admins can delete
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_string_action_works(self) -> None:
        """has_permission accepts string action."""
        user = UserContext(
            id="user-123",
            email="test@example.com",
            roles=["Employee"],
        )

        result = await has_permission(
            user=user,
            doctype="ProtectedInvoice",
            action="read",
        )

        assert result is True
