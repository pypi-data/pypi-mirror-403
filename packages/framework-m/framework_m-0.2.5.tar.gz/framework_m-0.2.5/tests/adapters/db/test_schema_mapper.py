"""Tests for SchemaMapper - Pydantic model to SQLAlchemy table conversion.

TDD: Tests written first, implementation to follow.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Float, Integer, MetaData, Numeric, String
from sqlalchemy.types import JSON
from sqlalchemy.types import UUID as SA_UUID

from framework_m import DocType, Field

# =============================================================================
# Test DocTypes
# =============================================================================


class Priority(Enum):
    """Priority enum for testing."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SimpleTodo(DocType):
    """Simple DocType for basic tests."""

    title: str = Field(description="Task title")
    is_completed: bool = False
    priority: int = 1


class FullFeaturedDoc(DocType):
    """DocType with all supported field types."""

    text_field: str
    int_field: int
    float_field: float
    bool_field: bool
    datetime_field: datetime
    decimal_field: Decimal
    uuid_field: UUID
    optional_field: str | None = None
    json_field: dict[str, Any] = Field(default_factory=dict)
    list_field: list[str] = Field(default_factory=list)


class DocWithOptionalFields(DocType):
    """DocType with optional fields for nullable tests."""

    required_field: str
    optional_str: str | None = None
    optional_int: int | None = None


class OptimisticDoc(DocType):
    """DocType with optimistic concurrency control."""

    title: str

    class Meta:
        concurrency = "optimistic"


class DocWithForeignKey(DocType):
    """DocType with foreign key reference."""

    customer_id: str = Field(description="Reference to Customer")


class DocWithEnum(DocType):
    """DocType with enum field."""

    priority: Priority = Priority.MEDIUM


class DocWithUnique(DocType):
    """DocType with unique constraint on a field."""

    email: str = Field(json_schema_extra={"unique": True})


# =============================================================================
# Tests
# =============================================================================


class TestSchemaMapperImports:
    """Tests for SchemaMapper imports."""

    def test_import_schema_mapper(self) -> None:
        """SchemaMapper should be importable."""
        from framework_m.adapters.db.schema_mapper import SchemaMapper

        assert SchemaMapper is not None

    def test_import_from_adapters_db(self) -> None:
        """SchemaMapper should be exported from adapters.db."""
        from framework_m.adapters.db import SchemaMapper

        assert SchemaMapper is not None


class TestSchemaMapperBasics:
    """Tests for basic SchemaMapper functionality."""

    def setup_method(self) -> None:
        """Create mapper for each test."""
        from framework_m.adapters.db.schema_mapper import SchemaMapper

        self.mapper = SchemaMapper()
        self.metadata = MetaData()

    def test_create_table_returns_table(self) -> None:
        """create_table should return a SQLAlchemy Table."""
        from sqlalchemy import Table

        result = self.mapper.create_table(SimpleTodo, self.metadata)

        assert isinstance(result, Table)

    def test_table_name_is_lowercase_class_name(self) -> None:
        """Table name should be lowercase class name."""
        result = self.mapper.create_table(SimpleTodo, self.metadata)

        assert result.name == "simpletodo"

    def test_table_has_id_column_as_primary_key(self) -> None:
        """Table should have 'id' column as primary key (UUID)."""
        from sqlalchemy.types import UUID as SA_UUID

        result = self.mapper.create_table(SimpleTodo, self.metadata)

        assert "id" in result.columns
        assert result.columns["id"].primary_key
        assert isinstance(result.columns["id"].type, SA_UUID)

    def test_table_has_name_column_as_unique(self) -> None:
        """Table should have 'name' column with unique constraint."""
        result = self.mapper.create_table(SimpleTodo, self.metadata)

        assert "name" in result.columns
        assert result.columns["name"].unique is True
        assert result.columns["name"].primary_key is False

    def test_table_includes_standard_doctype_fields(self) -> None:
        """Table should include standard BaseDocType fields."""
        result = self.mapper.create_table(SimpleTodo, self.metadata)

        # Standard fields from BaseDocType
        assert "id" in result.columns  # PK
        assert "name" in result.columns  # Unique
        assert "owner" in result.columns
        assert "creation" in result.columns
        assert "modified" in result.columns
        assert "modified_by" in result.columns


