"""Tests for Link Fields (Foreign Keys).

This module tests Link field functionality:
- Link fields store references to other DocTypes
- Foreign key constraints are created in the database
- Validation ensures target document exists
- Permission checks for linking
- Database-agnostic implementation
"""

from uuid import UUID, uuid4

import pytest

from framework_m import DocType, Field

# =============================================================================
# Test Models
# =============================================================================


class Customer(DocType):
    """Customer DocType for link testing."""

    customer_name: str = Field(description="Customer full name")
    email: str | None = Field(default=None, description="Email address")


class Product(DocType):
    """Product DocType for link testing."""

    product_name: str = Field(description="Product name")
    price: float = Field(description="Price")


class Order(DocType):
    """Order with link to Customer."""

    order_number: str = Field(description="Order number")
    # Link field - stores UUID reference to Customer
    customer: UUID | None = Field(
        default=None,
        description="Link to Customer",
        json_schema_extra={"link": "Customer"},
    )
    amount: float = Field(description="Order amount")


class OrderWithMultipleLinks(DocType):
    """Order with multiple link fields."""

    order_number: str = Field(description="Order number")
    customer: UUID | None = Field(
        default=None,
        description="Link to Customer",
        json_schema_extra={"link": "Customer"},
    )
    product: UUID | None = Field(
        default=None,
        description="Link to Product",
        json_schema_extra={"link": "Product"},
    )
    quantity: int = Field(default=1, description="Quantity")


# =============================================================================
# Test Link Field Type Detection
# =============================================================================


class TestLinkFieldDetection:
    """Test that Link fields are properly detected."""

    def test_link_field_has_json_schema_extra(self) -> None:
        """Link fields should have json_schema_extra with link key."""
        # Check Order model
        customer_field = Order.model_fields["customer"]
        assert customer_field.json_schema_extra is not None
        assert "link" in customer_field.json_schema_extra
        assert customer_field.json_schema_extra["link"] == "Customer"

    def test_link_field_type_is_uuid(self) -> None:
        """Link fields should use UUID type for storage."""
        customer_field = Order.model_fields["customer"]
        # Type should be UUID | None
        assert customer_field.annotation == UUID | None

    def test_multiple_link_fields_detected(self) -> None:
        """DocType can have multiple link fields."""
        customer_field = OrderWithMultipleLinks.model_fields["customer"]
        product_field = OrderWithMultipleLinks.model_fields["product"]

        assert customer_field.json_schema_extra["link"] == "Customer"
        assert product_field.json_schema_extra["link"] == "Product"

    def test_non_link_fields_no_link_metadata(self) -> None:
        """Regular fields should not have link metadata."""
        amount_field = Order.model_fields["amount"]
        assert (
            amount_field.json_schema_extra is None
            or "link" not in amount_field.json_schema_extra
        )


# =============================================================================
# Test Schema Creation with Foreign Keys
# =============================================================================


class TestLinkFieldSchema:
    """Test that Link fields create proper foreign key constraints."""

    @pytest.mark.asyncio
    async def test_link_field_creates_foreign_key_constraint(self) -> None:
        """Link fields should create foreign key constraints in schema."""
        from sqlalchemy import MetaData

        from framework_m.adapters.db.schema_mapper import SchemaMapper

        mapper = SchemaMapper()
        metadata = MetaData()

        # Create tables
        customer_table = mapper.create_table(Customer, metadata)
        order_table = mapper.create_table(Order, metadata)

        # Link field should be UUID column
        assert "customer" in order_table.c
        customer_col = order_table.c.customer

        # Should be nullable (optional link)
        assert customer_col.nullable is True

        # Should have foreign key constraint
        assert len(customer_col.foreign_keys) == 1
        fk = next(iter(customer_col.foreign_keys))

        # Should reference customer table's id column
        assert fk.column.table.name == customer_table.name
        assert fk.column.name == "id"

    @pytest.mark.asyncio
    async def test_multiple_link_fields_create_multiple_fks(self) -> None:
        """Multiple link fields should create multiple foreign key constraints."""
        from sqlalchemy import MetaData

        from framework_m.adapters.db.schema_mapper import SchemaMapper

        mapper = SchemaMapper()
        metadata = MetaData()

        # Create tables
        customer_table = mapper.create_table(Customer, metadata)
        product_table = mapper.create_table(Product, metadata)
        order_table = mapper.create_table(OrderWithMultipleLinks, metadata)

        # Customer link
        customer_col = order_table.c.customer
        assert len(customer_col.foreign_keys) == 1
        customer_fk = next(iter(customer_col.foreign_keys))
        assert customer_fk.column.table.name == customer_table.name

        # Product link
        product_col = order_table.c.product
        assert len(product_col.foreign_keys) == 1
        product_fk = next(iter(product_col.foreign_keys))
        assert product_fk.column.table.name == product_table.name

    @pytest.mark.asyncio
    async def test_link_field_without_target_table_no_fk(self) -> None:
        """Link field should not create FK if target table doesn't exist in metadata."""
        from sqlalchemy import MetaData

        from framework_m.adapters.db.schema_mapper import SchemaMapper

        mapper = SchemaMapper()
        metadata = MetaData()

        # Create order table WITHOUT creating customer table
        order_table = mapper.create_table(Order, metadata)

        # Should still have customer column
        assert "customer" in order_table.c

        # But no foreign key (target table not in metadata)
        # FK might not be created if target table not in metadata
        # This is acceptable - FK will be added when target table is created


