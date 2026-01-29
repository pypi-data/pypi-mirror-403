"""Tests for initialize_database function."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest

from framework_m import DocType, Field
from framework_m.adapters.db import (
    ConnectionFactory,
    SessionFactory,
    TableRegistry,
    initialize_database,
)
from framework_m.core.registry import MetaRegistry

# =============================================================================
# Test DocTypes
# =============================================================================


class InitTestDoc(DocType):
    """Test DocType for initialization tests."""

    title: str = Field(description="Document title")
    value: int = Field(default=0)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
async def reset_all_singletons() -> AsyncGenerator[None, None]:
    """Reset all singleton registries before each test and cleanup after."""
    # Setup
    conn_factory = ConnectionFactory()
    conn_factory.reset()
    SessionFactory().reset()
    TableRegistry().reset()
    MetaRegistry().clear()

    yield

    # Cleanup - dispose all engines
    for bind_name in conn_factory.list_engines():
        engine = conn_factory.get_engine(bind_name)
        await engine.dispose()

    conn_factory.reset()
    SessionFactory().reset()


# =============================================================================
# Tests for initialize_database
# =============================================================================


class TestInitializeDatabaseImport:
    """Tests for initialize_database imports."""

    def test_import_initialize_database(self) -> None:
        """initialize_database should be importable from adapters.db."""
        from framework_m.adapters.db import initialize_database

        assert initialize_database is not None
        assert callable(initialize_database)


class TestInitializeDatabaseConfigures:
    """Tests that initialize_database configures factories correctly."""

    @pytest.mark.asyncio
    async def test_configures_connection_factory(self) -> None:
        """initialize_database should configure ConnectionFactory."""
        # Register a DocType first
        MetaRegistry().register_doctype(InitTestDoc)

        await initialize_database(
            db_binds={"default": "sqlite+aiosqlite:///:memory:"},
        )

        conn_factory = ConnectionFactory()
        assert conn_factory.has_engine("default")

    @pytest.mark.asyncio
    async def test_configures_session_factory(self) -> None:
        """initialize_database should configure SessionFactory."""
        MetaRegistry().register_doctype(InitTestDoc)

        await initialize_database(
            db_binds={"default": "sqlite+aiosqlite:///:memory:"},
        )

        session_factory = SessionFactory()
        assert session_factory.is_configured


class TestInitializeDatabaseCreatesTable:
    """Tests that initialize_database creates tables."""

    @pytest.mark.asyncio
    async def test_registers_tables_in_table_registry(self) -> None:
        """initialize_database should register tables in TableRegistry."""
        MetaRegistry().register_doctype(InitTestDoc)

        await initialize_database(
            db_binds={"default": "sqlite+aiosqlite:///:memory:"},
        )

        table_registry = TableRegistry()
        assert table_registry.table_exists("InitTestDoc")

    @pytest.mark.asyncio
    async def test_creates_tables_in_database(self) -> None:
        """initialize_database should create tables in the database."""
        MetaRegistry().register_doctype(InitTestDoc)

        metadata = await initialize_database(
            db_binds={"default": "sqlite+aiosqlite:///:memory:"},
        )

        # Verify table exists in metadata
        assert "inittestdoc" in metadata.tables

    @pytest.mark.asyncio
    async def test_returns_metadata(self) -> None:
        """initialize_database should return SQLAlchemy MetaData."""
        from sqlalchemy import MetaData

        MetaRegistry().register_doctype(InitTestDoc)

        result = await initialize_database(
            db_binds={"default": "sqlite+aiosqlite:///:memory:"},
        )

        assert isinstance(result, MetaData)


class TestInitializeDatabaseIdempotent:
    """Tests that initialize_database is idempotent."""

    @pytest.mark.asyncio
    async def test_can_run_multiple_times(self) -> None:
        """initialize_database should be idempotent (can run twice)."""
        MetaRegistry().register_doctype(InitTestDoc)

        # First init
        await initialize_database(
            db_binds={"default": "sqlite+aiosqlite:///:memory:"},
        )

        # Dispose and reset connection to simulate restart
        engine = ConnectionFactory().get_engine("default")
        await engine.dispose()
        ConnectionFactory().reset()
        SessionFactory().reset()

        # Second init should not raise
        await initialize_database(
            db_binds={"default": "sqlite+aiosqlite:///:memory:"},
        )

        # Table should still be registered
        assert TableRegistry().table_exists("InitTestDoc")


class TestInitializeDatabaseNoDocTypes:
    """Tests initialize_database with no registered DocTypes."""

    @pytest.mark.asyncio
    async def test_works_with_no_doctypes(self) -> None:
        """initialize_database should work when no DocTypes registered."""
        # Don't register any DocTypes
        metadata = await initialize_database(
            db_binds={"default": "sqlite+aiosqlite:///:memory:"},
        )

        # Should still configure factories
        assert ConnectionFactory().has_engine("default")
        assert SessionFactory().is_configured

        # Metadata should be empty
        assert len(metadata.tables) == 0


class TestInitializeDatabaseAutoMigrate:
    """Tests for auto_migrate functionality."""

    @pytest.mark.asyncio
    async def test_auto_migrate_calls_migration_manager(self) -> None:
        """initialize_database with auto_migrate=True should call MigrationManager."""
        from unittest.mock import MagicMock, patch

        MetaRegistry().register_doctype(InitTestDoc)

        # Mock MigrationManager at its source - patch in migration module
        with patch(
            "framework_m.adapters.db.migration.MigrationManager"
        ) as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager

            await initialize_database(
                db_binds={"default": "sqlite+aiosqlite:///:memory:"},
                auto_migrate=True,
            )

            # Verify MigrationManager was instantiated and auto_migrate called
            mock_manager_class.assert_called_once()
            mock_manager.auto_migrate.assert_called_once()

            # Verify auto_migrate was called with correct arguments
            call_args = mock_manager.auto_migrate.call_args
            assert call_args.kwargs.get("dev_mode") is True
