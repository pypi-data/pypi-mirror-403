"""Tests for TableRegistry."""

import pytest
from sqlalchemy import Column, MetaData, String, Table

from framework_m.adapters.db.table_registry import (
    DuplicateTableError,
    TableNotFoundError,
    TableRegistry,
)


class TestTableRegistrySingleton:
    """Tests for TableRegistry singleton pattern."""

    def test_table_registry_is_singleton(self) -> None:
        """TableRegistry should return the same instance."""
        registry1 = TableRegistry()
        registry2 = TableRegistry()
        assert registry1 is registry2

    def test_table_registry_reset(self) -> None:
        """TableRegistry.reset() should clear all tables."""
        registry = TableRegistry()
        metadata = MetaData()
        table = Table("test_doc", metadata, Column("id", String, primary_key=True))

        registry.register_table("TestDoc", table)
        assert registry.table_exists("TestDoc")

        registry.reset()
        assert not registry.table_exists("TestDoc")


class TestTableRegistration:
    """Tests for table registration."""

    @pytest.fixture(autouse=True)
    def reset_registry(self) -> None:
        """Reset registry before each test."""
        TableRegistry().reset()

    def test_register_table(self) -> None:
        """register_table should store a table."""
        registry = TableRegistry()
        metadata = MetaData()
        table = Table("test_doc", metadata, Column("id", String, primary_key=True))

        registry.register_table("TestDoc", table)
        assert registry.table_exists("TestDoc")

    def test_register_table_duplicate_raises_error(self) -> None:
        """register_table should raise error on duplicate."""
        registry = TableRegistry()
        metadata = MetaData()
        table1 = Table("test_doc", metadata, Column("id", String, primary_key=True))
        table2 = Table("test_doc2", metadata, Column("id", String, primary_key=True))

        registry.register_table("TestDoc", table1)

        with pytest.raises(DuplicateTableError) as exc_info:
            registry.register_table("TestDoc", table2)

        assert "TestDoc" in str(exc_info.value)


class TestTableRetrieval:
    """Tests for table retrieval."""

    @pytest.fixture(autouse=True)
    def reset_registry(self) -> None:
        """Reset registry before each test."""
        TableRegistry().reset()

    def test_get_table_returns_table(self) -> None:
        """get_table should return the registered table."""
        registry = TableRegistry()
        metadata = MetaData()
        table = Table("test_doc", metadata, Column("id", String, primary_key=True))

        registry.register_table("TestDoc", table)
        retrieved = registry.get_table("TestDoc")

        assert retrieved is table

    def test_get_table_not_found_raises_error(self) -> None:
        """get_table should raise error if table not found."""
        registry = TableRegistry()

        with pytest.raises(TableNotFoundError) as exc_info:
            registry.get_table("NonExistent")

        assert "NonExistent" in str(exc_info.value)

    def test_table_exists_returns_true_for_registered(self) -> None:
        """table_exists should return True for registered tables."""
        registry = TableRegistry()
        metadata = MetaData()
        table = Table("test_doc", metadata, Column("id", String, primary_key=True))

        registry.register_table("TestDoc", table)
        assert registry.table_exists("TestDoc") is True

    def test_table_exists_returns_false_for_unregistered(self) -> None:
        """table_exists should return False for unregistered tables."""
        registry = TableRegistry()
        assert registry.table_exists("NonExistent") is False


class TestTableRegistryListing:
    """Tests for listing tables."""

    @pytest.fixture(autouse=True)
    def reset_registry(self) -> None:
        """Reset registry before each test."""
        TableRegistry().reset()

    def test_list_tables_empty(self) -> None:
        """list_tables should return empty list when no tables."""
        registry = TableRegistry()
        assert registry.list_tables() == []

    def test_list_tables_returns_all(self) -> None:
        """list_tables should return all registered table names."""
        registry = TableRegistry()
        metadata = MetaData()
        table1 = Table("doc1", metadata, Column("id", String, primary_key=True))
        table2 = Table("doc2", metadata, Column("id", String, primary_key=True))

        registry.register_table("Doc1", table1)
        registry.register_table("Doc2", table2)

        tables = registry.list_tables()
        assert set(tables) == {"Doc1", "Doc2"}


class TestTableRegistryImport:
    """Tests for TableRegistry imports."""

    def test_import_table_registry(self) -> None:
        """TableRegistry should be importable."""
        from framework_m.adapters.db.table_registry import TableRegistry

        assert TableRegistry is not None

    def test_import_exceptions(self) -> None:
        """Exceptions should be importable."""
        from framework_m.adapters.db.table_registry import (
            DuplicateTableError,
            TableNotFoundError,
        )

        assert DuplicateTableError is not None
        assert TableNotFoundError is not None
