"""Tests for select_in_loading for Child Tables.

TDD tests for efficient child table loading using select_in_loading strategy:
- Load parent documents with children in efficient queries
- Avoid N+1 query problem
- Use IN clause for batch loading children

Per CONTRIBUTING.md: Write failing tests FIRST, then implement.
"""

from typing import ClassVar
from uuid import uuid4

import pytest
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from framework_m.adapters.db.generic_repository import GenericRepository
from framework_m.adapters.db.schema_mapper import SchemaMapper
from framework_m.core.domain.base_doctype import BaseDocType, Field
from framework_m.core.registry import MetaRegistry

# =============================================================================
# Test DocTypes
# =============================================================================


class OrderItem(BaseDocType):
    """Child table for order items."""

    product_name: str = Field(description="Product name")
    quantity: int = Field(default=1)
    price: float = Field(default=0.0)

    class Meta:
        is_child_table: ClassVar[bool] = True


class Order(BaseDocType):
    """Parent DocType with child table."""

    customer: str = Field(description="Customer name")
    total: float = Field(default=0.0)
    # Note: items field is handled separately - not stored in parent table

    class Meta:
        api_resource: ClassVar[bool] = True


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def registry() -> MetaRegistry:
    """Get clean registry with test DocTypes."""
    reg = MetaRegistry.get_instance()
    reg.clear()
    reg.register_doctype(Order)
    reg.register_doctype(OrderItem)
    yield reg
    reg.clear()


@pytest.fixture
async def engine():
    """Create in-memory SQLite engine."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session(engine, registry) -> AsyncSession:
    """Create session with table schema for parent and child tables."""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    metadata = MetaData()
    mapper = SchemaMapper()

    # Create parent table for Order
    parent_table = mapper.create_table(Order, metadata)

    # Create child table for OrderItem separately
    child_table = mapper.create_table(OrderItem, metadata)
    # Add parent reference columns manually for the test
    # Note: The child table needs parent columns - let's recreate it properly
    from sqlalchemy import Column, Integer, String, Table
    from sqlalchemy.types import UUID as SA_UUID

    # Drop the auto-created table and make one with parent columns
    metadata.remove(child_table)
    child_table = Table(
        "orderitem",
        metadata,
        Column("id", SA_UUID, primary_key=True, nullable=False),
        Column("product_name", String, nullable=False),
        Column("quantity", Integer, nullable=True),
        Column(
            "price", String, nullable=True
        ),  # stored as float but we'll use String for simplicity
        Column("parent", String, nullable=False),
        Column("parentfield", String, nullable=False),
        Column("parenttype", String, nullable=False),
        Column("idx", Integer, nullable=False, default=0),
    )

    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session, parent_table, child_table


# =============================================================================
# Tests: Child Table Loading with select_in_loading
# =============================================================================


class TestSelectInLoadingChildTables:
    """Test efficient child table loading using select_in_loading."""

    @pytest.mark.asyncio
    async def test_load_children_with_in_clause(self, session) -> None:
        """Children should be loaded using IN clause for multiple parents."""
        sess, parent_table, child_table = session
        repo = GenericRepository(Order, parent_table)

        # Create two orders with items
        order1 = Order(customer="Alice", total=100.0)
        order2 = Order(customer="Bob", total=200.0)

        await repo.save(sess, order1)
        await repo.save(sess, order2)
        await sess.commit()

        # Insert child items directly using child table
        from sqlalchemy import insert

        child_items = [
            {
                "id": uuid4(),
                "product_name": "Widget",
                "quantity": 2,
                "price": 25.0,
                "parent": str(order1.id),
                "parentfield": "items",
                "parenttype": "Order",
                "idx": 0,
            },
            {
                "id": uuid4(),
                "product_name": "Gadget",
                "quantity": 1,
                "price": 50.0,
                "parent": str(order1.id),
                "parentfield": "items",
                "parenttype": "Order",
                "idx": 1,
            },
            {
                "id": uuid4(),
                "product_name": "Gizmo",
                "quantity": 3,
                "price": 33.33,
                "parent": str(order2.id),
                "parentfield": "items",
                "parenttype": "Order",
                "idx": 0,
            },
        ]

        await sess.execute(insert(child_table).values(child_items))
        await sess.commit()

        # Load orders with children using select_in_loading
        parent_ids = [order1.id, order2.id]
        children_by_parent = await repo.load_children_for_parents(
            sess,
            parent_ids=parent_ids,
            child_table=child_table,
            child_model=OrderItem,
        )

        # Verify children were loaded correctly
        assert str(order1.id) in children_by_parent
        assert str(order2.id) in children_by_parent
        assert len(children_by_parent[str(order1.id)]) == 2
        assert len(children_by_parent[str(order2.id)]) == 1

    @pytest.mark.asyncio
    async def test_load_children_empty_parent_list(self, session) -> None:
        """Empty parent list should return empty dict."""
        sess, parent_table, child_table = session
        repo = GenericRepository(Order, parent_table)

        result = await repo.load_children_for_parents(
            sess,
            parent_ids=[],
            child_table=child_table,
            child_model=OrderItem,
        )

        assert result == {}

    @pytest.mark.asyncio
    async def test_load_children_preserves_order(self, session) -> None:
        """Children should be ordered by idx within each parent."""
        sess, parent_table, child_table = session
        repo = GenericRepository(Order, parent_table)

        order = Order(customer="Charlie", total=300.0)
        await repo.save(sess, order)
        await sess.commit()

        from sqlalchemy import insert

        # Insert items in non-sequential idx order
        child_items = [
            {
                "id": uuid4(),
                "product_name": "Third",
                "quantity": 1,
                "price": 10.0,
                "parent": str(order.id),
                "parentfield": "items",
                "parenttype": "Order",
                "idx": 2,
            },
            {
                "id": uuid4(),
                "product_name": "First",
                "quantity": 1,
                "price": 10.0,
                "parent": str(order.id),
                "parentfield": "items",
                "parenttype": "Order",
                "idx": 0,
            },
            {
                "id": uuid4(),
                "product_name": "Second",
                "quantity": 1,
                "price": 10.0,
                "parent": str(order.id),
                "parentfield": "items",
                "parenttype": "Order",
                "idx": 1,
            },
        ]

        await sess.execute(insert(child_table).values(child_items))
        await sess.commit()

        children_by_parent = await repo.load_children_for_parents(
            sess,
            parent_ids=[order.id],
            child_table=child_table,
            child_model=OrderItem,
        )

        # Verify children are ordered by idx
        children = children_by_parent[str(order.id)]
        assert children[0].product_name == "First"
        assert children[1].product_name == "Second"
        assert children[2].product_name == "Third"
