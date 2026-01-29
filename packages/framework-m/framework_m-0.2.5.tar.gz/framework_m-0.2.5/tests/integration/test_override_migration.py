"""Integration tests for DocType override schema migration.

Tests end-to-end override functionality including:
- Registering DocType overrides
- Schema evolution with overrides
- Data preservation across overrides
"""

from __future__ import annotations

from typing import ClassVar

import pytest
from pydantic import Field

from framework_m.core.domain.base_doctype import BaseDocType
from framework_m.core.registry import MetaRegistry

# ============================================================================
# Base DocTypes
# ============================================================================


class BaseProduct(BaseDocType):
    """Base product DocType."""

    __doctype_name__: ClassVar[str] = "BaseProduct"

    name: str = Field(description="Product name")
    price: float = Field(description="Product price", ge=0)
    sku: str = Field(description="Stock keeping unit")

    class Meta:
        """DocType metadata."""

        table_name: ClassVar[str] = "base_product"


class ExtendedProduct(BaseProduct):
    """Extended product with additional fields."""

    __doctype_name__: ClassVar[str] = "ExtendedProduct"

    category: str = Field(default="General", description="Product category")
    weight: float | None = Field(default=None, description="Product weight in kg")

    class Meta:
        """DocType metadata."""

        table_name: ClassVar[str] = "base_product"


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def clear_registry() -> None:
    """Clear the MetaRegistry singleton before each test."""
    registry = MetaRegistry()
    registry.clear()
    yield
    registry.clear()


# ============================================================================
# Tests
# ============================================================================


class TestOverrideRegistration:
    """Test registering DocType overrides."""

    def test_register_override(self) -> None:
        """Test that override can be registered."""
        registry = MetaRegistry()
        registry.register_doctype(BaseProduct)
        registry.register_override("BaseProduct", ExtendedProduct)

        assert registry.has_override("BaseProduct")
        override = registry.get_override_class("BaseProduct")
        assert override is ExtendedProduct

    def test_get_doctype_returns_override(self) -> None:
        """Test that get_doctype returns override when registered."""
        registry = MetaRegistry()
        registry.register_doctype(BaseProduct)
        registry.register_override("BaseProduct", ExtendedProduct)

        doctype = registry.get_doctype("BaseProduct")
        assert doctype is ExtendedProduct

    def test_override_has_base_fields(self) -> None:
        """Test that override has all base fields."""
        product = ExtendedProduct(
            name="Test Product",
            price=99.99,
            sku="TEST-001",
            category="Electronics",
        )

        # Base fields
        assert product.name == "Test Product"
        assert product.price == 99.99
        assert product.sku == "TEST-001"

        # Extended fields
        assert product.category == "Electronics"
        assert product.weight is None

    def test_override_inherits_validators(self) -> None:
        """Test that override inherits base validators."""
        with pytest.raises(ValueError):
            ExtendedProduct(
                name="Invalid",
                price=-10.00,  # Negative price should fail
                sku="TEST-002",
            )


class TestOverrideSchemaEvolution:
    """Test schema evolution with overrides."""

    def test_extended_product_has_new_fields(self) -> None:
        """Test that extended product has new fields."""
        product = ExtendedProduct(
            name="Widget",
            price=29.99,
            sku="WGT-001",
            category="Widgets",
            weight=0.5,
        )

        assert product.category == "Widgets"
        assert product.weight == 0.5

    def test_extended_product_default_values(self) -> None:
        """Test that extended fields have proper defaults."""
        product = ExtendedProduct(
            name="Simple Widget",
            price=19.99,
            sku="SMP-001",
        )

        assert product.category == "General"  # Default value
        assert product.weight is None  # Optional, defaults to None

    def test_base_and_extended_are_compatible(self) -> None:
        """Test that base and extended types are compatible."""
        base_data = {
            "name": "Base Widget",
            "price": 15.99,
            "sku": "BSE-001",
        }

        # Should work for both types
        base = BaseProduct(**base_data)
        extended = ExtendedProduct(**base_data)

        assert base.name == extended.name
        assert base.price == extended.price
        assert base.sku == extended.sku


class TestOverrideMetadata:
    """Test override metadata handling."""

    def test_override_uses_same_table(self) -> None:
        """Test that override uses same table as base."""
        assert hasattr(BaseProduct.Meta, "table_name")
        assert hasattr(ExtendedProduct.Meta, "table_name")
        assert BaseProduct.Meta.table_name == ExtendedProduct.Meta.table_name

    def test_override_doctype_name(self) -> None:
        """Test that override has its own doctype name."""
        assert BaseProduct.__doctype_name__ == "BaseProduct"
        assert ExtendedProduct.__doctype_name__ == "ExtendedProduct"


class TestOverrideClear:
    """Test clearing overrides."""

    def test_clear_override(self) -> None:
        """Test that override can be cleared."""
        registry = MetaRegistry()
        registry.register_doctype(BaseProduct)
        registry.register_override("BaseProduct", ExtendedProduct)

        assert registry.has_override("BaseProduct")

        registry.clear()

        assert not registry.has_override("BaseProduct")

    def test_get_doctype_after_clear(self) -> None:
        """Test that get_doctype returns base after clear and re-register."""
        registry = MetaRegistry()
        registry.register_doctype(BaseProduct)
        registry.register_override("BaseProduct", ExtendedProduct)

        # Override should be active
        assert registry.get_doctype("BaseProduct") is ExtendedProduct

        registry.clear()

        # Re-register base (without override)
        registry.register_doctype(BaseProduct)

        # Should now return base, not override
        doctype = registry.get_doctype("BaseProduct")
        assert doctype is BaseProduct
        assert not registry.has_override("BaseProduct")
