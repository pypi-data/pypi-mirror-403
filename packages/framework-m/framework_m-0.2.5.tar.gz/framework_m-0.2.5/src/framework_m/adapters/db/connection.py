"""Connection Factory - Manages database connections and async engines.

This module provides the ConnectionFactory class that manages SQLAlchemy
async engines for multiple database binds. It supports:

- Multiple database bindings (default, legacy, timescale, etc.)
- Async engines for PostgreSQL and SQLite
- Connection pool configuration
- Environment variable expansion
"""

from __future__ import annotations

import os
from typing import Any, ClassVar

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


class ConnectionFactory:
    """Factory for creating and managing SQLAlchemy async engines.

    Provides centralized management of database connections with support
    for multiple binds (e.g., default, legacy, analytics). Uses singleton pattern.

    Example:
        >>> factory = ConnectionFactory()
        >>> factory.configure({
        ...     "default": "postgresql+asyncpg://user:pass@localhost/db",
        ...     "analytics": "postgresql+asyncpg://user:pass@localhost/analytics",
        ... })
        >>> engine = factory.get_engine("default")
    """

    _instance: ClassVar[ConnectionFactory | None] = None
    _engines: dict[str, AsyncEngine]
    _configured: bool

    def __new__(cls) -> ConnectionFactory:
        """Implement singleton pattern.

        Returns:
            The single ConnectionFactory instance
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._engines = {}
            cls._instance._configured = False
        return cls._instance

    def configure(
        self,
        db_binds: dict[str, str],
        *,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 1800,
        pool_pre_ping: bool = True,
        echo: bool = False,
    ) -> None:
        """Configure database connections from bind mapping.

        Args:
            db_binds: Mapping of bind name to database URL.
                      URLs can contain environment variables like ${DATABASE_URL}
            pool_size: The number of connections to keep in the pool
            max_overflow: Max connections allowed beyond pool_size
            pool_timeout: Seconds to wait for a connection from pool
            pool_recycle: Seconds after which to recycle connections
            pool_pre_ping: Enable connection health check before use
            echo: Enable SQL query logging
        """
        for bind_name, url in db_binds.items():
            # Expand environment variables in URL
            expanded_url = self._expand_env_vars(url)

            # Create engine with appropriate options
            engine_kwargs: dict[str, Any] = {"echo": echo}

            # SQLite doesn't support pool configuration
            if not expanded_url.startswith("sqlite"):
                engine_kwargs.update(
                    {
                        "pool_size": pool_size,
                        "max_overflow": max_overflow,
                        "pool_timeout": pool_timeout,
                        "pool_recycle": pool_recycle,
                        "pool_pre_ping": pool_pre_ping,
                    }
                )

            self._engines[bind_name] = create_async_engine(
                expanded_url,
                **engine_kwargs,
            )

        self._configured = True

    def get_engine(self, bind: str = "default") -> AsyncEngine:
        """Get the async engine for a database bind.

        Args:
            bind: Name of the database bind (default: "default")

        Returns:
            The AsyncEngine for the specified bind

        Raises:
            KeyError: If the bind is not configured
        """
        if bind not in self._engines:
            raise KeyError(f"Database bind '{bind}' is not configured")
        return self._engines[bind]

    def has_engine(self, bind: str) -> bool:
        """Check if an engine is configured for a bind.

        Args:
            bind: Name of the database bind

        Returns:
            True if an engine exists for this bind
        """
        return bind in self._engines

    def list_engines(self) -> list[str]:
        """List all configured engine bind names.

        Returns:
            List of configured bind names
        """
        return list(self._engines.keys())

    async def dispose_all(self) -> None:
        """Dispose all engines and close connections.

        Should be called during application shutdown.
        """
        for engine in self._engines.values():
            await engine.dispose()

    def reset(self) -> None:
        """Clear all configured engines.

        Use this for testing to reset the singleton state.
        Note: This does NOT dispose connections. Call dispose_all() first
        in production scenarios.
        """
        self._engines.clear()
        self._configured = False

    def _expand_env_vars(self, url: str) -> str:
        """Expand environment variables in a URL.

        Supports ${VAR_NAME} syntax.

        Args:
            url: URL that may contain environment variables

        Returns:
            URL with environment variables expanded
        """
        # Handle ${VAR} syntax
        result = url
        while "${" in result:
            start = result.index("${")
            end = result.index("}", start)
            var_name = result[start + 2 : end]
            var_value = os.environ.get(var_name, "")
            result = result[:start] + var_value + result[end + 1 :]
        return result


__all__ = ["ConnectionFactory"]
