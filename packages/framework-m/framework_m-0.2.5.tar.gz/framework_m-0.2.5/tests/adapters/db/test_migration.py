"""Tests for MigrationManager."""

from __future__ import annotations

from pathlib import Path

from framework_m.adapters.db.migration import MigrationManager

# =============================================================================
# Test: MigrationManager Creation
# =============================================================================


class TestMigrationManagerCreation:
    """Tests for MigrationManager instantiation."""

    def test_create_migration_manager(self) -> None:
        """MigrationManager should be creatable with base path."""
        manager = MigrationManager("/tmp/test")
        assert manager is not None

    def test_create_with_database_url(self) -> None:
        """MigrationManager should accept database URL."""
        manager = MigrationManager("/tmp/test", database_url="sqlite:///test.db")
        assert manager._database_url == "sqlite:///test.db"


# =============================================================================
# Test: Initialization
# =============================================================================


class TestMigrationManagerInit:
    """Tests for MigrationManager initialization."""

    def test_init_creates_alembic_directory(self, tmp_path: Path) -> None:
        """init() should create alembic directory."""
        manager = MigrationManager(tmp_path)
        manager.init()

        assert (tmp_path / "alembic").exists()
        assert (tmp_path / "alembic").is_dir()

    def test_init_creates_versions_directory(self, tmp_path: Path) -> None:
        """init() should create versions directory."""
        manager = MigrationManager(tmp_path)
        manager.init()

        assert (tmp_path / "alembic" / "versions").exists()
        assert (tmp_path / "alembic" / "versions").is_dir()

    def test_init_creates_alembic_ini(self, tmp_path: Path) -> None:
        """init() should create alembic.ini file."""
        manager = MigrationManager(tmp_path)
        manager.init()

        ini_path = tmp_path / "alembic.ini"
        assert ini_path.exists()
        assert "script_location = alembic" in ini_path.read_text()

    def test_init_creates_env_py(self, tmp_path: Path) -> None:
        """init() should create env.py with async support."""
        manager = MigrationManager(tmp_path)
        manager.init()

        env_path = tmp_path / "alembic" / "env.py"
        assert env_path.exists()

        content = env_path.read_text()
        assert "async_engine_from_config" in content
        assert "run_async_migrations" in content

    def test_init_creates_script_template(self, tmp_path: Path) -> None:
        """init() should create script.py.mako template."""
        manager = MigrationManager(tmp_path)
        manager.init()

        template_path = tmp_path / "alembic" / "script.py.mako"
        assert template_path.exists()
        assert "upgrade()" in template_path.read_text()

    def test_init_is_idempotent(self, tmp_path: Path) -> None:
        """init() should not overwrite existing files."""
        manager = MigrationManager(tmp_path)
        manager.init()

        ini_path = tmp_path / "alembic.ini"
        original_content = ini_path.read_text()

        # Add custom content
        ini_path.write_text(original_content + "\n# custom")

        # Run init again
        manager.init()

        # Custom content should still be there
        assert "# custom" in ini_path.read_text()


# =============================================================================
# Test: Properties
# =============================================================================


class TestMigrationManagerProperties:
    """Tests for MigrationManager properties."""

    def test_alembic_path_property(self, tmp_path: Path) -> None:
        """alembic_path should return correct path."""
        manager = MigrationManager(tmp_path)
        assert manager.alembic_path == tmp_path / "alembic"

    def test_versions_path_property(self, tmp_path: Path) -> None:
        """versions_path should return correct path."""
        manager = MigrationManager(tmp_path)
        assert manager.versions_path == tmp_path / "alembic" / "versions"


# =============================================================================
# Test: Schema Change Detection
# =============================================================================


