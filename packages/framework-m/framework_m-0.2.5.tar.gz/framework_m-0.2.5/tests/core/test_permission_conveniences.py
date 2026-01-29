"""Tests for Indie Mode Permission Conveniences.

TDD tests for @requires_permission decorator and check_permission helper.
Tests written FIRST per CONTRIBUTING.md guidelines.

0-Cliff Principle: These helpers internally construct PolicyEvaluateRequest.
Indie devs get simplicity; enterprise devs can use the full API when needed.
"""

from typing import ClassVar

import pytest

from framework_m.adapters.auth.rbac_permission import RbacPermissionAdapter
from framework_m.core.domain.base_controller import BaseController
from framework_m.core.domain.base_doctype import BaseDocType
from framework_m.core.exceptions import PermissionDeniedError
from framework_m.core.interfaces.auth_context import UserContext
from framework_m.core.interfaces.permission import PermissionAction
from framework_m.core.registry import MetaRegistry

# =============================================================================
# Test DocType and Controller
# =============================================================================


class Invoice(BaseDocType):
    """Test DocType for permission convenience tests."""

    amount: float = 0.0

    class Meta:
        requires_auth: ClassVar[bool] = True
        permissions: ClassVar[dict[str, list[str]]] = {
            "read": ["Employee", "Manager"],
            "write": ["Manager"],
            "create": ["Manager"],
            "delete": ["Admin"],
        }


class InvoiceController(BaseController[Invoice]):
    """Controller with permission convenience methods."""

    pass


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def register_invoice_doctype() -> None:
    """Register Invoice DocType in MetaRegistry for all tests."""
    registry = MetaRegistry.get_instance()
    try:
        registry.get_doctype("Invoice")
    except KeyError:
        registry.register_doctype(Invoice)


# =============================================================================
# Tests for @requires_permission Decorator
# =============================================================================


class TestRequiresPermissionDecorator:
    """Test @requires_permission decorator."""

    def test_decorator_is_importable(self) -> None:
        """requires_permission should be importable."""
        from framework_m.core.decorators import requires_permission

        assert requires_permission is not None

    @pytest.mark.asyncio
    async def test_allows_authorized_user(self) -> None:
        """Decorated method should execute if user is authorized."""
        from framework_m.core.decorators import requires_permission

        class TestController(BaseController[Invoice]):
            user: UserContext = UserContext(
                id="user-123",
                email="test@example.com",
                roles=["Manager"],
            )
            doctype_name: str = "Invoice"

            @requires_permission(PermissionAction.WRITE)
            async def update_amount(self, new_amount: float) -> float:
                return new_amount * 2

        controller = TestController(Invoice(amount=100))
        result = await controller.update_amount(50)
        assert result == 100

    @pytest.mark.asyncio
    async def test_raises_for_unauthorized_user(self) -> None:
        """Decorated method should raise PermissionDeniedError if not authorized."""
        from framework_m.core.decorators import requires_permission

        class TestController(BaseController[Invoice]):
            user: UserContext = UserContext(
                id="user-123",
                email="test@example.com",
                roles=["Employee"],  # Employee can't write
            )
            doctype_name: str = "Invoice"

            @requires_permission(PermissionAction.WRITE)
            async def update_amount(self, new_amount: float) -> float:
                return new_amount * 2

        controller = TestController(Invoice(amount=100))
        with pytest.raises(PermissionDeniedError):
            await controller.update_amount(50)

    @pytest.mark.asyncio
    async def test_decorator_with_read_action(self) -> None:
        """Decorator should work with READ action."""
        from framework_m.core.decorators import requires_permission

        class TestController(BaseController[Invoice]):
            user: UserContext = UserContext(
                id="user-123",
                email="test@example.com",
                roles=["Employee"],  # Employee can read
            )
            doctype_name: str = "Invoice"

            @requires_permission(PermissionAction.READ)
            async def get_details(self) -> str:
                return "Invoice details"

        controller = TestController(Invoice(amount=100))
        result = await controller.get_details()
        assert result == "Invoice details"


