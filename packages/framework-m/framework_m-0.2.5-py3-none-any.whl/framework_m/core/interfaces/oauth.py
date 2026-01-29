"""OAuth2Protocol - Interface for OAuth2/OIDC providers.

This module defines the protocol that OAuth2 provider implementations
must follow. The framework supports multiple providers (Google, GitHub,
Microsoft, generic OIDC).

Example:
    class GoogleOAuth2(OAuth2Protocol):
        async def get_authorization_url(self, state: str) -> str:
            return f"https://accounts.google.com/o/oauth2/auth?..."

        async def exchange_code(self, code: str) -> OAuth2Token:
            # Exchange authorization code for tokens
            ...

        async def get_user_info(self, token: OAuth2Token) -> OAuth2UserInfo:
            # Fetch user info from provider
            ...
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field


class OAuth2Token(BaseModel):
    """OAuth2 token response.

    Contains the access token and optional refresh token from the provider.
    """

    access_token: str = Field(description="OAuth2 access token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int | None = Field(default=None, description="Expiration in seconds")
    refresh_token: str | None = Field(default=None, description="Refresh token")
    scope: str | None = Field(default=None, description="Granted scopes")


class OAuth2UserInfo(BaseModel):
    """User information from OAuth2 provider.

    Contains the essential user identity information needed to link
    or create a local user account.
    """

    provider: str = Field(description="Provider name (google, github, etc.)")
    provider_user_id: str = Field(description="Unique user ID from provider")
    email: str | None = Field(default=None, description="User's email")
    display_name: str = Field(description="Display name")
    avatar_url: str | None = Field(default=None, description="Profile picture URL")


@runtime_checkable
class OAuth2Protocol(Protocol):
    """Protocol for OAuth2/OIDC provider implementations.

    Each provider (Google, GitHub, etc.) implements this protocol
    to handle the OAuth2 flow.

    Methods:
        get_authorization_url: Generate URL to redirect user to provider
        exchange_code: Exchange authorization code for tokens
        get_user_info: Fetch user info from provider using token

    Example:
        provider = GoogleOAuth2(client_id="...", client_secret="...")
        auth_url = await provider.get_authorization_url(state="abc123")
        # User visits auth_url and authorizes
        token = await provider.exchange_code(code="code-from-callback")
        user_info = await provider.get_user_info(token)
    """

    @property
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'google', 'github')."""
        ...

    async def get_authorization_url(
        self,
        state: str,
        redirect_uri: str,
    ) -> str:
        """Generate authorization URL to redirect user to provider.

        Args:
            state: CSRF protection state parameter
            redirect_uri: URL to redirect back after authorization

        Returns:
            Full authorization URL
        """
        ...

    async def exchange_code(
        self,
        code: str,
        redirect_uri: str,
    ) -> OAuth2Token:
        """Exchange authorization code for access token.

        Args:
            code: Authorization code from callback
            redirect_uri: Must match the original redirect_uri

        Returns:
            OAuth2Token with access_token

        Raises:
            OAuth2Error: If exchange fails
        """
        ...

    async def get_user_info(self, token: OAuth2Token) -> OAuth2UserInfo:
        """Fetch user information from provider.

        Args:
            token: OAuth2Token from exchange_code

        Returns:
            OAuth2UserInfo with provider-specific user data

        Raises:
            OAuth2Error: If fetch fails
        """
        ...


__all__ = ["OAuth2Protocol", "OAuth2Token", "OAuth2UserInfo"]
