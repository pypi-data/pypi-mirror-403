"""Tests for RbacPermissionAdapter.

TDD tests for the Role-Based Access Control permission adapter.
Tests written FIRST per CONTRIBUTING.md guidelines.
"""

from typing import Any, ClassVar

import pytest

from framework_m.adapters.auth.rbac_permission import RbacPermissionAdapter
from framework_m.core.domain.base_doctype import BaseDocType
from framework_m.core.interfaces.permission import (
    DecisionSource,
    PermissionAction,
    PolicyEvaluateRequest,
)
from framework_m.core.registry import MetaRegistry

# =============================================================================
# Test DocTypes for Testing Permissions
# =============================================================================


class Invoice(BaseDocType):
    """Test DocType with permissions."""

    amount: float = 0.0

    class Meta:
        permissions: ClassVar[dict[str, list[str]]] = {
            "read": ["Employee", "Manager", "Admin"],
            "write": ["Manager", "Admin"],
            "create": ["Manager", "Admin"],
            "delete": ["Admin"],
            "submit": ["Manager", "Admin"],
        }


class PublicAnnouncement(BaseDocType):
    """Test DocType requiring no auth."""

    title: str = ""

    class Meta:
        requires_auth = False
        apply_rls = False
        permissions: ClassVar[dict[str, Any]] = {}  # No role restrictions


class PrivateDocument(BaseDocType):
    """Test DocType with strict access."""

    content: str = ""

    class Meta:
        permissions: ClassVar[dict[str, list[str]]] = {
            "read": ["Admin"],
            "write": ["Admin"],
            "create": ["Admin"],
            "delete": ["Admin"],
        }


# =============================================================================
# Tests
# =============================================================================


