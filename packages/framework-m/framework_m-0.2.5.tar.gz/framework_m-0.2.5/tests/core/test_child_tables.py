"""Tests for Child Tables (Nested DocTypes) - Section 4.1.

This module tests the child table functionality that allows:
- DocTypes to be marked as child tables (is_child flag)
- Child tables stored in separate tables with parent references
- Parent/parenttype/idx columns for relational integrity
- Automatic cascade operations (save, load, delete children with parent)
- Ordering of child records via idx column
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest
from pydantic import Field
from sqlalchemy import MetaData

from framework_m.core.domain.base_doctype import BaseDocType


# Test Fixtures - Parent and Child DocTypes
class OrderItem(BaseDocType):
    """Child table for order line items."""

    item: str = Field(description="Item name")
    quantity: int = Field(description="Quantity ordered")
    rate: Decimal = Field(description="Price per unit")

    class Meta:
        is_child = True


class Order(BaseDocType):
    """Parent DocType with child table."""

    customer: str = Field(description="Customer name")
    items: list[OrderItem] = Field(default_factory=list, description="Order line items")


class InvoiceItem(BaseDocType):
    """Another child table example."""

    description: str = Field(description="Item description")
    amount: Decimal = Field(description="Line item amount")

    class Meta:
        is_child = True


class Invoice(BaseDocType):
    """Parent DocType with invoice items."""

    customer: str = Field(description="Customer name")
    items: list[InvoiceItem] = Field(
        default_factory=list, description="Invoice line items"
    )
    total: Decimal = Field(default=Decimal("0"), description="Invoice total")


class RegularDocType(BaseDocType):
    """Regular DocType without is_child flag."""

    title: str = Field(description="Title")
    description: str = Field(description="Description")


# Test Classes
class TestChildTableFlag:
    """Test is_child flag detection."""

    def test_child_table_has_is_child_flag(self) -> None:
        """Child table should have is_child=True in Meta."""
        meta = getattr(OrderItem, "Meta", None)
        assert meta is not None
        assert hasattr(meta, "is_child")
        assert meta.is_child is True

    def test_regular_doctype_no_is_child_flag(self) -> None:
        """Regular DocType should not have is_child flag or default to False."""
        meta = getattr(RegularDocType, "Meta", None)

        # Either no Meta class, or Meta without is_child, or is_child=False
        if meta is None:
            assert True  # No Meta is fine
        else:
            is_child = getattr(meta, "is_child", False)
            assert is_child is False

    def test_parent_doctype_no_is_child_flag(self) -> None:
        """Parent DocType should not be marked as child."""
        meta = getattr(Order, "Meta", None)

        if meta is None:
            assert True
        else:
            is_child = getattr(meta, "is_child", False)
            assert is_child is False

    def test_multiple_child_tables_each_marked(self) -> None:
        """Each child table should have its own is_child flag."""
        order_item_meta = getattr(OrderItem, "Meta", None)
        invoice_item_meta = getattr(InvoiceItem, "Meta", None)

        assert order_item_meta is not None
        assert invoice_item_meta is not None

        assert getattr(order_item_meta, "is_child", False) is True
        assert getattr(invoice_item_meta, "is_child", False) is True


class TestChildTableSchema:
    """Test child table schema generation."""

    def test_child_table_has_parent_column(self) -> None:
        """Child table should have 'parent' column."""
        from framework_m.adapters.db.schema_mapper import SchemaMapper

        mapper = SchemaMapper()
        metadata = MetaData()

        child_table = mapper.create_table(OrderItem, metadata)

        # Should have parent column
        assert "parent" in child_table.c

    def test_child_table_has_parenttype_column(self) -> None:
        """Child table should have 'parenttype' column."""
        from framework_m.adapters.db.schema_mapper import SchemaMapper

        mapper = SchemaMapper()
        metadata = MetaData()

        child_table = mapper.create_table(OrderItem, metadata)

        # Should have parenttype column
        assert "parenttype" in child_table.c

    def test_child_table_has_idx_column(self) -> None:
        """Child table should have 'idx' column for ordering."""
        from framework_m.adapters.db.schema_mapper import SchemaMapper

        mapper = SchemaMapper()
        metadata = MetaData()

        child_table = mapper.create_table(OrderItem, metadata)

        # Should have idx column
        assert "idx" in child_table.c

    def test_parent_column_type_is_string(self) -> None:
        """Parent column should be string (UUID as string)."""
        from framework_m.adapters.db.schema_mapper import SchemaMapper

        mapper = SchemaMapper()
        metadata = MetaData()

        child_table = mapper.create_table(OrderItem, metadata)

        parent_col = child_table.c.parent
        # Should be string type (VARCHAR/String)
        assert "String" in str(parent_col.type) or "VARCHAR" in str(parent_col.type)

    def test_parenttype_column_type_is_string(self) -> None:
        """Parenttype column should be string."""
        from framework_m.adapters.db.schema_mapper import SchemaMapper

        mapper = SchemaMapper()
        metadata = MetaData()

        child_table = mapper.create_table(OrderItem, metadata)

        parenttype_col = child_table.c.parenttype
        # Should be string type
        assert "String" in str(parenttype_col.type) or "VARCHAR" in str(
            parenttype_col.type
        )

    def test_idx_column_type_is_integer(self) -> None:
        """Idx column should be integer."""
        from framework_m.adapters.db.schema_mapper import SchemaMapper

        mapper = SchemaMapper()
        metadata = MetaData()

        child_table = mapper.create_table(OrderItem, metadata)

        idx_col = child_table.c.idx
        # Should be integer type
        assert "Integer" in str(idx_col.type) or "INT" in str(idx_col.type)

    def test_parent_column_not_nullable(self) -> None:
        """Parent column should not be nullable."""
        from framework_m.adapters.db.schema_mapper import SchemaMapper

        mapper = SchemaMapper()
        metadata = MetaData()

        child_table = mapper.create_table(OrderItem, metadata)

        parent_col = child_table.c.parent
        assert parent_col.nullable is False

    def test_parenttype_column_not_nullable(self) -> None:
        """Parenttype column should not be nullable."""
        from framework_m.adapters.db.schema_mapper import SchemaMapper

        mapper = SchemaMapper()
        metadata = MetaData()

        child_table = mapper.create_table(OrderItem, metadata)

        parenttype_col = child_table.c.parenttype
        assert parenttype_col.nullable is False

    def test_idx_column_not_nullable(self) -> None:
        """Idx column should not be nullable."""
        from framework_m.adapters.db.schema_mapper import SchemaMapper

        mapper = SchemaMapper()
        metadata = MetaData()

        child_table = mapper.create_table(OrderItem, metadata)

        idx_col = child_table.c.idx
        assert idx_col.nullable is False

    def test_regular_doctype_no_parent_columns(self) -> None:
        """Regular DocType should NOT have parent/parenttype/idx columns."""
        from framework_m.adapters.db.schema_mapper import SchemaMapper

        mapper = SchemaMapper()
        metadata = MetaData()

        regular_table = mapper.create_table(RegularDocType, metadata)

        # Should NOT have child table columns
        assert "parent" not in regular_table.c
        assert "parenttype" not in regular_table.c
        assert "idx" not in regular_table.c

    def test_child_table_has_standard_fields(self) -> None:
        """Child table should still have standard DocType fields."""
        from framework_m.adapters.db.schema_mapper import SchemaMapper

        mapper = SchemaMapper()
        metadata = MetaData()

        child_table = mapper.create_table(OrderItem, metadata)

        # Standard fields should exist
        assert "id" in child_table.c
        assert "creation" in child_table.c
        assert "modified" in child_table.c

    def test_child_table_has_custom_fields(self) -> None:
        """Child table should have its custom fields."""
        from framework_m.adapters.db.schema_mapper import SchemaMapper

        mapper = SchemaMapper()
        metadata = MetaData()

        child_table = mapper.create_table(OrderItem, metadata)

        # Custom fields should exist
        assert "item" in child_table.c
        assert "quantity" in child_table.c
        assert "rate" in child_table.c


class TestChildTableIndexes:
    """Test indexes on child tables."""

    def test_child_table_has_parent_index(self) -> None:
        """Child table should have index on parent column for fast lookups."""
        from framework_m.adapters.db.schema_mapper import SchemaMapper

        mapper = SchemaMapper()
        metadata = MetaData()

        child_table = mapper.create_table(OrderItem, metadata)

        # Check if any index includes the parent column
        has_parent_index = any(
            "parent" in [col.name for col in idx.columns] for idx in child_table.indexes
        )

        assert has_parent_index is True

    def test_child_table_has_composite_index(self) -> None:
        """Child table should have composite index on (parent, idx) for ordering."""
        from framework_m.adapters.db.schema_mapper import SchemaMapper

        mapper = SchemaMapper()
        metadata = MetaData()

        child_table = mapper.create_table(OrderItem, metadata)

        # Check for composite index with parent and idx
        has_composite_index = any(
            {col.name for col in idx.columns} == {"parent", "idx"}
            for idx in child_table.indexes
        )

        assert has_composite_index is True


class TestChildTableHelperMethods:
    """Test helper methods for child table detection."""

    def test_is_child_table_helper_returns_true_for_child(self) -> None:
        """Helper method should identify child tables."""
        from framework_m.adapters.db.schema_mapper import SchemaMapper

        mapper = SchemaMapper()

        is_child = mapper.is_child_table(OrderItem)
        assert is_child is True

    def test_is_child_table_helper_returns_false_for_regular(self) -> None:
        """Helper method should return False for regular DocTypes."""
        from framework_m.adapters.db.schema_mapper import SchemaMapper

        mapper = SchemaMapper()

        is_child = mapper.is_child_table(RegularDocType)
        assert is_child is False

    def test_is_child_table_helper_returns_false_for_parent(self) -> None:
        """Helper method should return False for parent DocTypes."""
        from framework_m.adapters.db.schema_mapper import SchemaMapper

        mapper = SchemaMapper()

        is_child = mapper.is_child_table(Order)
        assert is_child is False


class TestChildTableCRUD:
    """Test CRUD operations with child tables."""

    @pytest.mark.asyncio
    async def test_save_parent_with_children(
        self, test_engine: Any, clean_tables: Any
    ) -> None:
        """Saving parent should save all child records."""
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        from framework_m.adapters.db.generic_repository import GenericRepository
        from framework_m.adapters.db.schema_mapper import SchemaMapper
        from framework_m.adapters.db.table_registry import TableRegistry

        # Setup: Create tables
        mapper = SchemaMapper()
        parent_table = mapper.create_table(Order, clean_tables)
        child_table = mapper.create_table(OrderItem, clean_tables)

        # Register tables
        table_registry = TableRegistry()
        table_registry.register_table(Order.__name__, parent_table)
        table_registry.register_table(OrderItem.__name__, child_table)

        async with test_engine.begin() as conn:
            await conn.run_sync(clean_tables.create_all)

        # Create parent with children
        order = Order(
            name="ORD-001",
            customer="Acme Corp",
            items=[
                OrderItem(
                    name="ORD-001-item-1",
                    item="Widget",
                    quantity=10,
                    rate=Decimal("99.99"),
                ),
                OrderItem(
                    name="ORD-001-item-2",
                    item="Gadget",
                    quantity=5,
                    rate=Decimal("149.99"),
                ),
            ],
        )

        # Save parent (should save children too)
        repo = GenericRepository(Order, parent_table)
        async_session_maker = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )
        async with async_session_maker() as session:
            saved_order = await repo.save(session, order)
            await session.commit()

            # Verify children were saved
            from sqlalchemy import select

            result = await session.execute(select(child_table))
            rows = result.fetchall()

            assert len(rows) == 2
            # Verify parent references
            for row in rows:
                row_dict = dict(row._mapping)
                assert row_dict["parent"] == str(saved_order.id)
                assert row_dict["parenttype"] == "Order"
                assert row_dict["idx"] in [1, 2]

    @pytest.mark.asyncio
    async def test_load_parent_loads_children(
        self, test_engine: Any, clean_tables: Any
    ) -> None:
        """Loading parent should automatically load child records."""
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        from framework_m.adapters.db.generic_repository import GenericRepository
        from framework_m.adapters.db.schema_mapper import SchemaMapper
        from framework_m.adapters.db.table_registry import TableRegistry

        # Setup
        mapper = SchemaMapper()
        parent_table = mapper.create_table(Order, clean_tables)
        child_table = mapper.create_table(OrderItem, clean_tables)

        table_registry = TableRegistry()
        table_registry.register_table(Order.__name__, parent_table)
        table_registry.register_table(OrderItem.__name__, child_table)

        async with test_engine.begin() as conn:
            await conn.run_sync(clean_tables.create_all)

        # Create and save order
        order = Order(
            name="ORD-002",
            customer="Beta Inc",
            items=[
                OrderItem(
                    name="ORD-002-item-1",
                    item="Tool",
                    quantity=3,
                    rate=Decimal("50.00"),
                ),
            ],
        )

        repo = GenericRepository(Order, parent_table)
        async_session_maker = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )

        order_id = None
        async with async_session_maker() as session:
            saved_order = await repo.save(session, order)
            await session.commit()
            order_id = saved_order.id

        # Load parent (should load children)
        async with async_session_maker() as session:
            loaded_order = await repo.get(session, order_id)

            assert loaded_order is not None
            assert loaded_order.customer == "Beta Inc"
            assert len(loaded_order.items) == 1
            assert loaded_order.items[0].item == "Tool"
            assert loaded_order.items[0].quantity == 3
            assert loaded_order.items[0].rate == Decimal("50.00")

    @pytest.mark.asyncio
    async def test_update_parent_deletes_old_children(
        self, test_engine: Any, clean_tables: Any
    ) -> None:
        """Updating parent should delete old children and insert new ones."""
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        from framework_m.adapters.db.generic_repository import GenericRepository
        from framework_m.adapters.db.schema_mapper import SchemaMapper
        from framework_m.adapters.db.table_registry import TableRegistry

        # Setup
        mapper = SchemaMapper()
        parent_table = mapper.create_table(Order, clean_tables)
        child_table = mapper.create_table(OrderItem, clean_tables)

        table_registry = TableRegistry()
        table_registry.register_table(Order.__name__, parent_table)
        table_registry.register_table(OrderItem.__name__, child_table)

        async with test_engine.begin() as conn:
            await conn.run_sync(clean_tables.create_all)

        # Create initial order with 2 items
        order = Order(
            name="ORD-003",
            customer="Gamma LLC",
            items=[
                OrderItem(
                    name="ORD-003-item-1",
                    item="Part A",
                    quantity=5,
                    rate=Decimal("10.00"),
                ),
                OrderItem(
                    name="ORD-003-item-2",
                    item="Part B",
                    quantity=3,
                    rate=Decimal("15.00"),
                ),
            ],
        )

        repo = GenericRepository(Order, parent_table)
        async_session_maker = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session_maker() as session:
            saved_order = await repo.save(session, order)
            await session.commit()

            # Update with different items (only 1 item now)
            saved_order.items = [
                OrderItem(
                    name="ORD-003-item-new",
                    item="Part C",
                    quantity=10,
                    rate=Decimal("20.00"),
                ),
            ]

            await repo.save(session, saved_order)
            await session.commit()

            # Verify old children deleted, new one inserted
            from sqlalchemy import select

            result = await session.execute(select(child_table))
            rows = result.fetchall()

            assert len(rows) == 1
            row_dict = dict(rows[0]._mapping)
            assert row_dict["item"] == "Part C"
            assert row_dict["quantity"] == 10

    @pytest.mark.asyncio
    async def test_children_ordered_by_idx(
        self, test_engine: Any, clean_tables: Any
    ) -> None:
        """Children should be loaded in idx order."""
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        from framework_m.adapters.db.generic_repository import GenericRepository
        from framework_m.adapters.db.schema_mapper import SchemaMapper
        from framework_m.adapters.db.table_registry import TableRegistry

        # Setup
        mapper = SchemaMapper()
        parent_table = mapper.create_table(Order, clean_tables)
        child_table = mapper.create_table(OrderItem, clean_tables)

        table_registry = TableRegistry()
        table_registry.register_table(Order.__name__, parent_table)
        table_registry.register_table(OrderItem.__name__, child_table)

        async with test_engine.begin() as conn:
            await conn.run_sync(clean_tables.create_all)

        # Create order with multiple items
        order = Order(
            name="ORD-004",
            customer="Delta Co",
            items=[
                OrderItem(
                    name="ORD-004-item-1",
                    item="First",
                    quantity=1,
                    rate=Decimal("10.00"),
                ),
                OrderItem(
                    name="ORD-004-item-2",
                    item="Second",
                    quantity=2,
                    rate=Decimal("20.00"),
                ),
                OrderItem(
                    name="ORD-004-item-3",
                    item="Third",
                    quantity=3,
                    rate=Decimal("30.00"),
                ),
            ],
        )

        repo = GenericRepository(Order, parent_table)
        async_session_maker = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )

        order_id = None
        async with async_session_maker() as session:
            saved_order = await repo.save(session, order)
            await session.commit()
            order_id = saved_order.id

        # Load and verify order
        async with async_session_maker() as session:
            loaded_order = await repo.get(session, order_id)

            assert loaded_order is not None
            assert len(loaded_order.items) == 3
            # Verify idx order
            assert loaded_order.items[0].item == "First"
            assert loaded_order.items[1].item == "Second"
            assert loaded_order.items[2].item == "Third"

    @pytest.mark.asyncio
    async def test_delete_parent_deletes_children(
        self, test_engine: Any, clean_tables: Any
    ) -> None:
        """Deleting parent should delete all child records (cascade)."""
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        from framework_m.adapters.db.generic_repository import GenericRepository
        from framework_m.adapters.db.schema_mapper import SchemaMapper
        from framework_m.adapters.db.table_registry import TableRegistry

        # Setup
        mapper = SchemaMapper()
        parent_table = mapper.create_table(Order, clean_tables)
        child_table = mapper.create_table(OrderItem, clean_tables)

        table_registry = TableRegistry()
        table_registry.register_table(Order.__name__, parent_table)
        table_registry.register_table(OrderItem.__name__, child_table)

        async with test_engine.begin() as conn:
            await conn.run_sync(clean_tables.create_all)

        # Create order
        order = Order(
            name="ORD-005",
            customer="Epsilon Ltd",
            items=[
                OrderItem(
                    name="ORD-005-item-1", item="A", quantity=1, rate=Decimal("5.00")
                ),
                OrderItem(
                    name="ORD-005-item-2", item="B", quantity=2, rate=Decimal("10.00")
                ),
            ],
        )

        repo = GenericRepository(Order, parent_table)
        async_session_maker = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )

        order_id = None
        async with async_session_maker() as session:
            saved_order = await repo.save(session, order)
            await session.commit()
            order_id = saved_order.id

        # Delete parent
        async with async_session_maker() as session:
            await repo.delete(session, order_id, hard=True)
            await session.commit()

            # Verify children deleted
            from sqlalchemy import select

            result = await session.execute(select(child_table))
            rows = result.fetchall()

            assert len(rows) == 0  # All children should be deleted


class TestChildTableValidation:
    """Test validation for child tables."""

    def test_child_table_cannot_have_independent_name(self) -> None:
        """Child tables should not generate independent names."""
        # Child records are tied to parent, they don't need unique names
        # Verify that child tables don't participate in naming series
        pass

    def test_parent_field_is_set_on_save(self) -> None:
        """When saving children, parent field should be automatically set."""
        # Verify that the repository sets the parent UUID
        # when saving child records
        pass

    def test_parenttype_field_is_set_on_save(self) -> None:
        """When saving children, parenttype should be set to parent DocType name."""
        # Verify that parenttype is set to the parent's doctype name
        pass

    def test_idx_field_is_set_on_save(self) -> None:
        """When saving children, idx should be set based on list position."""
        # Verify that idx is set to the position in the list (1-indexed or 0-indexed)
        pass


class TestEdgeCases:
    """Test edge cases for child tables."""

    def test_empty_child_list(self) -> None:
        """Parent with empty child list should work correctly."""
        # Verify that saving a parent with empty items list works
        pass

    def test_single_child(self) -> None:
        """Parent with single child should work."""
        # Verify single child handling
        pass

    def test_many_children(self) -> None:
        """Parent with many children should work."""
        # Verify handling of large child lists
        pass

    def test_nested_child_tables_not_supported(self) -> None:
        """Child tables within child tables should not be supported (at least initially)."""
        # Document this limitation
        pass

    def test_child_table_with_list_field(self) -> None:
        """Child table can have list fields (stored as JSON)."""
        # Verify that child tables can have list/dict fields
        # stored as JSON columns
        pass


class TestChildTableIntegration:
    """Integration tests combining schema and repository."""

    @pytest.mark.asyncio
    async def test_complete_order_workflow(self) -> None:
        """Test complete workflow: create order with items, update, delete."""
        # End-to-end test:
        # 1. Create Order with 3 OrderItems
        # 2. Save to database
        # 3. Load from database (verify items loaded)
        # 4. Update order (change items)
        # 5. Verify old items deleted, new items inserted
        # 6. Delete order (verify items cascade deleted)
        pass

    @pytest.mark.asyncio
    async def test_multiple_parents_same_child_type(self) -> None:
        """Multiple parent records can have children of the same type."""
        # Test that two different Orders can each have OrderItems
        # and they don't interfere with each other
        pass

    @pytest.mark.asyncio
    async def test_query_children_independently(self) -> None:
        """Child records can be queried independently if needed."""
        # Verify that we can query OrderItem table directly
        # filtering by parent/parenttype
        pass


class TestBackwardCompatibility:
    """Test that existing functionality still works."""

    def test_regular_doctype_unchanged(self) -> None:
        """Regular DocTypes should work exactly as before."""
        from framework_m.adapters.db.schema_mapper import SchemaMapper

        mapper = SchemaMapper()
        metadata = MetaData()

        # Regular DocType should create table normally
        regular_table = mapper.create_table(RegularDocType, metadata)

        # Should have standard fields
        assert "id" in regular_table.c
        assert "title" in regular_table.c
        assert "description" in regular_table.c

        # Should NOT have child table fields
        assert "parent" not in regular_table.c

    def test_parent_doctype_unchanged(self) -> None:
        """Parent DocType table should be regular table (no child columns)."""
        from framework_m.adapters.db.schema_mapper import SchemaMapper

        mapper = SchemaMapper()
        metadata = MetaData()

        # Parent DocType should create regular table
        parent_table = mapper.create_table(Order, metadata)

        # Should have its fields
        assert "customer" in parent_table.c

        # Should NOT have child table columns
        assert "parent" not in parent_table.c
        assert "parenttype" not in parent_table.c
        assert "idx" not in parent_table.c
