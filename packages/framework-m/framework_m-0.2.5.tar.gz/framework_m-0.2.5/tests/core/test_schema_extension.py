"""Tests for Schema Extension - DocType Override Field Merging.

This module tests the schema merging functionality that allows
override DocTypes to:
- Add new fields to base DocTypes
- Modify field properties (description, default values)
- Preserve all base fields (cannot remove)
- Handle field type compatibility
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import Field
from pydantic.fields import FieldInfo
from sqlalchemy import MetaData

from framework_m.adapters.db.schema_mapper import SchemaMapper
from framework_m.core.domain.base_doctype import BaseDocType


# Test Fixtures
class User(BaseDocType):
    """Base User DocType."""

    email: str = Field(description="User email address")
    is_active: bool = True


class ExtendedUser(User):
    """Override User with additional fields."""

    department: str = Field(description="Department name")
    employee_id: str | None = None


class Product(BaseDocType):
    """Base Product DocType."""

    name: str = Field(description="Product name")
    price: Decimal = Field(default=Decimal("0.00"), description="Product price")


class ExtendedProduct(Product):
    """Override Product with modified field property."""

    # Override description for price field
    price: Decimal = Field(default=Decimal("0.00"), description="Product price in USD")
    # Add new field
    sku: str = Field(description="Stock keeping unit")


class InvalidOverride(User):
    """Invalid override - tries to change field type."""

    # This should fail validation - changing email from str to int
    email: int = Field(description="User email (invalid)")  # type: ignore[assignment]


# Test Classes
class TestSchemaMerging:
    """Test basic field merging from base and override."""

    def test_merge_includes_base_fields(self) -> None:
        """Override schema should include all base fields."""
        # Get fields from override class
        override_fields = ExtendedUser.model_fields

        # Should include base fields
        assert "email" in override_fields
        assert "is_active" in override_fields

        # Should include new fields
        assert "department" in override_fields
        assert "employee_id" in override_fields

    def test_merge_includes_standard_fields(self) -> None:
        """Override schema should include standard BaseDocType fields."""
        override_fields = ExtendedUser.model_fields

        # Standard fields from BaseDocType
        assert "id" in override_fields
        assert "name" in override_fields
        assert "creation" in override_fields
        assert "modified" in override_fields
        assert "owner" in override_fields

    def test_table_creation_with_override(self) -> None:
        """SchemaMapper should create table with all merged fields."""
        mapper = SchemaMapper()
        metadata = MetaData()

        table = mapper.create_table(ExtendedUser, metadata)

        # Base fields present
        assert "email" in table.c
        assert "is_active" in table.c

        # New fields present
        assert "department" in table.c
        assert "employee_id" in table.c

        # Standard fields present
        assert "id" in table.c
        assert "name" in table.c
        assert "creation" in table.c

    def test_field_count_matches_merged_schema(self) -> None:
        """Table should have correct number of columns."""
        mapper = SchemaMapper()
        metadata = MetaData()

        table = mapper.create_table(ExtendedUser, metadata)

        # Count fields in model
        model_field_count = len(ExtendedUser.model_fields)

        # Table columns (model fields, no _version in this case)
        # id, name, creation, modified, modified_by, owner, deleted_at = 7 standard
        # email, is_active = 2 base
        # department, employee_id = 2 override
        # Total = 11
        expected_columns = model_field_count
        actual_columns = len(table.c)

        assert actual_columns == expected_columns


class TestFieldPropertyModification:
    """Test modifying field properties in overrides."""

    def test_override_field_description(self) -> None:
        """Override can modify field description."""
        base_field = Product.model_fields["price"]
        override_field = ExtendedProduct.model_fields["price"]

        # Descriptions should differ
        assert base_field.description == "Product price"
        assert override_field.description == "Product price in USD"

    def test_override_preserves_field_type(self) -> None:
        """Override should preserve base field types."""
        base_field = Product.model_fields["price"]
        override_field = ExtendedProduct.model_fields["price"]

        # Both should be Decimal
        assert base_field.annotation == Decimal
        assert override_field.annotation == Decimal

    def test_override_adds_new_fields(self) -> None:
        """Override can add new fields not in base."""
        base_fields = Product.model_fields
        override_fields = ExtendedProduct.model_fields

        # New field only in override
        assert "sku" not in base_fields
        assert "sku" in override_fields

    def test_table_reflects_field_modifications(self) -> None:
        """Table should include both base and modified fields."""
        mapper = SchemaMapper()
        metadata = MetaData()

        table = mapper.create_table(ExtendedProduct, metadata)

        # All fields present
        assert "name" in table.c  # Base field
        assert "price" in table.c  # Modified field
        assert "sku" in table.c  # New field


class TestBaseFieldPreservation:
    """Test that base fields cannot be removed."""

    def test_base_fields_always_present(self) -> None:
        """Override cannot remove base fields."""
        override_fields = ExtendedUser.model_fields

        # All base User fields must be present
        assert "email" in override_fields
        assert "is_active" in override_fields

    def test_standard_fields_always_present(self) -> None:
        """Override cannot remove standard BaseDocType fields."""
        override_fields = ExtendedUser.model_fields

        # Standard fields must be present
        required_standard_fields = [
            "id",
            "name",
            "creation",
            "modified",
            "modified_by",
            "owner",
            "deleted_at",
        ]

        for field_name in required_standard_fields:
            assert field_name in override_fields

    def test_table_has_all_base_columns(self) -> None:
        """Table must include all base columns."""
        mapper = SchemaMapper()
        metadata = MetaData()

        base_table = mapper.create_table(User, metadata)
        override_table = mapper.create_table(ExtendedUser, metadata)

        # Every base column must exist in override table
        for col in base_table.c:
            assert col.name in override_table.c


class TestFieldTypeCompatibility:
    """Test field type validation and compatibility."""

    def test_compatible_nullable_modification(self) -> None:
        """Override can make required field optional."""

        class StrictProduct(BaseDocType):
            name: str = Field(description="Required name")

        class FlexibleProduct(StrictProduct):
            name: str | None = Field(default=None, description="Optional name")

        # Both should work
        override_fields = FlexibleProduct.model_fields
        assert "name" in override_fields

        # Type should be str | None
        field_type = override_fields["name"].annotation
        # Check if Union type with None
        from typing import get_args

        args = get_args(field_type)
        assert str in args
        assert type(None) in args

    def test_incompatible_type_change_fails(self) -> None:
        """Changing field type should cause validation issues."""
        # InvalidOverride changes email from str to int
        # This will fail at runtime when trying to create instance
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            # Try to create instance with string email (should fail)
            InvalidOverride(email="test@example.com")  # type: ignore[arg-type]


class TestMultipleLevelsOfInheritance:
    """Test schema extension across multiple inheritance levels."""

    def test_three_level_inheritance(self) -> None:
        """Schema merging should work with multiple inheritance levels."""

        class BaseEmployee(BaseDocType):
            employee_name: str = Field(description="Employee name")

        class Manager(BaseEmployee):
            team_size: int = Field(default=0, description="Team size")

        class Director(Manager):
            department: str = Field(description="Department")

        # Director should have all fields
        director_fields = Director.model_fields

        assert "employee_name" in director_fields  # From BaseEmployee
        assert "team_size" in director_fields  # From Manager
        assert "department" in director_fields  # From Director

        # Create table
        mapper = SchemaMapper()
        metadata = MetaData()
        table = mapper.create_table(Director, metadata)

        # All fields in table
        assert "employee_name" in table.c
        assert "team_size" in table.c
        assert "department" in table.c

    def test_field_override_at_multiple_levels(self) -> None:
        """Field can be overridden at multiple inheritance levels."""

        class Level1(BaseDocType):
            description: str = Field(description="Level 1 description")

        class Level2(Level1):
            description: str = Field(description="Level 2 description")

        class Level3(Level2):
            description: str = Field(description="Level 3 description")

        # Final description should be from Level3
        field_info = Level3.model_fields["description"]
        assert field_info.description == "Level 3 description"


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_override_with_no_new_fields(self) -> None:
        """Override can exist with no new fields (only modifies existing)."""

        class SimpleUser(User):
            # Just modify description, no new fields
            email: str = Field(description="Corporate email address")

        # Should still work
        fields = SimpleUser.model_fields
        assert "email" in fields
        assert fields["email"].description == "Corporate email address"

    def test_override_only_adds_fields(self) -> None:
        """Override can only add fields without modifying existing ones."""

        class UserWithPhone(User):
            # Only add new field
            phone: str = Field(description="Phone number")

        fields = UserWithPhone.model_fields

        # Base fields unchanged
        assert fields["email"].description == "User email address"

        # New field present
        assert "phone" in fields

    def test_empty_override(self) -> None:
        """Override with no changes should work."""

        class UnchangedUser(User):
            pass

        # Should have same fields as User
        assert set(User.model_fields.keys()) == set(UnchangedUser.model_fields.keys())

    def test_complex_field_types(self) -> None:
        """Override should handle complex field types."""

        class Document(BaseDocType):
            tags: list[str] = Field(default_factory=list, description="Tags")
            metadata_dict: dict[str, str] = Field(
                default_factory=dict, description="Metadata"
            )

        class ExtendedDocument(Document):
            categories: list[str] = Field(
                default_factory=list, description="Categories"
            )
            settings: dict[str, int] = Field(
                default_factory=dict, description="Settings"
            )

        # All complex fields should be present
        fields = ExtendedDocument.model_fields

        assert "tags" in fields
        assert "metadata_dict" in fields
        assert "categories" in fields
        assert "settings" in fields

        # Create table (complex types become JSON columns)
        mapper = SchemaMapper()
        metadata = MetaData()
        table = mapper.create_table(ExtendedDocument, metadata)

        assert "tags" in table.c
        assert "metadata_dict" in table.c
        assert "categories" in table.c
        assert "settings" in table.c


class TestSchemaMapperIntegration:
    """Test SchemaMapper's handling of override schemas."""

    def test_create_table_with_base_class(self) -> None:
        """SchemaMapper creates correct table for base class."""
        mapper = SchemaMapper()
        metadata = MetaData()

        table = mapper.create_table(User, metadata)

        # Should have base fields only
        assert "email" in table.c
        assert "is_active" in table.c

        # Should NOT have override fields
        assert "department" not in table.c
        assert "employee_id" not in table.c

    def test_create_table_with_override_class(self) -> None:
        """SchemaMapper creates correct table for override class."""
        mapper = SchemaMapper()
        metadata = MetaData()

        table = mapper.create_table(ExtendedUser, metadata)

        # Should have base fields
        assert "email" in table.c
        assert "is_active" in table.c

        # Should have override fields
        assert "department" in table.c
        assert "employee_id" in table.c

    def test_separate_tables_for_base_and_override(self) -> None:
        """Base and override should create separate tables."""
        mapper = SchemaMapper()
        metadata = MetaData()

        base_table = mapper.create_table(User, metadata)
        override_table = mapper.create_table(ExtendedUser, metadata)

        # Different table names
        assert base_table.name == "user"
        assert override_table.name == "extendeduser"

        # Different column sets
        base_cols = set(base_table.c.keys())
        override_cols = set(override_table.c.keys())

        assert base_cols != override_cols
        assert base_cols.issubset(override_cols)  # Base columns ⊂ Override columns

    def test_nullable_handling_in_overrides(self) -> None:
        """SchemaMapper correctly handles nullable fields in overrides."""
        mapper = SchemaMapper()
        metadata = MetaData()

        table = mapper.create_table(ExtendedUser, metadata)

        # department is required (not nullable)
        assert table.c.department.nullable is False

        # employee_id is optional (nullable)
        assert table.c.employee_id.nullable is True

    def test_unique_constraints_preserved(self) -> None:
        """Unique constraints from base should be preserved."""
        mapper = SchemaMapper()
        metadata = MetaData()

        base_table = mapper.create_table(User, metadata)
        override_table = mapper.create_table(ExtendedUser, metadata)

        # name should be unique in both
        assert base_table.c.name.unique is True
        assert override_table.c.name.unique is True

        # id should be primary key in both
        assert base_table.c.id.primary_key is True
        assert override_table.c.id.primary_key is True


