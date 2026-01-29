"""Table Registry - Stores created SQLAlchemy tables.

This module provides the TableRegistry class that manages the mapping
between DocType names and their corresponding SQLAlchemy Table objects.

The registry uses a singleton pattern to ensure a single source of truth
for table lookups across the application.
"""

from __future__ import annotations

from typing import ClassVar

from sqlalchemy import Table


class DuplicateTableError(Exception):
    """Raised when attempting to register a table that already exists."""

    def __init__(self, doctype_name: str) -> None:
        """Initialize with the duplicate doctype name.

        Args:
            doctype_name: Name of the DocType that was duplicated
        """
        self.doctype_name = doctype_name
        super().__init__(f"Table for DocType '{doctype_name}' is already registered")


class TableNotFoundError(Exception):
    """Raised when a table is not found in the registry."""

    def __init__(self, doctype_name: str) -> None:
        """Initialize with the missing doctype name.

        Args:
            doctype_name: Name of the DocType that was not found
        """
        self.doctype_name = doctype_name
        super().__init__(f"Table for DocType '{doctype_name}' not found in registry")


class TableRegistry:
    """Registry for SQLAlchemy Table objects.

    Provides a centralized location to store and retrieve Table objects
    created from DocType models. Uses singleton pattern.

    Example:
        >>> registry = TableRegistry()
        >>> registry.register_table("Todo", todo_table)
        >>> table = registry.get_table("Todo")
    """

    _instance: ClassVar[TableRegistry | None] = None
    _tables: dict[str, Table]

    def __new__(cls) -> TableRegistry:
        """Implement singleton pattern.

        Returns:
            The single TableRegistry instance
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tables = {}
        return cls._instance

    def register_table(self, doctype_name: str, table: Table) -> None:
        """Register a table for a DocType.

        Args:
            doctype_name: Name of the DocType
            table: SQLAlchemy Table object

        Raises:
            DuplicateTableError: If a table is already registered for this DocType
        """
        if doctype_name in self._tables:
            raise DuplicateTableError(doctype_name)
        self._tables[doctype_name] = table

    def get_table(self, doctype_name: str) -> Table:
        """Get the table for a DocType.

        Args:
            doctype_name: Name of the DocType

        Returns:
            The SQLAlchemy Table object

        Raises:
            TableNotFoundError: If no table is registered for this DocType
        """
        if doctype_name not in self._tables:
            raise TableNotFoundError(doctype_name)
        return self._tables[doctype_name]

    def table_exists(self, doctype_name: str) -> bool:
        """Check if a table is registered for a DocType.

        Args:
            doctype_name: Name of the DocType

        Returns:
            True if a table is registered, False otherwise
        """
        return doctype_name in self._tables

    def list_tables(self) -> list[str]:
        """List all registered DocType names.

        Returns:
            List of DocType names with registered tables
        """
        return list(self._tables.keys())

    def reset(self) -> None:
        """Clear all registered tables.

        Use this for testing to reset the singleton state.
        """
        self._tables.clear()


__all__ = ["DuplicateTableError", "TableNotFoundError", "TableRegistry"]
