"""Migration support for Framework M using Alembic.

This module provides utilities for database migrations using Alembic,
with integration to the Framework M DocType system.

Features:
- Auto-detection of schema changes from DocType definitions
- Integration with MetaRegistry and SchemaMapper
- Async database support
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from alembic.config import Config
from sqlalchemy import MetaData

from alembic import command

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


class SchemaChangeType(Enum):
    """Types of schema changes that can be detected."""

    NEW_TABLE = "new_table"
    NEW_COLUMN = "new_column"
    TYPE_CHANGE = "type_change"
    DROPPED_TABLE = "dropped_table"
    DROPPED_COLUMN = "dropped_column"


@dataclass
class SchemaChange:
    """Represents a detected schema change.

    Attributes:
        change_type: Type of change (new table, new column, etc.)
        table_name: Name of the affected table
        column_name: Name of the affected column (if applicable)
        old_type: Previous column type (for type changes)
        new_type: New column type (for type changes)
        details: Additional details about the change
    """

    change_type: SchemaChangeType
    table_name: str
    column_name: str | None = None
    old_type: str | None = None
    new_type: str | None = None
    details: dict[str, str] = field(default_factory=dict)


class MigrationManager:
    """Manages database migrations using Alembic.

    This class provides methods to initialize, run, and manage
    database migrations for Framework M applications.

    Example:
        >>> manager = MigrationManager("/path/to/app")
        >>> manager.init()  # Initialize Alembic
        >>> manager.upgrade("head")  # Run migrations
    """

    def __init__(
        self,
        base_path: str | Path,
        database_url: str | None = None,
    ) -> None:
        """Initialize the migration manager.

        Args:
            base_path: Base path for the application (where alembic/ will be created)
            database_url: Database connection URL (can also come from env var)
        """
        self._base_path = Path(base_path)
        self._database_url = database_url or os.environ.get("DATABASE_URL", "")
        self._alembic_path = self._base_path / "alembic"
        self._config: Config | None = None

    @property
    def alembic_path(self) -> Path:
        """Path to the alembic directory."""
        return self._alembic_path

    @property
    def versions_path(self) -> Path:
        """Path to the versions directory."""
        return self._alembic_path / "versions"

    @property
    def config(self) -> Config:
        """Get or create the Alembic configuration."""
        if self._config is None:
            self._config = self._create_config()
        return self._config

    def _create_config(self) -> Config:
        """Create an Alembic configuration object.

        Returns:
            Configured Alembic Config object
        """
        ini_path = self._base_path / "alembic.ini"

        config = Config(str(ini_path) if ini_path.exists() else None)

        # Set core paths
        config.set_main_option("script_location", str(self._alembic_path))

        # Set database URL (with fallback to async SQLite default)
        if self._database_url:
            config.set_main_option("sqlalchemy.url", self._database_url)
        elif not ini_path.exists():
            # If no alembic.ini and no explicit URL, use async SQLite default
            config.set_main_option("sqlalchemy.url", "sqlite+aiosqlite:///./dev.db")

        return config

    def init(self, metadata: MetaData | None = None) -> None:
        """Initialize Alembic for this project.

        Creates the alembic directory structure and configuration files.

        Args:
            metadata: Optional SQLAlchemy MetaData for schema comparison
        """
        # Create directories
        self._alembic_path.mkdir(parents=True, exist_ok=True)
        self.versions_path.mkdir(parents=True, exist_ok=True)

        # Create alembic.ini if it doesn't exist
        self._create_alembic_ini()

        # Create env.py with async support
        self._create_env_py()

        # Create script.py.mako template
        self._create_script_template()

    def _create_alembic_ini(self) -> None:
        """Create the alembic.ini configuration file."""
        ini_path = self._base_path / "alembic.ini"

        if ini_path.exists():
            return

        ini_content = """# Alembic Configuration for Framework M
# Auto-generated - customize as needed

