"""Tests for Bulk Operations with RLS.

TDD tests for bulk operations that MUST apply RLS:
- delete_many(filters) applies RLS so users only delete their own docs
- update_many(filters, data) applies RLS so users only update their own docs
- User can only bulk-modify docs they have access to

Per CONTRIBUTING.md: Write failing tests FIRST, then implement.
"""

from typing import ClassVar

import pytest
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from framework_m.adapters.db.generic_repository import GenericRepository
from framework_m.adapters.db.schema_mapper import SchemaMapper
from framework_m.core.domain.base_doctype import BaseDocType, Field
from framework_m.core.interfaces.auth_context import UserContext
from framework_m.core.interfaces.repository import FilterOperator, FilterSpec
from framework_m.core.registry import MetaRegistry

# =============================================================================
# Test DocTypes
# =============================================================================


class Task(BaseDocType):
    """Task DocType for testing bulk operations."""

    title: str = Field(description="Task title")
    status: str = Field(default="pending")

    class Meta:
        api_resource: ClassVar[bool] = True
        apply_rls: ClassVar[bool] = True
        permissions: ClassVar[dict[str, list[str]]] = {
            "read": ["Employee", "Manager", "Admin"],
            "write": ["Employee", "Manager", "Admin"],
            "delete": ["Manager", "Admin"],
        }


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def registry() -> MetaRegistry:
    """Get clean registry with test DocTypes."""
    reg = MetaRegistry.get_instance()
    reg.clear()
    reg.register_doctype(Task)
    yield reg
    reg.clear()


