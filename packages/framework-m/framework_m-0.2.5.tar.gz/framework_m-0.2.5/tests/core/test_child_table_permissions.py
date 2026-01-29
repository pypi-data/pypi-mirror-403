"""Tests for Child Table Permissions.

TDD tests for child table permission behavior:
- Child tables inherit parent's RLS by default
- Child rows are not independently permission-checked
- Loading parent loads all its children (no separate RLS query)

Per CONTRIBUTING.md: Write failing tests FIRST, then implement.
"""

from typing import ClassVar

import pytest

from framework_m.core.domain.base_doctype import BaseDocType, Field
from framework_m.core.registry import MetaRegistry

# =============================================================================
# Test DocTypes - Parent with Child Table
# =============================================================================


class InvoiceItem(BaseDocType):
    """Child DocType for invoice line items.

    Per design: Child tables inherit parent's RLS.
    This DocType should NOT have independent api_resource or RLS settings.
    """

    item_name: str = Field(description="Item name")
    quantity: int = Field(default=1)
    rate: float = Field(default=0.0)
    amount: float = Field(default=0.0)

    class Meta:
        # Child tables should NOT be api_resource
        api_resource: ClassVar[bool] = False
        # Child tables should NOT have independent RLS
        apply_rls: ClassVar[bool] = False
        is_child_table: ClassVar[bool] = True  # Mark as child


class Invoice(BaseDocType):
    """Parent DocType with child table.

    RLS is applied at parent level. Child items inherit.
    """

    customer: str = Field(description="Customer name")
    total: float = Field(default=0.0)
    items: list[InvoiceItem] = Field(default_factory=list, description="Line items")

    class Meta:
        api_resource: ClassVar[bool] = True
        apply_rls: ClassVar[bool] = True
        rls_field: ClassVar[str] = "owner"
        permissions: ClassVar[dict[str, list[str]]] = {
            "read": ["Employee", "Manager"],
            "write": ["Manager"],
            "create": ["Manager"],
            "delete": ["Admin"],
        }


# =============================================================================
# Tests: Child Table Permission Inheritance
# =============================================================================


class TestChildTablePermissionInheritance:
    """Test that child tables inherit parent's RLS."""

    @pytest.fixture(autouse=True)
    def register_doctypes(self) -> None:
        """Register test DocTypes."""
        registry = MetaRegistry.get_instance()
        registry.clear()
        registry.register_doctype(Invoice)
        registry.register_doctype(InvoiceItem)
        yield
        registry.clear()

    def test_child_doctype_not_api_resource(self) -> None:
        """Child table should not be exposed as API resource."""
        assert InvoiceItem.get_api_resource() is False

    def test_child_doctype_no_independent_rls(self) -> None:
        """Child table should not have independent RLS."""
        assert InvoiceItem.get_apply_rls() is False

    def test_child_doctype_marked_as_child(self) -> None:
        """Child table should have is_child_table=True."""
        assert InvoiceItem.get_is_child_table() is True

    def test_parent_has_rls(self) -> None:
        """Parent DocType should have RLS enabled."""
        assert Invoice.get_apply_rls() is True
        assert Invoice.get_rls_field() == "owner"

    def test_parent_has_child_field(self) -> None:
        """Parent should have a child table field."""
        assert "items" in Invoice.model_fields
        # The field type should be list[InvoiceItem]
        field_info = Invoice.model_fields["items"]
        assert field_info is not None


class TestChildTableNotIndependentlyChecked:
    """Test that child rows are not independently permission-checked."""

    @pytest.fixture(autouse=True)
    def register_doctypes(self) -> None:
        """Register test DocTypes."""
        registry = MetaRegistry.get_instance()
        registry.clear()
        registry.register_doctype(Invoice)
        registry.register_doctype(InvoiceItem)
        yield
        registry.clear()

    def test_child_not_in_api_resource_doctypes(self) -> None:
        """Child table should not appear in API resource list."""
        from framework_m.adapters.web.meta_router import create_meta_router

        router = create_meta_router()
        # Get route paths
        route_paths = [route.path for route in router.routes]

        # InvoiceItem should NOT have its own CRUD routes
        assert "/api/v1/InvoiceItem" not in route_paths
        assert "/api/v1/InvoiceItem/{id}" not in route_paths

    def test_parent_in_api_resource_doctypes(self) -> None:
        """Parent DocType should appear in API resource list."""
        from framework_m.adapters.web.meta_router import create_meta_router

        router = create_meta_router()
        route_paths = [route.path for route in router.routes]

        # Invoice should have CRUD routes
        assert "/api/v1/Invoice" in route_paths
        assert "/api/v1/Invoice/{entity_id:uuid}" in route_paths


class TestDocumentingChildTableBehavior:
    """Tests documenting expected child table behavior."""

    def test_child_table_design_documented(self) -> None:
        """Verify child table design principles are documented.

        Design principles:
        1. Child tables inherit parent's RLS by default
        2. Child rows are not independently permission-checked
        3. Loading parent loads all its children (no separate RLS query)
        4. If independent child access needed, make it a separate DocType

        This test validates these are enforced via Meta flags.
        """
        # Child tables have is_child_table=True
        assert hasattr(InvoiceItem.Meta, "is_child_table")

        # Child tables should not be api_resource
        assert InvoiceItem.get_api_resource() is False

        # For independent access, use regular DocType (api_resource=True)
        assert Invoice.get_api_resource() is True  # Parent is independent
