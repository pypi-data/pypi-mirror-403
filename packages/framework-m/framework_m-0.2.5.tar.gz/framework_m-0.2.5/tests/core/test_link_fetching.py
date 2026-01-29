"""Tests for Link Field Fetching (fetch_from).

Tests the ability to auto-populate fields from linked documents.
Example: Order has a customer link, and can fetch customer_name from customer.customer_name
"""

from uuid import UUID

import pytest
from pydantic import Field
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from framework_m.adapters.db.generic_repository import GenericRepository
from framework_m.adapters.db.schema_mapper import SchemaMapper
from framework_m.adapters.db.table_registry import TableRegistry
from framework_m.core.domain.base_doctype import BaseDocType

# =============================================================================
# Test Models
# =============================================================================


class Customer(BaseDocType):
    """Customer DocType for testing link fetching."""

    customer_name: str
    email: str
    credit_limit: float = 0.0


class Product(BaseDocType):
    """Product DocType for testing link fetching."""

    product_name: str
    price: float
    category: str = "General"


class Order(BaseDocType):
    """Order DocType with link fetching."""

    order_number: str

    # Link to Customer
    customer: UUID | None = Field(
        default=None,
        description="Link to Customer",
        json_schema_extra={"link": "Customer"},
    )

    # Fetch customer_name from customer.customer_name
    customer_name: str | None = Field(
        default=None,
        description="Customer Name",
        json_schema_extra={"fetch_from": "customer.customer_name"},
    )

    # Fetch email from customer.email
    customer_email: str | None = Field(
        default=None,
        description="Customer Email",
        json_schema_extra={"fetch_from": "customer.email"},
    )

    amount: float


class OrderWithMultipleFetches(BaseDocType):
    """Order with multiple link fetches."""

    order_number: str

    # Customer link
    customer: UUID | None = Field(
        default=None,
        json_schema_extra={"link": "Customer"},
    )
    customer_name: str | None = Field(
        default=None,
        json_schema_extra={"fetch_from": "customer.customer_name"},
    )
    customer_credit_limit: float | None = Field(
        default=None,
        json_schema_extra={"fetch_from": "customer.credit_limit"},
    )

    # Product link
    product: UUID | None = Field(
        default=None,
        json_schema_extra={"link": "Product"},
    )
    product_name: str | None = Field(
        default=None,
        json_schema_extra={"fetch_from": "product.product_name"},
    )
    product_price: float | None = Field(
        default=None,
        json_schema_extra={"fetch_from": "product.price"},
    )

    quantity: int = 1


# =============================================================================
# Test Link Fetch Detection
# =============================================================================


class TestLinkFetchDetection:
    """Test detection of fetch_from fields."""

    def test_fetch_from_field_has_metadata(self):
        """Fetch fields should have fetch_from in json_schema_extra."""
        field_info = Order.model_fields["customer_name"]
        assert field_info.json_schema_extra is not None
        assert "fetch_from" in field_info.json_schema_extra
        assert field_info.json_schema_extra["fetch_from"] == "customer.customer_name"

    def test_fetch_from_field_type_matches_target(self):
        """Fetch field type should match target field type."""
        # customer_name is str, fetched from customer.customer_name (str)
        customer_name_field = Order.model_fields["customer_name"]
        assert customer_name_field.annotation == str | None

        # customer_email is str, fetched from customer.email (str)
        customer_email_field = Order.model_fields["customer_email"]
        assert customer_email_field.annotation == str | None

    def test_multiple_fetch_fields_detected(self):
        """Model with multiple fetch fields should detect all."""
        fetch_fields = []
        for field_name, field_info in OrderWithMultipleFetches.model_fields.items():
            if (
                field_info.json_schema_extra
                and "fetch_from" in field_info.json_schema_extra
            ):
                fetch_fields.append(field_name)

        assert len(fetch_fields) == 4
        assert "customer_name" in fetch_fields
        assert "customer_credit_limit" in fetch_fields
        assert "product_name" in fetch_fields
        assert "product_price" in fetch_fields

    def test_non_fetch_fields_no_fetch_metadata(self):
        """Regular fields should not have fetch_from metadata."""
        field_info = Order.model_fields["order_number"]
        assert (
            field_info.json_schema_extra is None
            or "fetch_from" not in field_info.json_schema_extra
        )


