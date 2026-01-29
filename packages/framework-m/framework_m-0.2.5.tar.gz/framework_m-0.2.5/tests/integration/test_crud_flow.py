"""Integration tests for full CRUD flow with SQLite.

Tests the complete flow from DocType registration through database operations.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy import MetaData

from framework_m import DocType, Field
from framework_m.adapters.db import (
    ConnectionFactory,
    RepositoryFactory,
    SessionFactory,
    TableRegistry,
    initialize_database,
)
from framework_m.adapters.db.schema_mapper import SchemaMapper
from framework_m.core.registry import MetaRegistry

# =============================================================================
# Test DocType
# =============================================================================


class IntegrationTestDoc(DocType):
    """Test DocType for integration tests."""

    title: str = Field(description="Document title")
    count: int = Field(default=0)
    is_active: bool = Field(default=True)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
async def setup_database() -> AsyncGenerator[RepositoryFactory, None]:
    """Setup database with test DocType and cleanup after.

    Yields:
        RepositoryFactory configured with test metadata and session factory.
    """
    # Reset singletons
    ConnectionFactory().reset()
    SessionFactory().reset()
    TableRegistry().reset()
    MetaRegistry().clear()

    # Register DocType
    MetaRegistry().register_doctype(IntegrationTestDoc)

    # Initialize database
    await initialize_database(
        db_binds={"default": "sqlite+aiosqlite:///:memory:"},
    )

    # Create metadata and map schema
    metadata = MetaData()
    schema_mapper = SchemaMapper()
    schema_mapper.create_table(IntegrationTestDoc, metadata)

    # Create tables
    engine = ConnectionFactory().get_engine("default")
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)

    # Get session factory
    session_factory = SessionFactory()

    # Create and return repository factory
    repo_factory = RepositoryFactory(metadata, session_factory)

    yield repo_factory

    # Cleanup
    for bind_name in ConnectionFactory().list_engines():
        engine = ConnectionFactory().get_engine(bind_name)
        await engine.dispose()

    ConnectionFactory().reset()
    SessionFactory().reset()


# =============================================================================
# Tests: Full CRUD Flow
# =============================================================================


class TestCRUDFlowSQLite:
    """Integration tests for CRUD flow using SQLite."""

    @pytest.mark.asyncio
    async def test_register_doctype(self, setup_database: RepositoryFactory) -> None:
        """DocType should be registered in MetaRegistry."""
        registry = MetaRegistry()
        assert "IntegrationTestDoc" in registry.list_doctypes()

    @pytest.mark.asyncio
    async def test_table_created(self, setup_database: RepositoryFactory) -> None:
        """Table should be created in TableRegistry."""
        table_registry = TableRegistry()
        assert table_registry.table_exists("IntegrationTestDoc")

    @pytest.mark.asyncio
    async def test_insert_document(self, setup_database: RepositoryFactory) -> None:
        """Should be able to insert a document."""
        repo = setup_database.get_repository(IntegrationTestDoc)
        assert repo is not None, "Repository should be created"

        async with setup_database.session_factory.get_session() as session:
            doc = IntegrationTestDoc(title="Test Document", count=5, is_active=True)
            saved_doc = await repo.save(session, doc)

            assert saved_doc.name is not None
            assert saved_doc.title == "Test Document"
            assert saved_doc.count == 5
            assert saved_doc.is_active is True

    @pytest.mark.asyncio
    async def test_query_document(self, setup_database: RepositoryFactory) -> None:
        """Should be able to query a document by ID."""
        repo = setup_database.get_repository(IntegrationTestDoc)
        assert repo is not None

        async with setup_database.session_factory.get_session() as session:
            # Insert
            doc = IntegrationTestDoc(title="Query Test")
            saved_doc = await repo.save(session, doc)
            doc_id = saved_doc.id

        # Query in new session
        async with setup_database.session_factory.get_session() as session:
            found_doc = await repo.get(session, doc_id)

            assert found_doc is not None
            assert found_doc.title == "Query Test"

    @pytest.mark.asyncio
    async def test_update_document(self, setup_database: RepositoryFactory) -> None:
        """Should be able to update a document."""
        repo = setup_database.get_repository(IntegrationTestDoc)
        assert repo is not None

        async with setup_database.session_factory.get_session() as session:
            # Insert
            doc = IntegrationTestDoc(title="Original Title", count=0)
            saved_doc = await repo.save(session, doc)
            doc_id = saved_doc.id

        # Update in new session
        async with setup_database.session_factory.get_session() as session:
            fetched_doc = await repo.get(session, doc_id)
            assert fetched_doc is not None

            fetched_doc.title = "Updated Title"
            fetched_doc.count = 10
            await repo.save(session, fetched_doc)

        # Verify update
        async with setup_database.session_factory.get_session() as session:
            final_doc = await repo.get(session, doc_id)

            assert final_doc is not None
            assert final_doc.title == "Updated Title"
            assert final_doc.count == 10

    @pytest.mark.asyncio
    async def test_delete_document(self, setup_database: RepositoryFactory) -> None:
        """Should be able to delete a document."""
        repo = setup_database.get_repository(IntegrationTestDoc)
        assert repo is not None

        async with setup_database.session_factory.get_session() as session:
            # Insert
            doc = IntegrationTestDoc(title="To Delete")
            saved_doc = await repo.save(session, doc)
            doc_id = saved_doc.id

        # Delete
        async with setup_database.session_factory.get_session() as session:
            await repo.delete(session, doc_id)

        # Verify deleted (soft delete - should not be found)
        async with setup_database.session_factory.get_session() as session:
            found_doc = await repo.get(session, doc_id)
            assert found_doc is None

    @pytest.mark.asyncio
    async def test_exists_operation(self, setup_database: RepositoryFactory) -> None:
        """Should check if document exists."""
        repo = setup_database.get_repository(IntegrationTestDoc)
        assert repo is not None

        async with setup_database.session_factory.get_session() as session:
            # Insert
            doc = IntegrationTestDoc(title="Exists Test")
            saved_doc = await repo.save(session, doc)
            doc_id = saved_doc.id

            # Check exists
            exists = await repo.exists(session, doc_id)
            assert exists is True

        # Delete and check again
        async with setup_database.session_factory.get_session() as session:
            await repo.delete(session, doc_id)

        async with setup_database.session_factory.get_session() as session:
            exists_after_delete = await repo.exists(session, doc_id)
            assert exists_after_delete is False

    @pytest.mark.asyncio
    async def test_count_operation(self, setup_database: RepositoryFactory) -> None:
        """Should count documents."""
        repo = setup_database.get_repository(IntegrationTestDoc)
        assert repo is not None

        async with setup_database.session_factory.get_session() as session:
            # Start with 0
            initial_count = await repo.count(session)
            assert initial_count == 0

            # Insert 3 documents
            for i in range(3):
                await repo.save(session, IntegrationTestDoc(title=f"Doc {i}"))

            # Count should be 3
            count = await repo.count(session)
            assert count == 3