class TestSchemaMapperFieldTypes:
    """Tests for field type mapping."""

    def setup_method(self) -> None:
        """Create mapper for each test."""
        from framework_m.adapters.db.schema_mapper import SchemaMapper

        self.mapper = SchemaMapper()
        self.metadata = MetaData()

    def test_str_field_maps_to_string(self) -> None:
        """str field should map to String column."""
        result = self.mapper.create_table(SimpleTodo, self.metadata)

        assert isinstance(result.columns["title"].type, String)

    def test_int_field_maps_to_integer(self) -> None:
        """int field should map to Integer column."""
        result = self.mapper.create_table(SimpleTodo, self.metadata)

        assert isinstance(result.columns["priority"].type, Integer)

    def test_bool_field_maps_to_boolean(self) -> None:
        """bool field should map to Boolean column."""
        result = self.mapper.create_table(SimpleTodo, self.metadata)

        assert isinstance(result.columns["is_completed"].type, Boolean)

    def test_full_featured_doc_maps_all_types(self) -> None:
        """All field types should be mapped correctly."""
        result = self.mapper.create_table(FullFeaturedDoc, self.metadata)

        assert isinstance(result.columns["text_field"].type, String)
        assert isinstance(result.columns["int_field"].type, Integer)
        assert isinstance(result.columns["float_field"].type, Float)
        assert isinstance(result.columns["bool_field"].type, Boolean)
        assert isinstance(result.columns["datetime_field"].type, DateTime)
        assert isinstance(result.columns["decimal_field"].type, Numeric)
        assert isinstance(result.columns["uuid_field"].type, SA_UUID)
        assert isinstance(result.columns["json_field"].type, JSON)
        assert isinstance(result.columns["list_field"].type, JSON)


class TestSchemaMapperNullableFields:
    """Tests for optional/nullable field handling."""

    def setup_method(self) -> None:
        """Create mapper for each test."""
        from framework_m.adapters.db.schema_mapper import SchemaMapper

        self.mapper = SchemaMapper()
        self.metadata = MetaData()

    def test_required_field_is_not_nullable(self) -> None:
        """Required fields should not be nullable."""
        result = self.mapper.create_table(DocWithOptionalFields, self.metadata)

        assert result.columns["required_field"].nullable is False

    def test_optional_field_is_nullable(self) -> None:
        """Optional fields (T | None) should be nullable."""
        result = self.mapper.create_table(DocWithOptionalFields, self.metadata)

        assert result.columns["optional_str"].nullable is True
        assert result.columns["optional_int"].nullable is True


class TestSchemaMapperOptimisticConcurrency:
    """Tests for optimistic concurrency control."""

    def setup_method(self) -> None:
        """Create mapper for each test."""
        from framework_m.adapters.db.schema_mapper import SchemaMapper

        self.mapper = SchemaMapper()
        self.metadata = MetaData()

    def test_occ_doc_has_version_column(self) -> None:
        """DocType with concurrency='optimistic' should have _version column."""
        result = self.mapper.create_table(OptimisticDoc, self.metadata)

        assert "_version" in result.columns
        assert isinstance(result.columns["_version"].type, Integer)

    def test_regular_doc_has_no_version_column(self) -> None:
        """Regular DocType should not have _version column."""
        result = self.mapper.create_table(SimpleTodo, self.metadata)

        assert "_version" not in result.columns


class TestSchemaMapperForeignKeys:
    """Tests for foreign key detection."""

    def setup_method(self) -> None:
        """Create mapper for each test."""
        from framework_m.adapters.db.schema_mapper import SchemaMapper

        self.mapper = SchemaMapper()
        self.metadata = MetaData()

    def test_field_ending_with_id_is_foreign_key(self) -> None:
        """Fields ending with _id should be treated as potential foreign keys."""
        result = self.mapper.create_table(DocWithForeignKey, self.metadata)

        # The column should exist and be string type (for the reference)
        assert "customer_id" in result.columns
        assert isinstance(result.columns["customer_id"].type, String)