# =============================================================================
# Test Link Fetch on Save
# =============================================================================


class TestLinkFetchOnSave:
    """Test fetching values when saving documents."""

    @pytest.mark.asyncio
    async def test_fetch_values_on_save(self, test_engine):
        """Should fetch values from linked document on save."""
        # Setup
        metadata = MetaData()
        mapper = SchemaMapper()

        # Reset table registry
        table_registry = TableRegistry()
        table_registry.reset()

        customer_table = mapper.create_table(Customer, metadata)
        order_table = mapper.create_table(Order, metadata)

        table_registry.register_table(Customer.__name__, customer_table)
        table_registry.register_table(Order.__name__, order_table)

        async with test_engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

        # Create customer
        customer = Customer(
            name="CUST-001",
            customer_name="Acme Corp",
            email="contact@acme.com",
            credit_limit=10000.0,
        )

        customer_repo = GenericRepository(Customer, customer_table)
        async_session_maker = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session_maker() as session:
            await customer_repo.save(session, customer)
            await session.commit()

        # Create order with customer link
        order = Order(
            name="ORD-001",
            order_number="ORD-2024-0001",
            customer=customer.id,
            amount=5000.0,
        )

        order_repo = GenericRepository(Order, order_table)

        async with async_session_maker() as session:
            await order_repo.save(session, order)
            await session.commit()

        # Reload order and verify fetched values
        async with async_session_maker() as session:
            loaded_order = await order_repo.get(session, order.id)

        assert loaded_order is not None
        assert loaded_order.customer == customer.id
        assert loaded_order.customer_name == "Acme Corp"
        assert loaded_order.customer_email == "contact@acme.com"

    @pytest.mark.asyncio
    async def test_fetch_values_on_update(self, test_engine):
        """Should update fetched values when link changes."""
        # Setup
        metadata = MetaData()
        mapper = SchemaMapper()

        # Reset table registry
        table_registry = TableRegistry()
        table_registry.reset()

        customer_table = mapper.create_table(Customer, metadata)
        order_table = mapper.create_table(Order, metadata)

        table_registry.register_table(Customer.__name__, customer_table)
        table_registry.register_table(Order.__name__, order_table)

        async with test_engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

        async_session_maker = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )

        # Create two customers
        customer1 = Customer(
            name="CUST-001", customer_name="Acme Corp", email="acme@example.com"
        )
        customer2 = Customer(
            name="CUST-002", customer_name="Beta Inc", email="beta@example.com"
        )

        customer_repo = GenericRepository(Customer, customer_table)
        async with async_session_maker() as session:
            await customer_repo.save(session, customer1)
            await customer_repo.save(session, customer2)
            await session.commit()

        # Create order linked to customer1
        order = Order(
            name="ORD-001",
            order_number="ORD-001",
            customer=customer1.id,
            amount=100.0,
        )

        order_repo = GenericRepository(Order, order_table)
        async with async_session_maker() as session:
            await order_repo.save(session, order)
            await session.commit()

        # Update order to link to customer2
        order.customer = customer2.id

        async with async_session_maker() as session:
            await order_repo.save(session, order)
            await session.commit()

        # Reload and verify fetched values updated
        async with async_session_maker() as session:
            loaded_order = await order_repo.get(session, order.id)

        assert loaded_order is not None
        assert loaded_order.customer == customer2.id
        assert loaded_order.customer_name == "Beta Inc"
        assert loaded_order.customer_email == "beta@example.com"

    @pytest.mark.asyncio
    async def test_fetch_with_null_link(self, test_engine):
        """Should handle null link gracefully."""
        # Setup
        metadata = MetaData()
        mapper = SchemaMapper()

        # Reset table registry
        table_registry = TableRegistry()
        table_registry.reset()

        customer_table = mapper.create_table(Customer, metadata)
        order_table = mapper.create_table(Order, metadata)

        table_registry.register_table(Customer.__name__, customer_table)
        table_registry.register_table(Order.__name__, order_table)

        async with test_engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

        # Create order without customer link
        order = Order(
            name="ORD-001",
            order_number="ORD-001",
            customer=None,
            amount=100.0,
        )

        order_repo = GenericRepository(Order, order_table)
        async_session_maker = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session_maker() as session:
            await order_repo.save(session, order)
            await session.commit()

        # Reload and verify fetched values are None
        async with async_session_maker() as session:
            loaded_order = await order_repo.get(session, order.id)

        assert loaded_order is not None
        assert loaded_order.customer is None
        assert loaded_order.customer_name is None
        assert loaded_order.customer_email is None


