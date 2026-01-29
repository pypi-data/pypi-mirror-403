"""Tests for MetaRegistry DocType override functionality."""

from __future__ import annotations

import pytest

from framework_m import DocType, Field
from framework_m.core.registry import MetaRegistry


class User(DocType):
    """Base User DocType for testing overrides."""

    email: str = Field(description="User email")
    is_active: bool = True

    class Meta:
        table_name = "tab_user"


class ExtendedUser(User):
    """Extended User with additional fields."""

    department: str = Field(description="Department")
    employee_id: str | None = None


class AnotherExtendedUser(User):
    """Another extension of User."""

    phone: str = Field(description="Phone number")
    location: str = "Unknown"


class Product(DocType):
    """Base Product DocType."""

    name: str = Field(description="Product name")
    price: float = 0.0


class ExtendedProduct(Product):
    """Extended Product with SKU."""

    sku: str = Field(description="Stock keeping unit")


# ============================================================================
# Test: Override Registration
# ============================================================================


class TestOverrideRegistration:
    """Test registering DocType overrides."""

    def setup_method(self) -> None:
        """Clear registry before each test."""
        MetaRegistry().clear()

    def test_register_override_stores_mapping(self) -> None:
        """register_override should store base -> override mapping."""
        registry = MetaRegistry()
        registry.register_doctype(User)

        registry.register_override("User", ExtendedUser)

        # Should be able to retrieve override
        assert registry.has_override("User")

    def test_register_override_for_nonexistent_base_raises(self) -> None:
        """register_override should raise if base DocType not registered."""
        registry = MetaRegistry()

        with pytest.raises(KeyError, match="Base DocType 'User' not registered"):
            registry.register_override("User", ExtendedUser)

    def test_register_override_validates_inheritance(self) -> None:
        """register_override should validate that override extends base."""
        registry = MetaRegistry()
        registry.register_doctype(User)
        registry.register_doctype(Product)

        # ExtendedProduct does not inherit from User
        with pytest.raises(
            ValueError, match="Override class must inherit from base DocType"
        ):
            registry.register_override("User", ExtendedProduct)

    def test_register_multiple_overrides_for_same_base_raises(self) -> None:
        """register_override should only allow one override per base."""
        registry = MetaRegistry()
        registry.register_doctype(User)
        registry.register_override("User", ExtendedUser)

        with pytest.raises(ValueError, match="already has an override registered"):
            registry.register_override("User", AnotherExtendedUser)

    def test_has_override_returns_false_when_no_override(self) -> None:
        """has_override should return False when no override registered."""
        registry = MetaRegistry()
        registry.register_doctype(User)

        assert not registry.has_override("User")

    def test_has_override_returns_true_when_override_exists(self) -> None:
        """has_override should return True when override is registered."""
        registry = MetaRegistry()
        registry.register_doctype(User)
        registry.register_override("User", ExtendedUser)

        assert registry.has_override("User")


# ============================================================================
# Test: Getting DocType with Overrides
# ============================================================================


class TestGetDocTypeWithOverrides:
    """Test get_doctype returns override when registered."""

    def setup_method(self) -> None:
        """Clear registry before each test."""
        MetaRegistry().clear()

    def test_get_doctype_returns_base_when_no_override(self) -> None:
        """get_doctype should return base class when no override."""
        registry = MetaRegistry()
        registry.register_doctype(User)

        result = registry.get_doctype("User")

        assert result is User

    def test_get_doctype_returns_override_when_registered(self) -> None:
        """get_doctype should return override class when registered."""
        registry = MetaRegistry()
        registry.register_doctype(User)
        registry.register_override("User", ExtendedUser)

        result = registry.get_doctype("User")

        assert result is ExtendedUser

    def test_get_doctype_override_has_base_fields(self) -> None:
        """Override class should have all base class fields."""
        registry = MetaRegistry()
        registry.register_doctype(User)
        registry.register_override("User", ExtendedUser)

        override_class = registry.get_doctype("User")

        # Should have base fields
        assert "email" in override_class.model_fields
        assert "is_active" in override_class.model_fields

        # Should have new fields
        assert "department" in override_class.model_fields
        assert "employee_id" in override_class.model_fields

    def test_get_doctype_override_inherits_meta(self) -> None:
        """Override class should inherit Meta from base."""
        registry = MetaRegistry()
        registry.register_doctype(User)
        registry.register_override("User", ExtendedUser)

        override_class = registry.get_doctype("User")

        # Should inherit Meta from base
        # ExtendedUser doesn't override Meta.table_name, so it inherits from User
        assert hasattr(override_class, "Meta")
        assert hasattr(override_class.Meta, "table_name")
        assert override_class.Meta.table_name == "tab_user"

    def test_multiple_doctypes_can_have_different_overrides(self) -> None:
        """Different DocTypes can have independent overrides."""
        registry = MetaRegistry()
        registry.register_doctype(User)
        registry.register_doctype(Product)
        registry.register_override("User", ExtendedUser)
        registry.register_override("Product", ExtendedProduct)

        user_class = registry.get_doctype("User")
        product_class = registry.get_doctype("Product")

        assert user_class is ExtendedUser
        assert product_class is ExtendedProduct


# ============================================================================
# Test: Clear and Reset
# ============================================================================


class TestOverrideClear:
    """Test clearing overrides."""

    def setup_method(self) -> None:
        """Clear registry before each test."""
        MetaRegistry().clear()

    def test_clear_removes_overrides(self) -> None:
        """clear() should remove all overrides."""
        registry = MetaRegistry()
        registry.register_doctype(User)
        registry.register_override("User", ExtendedUser)

        registry.clear()

        # After clear, no DocTypes or overrides should exist
        assert registry.list_doctypes() == []

    def test_can_register_new_override_after_clear(self) -> None:
        """After clear, can register new overrides."""
        registry = MetaRegistry()
        registry.register_doctype(User)
        registry.register_override("User", ExtendedUser)
        registry.clear()

        # Register fresh
        registry.register_doctype(User)
        registry.register_override("User", AnotherExtendedUser)

        result = registry.get_doctype("User")
        assert result is AnotherExtendedUser


# ============================================================================
# Test: Edge Cases
# ============================================================================


class TestOverrideEdgeCases:
    """Test edge cases for override functionality."""

    def setup_method(self) -> None:
        """Clear registry before each test."""
        MetaRegistry().clear()

    def test_override_with_same_class_as_base_is_noop(self) -> None:
        """Registering base class as override should work (no-op)."""
        registry = MetaRegistry()
        registry.register_doctype(User)

        # This should work - registering User as override of User
        registry.register_override("User", User)

        result = registry.get_doctype("User")
        assert result is User

    def test_get_override_class_returns_none_when_no_override(self) -> None:
        """get_override_class should return None when no override."""
        registry = MetaRegistry()
        registry.register_doctype(User)

        result = registry.get_override_class("User")

        assert result is None

    def test_get_override_class_returns_override_when_registered(self) -> None:
        """get_override_class should return override class."""
        registry = MetaRegistry()
        registry.register_doctype(User)
        registry.register_override("User", ExtendedUser)

        result = registry.get_override_class("User")

        assert result is ExtendedUser

    def test_has_override_returns_false_for_nonexistent_doctype(self) -> None:
        """has_override should return False for non-existent DocType."""
        registry = MetaRegistry()

        assert not registry.has_override("NonExistent")
