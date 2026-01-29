"""Integration tests for migration flow.

Tests the complete migration cycle:
1. Create DocType with initial schema
2. Add a new field to DocType
3. Run auto-migration
4. Verify the new column exists in database
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import MetaData, create_engine, inspect, text

from framework_m import DocType, Field
from framework_m.adapters.db.migration import MigrationManager
from framework_m.adapters.db.schema_mapper import SchemaMapper
from framework_m.adapters.db.table_registry import TableRegistry
from framework_m.core.registry import MetaRegistry

# =============================================================================
# Test: Migration Flow
# =============================================================================


class TestMigrationFlow:
    """Integration tests for migration (add field, auto-migrate, verify column)."""

    @pytest.fixture(autouse=True)
    def reset_singletons(self) -> None:
        """Reset singletons before each test."""
        TableRegistry().reset()
        MetaRegistry().clear()
        yield
        TableRegistry().reset()
        MetaRegistry().clear()

    @pytest.fixture
    def temp_db_path(self, tmp_path: Path) -> Path:
        """Create a temporary database file."""
        return tmp_path / "test_migration.db"

    @pytest.fixture
    def migration_dir(self, tmp_path: Path) -> Path:
        """Create a temporary migration directory."""
        return tmp_path / "migrations"

    @pytest.fixture
    def sync_db_url(self, temp_db_path: Path) -> str:
        """Get sync database URL."""
        return f"sqlite:///{temp_db_path}"

    def test_add_field_and_verify_column(
        self, sync_db_url: str, migration_dir: Path
    ) -> None:
        """Test: Add field to DocType, run auto-migrate, verify column exists."""
        sync_engine = create_engine(sync_db_url)
        schema_mapper = SchemaMapper()

        # Step 1: Define initial DocType (V1) and create table
        class MigrationDoc(DocType):
            """Test DocType for migration."""

            title: str = Field(description="Title")

        metadata_v1 = MetaData()
        schema_mapper.create_tables(MigrationDoc, metadata_v1)
        metadata_v1.create_all(sync_engine)

        # Verify initial schema
        inspector = inspect(sync_engine)
        columns_v1 = {col["name"] for col in inspector.get_columns("migrationdoc")}
        assert "title" in columns_v1
        assert "description" not in columns_v1

        # Step 2: Create V2 metadata with new field
        # Note: We create a NEW metadata and add the column manually to simulate
        # what would happen if the DocType definition changed
        TableRegistry().reset()

        # Re-create table definition with new column
        class MigrationDocV2(DocType):
            """Test DocType for migration - V2 with new field."""

            __tablename__ = "migrationdoc"  # Use same table name as V1

            title: str = Field(description="Title")
            description: str | None = Field(default=None, description="Description")

        # Create target metadata using V2 definition with __tablename__
        metadata_target = MetaData()
        schema_mapper.create_tables(MigrationDocV2, metadata_target)

        # Step 3: Run auto-migration
        manager = MigrationManager(base_path=migration_dir, database_url=sync_db_url)
        if not (migration_dir / "alembic.ini").exists():
            manager.init()

        changes = manager.auto_migrate(
            target_metadata=metadata_target, dev_mode=True, engine=sync_engine
        )

        # Verify changes were detected
        assert len(changes) > 0, "Should detect schema changes"
        new_column_changes = [c for c in changes if c.column_name == "description"]
        assert len(new_column_changes) == 1, "Should detect new 'description' column"

        # Step 4: Verify new column exists in database
        inspector = inspect(sync_engine)
        columns_v2 = {col["name"] for col in inspector.get_columns("migrationdoc")}
        assert "description" in columns_v2, (
            "New column 'description' should exist after migration"
        )
        assert "title" in columns_v2, "Original column 'title' should still exist"

        sync_engine.dispose()

    def test_migration_preserves_existing_data(
        self, sync_db_url: str, migration_dir: Path
    ) -> None:
        """Test: Migration preserves existing data."""
        sync_engine = create_engine(sync_db_url)
        schema_mapper = SchemaMapper()

        # Step 1: Create initial table and insert data
        class DataDoc(DocType):
            """Test DocType for data preservation."""

            name_field: str = Field(description="Name")

        metadata_v1 = MetaData()
        schema_mapper.create_tables(DataDoc, metadata_v1)
        metadata_v1.create_all(sync_engine)

        # Insert test data with all required fields
        with sync_engine.connect() as conn:
            conn.execute(
                text(
                    "INSERT INTO datadoc "
                    "(id, name, name_field, creation, modified, owner) "
                    "VALUES ('test-uuid-1', 'DATA-001', 'Test Data', "
                    "datetime('now'), datetime('now'), 'test@test.com')"
                )
            )
            conn.commit()

        # Verify data was inserted
        with sync_engine.connect() as conn:
            result = conn.execute(
                text("SELECT name_field FROM datadoc WHERE name='DATA-001'")
            )
            row = result.fetchone()
            assert row is not None, "Data should be inserted"

        # Step 2: Create target metadata with new column using __tablename__
        TableRegistry().reset()

        class DataDocV2(DocType):
            """Test DocType V2 with new field."""

            __tablename__ = "datadoc"  # Use same table name as V1

            name_field: str = Field(description="Name")
            extra_field: str | None = Field(default=None, description="Extra")

        metadata_target = MetaData()
        schema_mapper.create_tables(DataDocV2, metadata_target)

        # Step 3: Run migration
        manager = MigrationManager(base_path=migration_dir, database_url=sync_db_url)
        if not (migration_dir / "alembic.ini").exists():
            manager.init()
        manager.auto_migrate(
            target_metadata=metadata_target, dev_mode=True, engine=sync_engine
        )

        # Step 4: Verify data preserved
        with sync_engine.connect() as conn:
            result = conn.execute(
                text("SELECT name_field FROM datadoc WHERE name='DATA-001'")
            )
            row = result.fetchone()
            assert row is not None, "Existing data should be preserved"
            assert row[0] == "Test Data", "Data value should be unchanged"

        sync_engine.dispose()


class TestMigrationImport:
    """Tests for module imports."""

    def test_import_migration_manager(self) -> None:
        """MigrationManager should be importable."""
        from framework_m.adapters.db.migration import MigrationManager

        assert MigrationManager is not None
