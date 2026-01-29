"""ApiKey DocType - API keys for scripts and integrations.

This module defines the ApiKey DocType for storing API key metadata.
The actual key is only returned once at creation time; only the hash
is stored.

Security:
- key_hash is NEVER included in JSON serialization
- Use argon2 for hashing (see LocalIdentityAdapter)
- Keys should have expiration dates
- Track last_used_at for security auditing

Example:
    # Creating a new API key
    key = ApiKey(
        key_hash=hash_password(raw_key),
        user_id="user-123",
        name="CI/CD Pipeline Key",
        scopes=["read", "write"],
        expires_at=datetime.now(UTC) + timedelta(days=90),
    )
"""

from datetime import datetime

from pydantic import Field

from framework_m.core.domain.base_doctype import BaseDocType


class ApiKey(BaseDocType):
    """API key for scripts and integrations.

    Attributes:
        key_hash: Argon2 hash of the API key (excluded from serialization)
        user_id: Owner of the key
        name: Human-readable label for the key
        scopes: Optional permission scopes (e.g., ["read", "write"])
        expires_at: Optional expiration date
        last_used_at: Last time the key was used (for auditing)
        is_active: Whether the key is currently active

    Security:
        - key_hash is excluded from model_dump() and model_dump_json()
        - Never store or return plaintext keys
        - Raw key is only shown once at creation time

    Example:
        key = ApiKey(
            key_hash="$argon2id$v=19$...",
            user_id="user-123",
            name="Production Deployment",
            scopes=["deploy"],
            expires_at=datetime(2025, 12, 31),
        )
    """

    key_hash: str = Field(
        description="Argon2 hash of the API key",
        exclude=True,  # Never include in serialization
    )
    user_id: str = Field(description="Owner user ID")
    name: str = Field(description="Human-readable key label")
    scopes: list[str] = Field(
        default_factory=list,
        description="Permission scopes for this key",
    )
    expires_at: datetime | None = Field(
        default=None,
        description="Key expiration date (None = never expires)",
    )
    last_used_at: datetime | None = Field(
        default=None,
        description="Last time the key was used",
    )
    is_active: bool = Field(
        default=True,
        description="Whether the key is active",
    )

    class Meta:
        """DocType metadata configuration."""

        api_resource = False  # Auth API handles key operations
        apply_rls = True  # Users can only see their own keys
        rls_field = "user_id"


__all__ = ["ApiKey"]
