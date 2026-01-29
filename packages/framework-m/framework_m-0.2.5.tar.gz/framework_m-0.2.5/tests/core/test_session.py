"""Tests for Session Management.

TDD: This test file is created BEFORE the implementation.

Tests cover:
- SessionProtocol interface
- Session DocType
- SessionManager service
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

# =============================================================================
# Test: SessionProtocol Import
# =============================================================================


class TestSessionProtocolImport:
    """Tests for SessionProtocol interface import."""

    def test_import_session_protocol(self) -> None:
        """SessionProtocol should be importable."""
        from framework_m.core.interfaces.session import SessionProtocol

        assert SessionProtocol is not None

    def test_import_session_data(self) -> None:
        """SessionData model should be importable."""
        from framework_m.core.interfaces.session import SessionData

        assert SessionData is not None


# =============================================================================
# Test: Session DocType
# =============================================================================


class TestSessionDoctypeImport:
    """Tests for Session DocType import."""

    def test_import_session_doctype(self) -> None:
        """Session DocType should be importable."""
        from framework_m.core.doctypes.session import Session

        assert Session is not None


class TestSessionDoctypeCreation:
    """Tests for Session DocType creation."""

    def test_create_session_with_required_fields(self) -> None:
        """Session should be creatable with required fields."""
        from framework_m.core.doctypes.session import Session

        expires_at = datetime.now(UTC) + timedelta(days=1)
        session = Session(
            session_id="sess_abc123",
            user_id="user-001",
            expires_at=expires_at,
        )

        assert session.session_id == "sess_abc123"
        assert session.user_id == "user-001"
        assert session.expires_at == expires_at

    def test_session_optional_fields(self) -> None:
        """Session should have optional ip_address and user_agent."""
        from framework_m.core.doctypes.session import Session

        session = Session(
            session_id="sess_abc123",
            user_id="user-001",
            expires_at=datetime.now(UTC) + timedelta(days=1),
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0...",
        )

        assert session.ip_address == "192.168.1.1"
        assert session.user_agent == "Mozilla/5.0..."


# =============================================================================
# Test: Session Config
# =============================================================================


class TestSessionConfig:
    """Tests for session configuration."""

    def test_import_get_session_config(self) -> None:
        """get_session_config should be importable."""
        from framework_m.core.interfaces.session import get_session_config

        assert get_session_config is not None

    def test_default_session_config(self) -> None:
        """Default session config should have sensible defaults."""
        from framework_m.core.interfaces.session import get_session_config

        with patch(
            "framework_m.core.interfaces.session.load_config",
            return_value={},
        ):
            config = get_session_config()

        assert config["backend"] == "database"  # Default for Indie
        assert config["ttl_seconds"] == 86400  # 24 hours
        assert config["cookie_name"] == "session_id"
        assert config["cookie_httponly"] is True

    def test_session_config_from_toml(self) -> None:
        """Session config should read from framework_config.toml."""
        from framework_m.core.interfaces.session import get_session_config

        config_data = {
            "auth": {
                "session": {
                    "backend": "redis",
                    "ttl_seconds": 3600,
                    "cookie_name": "my_session",
                }
            }
        }

        with patch(
            "framework_m.core.interfaces.session.load_config",
            return_value=config_data,
        ):
            config = get_session_config()

        assert config["backend"] == "redis"
        assert config["ttl_seconds"] == 3600
        assert config["cookie_name"] == "my_session"


# =============================================================================
# Test: DatabaseSessionAdapter
# =============================================================================


class TestDatabaseSessionAdapterImport:
    """Tests for DatabaseSessionAdapter import."""

    def test_import_database_session_adapter(self) -> None:
        """DatabaseSessionAdapter should be importable."""
        from framework_m.adapters.auth.session_store import DatabaseSessionAdapter

        assert DatabaseSessionAdapter is not None


class TestDatabaseSessionAdapter:
    """Tests for DatabaseSessionAdapter operations."""

    @pytest.mark.asyncio
    async def test_create_session(self) -> None:
        """create() should create a new session."""
        from framework_m.adapters.auth.session_store import DatabaseSessionAdapter
        from framework_m.core.doctypes.session import Session

        mock_repo = AsyncMock()
        # Create a proper Session mock with typed values
        mock_saved = Session(
            session_id="sess_new123",
            user_id="user-001",
            expires_at=datetime.now(UTC) + timedelta(hours=24),
            ip_address="127.0.0.1",
            user_agent=None,
        )
        mock_repo.save.return_value = mock_saved

        adapter = DatabaseSessionAdapter(session_repository=mock_repo)
        session_data = await adapter.create(
            user_id="user-001",
            ip_address="127.0.0.1",
        )

        assert session_data.session_id is not None
        mock_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session(self) -> None:
        """get() should retrieve session by ID."""
        from framework_m.adapters.auth.session_store import DatabaseSessionAdapter
        from framework_m.core.doctypes.session import Session

        mock_repo = AsyncMock()
        # Create a proper Session mock with typed values
        mock_session = Session(
            session_id="sess_abc123",
            user_id="user-001",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            ip_address=None,
            user_agent=None,
        )
        mock_repo.get_by_id.return_value = mock_session

        adapter = DatabaseSessionAdapter(session_repository=mock_repo)
        result = await adapter.get("sess_abc123")

        assert result is not None
        assert result.session_id == "sess_abc123"

    @pytest.mark.asyncio
    async def test_delete_session(self) -> None:
        """delete() should remove session."""
        from framework_m.adapters.auth.session_store import DatabaseSessionAdapter

        mock_repo = AsyncMock()
        mock_repo.delete.return_value = True

        adapter = DatabaseSessionAdapter(session_repository=mock_repo)
        result = await adapter.delete("sess_abc123")

        assert result is True
        mock_repo.delete.assert_called_once_with("sess_abc123")


# =============================================================================
# Test: RedisSessionAdapter
# =============================================================================


class TestRedisSessionAdapterImport:
    """Tests for RedisSessionAdapter import."""

    def test_import_redis_session_adapter(self) -> None:
        """RedisSessionAdapter should be importable."""
        from framework_m.adapters.auth.session_store import RedisSessionAdapter

        assert RedisSessionAdapter is not None


class TestRedisSessionAdapterInit:
    """Tests for RedisSessionAdapter initialization."""

    def test_init_with_defaults(self) -> None:
        """RedisSessionAdapter should initialize with defaults."""
        from framework_m.adapters.auth.session_store import RedisSessionAdapter

        with patch(
            "framework_m.adapters.auth.session_store.get_session_config",
            return_value={"ttl_seconds": 86400},
        ):
            adapter = RedisSessionAdapter()

        assert adapter._key_prefix == "session:"
        assert adapter._ttl_seconds == 86400

    def test_init_with_custom_params(self) -> None:
        """RedisSessionAdapter should accept custom parameters."""
        from framework_m.adapters.auth.session_store import RedisSessionAdapter

        with patch(
            "framework_m.adapters.auth.session_store.get_session_config",
            return_value={"ttl_seconds": 86400},
        ):
            adapter = RedisSessionAdapter(
                redis_url="redis://custom:6380",
                key_prefix="custom_session:",
                ttl_seconds=3600,
            )

        assert adapter._redis_url == "redis://custom:6380"
        assert adapter._key_prefix == "custom_session:"
        assert adapter._ttl_seconds == 3600
