"""Repository Protocol - Core interface for data access.

This module defines the RepositoryProtocol which is the primary port for
all data persistence operations in the hexagonal architecture.

Implementations (adapters) include:
- SQLAlchemyRepository: For SQL databases via SQLAlchemy
- Custom repositories: For Virtual DocTypes (APIs, NoSQL, etc.)
"""

from collections.abc import Sequence
from enum import StrEnum
from typing import Any, Protocol, TypeVar
from uuid import UUID

from pydantic import BaseModel, computed_field

T = TypeVar("T")


class FilterOperator(StrEnum):
    """Operators for filtering queries.

    Used in FilterSpec to specify how field values should be compared.
    """

    EQ = "eq"
    NE = "ne"
    LT = "lt"
    LTE = "lte"
    GT = "gt"
    GTE = "gte"
    IN = "in"
    NOT_IN = "not_in"
    LIKE = "like"
    IS_NULL = "is_null"


class FilterSpec(BaseModel):
    """Specification for filtering query results.

    Defines a single filter condition with field, operator, and value.
    Multiple FilterSpecs can be combined for complex queries.

    Example:
        filter = FilterSpec(field="status", operator=FilterOperator.EQ, value="active")
    """

    field: str
    operator: FilterOperator
    value: Any


class OrderDirection(StrEnum):
    """Direction for sorting results."""

    ASC = "asc"
    DESC = "desc"


class OrderSpec(BaseModel):
    """Specification for ordering query results.

    Defines sorting by field and direction.
    Multiple OrderSpecs can be combined for multi-column sorting.

    Example:
        order = OrderSpec(field="created_at", direction=OrderDirection.DESC)
    """

    field: str
    direction: OrderDirection = OrderDirection.ASC


class PaginatedResult[T](BaseModel):
    """Container for paginated query results.

    Wraps a list of items with pagination metadata.
    Use has_more to determine if more pages exist.

    Attributes:
        items: The current page of results
        total: Total count of all matching items
        limit: Maximum items per page
        offset: Number of items skipped (for pagination)
        has_more: Computed property indicating if more items exist
    """

    items: Sequence[T]
    total: int
    limit: int
    offset: int

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_more(self) -> bool:
        """Check if more items exist beyond current page."""
        return self.offset + len(self.items) < self.total


class RepositoryProtocol[T](Protocol):
    """Protocol defining the contract for data repositories.

    This is the primary port for data persistence in the hexagonal architecture.
    All repository adapters must implement this interface.

    Type parameter T represents the entity type being managed.

    Features:
    - Generic CRUD operations (get, save, delete)
    - Existence and count queries
    - Paginated listing with filtering and sorting
    - Bulk operations for performance
    - Optional Optimistic Concurrency Control (OCC) via version parameter

    Example implementation:
        class SQLAlchemyRepository(RepositoryProtocol[User]):
            async def get(self, id: UUID) -> User | None:
                ...
    """

    async def get(self, id: UUID) -> T | None:
        """Retrieve an entity by its unique identifier.

        Args:
            id: The unique identifier of the entity

        Returns:
            The entity if found, None otherwise
        """
        ...

    async def save(self, entity: T, version: int | None = None) -> T:
        """Persist an entity (insert or update).

        If the entity has an id, it will be updated. Otherwise, inserted.
        For Optimistic Concurrency Control, pass the expected version.

        Args:
            entity: The entity to save
            version: Expected version for OCC (raises VersionConflictError if mismatch)

        Returns:
            The saved entity with updated fields (id, modified, version, etc.)

        Raises:
            VersionConflictError: If version doesn't match (OCC)
        """
        ...

    async def delete(self, id: UUID) -> None:
        """Delete an entity by its unique identifier.

        Args:
            id: The unique identifier of the entity to delete

        Raises:
            EntityNotFoundError: If entity doesn't exist
        """
        ...

    async def exists(self, id: UUID) -> bool:
        """Check if an entity exists by its identifier.

        More efficient than get() when you only need existence check.

        Args:
            id: The unique identifier to check

        Returns:
            True if entity exists, False otherwise
        """
        ...

    async def count(self, filters: list[FilterSpec] | None = None) -> int:
        """Count entities matching the given filters.

        Args:
            filters: Optional list of filter conditions

        Returns:
            Count of matching entities
        """
        ...

    async def list(
        self,
        filters: list[FilterSpec] | None = None,
        order_by: list[OrderSpec] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> PaginatedResult[T]:
        """List entities with filtering, sorting, and pagination.

        Args:
            filters: Optional list of filter conditions
            order_by: Optional list of sort specifications
            limit: Maximum number of items to return (default: 20)
            offset: Number of items to skip (default: 0)

        Returns:
            PaginatedResult containing items and pagination metadata
        """
        ...

    async def bulk_save(self, entities: Sequence[T]) -> Sequence[T]:
        """Save multiple entities in a single operation.

        More efficient than calling save() multiple times.
        All entities are saved within a single transaction.

        Args:
            entities: List of entities to save

        Returns:
            List of saved entities with updated fields
        """
        ...


__all__ = [
    "FilterOperator",
    "FilterSpec",
    "OrderDirection",
    "OrderSpec",
    "PaginatedResult",
    "RepositoryProtocol",
]