class TestDetectSchemaChanges:
    """Tests for detect_schema_changes() functionality."""

    def test_detect_new_table(self, tmp_path: Path) -> None:
        """detect_schema_changes() should detect new tables."""
        # Create metadata with a new table
        from sqlalchemy import Column, Integer, MetaData, String, Table

        from framework_m.adapters.db.migration import SchemaChangeType

        target_metadata = MetaData()
        Table(
            "new_table",
            target_metadata,
            Column("id", Integer, primary_key=True),
            Column("name", String(100)),
        )

        manager = MigrationManager(tmp_path)
        changes = manager.detect_schema_changes(
            target_metadata=target_metadata,
            current_metadata=MetaData(),  # Empty database
        )

        assert len(changes) == 1
        assert changes[0].change_type == SchemaChangeType.NEW_TABLE
        assert changes[0].table_name == "new_table"

    def test_detect_new_column(self, tmp_path: Path) -> None:
        """detect_schema_changes() should detect new columns."""
        from sqlalchemy import Column, Integer, MetaData, String, Table

        from framework_m.adapters.db.migration import SchemaChangeType

        # Current schema
        current_metadata = MetaData()
        Table(
            "users",
            current_metadata,
            Column("id", Integer, primary_key=True),
        )

        # Target schema with new column
        target_metadata = MetaData()
        Table(
            "users",
            target_metadata,
            Column("id", Integer, primary_key=True),
            Column("email", String(255)),
        )

        manager = MigrationManager(tmp_path)
        changes = manager.detect_schema_changes(
            target_metadata=target_metadata,
            current_metadata=current_metadata,
        )

        assert len(changes) == 1
        assert changes[0].change_type == SchemaChangeType.NEW_COLUMN
        assert changes[0].table_name == "users"
        assert changes[0].column_name == "email"

    def test_detect_no_changes(self, tmp_path: Path) -> None:
        """detect_schema_changes() should return empty list when no changes."""
        from sqlalchemy import Column, Integer, MetaData, Table

        # Identical schemas
        metadata = MetaData()
        Table(
            "users",
            metadata,
            Column("id", Integer, primary_key=True),
        )

        manager = MigrationManager(tmp_path)
        changes = manager.detect_schema_changes(
            target_metadata=metadata,
            current_metadata=metadata,
        )

        assert len(changes) == 0


# =============================================================================
# Test: Auto-Migrate
# =============================================================================


class TestAutoMigrate:
    """Tests for auto_migrate() functionality."""

    def test_auto_migrate_returns_changes(self, tmp_path: Path) -> None:
        """auto_migrate() should return detected changes."""
        from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine

        target_metadata = MetaData()
        Table(
            "products",
            target_metadata,
            Column("id", Integer, primary_key=True),
            Column("name", String(100)),
        )

        # Create explicit sync SQLite engine to avoid aiosqlite async issues
        db_path = tmp_path / "test.db"
        engine = create_engine(f"sqlite:///{db_path}")

        manager = MigrationManager(tmp_path, database_url=f"sqlite:///{db_path}")
        manager.init()

        changes = manager.auto_migrate(
            target_metadata=target_metadata,
            dry_run=True,
            engine=engine,
        )

        assert len(changes) >= 1

    def test_auto_migrate_dry_run_no_files(self, tmp_path: Path) -> None:
        """auto_migrate(dry_run=True) should not create migration files."""
        from sqlalchemy import Column, Integer, MetaData, Table, create_engine

        target_metadata = MetaData()
        Table(
            "test_table",
            target_metadata,
            Column("id", Integer, primary_key=True),
        )

        # Create explicit sync SQLite engine to avoid aiosqlite async issues
        db_path = tmp_path / "test.db"
        engine = create_engine(f"sqlite:///{db_path}")

        manager = MigrationManager(tmp_path, database_url=f"sqlite:///{db_path}")
        manager.init()

        manager.auto_migrate(
            target_metadata=target_metadata, dry_run=True, engine=engine
        )

        # No migration files should be created
        versions_dir = tmp_path / "alembic" / "versions"
        migration_files = list(versions_dir.glob("*.py"))
        assert len(migration_files) == 0


# =============================================================================
# Test: SchemaChange Dataclass
# =============================================================================


