"""SocialAccount DocType - Links OAuth2/OIDC providers to local users.

This module defines the SocialAccount DocType for managing social login
connections. Each SocialAccount links an external provider identity to
a local user.

Key Principles:
- One User can have multiple SocialAccounts (Google + GitHub)
- First social login creates User + SocialAccount
- Subsequent logins match by provider + provider_user_id
- Minimal PII: only store what's needed for identity linking

Example:
    account = SocialAccount(
        provider="google",
        provider_user_id="1234567890",
        user_id="user-001",
        display_name="John Doe",
        email="john@gmail.com",  # For lookup only
    )
"""

from datetime import datetime

from pydantic import Field

from framework_m.core.domain.base_doctype import BaseDocType

# Supported OAuth2/OIDC providers
SUPPORTED_PROVIDERS = frozenset({"google", "github", "microsoft", "oidc"})


class SocialAccount(BaseDocType):
    """Links OAuth2/OIDC provider identity to local user.

    Attributes:
        provider: OAuth2 provider name (google, github, microsoft, oidc)
        provider_user_id: Unique ID from the provider
        user_id: Local user ID this account belongs to
        display_name: Display name from provider (for UI)
        email: Email from provider (for lookup, optional)
        last_login_at: Last time this social account was used

    Security:
        - No sensitive data (tokens, secrets) stored here
        - Only identity linking information
        - Tokens are handled by OAuth2 flow, not persisted

    Example:
        # User signs in with Google
        account = SocialAccount(
            provider="google",
            provider_user_id="1234567890",
            user_id="user-001",
            display_name="John Doe",
        )
    """

    provider: str = Field(
        description="OAuth2 provider (google, github, microsoft, oidc)",
    )
    provider_user_id: str = Field(
        description="Unique user ID from the provider",
    )
    user_id: str = Field(
        description="Local user ID this account belongs to",
    )
    display_name: str = Field(
        description="Display name from provider",
    )
    email: str | None = Field(
        default=None,
        description="Email from provider (for lookup)",
    )
    last_login_at: datetime | None = Field(
        default=None,
        description="Last time this social account was used for login",
    )

    class Meta:
        """DocType metadata configuration."""

        api_resource = False  # OAuth routes handle creation
        apply_rls = True  # Users can only see their own accounts
        rls_field = "user_id"


__all__ = ["SUPPORTED_PROVIDERS", "SocialAccount"]
