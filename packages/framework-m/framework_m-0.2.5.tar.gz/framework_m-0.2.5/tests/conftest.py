"""Pytest configuration and fixtures.

This module provides shared fixtures for testing Framework M:
- Mock implementations of all protocol interfaces
- Container fixtures for DI testing
- Sample data fixtures for DocType tests
- Database fixtures for integration testing
"""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

import pytest
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from framework_m import DocType, Field
from framework_m.core.container import Container
from framework_m.core.domain.base_controller import BaseController
from framework_m.core.registry import MetaRegistry

# =============================================================================
# Sample DocTypes for Testing
# =============================================================================


class TestTodo(DocType):
    """Sample Todo DocType for testing."""

    title: str = Field(description="Task title")
    is_completed: bool = False
    priority: int = 1


class TestTodoController(BaseController[TestTodo]):
    """Sample controller for TestTodo."""

    async def validate(self, context: Any = None) -> None:
        """Validate todo has non-empty title."""
        if not self.doc.title.strip():
            raise ValueError("Title cannot be empty")


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_doctype_data() -> dict[str, Any]:
    """Sample data for DocType tests."""
    return {
        "name": "test-doc-001",
        "owner": "test@example.com",
        "modified_by": "test@example.com",
    }


@pytest.fixture
def sample_todo() -> TestTodo:
    """Create a sample TestTodo instance."""
    return TestTodo(
        title="Test Task",
        is_completed=False,
        priority=1,
        name="TODO-001",
        owner="test@example.com",
    )


@pytest.fixture
def sample_todo_controller(sample_todo: TestTodo) -> TestTodoController:
    """Create a sample TestTodoController instance."""
    return TestTodoController(sample_todo)


@pytest.fixture
def container() -> Container:
    """Create a fresh Container instance for testing."""
    return Container()


@pytest.fixture
def configured_container() -> Container:
    """Create a Container with test configuration."""
    container = Container()
    container.config.from_dict(
        {
            "database_url": "sqlite:///:memory:",
            "debug": True,
            "app_name": "TestApp",
        }
    )
    return container


@pytest.fixture
def clean_registry() -> MetaRegistry:
    """Get a clean MetaRegistry instance for testing."""
    registry = MetaRegistry()
    registry.clear()
    return registry


@pytest.fixture
def registry_with_todo(clean_registry: MetaRegistry) -> MetaRegistry:
    """Registry with TestTodo registered."""
    clean_registry.register_doctype(TestTodo, TestTodoController)
    return clean_registry


# =============================================================================
# Async Fixtures
# =============================================================================


@pytest.fixture
async def async_sample_data() -> AsyncGenerator[dict[str, Any], None]:
    """Async fixture providing sample data."""
    yield {
        "created_at": datetime.now(UTC),
        "test_id": "async-test-001",
    }


# =============================================================================
# Mock Protocol Implementations (for future integration tests)
# =============================================================================

# Note: Mock implementations of protocols (Repository, EventBus, Cache, etc.)
# will be added here as needed for integration testing.
# For now, unit tests use protocol-level testing without mocks.


# =============================================================================
# Database Fixtures (for integration testing)
# =============================================================================


@pytest.fixture(scope="session")
def database_url() -> str:
    """Database URL for testing.

    Returns the connection URL from environment or defaults to SQLite for fast tests.
    SQLite is used by default per Architecture 4.2 (Database Agnosticism).
    Set TEST_DATABASE_URL to use PostgreSQL or other databases.

    Examples:
        # Fast tests with SQLite (default)
        pytest tests/

        # Production validation with PostgreSQL
        TEST_DATABASE_URL=postgresql+asyncpg://... pytest tests/
    """
    import os

    # Default to SQLite for fast tests (Architecture 4.2: Database Agnosticism)
    # Use PostgreSQL or other DB by setting TEST_DATABASE_URL env var
    return os.getenv(
        "TEST_DATABASE_URL",
        "sqlite+aiosqlite:///:memory:",
    )


@pytest.fixture
async def test_engine(database_url: str) -> AsyncGenerator[AsyncEngine, None]:
    """Create a test database engine.

    For SQLite, enables foreign key constraint enforcement.
    """
    engine = create_async_engine(database_url, echo=False, pool_pre_ping=True)

    # Enable foreign key constraints for SQLite only
    if "sqlite" in database_url:
        from sqlalchemy import event

        @event.listens_for(engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session with automatic rollback."""
    # Create session maker
    async_session_maker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session, session.begin():
        yield session
        # Rollback automatically after test
        await session.rollback()


@pytest.fixture
async def clean_tables(
    test_engine: AsyncEngine,
) -> AsyncGenerator[MetaData, None]:
    """Create a clean metadata and drop all tables after test."""
    # Reset table registry before each test
    from framework_m.adapters.db.table_registry import TableRegistry

    table_registry = TableRegistry()
    table_registry.reset()

    metadata = MetaData()
    yield metadata

    # Drop all tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
