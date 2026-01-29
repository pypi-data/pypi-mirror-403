"""Tests for Session Store Adapters.

Tests cover:
- DatabaseSessionAdapter: Database-backed session storage
- RedisSessionAdapter: Redis-backed session storage
- Session lifecycle (create, get, delete)
- Session expiry handling
- User session management
"""

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from framework_m.adapters.auth.session_store import (
    DatabaseSessionAdapter,
    RedisSessionAdapter,
    generate_session_id,
)
from framework_m.core.interfaces.session import SessionData

# =============================================================================
# Test: generate_session_id
# =============================================================================


class TestGenerateSessionId:
    """Tests for session ID generation."""

    def test_generates_string(self) -> None:
        """generate_session_id returns a string."""
        session_id = generate_session_id()
        assert isinstance(session_id, str)

    def test_has_prefix(self) -> None:
        """Session ID has 'sess_' prefix."""
        session_id = generate_session_id()
        assert session_id.startswith("sess_")

    def test_is_unique(self) -> None:
        """Each call generates unique ID."""
        ids = [generate_session_id() for _ in range(100)]
        assert len(set(ids)) == 100

    def test_sufficient_length(self) -> None:
        """Session ID has sufficient length for security."""
        session_id = generate_session_id()
        # 'sess_' + 43 chars (256 bits base64url)
        assert len(session_id) > 40


# =============================================================================
# Test: DatabaseSessionAdapter
# =============================================================================


class TestDatabaseSessionAdapterInit:
    """Tests for DatabaseSessionAdapter initialization."""

    def test_init_with_repository(self) -> None:
        """Adapter initializes with repository."""
        repo = MagicMock()
        adapter = DatabaseSessionAdapter(session_repository=repo)
        assert adapter._repo is repo

    def test_init_with_custom_ttl(self) -> None:
        """Adapter accepts custom TTL."""
        repo = MagicMock()
        adapter = DatabaseSessionAdapter(session_repository=repo, ttl_seconds=7200)
        assert adapter._ttl_seconds == 7200

    def test_init_uses_config_ttl(self) -> None:
        """Adapter uses config TTL when not specified."""
        repo = MagicMock()
        with patch(
            "framework_m.adapters.auth.session_store.get_session_config"
        ) as mock_config:
            mock_config.return_value = {"ttl_seconds": 3600}
            adapter = DatabaseSessionAdapter(session_repository=repo)
            assert adapter._ttl_seconds == 3600


class TestDatabaseSessionAdapterCreate:
    """Tests for DatabaseSessionAdapter.create()."""

    @pytest.mark.asyncio
    async def test_create_session(self) -> None:
        """Create returns SessionData with valid ID."""
        repo = AsyncMock()
        repo.save = AsyncMock(
            side_effect=lambda s: MagicMock(
                session_id=s.session_id,
                user_id=s.user_id,
                expires_at=s.expires_at,
                ip_address=s.ip_address,
                user_agent=s.user_agent,
            )
        )

        adapter = DatabaseSessionAdapter(session_repository=repo, ttl_seconds=3600)
        session = await adapter.create(user_id="user-001")

        assert isinstance(session, SessionData)
        assert session.session_id.startswith("sess_")
        assert session.user_id == "user-001"
        repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_with_ip_and_user_agent(self) -> None:
        """Create stores IP and user agent."""
        repo = AsyncMock()
        repo.save = AsyncMock(
            side_effect=lambda s: MagicMock(
                session_id=s.session_id,
                user_id=s.user_id,
                expires_at=s.expires_at,
                ip_address=s.ip_address,
                user_agent=s.user_agent,
            )
        )

        adapter = DatabaseSessionAdapter(session_repository=repo, ttl_seconds=3600)
        session = await adapter.create(
            user_id="user-001",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )

        assert session.ip_address == "192.168.1.1"
        assert session.user_agent == "Mozilla/5.0"

    @pytest.mark.asyncio
    async def test_create_sets_expiry(self) -> None:
        """Create sets correct expiry time."""
        repo = AsyncMock()
        repo.save = AsyncMock(
            side_effect=lambda s: MagicMock(
                session_id=s.session_id,
                user_id=s.user_id,
                expires_at=s.expires_at,
                ip_address=s.ip_address,
                user_agent=s.user_agent,
            )
        )

        adapter = DatabaseSessionAdapter(session_repository=repo, ttl_seconds=3600)
        session = await adapter.create(user_id="user-001")

        # Expiry should be ~1 hour from now
        expected = datetime.now(UTC) + timedelta(seconds=3600)
        delta = abs((session.expires_at - expected).total_seconds())
        assert delta < 5  # Within 5 seconds


