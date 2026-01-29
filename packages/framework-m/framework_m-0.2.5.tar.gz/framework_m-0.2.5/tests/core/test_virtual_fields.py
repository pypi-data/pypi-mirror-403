"""Tests for Virtual Fields and Computed Fields.

This module tests the @computed_field decorator functionality:
- Computed fields are calculated properties not stored in database
- They are included in model_dump() and API responses
- They don't create database columns
- They work with child table relationships
"""

from decimal import Decimal

import pytest
from pydantic import computed_field

from framework_m import DocType, Field

# =============================================================================
# Test Models
# =============================================================================


class InvoiceItem(DocType):
    """Invoice line item (child table)."""

    item: str = Field(description="Item name")
    quantity: int = Field(description="Quantity", ge=1)
    rate: Decimal = Field(description="Rate per unit")

    class Meta:
        """Metadata configuration."""

        is_child = True

    @computed_field  # type: ignore[prop-decorator]
    @property
    def amount(self) -> Decimal:
        """Computed field: quantity * rate."""
        return Decimal(str(self.quantity)) * self.rate


class Invoice(DocType):
    """Invoice with computed total field."""

    customer: str = Field(description="Customer name")
    items: list[InvoiceItem] = Field(default_factory=list, description="Line items")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total(self) -> Decimal:
        """Computed field: sum of all item amounts."""
        return sum((item.amount for item in self.items), Decimal("0"))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def item_count(self) -> int:
        """Computed field: total number of items."""
        return len(self.items)


