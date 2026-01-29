"""Unit of Work - Transaction management context manager.

This module provides the UnitOfWork class for managing database transactions
in a clean, consistent way. The UnitOfWork pattern ensures that all
operations within a business transaction are committed or rolled back together.

Key principles:
- Session is created on entry, closed on exit
- Exceptions trigger automatic rollback
- Caller explicitly calls commit() when ready
- Session is NOT tied to HTTP request lifecycle

Note:
    This module uses abstract types (Any) for session to keep core
    independent of SQLAlchemy. Concrete implementations bind the
    session_factory to return the appropriate session type.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from collections.abc import Callable


class SessionProtocol(Protocol):
    """Abstract session protocol for database operations.

    Any session implementation (SQLAlchemy, MongoDB, etc.) must support
    these async methods.
    """

    async def commit(self) -> None:
        """Commit the current transaction."""
        ...

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        ...

    async def close(self) -> None:
        """Close the session."""
        ...


class UnitOfWork:
    """Context manager for database transaction management.

    Provides a clean interface for working with database sessions:
    - Creates session on entry
    - Rolls back on exception
    - Closes session on exit

    The caller is responsible for calling commit() explicitly when
    all operations have succeeded. This allows for fine-grained control
    over transaction boundaries.

    Example:
        >>> async with UnitOfWork(session_factory) as uow:
        ...     saved = await repo.save(uow.session, entity)
        ...     await uow.commit()

    Note:
        Do NOT tie UnitOfWork lifecycle to HTTP request lifecycle.
        Create UnitOfWork instances for specific business transactions.
    """

    def __init__(self, session_factory: Callable[[], Any]) -> None:
        """Initialize the Unit of Work.

        Args:
            session_factory: A callable that returns a new session.
                             The session must implement SessionProtocol.
        """
        self._session_factory = session_factory
        self._session: Any = None

    @property
    def session(self) -> Any:
        """Get the current session.

        Returns:
            The active session (implements SessionProtocol)

        Raises:
            RuntimeError: If accessed before entering the context
        """
        if self._session is None:
            raise RuntimeError("UnitOfWork not entered")
        return self._session

    async def __aenter__(self) -> UnitOfWork:
        """Enter the context and create a new session.

        Returns:
            Self for use in the async with statement
        """
        self._session = self._session_factory()
        return self

    async def commit(self) -> None:
        """Commit the current transaction.

        Should be called explicitly when all operations have succeeded.
        If not called, changes will be rolled back on exit.
        """
        await self.session.commit()

    async def rollback(self) -> None:
        """Explicitly rollback the current transaction.

        Usually not needed as rollback happens automatically on exception.
        """
        await self.session.rollback()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit the context, handling cleanup.

        If an exception occurred, rolls back the transaction.
        Always closes the session.

        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Traceback if an exception occurred
        """
        if exc_type is not None:
            await self.session.rollback()
        await self.session.close()


__all__ = ["UnitOfWork"]