class TestDatabaseSessionAdapterGet:
    """Tests for DatabaseSessionAdapter.get()."""

    @pytest.mark.asyncio
    async def test_get_valid_session(self) -> None:
        """Get returns session if valid."""
        repo = AsyncMock()
        repo.get_by_id = AsyncMock(
            return_value=MagicMock(
                session_id="sess_abc123",
                user_id="user-001",
                expires_at=datetime.now(UTC) + timedelta(hours=1),
                ip_address="192.168.1.1",
                user_agent="Mozilla/5.0",
            )
        )

        adapter = DatabaseSessionAdapter(session_repository=repo, ttl_seconds=3600)
        session = await adapter.get("sess_abc123")

        assert session is not None
        assert session.session_id == "sess_abc123"
        assert session.user_id == "user-001"

    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self) -> None:
        """Get returns None for missing session."""
        repo = AsyncMock()
        repo.get_by_id = AsyncMock(return_value=None)

        adapter = DatabaseSessionAdapter(session_repository=repo, ttl_seconds=3600)
        session = await adapter.get("sess_notfound")

        assert session is None

    @pytest.mark.asyncio
    async def test_get_expired_session(self) -> None:
        """Get returns None and deletes expired session."""
        repo = AsyncMock()
        repo.get_by_id = AsyncMock(
            return_value=MagicMock(
                session_id="sess_expired",
                user_id="user-001",
                expires_at=datetime.now(UTC) - timedelta(hours=1),  # Expired
                ip_address=None,
                user_agent=None,
            )
        )
        repo.delete = AsyncMock(return_value=True)

        adapter = DatabaseSessionAdapter(session_repository=repo, ttl_seconds=3600)
        session = await adapter.get("sess_expired")

        assert session is None
        repo.delete.assert_called_once_with("sess_expired")


class TestDatabaseSessionAdapterDelete:
    """Tests for DatabaseSessionAdapter.delete()."""

    @pytest.mark.asyncio
    async def test_delete_existing_session(self) -> None:
        """Delete returns True for existing session."""
        repo = AsyncMock()
        repo.delete = AsyncMock(return_value=True)

        adapter = DatabaseSessionAdapter(session_repository=repo, ttl_seconds=3600)
        result = await adapter.delete("sess_abc123")

        assert result is True
        repo.delete.assert_called_once_with("sess_abc123")

    @pytest.mark.asyncio
    async def test_delete_nonexistent_session(self) -> None:
        """Delete returns False for missing session."""
        repo = AsyncMock()
        repo.delete = AsyncMock(return_value=False)

        adapter = DatabaseSessionAdapter(session_repository=repo, ttl_seconds=3600)
        result = await adapter.delete("sess_notfound")

        assert result is False


class TestDatabaseSessionAdapterDeleteAllForUser:
    """Tests for DatabaseSessionAdapter.delete_all_for_user()."""

    @pytest.mark.asyncio
    async def test_delete_all_user_sessions(self) -> None:
        """Delete all sessions for a user."""
        repo = AsyncMock()
        repo.find_by = AsyncMock(
            return_value=[
                MagicMock(session_id="sess_1"),
                MagicMock(session_id="sess_2"),
                MagicMock(session_id="sess_3"),
            ]
        )
        repo.delete = AsyncMock(return_value=True)

        adapter = DatabaseSessionAdapter(session_repository=repo, ttl_seconds=3600)
        count = await adapter.delete_all_for_user("user-001")

        assert count == 3
        assert repo.delete.call_count == 3

    @pytest.mark.asyncio
    async def test_delete_all_no_sessions(self) -> None:
        """Delete all returns 0 when no sessions exist."""
        repo = AsyncMock()
        repo.find_by = AsyncMock(return_value=[])

        adapter = DatabaseSessionAdapter(session_repository=repo, ttl_seconds=3600)
        count = await adapter.delete_all_for_user("user-001")

        assert count == 0


class TestDatabaseSessionAdapterListForUser:
    """Tests for DatabaseSessionAdapter.list_for_user()."""

    @pytest.mark.asyncio
    async def test_list_user_sessions(self) -> None:
        """List returns active sessions for user."""
        repo = AsyncMock()
        repo.find_by = AsyncMock(
            return_value=[
                MagicMock(
                    session_id="sess_1",
                    user_id="user-001",
                    expires_at=datetime.now(UTC) + timedelta(hours=1),
                    ip_address=None,
                    user_agent=None,
                ),
                MagicMock(
                    session_id="sess_2",
                    user_id="user-001",
                    expires_at=datetime.now(UTC) + timedelta(hours=2),
                    ip_address=None,
                    user_agent=None,
                ),
            ]
        )

        adapter = DatabaseSessionAdapter(session_repository=repo, ttl_seconds=3600)
        sessions = await adapter.list_for_user("user-001")

        assert len(sessions) == 2
        assert all(isinstance(s, SessionData) for s in sessions)

    @pytest.mark.asyncio
    async def test_list_filters_expired(self) -> None:
        """List excludes expired sessions."""
        repo = AsyncMock()
        repo.find_by = AsyncMock(
            return_value=[
                MagicMock(
                    session_id="sess_active",
                    user_id="user-001",
                    expires_at=datetime.now(UTC) + timedelta(hours=1),
                    ip_address=None,
                    user_agent=None,
                ),
                MagicMock(
                    session_id="sess_expired",
                    user_id="user-001",
                    expires_at=datetime.now(UTC) - timedelta(hours=1),
                    ip_address=None,
                    user_agent=None,
                ),
            ]
        )

        adapter = DatabaseSessionAdapter(session_repository=repo, ttl_seconds=3600)
        sessions = await adapter.list_for_user("user-001")

        assert len(sessions) == 1
        assert sessions[0].session_id == "sess_active"