# =============================================================================
# Test Multiple Link Fetches
# =============================================================================


class TestMultipleLinkFetches:
    """Test fetching from multiple links."""

    @pytest.mark.asyncio
    async def test_fetch_from_multiple_links(self, test_engine):
        """Should fetch from multiple different links."""
        # Setup
        metadata = MetaData()
        mapper = SchemaMapper()

        # Reset table registry
        table_registry = TableRegistry()
        table_registry.reset()

        customer_table = mapper.create_table(Customer, metadata)
        product_table = mapper.create_table(Product, metadata)
        order_table = mapper.create_table(OrderWithMultipleFetches, metadata)

        table_registry.register_table(Customer.__name__, customer_table)
        table_registry.register_table(Product.__name__, product_table)
        table_registry.register_table(OrderWithMultipleFetches.__name__, order_table)

        async with test_engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

        async_session_maker = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )

        # Create customer and product
        customer = Customer(
            name="CUST-001",
            customer_name="Acme Corp",
            email="acme@example.com",
            credit_limit=50000.0,
        )
        product = Product(
            name="PROD-001",
            product_name="Widget",
            price=99.99,
            category="Hardware",
        )

        customer_repo = GenericRepository(Customer, customer_table)
        product_repo = GenericRepository(Product, product_table)

        async with async_session_maker() as session:
            await customer_repo.save(session, customer)
            await product_repo.save(session, product)
            await session.commit()

        # Create order with both links
        order = OrderWithMultipleFetches(
            name="ORD-001",
            order_number="ORD-001",
            customer=customer.id,
            product=product.id,
            quantity=5,
        )

        order_repo = GenericRepository(OrderWithMultipleFetches, order_table)
        async with async_session_maker() as session:
            await order_repo.save(session, order)
            await session.commit()

        # Reload and verify all fetched values
        async with async_session_maker() as session:
            loaded_order = await order_repo.get(session, order.id)

        assert loaded_order is not None
        # Customer fetches
        assert loaded_order.customer_name == "Acme Corp"
        assert loaded_order.customer_credit_limit == 50000.0
        # Product fetches
        assert loaded_order.product_name == "Widget"
        assert loaded_order.product_price == 99.99

    @pytest.mark.asyncio
    async def test_fetch_with_partial_null_links(self, test_engine):
        """Should handle case where only some links are null."""
        # Setup
        metadata = MetaData()
        mapper = SchemaMapper()

        # Reset table registry
        table_registry = TableRegistry()
        table_registry.reset()

        customer_table = mapper.create_table(Customer, metadata)
        product_table = mapper.create_table(Product, metadata)
        order_table = mapper.create_table(OrderWithMultipleFetches, metadata)

        table_registry.register_table(Customer.__name__, customer_table)
        table_registry.register_table(Product.__name__, product_table)
        table_registry.register_table(OrderWithMultipleFetches.__name__, order_table)

        async with test_engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

        async_session_maker = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )

        # Create only customer
        customer = Customer(
            name="CUST-001",
            customer_name="Acme Corp",
            email="acme@example.com",
            credit_limit=50000.0,
        )

        customer_repo = GenericRepository(Customer, customer_table)
        async with async_session_maker() as session:
            await customer_repo.save(session, customer)
            await session.commit()

        # Create order with customer but no product
        order = OrderWithMultipleFetches(
            name="ORD-001",
            order_number="ORD-001",
            customer=customer.id,
            product=None,  # No product link
            quantity=1,
        )

        order_repo = GenericRepository(OrderWithMultipleFetches, order_table)
        async with async_session_maker() as session:
            await order_repo.save(session, order)
            await session.commit()

        # Reload and verify
        async with async_session_maker() as session:
            loaded_order = await order_repo.get(session, order.id)

        assert loaded_order is not None
        # Customer fetches should work
        assert loaded_order.customer_name == "Acme Corp"
        assert loaded_order.customer_credit_limit == 50000.0
        # Product fetches should be None
        assert loaded_order.product_name is None
        assert loaded_order.product_price is None


