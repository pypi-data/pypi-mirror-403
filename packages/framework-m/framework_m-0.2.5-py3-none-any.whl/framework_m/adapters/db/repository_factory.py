"""Repository Factory - Creates repositories for DocTypes.

This module provides the RepositoryFactory class that manages the creation
of repository instances for DocTypes. It supports custom repository overrides
for Virtual DocTypes backed by non-SQL data sources.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import MetaData

if TYPE_CHECKING:
    from framework_m.adapters.db.generic_repository import GenericRepository
    from framework_m.adapters.db.session import SessionFactory
    from framework_m.core.domain.base_doctype import BaseDocType


class RepositoryFactory:
    """Factory for creating and caching repository instances.

    Manages the mapping between DocTypes and their repository implementations.
    Supports custom repository overrides for Virtual DocTypes.

    Unlike a singleton, this factory is instantiated once in app lifespan
    and stored in app.state for DI-based access.

    Example:
        >>> factory = RepositoryFactory(metadata, session_factory)
        >>> repo = factory.get_repository(Customer)
        >>> async with factory.session_factory.get_session() as session:
        ...     items = await repo.list_entities(session, filters={})
    """

    def __init__(
        self,
        metadata: MetaData,
        session_factory: SessionFactory,
    ) -> None:
        """Initialize the repository factory.

        Args:
            metadata: SQLAlchemy MetaData containing table definitions
            session_factory: Factory for creating database sessions
        """
        self._metadata = metadata
        self._session_factory = session_factory
        self._repos: dict[str, GenericRepository[Any]] = {}
        self._overrides: dict[str, type[Any]] = {}

    @property
    def session_factory(self) -> SessionFactory:
        """Get the session factory.

        Returns:
            The SessionFactory for creating database sessions
        """
        return self._session_factory

    @property
    def metadata(self) -> MetaData:
        """Get the SQLAlchemy metadata.

        Returns:
            The MetaData containing table definitions
        """
        return self._metadata

    def register_override(self, doctype_name: str, repository_class: type[Any]) -> None:
        """Register a custom repository class for a DocType.

        Use this for Virtual DocTypes that need custom data sources
        (files, APIs, NoSQL databases, etc.).

        Args:
            doctype_name: Name of the DocType
            repository_class: Repository class implementing RepositoryProtocol
        """
        self._overrides[doctype_name] = repository_class

    def has_override(self, doctype_name: str) -> bool:
        """Check if a DocType has a custom repository override.

        Args:
            doctype_name: Name of the DocType

        Returns:
            True if a custom repository is registered
        """
        return doctype_name in self._overrides

    def get_override(self, doctype_name: str) -> type[Any]:
        """Get the custom repository class for a DocType.

        Args:
            doctype_name: Name of the DocType

        Returns:
            The repository class

        Raises:
            KeyError: If no override is registered for this DocType
        """
        if doctype_name not in self._overrides:
            raise KeyError(f"No repository override for DocType '{doctype_name}'")
        return self._overrides[doctype_name]

    def get_repository(
        self,
        doctype_class: type[BaseDocType],
    ) -> GenericRepository[Any] | None:
        """Get or create a cached repository for a DocType.

        Creates the repository on first access and caches it for
        subsequent calls. Returns None if the table doesn't exist.

        Args:
            doctype_class: The DocType class

        Returns:
            Cached GenericRepository instance, or None if table not found
        """
        doctype_name = doctype_class.__name__
        table_name = self._get_table_name(doctype_class)

        # Return cached repository if exists
        if doctype_name in self._repos:
            return self._repos[doctype_name]

        # Check for custom override
        if self.has_override(doctype_name):
            repo_class = self._overrides[doctype_name]
            override_repo: GenericRepository[Any] = repo_class()
            self._repos[doctype_name] = override_repo
            return override_repo

        # Get table from metadata
        table = self._metadata.tables.get(table_name)
        if table is None:
            return None

        # Import here to avoid circular imports
        from framework_m.adapters.db.generic_repository import GenericRepository
        from framework_m.core.registry import MetaRegistry

        meta_registry = MetaRegistry.get_instance()
        controller_class = meta_registry.get_controller(doctype_name)

        # Create and cache repository
        repo: GenericRepository[Any] = GenericRepository(
            model=doctype_class,
            table=table,
            controller_class=controller_class,
        )
        self._repos[doctype_name] = repo
        return repo

    def _get_table_name(self, doctype_class: type[BaseDocType]) -> str:
        """Get the table name for a DocType class.

        Uses __tablename__ if defined, otherwise lowercase class name.
        This matches the logic in SchemaMapper._get_table_name.

        Args:
            doctype_class: The DocType class

        Returns:
            Table name string
        """
        # Check for explicit __tablename__ attribute (same as SchemaMapper)
        if hasattr(doctype_class, "__tablename__") and doctype_class.__tablename__:
            return str(doctype_class.__tablename__)
        # Default: lowercase class name
        return doctype_class.__name__.lower()

    def list_overrides(self) -> list[str]:
        """List all DocTypes with custom repository overrides.

        Returns:
            List of DocType names with registered overrides
        """
        return list(self._overrides.keys())

    def list_cached_repositories(self) -> list[str]:
        """List all DocTypes with cached repository instances.

        Returns:
            List of DocType names with cached repositories
        """
        return list(self._repos.keys())

    def clear_cache(self) -> None:
        """Clear all cached repository instances.

        Use this for testing or when tables are modified.
        """
        self._repos.clear()

    def reset(self) -> None:
        """Clear all overrides and cached repositories.

        Use this for testing to reset the factory state.
        """
        self._overrides.clear()
        self._repos.clear()


__all__ = ["RepositoryFactory"]
