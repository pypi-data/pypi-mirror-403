"""Migration CLI commands for Framework M.

This module provides CLI commands for database migrations:
- m migrate: Run pending migrations
- m migrate create: Create a new migration
- m migrate rollback: Rollback the last migration
- m migrate status: Show current migration status
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Annotated

import cyclopts

# Load .env from current directory, then parent directories
try:
    from dotenv import load_dotenv

    # Try current directory first
    if Path(".env").exists():
        load_dotenv(".env")
    # Then try parent directories (for monorepo structure)
    elif Path("../../.env").exists():
        load_dotenv("../../.env")
    elif Path("../.env").exists():
        load_dotenv("../.env")
except ImportError:
    pass  # dotenv not installed, skip env loading

from framework_m.adapters.db.migration import MigrationManager

# Create the migrate command group
migrate_app = cyclopts.App(
    name="migrate",
    help="Database migration commands",
)


def get_manager(
    path: Path, database_url: str | None = None, skip_alembic_check: bool = False
) -> MigrationManager:
    """Create a MigrationManager instance.

    Args:
        path: Base path for the application
        database_url: Optional database URL
        skip_alembic_check: Skip checking if alembic directory exists (for init command)

    Returns:
        Configured MigrationManager

    Raises:
        SystemExit: If alembic directory not found or database URL is invalid
    """
    # Check if alembic directory exists (skip for init command)
    alembic_dir = path / "alembic"
    if not skip_alembic_check and not alembic_dir.exists():
        print(f"✗ Error: Alembic not initialized in {path.absolute()}", file=sys.stderr)
        print(f"  Expected to find: {alembic_dir}", file=sys.stderr)
        print(
            "\n  Run 'm migrate init' first, or specify --path to your app directory:",
            file=sys.stderr,
        )
        print("    cd apps/test_app && m migrate init", file=sys.stderr)
        print("    m migrate status --path apps/test_app", file=sys.stderr)
        raise SystemExit(1)

    # Check database URL format
    db_url = database_url or os.environ.get("DATABASE_URL", "")
    if (
        db_url
        and db_url.startswith("sqlite://")
        and not db_url.startswith("sqlite+aiosqlite://")
    ):
        print("✗ Error: Invalid database URL for async operation", file=sys.stderr)
        print(f"  Got: {db_url}", file=sys.stderr)
        print("  Use 'sqlite+aiosqlite:///' instead of 'sqlite:///'", file=sys.stderr)
        print("\n  Example:", file=sys.stderr)
        print(
            "    DATABASE_URL='sqlite+aiosqlite:///./dev.db' m migrate status",
            file=sys.stderr,
        )
        raise SystemExit(1)

    return MigrationManager(base_path=path, database_url=database_url)


@migrate_app.default
@migrate_app.command(name="run")
def migrate(
    path: Annotated[
        Path,
        cyclopts.Parameter(name="--path", help="Path to the application directory"),
    ] = Path(),
    database_url: Annotated[
        str | None,
        cyclopts.Parameter(
            name="--database-url",
            env_var="DATABASE_URL",
            help="Database connection URL",
        ),
    ] = None,
    revision: Annotated[
        str,
        cyclopts.Parameter(name="--revision", help="Target revision (default: head)"),
    ] = "head",
) -> None:
    """Run pending database migrations.

    By default, upgrades to the latest revision (head).
    Can be called as 'm migrate' or 'm migrate run'.
    """
    manager = get_manager(path, database_url)

    print(f"Running migrations in {path.resolve()}...")
    try:
        manager.upgrade(revision)
        print("✓ Migrations completed successfully")
    except Exception as e:
        print(f"✗ Migration failed: {e}", file=sys.stderr)
        raise SystemExit(1) from e


@migrate_app.command
def create(
    message: Annotated[str, cyclopts.Parameter(help="Migration description")],
    path: Annotated[
        Path,
        cyclopts.Parameter(name="--path", help="Path to the application directory"),
    ] = Path(),
    database_url: Annotated[
        str | None,
        cyclopts.Parameter(
            name="--database-url",
            env_var="DATABASE_URL",
            help="Database connection URL",
        ),
    ] = None,
    autogenerate: Annotated[
        bool,
        cyclopts.Parameter(name="--autogenerate", help="Auto-detect schema changes"),
    ] = True,
) -> None:
    """Create a new migration file.

    Creates a new Alembic revision with the specified message.
    Use --no-autogenerate for an empty migration template.
    """
    manager = get_manager(path, database_url)

    print(f"Creating migration: {message}")
    try:
        manager.revision(message=message, autogenerate=autogenerate)
        print("✓ Migration created successfully")
    except Exception as e:
        print(f"✗ Failed to create migration: {e}", file=sys.stderr)
        raise SystemExit(1) from e


@migrate_app.command
def rollback(
    path: Annotated[
        Path,
        cyclopts.Parameter(name="--path", help="Path to the application directory"),
    ] = Path(),
    database_url: Annotated[
        str | None,
        cyclopts.Parameter(
            name="--database-url",
            env_var="DATABASE_URL",
            help="Database connection URL",
        ),
    ] = None,
    steps: Annotated[
        int,
        cyclopts.Parameter(name="--steps", help="Number of migrations to rollback"),
    ] = 1,
) -> None:
    """Rollback database migrations.

    By default, rolls back one migration. Use --steps to rollback more.
    """
    manager = get_manager(path, database_url)

    revision = f"-{steps}"
    print(f"Rolling back {steps} migration(s)...")
    try:
        manager.downgrade(revision)
        print("✓ Rollback completed successfully")
    except Exception as e:
        print(f"✗ Rollback failed: {e}", file=sys.stderr)
        raise SystemExit(1) from e


@migrate_app.command
def status(
    path: Annotated[
        Path,
        cyclopts.Parameter(name="--path", help="Path to the application directory"),
    ] = Path(),
    database_url: Annotated[
        str | None,
        cyclopts.Parameter(
            name="--database-url",
            env_var="DATABASE_URL",
            help="Database connection URL",
        ),
    ] = None,
) -> None:
    """Show current migration status.

    Displays the current database revision information.
    """
    manager = get_manager(path, database_url)

    print("Migration Status:")
    print("-" * 40)
    try:
        manager.current()
    except Exception as e:
        print(f"✗ Failed to get status: {e}", file=sys.stderr)
        raise SystemExit(1) from e


@migrate_app.command
def history(
    path: Annotated[
        Path,
        cyclopts.Parameter(name="--path", help="Path to the application directory"),
    ] = Path(),
    database_url: Annotated[
        str | None,
        cyclopts.Parameter(
            name="--database-url",
            env_var="DATABASE_URL",
            help="Database connection URL",
        ),
    ] = None,
) -> None:
    """Show migration history.

    Lists all migrations in chronological order.
    """
    manager = get_manager(path, database_url)

    print("Migration History:")
    print("-" * 40)
    try:
        manager.history()
    except Exception as e:
        print(f"✗ Failed to get history: {e}", file=sys.stderr)
        raise SystemExit(1) from e


@migrate_app.command(name="init")
def init_alembic(
    path: Annotated[
        Path,
        cyclopts.Parameter(name="--path", help="Path to the application directory"),
    ] = Path(),
    database_url: Annotated[
        str | None,
        cyclopts.Parameter(
            name="--database-url",
            env_var="DATABASE_URL",
            help="Database connection URL",
        ),
    ] = None,
) -> None:
    """Initialize Alembic for this project.

    Creates the alembic directory structure and configuration files.
    """
    manager = get_manager(path, database_url, skip_alembic_check=True)

    print(f"Initializing Alembic in {path.resolve()}...")
    try:
        manager.init()
        print("✓ Alembic initialized successfully")
        print(f"  Created: {manager.alembic_path}")
    except Exception as e:
        print(f"✗ Initialization failed: {e}", file=sys.stderr)
        raise SystemExit(1) from e


__all__ = [
    "get_manager",
    "migrate_app",
]