class TestSchemaChange:
    """Tests for SchemaChange dataclass."""

    def test_schema_change_creation(self) -> None:
        """SchemaChange should be creatable with required fields."""
        from framework_m.adapters.db.migration import SchemaChange, SchemaChangeType

        change = SchemaChange(
            change_type=SchemaChangeType.NEW_TABLE,
            table_name="users",
        )

        assert change.change_type == SchemaChangeType.NEW_TABLE
        assert change.table_name == "users"
        assert change.column_name is None

    def test_schema_change_with_column(self) -> None:
        """SchemaChange should support column information."""
        from framework_m.adapters.db.migration import SchemaChange, SchemaChangeType

        change = SchemaChange(
            change_type=SchemaChangeType.NEW_COLUMN,
            table_name="users",
            column_name="email",
        )

        assert change.column_name == "email"


# =============================================================================
# Test: Import
# =============================================================================


class TestMigrationImport:
    """Tests for migration module imports."""

    def test_import_migration_manager(self) -> None:
        """MigrationManager should be importable."""
        from framework_m.adapters.db.migration import MigrationManager

        assert MigrationManager is not None

    def test_import_schema_change(self) -> None:
        """SchemaChange should be importable."""
        from framework_m.adapters.db.migration import SchemaChange, SchemaChangeType

        assert SchemaChange is not None
        assert SchemaChangeType is not None


# =============================================================================
# Test: Config Creation
# =============================================================================


class TestConfigCreation:
    """Tests for config creation and properties."""

    def test_config_property_creates_on_demand(self, tmp_path: Path) -> None:
        """config property should create config on first access."""
        manager = MigrationManager(tmp_path, database_url="sqlite:///test.db")
        manager.init()

        config = manager.config
        assert config is not None

    def test_config_sets_database_url(self, tmp_path: Path) -> None:
        """config should have database URL set."""
        manager = MigrationManager(tmp_path, database_url="sqlite:///test.db")
        manager.init()

        config = manager.config
        assert "sqlite" in config.get_main_option("sqlalchemy.url")


# =============================================================================
# Test: Detect Schema Changes - Edge Cases
# =============================================================================


class TestDetectSchemaChangesEdgeCases:
    """Edge case tests for detect_schema_changes()."""

    def test_detect_dropped_table(self, tmp_path: Path) -> None:
        """detect_schema_changes() should detect dropped tables."""
        from sqlalchemy import Column, Integer, MetaData, Table

        from framework_m.adapters.db.migration import SchemaChangeType

        # Current has a table
        current_metadata = MetaData()
        Table(
            "old_table",
            current_metadata,
            Column("id", Integer, primary_key=True),
        )

        # Target is empty
        target_metadata = MetaData()

        manager = MigrationManager(tmp_path)
        changes = manager.detect_schema_changes(
            target_metadata=target_metadata,
            current_metadata=current_metadata,
        )

        assert len(changes) == 1
        assert changes[0].change_type == SchemaChangeType.DROPPED_TABLE
        assert changes[0].table_name == "old_table"

    def test_detect_dropped_column(self, tmp_path: Path) -> None:
        """detect_schema_changes() should detect dropped columns."""
        from sqlalchemy import Column, Integer, MetaData, String, Table

        from framework_m.adapters.db.migration import SchemaChangeType

        # Current has extra column
        current_metadata = MetaData()
        Table(
            "users",
            current_metadata,
            Column("id", Integer, primary_key=True),
            Column("old_column", String(100)),
        )

        # Target without that column
        target_metadata = MetaData()
        Table(
            "users",
            target_metadata,
            Column("id", Integer, primary_key=True),
        )

        manager = MigrationManager(tmp_path)
        changes = manager.detect_schema_changes(
            target_metadata=target_metadata,
            current_metadata=current_metadata,
        )

        assert len(changes) == 1
        assert changes[0].change_type == SchemaChangeType.DROPPED_COLUMN
        assert changes[0].column_name == "old_column"

    def test_detect_type_change(self, tmp_path: Path) -> None:
        """detect_schema_changes() should detect column type changes."""
        from sqlalchemy import Column, Integer, MetaData, String, Table, Text

        from framework_m.adapters.db.migration import SchemaChangeType

        # Current has VARCHAR
        current_metadata = MetaData()
        Table(
            "users",
            current_metadata,
            Column("id", Integer, primary_key=True),
            Column("bio", String(255)),
        )

        # Target has TEXT
        target_metadata = MetaData()
        Table(
            "users",
            target_metadata,
            Column("id", Integer, primary_key=True),
            Column("bio", Text),
        )

        manager = MigrationManager(tmp_path)
        changes = manager.detect_schema_changes(
            target_metadata=target_metadata,
            current_metadata=current_metadata,
        )

        assert len(changes) == 1
        assert changes[0].change_type == SchemaChangeType.TYPE_CHANGE
        assert changes[0].column_name == "bio"

    def test_detect_with_none_current_metadata(self, tmp_path: Path) -> None:
        """detect_schema_changes() should handle None current_metadata."""
        from sqlalchemy import Column, Integer, MetaData, Table

        from framework_m.adapters.db.migration import SchemaChangeType

        target_metadata = MetaData()
        Table(
            "new_table",
            target_metadata,
            Column("id", Integer, primary_key=True),
        )

        manager = MigrationManager(tmp_path)
        changes = manager.detect_schema_changes(
            target_metadata=target_metadata,
            current_metadata=None,
        )

        assert len(changes) == 1
        assert changes[0].change_type == SchemaChangeType.NEW_TABLE