# =============================================================================
# Tests for check_permission Helper
# =============================================================================


class TestCheckPermissionHelper:
    """Test check_permission() helper in BaseController."""

    @pytest.mark.asyncio
    async def test_returns_true_for_authorized(self) -> None:
        """check_permission should return True for authorized user."""

        class TestController(BaseController[Invoice]):
            user: UserContext = UserContext(
                id="user-123",
                email="test@example.com",
                roles=["Manager"],
            )
            doctype_name: str = "Invoice"
            permission = RbacPermissionAdapter()

        controller = TestController(Invoice(amount=100))
        result = await controller.check_permission("write")
        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_for_unauthorized(self) -> None:
        """check_permission should return False for unauthorized user."""

        class TestController(BaseController[Invoice]):
            user: UserContext = UserContext(
                id="user-123",
                email="test@example.com",
                roles=["Employee"],  # Employee can't write
            )
            doctype_name: str = "Invoice"
            permission = RbacPermissionAdapter()

        controller = TestController(Invoice(amount=100))
        result = await controller.check_permission("write")
        assert result is False

    @pytest.mark.asyncio
    async def test_with_doc_id(self) -> None:
        """check_permission should accept optional doc_id."""

        class TestController(BaseController[Invoice]):
            user: UserContext = UserContext(
                id="user-123",
                email="test@example.com",
                roles=["Manager"],
            )
            doctype_name: str = "Invoice"
            permission = RbacPermissionAdapter()

        controller = TestController(Invoice(amount=100))
        result = await controller.check_permission("read", doc_id="INV-001")
        assert result is True


# =============================================================================
# Tests for require_permission Helper
# =============================================================================


class TestRequirePermissionHelper:
    """Test require_permission() helper that raises on failure."""

    @pytest.mark.asyncio
    async def test_does_not_raise_for_authorized(self) -> None:
        """require_permission should not raise for authorized user."""

        class TestController(BaseController[Invoice]):
            user: UserContext = UserContext(
                id="user-123",
                email="test@example.com",
                roles=["Manager"],
            )
            doctype_name: str = "Invoice"
            permission = RbacPermissionAdapter()

        controller = TestController(Invoice(amount=100))
        # Should not raise
        await controller.require_permission("write")

    @pytest.mark.asyncio
    async def test_raises_for_unauthorized(self) -> None:
        """require_permission should raise PermissionDeniedError for unauthorized."""

        class TestController(BaseController[Invoice]):
            user: UserContext = UserContext(
                id="user-123",
                email="test@example.com",
                roles=["Employee"],
            )
            doctype_name: str = "Invoice"
            permission = RbacPermissionAdapter()

        controller = TestController(Invoice(amount=100))
        with pytest.raises(PermissionDeniedError):
            await controller.require_permission("write")


# =============================================================================
# Tests for has_permission Function
# =============================================================================


class TestHasPermissionFunction:
    """Test has_permission() convenience function."""

    @pytest.mark.asyncio
    async def test_has_permission_is_importable(self) -> None:
        """has_permission should be importable."""
        from framework_m.core.permissions import has_permission

        assert has_permission is not None

    @pytest.mark.asyncio
    async def test_has_permission_returns_false_for_unknown_doctype(self) -> None:
        """has_permission should return False for unknown DocType."""
        from framework_m.core.permissions import has_permission

        result = await has_permission(
            UserContext(id="user-1", email="test@example.com", roles=["Admin"]),
            "NonExistentDocType",
            "read",
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_has_permission_with_authorized_user(self) -> None:
        """has_permission should return True for authorized user."""
        from framework_m.core.permissions import has_permission

        result = await has_permission(
            UserContext(id="user-1", email="test@example.com", roles=["Manager"]),
            "Invoice",
            "read",
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_has_permission_with_unauthorized_user(self) -> None:
        """has_permission should return False for unauthorized user."""
        from framework_m.core.permissions import has_permission

        result = await has_permission(
            UserContext(id="user-1", email="test@example.com", roles=["Guest"]),
            "Invoice",
            "delete",
        )
        assert result is False
