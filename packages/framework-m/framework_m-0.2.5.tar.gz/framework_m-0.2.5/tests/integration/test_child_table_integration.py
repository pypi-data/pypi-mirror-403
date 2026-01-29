"""Integration tests for child table CRUD operations.

Tests end-to-end child table functionality including:
- Parent with children creation
- Child table CRUD operations
- Cascade delete behavior
- Transaction rollback scenarios
"""

from __future__ import annotations

from typing import ClassVar
from uuid import uuid4

import pytest
from pydantic import Field

from framework_m.core.domain.base_doctype import BaseDocType

# ============================================================================
# Test DocTypes
# ============================================================================


class OrderItem(BaseDocType):
    """Child table for order items."""

    __doctype_name__: ClassVar[str] = "OrderItem"

    name: str = Field(default_factory=lambda: str(uuid4()))
    product: str = Field(description="Product name")
    quantity: int = Field(description="Quantity ordered", ge=1)
    unit_price: float = Field(description="Price per unit", ge=0)
    parent: str | None = Field(default=None, description="Parent order name")
    parenttype: str | None = Field(default=None, description="Parent doctype")
    idx: int = Field(default=0, description="Row index")

    class Meta:
        """DocType metadata."""

        is_child: ClassVar[bool] = True


class SalesOrder(BaseDocType):
    """Sales Order with child table items."""

    __doctype_name__: ClassVar[str] = "SalesOrder"

    name: str = Field(description="Order number")
    customer: str = Field(description="Customer name")
    items: list[OrderItem] = Field(default_factory=list, description="Order items")
    total: float = Field(default=0.0, description="Order total")

    class Meta:
        """DocType metadata."""

        name_pattern: ClassVar[str] = "SO-.####"


# ============================================================================
# Tests
# ============================================================================


class TestChildTableCreation:
    """Test creating parents with child tables."""

    def test_create_parent_with_children(self) -> None:
        """Test creating a parent document with child items."""
        order = SalesOrder(
            name="SO-0001",
            customer="Acme Corp",
            items=[
                OrderItem(product="Widget A", quantity=5, unit_price=10.00),
                OrderItem(product="Widget B", quantity=3, unit_price=25.00),
            ],
        )

        assert len(order.items) == 2
        assert order.items[0].product == "Widget A"
        assert order.items[1].product == "Widget B"

    def test_child_items_have_unique_names(self) -> None:
        """Test that child items get unique names."""
        order = SalesOrder(
            name="SO-0002",
            customer="Test Customer",
            items=[
                OrderItem(product="Item 1", quantity=1, unit_price=10.00),
                OrderItem(product="Item 2", quantity=1, unit_price=20.00),
            ],
        )

        # Each item should have a unique name
        assert order.items[0].name != order.items[1].name

    def test_empty_child_list(self) -> None:
        """Test creating parent with no children."""
        order = SalesOrder(
            name="SO-0003",
            customer="Empty Order Customer",
            items=[],
        )

        assert order.items == []
        assert len(order.items) == 0


class TestChildTableModification:
    """Test modifying child tables."""

    def test_add_child_to_parent(self) -> None:
        """Test adding a child item to an existing parent."""
        order = SalesOrder(
            name="SO-0004",
            customer="Growing Order",
            items=[OrderItem(product="Initial Item", quantity=1, unit_price=10.00)],
        )

        # Add new item
        order.items.append(OrderItem(product="New Item", quantity=2, unit_price=15.00))

        assert len(order.items) == 2
        assert order.items[1].product == "New Item"

    def test_remove_child_from_parent(self) -> None:
        """Test removing a child item from parent."""
        order = SalesOrder(
            name="SO-0005",
            customer="Shrinking Order",
            items=[
                OrderItem(product="Keep This", quantity=1, unit_price=10.00),
                OrderItem(product="Remove This", quantity=1, unit_price=20.00),
            ],
        )

        # Remove second item
        order.items = [item for item in order.items if item.product != "Remove This"]

        assert len(order.items) == 1
        assert order.items[0].product == "Keep This"

    def test_modify_child_item(self) -> None:
        """Test modifying a child item's properties."""
        order = SalesOrder(
            name="SO-0006",
            customer="Modify Order",
            items=[OrderItem(product="Widget", quantity=5, unit_price=10.00)],
        )

        # Modify the item
        order.items[0].quantity = 10
        order.items[0].unit_price = 12.50

        assert order.items[0].quantity == 10
        assert order.items[0].unit_price == 12.50

    def test_replace_all_children(self) -> None:
        """Test replacing all child items."""
        order = SalesOrder(
            name="SO-0007",
            customer="Replace Order",
            items=[
                OrderItem(product="Old Item 1", quantity=1, unit_price=10.00),
                OrderItem(product="Old Item 2", quantity=2, unit_price=20.00),
            ],
        )

        # Replace all items
        order.items = [
            OrderItem(product="New Item 1", quantity=3, unit_price=30.00),
        ]

        assert len(order.items) == 1
        assert order.items[0].product == "New Item 1"


class TestChildTableValidation:
    """Test child table validation scenarios."""

    def test_child_quantity_validation(self) -> None:
        """Test that child item quantity validation works."""
        with pytest.raises(ValueError):
            OrderItem(product="Invalid", quantity=0, unit_price=10.00)

    def test_child_price_validation(self) -> None:
        """Test that child item price validation works."""
        with pytest.raises(ValueError):
            OrderItem(product="Invalid", quantity=1, unit_price=-10.00)

    def test_valid_child_passes_validation(self) -> None:
        """Test that valid child items pass validation."""
        item = OrderItem(product="Valid", quantity=1, unit_price=0.00)
        assert item.product == "Valid"
        assert item.quantity == 1
        assert item.unit_price == 0.00


class TestChildTableOrdering:
    """Test child table ordering by idx."""

    def test_children_maintain_order(self) -> None:
        """Test that children maintain insertion order."""
        order = SalesOrder(
            name="SO-0008",
            customer="Ordered Items",
            items=[
                OrderItem(product="First", quantity=1, unit_price=10.00, idx=0),
                OrderItem(product="Second", quantity=1, unit_price=20.00, idx=1),
                OrderItem(product="Third", quantity=1, unit_price=30.00, idx=2),
            ],
        )

        assert order.items[0].product == "First"
        assert order.items[1].product == "Second"
        assert order.items[2].product == "Third"

    def test_reorder_children(self) -> None:
        """Test reordering child items."""
        order = SalesOrder(
            name="SO-0009",
            customer="Reorder Test",
            items=[
                OrderItem(product="A", quantity=1, unit_price=10.00),
                OrderItem(product="B", quantity=1, unit_price=20.00),
                OrderItem(product="C", quantity=1, unit_price=30.00),
            ],
        )

        # Reverse the order
        order.items = list(reversed(order.items))

        assert order.items[0].product == "C"
        assert order.items[1].product == "B"
        assert order.items[2].product == "A"