# =============================================================================
# Test: Auto-Migrate - Dev Mode
# =============================================================================


class TestAutoMigrateDevMode:
    """Tests for auto_migrate() dev mode functionality."""

    def test_auto_migrate_dev_mode_creates_table(self, tmp_path: Path) -> None:
        """auto_migrate(dev_mode=True) should create new tables directly."""
        from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine

        db_path = tmp_path / "test.db"
        engine = create_engine(f"sqlite:///{db_path}")

        target_metadata = MetaData()
        Table(
            "items",
            target_metadata,
            Column("id", Integer, primary_key=True),
            Column("name", String(100)),
        )

        manager = MigrationManager(tmp_path, database_url=f"sqlite:///{db_path}")
        manager.init()

        changes = manager.auto_migrate(
            target_metadata=target_metadata,
            dev_mode=True,
            engine=engine,
        )

        # Should have detected and applied the change
        assert len(changes) >= 1

        # Verify table was created
        from sqlalchemy import inspect

        inspector = inspect(engine)
        assert "items" in inspector.get_table_names()

    def test_auto_migrate_dev_mode_adds_column(self, tmp_path: Path) -> None:
        """auto_migrate(dev_mode=True) should add new columns directly."""
        from sqlalchemy import (
            Column,
            Integer,
            MetaData,
            String,
            Table,
            create_engine,
            inspect,
        )

        db_path = tmp_path / "test.db"
        engine = create_engine(f"sqlite:///{db_path}")

        # Create initial table
        initial_metadata = MetaData()
        Table(
            "items",
            initial_metadata,
            Column("id", Integer, primary_key=True),
        )
        initial_metadata.create_all(engine)

        # Target with new column
        target_metadata = MetaData()
        Table(
            "items",
            target_metadata,
            Column("id", Integer, primary_key=True),
            Column("description", String(255)),
        )

        manager = MigrationManager(tmp_path, database_url=f"sqlite:///{db_path}")
        manager.init()

        changes = manager.auto_migrate(
            target_metadata=target_metadata,
            dev_mode=True,
            engine=engine,
        )

        # Should have detected the new column
        assert len(changes) >= 1

        # Verify column was added
        inspector = inspect(engine)
        columns = [c["name"] for c in inspector.get_columns("items")]
        assert "description" in columns


# =============================================================================
# Test: SchemaChange details field
# =============================================================================


class TestSchemaChangeDetails:
    """Tests for SchemaChange details field."""

    def test_schema_change_with_details(self) -> None:
        """SchemaChange should support details field."""
        from framework_m.adapters.db.migration import SchemaChange, SchemaChangeType

        change = SchemaChange(
            change_type=SchemaChangeType.TYPE_CHANGE,
            table_name="users",
            column_name="age",
            old_type="VARCHAR(10)",
            new_type="INTEGER",
            details={"reason": "schema update"},
        )

        assert change.old_type == "VARCHAR(10)"
        assert change.new_type == "INTEGER"
        assert change.details["reason"] == "schema update"