class TestRbacPermissionAdapterEvaluate:
    """Test the evaluate() method."""

    @pytest.fixture(autouse=True)
    def setup_registry(self) -> None:
        """Register test DocTypes before each test."""
        registry = MetaRegistry.get_instance()
        registry.clear()
        registry.register_doctype(Invoice)
        registry.register_doctype(PublicAnnouncement)
        registry.register_doctype(PrivateDocument)

    @pytest.mark.asyncio
    async def test_allows_read_when_role_matches(self) -> None:
        """User with matching role should be authorized for read."""
        adapter = RbacPermissionAdapter()

        request = PolicyEvaluateRequest(
            principal="user-123",
            action=PermissionAction.READ,
            resource="Invoice",
            principal_attributes={"roles": ["Employee"]},
        )

        result = await adapter.evaluate(request)

        assert result.authorized is True
        assert result.decision_source == DecisionSource.RBAC

    @pytest.mark.asyncio
    async def test_denies_read_when_role_not_matching(self) -> None:
        """User without matching role should be denied."""
        adapter = RbacPermissionAdapter()

        request = PolicyEvaluateRequest(
            principal="user-123",
            action=PermissionAction.READ,
            resource="Invoice",
            principal_attributes={"roles": ["Guest"]},  # Not in read roles
        )

        result = await adapter.evaluate(request)

        assert result.authorized is False
        assert result.decision_source == DecisionSource.RBAC
        assert result.reason is not None

    @pytest.mark.asyncio
    async def test_allows_write_for_manager(self) -> None:
        """Manager should be able to write."""
        adapter = RbacPermissionAdapter()

        request = PolicyEvaluateRequest(
            principal="user-123",
            action=PermissionAction.WRITE,
            resource="Invoice",
            principal_attributes={"roles": ["Manager"]},
        )

        result = await adapter.evaluate(request)

        assert result.authorized is True

    @pytest.mark.asyncio
    async def test_denies_write_for_employee(self) -> None:
        """Employee should not be able to write."""
        adapter = RbacPermissionAdapter()

        request = PolicyEvaluateRequest(
            principal="user-123",
            action=PermissionAction.WRITE,
            resource="Invoice",
            principal_attributes={"roles": ["Employee"]},
        )

        result = await adapter.evaluate(request)

        assert result.authorized is False

    @pytest.mark.asyncio
    async def test_allows_delete_only_for_admin(self) -> None:
        """Only Admin should be able to delete."""
        adapter = RbacPermissionAdapter()

        # Admin can delete
        admin_request = PolicyEvaluateRequest(
            principal="admin-123",
            action=PermissionAction.DELETE,
            resource="Invoice",
            principal_attributes={"roles": ["Admin"]},
        )
        result = await adapter.evaluate(admin_request)
        assert result.authorized is True

        # Manager cannot delete
        manager_request = PolicyEvaluateRequest(
            principal="manager-123",
            action=PermissionAction.DELETE,
            resource="Invoice",
            principal_attributes={"roles": ["Manager"]},
        )
        result = await adapter.evaluate(manager_request)
        assert result.authorized is False

    @pytest.mark.asyncio
    async def test_multiple_roles_any_match(self) -> None:
        """User with multiple roles should match if any role is allowed."""
        adapter = RbacPermissionAdapter()

        request = PolicyEvaluateRequest(
            principal="user-123",
            action=PermissionAction.DELETE,
            resource="Invoice",
            principal_attributes={"roles": ["Employee", "Admin"]},  # Admin can delete
        )

        result = await adapter.evaluate(request)

        assert result.authorized is True

    @pytest.mark.asyncio
    async def test_doctype_not_found_denies(self) -> None:
        """Unknown DocType should result in denied access."""
        adapter = RbacPermissionAdapter()

        request = PolicyEvaluateRequest(
            principal="user-123",
            action=PermissionAction.READ,
            resource="NonExistentDocType",
            principal_attributes={"roles": ["Employee"]},  # Non-admin role
        )

        result = await adapter.evaluate(request)

        assert result.authorized is False
        assert "not found" in (result.reason or "").lower()

    @pytest.mark.asyncio
    async def test_action_not_defined_denies(self) -> None:
        """Action not defined in permissions should be denied."""
        adapter = RbacPermissionAdapter()

        request = PolicyEvaluateRequest(
            principal="user-123",
            action=PermissionAction.AMEND,  # Not defined in Invoice
            resource="Invoice",
            principal_attributes={"roles": ["Manager"]},  # Non-admin role
        )

        result = await adapter.evaluate(request)

        assert result.authorized is False

    @pytest.mark.asyncio
    async def test_empty_roles_denied(self) -> None:
        """User with no roles should be denied (except for public DocTypes)."""
        adapter = RbacPermissionAdapter()

        request = PolicyEvaluateRequest(
            principal="user-123",
            action=PermissionAction.READ,
            resource="Invoice",
            principal_attributes={"roles": []},
        )

        result = await adapter.evaluate(request)

        assert result.authorized is False

    @pytest.mark.asyncio
    async def test_string_action_works(self) -> None:
        """String action should work same as enum."""
        adapter = RbacPermissionAdapter()

        request = PolicyEvaluateRequest(
            principal="user-123",
            action="read",  # String instead of enum
            resource="Invoice",
            principal_attributes={"roles": ["Employee"]},
        )

        result = await adapter.evaluate(request)

        assert result.authorized is True


class TestRbacPermissionAdapterGetPermittedFilters:
    """Test the get_permitted_filters() method for RLS."""

    @pytest.fixture(autouse=True)
    def setup_registry(self) -> None:
        """Register test DocTypes before each test."""
        registry = MetaRegistry.get_instance()
        registry.clear()
        registry.register_doctype(Invoice)

    @pytest.mark.asyncio
    async def test_returns_owner_filter_by_default(self) -> None:
        """Should return owner filter for regular users."""
        adapter = RbacPermissionAdapter()

        filters = await adapter.get_permitted_filters(
            principal="user-123",
            principal_attributes={"roles": ["Employee"]},
            resource="Invoice",
        )

        # Default RLS: filter by owner
        assert "owner" in filters
        assert filters["owner"] == "user-123"

    @pytest.mark.asyncio
    async def test_admin_gets_no_filters(self) -> None:
        """Admin users should get empty filters (see everything)."""
        adapter = RbacPermissionAdapter()

        filters = await adapter.get_permitted_filters(
            principal="admin-123",
            principal_attributes={"roles": ["Admin"]},
            resource="Invoice",
        )

        # Admin sees all
        assert filters == {}

    @pytest.mark.asyncio
    async def test_system_user_gets_no_filters(self) -> None:
        """System users should get empty filters."""
        adapter = RbacPermissionAdapter()

        filters = await adapter.get_permitted_filters(
            principal="system",
            principal_attributes={"roles": ["System"], "is_system_user": True},
            resource="Invoice",
        )

        assert filters == {}
