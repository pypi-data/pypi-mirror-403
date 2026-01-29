"""Database adapters package.

This package contains database-related adapters including:
- FieldRegistry: Python to SQLAlchemy type mappings
- SchemaMapper: Pydantic model to SQLAlchemy table conversion
- TableRegistry: Storage for created SQLAlchemy tables
- ConnectionFactory: Manages async database engines
- SessionFactory: Creates async database sessions
- RepositoryFactory: Creates repositories with override support
- GenericRepository: RepositoryProtocol implementation
- initialize_database: Startup sequence orchestration
"""

from typing import Any

from sqlalchemy import MetaData

from framework_m.adapters.db.connection import ConnectionFactory
from framework_m.adapters.db.field_registry import FieldRegistry, FieldTypeInfo
from framework_m.adapters.db.generic_repository import (
    GenericRepository,
    VersionConflictError,
)
from framework_m.adapters.db.repository_factory import RepositoryFactory
from framework_m.adapters.db.schema_mapper import SchemaMapper
from framework_m.adapters.db.session import SessionFactory
from framework_m.adapters.db.table_registry import (
    DuplicateTableError,
    TableNotFoundError,
    TableRegistry,
)
from framework_m.core.registry import MetaRegistry


async def initialize_database(
    db_binds: dict[str, str],
    installed_apps: list[str] | None = None,
    auto_migrate: bool = False,
    **pool_options: Any,
) -> MetaData:
    """Initialize the database with DocTypes from MetaRegistry.

    This function orchestrates the full database startup sequence:
    1. Initialize database connection via ConnectionFactory
    2. Configure SessionFactory with connection
    3. Discover all DocTypes via MetaRegistry (if apps provided)
    4. Create tables via SchemaMapper
    5. Register tables in TableRegistry
    6. Create tables in the actual database
    7. Run auto-migration if enabled (future)

    Args:
        db_binds: Mapping of bind name to database URL
                  Example: {"default": "postgresql+asyncpg://..."}
        installed_apps: Optional list of app package names to discover DocTypes from
        auto_migrate: If True, run auto-migration after table creation
        **pool_options: Additional pool configuration options passed to ConnectionFactory

    Returns:
        SQLAlchemy MetaData containing all created tables

    Example:
        >>> await initialize_database(
        ...     db_binds={"default": "postgresql+asyncpg://user:pass@localhost/db"},
        ...     installed_apps=["myapp.doctypes"],
        ... )
    """
    # 1. Initialize database connection
    conn_factory = ConnectionFactory()
    conn_factory.configure(db_binds, **pool_options)

    # 2. Configure sessions
    session_factory = SessionFactory()
    session_factory.configure(conn_factory)

    # 3. Discover DocTypes (if apps provided)
    meta_registry = MetaRegistry()
    if installed_apps:
        meta_registry.load_apps(installed_apps)

    # 4. Create tables via SchemaMapper
    metadata = MetaData()
    schema_mapper = SchemaMapper()
    table_registry = TableRegistry()

    for doctype_name in meta_registry.list_doctypes():
        doctype_class = meta_registry.get_doctype(doctype_name)

        # Skip if table already registered (e.g., from previous init)
        if table_registry.table_exists(doctype_name):
            continue

        # Create tables (main + child tables)
        tables = schema_mapper.create_tables(doctype_class, metadata)

        # Register main table with DocType name
        if tables:
            table_registry.register_table(doctype_name, tables[0])

            # Register child tables with their actual table names
            for child_table in tables[1:]:
                child_name = child_table.name
                if not table_registry.table_exists(child_name):
                    table_registry.register_table(child_name, child_table)

    # 5. Create tables in database
    engine = conn_factory.get_engine("default")
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)

    # 6. Run auto-migration if enabled
    if auto_migrate:
        from pathlib import Path

        from sqlalchemy import create_engine

        from framework_m.adapters.db.migration import MigrationManager

        # Get the sync URL for migration (convert async URL to sync)
        async_url = str(engine.url)
        sync_url = async_url.replace("+aiosqlite", "").replace("+asyncpg", "")

        # Create sync engine for migrations
        sync_engine = create_engine(sync_url)

        # Use current working directory as base path for migrations
        manager = MigrationManager(base_path=Path.cwd(), database_url=sync_url)
        manager.auto_migrate(
            target_metadata=metadata, dev_mode=True, engine=sync_engine
        )

        sync_engine.dispose()

    return metadata


__all__ = [
    "ConnectionFactory",
    "DuplicateTableError",
    "FieldRegistry",
    "FieldTypeInfo",
    "GenericRepository",
    "RepositoryFactory",
    "SchemaMapper",
    "SessionFactory",
    "TableNotFoundError",
    "TableRegistry",
    "VersionConflictError",
    "initialize_database",
]
