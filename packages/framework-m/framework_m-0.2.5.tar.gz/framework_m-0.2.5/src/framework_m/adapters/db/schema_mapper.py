"""Schema Mapper - Converts Pydantic DocTypes to SQLAlchemy Tables.

This module provides the SchemaMapper class that dynamically creates
SQLAlchemy Table objects from Pydantic BaseDocType models. All mappings
are database-agnostic.
"""

from __future__ import annotations

import types
from enum import Enum
from typing import Any, Union, get_args, get_origin

from pydantic.fields import FieldInfo
from sqlalchemy import Column, Integer, MetaData, String, Table
from sqlalchemy.types import TypeEngine

from framework_m.adapters.db.field_registry import FieldRegistry
from framework_m.core.domain.base_doctype import BaseDocType


class SchemaMapper:
    """Maps Pydantic DocType models to SQLAlchemy Table objects.

    The SchemaMapper uses the FieldRegistry to convert Python types
    to SQLAlchemy column types. It handles:

    - Standard field types (str, int, bool, etc.)
    - Optional/nullable fields (T | None)
    - Optimistic concurrency control (_version column)
    - Enum fields (stored as String)
    - Foreign key references (*_id pattern)

    All mappings are database-agnostic and work with SQLite and PostgreSQL.

    Example:
        mapper = SchemaMapper()
        metadata = MetaData()

        table = mapper.create_table(Todo, metadata)
        # Returns SQLAlchemy Table with all columns mapped
    """

    def __init__(self, field_registry: FieldRegistry | None = None) -> None:
        """Initialize the mapper.

        Args:
            field_registry: Optional FieldRegistry instance.
                            Uses singleton if not provided.
        """
        self._field_registry = field_registry or FieldRegistry()

    def _get_table_name(self, model: type[BaseDocType]) -> str:
        """Get the table name for a DocType model.

        Uses __tablename__ if defined, otherwise derives from class name.

        Args:
            model: The DocType class

        Returns:
            Table name string (lowercase)
        """
        # Check for explicit __tablename__ attribute
        if hasattr(model, "__tablename__") and model.__tablename__:
            return str(model.__tablename__)
        # Default: lowercase class name
        return model.__name__.lower()

    def create_table(
        self,
        model: type[BaseDocType],
        metadata: MetaData,
    ) -> Table:
        """Create a SQLAlchemy Table from a Pydantic DocType model.

        Args:
            model: The DocType class to convert
            metadata: SQLAlchemy MetaData to attach the table to

        Returns:
            SQLAlchemy Table object with all columns mapped

        Note:
            - Uses `id` (UUID) as primary key for cheap renames
            - Uses `name` as unique index for human-readable lookup
            - Adds automatic indexes for:
              - owner (when RLS is enabled)
              - creation (for date ordering)
              - Custom indexes from Meta.indexes
            - For DocTypes with child table fields (list[DocType]),
              use create_tables() instead, which returns all related tables.
        """
        from sqlalchemy.types import UUID as SA_UUID

        table_name = self._get_table_name(model)
        columns: list[Column[Any]] = []

        # Add id column as primary key (UUID, auto-generated)
        # This allows cheap document renames without FK cascades
        columns.append(Column("id", SA_UUID, primary_key=True, nullable=False))

        # Process all fields from the model
        for field_name, field_info in model.model_fields.items():
            # Skip id - already added as primary key above
            if field_name == "id":
                continue
            # Skip child table fields - they become separate tables
            if self._is_child_doctype_field(field_info):
                continue
            column = self._create_column(field_name, field_info, metadata)
            columns.append(column)

        # Add _version column for optimistic concurrency control
        if self._has_occ(model):
            columns.append(Column("_version", Integer, nullable=False, default=0))

        # Add child table columns if this is a child table
        if self.is_child_table(model):
            columns.extend(
                [
                    Column(
                        "parent", String, nullable=False
                    ),  # Parent document ID (UUID as string)
                    Column("parenttype", String, nullable=False),  # Parent DocType name
                    Column("idx", Integer, nullable=False, default=0),  # Order index
                ]
            )

        # Create the table
        table = Table(table_name, metadata, *columns)

        # Add automatic indexes for query optimization
        self._add_automatic_indexes(table, model)

        # Add custom indexes from Meta.indexes
        self._add_custom_indexes(table, model)

        # Add child table indexes
        if self.is_child_table(model):
            self._add_child_table_indexes(table)

        return table

    def _add_automatic_indexes(
        self,
        table: Table,
        model: type[BaseDocType],
    ) -> None:
        """Add automatic indexes for common query patterns.

        Args:
            table: The SQLAlchemy Table
            model: The DocType class
        """
        from sqlalchemy import Index

        # Add index on owner for RLS filtering
        if model.get_apply_rls() and "owner" in table.c:
            Index(f"ix_{table.name}_owner", table.c.owner)

        # Add index on creation for date ordering
        if "creation" in table.c:
            Index(f"ix_{table.name}_creation", table.c.creation)

    def _add_custom_indexes(
        self,
        table: Table,
        model: type[BaseDocType],
    ) -> None:
        """Add custom indexes from Meta.indexes.

        Args:
            table: The SQLAlchemy Table
            model: The DocType class
        """
        from sqlalchemy import Index

        indexes = model.get_indexes()
        for index_spec in indexes:
            fields = index_spec.get("fields", [])
            if not fields:
                continue

            # Ensure fields is a list
            if isinstance(fields, str):
                fields = [fields]

            # Build column list
            columns = []
            for field_name in fields:
                if field_name in table.c:
                    columns.append(table.c[field_name])

            if columns:
                # Create index name based on fields
                field_names = "_".join(fields)
                index_name = f"ix_{table.name}_{field_names}"
                Index(index_name, *columns)

    def _add_child_table_indexes(self, table: Table) -> None:
        """Add indexes for child table columns.

        Child tables get two indexes:
        - parent column for fast lookups
        - (parent, idx) composite for ordered retrieval

        Args:
            table: The SQLAlchemy Table (must be a child table)
        """
        from sqlalchemy import Index

        # Index on parent for fast parent lookups
        Index(f"ix_{table.name}_parent", table.c.parent)

        # Composite index on (parent, idx) for ordered retrieval
        Index(f"ix_{table.name}_parent_idx", table.c.parent, table.c.idx)

    def create_tables(
        self,
        model: type[BaseDocType],
        metadata: MetaData,
    ) -> list[Table]:
        """Create SQLAlchemy Tables for a DocType and its child tables.

        This method handles DocTypes that have list[DocType] fields,
        creating separate child tables with proper parent references.

        Args:
            model: The DocType class to convert
            metadata: SQLAlchemy MetaData to attach tables to

        Returns:
            List of SQLAlchemy Table objects (parent first, then children)
        """
        tables: list[Table] = []

        # Create the main/parent table
        parent_table = self.create_table(model, metadata)
        tables.append(parent_table)

        # Create child tables for list[DocType] fields
        for field_name, field_info in model.model_fields.items():
            child_type = self._get_child_doctype_type(field_info)
            if child_type is not None:
                child_table = self._create_child_table(
                    child_type, field_name, model, metadata
                )
                tables.append(child_table)

        return tables

    def _create_child_table(
        self,
        child_model: type[BaseDocType],
        field_name: str,
        parent_model: type[BaseDocType],
        metadata: MetaData,
    ) -> Table:
        """Create a child table with parent reference columns.

        Child tables have additional columns for linking to parent:
        - parent: FK to parent document's name
        - parentfield: Name of the field in parent (e.g., "items")
        - parenttype: DocType name of parent (e.g., "Invoice")
        - idx: Integer for ordering within parent

        Args:
            child_model: The child DocType class
            field_name: Name of the field in parent
            parent_model: The parent DocType class
            metadata: SQLAlchemy MetaData

        Returns:
            SQLAlchemy Table for the child DocType
        """
        table_name = self._get_table_name(child_model)
        columns: list[Column[Any]] = []

        # Process child model's own fields
        for child_field_name, child_field_info in child_model.model_fields.items():
            if self._is_child_doctype_field(child_field_info):
                continue
            column = self._create_column(child_field_name, child_field_info, metadata)
            columns.append(column)

        # Add parent reference columns
        columns.extend(
            [
                Column("parent", String, nullable=False),  # FK to parent.name
                Column("parentfield", String, nullable=False),  # e.g., "items"
                Column("parenttype", String, nullable=False),  # e.g., "Invoice"
                Column(
                    "idx", Integer, nullable=False, default=0
                ),  # Order within parent
            ]
        )

        # Add _version for OCC if child model uses it
        if self._has_occ(child_model):
            columns.append(Column("_version", Integer, nullable=False, default=0))

        # Create the child table
        child_table = Table(table_name, metadata, *columns)

        # Add index on parent for efficient joins
        from sqlalchemy import Index

        Index(f"ix_{table_name}_parent", child_table.c.parent)

        return child_table

    def _is_child_doctype_field(self, field_info: FieldInfo) -> bool:
        """Check if a field is a list of DocType (child table).

        Args:
            field_info: Pydantic FieldInfo object

        Returns:
            True if field is list[DocType]
        """
        return self._get_child_doctype_type(field_info) is not None

    def _get_child_doctype_type(
        self, field_info: FieldInfo
    ) -> type[BaseDocType] | None:
        """Get the child DocType class from a list[DocType] field.

        Args:
            field_info: Pydantic FieldInfo object

        Returns:
            The child DocType class, or None if not a child field
        """
        python_type = field_info.annotation
        if python_type is None:
            return None

        origin = get_origin(python_type)
        if origin is not list:
            return None

        args = get_args(python_type)
        if not args:
            return None

        item_type = args[0]
        if isinstance(item_type, type) and issubclass(item_type, BaseDocType):
            return item_type

        return None

    def _create_column(
        self,
        field_name: str,
        field_info: FieldInfo,
        metadata: MetaData | None = None,
    ) -> Column[Any]:
        """Create a SQLAlchemy Column from a Pydantic field.

        Args:
            field_name: Name of the field
            field_info: Pydantic FieldInfo object
            metadata: Optional MetaData for resolving Link field foreign keys

        Returns:
            SQLAlchemy Column
        """
        python_type = field_info.annotation
        is_nullable = False
        is_unique = field_name == "name"  # name is unique, not PK

        # Handle Optional types (T | None) - supports both Union and Python 3.10+ |
        if python_type is not None:
            origin = get_origin(python_type)
            # Check for Union (typing.Union) or UnionType (Python 3.10+ T | None)
            if origin is Union or isinstance(python_type, types.UnionType):
                args = get_args(python_type)
                # Check if it's Optional (Union with None)
                if type(None) in args:
                    is_nullable = True
                    # Get the non-None type
                    non_none_types = [t for t in args if t is not type(None)]
                    if non_none_types:
                        python_type = non_none_types[0]

        # Ensure python_type is valid
        if python_type is None:
            python_type = str

        # Handle Enum types - store as String for database agnosticism
        sa_type: type[TypeEngine[Any]] | TypeEngine[Any]
        if isinstance(python_type, type) and issubclass(python_type, Enum):
            sa_type = String
        else:
            # Get SQLAlchemy type from registry
            try:
                sa_type = self._field_registry.get_sqlalchemy_type(python_type)
            except TypeError:
                # Fallback to String for unknown types
                sa_type = String

        # Required fields (no default) are not nullable
        if (
            not is_nullable
            and field_info.default is None
            and field_info.default_factory is None
        ):
            # Field has no default, so it's required
            is_nullable = False
        elif not is_nullable and (
            field_info.default is not None or field_info.default_factory is not None
        ):
            # Field has a default, but type is not Optional - still not nullable
            is_nullable = False

        # Check for Link field (foreign key reference)
        # Link fields have json_schema_extra={"link": "TargetDocType"}
        foreign_key = None
        if (
            field_info.json_schema_extra
            and isinstance(field_info.json_schema_extra, dict)
            and "link" in field_info.json_schema_extra
        ):
            target_doctype = field_info.json_schema_extra["link"]
            # Narrow type to str
            if not isinstance(target_doctype, str):
                # Skip if target_doctype is not a string
                pass
            # Try to find the target table in metadata
            elif metadata is not None:
                target_table_name = target_doctype.lower()
                if target_table_name in metadata.tables:
                    # Create ForeignKey constraint referencing target table's id
                    from sqlalchemy import ForeignKey

                    foreign_key = ForeignKey(f"{target_table_name}.id")

        # Check for unique constraint in json_schema_extra
        if (
            field_info.json_schema_extra
            and isinstance(field_info.json_schema_extra, dict)
            and field_info.json_schema_extra.get("unique") is True
        ):
            is_unique = True

        # Create column with or without foreign key
        if foreign_key is not None:
            return Column(
                field_name,
                sa_type,
                foreign_key,
                unique=is_unique,
                nullable=is_nullable,
            )
        else:
            return Column(
                field_name,
                sa_type,
                unique=is_unique,
                nullable=is_nullable,
            )

    def _has_occ(self, model: type[BaseDocType]) -> bool:
        """Check if model uses optimistic concurrency control.

        Args:
            model: The DocType class

        Returns:
            True if model has Meta.concurrency = "optimistic"
        """
        meta = getattr(model, "Meta", None)
        if meta is None:
            return False
        return getattr(meta, "concurrency", None) == "optimistic"

    def is_child_table(self, model: type[BaseDocType]) -> bool:
        """Check if a DocType is a child table.

        Child tables have Meta.is_child = True and are stored in separate
        tables with parent references (parent/parenttype/idx columns).

        Args:
            model: The DocType class

        Returns:
            True if model has Meta.is_child = True

        Example:
            class OrderItem(BaseDocType):
                class Meta:
                    is_child = True

            mapper = SchemaMapper()
            mapper.is_child_table(OrderItem)  # True
        """
        meta = getattr(model, "Meta", None)
        if meta is None:
            return False
        return getattr(meta, "is_child", False) is True

    def get_merged_fields(
        self, model: type[BaseDocType]
    ) -> dict[str, tuple[type[Any], FieldInfo]]:
        """Get the complete merged field schema for a DocType.

        This method returns all fields from the DocType, including:
        - Fields inherited from base classes
        - Fields defined in the DocType itself
        - Standard BaseDocType fields (id, name, creation, etc.)

        When a DocType overrides a base DocType, Pydantic's inheritance
        automatically merges the schemas. This method provides explicit
        access to the merged result for documentation and validation.

        Args:
            model: The DocType class (may be an override)

        Returns:
            Dictionary mapping field names to (type, FieldInfo) tuples

        Example:
            class User(BaseDocType):
                email: str

            class ExtendedUser(User):
                department: str

            mapper = SchemaMapper()
            fields = mapper.get_merged_fields(ExtendedUser)
            # Returns: {'id': ..., 'email': ..., 'department': ..., ...}
        """
        # Pydantic automatically merges fields from base classes
        # model.model_fields contains the complete merged schema
        result: dict[str, tuple[type[Any], FieldInfo]] = {}

        for field_name, field_info in model.model_fields.items():
            field_type = field_info.annotation or str
            result[field_name] = (field_type, field_info)

        return result

    def validate_override_schema(
        self,
        base_model: type[BaseDocType],
        override_model: type[BaseDocType],
    ) -> None:
        """Validate that an override schema is compatible with its base.

        Checks:
        - All base fields are present in override (cannot remove fields)
        - Field types are compatible (same type or compatible subtype)

        Args:
            base_model: The base DocType class
            override_model: The override DocType class

        Raises:
            ValueError: If override schema is invalid

        Example:
            class User(BaseDocType):
                email: str

            class ExtendedUser(User):
                department: str  # ✅ Adds field

            class InvalidUser(User):
                pass
            # If InvalidUser somehow removed email, would raise ValueError
        """
        base_fields = base_model.model_fields
        override_fields = override_model.model_fields

        # Check all base fields are present
        missing_fields = set(base_fields.keys()) - set(override_fields.keys())
        if missing_fields:
            raise ValueError(
                f"Override {override_model.__name__} is missing base fields: "
                f"{missing_fields}"
            )

        # Note: We don't validate field type changes here because:
        # 1. Pydantic allows compatible type changes (e.g., str -> str | None)
        # 2. Type incompatibilities will be caught at runtime by Pydantic
        # 3. Strict type checking is enforced by mypy --strict

    def detect_schema_changes(
        self,
        base_model: type[BaseDocType],
        override_model: type[BaseDocType],
    ) -> dict[str, Any]:
        """Detect schema changes between base and override DocTypes.

        Compares the fields of two DocType classes and identifies:
        - New fields added in the override
        - Fields with modified types or properties
        - Nullable changes

        Args:
            base_model: The base DocType class
            override_model: The override DocType class (may be same as base)

        Returns:
            Dictionary with:
            - 'added_fields': Dict of new fields with their metadata
            - 'modified_fields': Dict of fields with type changes
            - 'removed_fields': Dict of removed fields (should be empty)

        Example:
            class User(BaseDocType):
                email: str

            class ExtendedUser(User):
                department: str
                employee_id: str | None

            mapper = SchemaMapper()
            changes = mapper.detect_schema_changes(User, ExtendedUser)
            # Returns: {
            #   'added_fields': {
            #     'department': {'type': str, 'nullable': False, ...},
            #     'employee_id': {'type': str, 'nullable': True, ...}
            #   },
            #   'modified_fields': {},
            #   'removed_fields': {}
            # }
        """
        base_fields = base_model.model_fields
        override_fields = override_model.model_fields

        added_fields: dict[str, Any] = {}
        modified_fields: dict[str, Any] = {}
        removed_fields: dict[str, Any] = {}

        # Identify added fields
        for field_name, field_info in override_fields.items():
            if field_name not in base_fields:
                # This is a new field
                field_type = field_info.annotation or str
                is_nullable = self._is_field_nullable(field_info)

                # Get SQLAlchemy column type for this field
                sa_type = self._get_sa_type_for_field(field_type, field_info)

                added_fields[field_name] = {
                    "type": field_type,
                    "nullable": is_nullable,
                    "sa_type": sa_type,
                    "field_info": field_info,
                }

        # Identify modified fields
        for field_name in base_fields:
            if field_name in override_fields:
                base_field = base_fields[field_name]
                override_field = override_fields[field_name]

                # Check if type changed
                base_type = base_field.annotation
                override_type = override_field.annotation

                if base_type != override_type:
                    modified_fields[field_name] = {
                        "old_type": base_type,
                        "new_type": override_type,
                        "field_info": override_field,
                    }

        # Identify removed fields (shouldn't happen with proper inheritance)
        for field_name in base_fields:
            if field_name not in override_fields:
                removed_fields[field_name] = base_fields[field_name]

        return {
            "added_fields": added_fields,
            "modified_fields": modified_fields,
            "removed_fields": removed_fields,
        }

    def _is_field_nullable(self, field_info: FieldInfo) -> bool:
        """Check if a field is nullable.

        Args:
            field_info: Pydantic FieldInfo object

        Returns:
            True if field allows None, False otherwise
        """
        python_type = field_info.annotation
        if python_type is None:
            return True

        origin = get_origin(python_type)
        # Check for Union (typing.Union) or UnionType (Python 3.10+ T | None)
        if origin is Union or isinstance(python_type, types.UnionType):
            args = get_args(python_type)
            # Check if it's Optional (Union with None)
            if type(None) in args:
                return True

        # Has a default or default_factory
        if field_info.default is not None or field_info.default_factory is not None:
            # Even with default, if type doesn't include None, it's not nullable
            return False

        return False

    def _get_sa_type_for_field(
        self, python_type: Any, field_info: FieldInfo
    ) -> type[TypeEngine[Any]] | TypeEngine[Any]:
        """Get SQLAlchemy type for a Python type.

        Args:
            python_type: Python type annotation
            field_info: Pydantic FieldInfo object

        Returns:
            SQLAlchemy type
        """
        # Handle Union types - extract non-None type
        origin = get_origin(python_type)
        if origin is Union or isinstance(python_type, types.UnionType):
            args = get_args(python_type)
            non_none_types = [t for t in args if t is not type(None)]
            if non_none_types:
                python_type = non_none_types[0]

        # Handle Enum types
        if isinstance(python_type, type) and issubclass(python_type, Enum):
            return String

        # Get type from registry
        try:
            return self._field_registry.get_sqlalchemy_type(python_type)
        except TypeError:
            # Fallback to String for unknown types
            return String

    def generate_alter_table_statements(
        self,
        table_name: str,
        schema_changes: dict[str, Any],
        metadata: MetaData,
    ) -> list[Any]:
        """Generate ALTER TABLE DDL statements for schema changes.

        Creates database-agnostic DDL statements to alter an existing table
        based on detected schema changes. Only handles adding new columns.

        Args:
            table_name: Name of the table to alter
            schema_changes: Result from detect_schema_changes()
            metadata: SQLAlchemy MetaData object

        Returns:
            List of SQLAlchemy DDL objects (DDL statements)

        Example:
            changes = mapper.detect_schema_changes(User, ExtendedUser)
            statements = mapper.generate_alter_table_statements(
                'extendeduser', changes, metadata
            )
            # Returns: [DDL(...), DDL(...)]
        """
        from sqlalchemy import Column as SAColumn
        from sqlalchemy.schema import DDL

        statements: list[Any] = []

        added_fields = schema_changes.get("added_fields", {})

        if not added_fields:
            return statements

        for field_name, field_meta in added_fields.items():
            sa_type = field_meta["sa_type"]
            is_nullable = field_meta["nullable"]

            # Create column for type compilation
            column = SAColumn(
                field_name,
                sa_type,
                nullable=is_nullable,
            )

            # Build column type string using compile
            # This ensures database-agnostic type rendering
            type_str = str(column.type.compile())

            # Build NULL constraint
            null_clause = "" if is_nullable else " NOT NULL"

            # Create DDL statement
            ddl_text = (
                f"ALTER TABLE {table_name} ADD COLUMN {field_name} "
                f"{type_str}{null_clause}"
            )

            ddl = DDL(ddl_text)  # type: ignore[no-untyped-call]
            statements.append(ddl)

        return statements


__all__ = ["SchemaMapper"]
