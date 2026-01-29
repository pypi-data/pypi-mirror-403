"""Tests for Validation Rules.

Tests for Pydantic field validators (Section 8.1) and
controller validate() hook (Section 8.2).
"""

from decimal import Decimal

import pytest
from pydantic import ValidationError, field_validator
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from framework_m.adapters.db.generic_repository import GenericRepository
from framework_m.adapters.db.schema_mapper import SchemaMapper
from framework_m.adapters.db.table_registry import TableRegistry
from framework_m.core.domain.base_controller import BaseController
from framework_m.core.domain.base_doctype import BaseDocType, Field

# =============================================================================
# Test Models with Field Validators
# =============================================================================


class Invoice(BaseDocType):
    """Invoice with field-level validation."""

    customer: str = Field(description="Customer name")
    total: Decimal = Field(default=Decimal("0"), description="Invoice total")

    @field_validator("total")
    @classmethod
    def validate_total_not_negative(cls, v: Decimal) -> Decimal:
        """Total cannot be negative."""
        if v < 0:
            raise ValueError("Total cannot be negative")
        return v

    @field_validator("customer")
    @classmethod
    def validate_customer_not_empty(cls, v: str) -> str:
        """Customer name cannot be empty."""
        if not v.strip():
            raise ValueError("Customer name cannot be empty")
        return v.strip()


class Product(BaseDocType):
    """Product with multiple field validators."""

    name: str = Field(description="Product name")
    sku: str = Field(description="Stock keeping unit")
    price: Decimal = Field(default=Decimal("0"), description="Unit price")
    quantity: int = Field(default=0, description="Stock quantity")

    @field_validator("sku")
    @classmethod
    def validate_sku_format(cls, v: str) -> str:
        """SKU must be uppercase alphanumeric."""
        if not v.isalnum():
            raise ValueError("SKU must be alphanumeric")
        return v.upper()

    @field_validator("price")
    @classmethod
    def validate_price_positive(cls, v: Decimal) -> Decimal:
        """Price must be positive."""
        if v < 0:
            raise ValueError("Price must be non-negative")
        return v

    @field_validator("quantity")
    @classmethod
    def validate_quantity_non_negative(cls, v: int) -> int:
        """Quantity cannot be negative."""
        if v < 0:
            raise ValueError("Quantity cannot be negative")
        return v


# =============================================================================
# Test Models with Controller Validation
# =============================================================================


class Order(BaseDocType):
    """Order with document-level validation in controller."""

    customer: str
    subtotal: Decimal = Field(default=Decimal("0"))
    tax: Decimal = Field(default=Decimal("0"))
    total: Decimal = Field(default=Decimal("0"))


class OrderController(BaseController[Order]):
    """Controller with document-level validation."""

    async def validate(self, context=None) -> None:
        """Validate that total equals subtotal + tax."""
        expected_total = self.doc.subtotal + self.doc.tax
        if self.doc.total != expected_total:
            raise ValueError(
                f"Total mismatch: expected {expected_total}, got {self.doc.total}"
            )


# =============================================================================
# Test Field Validators (Section 8.1)
# =============================================================================


class TestFieldValidators:
    """Test Pydantic field_validator for field-level validation."""

    def test_valid_invoice_creation(self):
        """Invoice with valid data should be created."""
        invoice = Invoice(customer="Acme Corp", total=Decimal("100.00"))
        assert invoice.customer == "Acme Corp"
        assert invoice.total == Decimal("100.00")

    def test_negative_total_rejected(self):
        """Invoice with negative total should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Invoice(customer="Test", total=Decimal("-50"))

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "Total cannot be negative" in str(errors[0]["msg"])

    def test_empty_customer_rejected(self):
        """Invoice with empty customer should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Invoice(customer="   ", total=Decimal("100"))

        errors = exc_info.value.errors()
        assert "Customer name cannot be empty" in str(errors[0]["msg"])

    def test_customer_name_trimmed(self):
        """Customer name should be trimmed of whitespace."""
        invoice = Invoice(customer="  Acme Corp  ", total=Decimal("100"))
        assert invoice.customer == "Acme Corp"

    def test_product_sku_uppercased(self):
        """SKU should be converted to uppercase."""
        product = Product(name="Widget", sku="abc123", price=Decimal("10"))
        assert product.sku == "ABC123"

    def test_product_sku_alphanumeric_only(self):
        """SKU must be alphanumeric."""
        with pytest.raises(ValidationError) as exc_info:
            Product(name="Widget", sku="ABC-123", price=Decimal("10"))

        errors = exc_info.value.errors()
        assert "SKU must be alphanumeric" in str(errors[0]["msg"])

    def test_product_negative_price_rejected(self):
        """Product with negative price should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Product(name="Widget", sku="ABC123", price=Decimal("-5"))

        errors = exc_info.value.errors()
        assert "Price must be non-negative" in str(errors[0]["msg"])

    def test_product_negative_quantity_rejected(self):
        """Product with negative quantity should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Product(name="Widget", sku="ABC123", price=Decimal("10"), quantity=-5)

        errors = exc_info.value.errors()
        assert "Quantity cannot be negative" in str(errors[0]["msg"])


