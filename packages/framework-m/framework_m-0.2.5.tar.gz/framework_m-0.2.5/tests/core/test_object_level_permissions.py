"""Tests for Object-Level Ownership and Repository RLS Integration.

TDD tests for:
1. Object-level ownership checks in has_permission()
2. Repository methods with RLS filtering
Tests written FIRST per CONTRIBUTING.md guidelines.
"""

from typing import ClassVar
from uuid import uuid4

import pytest

from framework_m.core.domain.base_doctype import BaseDocType
from framework_m.core.exceptions import PermissionDeniedError
from framework_m.core.interfaces.auth_context import UserContext
from framework_m.core.interfaces.permission import PermissionAction
from framework_m.core.permissions import has_permission_for_doc
from framework_m.core.registry import MetaRegistry

# =============================================================================
# Test DocTypes
# =============================================================================


class Invoice(BaseDocType):
    """DocType with RLS enabled."""

    amount: float = 0.0

    class Meta:
        requires_auth: ClassVar[bool] = True
        apply_rls: ClassVar[bool] = True
        permissions: ClassVar[dict[str, list[str]]] = {
            "read": ["Employee", "Manager", "Admin"],
            "write": ["Employee", "Manager", "Admin"],
            "delete": ["Admin"],
        }


class SharedDocument(BaseDocType):
    """DocType with RLS disabled (everyone sees all)."""

    title: str = ""

    class Meta:
        requires_auth: ClassVar[bool] = True
        apply_rls: ClassVar[bool] = False
        permissions: ClassVar[dict[str, list[str]]] = {
            "read": ["Employee", "Manager"],
            "write": ["Manager"],
        }


# =============================================================================
# Tests for Object-Level Ownership
# =============================================================================


class TestHasPermissionForDoc:
    """Test has_permission_for_doc() for object-level checks."""

    @pytest.fixture(autouse=True)
    def setup_registry(self) -> None:
        """Register test DocTypes before each test."""
        registry = MetaRegistry.get_instance()
        registry.clear()
        registry.register_doctype(Invoice)
        registry.register_doctype(SharedDocument)

    @pytest.mark.asyncio
    async def test_owner_can_read_own_doc(self) -> None:
        """Owner should be able to read their own document."""
        user = UserContext(
            id="user-123",
            email="test@example.com",
            roles=["Employee"],
        )

        invoice = Invoice(
            id=uuid4(),
            owner="user-123",  # Same as user.id
            amount=100.0,
        )

        result = await has_permission_for_doc(
            user=user,
            doc=invoice,
            action=PermissionAction.READ,
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_non_owner_cannot_read_with_rls(self) -> None:
        """Non-owner should not be able to read when RLS is enabled."""
        user = UserContext(
            id="user-456",
            email="other@example.com",
            roles=["Employee"],
        )

        invoice = Invoice(
            id=uuid4(),
            owner="user-123",  # Different from user.id
            amount=100.0,
        )

        result = await has_permission_for_doc(
            user=user,
            doc=invoice,
            action=PermissionAction.READ,
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_admin_can_read_any_doc(self) -> None:
        """Admin should be able to read any document."""
        user = UserContext(
            id="admin-123",
            email="admin@example.com",
            roles=["Admin"],
        )

        invoice = Invoice(
            id=uuid4(),
            owner="user-123",  # Different owner
            amount=100.0,
        )

        result = await has_permission_for_doc(
            user=user,
            doc=invoice,
            action=PermissionAction.READ,
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_no_rls_anyone_can_read(self) -> None:
        """When RLS is disabled, any authorized user can read."""
        user = UserContext(
            id="user-456",
            email="other@example.com",
            roles=["Employee"],
        )

        doc = SharedDocument(
            id=uuid4(),
            owner="user-123",  # Different owner
            title="Shared Doc",
        )

        result = await has_permission_for_doc(
            user=user,
            doc=doc,
            action=PermissionAction.READ,
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_owner_can_write_own_doc(self) -> None:
        """Owner should be able to write to their own document."""
        user = UserContext(
            id="user-123",
            email="test@example.com",
            roles=["Employee"],
        )

        invoice = Invoice(
            id=uuid4(),
            owner="user-123",
            amount=100.0,
        )

        result = await has_permission_for_doc(
            user=user,
            doc=invoice,
            action=PermissionAction.WRITE,
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_non_owner_cannot_write_with_rls(self) -> None:
        """Non-owner should not be able to write when RLS is enabled."""
        user = UserContext(
            id="user-456",
            email="other@example.com",
            roles=["Employee"],
        )

        invoice = Invoice(
            id=uuid4(),
            owner="user-123",  # Different owner
            amount=100.0,
        )

        result = await has_permission_for_doc(
            user=user,
            doc=invoice,
            action=PermissionAction.WRITE,
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_non_admin_cannot_delete(self) -> None:
        """Non-admin cannot delete even their own doc if role not allowed."""
        user = UserContext(
            id="user-123",
            email="test@example.com",
            roles=["Employee"],  # delete requires Admin
        )

        invoice = Invoice(
            id=uuid4(),
            owner="user-123",  # Same owner
            amount=100.0,
        )

        result = await has_permission_for_doc(
            user=user,
            doc=invoice,
            action=PermissionAction.DELETE,
        )

        assert result is False


class TestRequirePermissionForDoc:
    """Test the require_permission_for_doc() helper that raises exceptions."""

    @pytest.fixture(autouse=True)
    def setup_registry(self) -> None:
        """Register test DocTypes before each test."""
        registry = MetaRegistry.get_instance()
        registry.clear()
        registry.register_doctype(Invoice)

    @pytest.mark.asyncio
    async def test_raises_permission_denied_for_non_owner(self) -> None:
        """Should raise PermissionDeniedError when access is denied."""
        from framework_m.core.permissions import require_permission_for_doc

        user = UserContext(
            id="user-456",
            email="other@example.com",
            roles=["Employee"],
        )

        invoice = Invoice(
            id=uuid4(),
            owner="user-123",
            amount=100.0,
        )

        with pytest.raises(PermissionDeniedError):
            await require_permission_for_doc(
                user=user,
                doc=invoice,
                action=PermissionAction.READ,
            )

    @pytest.mark.asyncio
    async def test_does_not_raise_for_owner(self) -> None:
        """Should not raise when owner accesses their document."""
        from framework_m.core.permissions import require_permission_for_doc

        user = UserContext(
            id="user-123",
            email="test@example.com",
            roles=["Employee"],
        )

        invoice = Invoice(
            id=uuid4(),
            owner="user-123",
            amount=100.0,
        )

        # Should not raise
        await require_permission_for_doc(
            user=user,
            doc=invoice,
            action=PermissionAction.READ,
        )