# =============================================================================
# Test: RedisSessionAdapter
# =============================================================================


class TestRedisSessionAdapterInit:
    """Tests for RedisSessionAdapter initialization."""

    def test_init_default(self) -> None:
        """Adapter initializes with defaults."""
        adapter = RedisSessionAdapter()
        assert adapter._key_prefix == "session:"
        assert adapter._redis is None

    def test_init_with_url(self) -> None:
        """Adapter accepts Redis URL."""
        adapter = RedisSessionAdapter(redis_url="redis://localhost:6379")
        assert adapter._redis_url == "redis://localhost:6379"

    def test_init_with_key_prefix(self) -> None:
        """Adapter accepts custom key prefix."""
        adapter = RedisSessionAdapter(key_prefix="myapp:session:")
        assert adapter._key_prefix == "myapp:session:"

    def test_init_with_ttl(self) -> None:
        """Adapter accepts custom TTL."""
        adapter = RedisSessionAdapter(ttl_seconds=7200)
        assert adapter._ttl_seconds == 7200


class TestRedisSessionAdapterConnect:
    """Tests for RedisSessionAdapter.connect()."""

    @pytest.mark.asyncio
    async def test_connect_creates_client(self) -> None:
        """Connect creates Redis client."""
        adapter = RedisSessionAdapter(redis_url="redis://localhost:6379")

        with patch("redis.asyncio.from_url") as mock_from_url:
            mock_redis = AsyncMock()
            mock_from_url.return_value = mock_redis

            await adapter.connect()

            mock_from_url.assert_called_once()
            assert adapter._redis is not None


class TestRedisSessionAdapterClose:
    """Tests for RedisSessionAdapter.close()."""

    @pytest.mark.asyncio
    async def test_close_disconnects(self) -> None:
        """Close disconnects Redis client."""
        adapter = RedisSessionAdapter()
        mock_redis = AsyncMock()
        adapter._redis = mock_redis

        await adapter.close()

        mock_redis.close.assert_called_once()


class TestRedisSessionAdapterKeys:
    """Tests for Redis key generation."""

    def test_session_key(self) -> None:
        """Session key has correct format."""
        adapter = RedisSessionAdapter(key_prefix="session:")
        key = adapter._session_key("sess_abc123")
        assert key == "session:sess_abc123"

    def test_user_sessions_key(self) -> None:
        """User sessions key has correct format."""
        adapter = RedisSessionAdapter()
        key = adapter._user_sessions_key("user-001")
        assert key == "user_sessions:user-001"


class TestRedisSessionAdapterCreate:
    """Tests for RedisSessionAdapter.create()."""

    @pytest.mark.asyncio
    async def test_create_session(self) -> None:
        """Create stores session in Redis."""
        adapter = RedisSessionAdapter(ttl_seconds=3600)
        mock_redis = AsyncMock()
        adapter._redis = mock_redis

        session = await adapter.create(user_id="user-001")

        assert isinstance(session, SessionData)
        assert session.session_id.startswith("sess_")
        assert session.user_id == "user-001"
        mock_redis.setex.assert_called_once()
        mock_redis.sadd.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_auto_connects(self) -> None:
        """Create auto-connects if not connected."""
        adapter = RedisSessionAdapter(
            redis_url="redis://localhost:6379",
            ttl_seconds=3600,
        )

        with patch("redis.asyncio.from_url") as mock_from_url:
            mock_redis = AsyncMock()
            mock_from_url.return_value = mock_redis

            session = await adapter.create(user_id="user-001")

            assert session is not None
            mock_from_url.assert_called_once()