class TestGetMergedFields:
    """Test get_merged_fields() helper method."""

    def test_get_merged_fields_base_class(self) -> None:
        """get_merged_fields() returns all fields for base class."""
        mapper = SchemaMapper()
        fields = mapper.get_merged_fields(User)

        # Should include base fields
        assert "email" in fields
        assert "is_active" in fields

        # Should include standard fields
        assert "id" in fields
        assert "name" in fields

    def test_get_merged_fields_override_class(self) -> None:
        """get_merged_fields() returns merged fields for override."""
        mapper = SchemaMapper()
        fields = mapper.get_merged_fields(ExtendedUser)

        # Should include base fields
        assert "email" in fields
        assert "is_active" in fields

        # Should include override fields
        assert "department" in fields
        assert "employee_id" in fields

    def test_merged_fields_structure(self) -> None:
        """get_merged_fields() returns correct structure."""
        mapper = SchemaMapper()
        fields = mapper.get_merged_fields(ExtendedUser)

        # Each entry should be (type, FieldInfo) tuple
        field_name, (_field_type, field_info) = next(iter(fields.items()))

        assert isinstance(field_name, str)
        assert isinstance(field_info, FieldInfo)

    def test_merged_fields_include_field_info(self) -> None:
        """get_merged_fields() includes complete FieldInfo."""
        mapper = SchemaMapper()
        fields = mapper.get_merged_fields(ExtendedUser)

        email_type, email_info = fields["email"]

        # Should have field metadata
        assert email_info.description == "User email address"
        assert email_type is str