# =============================================================================
# Test Controller Validation (Section 8.2)
# =============================================================================


class TestControllerValidation:
    """Test controller validate() hook for document-level validation."""

    @pytest.mark.asyncio
    async def test_valid_order_passes_validation(self):
        """Order with correct total should pass validation."""
        order = Order(
            customer="Test",
            subtotal=Decimal("100"),
            tax=Decimal("10"),
            total=Decimal("110"),
        )
        controller = OrderController(order)
        # Should not raise
        await controller.validate()

    @pytest.mark.asyncio
    async def test_invalid_total_fails_validation(self):
        """Order with incorrect total should fail validation."""
        order = Order(
            customer="Test",
            subtotal=Decimal("100"),
            tax=Decimal("10"),
            total=Decimal("120"),  # Wrong! Should be 110
        )
        controller = OrderController(order)

        with pytest.raises(ValueError) as exc_info:
            await controller.validate()

        assert "Total mismatch" in str(exc_info.value)
        assert "expected 110" in str(exc_info.value)


# =============================================================================
# Test Repository Integration with Validators
# =============================================================================


class TestValidatorIntegration:
    """Test that validators work correctly when saving via repository."""

    @pytest.mark.asyncio
    async def test_field_validation_on_model_creation(self, test_engine):
        """Field validators should run when creating model instance."""
        # This should fail at model creation, before repository
        with pytest.raises(ValidationError):
            Invoice(customer="", total=Decimal("-10"))

    @pytest.mark.asyncio
    async def test_controller_validation_on_save(self, test_engine):
        """Controller validate() should be called during repository save."""
        # Setup
        metadata = MetaData()
        mapper = SchemaMapper()

        table_registry = TableRegistry()
        table_registry.reset()

        order_table = mapper.create_table(Order, metadata)
        table_registry.register_table(Order.__name__, order_table)

        async with test_engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

        order_repo = GenericRepository(
            Order, order_table, controller_class=OrderController
        )
        async_session_maker = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )

        # Create order with wrong total
        order = Order(
            customer="Test",
            subtotal=Decimal("100"),
            tax=Decimal("10"),
            total=Decimal("999"),  # Wrong!
        )

        # Save should fail due to controller validation
        async with async_session_maker() as session:
            with pytest.raises(ValueError) as exc_info:
                await order_repo.save(session, order)

            assert "Total mismatch" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_valid_order_saves_successfully(self, test_engine):
        """Valid order with correct total should save successfully."""
        # Setup
        metadata = MetaData()
        mapper = SchemaMapper()

        table_registry = TableRegistry()
        table_registry.reset()

        order_table = mapper.create_table(Order, metadata)
        table_registry.register_table(Order.__name__, order_table)

        async with test_engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

        order_repo = GenericRepository(
            Order, order_table, controller_class=OrderController
        )
        async_session_maker = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )

        # Create valid order
        order = Order(
            customer="Test",
            subtotal=Decimal("100"),
            tax=Decimal("10"),
            total=Decimal("110"),  # Correct!
        )

        async with async_session_maker() as session:
            saved = await order_repo.save(session, order)
            await session.commit()

        assert saved.name is not None
        assert saved.total == Decimal("110")