@pytest.fixture
async def engine():
    """Create in-memory SQLite engine."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session(engine, registry) -> AsyncSession:
    """Create session with table schema."""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    metadata = MetaData()
    mapper = SchemaMapper()
    tables = mapper.create_tables(Task, metadata)
    table = tables[0]

    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session, table


@pytest.fixture
def user_alice() -> UserContext:
    """User Alice with Employee role."""
    return UserContext(
        id="alice",
        email="alice@example.com",
        roles=["Employee"],
    )


@pytest.fixture
def user_bob() -> UserContext:
    """User Bob with Employee role."""
    return UserContext(
        id="bob",
        email="bob@example.com",
        roles=["Employee"],
    )


@pytest.fixture
def admin_user() -> UserContext:
    """Admin user who can see all."""
    return UserContext(
        id="admin",
        email="admin@example.com",
        roles=["Admin"],
    )


# =============================================================================
# Tests: delete_many with RLS
# =============================================================================


class TestDeleteManyWithRLS:
    """Test delete_many applies RLS filters."""

    @pytest.mark.asyncio
    async def test_delete_many_only_deletes_own_docs(
        self, session, user_alice, user_bob
    ) -> None:
        """Users should only be able to delete their own docs."""
        sess, table = session
        repo = GenericRepository(Task, table)

        # Create docs for both users
        alice_task = Task(title="Alice's Task", owner="alice")
        bob_task = Task(title="Bob's Task", owner="bob")

        await repo.save(sess, alice_task)
        await repo.save(sess, bob_task)
        await sess.commit()

        # Alice tries to delete all "pending" tasks
        # Should only delete HER pending tasks, not Bob's
        deleted_count = await repo.delete_many_for_user(
            sess,
            user=user_alice,
            filters=[
                FilterSpec(field="status", operator=FilterOperator.EQ, value="pending")
            ],
        )

        await sess.commit()

        # Alice should only have deleted her own task
        assert deleted_count == 1

        # Bob's task should still exist
        bob_tasks = await repo.list_entities(sess)
        assert bob_tasks.total == 1
        assert bob_tasks.items[0].owner == "bob"

    @pytest.mark.asyncio
    async def test_delete_many_admin_can_delete_all(
        self, session, admin_user, user_alice, user_bob
    ) -> None:
        """Admin users can delete all matching docs (no RLS)."""
        sess, table = session
        repo = GenericRepository(Task, table)

        # Create docs for both users
        alice_task = Task(title="Alice's Task", owner="alice")
        bob_task = Task(title="Bob's Task", owner="bob")

        await repo.save(sess, alice_task)
        await repo.save(sess, bob_task)
        await sess.commit()

        # Admin deletes all pending tasks
        deleted_count = await repo.delete_many_for_user(
            sess,
            user=admin_user,
            filters=[
                FilterSpec(field="status", operator=FilterOperator.EQ, value="pending")
            ],
        )

        await sess.commit()

        # Admin should have deleted all tasks
        assert deleted_count == 2


# =============================================================================
# Tests: update_many with RLS
# =============================================================================


class TestUpdateManyWithRLS:
    """Test update_many applies RLS filters."""

    @pytest.mark.asyncio
    async def test_update_many_only_updates_own_docs(
        self, session, user_alice, user_bob
    ) -> None:
        """Users should only be able to update their own docs."""
        sess, table = session
        repo = GenericRepository(Task, table)

        # Create docs for both users
        alice_task = Task(title="Alice's Task", owner="alice")
        bob_task = Task(title="Bob's Task", owner="bob")

        await repo.save(sess, alice_task)
        await repo.save(sess, bob_task)
        await sess.commit()

        # Alice tries to update all tasks to "completed"
        # Should only update HER tasks, not Bob's
        updated_count = await repo.update_many_for_user(
            sess,
            user=user_alice,
            filters=[
                FilterSpec(field="status", operator=FilterOperator.EQ, value="pending")
            ],
            data={"status": "completed"},
        )

        await sess.commit()

        # Alice should only have updated her own task
        assert updated_count == 1

        # Check Bob's task is still pending
        all_tasks = await repo.list_entities(sess)
        bob_task = next(t for t in all_tasks.items if t.owner == "bob")
        alice_task = next(t for t in all_tasks.items if t.owner == "alice")

        assert bob_task.status == "pending"
        assert alice_task.status == "completed"

    @pytest.mark.asyncio
    async def test_update_many_admin_can_update_all(self, session, admin_user) -> None:
        """Admin users can update all matching docs (no RLS)."""
        sess, table = session
        repo = GenericRepository(Task, table)

        # Create docs for different users
        task1 = Task(title="Task 1", owner="alice")
        task2 = Task(title="Task 2", owner="bob")

        await repo.save(sess, task1)
        await repo.save(sess, task2)
        await sess.commit()

        # Admin updates all pending tasks
        updated_count = await repo.update_many_for_user(
            sess,
            user=admin_user,
            filters=[
                FilterSpec(field="status", operator=FilterOperator.EQ, value="pending")
            ],
            data={"status": "completed"},
        )

        await sess.commit()

        # Admin should have updated all tasks
        assert updated_count == 2

        # Verify all are completed
        all_tasks = await repo.list_entities(sess)
        for task in all_tasks.items:
            assert task.status == "completed"


# =============================================================================
# Tests: No access without RLS
# =============================================================================


class TestBulkOperationsUserContext:
    """Test bulk operations user context behavior."""

    @pytest.mark.asyncio
    async def test_delete_many_with_none_user_bypasses_rls(self, session) -> None:
        """delete_many_for_user with None user bypasses RLS (for public DocTypes).

        Design: Some DocTypes have requires_auth=False.
        For those, operations with user=None are allowed.
        """
        sess, table = session
        repo = GenericRepository(Task, table)

        # Create some tasks
        task = Task(title="Test Task", owner="alice")
        await repo.save(sess, task)
        await sess.commit()

        # With None user, RLS is bypassed (like public access)
        deleted_count = await repo.delete_many_for_user(
            sess,
            user=None,  # type: ignore[arg-type]
            filters=[],
            hard=True,
        )
        await sess.commit()

        # Should delete all (no RLS filter applied)
        assert deleted_count == 1

    @pytest.mark.asyncio
    async def test_update_many_with_none_user_bypasses_rls(self, session) -> None:
        """update_many_for_user with None user bypasses RLS (for public DocTypes).

        Design: For requires_auth=False DocTypes, no user context needed.
        """
        sess, table = session
        repo = GenericRepository(Task, table)

        # Create some tasks
        task = Task(title="Test Task", owner="alice")
        await repo.save(sess, task)
        await sess.commit()

        # With None user, RLS is bypassed
        updated_count = await repo.update_many_for_user(
            sess,
            user=None,  # type: ignore[arg-type]
            filters=[],
            data={"status": "completed"},
        )
        await sess.commit()

        # Should update all (no RLS filter applied)
        assert updated_count == 1