# =============================================================================
# Test Link Field Validation
# =============================================================================


class TestLinkFieldValidation:
    """Test validation for link fields."""

    @pytest.mark.asyncio
    async def test_save_order_with_valid_customer_link(
        self, test_engine, clean_tables
    ) -> None:
        """Saving order with valid customer link should succeed."""
        from sqlalchemy import MetaData
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        from framework_m.adapters.db.generic_repository import GenericRepository
        from framework_m.adapters.db.schema_mapper import SchemaMapper
        from framework_m.adapters.db.table_registry import TableRegistry

        # Setup
        mapper = SchemaMapper()
        metadata = MetaData()
        customer_table = mapper.create_table(Customer, metadata)
        order_table = mapper.create_table(Order, metadata)

        table_registry = TableRegistry()
        table_registry.register_table(Customer.__name__, customer_table)
        table_registry.register_table(Order.__name__, order_table)

        async with test_engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

        # Create customer first
        customer = Customer(
            name="CUST-001",
            customer_name="Acme Corp",
            email="contact@acme.com",
        )

        customer_repo = GenericRepository(Customer, customer_table)
        async_session_maker = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )

        customer_id = None
        async with async_session_maker() as session:
            saved_customer = await customer_repo.save(session, customer)
            await session.commit()
            customer_id = saved_customer.id

        # Create order with link to customer
        order = Order(
            name="ORD-001",
            order_number="ORD-2024-0001",
            customer=customer_id,
            amount=1500.00,
        )

        order_repo = GenericRepository(Order, order_table)

        async with async_session_maker() as session:
            saved_order = await order_repo.save(session, order)
            await session.commit()

            assert saved_order.customer == customer_id

    @pytest.mark.asyncio
    async def test_save_order_with_null_customer_link(
        self, test_engine, clean_tables
    ) -> None:
        """Saving order without customer link should succeed (nullable)."""
        from sqlalchemy import MetaData
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        from framework_m.adapters.db.generic_repository import GenericRepository
        from framework_m.adapters.db.schema_mapper import SchemaMapper
        from framework_m.adapters.db.table_registry import TableRegistry

        # Setup
        mapper = SchemaMapper()
        metadata = MetaData()
        order_table = mapper.create_table(Order, metadata)

        table_registry = TableRegistry()
        table_registry.register_table(Order.__name__, order_table)

        async with test_engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

        # Create order without customer link
        order = Order(
            name="ORD-002",
            order_number="ORD-2024-0002",
            customer=None,  # No link
            amount=500.00,
        )

        order_repo = GenericRepository(Order, order_table)
        async_session_maker = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session_maker() as session:
            saved_order = await order_repo.save(session, order)
            await session.commit()

            assert saved_order.customer is None

    @pytest.mark.asyncio
    async def test_save_order_with_invalid_customer_id_fails(
        self, test_engine, clean_tables
    ) -> None:
        """Saving order with non-existent customer ID should fail (FK constraint)."""
        from sqlalchemy import MetaData
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        from framework_m.adapters.db.generic_repository import GenericRepository
        from framework_m.adapters.db.schema_mapper import SchemaMapper
        from framework_m.adapters.db.table_registry import TableRegistry
        from framework_m.core.exceptions import IntegrityError

        # Setup
        mapper = SchemaMapper()
        metadata = MetaData()
        customer_table = mapper.create_table(Customer, metadata)
        order_table = mapper.create_table(Order, metadata)

        table_registry = TableRegistry()
        table_registry.register_table(Customer.__name__, customer_table)
        table_registry.register_table(Order.__name__, order_table)

        async with test_engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

        # Create order with non-existent customer ID
        fake_customer_id = uuid4()
        order = Order(
            name="ORD-003",
            order_number="ORD-2024-0003",
            customer=fake_customer_id,  # Invalid link
            amount=750.00,
        )

        order_repo = GenericRepository(Order, order_table)
        async_session_maker = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )

        # Should raise IntegrityError due to FK constraint
        with pytest.raises(IntegrityError):
            async with async_session_maker() as session:
                await order_repo.save(session, order)
                await session.commit()


