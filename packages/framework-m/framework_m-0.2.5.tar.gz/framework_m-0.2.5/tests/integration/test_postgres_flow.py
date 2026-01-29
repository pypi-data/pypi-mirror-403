"""Integration tests for PostgreSQL using testcontainers.

These tests require Docker to be running and will be skipped if Docker is unavailable.

Run with: pytest libs/framework-m/tests/integration/test_postgres_flow.py -v
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import MetaData, text
from sqlalchemy.ext.asyncio import create_async_engine

from framework_m import DocType, Field
from framework_m.adapters.db import (
    ConnectionFactory,
    RepositoryFactory,
    SessionFactory,
    TableRegistry,
    initialize_database,
)
from framework_m.adapters.db.field_registry import FieldRegistry
from framework_m.adapters.db.schema_mapper import SchemaMapper
from framework_m.core.registry import MetaRegistry

if TYPE_CHECKING:
    from testcontainers.postgres import (
        PostgresContainer,  # type: ignore[import-untyped]
    )


# Check if Docker is available
def docker_available() -> bool:
    """Check if Docker is available for testcontainers."""
    try:
        import docker

        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False


# Skip all tests in this module if Docker is not available
pytestmark = pytest.mark.skipif(
    not docker_available(),
    reason="Docker not available - required for PostgreSQL testcontainers",
)


# =============================================================================
# Test DocType
# =============================================================================


class PostgresTestDoc(DocType):
    """Test DocType for PostgreSQL integration tests."""

    title: str = Field(description="Document title")
    count: int = Field(default=0)
    is_active: bool = Field(default=True)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(scope="module")
def postgres_container() -> PostgresContainer:
    """Start PostgreSQL container for testing."""
    from testcontainers.postgres import PostgresContainer

    container = PostgresContainer("postgres:15")
    container.start()
    yield container
    container.stop()


@pytest.fixture
async def setup_postgres(
    postgres_container: PostgresContainer,
) -> AsyncGenerator[RepositoryFactory, None]:
    """Setup database with test DocType on PostgreSQL.

    Yields:
        RepositoryFactory configured for PostgreSQL.
    """
    # Reset singletons
    ConnectionFactory().reset()
    SessionFactory().reset()
    TableRegistry().reset()
    MetaRegistry().clear()
    FieldRegistry().reset()

    # Build async PostgreSQL URL
    host = postgres_container.get_container_host_ip()
    port = postgres_container.get_exposed_port(5432)
    user = postgres_container.username
    password = postgres_container.password
    dbname = postgres_container.dbname

    db_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{dbname}"

    # Drop table to ensure fresh schema (container persists across tests)
    temp_engine = create_async_engine(db_url)
    async with temp_engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS postgrestestdoc"))
    await temp_engine.dispose()

    # Register DocType
    MetaRegistry().register_doctype(PostgresTestDoc)

    # Initialize database
    await initialize_database(
        db_binds={"default": db_url},
    )

    # Create metadata and map schema
    metadata = MetaData()
    schema_mapper = SchemaMapper()
    schema_mapper.create_table(PostgresTestDoc, metadata)

    # Create tables
    engine = ConnectionFactory().get_engine("default")
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)

    # Get session factory
    session_factory = SessionFactory()

    # Create and yield repository factory
    repo_factory = RepositoryFactory(metadata, session_factory)

    yield repo_factory

    # Cleanup
    for bind_name in ConnectionFactory().list_engines():
        engine = ConnectionFactory().get_engine(bind_name)
        await engine.dispose()

    ConnectionFactory().reset()
    SessionFactory().reset()


# =============================================================================
# Tests: PostgreSQL CRUD Flow
# =============================================================================


class TestCRUDFlowPostgres:
    """Integration tests for CRUD flow using PostgreSQL."""

    @pytest.mark.asyncio
    async def test_table_created_postgres(
        self, setup_postgres: RepositoryFactory
    ) -> None:
        """Table should be created in PostgreSQL."""
        table_registry = TableRegistry()
        assert table_registry.table_exists("PostgresTestDoc")

    @pytest.mark.asyncio
    async def test_insert_and_query_postgres(
        self, setup_postgres: RepositoryFactory
    ) -> None:
        """Should insert and query document in PostgreSQL."""
        repo = setup_postgres.get_repository(PostgresTestDoc)
        assert repo is not None

        async with setup_postgres.session_factory.get_session() as session:
            # Insert
            doc = PostgresTestDoc(title="Postgres Test", count=42, is_active=False)
            saved_doc = await repo.save(session, doc)
            doc_id = saved_doc.id

        # Query in new session
        async with setup_postgres.session_factory.get_session() as session:
            found_doc = await repo.get(session, doc_id)

            assert found_doc is not None
            assert found_doc.title == "Postgres Test"
            assert found_doc.count == 42
            assert found_doc.is_active is False

    @pytest.mark.asyncio
    async def test_update_postgres(self, setup_postgres: RepositoryFactory) -> None:
        """Should update document in PostgreSQL."""
        repo = setup_postgres.get_repository(PostgresTestDoc)
        assert repo is not None

        async with setup_postgres.session_factory.get_session() as session:
            # Insert
            doc = PostgresTestDoc(title="Update Test")
            saved_doc = await repo.save(session, doc)
            doc_id = saved_doc.id

        # Update in new session
        async with setup_postgres.session_factory.get_session() as session:
            fetched_doc = await repo.get(session, doc_id)
            assert fetched_doc is not None

            fetched_doc.title = "Updated in Postgres"
            fetched_doc.count = 100
            await repo.save(session, fetched_doc)

        # Verify
        async with setup_postgres.session_factory.get_session() as session:
            final_doc = await repo.get(session, doc_id)
            assert final_doc is not None
            assert final_doc.title == "Updated in Postgres"
            assert final_doc.count == 100

    @pytest.mark.asyncio
    async def test_delete_postgres(self, setup_postgres: RepositoryFactory) -> None:
        """Should delete document in PostgreSQL."""
        repo = setup_postgres.get_repository(PostgresTestDoc)
        assert repo is not None

        async with setup_postgres.session_factory.get_session() as session:
            # Insert
            doc = PostgresTestDoc(title="Delete Test")
            saved_doc = await repo.save(session, doc)
            doc_id = saved_doc.id

        # Delete
        async with setup_postgres.session_factory.get_session() as session:
            await repo.delete(session, doc_id)

        # Verify
        async with setup_postgres.session_factory.get_session() as session:
            found_doc = await repo.get(session, doc_id)
            assert found_doc is None
