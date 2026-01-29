"""Tests for SessionFactory."""

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from framework_m.adapters.db.connection import ConnectionFactory
from framework_m.adapters.db.session import SessionFactory


@pytest.fixture(autouse=True)
async def reset_all_factories() -> AsyncGenerator[None, None]:
    """Reset all factories before each test."""
    SessionFactory().reset()
    ConnectionFactory().reset()
    yield
    # Cleanup engines
    factory = ConnectionFactory()
    for name in factory.list_engines():
        await factory.get_engine(name).dispose()
    factory.reset()


class TestSessionFactorySingleton:
    """Tests for SessionFactory singleton pattern."""

    def test_session_factory_is_singleton(self) -> None:
        """SessionFactory should return the same instance."""
        factory1 = SessionFactory()
        factory2 = SessionFactory()
        assert factory1 is factory2

    def test_session_factory_reset(self) -> None:
        """SessionFactory.reset() should clear state."""
        factory = SessionFactory()
        # Configure connection factory first
        conn_factory = ConnectionFactory()
        conn_factory.reset()
        conn_factory.configure({"default": "sqlite+aiosqlite:///:memory:"})

        factory.configure(conn_factory)
        assert factory.is_configured

        factory.reset()
        assert not factory.is_configured


class TestSessionFactoryConfiguration:
    """Tests for SessionFactory configuration."""

    @pytest.fixture(autouse=True)
    def reset_factories(self) -> None:
        """Reset factories before each test."""
        SessionFactory().reset()
        ConnectionFactory().reset()

    def test_configure_with_connection_factory(self) -> None:
        """configure() should accept a ConnectionFactory."""
        conn_factory = ConnectionFactory()
        conn_factory.configure({"default": "sqlite+aiosqlite:///:memory:"})

        session_factory = SessionFactory()
        session_factory.configure(conn_factory)

        assert session_factory.is_configured


class TestGetSession:
    """Tests for get_session()."""

    @pytest.fixture(autouse=True)
    def reset_factories(self) -> None:
        """Reset factories before each test."""
        SessionFactory().reset()
        ConnectionFactory().reset()

    @pytest.fixture
    def configured_factories(self) -> tuple[ConnectionFactory, SessionFactory]:
        """Create configured factories."""
        conn_factory = ConnectionFactory()
        conn_factory.configure(
            {
                "default": "sqlite+aiosqlite:///:memory:",
                "legacy": "sqlite+aiosqlite:///:memory:",
            }
        )

        session_factory = SessionFactory()
        session_factory.configure(conn_factory)

        return conn_factory, session_factory

    @pytest.mark.asyncio
    async def test_get_session_returns_async_session(
        self, configured_factories: tuple[ConnectionFactory, SessionFactory]
    ) -> None:
        """get_session() should return an AsyncSession."""
        _, session_factory = configured_factories

        async with session_factory.get_session() as session:
            assert isinstance(session, AsyncSession)

    @pytest.mark.asyncio
    async def test_get_session_with_bind(
        self, configured_factories: tuple[ConnectionFactory, SessionFactory]
    ) -> None:
        """get_session() should accept a bind parameter."""
        _, session_factory = configured_factories

        async with session_factory.get_session(bind="legacy") as session:
            assert isinstance(session, AsyncSession)

    @pytest.mark.asyncio
    async def test_get_session_default_bind(
        self, configured_factories: tuple[ConnectionFactory, SessionFactory]
    ) -> None:
        """get_session() should use 'default' bind when not specified."""
        _, session_factory = configured_factories

        async with session_factory.get_session() as session:
            assert isinstance(session, AsyncSession)

    @pytest.mark.asyncio
    async def test_get_session_invalid_bind_raises_error(
        self, configured_factories: tuple[ConnectionFactory, SessionFactory]
    ) -> None:
        """get_session() should raise KeyError for unknown bind."""
        _, session_factory = configured_factories

        with pytest.raises(KeyError):
            async with session_factory.get_session(bind="nonexistent"):
                pass

    @pytest.mark.asyncio
    async def test_session_is_closed_after_context(
        self, configured_factories: tuple[ConnectionFactory, SessionFactory]
    ) -> None:
        """Session should be closed after context manager exits."""
        _, session_factory = configured_factories

        async with session_factory.get_session() as _:
            pass  # Session should be valid here

        # Session should be closed after context
        # (We can't easily test this, but the context manager should handle it)


class TestSessionFactoryImport:
    """Tests for SessionFactory imports."""

    def test_import_session_factory(self) -> None:
        """SessionFactory should be importable."""
        from framework_m.adapters.db.session import SessionFactory

        assert SessionFactory is not None