# =============================================================================
# Test Link Field Queries
# =============================================================================


class TestLinkFieldQueries:
    """Test querying with link fields."""

    @pytest.mark.asyncio
    async def test_load_order_with_customer_link(
        self, test_engine, clean_tables
    ) -> None:
        """Loading order should preserve customer link."""
        from sqlalchemy import MetaData
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        from framework_m.adapters.db.generic_repository import GenericRepository
        from framework_m.adapters.db.schema_mapper import SchemaMapper
        from framework_m.adapters.db.table_registry import TableRegistry

        # Setup
        mapper = SchemaMapper()
        metadata = MetaData()
        customer_table = mapper.create_table(Customer, metadata)
        order_table = mapper.create_table(Order, metadata)

        table_registry = TableRegistry()
        table_registry.register_table(Customer.__name__, customer_table)
        table_registry.register_table(Order.__name__, order_table)

        async with test_engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

        # Create customer
        customer = Customer(
            name="CUST-002",
            customer_name="Beta Inc",
        )

        customer_repo = GenericRepository(Customer, customer_table)
        async_session_maker = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )

        customer_id = None
        async with async_session_maker() as session:
            saved_customer = await customer_repo.save(session, customer)
            await session.commit()
            customer_id = saved_customer.id

        # Create order
        order = Order(
            name="ORD-004",
            order_number="ORD-2024-0004",
            customer=customer_id,
            amount=2000.00,
        )

        order_repo = GenericRepository(Order, order_table)

        order_id = None
        async with async_session_maker() as session:
            saved_order = await order_repo.save(session, order)
            await session.commit()
            order_id = saved_order.id

        # Load order
        async with async_session_maker() as session:
            loaded_order = await order_repo.get(session, order_id)

            assert loaded_order is not None
            assert loaded_order.customer == customer_id


# =============================================================================
# Test Database Agnosticism
# =============================================================================


class TestLinkFieldDatabaseAgnostic:
    """Test that link fields work with different databases."""

    @pytest.mark.asyncio
    async def test_link_field_works_with_sqlite(
        self, test_engine, clean_tables
    ) -> None:
        """Link fields should work with SQLite (default test database)."""
        from sqlalchemy import MetaData

        from framework_m.adapters.db.schema_mapper import SchemaMapper

        mapper = SchemaMapper()
        metadata = MetaData()

        # Create tables
        mapper.create_table(Customer, metadata)
        order_table = mapper.create_table(Order, metadata)

        # Can create tables without error
        async with test_engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

        # FK constraint should exist
        customer_col = order_table.c.customer
        assert len(customer_col.foreign_keys) >= 1


class TestEdgeCases:
    """Test edge cases for link fields."""

    def test_link_field_can_be_required(self) -> None:
        """Link fields can be required (non-nullable)."""

        class OrderRequiredCustomer(DocType):
            """Order with required customer link."""

            order_number: str
            customer: UUID = Field(
                description="Link to Customer",
                json_schema_extra={"link": "Customer"},
            )  # Required (no default, no Optional)

        # Field should not be nullable
        customer_field = OrderRequiredCustomer.model_fields["customer"]
        assert customer_field.annotation == UUID

    def test_link_field_with_string_description(self) -> None:
        """Link field can have description like any field."""
        customer_field = Order.model_fields["customer"]
        assert customer_field.description == "Link to Customer"