class TestValidateOverrideSchema:
    """Test validate_override_schema() validation method."""

    def test_valid_override_passes_validation(self) -> None:
        """Valid override should pass validation."""
        mapper = SchemaMapper()

        # Should not raise
        mapper.validate_override_schema(User, ExtendedUser)

    def test_override_with_all_base_fields_passes(self) -> None:
        """Override with all base fields present passes."""
        mapper = SchemaMapper()

        class CompleteOverride(User):
            # Includes all base fields plus new ones
            extra_field: str = Field(description="Extra field")

        # Should not raise
        mapper.validate_override_schema(User, CompleteOverride)

    def test_validation_checks_all_base_fields(self) -> None:
        """Validation ensures all base fields are present."""
        # In practice, Pydantic inheritance ensures base fields are present
        # This test validates the validation logic itself

        mapper = SchemaMapper()

        # Create a mock override that somehow lost a field
        # (In practice, this can't happen with Pydantic, but we test the check)
        class FakeOverride(BaseDocType):
            # Missing 'email' and 'is_active' from User
            department: str = Field(description="Department")

        # Should raise because email and is_active are missing
        with pytest.raises(ValueError, match="missing base fields"):
            mapper.validate_override_schema(User, FakeOverride)

    def test_validation_allows_new_fields(self) -> None:
        """Validation allows adding new fields."""
        mapper = SchemaMapper()

        # Override with many new fields
        class ExtensiveUser(User):
            field1: str = Field(description="Field 1")
            field2: int = Field(default=0, description="Field 2")
            field3: bool = Field(default=False, description="Field 3")

        # Should not raise
        mapper.validate_override_schema(User, ExtensiveUser)

    def test_validation_with_multiple_inheritance_levels(self) -> None:
        """Validation works with multiple inheritance levels."""

        class Level1(BaseDocType):
            field1: str = Field(description="Level 1")

        class Level2(Level1):
            field2: str = Field(description="Level 2")

        class Level3(Level2):
            field3: str = Field(description="Level 3")

        mapper = SchemaMapper()

        # Level3 should be valid override of Level2
        mapper.validate_override_schema(Level2, Level3)

        # Level3 should be valid override of Level1
        mapper.validate_override_schema(Level1, Level3)
