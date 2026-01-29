"""Session DocType - Database-backed session storage.

This module defines the Session DocType for storing user sessions
in the database (fallback for environments without Redis).

Sessions track:
- Session ID (unique identifier)
- User ID (owner)
- Expiration time
- Client metadata (IP, user agent)

Example:
    session = Session(
        session_id="sess_abc123",
        user_id="user-001",
        expires_at=datetime.now(UTC) + timedelta(days=1),
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0...",
    )
"""

from datetime import datetime

from pydantic import Field

from framework_m.core.domain.base_doctype import BaseDocType


class Session(BaseDocType):
    """Database-backed user session.

    Attributes:
        session_id: Unique session identifier (used as cookie value)
        user_id: User this session belongs to
        expires_at: When the session expires
        ip_address: Client IP address for security auditing
        user_agent: Client user agent for display

    Security:
        - session_id should be cryptographically random
        - Check expires_at before accepting session
        - Track ip_address/user_agent for security alerts
    """

    session_id: str = Field(
        description="Unique session identifier",
    )
    user_id: str = Field(
        description="User this session belongs to",
    )
    expires_at: datetime = Field(
        description="Session expiration time",
    )
    ip_address: str | None = Field(
        default=None,
        description="Client IP address",
    )
    user_agent: str | None = Field(
        default=None,
        description="Client user agent string",
    )

    class Meta:
        """DocType metadata configuration."""

        api_resource = False  # Session API handles operations
        apply_rls = True  # Users can only see their own sessions
        rls_field = "user_id"


__all__ = ["Session"]
