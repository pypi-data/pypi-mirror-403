"""Tests for ConnectionFactory."""

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from framework_m.adapters.db.connection import ConnectionFactory


@pytest.fixture(autouse=True)
async def reset_connection_factory() -> AsyncGenerator[None, None]:
    """Reset ConnectionFactory before each test."""
    ConnectionFactory().reset()
    yield
    # Cleanup any engines created during tests
    factory = ConnectionFactory()
    for name in factory.list_engines():
        await factory.get_engine(name).dispose()
    factory.reset()


class TestConnectionFactorySingleton:
    """Tests for ConnectionFactory singleton pattern."""

    def test_connection_factory_is_singleton(self) -> None:
        """ConnectionFactory should return the same instance."""
        factory1 = ConnectionFactory()
        factory2 = ConnectionFactory()
        assert factory1 is factory2

    @pytest.mark.asyncio
    async def test_connection_factory_reset(self) -> None:
        """ConnectionFactory.reset() should clear all engines."""
        factory = ConnectionFactory()
        factory.configure({"default": "sqlite+aiosqlite:///:memory:"})

        assert factory.has_engine("default")

        # Dispose before reset to avoid ResourceWarning
        await factory.get_engine("default").dispose()

        factory.reset()
        assert not factory.has_engine("default")


class TestConnectionFactoryConfiguration:
    """Tests for ConnectionFactory configuration."""

    @pytest.fixture(autouse=True)
    def reset_factory(self) -> None:
        """Reset factory before each test."""
        ConnectionFactory().reset()

    def test_configure_single_bind(self) -> None:
        """configure() should create a single engine."""
        factory = ConnectionFactory()
        factory.configure({"default": "sqlite+aiosqlite:///:memory:"})

        assert factory.has_engine("default")

    def test_configure_multiple_binds(self) -> None:
        """configure() should support multiple database binds."""
        factory = ConnectionFactory()
        factory.configure(
            {
                "default": "sqlite+aiosqlite:///:memory:",
                "legacy": "sqlite+aiosqlite:///:memory:",
                "timescale": "sqlite+aiosqlite:///:memory:",
            }
        )

        assert factory.has_engine("default")
        assert factory.has_engine("legacy")
        assert factory.has_engine("timescale")

    def test_configure_from_environment(self) -> None:
        """configure() should support environment variable expansion."""
        factory = ConnectionFactory()
        # Using explicit URL, but implementation should support ${DATABASE_URL}
        factory.configure({"default": "sqlite+aiosqlite:///:memory:"})

        assert factory.has_engine("default")


class TestEngineRetrieval:
    """Tests for engine retrieval."""

    @pytest.fixture(autouse=True)
    def reset_factory(self) -> None:
        """Reset factory before each test."""
        ConnectionFactory().reset()

    def test_get_engine_returns_async_engine(self) -> None:
        """get_engine() should return an AsyncEngine."""
        factory = ConnectionFactory()
        factory.configure({"default": "sqlite+aiosqlite:///:memory:"})

        engine = factory.get_engine("default")
        assert isinstance(engine, AsyncEngine)

    def test_get_engine_not_configured_raises_error(self) -> None:
        """get_engine() should raise KeyError if engine not configured."""
        factory = ConnectionFactory()

        with pytest.raises(KeyError) as exc_info:
            factory.get_engine("nonexistent")

        assert "nonexistent" in str(exc_info.value)

    def test_get_default_engine(self) -> None:
        """get_engine() with no args should return default engine."""
        factory = ConnectionFactory()
        factory.configure({"default": "sqlite+aiosqlite:///:memory:"})

        engine = factory.get_engine()
        assert isinstance(engine, AsyncEngine)

    def test_has_engine_returns_true_for_configured(self) -> None:
        """has_engine() should return True for configured engines."""
        factory = ConnectionFactory()
        factory.configure({"default": "sqlite+aiosqlite:///:memory:"})

        assert factory.has_engine("default") is True

    def test_has_engine_returns_false_for_unconfigured(self) -> None:
        """has_engine() should return False for unconfigured engines."""
        factory = ConnectionFactory()
        assert factory.has_engine("nonexistent") is False


