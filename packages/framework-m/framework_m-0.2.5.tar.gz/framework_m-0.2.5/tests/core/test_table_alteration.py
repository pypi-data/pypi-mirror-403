"""Tests for Table Alteration - Schema Change Detection and Migration.

This module tests the table alteration functionality that:
- Detects schema changes between base and override DocTypes
- Generates ALTER TABLE statements for migrations
- Adds new columns for override fields
- Modifies column types with validation
- Ensures database-agnostic DDL generation
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import Field
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
    """Override Product with new field and modified field."""

    # Modified field (same type, different description)
    price: Decimal = Field(default=Decimal("0.00"), description="Product price in USD")
    # New field
    sku: str = Field(description="Stock keeping unit")
    stock_quantity: int = Field(default=0, description="Stock quantity")


class ModifiedTypeProduct(Product):
    """Override that changes field type (should be flagged)."""

    # Change price from Decimal to float (potentially unsafe)
    price: float = Field(default=0.0, description="Product price")  # type: ignore[assignment]


# Test Classes
class TestDetectSchemaChanges:
    """Test detection of schema changes between base and override."""

    def test_detect_new_fields(self) -> None:
        """Should detect fields added in override."""
        mapper = SchemaMapper()

        # Get schema changes
        changes = mapper.detect_schema_changes(User, ExtendedUser)

        # Should detect new fields
        assert "added_fields" in changes
        added_fields = changes["added_fields"]

        assert "department" in added_fields
        assert "employee_id" in added_fields

    def test_detect_no_changes_for_same_class(self) -> None:
        """Should detect no changes when comparing same class."""
        mapper = SchemaMapper()

        changes = mapper.detect_schema_changes(User, User)

        # No added fields
        assert len(changes["added_fields"]) == 0
        # No modified fields
        assert len(changes["modified_fields"]) == 0

    def test_detect_modified_field_properties(self) -> None:
        """Should detect when field properties are modified."""
        mapper = SchemaMapper()

        changes = mapper.detect_schema_changes(Product, ExtendedProduct)

        # price exists in both but description changed
        # This is a modification, but same type
        added_fields = changes["added_fields"]

        # sku and stock_quantity are new
        assert "sku" in added_fields
        assert "stock_quantity" in added_fields

    def test_detect_multiple_new_fields(self) -> None:
        """Should detect all new fields in override."""
        mapper = SchemaMapper()

        changes = mapper.detect_schema_changes(Product, ExtendedProduct)

        added_fields = changes["added_fields"]

        # Two new fields
        assert len(added_fields) == 2
        assert "sku" in added_fields
        assert "stock_quantity" in added_fields

    def test_changes_include_field_details(self) -> None:
        """Schema changes should include field type and metadata."""
        mapper = SchemaMapper()

        changes = mapper.detect_schema_changes(User, ExtendedUser)

        added_fields = changes["added_fields"]

        # Check department field details
        dept_info = added_fields["department"]
        assert "type" in dept_info
        assert "nullable" in dept_info
        assert dept_info["nullable"] is False  # Required field

        # Check employee_id field details
        emp_info = added_fields["employee_id"]
        assert emp_info["nullable"] is True  # Optional field


class TestGenerateAlterTableStatements:
    """Test generation of ALTER TABLE DDL statements."""

    def test_generate_add_column_statements(self) -> None:
        """Should generate ALTER TABLE ADD COLUMN for new fields."""
        mapper = SchemaMapper()
        metadata = MetaData()

        # Detect changes
        changes = mapper.detect_schema_changes(User, ExtendedUser)

        # Generate ALTER TABLE statements
        statements = mapper.generate_alter_table_statements(
            "extendeduser", changes, metadata
        )

        # Should have statements for each new field
        assert len(statements) > 0

        # Check for ADD COLUMN statements
        add_column_stmts = [s for s in statements if "ADD COLUMN" in str(s).upper()]
        assert len(add_column_stmts) == 2  # department and employee_id

    def test_alter_statements_are_executable(self) -> None:
        """Generated statements should be valid SQLAlchemy DDL."""
        mapper = SchemaMapper()
        metadata = MetaData()

        changes = mapper.detect_schema_changes(User, ExtendedUser)
        statements = mapper.generate_alter_table_statements(
            "extendeduser", changes, metadata
        )

        # All statements should be DDL objects
        from sqlalchemy.schema import DDLElement

        for stmt in statements:
            assert isinstance(stmt, DDLElement)

    def test_nullable_fields_have_correct_constraint(self) -> None:
        """ALTER TABLE should respect nullable constraints."""
        mapper = SchemaMapper()
        metadata = MetaData()

        changes = mapper.detect_schema_changes(User, ExtendedUser)
        statements = mapper.generate_alter_table_statements(
            "extendeduser", changes, metadata
        )

        # Convert to SQL strings for inspection
        sql_strings = [str(stmt.compile()) for stmt in statements]

        # department should be NOT NULL
        dept_stmts = [s for s in sql_strings if "department" in s.lower()]
        assert any("NOT NULL" in s.upper() for s in dept_stmts)

        # employee_id should allow NULL (or not have NOT NULL)
        emp_stmts = [s for s in sql_strings if "employee_id" in s.lower()]
        # Either explicitly NULL or no NOT NULL constraint
        assert all("NOT NULL" not in s.upper() for s in emp_stmts)

    def test_no_statements_when_no_changes(self) -> None:
        """Should generate no statements when schemas are identical."""
        mapper = SchemaMapper()
        metadata = MetaData()

        changes = mapper.detect_schema_changes(User, User)
        statements = mapper.generate_alter_table_statements("user", changes, metadata)

        # No changes, no statements
        assert len(statements) == 0

    def test_multiple_fields_generate_multiple_statements(self) -> None:
        """Each new field should get its own ALTER TABLE statement."""
        mapper = SchemaMapper()
        metadata = MetaData()

        changes = mapper.detect_schema_changes(Product, ExtendedProduct)
        statements = mapper.generate_alter_table_statements(
            "extendedproduct", changes, metadata
        )

        # Two new fields (sku, stock_quantity)
        assert len(statements) == 2


class TestColumnTypeMapping:
    """Test that field types map correctly to SQL column types."""

    def test_string_field_maps_to_varchar(self) -> None:
        """String fields should map to VARCHAR/String columns."""
        mapper = SchemaMapper()
        metadata = MetaData()

        changes = mapper.detect_schema_changes(User, ExtendedUser)
        statements = mapper.generate_alter_table_statements(
            "extendeduser", changes, metadata
        )

        sql_strings = [str(stmt.compile()) for stmt in statements]

        # department (str) should map to VARCHAR or similar
        dept_stmts = [s for s in sql_strings if "department" in s.lower()]
        assert len(dept_stmts) > 0
        # Check for VARCHAR, TEXT, or STRING type
        assert any(
            any(t in s.upper() for t in ["VARCHAR", "TEXT", "STRING"])
            for s in dept_stmts
        )

    def test_integer_field_maps_to_integer(self) -> None:
        """Integer fields should map to INTEGER columns."""
        mapper = SchemaMapper()
        metadata = MetaData()

        changes = mapper.detect_schema_changes(Product, ExtendedProduct)
        statements = mapper.generate_alter_table_statements(
            "extendedproduct", changes, metadata
        )

        sql_strings = [str(stmt.compile()) for stmt in statements]

        # stock_quantity (int) should map to INTEGER
        stock_stmts = [s for s in sql_strings if "stock_quantity" in s.lower()]
        assert any("INTEGER" in s.upper() for s in stock_stmts)

    def test_boolean_field_maps_to_boolean(self) -> None:
        """Boolean fields should map to BOOLEAN columns."""

        class ExtendedUserWithFlag(User):
            is_verified: bool = Field(default=False, description="Verified user")

        mapper = SchemaMapper()
        metadata = MetaData()

        changes = mapper.detect_schema_changes(User, ExtendedUserWithFlag)
        statements = mapper.generate_alter_table_statements(
            "extendeduserWithflag", changes, metadata
        )

        sql_strings = [str(stmt.compile()) for stmt in statements]

        # is_verified (bool) should map to BOOLEAN or INTEGER (SQLite)
        verified_stmts = [s for s in sql_strings if "is_verified" in s.lower()]
        assert any(
            any(t in s.upper() for t in ["BOOLEAN", "INTEGER"]) for s in verified_stmts
        )


class TestDatabaseAgnosticDDL:
    """Test that generated DDL is database-agnostic."""

    def test_ddl_works_with_sqlite_dialect(self) -> None:
        """Generated DDL should compile for SQLite."""
        from sqlalchemy.dialects import sqlite

        mapper = SchemaMapper()
        metadata = MetaData()

        changes = mapper.detect_schema_changes(User, ExtendedUser)
        statements = mapper.generate_alter_table_statements(
            "extendeduser", changes, metadata
        )

        # Should compile without errors for SQLite
        for stmt in statements:
            sql = str(stmt.compile(dialect=sqlite.dialect()))
            assert len(sql) > 0
            assert "ALTER TABLE" in sql.upper()

    def test_ddl_works_with_postgresql_dialect(self) -> None:
        """Generated DDL should compile for PostgreSQL."""
        from sqlalchemy.dialects import postgresql

        mapper = SchemaMapper()
        metadata = MetaData()

        changes = mapper.detect_schema_changes(User, ExtendedUser)
        statements = mapper.generate_alter_table_statements(
            "extendeduser", changes, metadata
        )

        # Should compile without errors for PostgreSQL
        for stmt in statements:
            sql = str(stmt.compile(dialect=postgresql.dialect()))
            assert len(sql) > 0
            assert "ALTER TABLE" in sql.upper()

    def test_no_database_specific_features(self) -> None:
        """DDL should not use database-specific features."""
        mapper = SchemaMapper()
        metadata = MetaData()

        changes = mapper.detect_schema_changes(User, ExtendedUser)
        statements = mapper.generate_alter_table_statements(
            "extendeduser", changes, metadata
        )

        sql_strings = [str(stmt.compile()) for stmt in statements]

        # Should not use PostgreSQL-specific types
        for sql in sql_strings:
            assert "ARRAY" not in sql.upper()
            assert "JSONB" not in sql.upper()
            assert "HSTORE" not in sql.upper()


class TestTypeModificationValidation:
    """Test validation when field types are modified."""

    def test_detect_type_change(self) -> None:
        """Should detect when field type changes."""
        mapper = SchemaMapper()

        changes = mapper.detect_schema_changes(Product, ModifiedTypeProduct)

        # Should detect type modification
        assert "modified_fields" in changes
        modified_fields = changes["modified_fields"]

        # price type changed from Decimal to float
        assert "price" in modified_fields

    def test_type_change_includes_old_and_new_types(self) -> None:
        """Type change info should include both old and new types."""
        mapper = SchemaMapper()

        changes = mapper.detect_schema_changes(Product, ModifiedTypeProduct)

        modified_fields = changes["modified_fields"]
        price_change = modified_fields["price"]

        assert "old_type" in price_change
        assert "new_type" in price_change

    def test_safe_type_changes_allowed(self) -> None:
        """Some type changes should be considered safe."""

        class FlexibleProduct(Product):
            # Make required field optional (safe change)
            name: str | None = Field(default=None, description="Product name")

        mapper = SchemaMapper()

        changes = mapper.detect_schema_changes(Product, FlexibleProduct)

        # This is a nullable change, not a type change
        # Should be detected as modification
        assert "name" in changes.get(
            "modified_fields", {}
        ) or "name" not in changes.get("added_fields", {})


class TestEdgeCases:
    """Test edge cases in table alteration."""

    def test_empty_override_generates_no_statements(self) -> None:
        """Override with no new fields should generate no ALTER statements."""

        class UnchangedUser(User):
            pass

        mapper = SchemaMapper()
        metadata = MetaData()

        changes = mapper.detect_schema_changes(User, UnchangedUser)
        statements = mapper.generate_alter_table_statements(
            "unchangeduser", changes, metadata
        )

        assert len(statements) == 0

    def test_complex_types_generate_json_columns(self) -> None:
        """List and dict fields should map to JSON columns."""

        class DocumentWithMetadata(BaseDocType):
            title: str = Field(description="Title")

        class ExtendedDocument(DocumentWithMetadata):
            tags: list[str] = Field(default_factory=list, description="Tags")
            metadata: dict[str, str] = Field(
                default_factory=dict, description="Metadata"
            )

        mapper = SchemaMapper()
        metadata = MetaData()

        changes = mapper.detect_schema_changes(DocumentWithMetadata, ExtendedDocument)
        statements = mapper.generate_alter_table_statements(
            "extendeddocument", changes, metadata
        )

        sql_strings = [str(stmt.compile()) for stmt in statements]

        # tags and metadata should use JSON type
        tags_stmts = [s for s in sql_strings if "tags" in s.lower()]
        meta_stmts = [s for s in sql_strings if "metadata" in s.lower()]

        assert any("JSON" in s.upper() for s in tags_stmts)
        assert any("JSON" in s.upper() for s in meta_stmts)

    def test_multiple_inheritance_levels(self) -> None:
        """Should detect changes across multiple inheritance levels."""

        class Manager(User):
            team_size: int = Field(default=0, description="Team size")

        class Director(Manager):
            budget: Decimal = Field(
                default=Decimal("0"), description="Department budget"
            )

        mapper = SchemaMapper()

        # Compare User to Director (skipping Manager)
        changes = mapper.detect_schema_changes(User, Director)

        added_fields = changes["added_fields"]

        # Should detect both team_size and budget
        assert "team_size" in added_fields
        assert "budget" in added_fields


class TestIntegrationWithSchemaMapper:
    """Test integration with existing SchemaMapper methods."""

    def test_detect_changes_after_create_table(self) -> None:
        """Should work with tables created by create_table()."""
        mapper = SchemaMapper()
        metadata = MetaData()

        # Create base table (ensures mapper works end-to-end)
        mapper.create_table(User, metadata)

        # Detect changes for override
        changes = mapper.detect_schema_changes(User, ExtendedUser)

        # Changes should be detectable
        assert len(changes["added_fields"]) > 0

    def test_alter_statements_reference_correct_table(self) -> None:
        """ALTER TABLE statements should reference the correct table name."""
        mapper = SchemaMapper()
        metadata = MetaData()

        changes = mapper.detect_schema_changes(User, ExtendedUser)
        statements = mapper.generate_alter_table_statements(
            "extendeduser", changes, metadata
        )

        # All statements should reference the table
        for stmt in statements:
            sql = str(stmt.compile()).lower()
            assert "extendeduser" in sql

    def test_changes_preserve_standard_fields(self) -> None:
        """Schema changes should not affect standard BaseDocType fields."""
        mapper = SchemaMapper()

        changes = mapper.detect_schema_changes(User, ExtendedUser)

        added_fields = changes["added_fields"]

        # Standard fields should not be in added_fields
        standard_fields = ["id", "name", "creation", "modified", "owner"]
        for field in standard_fields:
            assert field not in added_fields
