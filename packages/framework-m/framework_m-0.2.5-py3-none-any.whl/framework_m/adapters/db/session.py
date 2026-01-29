"""Session Factory - Manages async database sessions.

This module provides the SessionFactory class that creates and manages
SQLAlchemy async sessions for database operations. It supports multiple
binds for different databases.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, ClassVar

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

if TYPE_CHECKING:
    from framework_m.adapters.db.connection import ConnectionFactory


class SessionFactory:
    """Factory for creating SQLAlchemy async sessions.

    Provides centralized session management with support for multiple
    database binds. Uses singleton pattern.

    Example:
        >>> session_factory = SessionFactory()
        >>> session_factory.configure(connection_factory)
        >>> async with session_factory.get_session() as session:
        ...     result = await session.execute(query)
    """

    _instance: ClassVar[SessionFactory | None] = None
    _session_makers: dict[str, async_sessionmaker[AsyncSession]]
    _configured: bool

    def __new__(cls) -> SessionFactory:
        """Implement singleton pattern.

        Returns:
            The single SessionFactory instance
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._session_makers = {}
            cls._instance._configured = False
        return cls._instance

    @property
    def is_configured(self) -> bool:
        """Check if the factory is configured.

        Returns:
            True if configure() has been called
        """
        return self._configured

    def configure(self, connection_factory: ConnectionFactory) -> None:
        """Configure session makers from connection factory.

        Creates a session maker for each engine in the connection factory.

        Args:
            connection_factory: The ConnectionFactory with configured engines
        """
        for bind_name in connection_factory.list_engines():
            engine = connection_factory.get_engine(bind_name)
            self._session_makers[bind_name] = async_sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
        self._configured = True

    @asynccontextmanager
    async def get_session(
        self, bind: str = "default"
    ) -> AsyncGenerator[AsyncSession, None]:
        """Get an async session for a database bind.

        This is an async context manager that yields a session and
        handles commit/rollback on exit.

        Args:
            bind: Name of the database bind (default: "default")

        Yields:
            An AsyncSession for the specified bind

        Raises:
            KeyError: If the bind is not configured
        """
        if bind not in self._session_makers:
            raise KeyError(f"Session maker for bind '{bind}' is not configured")

        session_maker = self._session_makers[bind]
        async with session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    def reset(self) -> None:
        """Clear all configured session makers.

        Use this for testing to reset the singleton state.
        """
        self._session_makers.clear()
        self._configured = False


__all__ = ["SessionFactory"]