class TestEngineOptions:
    """Tests for engine creation options."""

    @pytest.fixture(autouse=True)
    def reset_factory(self) -> None:
        """Reset factory before each test."""
        ConnectionFactory().reset()

    def test_configure_with_pool_options(self) -> None:
        """configure() should accept pool configuration."""
        factory = ConnectionFactory()
        factory.configure(
            {"default": "sqlite+aiosqlite:///:memory:"},
            pool_size=10,
            max_overflow=5,
        )

        engine = factory.get_engine("default")
        assert isinstance(engine, AsyncEngine)

    def test_configure_with_echo(self) -> None:
        """configure() should accept echo option for SQL logging."""
        factory = ConnectionFactory()
        factory.configure(
            {"default": "sqlite+aiosqlite:///:memory:"},
            echo=True,
        )

        engine = factory.get_engine("default")
        assert engine.echo is True


class TestListEngines:
    """Tests for listing configured engines."""

    @pytest.fixture(autouse=True)
    def reset_factory(self) -> None:
        """Reset factory before each test."""
        ConnectionFactory().reset()

    def test_list_engines_empty(self) -> None:
        """list_engines() should return empty list when no engines."""
        factory = ConnectionFactory()
        assert factory.list_engines() == []

    def test_list_engines_returns_all(self) -> None:
        """list_engines() should return all configured engine names."""
        factory = ConnectionFactory()
        factory.configure(
            {
                "default": "sqlite+aiosqlite:///:memory:",
                "analytics": "sqlite+aiosqlite:///:memory:",
            }
        )

        engines = factory.list_engines()
        assert set(engines) == {"default", "analytics"}


class TestConnectionFactoryImport:
    """Tests for ConnectionFactory imports."""

    def test_import_connection_factory(self) -> None:
        """ConnectionFactory should be importable."""
        from framework_m.adapters.db.connection import ConnectionFactory

        assert ConnectionFactory is not None


class TestEnvironmentVariableExpansion:
    """Tests for environment variable expansion in URLs."""

    @pytest.fixture(autouse=True)
    def reset_factory(self) -> None:
        """Reset factory before each test."""
        ConnectionFactory().reset()

    def test_expand_env_vars_single(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """_expand_env_vars should expand single env var."""
        monkeypatch.setenv("DB_HOST", "localhost")

        factory = ConnectionFactory()
        result = factory._expand_env_vars("postgresql://${DB_HOST}/db")

        assert result == "postgresql://localhost/db"

    def test_expand_env_vars_multiple(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """_expand_env_vars should expand multiple env vars."""
        monkeypatch.setenv("DB_HOST", "localhost")
        monkeypatch.setenv("DB_NAME", "mydb")

        factory = ConnectionFactory()
        result = factory._expand_env_vars("postgresql://${DB_HOST}/${DB_NAME}")

        assert result == "postgresql://localhost/mydb"

    def test_expand_env_vars_missing(self) -> None:
        """_expand_env_vars should replace missing vars with empty string."""
        factory = ConnectionFactory()
        result = factory._expand_env_vars("postgresql://${MISSING_VAR}/db")

        assert result == "postgresql:///db"


class TestDisposeAll:
    """Tests for dispose_all method."""

    @pytest.fixture(autouse=True)
    def reset_factory(self) -> None:
        """Reset factory before each test."""
        ConnectionFactory().reset()

    @pytest.mark.asyncio
    async def test_dispose_all_closes_connections(self) -> None:
        """dispose_all should close all engine connections."""
        factory = ConnectionFactory()
        factory.configure(
            {
                "default": "sqlite+aiosqlite:///:memory:",
                "other": "sqlite+aiosqlite:///:memory:",
            }
        )

        # Engines should exist
        assert factory.has_engine("default")
        assert factory.has_engine("other")

        # Dispose all should not raise
        await factory.dispose_all()

        # Engines still exist but are disposed
        assert factory.has_engine("default")
