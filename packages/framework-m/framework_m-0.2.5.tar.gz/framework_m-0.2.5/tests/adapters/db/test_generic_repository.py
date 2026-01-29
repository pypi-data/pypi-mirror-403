"""Tests for GenericRepository."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy import Boolean, Column, DateTime, MetaData, String, Table
from sqlalchemy.ext.asyncio import AsyncSession

from framework_m import DocType, Field
from framework_m.adapters.db.generic_repository import GenericRepository
from framework_m.core.domain.base_controller import BaseController
from framework_m.core.domain.base_doctype import BaseDocType
from framework_m.core.interfaces.repository import PaginatedResult

if TYPE_CHECKING:
    pass


# =============================================================================
# Test DocType and Controller
# =============================================================================


class Todo(DocType):
    """Test DocType for repository tests."""

    title: str = Field(description="Task title")
    is_completed: bool = False


class TodoController(BaseController[Todo]):
    """Controller for Todo to test lifecycle hooks."""

    async def validate(self, context: object = None) -> None:
        """Validate todo has non-empty title."""
        if not self.doc.title.strip():
            raise ValueError("Title cannot be empty")


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def metadata() -> MetaData:
    """Create SQLAlchemy metadata."""
    return MetaData()


@pytest.fixture
def todo_table(metadata: MetaData) -> Table:
    """Create Todo table for testing."""
    return Table(
        "tab_todo",
        metadata,
        Column("id", String, primary_key=True),
        Column("name", String, unique=True),
        Column("title", String),
        Column("is_completed", String),
        Column("owner", String),
        Column("modified_by", String),
        Column("deleted_at", String, nullable=True),
        Column("_version", String, nullable=True),
    )


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create a mock AsyncSession."""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def repository(todo_table: Table) -> GenericRepository[Todo]:
    """Create a GenericRepository for Todo."""
    return GenericRepository(
        model=Todo,
        table=todo_table,
        controller_class=None,
    )


@pytest.fixture
def repository_with_controller(todo_table: Table) -> GenericRepository[Todo]:
    """Create a GenericRepository with controller."""
    return GenericRepository(
        model=Todo,
        table=todo_table,
        controller_class=TodoController,
    )


# =============================================================================
# Test: Repository Creation
# =============================================================================


class TestGenericRepositoryCreation:
    """Tests for GenericRepository instantiation."""

    def test_create_repository(self, todo_table: Table) -> None:
        """Repository should be creatable with required dependencies."""
        repo = GenericRepository(
            model=Todo,
            table=todo_table,
        )
        assert repo is not None
        assert repo.model is Todo
        assert repo.table is todo_table

    def test_create_repository_with_controller(self, todo_table: Table) -> None:
        """Repository should accept optional controller class."""
        repo = GenericRepository(
            model=Todo,
            table=todo_table,
            controller_class=TodoController,
        )
        assert repo.controller_class is TodoController


# =============================================================================
# Test: Get Operation
# =============================================================================