class TestRedisSessionAdapterGet:
    """Tests for RedisSessionAdapter.get()."""

    @pytest.mark.asyncio
    async def test_get_valid_session(self) -> None:
        """Get returns session from Redis."""
        adapter = RedisSessionAdapter(ttl_seconds=3600)
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(
            return_value=json.dumps(
                {
                    "session_id": "sess_abc123",
                    "user_id": "user-001",
                    "expires_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
                    "ip_address": "192.168.1.1",
                    "user_agent": "Mozilla/5.0",
                    "created_at": datetime.now(UTC).isoformat(),
                }
            )
        )
        adapter._redis = mock_redis

        session = await adapter.get("sess_abc123")

        assert session is not None
        assert session.session_id == "sess_abc123"
        assert session.user_id == "user-001"

    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self) -> None:
        """Get returns None for missing session."""
        adapter = RedisSessionAdapter(ttl_seconds=3600)
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        adapter._redis = mock_redis

        session = await adapter.get("sess_notfound")

        assert session is None


class TestRedisSessionAdapterDelete:
    """Tests for RedisSessionAdapter.delete()."""

    @pytest.mark.asyncio
    async def test_delete_session(self) -> None:
        """Delete removes session from Redis."""
        adapter = RedisSessionAdapter(ttl_seconds=3600)
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(
            return_value=json.dumps(
                {
                    "session_id": "sess_abc123",
                    "user_id": "user-001",
                    "expires_at": datetime.now(UTC).isoformat(),
                    "ip_address": None,
                    "user_agent": None,
                    "created_at": datetime.now(UTC).isoformat(),
                }
            )
        )
        mock_redis.delete = AsyncMock(return_value=1)
        mock_redis.srem = AsyncMock(return_value=1)
        adapter._redis = mock_redis

        result = await adapter.delete("sess_abc123")

        assert result is True
        mock_redis.delete.assert_called_once()


class TestRedisSessionAdapterDeleteAllForUser:
    """Tests for RedisSessionAdapter.delete_all_for_user()."""

    @pytest.mark.asyncio
    async def test_delete_all_user_sessions(self) -> None:
        """Delete all sessions for user from Redis."""
        adapter = RedisSessionAdapter(ttl_seconds=3600)
        mock_redis = AsyncMock()
        mock_redis.smembers = AsyncMock(return_value={"sess_1", "sess_2", "sess_3"})
        mock_redis.delete = AsyncMock(return_value=1)
        adapter._redis = mock_redis

        count = await adapter.delete_all_for_user("user-001")

        assert count == 3


class TestRedisSessionAdapterListForUser:
    """Tests for RedisSessionAdapter.list_for_user()."""

    @pytest.mark.asyncio
    async def test_list_user_sessions(self) -> None:
        """List returns sessions for user from Redis."""
        adapter = RedisSessionAdapter(ttl_seconds=3600)
        mock_redis = AsyncMock()
        mock_redis.smembers = AsyncMock(return_value={"sess_1", "sess_2"})
        mock_redis.get = AsyncMock(
            side_effect=[
                json.dumps(
                    {
                        "session_id": "sess_1",
                        "user_id": "user-001",
                        "expires_at": (
                            datetime.now(UTC) + timedelta(hours=1)
                        ).isoformat(),
                        "ip_address": None,
                        "user_agent": None,
                        "created_at": datetime.now(UTC).isoformat(),
                    }
                ),
                json.dumps(
                    {
                        "session_id": "sess_2",
                        "user_id": "user-001",
                        "expires_at": (
                            datetime.now(UTC) + timedelta(hours=2)
                        ).isoformat(),
                        "ip_address": None,
                        "user_agent": None,
                        "created_at": datetime.now(UTC).isoformat(),
                    }
                ),
            ]
        )
        adapter._redis = mock_redis

        sessions = await adapter.list_for_user("user-001")

        assert len(sessions) == 2
        assert all(isinstance(s, SessionData) for s in sessions)


# =============================================================================
# Test: Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    async def test_database_adapter_handles_session_data_copy(self) -> None:
        """Database adapter returns separate SessionData instances."""
        repo = AsyncMock()
        repo.save = AsyncMock(
            side_effect=lambda s: MagicMock(
                session_id=s.session_id,
                user_id=s.user_id,
                expires_at=s.expires_at,
                ip_address=None,
                user_agent=None,
            )
        )

        adapter = DatabaseSessionAdapter(session_repository=repo, ttl_seconds=3600)
        session1 = await adapter.create(user_id="user-001")
        session2 = await adapter.create(user_id="user-001")

        # Each session should have unique ID
        assert session1.session_id != session2.session_id

    def test_redis_adapter_key_prefix_flexibility(self) -> None:
        """Redis adapter supports various key prefixes."""
        adapter1 = RedisSessionAdapter(key_prefix="app1:sess:")
        adapter2 = RedisSessionAdapter(key_prefix="prod:session:")

        assert adapter1._session_key("abc") == "app1:sess:abc"
        assert adapter2._session_key("abc") == "prod:session:abc"