# =============================================================================
# Test Edge Cases
# =============================================================================


class TestLinkFetchEdgeCases:
    """Test edge cases for link fetching."""

    def test_fetch_from_invalid_syntax(self):
        """Fetch_from should follow link.field pattern."""
        # This is validated at model definition time by the pattern itself
        # fetch_from must be in format "link_field.target_field"

        # Valid pattern
        class ValidOrder(BaseDocType):
            customer: UUID | None = Field(json_schema_extra={"link": "Customer"})
            customer_name: str | None = Field(
                default=None,
                json_schema_extra={"fetch_from": "customer.customer_name"},
            )

        # Check that valid model can be created
        assert "customer_name" in ValidOrder.model_fields

    @pytest.mark.asyncio
    async def test_fetch_from_non_existent_link_field(self, test_engine):
        """If fetch_from references non-existent link, should be ignored."""

        class OrderWithBadFetch(BaseDocType):
            order_number: str
            # No customer link field
            customer_name: str | None = Field(
                default=None,
                json_schema_extra={"fetch_from": "customer.customer_name"},
            )

        metadata = MetaData()
        mapper = SchemaMapper()

        # Reset table registry
        table_registry = TableRegistry()
        table_registry.reset()

        order_table = mapper.create_table(OrderWithBadFetch, metadata)
        table_registry.register_table(OrderWithBadFetch.__name__, order_table)

        async with test_engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

        # Create order - fetch should be ignored since link doesn't exist
        order = OrderWithBadFetch(
            name="ORD-001",
            order_number="ORD-001",
        )

        order_repo = GenericRepository(OrderWithBadFetch, order_table)
        async_session_maker = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session_maker() as session:
            await order_repo.save(session, order)
            await session.commit()

        # Should save successfully, customer_name stays None
        async with async_session_maker() as session:
            loaded = await order_repo.get(session, order.id)

        assert loaded is not None
        assert loaded.customer_name is None

    @pytest.mark.asyncio
    async def test_manual_override_of_fetched_value(self, test_engine):
        """Fetched values always sync with link (no manual override)."""
        # Setup
        metadata = MetaData()
        mapper = SchemaMapper()

        # Reset table registry
        table_registry = TableRegistry()
        table_registry.reset()

        customer_table = mapper.create_table(Customer, metadata)
        order_table = mapper.create_table(Order, metadata)

        table_registry.register_table(Customer.__name__, customer_table)
        table_registry.register_table(Order.__name__, order_table)

        async with test_engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

        async_session_maker = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )

        # Create customer
        customer = Customer(
            name="CUST-001",
            customer_name="Acme Corp",
            email="acme@example.com",
        )

        customer_repo = GenericRepository(Customer, customer_table)
        async with async_session_maker() as session:
            await customer_repo.save(session, customer)
            await session.commit()

        # Create order - even with manual value, fetch_from overrides it
        order = Order(
            name="ORD-001",
            order_number="ORD-001",
            customer=customer.id,
            customer_name="Custom Name Override",  # This will be overridden by fetch
            amount=100.0,
        )

        order_repo = GenericRepository(Order, order_table)
        async with async_session_maker() as session:
            await order_repo.save(session, order)
            await session.commit()

        # Fetched value should override manual value (keeps data in sync)
        async with async_session_maker() as session:
            loaded = await order_repo.get(session, order.id)

        assert loaded is not None
        # fetch_from always syncs with link (prevents data inconsistency)
        assert loaded.customer_name == "Acme Corp"