[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os

# Database URL - recommend setting via DATABASE_URL env var
# For async SQLite: sqlite+aiosqlite:///./dev.db
# For PostgreSQL: postgresql+asyncpg://user:pass@localhost/dbname
sqlalchemy.url = sqlite+aiosqlite:///./dev.db

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""
        ini_path.write_text(ini_content)

    def _create_env_py(self) -> None:
        """Create the env.py file with async support and DocType discovery."""
        env_path = self._alembic_path / "env.py"

        if env_path.exists():
            return

        env_content = '''"""Alembic environment configuration for Framework M.

This file is auto-generated but can be customized.
It provides async database support and integration with the DocType system.
"""

import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import MetaData, pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def discover_doctypes() -> MetaData:
    """Discover DocTypes from the project and build MetaData.

    Scans src/doctypes for DocType definitions and creates SQLAlchemy tables.
    """
    from framework_m.adapters.db.schema_mapper import SchemaMapper
    from framework_m.core.domain.base_doctype import BaseDocType

    metadata = MetaData()
    mapper = SchemaMapper()

    # Potential DocType locations
    doctype_dirs = [
        project_root / "src" / "doctypes",
        project_root / "doctypes",
    ]

    for doctypes_dir in doctype_dirs:
        if not doctypes_dir.exists():
            continue

        # Scan for Python files
        for py_file in doctypes_dir.rglob("*.py"):
            if py_file.name.startswith("_") or py_file.name.startswith("test_"):
                continue

            try:
                # Import the module
                relative_path = py_file.relative_to(project_root)
                module_name = str(relative_path.with_suffix("")).replace("/", ".").replace("\\\\", ".")

                import importlib.util
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    # Find BaseDocType subclasses
                    for name in dir(module):
                        obj = getattr(module, name)
                        if (
                            isinstance(obj, type)
                            and issubclass(obj, BaseDocType)
                            and obj is not BaseDocType
                            and not name.startswith("_")
                        ):
                            # Create table for this DocType
                            mapper.create_table(obj, metadata)
            except Exception:
                # Skip files that fail to import
                pass

    return metadata


# Build target_metadata from discovered DocTypes
target_metadata = discover_doctypes()


def get_url() -> str:
    """Get database URL from environment or config."""
    return os.environ.get("DATABASE_URL", config.get_main_option("sqlalchemy.url", ""))


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well. By skipping the Engine
    creation we don't even need a DBAPI to be available.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with the given connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''
        env_path.write_text(env_content)

    def _create_script_template(self) -> None:
        """Create the script.py.mako template."""
        template_path = self._alembic_path / "script.py.mako"

        if template_path.exists():
            return

        template_content = '''"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    """Upgrade database schema."""
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """Downgrade database schema."""
    ${downgrades if downgrades else "pass"}
'''
        template_path.write_text(template_content)

    def upgrade(self, revision: str = "head") -> None:
        """Upgrade to a later version.

        Args:
            revision: Target revision (default: "head")
        """
        command.upgrade(self.config, revision)

    def downgrade(self, revision: str = "-1") -> None:
        """Downgrade to a previous version.

        Args:
            revision: Target revision (default: previous version)
        """
        command.downgrade(self.config, revision)

    def revision(
        self,
        message: str,
        autogenerate: bool = True,
    ) -> None:
        """Create a new revision file.

        Args:
            message: Message describing the revision
            autogenerate: Whether to auto-detect schema changes
        """
        command.revision(
            self.config,
            message=message,
            autogenerate=autogenerate,
        )

    def current(self) -> None:
        """Display the current revision."""
        command.current(self.config)

    def history(self) -> None:
        """List revision history."""
        command.history(self.config)

    def heads(self) -> None:
        """Show current available heads."""
        command.heads(self.config)

    def detect_schema_changes(
        self,
        target_metadata: MetaData,
        current_metadata: MetaData | None = None,
    ) -> list[SchemaChange]:
        """Detect schema changes between target and current database schema.

        Compares the target metadata (from DocType definitions) with the
        current database schema to detect:
        - New tables
        - New columns
        - Type changes
        - Dropped tables/columns

        Args:
            target_metadata: Target schema (from DocTypes)
            current_metadata: Current database schema (if None, compares against empty)

        Returns:
            List of SchemaChange objects describing detected changes
        """
        changes: list[SchemaChange] = []

        if current_metadata is None:
            current_metadata = MetaData()

        target_tables = set(target_metadata.tables.keys())
        current_tables = set(current_metadata.tables.keys())

        # Detect new tables
        for table_name in target_tables - current_tables:
            changes.append(
                SchemaChange(
                    change_type=SchemaChangeType.NEW_TABLE,
                    table_name=table_name,
                )
            )

        # Detect dropped tables
        for table_name in current_tables - target_tables:
            changes.append(
                SchemaChange(
                    change_type=SchemaChangeType.DROPPED_TABLE,
                    table_name=table_name,
                )
            )

        # Detect column changes for existing tables
        for table_name in target_tables & current_tables:
            target_table = target_metadata.tables[table_name]
            current_table = current_metadata.tables[table_name]

            target_columns = {c.name for c in target_table.columns}
            current_columns = {c.name for c in current_table.columns}

            # New columns
            for column_name in target_columns - current_columns:
                changes.append(
                    SchemaChange(
                        change_type=SchemaChangeType.NEW_COLUMN,
                        table_name=table_name,
                        column_name=column_name,
                    )
                )

            # Dropped columns
            for column_name in current_columns - target_columns:
                changes.append(
                    SchemaChange(
                        change_type=SchemaChangeType.DROPPED_COLUMN,
                        table_name=table_name,
                        column_name=column_name,
                    )
                )

            # Type changes (for columns that exist in both)
            for column_name in target_columns & current_columns:
                target_col = target_table.columns[column_name]
                current_col = current_table.columns[column_name]

                target_type = str(target_col.type)
                current_type = str(current_col.type)

                if target_type != current_type:
                    changes.append(
                        SchemaChange(
                            change_type=SchemaChangeType.TYPE_CHANGE,
                            table_name=table_name,
                            column_name=column_name,
                            old_type=current_type,
                            new_type=target_type,
                        )
                    )

        return changes

    def auto_migrate(
        self,
        target_metadata: MetaData,
        dry_run: bool = False,
        dev_mode: bool = False,
        engine: Engine | None = None,
    ) -> list[SchemaChange]:
        """Auto-detect and optionally apply schema migrations.

        This method:
        1. Reflects current database schema
        2. Detects schema changes from target metadata
        3. If dev_mode is True, applies changes directly using DDL
        4. Otherwise, generates an Alembic migration file

        Args:
            target_metadata: Target schema (from DocTypes)
            dry_run: If True, only detect changes without applying
            dev_mode: If True, apply changes directly (no Alembic)
            engine: SQLAlchemy engine for reflection (uses database_url if None)

        Returns:
            List of detected SchemaChange objects
        """
        from sqlalchemy import create_engine, text

        # Create engine if not provided
        if engine is None:
            db_url = self._database_url or "sqlite:///app.db"
            engine = create_engine(db_url)

        # Reflect current database schema
        current_metadata = MetaData()
        current_metadata.reflect(bind=engine)

        # Detect changes
        changes = self.detect_schema_changes(
            target_metadata=target_metadata,
            current_metadata=current_metadata,
        )

        if not changes or dry_run:
            return changes

        if dev_mode:
            # Apply changes directly using DDL (avoids Alembic async issues)
            with engine.begin() as conn:
                for change in changes:
                    if change.change_type == SchemaChangeType.NEW_TABLE:
                        # Create new table
                        table = target_metadata.tables.get(change.table_name)
                        if table is not None:
                            table.create(bind=conn)

                    elif change.change_type == SchemaChangeType.NEW_COLUMN:
                        # Add new column using ALTER TABLE
                        table = target_metadata.tables.get(change.table_name)
                        if table is not None and change.column_name:
                            column = table.c.get(change.column_name)
                            if column is not None:
                                # Get column type as SQL string
                                col_type = column.type.compile(dialect=engine.dialect)
                                nullable = "NULL" if column.nullable else "NOT NULL"
                                default = ""
                                if column.default is not None:
                                    # Handle different default types
                                    default_val = getattr(column.default, "arg", None)
                                    if callable(default_val):
                                        pass  # Skip callable defaults
                                    elif isinstance(default_val, str):
                                        default = f" DEFAULT '{default_val}'"
                                    elif default_val is not None:
                                        default = f" DEFAULT {default_val}"

                                # SQLite uses simpler syntax
                                if "sqlite" in str(engine.url):
                                    sql = (
                                        f"ALTER TABLE {change.table_name} "
                                        f"ADD COLUMN {change.column_name} "
                                        f"{col_type}{default}"
                                    )
                                else:
                                    sql = (
                                        f"ALTER TABLE {change.table_name} "
                                        f"ADD COLUMN {change.column_name} "
                                        f"{col_type} {nullable}{default}"
                                    )
                                conn.execute(text(sql))
        else:
            # Generate Alembic migration (for production use)
            change_summary = ", ".join(
                f"{c.change_type.value}: {c.table_name}" for c in changes[:3]
            )
            if len(changes) > 3:
                change_summary += f" (+{len(changes) - 3} more)"

            self.revision(
                message=f"Auto-migration: {change_summary}",
                autogenerate=True,
            )
            self.upgrade("head")

        return changes


__all__ = ["MigrationManager", "SchemaChange", "SchemaChangeType"]