class TestGetOperation:
    """Tests for get() operation."""

    @pytest.mark.asyncio
    async def test_get_existing_entity(
        self, repository: GenericRepository[Todo], mock_session: AsyncMock
    ) -> None:
        """get() should return entity when found."""
        doc_id = uuid4()
        mock_row = MagicMock()
        mock_row._mapping = {
            "id": str(doc_id),
            "name": "TODO-001",
            "title": "Test Task",
            "is_completed": "false",
            "owner": "user@example.com",
            "modified_by": "user@example.com",
            "deleted_at": None,
        }

        mock_result = MagicMock()
        mock_result.first.return_value = mock_row
        mock_session.execute.return_value = mock_result

        result = await repository.get(mock_session, doc_id)

        assert result is not None
        assert result.title == "Test Task"
        assert result.name == "TODO-001"

    @pytest.mark.asyncio
    async def test_get_nonexistent_entity(
        self, repository: GenericRepository[Todo], mock_session: AsyncMock
    ) -> None:
        """get() should return None when not found."""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repository.get(mock_session, uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_get_filters_deleted(
        self, repository: GenericRepository[Todo], mock_session: AsyncMock
    ) -> None:
        """get() should filter out soft-deleted entities by default."""
        doc_id = uuid4()
        # Soft-deleted row (deleted_at is set)
        mock_result = MagicMock()
        mock_result.first.return_value = None  # Filtered out by query
        mock_session.execute.return_value = mock_result

        result = await repository.get(mock_session, doc_id)

        assert result is None
        # Verify execute was called (query built correctly)
        mock_session.execute.assert_called_once()


# =============================================================================
# Test: Save Operation (Insert)
# =============================================================================


class TestSaveInsertOperation:
    """Tests for save() insert operation."""

    @pytest.mark.asyncio
    async def test_save_new_entity(
        self, repository: GenericRepository[Todo], mock_session: AsyncMock
    ) -> None:
        """save() should insert new entity."""
        todo = Todo(title="New Task", owner="user@example.com")

        # Mock for exists check
        mock_exists_result = MagicMock()
        mock_exists_result.scalar.return_value = False
        mock_session.execute.return_value = mock_exists_result

        result = await repository.save(mock_session, todo)

        assert result.title == "New Task"
        assert result.name is not None  # Auto-generated

    @pytest.mark.asyncio
    async def test_save_generates_name(
        self, repository: GenericRepository[Todo], mock_session: AsyncMock
    ) -> None:
        """save() should generate name if not provided."""
        todo = Todo(title="Unnamed Task")

        mock_exists_result = MagicMock()
        mock_exists_result.scalar.return_value = False
        mock_session.execute.return_value = mock_exists_result

        result = await repository.save(mock_session, todo)

        assert result.name is not None
        assert len(result.name) > 0


# =============================================================================
# Test: Save Operation (Update)
# =============================================================================


class TestSaveUpdateOperation:
    """Tests for save() update operation."""

    @pytest.mark.asyncio
    async def test_save_existing_entity(
        self, repository: GenericRepository[Todo], mock_session: AsyncMock
    ) -> None:
        """save() should update existing entity."""
        todo = Todo(title="Updated Task", name="TODO-001")

        # First call: exists check returns True
        mock_exists_result = MagicMock()
        mock_exists_result.scalar.return_value = True
        mock_session.execute.return_value = mock_exists_result

        result = await repository.save(mock_session, todo)

        assert result.title == "Updated Task"


# =============================================================================
# Test: Delete Operation
# =============================================================================


class TestDeleteOperation:
    """Tests for delete() operation."""

    @pytest.mark.asyncio
    async def test_delete_entity(
        self, repository: GenericRepository[Todo], mock_session: AsyncMock
    ) -> None:
        """delete() should soft-delete entity."""
        from datetime import UTC, datetime

        doc_id = uuid4()

        # Mock for get() call (delete fetches entity for event emission)
        mock_row = MagicMock()
        mock_row._mapping = {
            "id": str(doc_id),
            "name": "TODO-001",
            "title": "Test Task",
            "is_completed": False,
            "owner": None,
            "modified": datetime.now(UTC),
            "modified_by": None,
            "deleted_at": None,
        }
        mock_get_result = MagicMock()
        mock_get_result.first.return_value = mock_row

        # Mock for update (soft delete)
        mock_update_result = MagicMock()
        mock_update_result.rowcount = 1

        mock_session.execute.side_effect = [mock_get_result, mock_update_result]

        await repository.delete(mock_session, doc_id)

        assert mock_session.execute.call_count == 2


# =============================================================================
# Test: Exists Operation
# =============================================================================


class TestExistsOperation:
    """Tests for exists() operation."""

    @pytest.mark.asyncio
    async def test_exists_returns_true(
        self, repository: GenericRepository[Todo], mock_session: AsyncMock
    ) -> None:
        """exists() should return True for existing entity."""
        doc_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar.return_value = True
        mock_session.execute.return_value = mock_result

        result = await repository.exists(mock_session, doc_id)

        assert result is True

    @pytest.mark.asyncio
    async def test_exists_returns_false(
        self, repository: GenericRepository[Todo], mock_session: AsyncMock
    ) -> None:
        """exists() should return False for non-existing entity."""
        doc_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar.return_value = False
        mock_session.execute.return_value = mock_result

        result = await repository.exists(mock_session, doc_id)

        assert result is False


# =============================================================================
# Test: Count Operation
# =============================================================================


class TestCountOperation:
    """Tests for count() operation."""

    @pytest.mark.asyncio
    async def test_count_all(
        self, repository: GenericRepository[Todo], mock_session: AsyncMock
    ) -> None:
        """count() should return total count."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 42
        mock_session.execute.return_value = mock_result

        result = await repository.count(mock_session)

        assert result == 42


# =============================================================================
# Test: Controller Lifecycle Hooks
# =============================================================================


class TestControllerHooks:
    """Tests for controller lifecycle hook integration."""

    @pytest.mark.asyncio
    async def test_save_calls_validate(
        self,
        repository_with_controller: GenericRepository[Todo],
        mock_session: AsyncMock,
    ) -> None:
        """save() should call controller.validate()."""
        todo = Todo(title="Valid Task")

        mock_exists_result = MagicMock()
        mock_exists_result.scalar.return_value = False
        mock_session.execute.return_value = mock_exists_result

        # This should not raise
        result = await repository_with_controller.save(mock_session, todo)
        assert result.title == "Valid Task"

    @pytest.mark.asyncio
    async def test_save_validation_fails(
        self,
        repository_with_controller: GenericRepository[Todo],
        mock_session: AsyncMock,
    ) -> None:
        """save() should raise on validation failure."""
        todo = Todo(title="   ")  # Empty after strip

        mock_exists_result = MagicMock()
        mock_exists_result.scalar.return_value = False
        mock_session.execute.return_value = mock_exists_result

        with pytest.raises(ValueError, match="Title cannot be empty"):
            await repository_with_controller.save(mock_session, todo)


# =============================================================================
# Test: Hard Delete
# =============================================================================


class TestHardDelete:
    """Tests for hard delete functionality."""

    @pytest.mark.asyncio
    async def test_hard_delete(
        self, repository: GenericRepository[Todo], mock_session: AsyncMock
    ) -> None:
        """delete(hard=True) should physically remove the row."""
        from datetime import UTC, datetime

        doc_id = uuid4()

        # Mock for get() call
        mock_row = MagicMock()
        mock_row._mapping = {
            "id": str(doc_id),
            "name": "TODO-001",
            "title": "Test Task",
            "is_completed": False,
            "owner": None,
            "modified": datetime.now(UTC),
            "modified_by": None,
            "deleted_at": None,
        }
        mock_get_result = MagicMock()
        mock_get_result.first.return_value = mock_row

        # Mock for delete
        mock_delete_result = MagicMock()
        mock_delete_result.rowcount = 1

        mock_session.execute.side_effect = [mock_get_result, mock_delete_result]

        await repository.delete(mock_session, doc_id, hard=True)

        assert mock_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_soft_delete_default(
        self, repository: GenericRepository[Todo], mock_session: AsyncMock
    ) -> None:
        """delete() should soft-delete by default (hard=False)."""
        from datetime import UTC, datetime

        doc_id = uuid4()

        # Mock for get() call
        mock_row = MagicMock()
        mock_row._mapping = {
            "id": str(doc_id),
            "name": "TODO-001",
            "title": "Test Task",
            "is_completed": False,
            "owner": None,
            "modified": datetime.now(UTC),
            "modified_by": None,
            "deleted_at": None,
        }
        mock_get_result = MagicMock()
        mock_get_result.first.return_value = mock_row

        # Mock for update (soft delete)
        mock_update_result = MagicMock()
        mock_update_result.rowcount = 1

        mock_session.execute.side_effect = [mock_get_result, mock_update_result]

        await repository.delete(mock_session, doc_id)  # Default is soft

        assert mock_session.execute.call_count == 2


# =============================================================================
# Test: Get By Name
# =============================================================================


class TestGetByName:
    """Tests for get_by_name() operation."""

    @pytest.mark.asyncio
    async def test_get_by_name_found(
        self, repository: GenericRepository[Todo], mock_session: AsyncMock
    ) -> None:
        """get_by_name() should return entity when found."""
        mock_row = MagicMock()
        mock_row._mapping = {
            "id": str(uuid4()),
            "name": "TODO-001",
            "title": "Test Task",
            "is_completed": "false",
            "owner": "user@example.com",
            "modified_by": "user@example.com",
            "deleted_at": None,
        }

        mock_result = MagicMock()
        mock_result.first.return_value = mock_row
        mock_session.execute.return_value = mock_result

        result = await repository.get_by_name(mock_session, "TODO-001")

        assert result is not None
        assert result.name == "TODO-001"

    @pytest.mark.asyncio
    async def test_get_by_name_not_found(
        self, repository: GenericRepository[Todo], mock_session: AsyncMock
    ) -> None:
        """get_by_name() should return None when not found."""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repository.get_by_name(mock_session, "NONEXISTENT")

        assert result is None


# =============================================================================
# Test: OCC (Optimistic Concurrency Control)
# =============================================================================


class TestOCC:
    """Tests for Optimistic Concurrency Control."""

    @pytest.mark.asyncio
    async def test_version_conflict_raises_error(
        self, repository: GenericRepository[Todo], mock_session: AsyncMock
    ) -> None:
        """save() with wrong version should raise VersionConflictError."""
        from framework_m.adapters.db.generic_repository import VersionConflictError

        todo = Todo(title="Task", name="TODO-001")

        # Entity exists
        mock_exists_result = MagicMock()
        mock_exists_result.scalar.return_value = True

        # Update returns 0 rows (version mismatch)
        mock_update_result = MagicMock()
        mock_update_result.rowcount = 0

        mock_session.execute.side_effect = [mock_exists_result, mock_update_result]

        with pytest.raises(VersionConflictError):
            await repository.save(mock_session, todo, version=1)

    @pytest.mark.asyncio
    async def test_save_with_version_success(
        self, repository: GenericRepository[Todo], mock_session: AsyncMock
    ) -> None:
        """save() with correct version should succeed."""
        todo = Todo(title="Task", name="TODO-001")

        # Entity exists
        mock_exists_result = MagicMock()
        mock_exists_result.scalar.return_value = True

        # Update returns 1 row (version matches)
        mock_update_result = MagicMock()
        mock_update_result.rowcount = 1

        mock_session.execute.side_effect = [mock_exists_result, mock_update_result]

        result = await repository.save(mock_session, todo, version=1)
        assert result.title == "Task"


# =============================================================================
# Test: Delete Lifecycle Hooks
# =============================================================================


class TodoControllerWithDeleteHooks(BaseController[Todo]):
    """Controller with delete hooks for testing."""

    delete_hooks_called: ClassVar[list[str]] = []

    async def before_delete(self, context: object = None) -> None:
        """Called before delete."""
        self.delete_hooks_called.append("before_delete")

    async def after_delete(self, context: object = None) -> None:
        """Called after delete."""
        self.delete_hooks_called.append("after_delete")


class TestDeleteHooks:
    """Tests for delete lifecycle hooks."""

    @pytest.fixture
    def repository_with_delete_hooks(
        self, todo_table: Table
    ) -> GenericRepository[Todo]:
        """Create repository with delete hooks controller."""
        return GenericRepository(
            model=Todo,
            table=todo_table,
            controller_class=TodoControllerWithDeleteHooks,
        )

    @pytest.mark.asyncio
    async def test_delete_calls_lifecycle_hooks(
        self,
        repository_with_delete_hooks: GenericRepository[Todo],
        mock_session: AsyncMock,
    ) -> None:
        """delete() should call before_delete and after_delete hooks."""
        doc_id = uuid4()
        TodoControllerWithDeleteHooks.delete_hooks_called = []

        # Mock get to return entity
        mock_row = MagicMock()
        mock_row._mapping = {
            "name": "TODO-001",
            "title": "Test",
            "is_completed": "false",
        }
        mock_get_result = MagicMock()
        mock_get_result.first.return_value = mock_row

        mock_update_result = MagicMock()
        mock_update_result.rowcount = 1

        mock_session.execute.side_effect = [mock_get_result, mock_update_result]

        await repository_with_delete_hooks.delete(mock_session, doc_id)

        assert "before_delete" in TodoControllerWithDeleteHooks.delete_hooks_called
        assert "after_delete" in TodoControllerWithDeleteHooks.delete_hooks_called


# =============================================================================
# Test: _call_hook Helper Method
# =============================================================================


class TodoControllerWithAllHooks(BaseController[Todo]):
    """Controller with all lifecycle hooks for comprehensive testing."""

    hooks_called: ClassVar[list[str]] = []

    async def validate(self, context: object = None) -> None:
        """Validate hook."""
        self.hooks_called.append("validate")

    async def before_insert(self, context: object = None) -> None:
        """Before insert hook."""
        self.hooks_called.append("before_insert")

    async def after_insert(self, context: object = None) -> None:
        """After insert hook."""
        self.hooks_called.append("after_insert")

    async def before_save(self, context: object = None) -> None:
        """Before save hook."""
        self.hooks_called.append("before_save")

    async def after_save(self, context: object = None) -> None:
        """After save hook."""
        self.hooks_called.append("after_save")

    async def before_delete(self, context: object = None) -> None:
        """Before delete hook."""
        self.hooks_called.append("before_delete")

    async def after_delete(self, context: object = None) -> None:
        """After delete hook."""
        self.hooks_called.append("after_delete")


class TodoControllerWithError(BaseController[Todo]):
    """Controller that raises error in hook."""

    async def before_save(self, context: object = None) -> None:
        """Hook that raises error."""
        raise RuntimeError("Hook error")


class TestCallHookHelper:
    """Tests for _call_hook helper method."""

    @pytest.fixture
    def repository_all_hooks(self, todo_table: Table) -> GenericRepository[Todo]:
        """Create repository with all hooks controller."""
        return GenericRepository(
            model=Todo,
            table=todo_table,
            controller_class=TodoControllerWithAllHooks,
        )

    @pytest.fixture
    def repository_with_error_hooks(self, todo_table: Table) -> GenericRepository[Todo]:
        """Create repository with error-throwing controller."""
        return GenericRepository(
            model=Todo,
            table=todo_table,
            controller_class=TodoControllerWithError,
        )

    @pytest.mark.asyncio
    async def test_insert_calls_all_hooks_in_order(
        self, repository_all_hooks: GenericRepository[Todo], mock_session: AsyncMock
    ) -> None:
        """Insert should call validate, before_insert, before_save, after_save, after_insert."""
        TodoControllerWithAllHooks.hooks_called = []
        todo = Todo(title="Test Task")

        mock_exists_result = MagicMock()
        mock_exists_result.scalar.return_value = False
        mock_session.execute.return_value = mock_exists_result

        await repository_all_hooks.save(mock_session, todo)

        expected_order = [
            "validate",
            "before_insert",
            "before_save",
            "after_save",
            "after_insert",
        ]
        assert TodoControllerWithAllHooks.hooks_called == expected_order

    @pytest.mark.asyncio
    async def test_update_calls_hooks_in_order(
        self, repository_all_hooks: GenericRepository[Todo], mock_session: AsyncMock
    ) -> None:
        """Update should call validate, before_save, after_save."""
        TodoControllerWithAllHooks.hooks_called = []
        todo = Todo(title="Test Task", name="TODO-001")

        mock_exists_result = MagicMock()
        mock_exists_result.scalar.return_value = True

        mock_update_result = MagicMock()
        mock_update_result.rowcount = 1

        mock_session.execute.side_effect = [mock_exists_result, mock_update_result]

        await repository_all_hooks.save(mock_session, todo)

        expected_order = ["validate", "before_save", "after_save"]
        assert TodoControllerWithAllHooks.hooks_called == expected_order

    @pytest.mark.asyncio
    async def test_hook_error_propagates(
        self,
        repository_with_error_hooks: GenericRepository[Todo],
        mock_session: AsyncMock,
    ) -> None:
        """Hook exceptions should propagate to caller."""
        todo = Todo(title="Test Task", name="TODO-001")

        mock_exists_result = MagicMock()
        mock_exists_result.scalar.return_value = True
        mock_session.execute.return_value = mock_exists_result

        with pytest.raises(RuntimeError, match="Hook error"):
            await repository_with_error_hooks.save(mock_session, todo)

    @pytest.mark.asyncio
    async def test_missing_hook_is_ignored(
        self, repository: GenericRepository[Todo], mock_session: AsyncMock
    ) -> None:
        """Missing hooks (no controller) should be silently ignored."""
        todo = Todo(title="Test Task")

        mock_exists_result = MagicMock()
        mock_exists_result.scalar.return_value = False
        mock_session.execute.return_value = mock_exists_result

        # Should not raise even though no controller
        result = await repository.save(mock_session, todo)
        assert result.title == "Test Task"


# =============================================================================
# Test: Import
# =============================================================================


class TestGenericRepositoryImport:
    """Tests for GenericRepository imports."""

    def test_import_generic_repository(self) -> None:
        """GenericRepository should be importable."""
        from framework_m.adapters.db.generic_repository import GenericRepository

        assert GenericRepository is not None

    def test_import_version_conflict_error(self) -> None:
        """VersionConflictError should be importable."""
        from framework_m.adapters.db.generic_repository import VersionConflictError

        assert VersionConflictError is not None


# =============================================================================
# Test: Transaction Rollback on Error
# =============================================================================


class TestTransactionRollback:
    """Tests for transaction rollback on error."""

    @pytest.mark.asyncio
    async def test_save_rollback_on_database_error(
        self, mock_session: AsyncMock, todo_table: Table
    ) -> None:
        """save() should convert SQLAlchemy errors to domain exceptions."""
        from sqlalchemy.exc import IntegrityError

        from framework_m.core.exceptions import DuplicateNameError

        repository = GenericRepository(
            model=Todo,
            table=todo_table,
            controller_class=None,
        )

        todo = Todo(title="Test Task")

        # First call for exists check, second call for insert raises error
        mock_exists_result = MagicMock()
        mock_exists_result.scalar.return_value = False

        def side_effect(*args: object, **kwargs: object) -> MagicMock:
            # First call returns exists result, second raises IntegrityError
            if mock_session.execute.call_count == 1:
                return mock_exists_result
            raise IntegrityError("INSERT", {}, Exception("Duplicate key"))

        mock_session.execute.side_effect = side_effect

        # Should raise DuplicateNameError (converted from IntegrityError)
        with pytest.raises(DuplicateNameError):
            await repository.save(mock_session, todo)

    @pytest.mark.asyncio
    async def test_save_rollback_on_validation_error(
        self, mock_session: AsyncMock, todo_table: Table
    ) -> None:
        """save() should trigger rollback when validation fails."""

        class StrictController(BaseController[Todo]):
            """Controller that always fails validation."""

            def validate(self, context: Any = None) -> None:
                raise ValueError("Validation failed")

        repository = GenericRepository(
            model=Todo,
            table=todo_table,
            controller_class=StrictController,
        )

        todo = Todo(title="Test Task")

        # Setup mock for exists check (validation happens before DB ops)
        mock_exists_result = MagicMock()
        mock_exists_result.scalar.return_value = False
        mock_session.execute.return_value = mock_exists_result

        with pytest.raises(ValueError, match="Validation failed"):
            await repository.save(mock_session, todo)

    @pytest.mark.asyncio
    async def test_delete_rollback_on_database_error(
        self, mock_session: AsyncMock, todo_table: Table
    ) -> None:
        """delete() should trigger rollback when database error occurs."""
        from uuid import uuid4

        from sqlalchemy.exc import OperationalError

        repository = GenericRepository(
            model=Todo,
            table=todo_table,
            controller_class=None,
        )

        entity_id = uuid4()

        # Simulate database connection error
        mock_session.execute.side_effect = OperationalError(
            "UPDATE", {}, Exception("Connection lost")
        )

        with pytest.raises(OperationalError):
            await repository.delete(mock_session, entity_id)


# =============================================================================
# Test: Event Emission
# =============================================================================


class TestEventEmission:
    """Tests for event emission on CRUD operations."""

    @pytest.fixture
    def mock_event_bus(self) -> AsyncMock:
        """Create a mock event bus."""
        bus = AsyncMock()
        bus.publish = AsyncMock()
        return bus

    @pytest.fixture
    def repository_with_events(
        self, todo_table: Table, mock_event_bus: AsyncMock
    ) -> GenericRepository[Todo]:
        """Create a GenericRepository with event bus."""
        return GenericRepository(
            model=Todo,
            table=todo_table,
            controller_class=None,
            event_bus=mock_event_bus,
        )

    @pytest.mark.asyncio
    async def test_save_new_entity_emits_create_event(
        self,
        repository_with_events: GenericRepository[Todo],
        mock_session: AsyncMock,
        mock_event_bus: AsyncMock,
    ) -> None:
        """save() on new entity should emit a create event."""
        todo = Todo(title="Test Task")

        mock_exists_result = MagicMock()
        mock_exists_result.scalar.return_value = False
        mock_session.execute.return_value = mock_exists_result

        await repository_with_events.save(mock_session, todo)

        # Check that publish was called
        mock_event_bus.publish.assert_called_once()
        call_args = mock_event_bus.publish.call_args
        topic = call_args[0][0]
        event = call_args[0][1]

        assert topic == "doc.create"
        assert event.type == "doc.created"
        assert event.doctype == "Todo"

    @pytest.mark.asyncio
    async def test_save_existing_entity_emits_update_event(
        self,
        repository_with_events: GenericRepository[Todo],
        mock_session: AsyncMock,
        mock_event_bus: AsyncMock,
    ) -> None:
        """save() on existing entity should emit an update event."""
        todo = Todo(title="Test Task", name="TODO-001")

        mock_exists_result = MagicMock()
        mock_exists_result.scalar.return_value = True

        mock_update_result = MagicMock()
        mock_update_result.rowcount = 1

        mock_session.execute.side_effect = [mock_exists_result, mock_update_result]

        await repository_with_events.save(mock_session, todo)

        mock_event_bus.publish.assert_called_once()
        call_args = mock_event_bus.publish.call_args
        topic = call_args[0][0]
        event = call_args[0][1]

        assert topic == "doc.update"
        assert event.type == "doc.updated"

    @pytest.mark.asyncio
    async def test_delete_emits_delete_event(
        self,
        repository_with_events: GenericRepository[Todo],
        mock_session: AsyncMock,
        mock_event_bus: AsyncMock,
    ) -> None:
        """delete() should emit a delete event."""
        from datetime import UTC, datetime

        doc_id = uuid4()
        mock_row = MagicMock()
        mock_row._mapping = {
            "id": str(doc_id),
            "name": "TODO-001",
            "title": "Test Task",
            "is_completed": False,
            "owner": None,
            "modified": datetime.now(UTC),
            "modified_by": None,
            "deleted_at": None,
        }
        mock_result = MagicMock()
        mock_result.first.return_value = mock_row
        mock_session.execute.return_value = mock_result

        await repository_with_events.delete(mock_session, doc_id)

        mock_event_bus.publish.assert_called_once()
        call_args = mock_event_bus.publish.call_args
        topic = call_args[0][0]
        event = call_args[0][1]

        assert topic == "doc.delete"
        assert event.type == "doc.deleted"
        assert event.doc_name == "TODO-001"

    @pytest.mark.asyncio
    async def test_no_event_bus_no_emission(
        self, repository: GenericRepository[Todo], mock_session: AsyncMock
    ) -> None:
        """save() without event_bus should not fail."""
        todo = Todo(title="Test Task")

        mock_exists_result = MagicMock()
        mock_exists_result.scalar.return_value = False
        mock_session.execute.return_value = mock_exists_result

        # Should not raise even without event_bus
        result = await repository.save(mock_session, todo)
        assert result.title == "Test Task"

    def test_event_bus_property(
        self,
        repository_with_events: GenericRepository[Todo],
        mock_event_bus: AsyncMock,
    ) -> None:
        """event_bus property should return the configured event bus."""
        assert repository_with_events.event_bus is mock_event_bus


# =============================================================================
# Test: RLS Methods (list_for_user, get_for_user)
# =============================================================================


class TodoWithRLS(BaseDocType):
    """Test DocType with RLS enabled for permission tests."""

    title: str = Field(description="Task title")
    is_completed: bool = False

    class Meta:
        requires_auth: ClassVar[bool] = True
        apply_rls: ClassVar[bool] = True
        permissions: ClassVar[dict[str, list[str]]] = {
            "read": ["Employee", "Manager", "Admin"],
            "write": ["Manager", "Admin"],
        }


class TestRlsMethods:
    """Tests for list_for_user() and get_for_user() RLS methods."""

    @pytest.fixture
    def rls_table(self, metadata: MetaData) -> Table:
        """Create TodoWithRLS table for testing."""
        return Table(
            "todo_with_rls",
            metadata,
            Column("id", String(36), primary_key=True),
            Column("name", String(255), unique=True),
            Column("title", String(255)),
            Column("is_completed", Boolean, default=False),
            Column("owner", String(255)),
            Column("modified", DateTime),
            Column("modified_by", String(255)),
            Column("deleted_at", DateTime, nullable=True),
        )

    @pytest.fixture
    def rls_repository(self, rls_table: Table) -> GenericRepository[TodoWithRLS]:
        """Create a GenericRepository for TodoWithRLS."""
        return GenericRepository(
            model=TodoWithRLS,
            table=rls_table,
            controller_class=None,
        )

    @pytest.fixture
    def test_user(self) -> Any:
        """Create a test user context."""
        from framework_m.core.interfaces.auth_context import UserContext

        return UserContext(
            id="user-123",
            email="test@example.com",
            roles=["Employee"],
        )

    @pytest.fixture
    def admin_user(self) -> Any:
        """Create an admin user context."""
        from framework_m.core.interfaces.auth_context import UserContext

        return UserContext(
            id="admin-123",
            email="admin@example.com",
            roles=["Admin"],
        )

    @pytest.mark.asyncio
    async def test_list_for_user_calls_list_entities(
        self, rls_repository: GenericRepository[TodoWithRLS], mock_session: AsyncMock
    ) -> None:
        """list_for_user should delegate to list_entities."""
        from unittest.mock import patch

        with patch.object(rls_repository, "list_entities") as mock_list:
            mock_list.return_value = PaginatedResult(
                items=[], total=0, limit=20, offset=0
            )

            # Call without user
            await rls_repository.list_for_user(mock_session, None)

            # Should have called list_entities
            mock_list.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_for_user_returns_entity_for_owner(
        self,
        rls_repository: GenericRepository[TodoWithRLS],
        mock_session: AsyncMock,
        test_user: Any,
    ) -> None:
        """get_for_user should return entity when user is owner."""
        from unittest.mock import patch

        doc_id = uuid4()
        todo = TodoWithRLS(id=doc_id, title="Test", owner="user-123")

        # Patch internal get to return our test todo
        with patch.object(rls_repository, "get", return_value=todo):
            # Also need to patch the registry lookup for has_permission_for_doc
            from framework_m.core.registry import MetaRegistry

            registry = MetaRegistry.get_instance()
            registry.register_doctype(TodoWithRLS)

            result = await rls_repository.get_for_user(
                mock_session, test_user, doc_id, action="read"
            )

            assert result == todo
            registry.clear()

    @pytest.mark.asyncio
    async def test_get_for_user_raises_for_non_owner(
        self,
        rls_repository: GenericRepository[TodoWithRLS],
        mock_session: AsyncMock,
        test_user: Any,
    ) -> None:
        """get_for_user should raise PermissionDeniedError for non-owner."""
        from unittest.mock import patch

        from framework_m.core.exceptions import PermissionDeniedError

        doc_id = uuid4()
        # Different owner
        todo = TodoWithRLS(id=doc_id, title="Test", owner="other-user")

        with patch.object(rls_repository, "get", return_value=todo):
            from framework_m.core.registry import MetaRegistry

            registry = MetaRegistry.get_instance()
            registry.register_doctype(TodoWithRLS)

            with pytest.raises(PermissionDeniedError):
                await rls_repository.get_for_user(
                    mock_session, test_user, doc_id, action="read"
                )

            registry.clear()

    @pytest.mark.asyncio
    async def test_get_for_user_raises_entity_not_found(
        self,
        rls_repository: GenericRepository[TodoWithRLS],
        mock_session: AsyncMock,
        test_user: Any,
    ) -> None:
        """get_for_user should raise EntityNotFoundError when entity doesn't exist."""
        from unittest.mock import patch

        from framework_m.core.exceptions import EntityNotFoundError

        doc_id = uuid4()

        with (
            patch.object(rls_repository, "get", return_value=None),
            pytest.raises(EntityNotFoundError),
        ):
            await rls_repository.get_for_user(
                mock_session, test_user, doc_id, action="read"
            )

    @pytest.mark.asyncio
    async def test_get_for_user_admin_bypasses_rls(
        self,
        rls_repository: GenericRepository[TodoWithRLS],
        mock_session: AsyncMock,
        admin_user: Any,
    ) -> None:
        """get_for_user should allow admin to access any entity."""
        from unittest.mock import patch

        doc_id = uuid4()
        # Different owner
        todo = TodoWithRLS(id=doc_id, title="Test", owner="other-user")

        with patch.object(rls_repository, "get", return_value=todo):
            from framework_m.core.registry import MetaRegistry

            registry = MetaRegistry.get_instance()
            registry.register_doctype(TodoWithRLS)

            # Admin should be able to access
            result = await rls_repository.get_for_user(
                mock_session, admin_user, doc_id, action="read"
            )

            assert result == todo
            registry.clear()


# =============================================================================
# Test: Filter Operators
# =============================================================================


class TestFilterOperators:
    """Tests for list_entities() with various filter operators."""

    @pytest.mark.asyncio
    async def test_list_with_gt_operator(
        self, repository: GenericRepository[Todo], mock_session: AsyncMock
    ) -> None:
        """list_entities should support GT (greater than) operator."""
        from framework_m.core.interfaces.repository import FilterOperator, FilterSpec

        filters = [FilterSpec(field="title", operator=FilterOperator.GT, value="A")]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_count = MagicMock()
        mock_count.scalar.return_value = 0
        mock_session.execute.side_effect = [mock_result, mock_count]

        result = await repository.list_entities(mock_session, filters=filters)
        assert isinstance(result, PaginatedResult)

    @pytest.mark.asyncio
    async def test_list_with_lt_operator(
        self, repository: GenericRepository[Todo], mock_session: AsyncMock
    ) -> None:
        """list_entities should support LT (less than) operator."""
        from framework_m.core.interfaces.repository import FilterOperator, FilterSpec

        filters = [FilterSpec(field="title", operator=FilterOperator.LT, value="Z")]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_count = MagicMock()
        mock_count.scalar.return_value = 0
        mock_session.execute.side_effect = [mock_result, mock_count]

        result = await repository.list_entities(mock_session, filters=filters)
        assert isinstance(result, PaginatedResult)

    @pytest.mark.asyncio
    async def test_list_with_gte_operator(
        self, repository: GenericRepository[Todo], mock_session: AsyncMock
    ) -> None:
        """list_entities should support GTE (greater than or equal) operator."""
        from framework_m.core.interfaces.repository import FilterOperator, FilterSpec

        filters = [FilterSpec(field="title", operator=FilterOperator.GTE, value="A")]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_count = MagicMock()
        mock_count.scalar.return_value = 0
        mock_session.execute.side_effect = [mock_result, mock_count]

        result = await repository.list_entities(mock_session, filters=filters)
        assert isinstance(result, PaginatedResult)

    @pytest.mark.asyncio
    async def test_list_with_lte_operator(
        self, repository: GenericRepository[Todo], mock_session: AsyncMock
    ) -> None:
        """list_entities should support LTE (less than or equal) operator."""
        from framework_m.core.interfaces.repository import FilterOperator, FilterSpec

        filters = [FilterSpec(field="title", operator=FilterOperator.LTE, value="Z")]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_count = MagicMock()
        mock_count.scalar.return_value = 0
        mock_session.execute.side_effect = [mock_result, mock_count]

        result = await repository.list_entities(mock_session, filters=filters)
        assert isinstance(result, PaginatedResult)

    @pytest.mark.asyncio
    async def test_list_with_ne_operator(
        self, repository: GenericRepository[Todo], mock_session: AsyncMock
    ) -> None:
        """list_entities should support NE (not equal) operator."""
        from framework_m.core.interfaces.repository import FilterOperator, FilterSpec

        filters = [
            FilterSpec(field="is_completed", operator=FilterOperator.NE, value=True)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_count = MagicMock()
        mock_count.scalar.return_value = 0
        mock_session.execute.side_effect = [mock_result, mock_count]

        result = await repository.list_entities(mock_session, filters=filters)
        assert isinstance(result, PaginatedResult)

    @pytest.mark.asyncio
    async def test_list_with_in_operator(
        self, repository: GenericRepository[Todo], mock_session: AsyncMock
    ) -> None:
        """list_entities should support IN operator."""
        from framework_m.core.interfaces.repository import FilterOperator, FilterSpec

        filters = [
            FilterSpec(
                field="title", operator=FilterOperator.IN, value=["Task 1", "Task 2"]
            )
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_count = MagicMock()
        mock_count.scalar.return_value = 0
        mock_session.execute.side_effect = [mock_result, mock_count]

        result = await repository.list_entities(mock_session, filters=filters)
        assert isinstance(result, PaginatedResult)

    @pytest.mark.asyncio
    async def test_list_with_like_operator(
        self, repository: GenericRepository[Todo], mock_session: AsyncMock
    ) -> None:
        """list_entities should support LIKE operator."""
        from framework_m.core.interfaces.repository import FilterOperator, FilterSpec

        filters = [
            FilterSpec(field="title", operator=FilterOperator.LIKE, value="%Task%")
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_count = MagicMock()
        mock_count.scalar.return_value = 0
        mock_session.execute.side_effect = [mock_result, mock_count]

        result = await repository.list_entities(mock_session, filters=filters)
        assert isinstance(result, PaginatedResult)


# =============================================================================
# Test: Ordering
# =============================================================================


class TestOrderingOperations:
    """Tests for list_entities() ordering."""

    @pytest.mark.asyncio
    async def test_list_with_asc_order(
        self, repository: GenericRepository[Todo], mock_session: AsyncMock
    ) -> None:
        """list_entities should support ascending order."""
        from framework_m.core.interfaces.repository import OrderSpec

        order_by = [OrderSpec(field="title", direction="asc")]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_count = MagicMock()
        mock_count.scalar.return_value = 0
        mock_session.execute.side_effect = [mock_result, mock_count]

        result = await repository.list_entities(mock_session, order_by=order_by)
        assert isinstance(result, PaginatedResult)

    @pytest.mark.asyncio
    async def test_list_with_desc_order(
        self, repository: GenericRepository[Todo], mock_session: AsyncMock
    ) -> None:
        """list_entities should support descending order."""
        from framework_m.core.interfaces.repository import OrderSpec

        order_by = [OrderSpec(field="title", direction="desc")]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_count = MagicMock()
        mock_count.scalar.return_value = 0
        mock_session.execute.side_effect = [mock_result, mock_count]

        result = await repository.list_entities(mock_session, order_by=order_by)
        assert isinstance(result, PaginatedResult)

    @pytest.mark.asyncio
    async def test_list_with_multiple_order_fields(
        self, repository: GenericRepository[Todo], mock_session: AsyncMock
    ) -> None:
        """list_entities should support multiple order fields."""
        from framework_m.core.interfaces.repository import OrderSpec

        order_by = [
            OrderSpec(field="is_completed", direction="asc"),
            OrderSpec(field="title", direction="desc"),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_count = MagicMock()
        mock_count.scalar.return_value = 0
        mock_session.execute.side_effect = [mock_result, mock_count]

        result = await repository.list_entities(mock_session, order_by=order_by)
        assert isinstance(result, PaginatedResult)


# =============================================================================
# Test: Pagination Edge Cases
# =============================================================================


class TestPaginationEdgeCases:
    """Tests for list_entities() pagination edge cases."""

    @pytest.mark.asyncio
    async def test_list_with_zero_offset(
        self, repository: GenericRepository[Todo], mock_session: AsyncMock
    ) -> None:
        """list_entities should work with zero offset."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_count = MagicMock()
        mock_count.scalar.return_value = 0
        mock_session.execute.side_effect = [mock_result, mock_count]

        result = await repository.list_entities(mock_session, offset=0, limit=10)
        assert result.offset == 0

    @pytest.mark.asyncio
    async def test_list_with_large_offset(
        self, repository: GenericRepository[Todo], mock_session: AsyncMock
    ) -> None:
        """list_entities should work with large offset."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_count = MagicMock()
        mock_count.scalar.return_value = 5  # Only 5 items exist
        mock_session.execute.side_effect = [mock_result, mock_count, mock_count]

        result = await repository.list_entities(mock_session, offset=100, limit=10)
        assert result.items == []

    @pytest.mark.asyncio
    async def test_list_with_small_limit(
        self, repository: GenericRepository[Todo], mock_session: AsyncMock
    ) -> None:
        """list_entities should respect small limit."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_count = MagicMock()
        mock_count.scalar.return_value = 100
        mock_session.execute.side_effect = [mock_result, mock_count]

        result = await repository.list_entities(mock_session, limit=1)
        assert result.limit == 1


# =============================================================================
# Test: Cache Integration
# =============================================================================


class TestCacheIntegration:
    """Tests for cache integration in GenericRepository."""

    def test_repository_accepts_cache_parameter(self, todo_table: Table) -> None:
        """GenericRepository should accept cache parameter."""
        from framework_m.adapters.cache import InMemoryCacheAdapter

        cache = InMemoryCacheAdapter()
        repo = GenericRepository(
            model=Todo,
            table=todo_table,
            cache=cache,
        )

        assert repo.cache is not None
        assert repo.cache is cache

    def test_cache_key_format(self, todo_table: Table) -> None:
        """Cache key should follow DocTypeName:id format."""
        repo = GenericRepository(model=Todo, table=todo_table)
        test_id = uuid4()

        key = repo._cache_key(test_id)

        assert key == f"Todo:{test_id}"

    @pytest.mark.asyncio
    async def test_get_checks_cache_first(
        self, todo_table: Table, mock_session: AsyncMock
    ) -> None:
        """get() should check cache before database."""
        from framework_m.adapters.cache import InMemoryCacheAdapter

        cache = InMemoryCacheAdapter()
        repo = GenericRepository(model=Todo, table=todo_table, cache=cache)
        test_id = uuid4()

        # Pre-populate cache
        cached_data = {
            "id": str(test_id),
            "name": "cached-todo",
            "title": "Cached Todo",
            "is_completed": False,
            "owner": "user-1",
            "creation": "2024-01-01T00:00:00",
            "modified": "2024-01-01T00:00:00",
        }
        await cache.set(f"Todo:{test_id}", cached_data)

        # get() should return cached value without hitting DB
        result = await repo.get(mock_session, test_id)

        assert result is not None
        assert result.title == "Cached Todo"
        # Session should NOT have been used
        mock_session.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_stores_result_in_cache(
        self, todo_table: Table, mock_session: AsyncMock
    ) -> None:
        """get() should store result in cache on cache miss."""
        from framework_m.adapters.cache import InMemoryCacheAdapter

        cache = InMemoryCacheAdapter()
        repo = GenericRepository(model=Todo, table=todo_table, cache=cache)
        test_id = uuid4()

        # Setup mock to return a row
        mock_row = MagicMock()
        mock_row._mapping = {
            "id": test_id,
            "name": "db-todo",
            "title": "DB Todo",
            "is_completed": False,
            "owner": "user-1",
            "creation": "2024-01-01T00:00:00",
            "modified": "2024-01-01T00:00:00",
        }
        mock_result = MagicMock()
        mock_result.first.return_value = mock_row
        mock_session.execute.return_value = mock_result

        # Call get()
        await repo.get(mock_session, test_id)

        # Should now be in cache
        cached = await cache.get(f"Todo:{test_id}")
        assert cached is not None