class Product(DocType):
    """Product with computed fields."""

    name: str = Field(description="Product name")
    price: Decimal = Field(description="Base price")
    tax_rate: Decimal = Field(
        default=Decimal("0.1"), description="Tax rate (0.1 = 10%)"
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def price_with_tax(self) -> Decimal:
        """Computed field: price including tax."""
        return self.price * (Decimal("1") + self.tax_rate)


# =============================================================================
# Test Computed Field Functionality
# =============================================================================


class TestComputedFieldBasics:
    """Test basic computed field functionality."""

    def test_computed_field_is_calculated(self) -> None:
        """Computed fields should be calculated from other fields."""
        product = Product(
            name="Widget",
            price=Decimal("100.00"),
            tax_rate=Decimal("0.15"),
        )

        # Computed field should calculate correctly
        assert product.price_with_tax == Decimal("115.00")

    def test_computed_field_updates_with_data(self) -> None:
        """Computed fields should recalculate when source data changes."""
        product = Product(
            name="Widget",
            price=Decimal("100.00"),
        )

        assert product.price_with_tax == Decimal("110.00")  # 10% tax

        # Change price
        product = Product(
            name="Widget",
            price=Decimal("200.00"),
        )
        assert product.price_with_tax == Decimal("220.00")

    def test_computed_field_with_child_tables(self) -> None:
        """Computed fields should work with child table data."""
        invoice = Invoice(
            name="INV-001",
            customer="Acme Corp",
            items=[
                InvoiceItem(
                    name="INV-001-1",
                    item="Widget",
                    quantity=2,
                    rate=Decimal("50.00"),
                ),
                InvoiceItem(
                    name="INV-001-2",
                    item="Gadget",
                    quantity=3,
                    rate=Decimal("30.00"),
                ),
            ],
        )

        # Verify child item computed fields
        assert invoice.items[0].amount == Decimal("100.00")  # 2 * 50
        assert invoice.items[1].amount == Decimal("90.00")  # 3 * 30

        # Verify parent computed fields
        assert invoice.total == Decimal("190.00")  # 100 + 90
        assert invoice.item_count == 2

    def test_computed_field_with_empty_list(self) -> None:
        """Computed fields should handle empty child lists."""
        invoice = Invoice(
            name="INV-002",
            customer="Beta Inc",
            items=[],
        )

        assert invoice.total == Decimal("0")
        assert invoice.item_count == 0


class TestComputedFieldSerialization:
    """Test that computed fields are included in serialization."""

    def test_computed_field_in_model_dump(self) -> None:
        """Computed fields should be included in model_dump()."""
        product = Product(
            name="Widget",
            price=Decimal("100.00"),
        )

        data = product.model_dump()

        # Regular fields
        assert data["name"] == "Widget"
        assert data["price"] == Decimal("100.00")

        # Computed field should be included
        assert "price_with_tax" in data
        assert data["price_with_tax"] == Decimal("110.00")

    def test_computed_field_in_json_serialization(self) -> None:
        """Computed fields should be included in JSON."""
        product = Product(
            name="Widget",
            price=Decimal("100.00"),
        )

        json_str = product.model_dump_json()

        # Should include computed field
        assert "price_with_tax" in json_str

    def test_computed_field_with_nested_child_tables(self) -> None:
        """Computed fields should serialize with child tables."""
        invoice = Invoice(
            name="INV-003",
            customer="Gamma Ltd",
            items=[
                InvoiceItem(
                    name="INV-003-1",
                    item="Widget",
                    quantity=1,
                    rate=Decimal("100.00"),
                ),
            ],
        )

        data = invoice.model_dump()

        # Parent computed fields
        assert data["total"] == Decimal("100.00")
        assert data["item_count"] == 1

        # Child computed fields
        assert data["items"][0]["amount"] == Decimal("100.00")


class TestComputedFieldSchemaExclusion:
    """Test that computed fields are excluded from database schema."""

    def test_computed_fields_not_in_model_fields(self) -> None:
        """Computed fields should not appear in model_fields."""
        # Pydantic's computed_field are stored separately
        assert "price_with_tax" not in Product.model_fields
        assert "total" not in Invoice.model_fields
        assert "item_count" not in Invoice.model_fields

    def test_computed_fields_in_model_computed_fields(self) -> None:
        """Computed fields should appear in model_computed_fields."""
        # Verify they're registered as computed fields
        assert "price_with_tax" in Product.model_computed_fields
        assert "total" in Invoice.model_computed_fields
        assert "item_count" in Invoice.model_computed_fields
        assert "amount" in InvoiceItem.model_computed_fields

    @pytest.mark.asyncio
    async def test_schema_mapper_excludes_computed_fields(self) -> None:
        """SchemaMapper should not create columns for computed fields."""
        from sqlalchemy import MetaData

        from framework_m.adapters.db.schema_mapper import SchemaMapper

        mapper = SchemaMapper()
        metadata = MetaData()

        # Create table for Product
        table = mapper.create_table(Product, metadata)

        # Regular fields should have columns
        assert "name" in table.c
        assert "price" in table.c
        assert "tax_rate" in table.c

        # Computed field should NOT have a column
        assert "price_with_tax" not in table.c

    @pytest.mark.asyncio
    async def test_child_table_excludes_computed_fields(self) -> None:
        """Child tables should not create columns for computed fields."""
        from sqlalchemy import MetaData

        from framework_m.adapters.db.schema_mapper import SchemaMapper

        mapper = SchemaMapper()
        metadata = MetaData()

        # Create table for InvoiceItem (child)
        table = mapper.create_table(InvoiceItem, metadata)

        # Regular fields
        assert "item" in table.c
        assert "quantity" in table.c
        assert "rate" in table.c

        # Computed field should NOT have a column
        assert "amount" not in table.c


class TestComputedFieldDatabaseOperations:
    """Test that computed fields work correctly with database operations."""

    @pytest.mark.asyncio
    async def test_save_and_load_with_computed_fields(
        self, test_engine, clean_tables
    ) -> None:
        """Saving and loading should preserve computed field calculations."""
        from sqlalchemy import MetaData
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        from framework_m.adapters.db.generic_repository import GenericRepository
        from framework_m.adapters.db.schema_mapper import SchemaMapper
        from framework_m.adapters.db.table_registry import TableRegistry

        # Setup
        mapper = SchemaMapper()
        metadata = MetaData()
        product_table = mapper.create_table(Product, metadata)

        table_registry = TableRegistry()
        table_registry.register_table(Product.__name__, product_table)

        async with test_engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

        # Create product
        product = Product(
            name="Super Widget",
            price=Decimal("200.00"),
            tax_rate=Decimal("0.20"),
        )

        # Verify computed field before save
        assert product.price_with_tax == Decimal("240.00")

        # Save
        repo = GenericRepository(Product, product_table)
        async_session_maker = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )

        product_id = None
        async with async_session_maker() as session:
            saved_product = await repo.save(session, product)
            await session.commit()
            product_id = saved_product.id

        # Load
        async with async_session_maker() as session:
            loaded_product = await repo.get(session, product_id)

            assert loaded_product is not None
            assert loaded_product.name == "Super Widget"
            assert loaded_product.price == Decimal("200.00")
            assert loaded_product.tax_rate == Decimal("0.20")

            # Computed field should still work after loading
            assert loaded_product.price_with_tax == Decimal("240.00")

    @pytest.mark.asyncio
    async def test_save_load_invoice_with_computed_totals(
        self, test_engine, clean_tables
    ) -> None:
        """Invoice with child items should compute totals correctly after load."""
        from sqlalchemy import MetaData
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        from framework_m.adapters.db.generic_repository import GenericRepository
        from framework_m.adapters.db.schema_mapper import SchemaMapper
        from framework_m.adapters.db.table_registry import TableRegistry

        # Setup
        mapper = SchemaMapper()
        metadata = MetaData()
        invoice_table = mapper.create_table(Invoice, metadata)
        item_table = mapper.create_table(InvoiceItem, metadata)

        table_registry = TableRegistry()
        table_registry.register_table(Invoice.__name__, invoice_table)
        table_registry.register_table(InvoiceItem.__name__, item_table)

        async with test_engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

        # Create invoice
        invoice = Invoice(
            name="INV-100",
            customer="Delta Corp",
            items=[
                InvoiceItem(
                    name="INV-100-1",
                    item="Product A",
                    quantity=5,
                    rate=Decimal("10.00"),
                ),
                InvoiceItem(
                    name="INV-100-2",
                    item="Product B",
                    quantity=2,
                    rate=Decimal("25.00"),
                ),
            ],
        )

        # Verify computed fields before save
        assert invoice.total == Decimal("100.00")  # 50 + 50
        assert invoice.item_count == 2

        # Save
        repo = GenericRepository(Invoice, invoice_table)
        async_session_maker = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )

        invoice_id = None
        async with async_session_maker() as session:
            saved_invoice = await repo.save(session, invoice)
            await session.commit()
            invoice_id = saved_invoice.id

        # Load
        async with async_session_maker() as session:
            loaded_invoice = await repo.get(session, invoice_id)

            assert loaded_invoice is not None
            assert loaded_invoice.customer == "Delta Corp"
            assert len(loaded_invoice.items) == 2

            # Computed fields on children
            assert loaded_invoice.items[0].amount == Decimal("50.00")
            assert loaded_invoice.items[1].amount == Decimal("50.00")

            # Computed fields on parent
            assert loaded_invoice.total == Decimal("100.00")
            assert loaded_invoice.item_count == 2


