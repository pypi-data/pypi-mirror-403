"""User DocTypes - LocalUser and UserPreferences for Indie mode.

This module defines the user-related DocTypes for Framework M's
identity management system (Indie mode / Mode A).

LocalUser is SQL-backed and stores:
- email (unique)
- password_hash (never serialized)
- full_name (optional)
- is_active (default True)

UserPreferences stores user-specific settings (theme, language, etc.)
and is used by both Indie and Federated modes.

Security:
- password_hash is NEVER included in JSON serialization
- Use argon2 for password hashing (adapter responsibility)
"""

from typing import Any

from pydantic import Field

from framework_m.core.domain.base_doctype import BaseDocType


class LocalUser(BaseDocType):
    """SQL-backed user for Indie mode (Mode A).

    Stores credentials and profile information locally.
    Default implementation for rapid development.

    Attributes:
        email: Unique email address (login identifier)
        password_hash: Argon2 hash of password (excluded from serialization)
        full_name: Optional display name
        is_active: Whether user can log in (default True)

    Security:
        - password_hash is excluded from model_dump() and model_dump_json()
        - Never store plaintext passwords
        - Use argon2 for hashing (see LocalIdentityAdapter)

    Example:
        user = LocalUser(
            email="john@example.com",
            password_hash="$argon2id$v=19$...",
            full_name="John Doe",
        )
    """

    email: str = Field(description="Unique email address")
    password_hash: str = Field(
        description="Argon2 password hash",
        exclude=True,  # Never include in serialization
    )
    full_name: str | None = Field(default=None, description="User's display name")
    is_active: bool = Field(default=True, description="Whether user can log in")
    locale: str | None = Field(
        default=None,
        description="User's preferred locale (e.g., 'en', 'hi', 'ta')",
        max_length=10,
    )

    class Meta:
        """DocType metadata configuration."""

        api_resource = False  # Auth API handles user operations
        apply_rls = False  # Users are system-wide, not per-owner
        requires_auth = True  # Default: require authentication


class UserPreferences(BaseDocType):
    """User preferences and settings.

    Stores user-specific configuration like theme, language,
    notification preferences, etc.

    Used by both Indie and Federated modes:
    - Indie: Linked to LocalUser
    - Federated: Linked by user_id from auth gateway

    Attributes:
        user_id: Reference to user (string ID for flexibility)
        settings: JSON dict of preference key-value pairs

    Example:
        prefs = UserPreferences(
            user_id="user-123",
            settings={
                "theme": "dark",
                "language": "en",
                "notifications_enabled": True,
            },
        )
    """

    user_id: str = Field(description="User identifier")
    settings: dict[str, Any] = Field(
        default_factory=dict,
        description="User preference key-value pairs",
    )

    class Meta:
        """DocType metadata configuration."""

        api_resource = False  # Custom API for preferences
        apply_rls = True  # Users can only see their own preferences
        rls_field = "user_id"  # Filter by user_id, not owner


__all__ = [
    "LocalUser",
    "UserPreferences",
]
