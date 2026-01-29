"""Session Store Adapters - Backend implementations for session storage.

This module provides session storage implementations:
- DatabaseSessionAdapter: Stores sessions in database (default for Indie)
- RedisSessionAdapter: Stores sessions in Redis (default for Enterprise)

Example:
    from framework_m.adapters.auth.session_store import DatabaseSessionAdapter

    adapter = DatabaseSessionAdapter(session_repository=repo)
    session = await adapter.create(user_id="user-001")
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from framework_m.core.interfaces.session import (
    SessionData,
    get_session_config,
)

if TYPE_CHECKING:
    pass


def generate_session_id() -> str:
    """Generate a cryptographically secure session ID.

    Returns:
        URL-safe session ID with 'sess_' prefix
    """
    return f"sess_{secrets.token_urlsafe(32)}"


class DatabaseSessionAdapter:
    """Session storage using database backend.

    Uses the Session DocType for persistence. Suitable for
    Indie deployments without Redis.

    Args:
        session_repository: Repository for Session DocType operations
        ttl_seconds: Session TTL (defaults to config or 24 hours)

    Example:
        adapter = DatabaseSessionAdapter(session_repository=repo)
        session = await adapter.create(user_id="user-001")
    """

    def __init__(
        self,
        session_repository: Any,
        ttl_seconds: int | None = None,
    ) -> None:
        """Initialize DatabaseSessionAdapter.

        Args:
            session_repository: Repository for Session CRUD
            ttl_seconds: Session TTL override
        """
        self._repo = session_repository
        config = get_session_config()
        self._ttl_seconds = ttl_seconds or config["ttl_seconds"]

    async def create(
        self,
        user_id: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> SessionData:
        """Create a new session.

        Args:
            user_id: User to create session for
            ip_address: Optional client IP
            user_agent: Optional client user agent

        Returns:
            SessionData with new session_id
        """
        from framework_m.core.doctypes.session import Session

        session_id = generate_session_id()
        expires_at = datetime.now(UTC) + timedelta(seconds=self._ttl_seconds)

        session = Session(
            session_id=session_id,
            user_id=user_id,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        saved = await self._repo.save(session)

        return SessionData(
            session_id=saved.session_id,
            user_id=saved.user_id,
            expires_at=saved.expires_at,
            ip_address=saved.ip_address,
            user_agent=saved.user_agent,
            created_at=getattr(saved, "created_at", None),
        )

    async def get(self, session_id: str) -> SessionData | None:
        """Get session by ID.

        Returns None if session not found or expired.

        Args:
            session_id: Session identifier

        Returns:
            SessionData if valid, None otherwise
        """
        session = await self._repo.get_by_id(session_id)

        if session is None:
            return None

        # Check expiration
        if session.expires_at < datetime.now(UTC):
            # Session expired, clean it up
            await self._repo.delete(session_id)
            return None

        return SessionData(
            session_id=session.session_id,
            user_id=session.user_id,
            expires_at=session.expires_at,
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            created_at=getattr(session, "created_at", None),
        )

    async def delete(self, session_id: str) -> bool:
        """Delete a session.

        Args:
            session_id: Session to delete

        Returns:
            True if deleted
        """
        result: bool = await self._repo.delete(session_id)
        return result

    async def delete_all_for_user(self, user_id: str) -> int:
        """Delete all sessions for a user.

        Args:
            user_id: User whose sessions to delete

        Returns:
            Number of sessions deleted
        """
        sessions = await self._repo.find_by(user_id=user_id)
        count = 0
        for session in sessions:
            if await self._repo.delete(session.session_id):
                count += 1
        return count

    async def list_for_user(self, user_id: str) -> list[SessionData]:
        """List all active sessions for a user.

        Args:
            user_id: User to list sessions for

        Returns:
            List of active sessions
        """
        sessions = await self._repo.find_by(user_id=user_id)
        now = datetime.now(UTC)

        return [
            SessionData(
                session_id=s.session_id,
                user_id=s.user_id,
                expires_at=s.expires_at,
                ip_address=s.ip_address,
                user_agent=s.user_agent,
                created_at=getattr(s, "created_at", None),
            )
            for s in sessions
            if s.expires_at > now
        ]


# =============================================================================
# Redis Session Adapter
# =============================================================================


class RedisSessionAdapter:
    """Session storage using Redis backend.

    Uses Redis for fast, scalable session storage with automatic TTL.
    Suitable for Enterprise deployments.

    Session data is stored as JSON with the following key format:
    - Session: session:{session_id}
    - User index: user_sessions:{user_id} (set of session IDs)

    Args:
        redis_url: Redis connection URL (defaults to REDIS_URL env var)
        key_prefix: Prefix for session keys (default: "session:")
        ttl_seconds: Session TTL (defaults to config or 24 hours)

    Example:
        adapter = RedisSessionAdapter()
        await adapter.connect()
        session = await adapter.create(user_id="user-001")
    """

    def __init__(
        self,
        redis_url: str | None = None,
        key_prefix: str = "session:",
        ttl_seconds: int | None = None,
    ) -> None:
        """Initialize RedisSessionAdapter.

        Args:
            redis_url: Redis connection URL
            key_prefix: Key prefix for sessions
            ttl_seconds: Session TTL override
        """
        import os

        self._redis_url = redis_url or os.environ.get(
            "REDIS_URL", "redis://localhost:6379"
        )
        self._key_prefix = key_prefix
        self._redis: Any = None

        config = get_session_config()
        self._ttl_seconds = ttl_seconds or config["ttl_seconds"]

    async def connect(self) -> None:
        """Connect to Redis server."""
        try:
            import redis.asyncio as redis_async

            self._redis = redis_async.from_url(self._redis_url)  # type: ignore[no-untyped-call]
            await self._redis.ping()
        except ImportError:
            raise ImportError(
                "redis package not installed. Run: pip install redis"
            ) from None

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None

    def _session_key(self, session_id: str) -> str:
        """Get Redis key for session."""
        return f"{self._key_prefix}{session_id}"

    def _user_sessions_key(self, user_id: str) -> str:
        """Get Redis key for user's session set."""
        return f"user_sessions:{user_id}"

    async def create(
        self,
        user_id: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> SessionData:
        """Create a new session.

        Args:
            user_id: User to create session for
            ip_address: Optional client IP
            user_agent: Optional client user agent

        Returns:
            SessionData with new session_id
        """
        import json

        if not self._redis:
            await self.connect()

        session_id = generate_session_id()
        now = datetime.now(UTC)
        expires_at = now + timedelta(seconds=self._ttl_seconds)

        session_data = SessionData(
            session_id=session_id,
            user_id=user_id,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=now,
        )

        # Store session data as JSON
        data = {
            "session_id": session_id,
            "user_id": user_id,
            "expires_at": expires_at.isoformat(),
            "ip_address": ip_address,
            "user_agent": user_agent,
            "created_at": now.isoformat(),
        }

        # Set with TTL
        await self._redis.setex(
            self._session_key(session_id),
            self._ttl_seconds,
            json.dumps(data),
        )

        # Add to user's session set
        await self._redis.sadd(self._user_sessions_key(user_id), session_id)

        return session_data

    async def get(self, session_id: str) -> SessionData | None:
        """Get session by ID.

        Args:
            session_id: Session identifier

        Returns:
            SessionData if found and not expired, None otherwise
        """
        import json

        if not self._redis:
            await self.connect()

        data = await self._redis.get(self._session_key(session_id))
        if data is None:
            return None

        try:
            parsed = json.loads(data)
            return SessionData(
                session_id=parsed["session_id"],
                user_id=parsed["user_id"],
                expires_at=datetime.fromisoformat(parsed["expires_at"]),
                ip_address=parsed.get("ip_address"),
                user_agent=parsed.get("user_agent"),
                created_at=(
                    datetime.fromisoformat(parsed["created_at"])
                    if parsed.get("created_at")
                    else None
                ),
            )
        except (json.JSONDecodeError, KeyError):
            return None

    async def delete(self, session_id: str) -> bool:
        """Delete a session.

        Args:
            session_id: Session to delete

        Returns:
            True if deleted
        """
        if not self._redis:
            await self.connect()

        # Get user_id to remove from user's set
        session = await self.get(session_id)
        if session:
            await self._redis.srem(self._user_sessions_key(session.user_id), session_id)

        result = await self._redis.delete(self._session_key(session_id))
        return bool(result)

    async def delete_all_for_user(self, user_id: str) -> int:
        """Delete all sessions for a user.

        Args:
            user_id: User whose sessions to delete

        Returns:
            Number of sessions deleted
        """
        if not self._redis:
            await self.connect()

        # Get all session IDs for user
        session_ids = await self._redis.smembers(self._user_sessions_key(user_id))
        count = 0

        for sid in session_ids:
            session_id = sid.decode() if isinstance(sid, bytes) else sid
            if await self._redis.delete(self._session_key(session_id)):
                count += 1

        # Clear the user's session set
        await self._redis.delete(self._user_sessions_key(user_id))

        return count

    async def list_for_user(self, user_id: str) -> list[SessionData]:
        """List all active sessions for a user.

        Args:
            user_id: User to list sessions for

        Returns:
            List of active sessions
        """
        if not self._redis:
            await self.connect()

        session_ids = await self._redis.smembers(self._user_sessions_key(user_id))
        sessions = []

        for sid in session_ids:
            session_id = sid.decode() if isinstance(sid, bytes) else sid
            session = await self.get(session_id)
            if session:
                sessions.append(session)
            else:
                # Clean up stale reference
                await self._redis.srem(self._user_sessions_key(user_id), session_id)

        return sessions


__all__ = [
    "DatabaseSessionAdapter",
    "RedisSessionAdapter",
    "generate_session_id",
]
