"""Tests for Row-Level Security (RLS).

TDD tests for the RLS implementation including get_permitted_filters()
and RLS filter application in repositories.
Tests written FIRST per CONTRIBUTING.md guidelines.
"""

from typing import ClassVar

import pytest

from framework_m.adapters.auth.rbac_permission import RbacPermissionAdapter
from framework_m.core.domain.base_doctype import BaseDocType
from framework_m.core.interfaces.auth_context import UserContext
from framework_m.core.registry import MetaRegistry
from framework_m.core.rls import apply_rls_filters, get_rls_filters

# =============================================================================
# Test DocTypes
# =============================================================================


class Invoice(BaseDocType):
    """Standard DocType with RLS enabled (default)."""

    amount: float = 0.0
    customer: str = ""

    class Meta:
        requires_auth: ClassVar[bool] = True
        apply_rls: ClassVar[bool] = True
        permissions: ClassVar[dict[str, list[str]]] = {
            "read": ["Employee", "Manager", "Admin"],
        }


class Country(BaseDocType):
    """Lookup table with RLS disabled."""

    code: str = ""
    name: str = ""

    class Meta:
        requires_auth: ClassVar[bool] = True
        apply_rls: ClassVar[bool] = False  # Everyone sees all countries
        permissions: ClassVar[dict[str, list[str]]] = {
            "read": ["Employee", "Manager", "Admin"],
        }


class PublicPost(BaseDocType):
    """Public DocType with no auth but RLS for owner filtering."""

    title: str = ""
    content: str = ""

    class Meta:
        requires_auth: ClassVar[bool] = False
        apply_rls: ClassVar[bool] = True  # Only show owner's posts
        permissions: ClassVar[dict[str, list[str]]] = {}


# =============================================================================
# Tests for get_permitted_filters
# =============================================================================


class TestRbacGetPermittedFilters:
    """Test RbacPermissionAdapter.get_permitted_filters()."""

    @pytest.fixture(autouse=True)
    def setup_registry(self) -> None:
        """Register test DocTypes before each test."""
        registry = MetaRegistry.get_instance()
        registry.clear()
        registry.register_doctype(Invoice)
        registry.register_doctype(Country)
        registry.register_doctype(PublicPost)

    @pytest.mark.asyncio
    async def test_returns_owner_filter_when_rls_enabled(self) -> None:
        """When apply_rls=True, filter by owner."""
        adapter = RbacPermissionAdapter()

        filters = await adapter.get_permitted_filters(
            principal="user-123",
            principal_attributes={"roles": ["Employee"]},
            resource="Invoice",
        )

        assert filters == {"owner": "user-123"}

    @pytest.mark.asyncio
    async def test_returns_empty_when_rls_disabled(self) -> None:
        """When apply_rls=False, no RLS filters."""
        adapter = RbacPermissionAdapter()

        filters = await adapter.get_permitted_filters(
            principal="user-123",
            principal_attributes={"roles": ["Employee"]},
            resource="Country",
        )

        assert filters == {}

    @pytest.mark.asyncio
    async def test_admin_bypasses_rls(self) -> None:
        """Admin users see all, even with apply_rls=True."""
        adapter = RbacPermissionAdapter()

        filters = await adapter.get_permitted_filters(
            principal="admin-123",
            principal_attributes={"roles": ["Admin"]},
            resource="Invoice",
        )

        assert filters == {}

    @pytest.mark.asyncio
    async def test_system_user_bypasses_rls(self) -> None:
        """System users see all."""
        adapter = RbacPermissionAdapter()

        filters = await adapter.get_permitted_filters(
            principal="system",
            principal_attributes={"roles": ["System"], "is_system_user": True},
            resource="Invoice",
        )

        assert filters == {}

    @pytest.mark.asyncio
    async def test_unknown_doctype_returns_owner_filter(self) -> None:
        """Unknown DocType should still apply owner filter for safety."""
        adapter = RbacPermissionAdapter()

        filters = await adapter.get_permitted_filters(
            principal="user-123",
            principal_attributes={"roles": ["Employee"]},
            resource="NonExistentDocType",
        )

        # For safety, apply owner filter even if DocType unknown
        assert filters == {"owner": "user-123"}


# =============================================================================
# Tests for RLS Helper Functions
# =============================================================================


class TestGetRlsFilters:
    """Test the get_rls_filters() helper function."""

    @pytest.fixture(autouse=True)
    def setup_registry(self) -> None:
        """Register test DocTypes before each test."""
        registry = MetaRegistry.get_instance()
        registry.clear()
        registry.register_doctype(Invoice)
        registry.register_doctype(Country)

    @pytest.mark.asyncio
    async def test_returns_filters_for_user(self) -> None:
        """get_rls_filters returns owner filter for regular users."""
        user = UserContext(
            id="user-123",
            email="test@example.com",
            roles=["Employee"],
        )

        filters = await get_rls_filters(user, "Invoice")

        assert filters == {"owner": "user-123"}

    @pytest.mark.asyncio
    async def test_returns_empty_for_none_user(self) -> None:
        """get_rls_filters with None user returns empty (public access)."""
        filters = await get_rls_filters(None, "Country")

        assert filters == {}

    @pytest.mark.asyncio
    async def test_returns_empty_for_admin(self) -> None:
        """get_rls_filters returns empty for admin users."""
        user = UserContext(
            id="admin-123",
            email="admin@example.com",
            roles=["Admin"],
        )

        filters = await get_rls_filters(user, "Invoice")

        assert filters == {}


class TestApplyRlsFilters:
    """Test the apply_rls_filters() helper function."""

    @pytest.fixture(autouse=True)
    def setup_registry(self) -> None:
        """Register test DocTypes before each test."""
        registry = MetaRegistry.get_instance()
        registry.clear()
        registry.register_doctype(Invoice)
        registry.register_doctype(Country)

    @pytest.mark.asyncio
    async def test_merges_with_existing_filters(self) -> None:
        """apply_rls_filters merges RLS filters with existing filters."""
        from framework_m.core.interfaces.repository import FilterOperator, FilterSpec

        user = UserContext(
            id="user-123",
            email="test@example.com",
            roles=["Employee"],
        )

        existing_filters = [
            FilterSpec(field="amount", operator=FilterOperator.GT, value=100),
        ]

        merged = await apply_rls_filters(user, "Invoice", existing_filters)

        # Should have both the existing filter + owner filter
        assert len(merged) == 2
        field_names = [f.field for f in merged]
        assert "amount" in field_names
        assert "owner" in field_names

    @pytest.mark.asyncio
    async def test_no_change_when_rls_disabled(self) -> None:
        """apply_rls_filters returns original filters when RLS disabled."""
        from framework_m.core.interfaces.repository import FilterOperator, FilterSpec

        user = UserContext(
            id="user-123",
            email="test@example.com",
            roles=["Employee"],
        )

        existing_filters = [
            FilterSpec(field="name", operator=FilterOperator.EQ, value="USA"),
        ]

        merged = await apply_rls_filters(user, "Country", existing_filters)

        # No RLS filter should be added
        assert len(merged) == 1
        assert merged[0].field == "name"