class TestSchemaMapperEnums:
    """Tests for enum field handling."""

    def setup_method(self) -> None:
        """Create mapper for each test."""
        from framework_m.adapters.db.schema_mapper import SchemaMapper

        self.mapper = SchemaMapper()
        self.metadata = MetaData()

    def test_enum_field_is_stored_as_string(self) -> None:
        """Enum fields should be stored as String (database agnostic)."""
        result = self.mapper.create_table(DocWithEnum, self.metadata)

        # Store as String for database agnosticism
        assert isinstance(result.columns["priority"].type, String)


class TestSchemaMapperUnique:
    """Tests for unique constraint mapping."""

    def setup_method(self) -> None:
        """Create mapper for each test."""
        from framework_m.adapters.db.schema_mapper import SchemaMapper

        self.mapper = SchemaMapper()
        self.metadata = MetaData()

    def test_unique_field_maps_to_unique_constraint(self) -> None:
        """Field with json_schema_extra={'unique': True} should have unique constraint."""
        result = self.mapper.create_table(DocWithUnique, self.metadata)

        assert "email" in result.columns
        assert result.columns["email"].unique is True


# =============================================================================
# Child DocType Tests
# =============================================================================


class InvoiceItem(DocType):
    """Child DocType for testing - represents an invoice line item."""

    description: str
    quantity: int = 1
    unit_price: float = 0.0
    # Parent reference - will be auto-added by SchemaMapper
    # parent: str - auto-added as foreign key
    # parentfield: str - auto-added to identify which field
    # parenttype: str - auto-added to identify parent DocType


class Invoice(DocType):
    """Parent DocType with child table."""

    customer_name: str
    items: list[InvoiceItem] = Field(default_factory=list)
    total: float = 0.0


class TestSchemaMapperChildDocTypes:
    """Tests for Child DocType handling with relational tables."""

    def setup_method(self) -> None:
        """Create mapper for each test."""
        from framework_m.adapters.db.schema_mapper import SchemaMapper

        self.mapper = SchemaMapper()
        self.metadata = MetaData()

    def test_child_doctype_field_creates_separate_table(self) -> None:
        """list[DocType] should create a separate child table."""
        tables = self.mapper.create_tables(Invoice, self.metadata)

        # Should return multiple tables: parent and child
        assert len(tables) >= 2
        table_names = [t.name for t in tables]
        assert "invoice" in table_names
        assert "invoiceitem" in table_names

    def test_child_table_has_parent_foreign_key(self) -> None:
        """Child table should have parent foreign key column."""
        tables = self.mapper.create_tables(Invoice, self.metadata)

        child_table = next(t for t in tables if t.name == "invoiceitem")

        assert "parent" in child_table.columns
        assert isinstance(child_table.columns["parent"].type, String)

    def test_child_table_has_parentfield_column(self) -> None:
        """Child table should have parentfield column to identify the field."""
        tables = self.mapper.create_tables(Invoice, self.metadata)

        child_table = next(t for t in tables if t.name == "invoiceitem")

        assert "parentfield" in child_table.columns
        assert isinstance(child_table.columns["parentfield"].type, String)

    def test_child_table_has_parenttype_column(self) -> None:
        """Child table should have parenttype column to identify parent DocType."""
        tables = self.mapper.create_tables(Invoice, self.metadata)

        child_table = next(t for t in tables if t.name == "invoiceitem")

        assert "parenttype" in child_table.columns
        assert isinstance(child_table.columns["parenttype"].type, String)

    def test_child_table_has_idx_column(self) -> None:
        """Child table should have idx column for ordering."""
        tables = self.mapper.create_tables(Invoice, self.metadata)

        child_table = next(t for t in tables if t.name == "invoiceitem")

        assert "idx" in child_table.columns
        assert isinstance(child_table.columns["idx"].type, Integer)

    def test_parent_table_excludes_child_field(self) -> None:
        """Parent table should not have column for list[DocType] field."""
        tables = self.mapper.create_tables(Invoice, self.metadata)

        parent_table = next(t for t in tables if t.name == "invoice")

        # items field should NOT be a column - it's a child table reference
        assert "items" not in parent_table.columns
