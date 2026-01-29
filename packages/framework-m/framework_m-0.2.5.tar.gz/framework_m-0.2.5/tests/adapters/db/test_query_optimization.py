"""Tests for Query Optimization - Index Creation.

TDD tests for adding indexes for common queries:
- owner field index (for RLS filtering)
- creation/modified date indexes (for ordering)
- Custom indexes from Meta.indexes
- Child table parent field index

Per CONTRIBUTING.md: Write failing tests FIRST, then implement.
"""

from typing import ClassVar

import pytest
from sqlalchemy import MetaData

from framework_m.adapters.db.schema_mapper import SchemaMapper
from framework_m.core.domain.base_doctype import BaseDocType, Field

# =============================================================================
# Test DocTypes
# =============================================================================


class TodoWithRLS(BaseDocType):
    """DocType with RLS enabled - should have owner index."""

    title: str = Field(description="Title")
    status: str = Field(default="pending")

    class Meta:
        apply_rls: ClassVar[bool] = True


class AuditableDoc(BaseDocType):
    """DocType that needs date ordering - should have creation/modified indexes."""

    title: str = Field(description="Title")

    class Meta:
        api_resource: ClassVar[bool] = True


class CustomIndexDoc(BaseDocType):
    """DocType with custom indexes defined in Meta."""

    title: str = Field(description="Title")
    category: str = Field(default="general")
    status: str = Field(default="active")

    class Meta:
        # Define custom indexes
        indexes: ClassVar[list[dict[str, str | list[str]]]] = [
            {"fields": ["category"]},
            {"fields": ["status", "category"]},  # Composite index
        ]


class InvoiceItem(BaseDocType):
    """Child table - should have parent field index."""

    item_name: str = Field(description="Item name")
    quantity: int = Field(default=1)

    class Meta:
        is_child_table: ClassVar[bool] = True


class Invoice(BaseDocType):
    """Parent with child table."""

    customer: str = Field(description="Customer name")
    items: list[InvoiceItem] = Field(default_factory=list)

    class Meta:
        api_resource: ClassVar[bool] = True
        apply_rls: ClassVar[bool] = True


# =============================================================================
# Tests: Index Creation via Meta.indexes
# =============================================================================


class TestCustomIndexes:
    """Test custom index creation from Meta.indexes."""

    def test_table_has_index_on_owner_when_rls_enabled(self) -> None:
        """Tables with RLS should auto-create index on owner field."""
        mapper = SchemaMapper()
        metadata = MetaData()

        table = mapper.create_table(TodoWithRLS, metadata)

        # Check for index on owner column
        owner_indexes = [
            idx for idx in table.indexes if "owner" in [c.name for c in idx.columns]
        ]
        assert len(owner_indexes) >= 1, "Should have index on owner for RLS filtering"

    def test_table_has_indexes_on_common_date_fields(self) -> None:
        """Tables should have indexes on creation and modified for ordering."""
        mapper = SchemaMapper()
        metadata = MetaData()

        table = mapper.create_table(AuditableDoc, metadata)

        # Check for indexes on date fields
        index_columns = set()
        for idx in table.indexes:
            for col in idx.columns:
                index_columns.add(col.name)

        # creation and modified are common ordering fields
        assert "creation" in index_columns or "modified" in index_columns, (
            "Should have index on date fields for ordering"
        )

    def test_meta_indexes_creates_single_column_index(self) -> None:
        """Meta.indexes should create specified single-column indexes."""
        mapper = SchemaMapper()
        metadata = MetaData()

        table = mapper.create_table(CustomIndexDoc, metadata)

        # Find index on category
        category_indexes = [
            idx
            for idx in table.indexes
            if "category" in [c.name for c in idx.columns] and len(idx.columns) == 1
        ]
        assert len(category_indexes) >= 1, "Should have index on category"

    def test_meta_indexes_creates_composite_index(self) -> None:
        """Meta.indexes should create composite (multi-column) indexes."""
        mapper = SchemaMapper()
        metadata = MetaData()

        table = mapper.create_table(CustomIndexDoc, metadata)

        # Find composite index on status + category
        composite_indexes = [idx for idx in table.indexes if len(idx.columns) == 2]
        assert len(composite_indexes) >= 1, "Should have composite index"

        # Verify it's the right columns
        for idx in composite_indexes:
            col_names = [c.name for c in idx.columns]
            if "status" in col_names and "category" in col_names:
                return  # Found it

        pytest.fail("Should have composite index on status + category")


class TestChildTableIndexes:
    """Test index creation for child tables."""

    def test_child_table_has_parent_index(self) -> None:
        """Child tables should have index on parent field for joins."""
        mapper = SchemaMapper()
        metadata = MetaData()

        tables = mapper.create_tables(Invoice, metadata)
        child_table = tables[1]  # First child table

        # Check for index on parent column
        parent_indexes = [
            idx
            for idx in child_table.indexes
            if "parent" in [c.name for c in idx.columns]
        ]
        assert len(parent_indexes) >= 1, "Child table should have index on parent"


# =============================================================================
# Tests: Get Indexes Meta Method
# =============================================================================


class TestGetIndexesMeta:
    """Test the get_indexes class method on BaseDocType."""

    def test_get_indexes_returns_empty_by_default(self) -> None:
        """DocType without Meta.indexes should return empty list."""
        assert TodoWithRLS.get_indexes() == []

    def test_get_indexes_returns_configured_indexes(self) -> None:
        """DocType with Meta.indexes should return the list."""
        indexes = CustomIndexDoc.get_indexes()
        assert len(indexes) == 2
        assert indexes[0]["fields"] == ["category"]
        assert indexes[1]["fields"] == ["status", "category"]
