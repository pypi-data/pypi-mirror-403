"""Generic Repository - SQLAlchemy implementation of RepositoryProtocol.

This module provides the GenericRepository class that implements standard
CRUD operations for DocTypes using SQLAlchemy async sessions.

Features:
- Automatic soft delete (deleted_at)
- Controller lifecycle hooks
- Optimistic Concurrency Control (OCC) support
- Name auto-generation
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, get_args, get_origin
from uuid import UUID, uuid4

from sqlalchemy import Table, func, select, update
from sqlalchemy import delete as sql_delete
from sqlalchemy.exc import IntegrityError as SAIntegrityError
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from framework_m.core.domain.base_doctype import BaseDocType
from framework_m.core.exceptions import (
    DatabaseError,
    DuplicateNameError,
    IntegrityError,
    RepositoryError,
)
from framework_m.core.interfaces.repository import (
    FilterOperator,
    FilterSpec,
    OrderDirection,
    OrderSpec,
    PaginatedResult,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from framework_m.adapters.cache.redis_cache import CacheProtocol
    from framework_m.core.domain.base_controller import BaseController
    from framework_m.core.interfaces.auth_context import UserContext
    from framework_m.core.interfaces.event_bus import EventBusProtocol


class VersionConflictError(Exception):
    """Raised when optimistic concurrency control detects a conflict."""

    def __init__(self, entity_id: UUID, expected_version: int) -> None:
        """Initialize with conflict details.

        Args:
            entity_id: The ID of the entity with version conflict
            expected_version: The version that was expected
        """
        self.entity_id = entity_id
        self.expected_version = expected_version
        super().__init__(
            f"Version conflict for entity {entity_id}. "
            f"Expected version {expected_version}."
        )


class GenericRepository[T: BaseDocType]:
    """Generic SQLAlchemy repository implementing RepositoryProtocol.

    Provides standard CRUD operations for DocTypes using async SQLAlchemy.
    Supports controller lifecycle hooks and optimistic concurrency control.

    Note:
        This repository does NOT store sessions. All CRUD methods accept
        session as the first parameter. The caller owns the session via
        UnitOfWork context manager.

    Example:
        >>> repo = GenericRepository(
        ...     model=Todo,
        ...     table=todo_table,
        ...     controller_class=TodoController,
        ...     event_bus=InMemoryEventBus(),
        ... )
        >>> async with uow_factory() as uow:
        ...     todo = await repo.save(uow.session, entity)
    """

    def __init__(
        self,
        model: type[T],
        table: Table,
        controller_class: type[BaseController[T]] | None = None,
        event_bus: EventBusProtocol | None = None,
        cache: CacheProtocol | None = None,
    ) -> None:
        """Initialize the repository.

        Args:
            model: The DocType model class
            table: SQLAlchemy Table object
            controller_class: Optional controller for lifecycle hooks
            event_bus: Optional event bus for publishing domain events
            cache: Optional cache for query result caching
        """
        self._model = model
        self._table = table
        self._controller_class = controller_class
        self._event_bus = event_bus
        self._cache = cache

    @property
    def model(self) -> type[T]:
        """Get the DocType model class."""
        return self._model

    @property
    def table(self) -> Table:
        """Get the SQLAlchemy table."""
        return self._table

    @property
    def controller_class(self) -> type[BaseController[T]] | None:
        """Get the controller class if set."""
        return self._controller_class

    @property
    def event_bus(self) -> EventBusProtocol | None:
        """Get the event bus if set."""
        return self._event_bus

    @property
    def cache(self) -> CacheProtocol | None:
        """Get the cache if set."""
        return self._cache

    def _cache_key(self, id: UUID) -> str:
        """Generate cache key for an entity."""
        return f"{self._model.__name__}:{id}"

    async def get(
        self, session: AsyncSession, id: UUID, include_deleted: bool = False
    ) -> T | None:
        """Retrieve an entity by its unique identifier.

        Args:
            session: SQLAlchemy async session
            id: The UUID of the entity
            include_deleted: If True, include soft-deleted entities

        Returns:
            The entity if found, None otherwise
        """
        # Check cache first (only for non-deleted queries)
        if self._cache and not include_deleted:
            cache_key = self._cache_key(id)
            cached = await self._cache.get(cache_key)
            if cached:
                logger.debug("CACHE HIT %s[%s]", self._model.__name__, id)
                return self._model.model_validate(cached)

        stmt = select(self._table).where(self._table.c.id == id)

        # Filter soft-deleted by default
        if not include_deleted and hasattr(self._table.c, "deleted_at"):
            stmt = stmt.where(self._table.c.deleted_at.is_(None))

        logger.debug(
            "GET %s[%s] (include_deleted=%s)",
            self._model.__name__,
            id,
            include_deleted,
        )

        result = await session.execute(stmt)
        row = result.first()

        if row is None:
            return None

        entity = self._row_to_entity(row)

        # Load child tables
        child_fields = self._get_child_table_fields()
        if child_fields and entity:
            await self._load_child_tables(session, entity, child_fields)

        # Cache the result
        if self._cache and entity and not include_deleted:
            cache_key = self._cache_key(id)
            await self._cache.set(cache_key, entity.model_dump(mode="json"), ttl=300)
            logger.debug("CACHE SET %s[%s]", self._model.__name__, id)

        return entity

    async def get_by_name(
        self, session: AsyncSession, name: str, include_deleted: bool = False
    ) -> T | None:
        """Retrieve an entity by its human-readable name.

        Args:
            session: SQLAlchemy async session
            name: The name of the entity
            include_deleted: If True, include soft-deleted entities

        Returns:
            The entity if found, None otherwise
        """
        stmt = select(self._table).where(self._table.c.name == name)

        if not include_deleted and hasattr(self._table.c, "deleted_at"):
            stmt = stmt.where(self._table.c.deleted_at.is_(None))

        result = await session.execute(stmt)
        row = result.first()

        if row is None:
            return None

        return self._row_to_entity(row)

    async def save(
        self, session: AsyncSession, entity: T, version: int | None = None
    ) -> T:
        """Persist an entity (insert or update).

        Args:
            session: SQLAlchemy async session
            entity: The entity to save
            version: Expected version for OCC (optional)

        Returns:
            The saved entity with updated fields

        Raises:
            VersionConflictError: If version doesn't match (OCC)
            DuplicateNameError: If name collision persists after retries
        """
        # Track if we auto-generated the name (for retry logic)
        auto_generated_name = entity.name is None

        # Generate name if not set
        if auto_generated_name:
            entity.name = await self._generate_name(session, entity)

        # Check if entity exists
        is_new = not await self._entity_exists(session, entity)

        # Get controller instance if available
        controller = self._get_controller(entity)

        if is_new:
            return await self._insert_with_retry(
                session, entity, controller, auto_generated_name
            )
        else:
            return await self._update(session, entity, controller, version)

    async def delete(self, session: AsyncSession, id: UUID, hard: bool = False) -> None:
        """Delete an entity by its unique identifier.

        By default performs soft-delete (sets deleted_at). Use hard=True
        for physical deletion.

        Args:
            session: SQLAlchemy async session
            id: The UUID of the entity to delete
            hard: If True, physically delete; otherwise soft-delete
        """
        # Get entity for lifecycle hooks and event emission
        entity = await self.get(session, id)
        controller = None
        if entity and self._controller_class is not None:
            controller = self._get_controller(entity)

        # Lifecycle: before_delete
        if controller:
            await controller.before_delete()

        # Delete child tables first (cascade)
        child_fields = self._get_child_table_fields()
        if child_fields:
            await self._delete_child_tables(session, id, child_fields)

        if hard:
            # Physical delete
            delete_stmt = sql_delete(self._table).where(self._table.c.id == id)
            await session.execute(delete_stmt)
        else:
            # Soft delete
            update_stmt = (
                update(self._table)
                .where(self._table.c.id == id)
                .values(deleted_at=datetime.now(UTC))
            )
            await session.execute(update_stmt)

        # Lifecycle: after_delete
        if controller:
            await controller.after_delete()

        # Emit delete event
        if entity:
            await self._emit_event("delete", entity)

        # Invalidate cache
        if self._cache:
            await self._cache.delete(self._cache_key(id))
            logger.debug("CACHE INVALIDATE %s[%s]", self._model.__name__, id)

    async def exists(self, session: AsyncSession, id: UUID) -> bool:
        """Check if an entity exists by its identifier.

        Args:
            session: SQLAlchemy async session
            id: The UUID to check

        Returns:
            True if entity exists and is not soft-deleted
        """
        stmt = (
            select(func.count()).select_from(self._table).where(self._table.c.id == id)
        )
        if hasattr(self._table.c, "deleted_at"):
            stmt = stmt.where(self._table.c.deleted_at.is_(None))

        result = await session.execute(stmt)
        count = result.scalar()
        return count is not None and count > 0

    async def count(
        self, session: AsyncSession, filters: list[FilterSpec] | None = None
    ) -> int:
        """Count entities matching the given filters.

        Args:
            session: SQLAlchemy async session
            filters: Optional list of filter conditions

        Returns:
            Total count of matching entities
        """
        stmt = select(func.count()).select_from(self._table)

        # Exclude soft-deleted
        if hasattr(self._table.c, "deleted_at"):
            stmt = stmt.where(self._table.c.deleted_at.is_(None))

        if filters:
            stmt = self._apply_filters(stmt, filters)

        result = await session.execute(stmt)
        return result.scalar() or 0

    async def list_entities(
        self,
        session: AsyncSession,
        filters: list[FilterSpec] | None = None,
        order_by: list[OrderSpec] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> PaginatedResult[T]:
        """List entities with filtering, sorting, and pagination.

        Args:
            session: SQLAlchemy async session
            filters: Filter conditions
            order_by: Sort specifications
            limit: Maximum number of items (default 20, max 1000)
            offset: Number of items to skip

        Returns:
            PaginatedResult containing items and metadata
        """
        # Enforce max limit
        effective_limit = min(limit, 1000)

        # Build base query
        stmt = select(self._table)

        # Exclude soft-deleted
        if hasattr(self._table.c, "deleted_at"):
            stmt = stmt.where(self._table.c.deleted_at.is_(None))

        if filters is not None:
            stmt = self._apply_filters(stmt, filters)

        # Get total count
        total = await self.count(session, filters)

        # Apply ordering
        if order_by is not None:
            stmt = self._apply_ordering(stmt, order_by)

        # Apply pagination
        stmt = stmt.limit(effective_limit).offset(offset)

        logger.debug(
            "LIST %s (filters=%d, order_by=%d, limit=%d, offset=%d)",
            self._model.__name__,
            len(filters) if filters else 0,
            len(order_by) if order_by else 0,
            effective_limit,
            offset,
        )

        result = await session.execute(stmt)
        rows = result.fetchall()

        items = [self._row_to_entity(row) for row in rows]

        return PaginatedResult(
            items=items,
            total=total,
            limit=effective_limit,
            offset=offset,
        )

    async def list_for_user(
        self,
        session: AsyncSession,
        user: UserContext | None,
        filters: list[FilterSpec] | None = None,
        order_by: list[OrderSpec] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> PaginatedResult[T]:
        """List entities with RLS filtering applied.

        This method automatically applies Row-Level Security filters
        based on the user's permissions and the DocType's RLS settings.

        Args:
            session: SQLAlchemy async session
            user: Current user context (None for public access)
            filters: Additional filter conditions
            order_by: Sort specifications
            limit: Maximum number of items (default 20, max 1000)
            offset: Number of items to skip

        Returns:
            PaginatedResult containing only items the user can access
        """
        from framework_m.core.rls import apply_rls_filters

        # Apply RLS filters
        doctype_name = self._model.get_doctype_name()
        merged_filters = await apply_rls_filters(user, doctype_name, filters)

        return await self.list_entities(
            session=session,
            filters=merged_filters,
            order_by=order_by,
            limit=limit,
            offset=offset,
        )

    async def get_for_user(
        self,
        session: AsyncSession,
        user: UserContext,
        id: UUID,
        action: str = "read",
        include_deleted: bool = False,
    ) -> T:
        """Retrieve an entity with permission checking.

        Loads the entity and verifies the user has permission to access it.
        Raises PermissionDeniedError if access is denied.

        Args:
            session: SQLAlchemy async session
            user: Current user context
            id: The UUID of the entity
            action: The action to check (default: "read")
            include_deleted: If True, include soft-deleted entities

        Returns:
            The entity if found and accessible

        Raises:
            EntityNotFoundError: If entity does not exist
            PermissionDeniedError: If user lacks permission
        """
        from framework_m.core.exceptions import (
            EntityNotFoundError,
            PermissionDeniedError,
        )
        from framework_m.core.permissions import has_permission_for_doc

        # First load the entity
        entity = await self.get(session, id, include_deleted)

        if entity is None:
            raise EntityNotFoundError(self._model.__name__, str(id))

        # Check permission
        has_perm = await has_permission_for_doc(user, entity, action)
        if not has_perm:
            raise PermissionDeniedError(
                f"User '{user.id}' does not have '{action}' permission for "
                f"{self._model.__name__} '{id}'"
            )

        return entity

    async def bulk_save(self, session: AsyncSession, entities: list[T]) -> list[T]:
        """Save multiple entities in a single operation.

        Uses SQLAlchemy bulk insert for new entities for better performance.
        For updates, falls back to individual saves due to version handling.

        Args:
            session: SQLAlchemy async session
            entities: List of entities to save

        Returns:
            List of saved entities with updated fields
        """
        if not entities:
            return []

        # Separate new and existing entities
        new_entities: list[T] = []
        existing_entities: list[T] = []

        for entity in entities:
            if await self._entity_exists(session, entity):
                existing_entities.append(entity)
            else:
                new_entities.append(entity)

        results: list[T] = []

        # Bulk insert new entities
        if new_entities:
            inserted = await self._bulk_insert(session, new_entities)
            results.extend(inserted)

        # Update existing entities individually (for version handling)
        for entity in existing_entities:
            saved = await self.save(session, entity)
            results.append(saved)

        return results

    async def _bulk_insert(self, session: AsyncSession, entities: list[T]) -> list[T]:
        """Bulk insert multiple new entities.

        Uses SQLAlchemy's bulk insert for better performance.

        Args:
            session: SQLAlchemy async session
            entities: List of new entities to insert

        Returns:
            List of inserted entities
        """
        if not entities:
            return []

        # Prepare all entity data
        values_list = []
        for entity in entities:
            # Generate name if not set
            if entity.name is None:
                entity.name = await self._generate_name(session, entity)

            data = entity.model_dump()
            data["modified"] = datetime.now(UTC)
            values_list.append(data)

        # Execute bulk insert with error handling
        try:
            stmt = self._table.insert().values(values_list)
            await session.execute(stmt)
            logger.debug(
                "Bulk inserted %d %s entities",
                len(entities),
                self._model.__name__,
            )
        except SAIntegrityError as e:
            error_msg = str(e.orig) if e.orig else str(e)
            logger.error(
                "Bulk insert failed for %s: %s",
                self._model.__name__,
                error_msg,
                extra={"doctype": self._model.__name__, "count": len(entities)},
            )
            if "UNIQUE constraint" in error_msg or "duplicate key" in error_msg.lower():
                raise DuplicateNameError(self._model.__name__, "bulk") from e
            raise IntegrityError(error_msg) from e
        except SQLAlchemyError as e:
            logger.error(
                "Bulk insert database error for %s: %s",
                self._model.__name__,
                str(e),
                extra={"doctype": self._model.__name__, "operation": "bulk_insert"},
            )
            raise RepositoryError(f"Bulk insert failed: {e}") from e

        return entities

    # =========================================================================
    # Private Methods
    # =========================================================================

    def _row_to_entity(self, row: Any) -> T:
        """Convert a database row to an entity.

        Args:
            row: SQLAlchemy row result

        Returns:
            Entity instance
        """
        data = dict(row._mapping)

        # Get model field names to filter out db-only columns
        model_fields = set(self._model.model_fields.keys())

        # Filter data to only include model fields
        filtered_data: dict[str, Any] = {}
        for key, value in data.items():
            if key in model_fields:
                # Convert string booleans if needed
                if value == "true":
                    filtered_data[key] = True
                elif value == "false":
                    filtered_data[key] = False
                else:
                    filtered_data[key] = value

        return self._model.model_validate(filtered_data)

    async def _generate_name(self, session: AsyncSession, entity: T) -> str:
        """Generate a unique name for an entity based on Meta.name_pattern.

        If Meta.name_pattern is defined, generates name using pattern.
        Otherwise, uses default UUID-based naming.

        Supports:
        - Regular patterns: "INV-.YYYY.-.####" -> "INV-2026-0001"
        - Sequence patterns: "sequence:invoice_seq" -> Uses DB sequence

        Args:
            session: SQLAlchemy async session for counter queries
            entity: The entity to generate name for

        Returns:
            Generated name string
        """
        # Check if model has name_pattern
        meta = getattr(self._model, "Meta", None)
        name_pattern = getattr(meta, "name_pattern", None) if meta else None

        if not name_pattern:
            # No pattern - use default UUID-based naming
            prefix = self._model.__name__.upper()[:4]
            unique_part = uuid4().hex[:8].upper()
            return f"{prefix}-{unique_part}"

        # Check for sequence-based pattern
        if name_pattern.startswith("sequence:"):
            return await self._generate_name_from_sequence(session, name_pattern)

        # Generate name from regular pattern
        return await self._generate_name_from_pattern(session, entity, name_pattern)

    async def _generate_name_from_sequence(
        self, session: AsyncSession, pattern: str
    ) -> str:
        """Generate name using a database sequence.

        For PostgreSQL, uses native sequences for high performance.
        For other databases, falls back to counter-based approach.

        Args:
            session: SQLAlchemy async session
            pattern: Sequence pattern like "sequence:invoice_seq"

        Returns:
            Generated name from sequence value
        """
        sequence_name = pattern.split(":", 1)[1]

        # Try to use native PostgreSQL sequence
        try:
            from sqlalchemy import text

            # Check if we're on PostgreSQL by trying to use nextval
            result = await session.execute(text(f"SELECT nextval('{sequence_name}')"))
            seq_value = result.scalar()
            return f"{self._model.__name__.upper()[:4]}-{seq_value:08d}"
        except Exception:
            # Fallback for non-PostgreSQL (SQLite, etc.)
            # Use prefix-based counter approach
            prefix = f"{self._model.__name__.upper()[:4]}-"
            counter = await self._get_next_counter(session, prefix)
            return f"{prefix}{counter:08d}"

    async def _generate_name_from_pattern(
        self, session: AsyncSession, entity: T, pattern: str
    ) -> str:
        """Generate name from naming pattern.

        Supports patterns like:
        - INV-.YYYY.-.#### (year + counter)
        - ORD-.YYYY.-.MM.-.#### (year + month + counter)
        - RCP-.YYYY.MM.DD.-.#### (full date + counter)
        - TASK-.{field}.-.#### (field value + counter)

        Args:
            session: SQLAlchemy async session
            entity: The entity
            pattern: Naming pattern string

        Returns:
            Generated name
        """
        import re
        from datetime import UTC, datetime

        now = datetime.now(UTC)

        # Replace date/time placeholders
        result = pattern
        result = result.replace(".YYYY.", f"{now.year}")
        result = result.replace(".MM.", f"{now.month:02d}")
        result = result.replace(".DD.", f"{now.day:02d}")

        # Also handle patterns without surrounding dots
        result = result.replace("YYYY", f"{now.year}")
        result = result.replace("MM", f"{now.month:02d}")
        result = result.replace("DD", f"{now.day:02d}")

        # Replace field value placeholders {field}
        field_pattern = re.compile(r"\{(\w+)\}")
        for match in field_pattern.finditer(result):
            field_name = match.group(1)
            if hasattr(entity, field_name):
                field_value = getattr(entity, field_name)
                result = result.replace(f".{{{field_name}}}.", str(field_value))
                result = result.replace(f"{{{field_name}}}", str(field_value))

        # Remove pattern separator dots (.) - they delimit placeholders
        result = result.replace(".", "")

        # Count # characters to determine counter width
        hash_count = pattern.count("#")
        if hash_count == 0:
            # No counter needed
            return result

        # Get prefix (everything before the counter)
        prefix = result.split("#")[0]

        # Get next counter value for this prefix
        counter = await self._get_next_counter(session, prefix)

        # Replace #### with padded counter
        counter_str = str(counter).zfill(hash_count)
        result = result.replace("#" * hash_count, counter_str)

        return result

    async def _get_next_counter(self, session: AsyncSession, prefix: str) -> int:
        """Get next counter value for a prefix.

        Uses optimistic approach - query max existing counter and increment.
        If collision occurs, retry with next number (handled by unique constraint).

        Args:
            session: SQLAlchemy async session
            prefix: Name prefix (e.g., "INV-2024-")

        Returns:
            Next counter value
        """
        from sqlalchemy import select

        # Query for highest existing counter with this prefix
        # Pattern: prefix + number, so we look for names starting with prefix
        stmt = (
            select(self._table.c.name)
            .where(self._table.c.name.like(f"{prefix}%"))
            .order_by(self._table.c.name.desc())
        )
        result = await session.execute(stmt)
        rows = result.fetchall()

        if not rows:
            # No existing documents with this prefix
            return 1

        # Extract counter from last name
        last_name = rows[0][0]
        suffix = last_name[len(prefix) :]

        # Try to parse as integer
        try:
            last_counter = int(suffix)
            return last_counter + 1
        except ValueError:
            # Could not parse counter, start at 1
            return 1

    async def _entity_exists(self, session: AsyncSession, entity: T) -> bool:
        """Check if an entity already exists in the database.

        Args:
            session: SQLAlchemy async session
            entity: The entity to check

        Returns:
            True if entity exists
        """
        if entity.name is None:
            return False

        stmt = (
            select(func.count())
            .select_from(self._table)
            .where(self._table.c.name == entity.name)
        )
        result = await session.execute(stmt)
        count = result.scalar()
        return count is not None and count > 0

    def _get_controller(self, entity: T) -> BaseController[T] | None:
        """Get a controller instance for the entity.

        Args:
            entity: The entity

        Returns:
            Controller instance or None
        """
        if self._controller_class is None:
            return None
        return self._controller_class(entity)

    async def _call_hook(
        self,
        controller: BaseController[T] | None,
        hook_name: str,
        context: object = None,
    ) -> None:
        """Call a lifecycle hook on the controller if it exists.

        This helper method checks if the controller exists, if the hook method
        exists on the controller, and calls it with optional context.

        Args:
            controller: Optional controller instance
            hook_name: Name of the hook method to call (e.g., 'validate', 'before_save')
            context: Optional context to pass to the hook

        Raises:
            Any exception raised by the hook method is propagated to the caller
        """
        if controller is None:
            return

        hook_method = getattr(controller, hook_name, None)
        if hook_method is None:
            return

        if callable(hook_method):
            await hook_method(context)

    async def _emit_event(
        self,
        event_type: str,
        entity: T,
        changed_fields: list[str] | None = None,
    ) -> None:
        """Emit a domain event if event_bus is configured.

        Args:
            event_type: Event type suffix (e.g., "create", "update", "delete")
            entity: The entity that triggered the event
            changed_fields: List of changed field names (for updates)
        """
        if self._event_bus is None:
            return

        # Import here to avoid circular imports at module level
        from framework_m.core.events import DocCreated, DocDeleted, DocUpdated
        from framework_m.core.interfaces.event_bus import Event

        doctype_name = self._model.__name__
        doc_name = str(entity.name) if entity.name else str(entity.id)

        # Create appropriate event type
        event: Event
        if event_type == "create":
            event = DocCreated(
                doctype=doctype_name,
                doc_name=doc_name,
            )
        elif event_type == "update":
            event = DocUpdated(
                doctype=doctype_name,
                doc_name=doc_name,
                changed_fields=changed_fields or [],
            )
        elif event_type == "delete":
            event = DocDeleted(
                doctype=doctype_name,
                doc_name=doc_name,
            )
        else:
            # Fallback to generic event
            event = Event(
                id=str(uuid4()),
                type=f"{doctype_name}.{event_type}",
                source="framework_m",
                subject=f"{doctype_name}:{doc_name}",
                data={
                    "id": str(entity.id),
                    "name": entity.name,
                    "doctype": doctype_name,
                },
            )

        try:
            topic = f"doc.{event_type}"
            await self._event_bus.publish(topic, event)
            logger.debug(
                "Emitted event %s for %s",
                event.type,
                doc_name,
                extra={"doctype": doctype_name, "event_type": event_type},
            )
        except Exception as e:
            # Log but don't fail the operation if event emission fails
            logger.warning(
                "Failed to emit event %s: %s",
                event.type,
                str(e),
                extra={"doctype": doctype_name, "event_type": event_type},
            )

    async def _insert_with_retry(
        self,
        session: AsyncSession,
        entity: T,
        controller: BaseController[T] | None,
        auto_generated_name: bool,
        max_retries: int = 3,
    ) -> T:
        """Insert a new entity with retry on name collision.

        For auto-generated names, retries with a new name if DuplicateNameError
        occurs (e.g., from concurrent inserts with same counter value).
        For manually provided names, does not retry.

        Args:
            session: SQLAlchemy async session
            entity: The entity to insert
            controller: Optional controller for lifecycle hooks
            auto_generated_name: Whether name was auto-generated (enables retry)
            max_retries: Maximum number of retry attempts (default 3)

        Returns:
            The inserted entity

        Raises:
            DuplicateNameError: If collision persists after max retries (or manual name)
        """
        for attempt in range(max_retries + 1):
            try:
                return await self._insert(session, entity, controller)
            except DuplicateNameError:
                if not auto_generated_name or attempt >= max_retries:
                    # Manual name or max retries exceeded - propagate error
                    raise
                # Retry with new generated name
                logger.debug(
                    "Name collision on %s attempt %d, regenerating",
                    entity.name,
                    attempt + 1,
                )
                entity.name = await self._generate_name(session, entity)

        # Should not reach here, but satisfy type checker
        return await self._insert(session, entity, controller)

    async def _insert(
        self, session: AsyncSession, entity: T, controller: BaseController[T] | None
    ) -> T:
        """Insert a new entity.

        Args:
            session: SQLAlchemy async session
            entity: The entity to insert
            controller: Optional controller for lifecycle hooks

        Returns:
            The inserted entity
        """
        # Fetch values from linked documents
        await self._fetch_link_values(session, entity)

        # Lifecycle hooks: validate, before_insert, before_save
        await self._call_hook(controller, "validate")
        await self._call_hook(controller, "before_insert")
        await self._call_hook(controller, "before_save")

        # Prepare data (exclude child table fields and computed fields)
        exclude_fields = self._get_excluded_fields()
        data = entity.model_dump(exclude=exclude_fields)
        data["modified"] = datetime.now(UTC)

        # Execute insert with error handling
        try:
            stmt = self._table.insert().values(**data)
            await session.execute(stmt)
            await session.flush()  # Ensure INSERT is written to DB
        except SAIntegrityError as e:
            error_msg = str(e.orig) if e.orig else str(e)
            logger.error(
                "Insert failed for %s: %s",
                self._model.__name__,
                error_msg,
                extra={"doctype": self._model.__name__, "entity_name": entity.name},
            )
            # Check for duplicate name error
            if "UNIQUE constraint" in error_msg or "duplicate key" in error_msg.lower():
                raise DuplicateNameError(self._model.__name__, entity.name or "") from e
            raise IntegrityError(error_msg) from e
        except OperationalError as e:
            logger.error(
                "Database operation failed for %s: %s",
                self._model.__name__,
                str(e),
                extra={"doctype": self._model.__name__, "operation": "insert"},
            )
            raise DatabaseError("insert", str(e)) from e
        except SQLAlchemyError as e:
            logger.error(
                "Unexpected database error for %s: %s",
                self._model.__name__,
                str(e),
                extra={"doctype": self._model.__name__, "operation": "insert"},
            )
            raise RepositoryError(f"Insert failed: {e}") from e

        # Lifecycle hooks: after_save, after_insert
        await self._call_hook(controller, "after_save")
        await self._call_hook(controller, "after_insert")

        # Save child tables
        child_fields = self._get_child_table_fields()
        if child_fields:
            await self._save_child_tables(session, entity, child_fields)

        # Emit create event
        await self._emit_event("create", entity)

        return entity

    async def _update(
        self,
        session: AsyncSession,
        entity: T,
        controller: BaseController[T] | None,
        version: int | None = None,
    ) -> T:
        """Update an existing entity.

        Args:
            session: SQLAlchemy async session
            entity: The entity to update
            controller: Optional controller for lifecycle hooks
            version: Expected version for OCC

        Returns:
            The updated entity

        Raises:
            VersionConflictError: If version doesn't match
        """
        # Fetch values from linked documents
        await self._fetch_link_values(session, entity)

        # Lifecycle hooks: validate, before_save
        await self._call_hook(controller, "validate")
        await self._call_hook(controller, "before_save")

        # Prepare data (exclude child table fields and computed fields)
        exclude_fields = self._get_excluded_fields()
        data = entity.model_dump(exclude=exclude_fields)
        data["modified"] = datetime.now(UTC)

        # Build update statement
        stmt = update(self._table).where(self._table.c.name == entity.name)

        # OCC: Add version check if provided
        if version is not None:
            stmt = stmt.where(self._table.c._version == version)
            data["_version"] = version + 1

        stmt = stmt.values(**data)
        result = await session.execute(stmt)

        # OCC: Check if update succeeded
        # Access rowcount via getattr for type safety with async results
        rowcount: int = getattr(result, "rowcount", 0)
        if version is not None and rowcount == 0:
            raise VersionConflictError(
                entity_id=entity.name if entity.name else "unknown",  # type: ignore[arg-type]
                expected_version=version,
            )

        # Lifecycle hook: after_save
        await self._call_hook(controller, "after_save")

        # Update child tables (delete old, insert new)
        child_fields = self._get_child_table_fields()
        if child_fields and entity.id:
            # Delete old children
            await self._delete_child_tables(session, entity.id, child_fields)
            # Save new children
            await self._save_child_tables(session, entity, child_fields)

        # Emit update event
        await self._emit_event("update", entity)

        # Invalidate cache after update
        if self._cache and entity.id:
            await self._cache.delete(self._cache_key(entity.id))
            logger.debug("CACHE INVALIDATE %s[%s]", self._model.__name__, entity.id)

        return entity

    def _apply_filters(self, stmt: Any, filters: list[FilterSpec]) -> Any:
        """Apply filter conditions to a query.

        Args:
            stmt: SQLAlchemy statement
            filters: List of filter specs

        Returns:
            Modified statement
        """
        for f in filters:
            column = getattr(self._table.c, f.field)

            match f.operator:
                case FilterOperator.EQ:
                    stmt = stmt.where(column == f.value)
                case FilterOperator.NE:
                    stmt = stmt.where(column != f.value)
                case FilterOperator.LT:
                    stmt = stmt.where(column < f.value)
                case FilterOperator.LTE:
                    stmt = stmt.where(column <= f.value)
                case FilterOperator.GT:
                    stmt = stmt.where(column > f.value)
                case FilterOperator.GTE:
                    stmt = stmt.where(column >= f.value)
                case FilterOperator.IN:
                    stmt = stmt.where(column.in_(f.value))
                case FilterOperator.NOT_IN:
                    stmt = stmt.where(~column.in_(f.value))
                case FilterOperator.LIKE:
                    stmt = stmt.where(column.like(f.value))
                case FilterOperator.IS_NULL:
                    if f.value:
                        stmt = stmt.where(column.is_(None))
                    else:
                        stmt = stmt.where(column.is_not(None))

        return stmt

    def _apply_ordering(self, stmt: Any, order_by: list[OrderSpec]) -> Any:
        """Apply ordering to a query.

        Args:
            stmt: SQLAlchemy statement
            order_by: List of order specs

        Returns:
            Modified statement
        """
        for spec in order_by:
            column = getattr(self._table.c, spec.field)
            if spec.direction == OrderDirection.DESC:
                stmt = stmt.order_by(column.desc())
            else:
                stmt = stmt.order_by(column.asc())

        return stmt

    # ==========================================
    # Bulk Operations with RLS
    # ==========================================

    async def delete_many_for_user(
        self,
        session: AsyncSession,
        user: UserContext | None,
        filters: list[FilterSpec] | None = None,
        hard: bool = False,
    ) -> int:
        """Delete multiple entities with RLS filtering.

        IMPORTANT: RLS is applied so users can only delete their own documents.
        Admin/System users bypass RLS and can delete all matching documents.
        If user is None, no RLS is applied (for public DocTypes).

        Args:
            session: SQLAlchemy async session
            user: Current user context (None bypasses RLS for public access)
            filters: Additional filter conditions
            hard: If True, physically delete; otherwise soft-delete

        Returns:
            Number of documents deleted
        """
        from framework_m.core.rls import apply_rls_filters

        # Apply RLS filters based on user context
        rls_filters = await apply_rls_filters(
            user, self._model.get_doctype_name(), filters
        )

        if hard:
            # Physical delete
            from sqlalchemy import delete

            delete_stmt = delete(self._table)
            delete_stmt = self._apply_filters(delete_stmt, rls_filters)
            result = await session.execute(delete_stmt)
            return int(getattr(result, "rowcount", 0) or 0)
        else:
            # Soft delete - set deleted_at
            from datetime import datetime

            from sqlalchemy import update

            update_stmt = update(self._table).values(deleted_at=datetime.now())
            update_stmt = self._apply_filters(update_stmt, rls_filters)
            result = await session.execute(update_stmt)
            return int(getattr(result, "rowcount", 0) or 0)

    async def update_many_for_user(
        self,
        session: AsyncSession,
        user: UserContext | None,
        filters: list[FilterSpec] | None = None,
        data: dict[str, Any] | None = None,
    ) -> int:
        """Update multiple entities with RLS filtering.

        IMPORTANT: RLS is applied so users can only update their own documents.
        Admin/System users bypass RLS and can update all matching documents.
        If user is None, no RLS is applied (for public DocTypes).

        Args:
            session: SQLAlchemy async session
            user: Current user context (None bypasses RLS for public access)
            filters: Additional filter conditions
            data: Fields to update

        Returns:
            Number of documents updated
        """
        from datetime import datetime

        from sqlalchemy import update

        from framework_m.core.rls import apply_rls_filters

        if not data:
            return 0

        # Apply RLS filters based on user context
        rls_filters = await apply_rls_filters(
            user, self._model.get_doctype_name(), filters
        )

        # Add modified timestamp to update data
        update_data = {**data, "modified": datetime.now()}

        update_stmt = update(self._table).values(**update_data)
        update_stmt = self._apply_filters(update_stmt, rls_filters)
        result = await session.execute(update_stmt)
        return int(getattr(result, "rowcount", 0) or 0)

    # ==========================================
    # Field Exclusion Helpers
    # ==========================================

    def _get_excluded_fields(self) -> set[str]:
        """Get fields that should be excluded from database operations.

        This includes:
        - Child table fields (list[ChildDocType])
        - Computed fields (@computed_field properties)

        Returns:
            Set of field names to exclude from INSERT/UPDATE.
        """
        excluded: set[str] = set()

        # Exclude child table fields
        child_fields = self._get_child_table_fields()
        excluded.update(child_fields.keys())

        # Exclude computed fields (Pydantic's model_computed_fields)
        computed_fields = getattr(self._model, "model_computed_fields", {})
        excluded.update(computed_fields.keys())

        return excluded

    # ==========================================
    # Link Field Fetching
    # ==========================================

    async def _fetch_link_values(self, session: AsyncSession, entity: T) -> None:
        """Fetch values from linked documents based on fetch_from metadata.

        This method processes fields with json_schema_extra={"fetch_from": "link.field"}
        and auto-populates them from the linked document.

        Example:
            customer: UUID | None = Field(json_schema_extra={"link": "Customer"})
            customer_name: str | None = Field(
                json_schema_extra={"fetch_from": "customer.customer_name"}
            )

        Args:
            session: SQLAlchemy async session
            entity: The entity to populate fetch fields for
        """
        from sqlalchemy import select

        # Track which link fields we need to check for manual overrides
        # Key: fetch_field_name, Value: (link_field_name, link_value)
        fetch_fields_to_check: dict[str, tuple[str, UUID | None]] = {}

        # First pass: identify all fetch fields and their link sources
        for field_name, field_info in self._model.model_fields.items():
            if not field_info.json_schema_extra or not isinstance(
                field_info.json_schema_extra, dict
            ):
                continue

            fetch_from = field_info.json_schema_extra.get("fetch_from")
            if not fetch_from or not isinstance(fetch_from, str):
                continue

            # Parse fetch_from: "link_field.target_field"
            parts = fetch_from.split(".", 1)
            if len(parts) != 2:
                continue

            link_field_name, target_field_name = parts

            # Check if entity has the link field
            if not hasattr(entity, link_field_name):
                continue

            # Get link value
            link_value = getattr(entity, link_field_name, None)
            fetch_fields_to_check[field_name] = (link_field_name, link_value)

        # Second pass: fetch values
        for field_name, field_info in self._model.model_fields.items():
            if field_name not in fetch_fields_to_check:
                continue

            link_field_name, link_value = fetch_fields_to_check[field_name]

            if link_value is None:
                # No link set, set fetch field to None
                setattr(entity, field_name, None)
                continue

            # Get fetch_from metadata again
            if not field_info.json_schema_extra or not isinstance(
                field_info.json_schema_extra, dict
            ):
                continue

            fetch_from = field_info.json_schema_extra.get("fetch_from")
            if not fetch_from or not isinstance(fetch_from, str):
                continue

            parts = fetch_from.split(".", 1)
            if len(parts) != 2:
                continue

            _, target_field_name = parts

            # Get link metadata to find target DocType
            link_field_info = self._model.model_fields.get(link_field_name)
            if (
                not link_field_info
                or not link_field_info.json_schema_extra
                or not isinstance(link_field_info.json_schema_extra, dict)
            ):
                continue

            target_doctype = link_field_info.json_schema_extra.get("link")
            if not target_doctype or not isinstance(target_doctype, str):
                continue

            # Get target table from registry
            from framework_m.adapters.db.table_registry import TableRegistry

            table_registry = TableRegistry()
            try:
                target_table = table_registry.get_table(target_doctype)
            except KeyError:
                # Target table not registered, skip
                continue

            # Query target document
            stmt = select(target_table).where(target_table.c.id == link_value)
            result = await session.execute(stmt)
            target_row = result.first()

            if target_row is None:
                # Linked document not found, set to None
                setattr(entity, field_name, None)
                continue

            # Get target field value
            if not hasattr(target_table.c, target_field_name):
                # Target field doesn't exist, skip
                continue

            fetched_value = getattr(target_row, target_field_name, None)

            # Always update the fetch field to match the current link
            # This ensures fetched values stay in sync with link changes
            setattr(entity, field_name, fetched_value)

    # ==========================================
    # Child Table Operations
    # ==========================================

    def _get_child_table_fields(self) -> dict[str, type[BaseDocType]]:
        """Detect list[ChildDocType] fields in the model.

        Returns:
            Dict mapping field name to child DocType class.
            Only includes fields where the child has Meta.is_child = True.
        """
        child_fields: dict[str, type[BaseDocType]] = {}

        for field_name, field_info in self._model.model_fields.items():
            annotation = field_info.annotation
            if annotation is None:
                continue

            # Check if field is list[SomeType]
            origin = get_origin(annotation)
            if origin is list:
                args = get_args(annotation)
                if args:
                    child_type = args[0]
                    # Check if child_type is a BaseDocType subclass with is_child flag
                    if isinstance(child_type, type) and issubclass(
                        child_type, BaseDocType
                    ):
                        meta = getattr(child_type, "Meta", None)
                        if meta and getattr(meta, "is_child", False):
                            child_fields[field_name] = child_type

        return child_fields

    async def _save_child_tables(
        self,
        session: AsyncSession,
        parent: T,
        child_fields: dict[str, type[BaseDocType]],
    ) -> None:
        """Save child records for a parent document.

        Args:
            session: SQLAlchemy async session
            parent: Parent document
            child_fields: Dict of field_name -> child DocType class
        """
        from framework_m.adapters.db.table_registry import TableRegistry

        table_registry = TableRegistry()

        for field_name, child_model in child_fields.items():
            # Get children from parent
            children: list[BaseDocType] = getattr(parent, field_name, [])
            if not children:
                continue

            # Get child table
            child_table = table_registry.get_table(child_model.__name__)
            if child_table is None:
                logger.warning("Child table not found for %s", child_model.__name__)
                continue

            # Insert each child with parent reference
            for idx, child in enumerate(children, start=1):
                # Exclude computed fields from child data
                computed_fields = getattr(child_model, "model_computed_fields", {})
                exclude_fields = set(computed_fields.keys())
                child_data = child.model_dump(exclude=exclude_fields)

                # Add parent reference columns
                child_data["parent"] = str(parent.id)
                child_data["parenttype"] = self._model.__name__
                child_data["idx"] = idx
                child_data["modified"] = datetime.now(UTC)

                # Insert child
                stmt = child_table.insert().values(**child_data)
                await session.execute(stmt)

    async def _delete_child_tables(
        self,
        session: AsyncSession,
        parent_id: UUID,
        child_fields: dict[str, type[BaseDocType]],
    ) -> None:
        """Delete all child records for a parent document.

        Args:
            session: SQLAlchemy async session
            parent_id: Parent document ID
            child_fields: Dict of field_name -> child DocType class
        """
        from framework_m.adapters.db.table_registry import TableRegistry

        table_registry = TableRegistry()
        parent_id_str = str(parent_id)

        for _field_name, child_model in child_fields.items():
            # Get child table
            child_table = table_registry.get_table(child_model.__name__)
            if child_table is None:
                continue

            # Delete all children for this parent
            delete_stmt = sql_delete(child_table).where(
                child_table.c.parent == parent_id_str
            )
            await session.execute(delete_stmt)

    async def _load_child_tables(
        self,
        session: AsyncSession,
        parent: T,
        child_fields: dict[str, type[BaseDocType]],
    ) -> None:
        """Load child records for a parent document.

        Args:
            session: SQLAlchemy async session
            parent: Parent document to populate with children
            child_fields: Dict of field_name -> child DocType class
        """
        from framework_m.adapters.db.table_registry import TableRegistry

        table_registry = TableRegistry()

        for field_name, child_model in child_fields.items():
            # Get child table
            child_table = table_registry.get_table(child_model.__name__)
            if child_table is None:
                continue

            # Load children for this parent
            children_by_parent = await self.load_children_for_parents(
                session,
                [parent.id],
                child_table,
                child_model,  # type: ignore[arg-type]
            )

            # Populate the field
            parent_id_str = str(parent.id)
            children = children_by_parent.get(parent_id_str, [])
            setattr(parent, field_name, children)

    # Child Table Loading (select_in_loading)
    # ==========================================

    async def load_children_for_parents(
        self,
        session: AsyncSession,
        parent_ids: list[Any],
        child_table: Table,
        child_model: type[T],
    ) -> dict[str, list[T]]:
        """Load child table rows for multiple parents using select_in_loading.

        This method efficiently loads all children for multiple parents in a
        single query using WHERE parent IN (...), avoiding the N+1 query problem.

        Args:
            session: SQLAlchemy async session
            parent_ids: List of parent document IDs
            child_table: SQLAlchemy Table for child DocType
            child_model: Child DocType class

        Returns:
            Dict mapping parent_id (str) to list of child instances,
            ordered by idx within each parent.
        """
        if not parent_ids:
            return {}

        from sqlalchemy import select

        # Convert UUIDs to strings for parent column matching
        parent_id_strs = [str(pid) for pid in parent_ids]

        # Build query with IN clause (select_in_loading pattern)
        stmt = (
            select(child_table)
            .where(child_table.c.parent.in_(parent_id_strs))
            .order_by(child_table.c.parent, child_table.c.idx)
        )

        result = await session.execute(stmt)
        rows = result.fetchall()

        # Group children by parent
        children_by_parent: dict[str, list[T]] = {}
        for row in rows:
            row_dict = dict(row._mapping)
            parent_id = row_dict.pop("parent", None)
            # Remove parent reference columns (not part of child model)
            row_dict.pop("parentfield", None)
            row_dict.pop("parenttype", None)
            row_dict.pop("idx", None)

            if parent_id is not None:
                parent_id = str(parent_id)
                if parent_id not in children_by_parent:
                    children_by_parent[parent_id] = []
                # Create child model instance
                child_instance = child_model(**row_dict)
                children_by_parent[parent_id].append(child_instance)

        return children_by_parent


__all__ = ["GenericRepository", "VersionConflictError"]