class TestEdgeCases:
    """Test edge cases for computed fields."""

    def test_computed_field_with_none_values(self) -> None:
        """Computed fields should handle None gracefully."""

        class OptionalProduct(DocType):
            """Product with optional price."""

            name: str
            price: Decimal | None = None

            @computed_field  # type: ignore[prop-decorator]
            @property
            def display_price(self) -> str:
                """Display price or 'N/A'."""
                return f"${self.price}" if self.price is not None else "N/A"

        product = OptionalProduct(name="Mystery Box")
        assert product.display_price == "N/A"

        product = OptionalProduct(name="Widget", price=Decimal("50.00"))
        assert product.display_price == "$50.00"

    def test_multiple_computed_fields(self) -> None:
        """DocType can have multiple computed fields."""

        class Stats(DocType):
            """Stats with multiple computed values."""

            count: int
            sum: Decimal

            @computed_field  # type: ignore[prop-decorator]
            @property
            def average(self) -> Decimal:
                """Average value."""
                if self.count == 0:
                    return Decimal("0")
                return self.sum / Decimal(str(self.count))

            @computed_field  # type: ignore[prop-decorator]
            @property
            def is_empty(self) -> bool:
                """Check if stats are empty."""
                return self.count == 0

        stats = Stats(name="test", count=5, sum=Decimal("100"))
        assert stats.average == Decimal("20")
        assert stats.is_empty is False

        empty_stats = Stats(name="empty", count=0, sum=Decimal("0"))
        assert empty_stats.average == Decimal("0")
        assert empty_stats.is_empty is True
