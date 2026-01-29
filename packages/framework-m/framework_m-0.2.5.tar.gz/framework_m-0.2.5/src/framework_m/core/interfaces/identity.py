"""Identity Protocol - Core interface for identity management.

This module defines the IdentityProtocol for managing user identities
and authentication. It works alongside AuthContextProtocol:

- AuthContextProtocol: "Who is making this request?" (stateless, from JWT/headers)
- IdentityProtocol: "How do I manage users?" (CRUD, authenticate, attributes)

The framework supports pluggable identity providers:
- Indie Mode: LocalIdentityProvider (SQL-backed user table)
- Federated Mode: FederatedIdentityProvider (hydrates from headers)
"""

from typing import Any, Protocol

from pydantic import BaseModel, Field

from framework_m.core.interfaces.auth_context import UserContext


class Token(BaseModel):
    """Authentication token returned by identity provider.

    Follows OAuth2 token response format for compatibility.

    Attributes:
        access_token: The token string for API access
        token_type: Token type (typically "Bearer")
        expires_in: Token lifetime in seconds (optional)
        refresh_token: Token for obtaining new access tokens (optional)

    Example:
        token = Token(
            access_token="eyJhbGciOiJIUzI1NiIs...",
            token_type="Bearer",
            expires_in=3600,
            refresh_token="dGhpcyBpcyBhIHJlZnJlc2g=",
        )
    """

    access_token: str
    token_type: str = Field(default="Bearer")
    expires_in: int | None = None
    refresh_token: str | None = None


class Credentials(BaseModel):
    """Base credentials model for authentication.

    Subclass this for different authentication methods:
    - PasswordCredentials: username/password
    - ApiKeyCredentials: API key authentication
    - OAuthCredentials: OAuth2 authorization code

    This base class is intentionally empty to allow any credential type.
    """

    pass


class PasswordCredentials(Credentials):
    """Username and password authentication credentials.

    Attributes:
        username: User identifier (email or username)
        password: Plain-text password (will be hashed by adapter)

    Example:
        creds = PasswordCredentials(
            username="user@example.com",
            password="secret123",
        )
    """

    username: str
    password: str


class MagicLinkCredentials(Credentials):
    """Magic link (passwordless) authentication credentials.

    Attributes:
        email: User's email address
        token: Magic link token from URL

    Example:
        creds = MagicLinkCredentials(
            email="user@example.com",
            token="abc123...",
        )
    """

    email: str
    token: str


class IdentityProtocol(Protocol):
    """Protocol defining the contract for identity management.

    This is the primary port for user management in the hexagonal
    architecture. Implementations can be:

    - LocalIdentityProvider: SQL-backed user table (Indie mode)
    - FederatedIdentityProvider: Hydrates from auth headers (Enterprise)
    - MockIdentityProvider: For testing

    All methods are async for consistency with the framework.

    Example usage:
        identity: IdentityProtocol = container.get(IdentityProtocol)

        # Authenticate user
        token = await identity.authenticate(
            PasswordCredentials(username="user@example.com", password="secret")
        )

        # Get user by ID
        user = await identity.get_user("user-123")

        # Get user's ABAC attributes
        attrs = await identity.get_attributes("user-123")
        # Returns: {"roles": ["Employee"], "teams": ["Sales"], "department": "EMEA"}
    """

    async def get_user(self, user_id: str) -> UserContext | None:
        """Get user by their unique identifier.

        Args:
            user_id: The user's unique identifier

        Returns:
            UserContext if found, None otherwise
        """
        ...

    async def get_user_by_email(self, email: str) -> UserContext | None:
        """Get user by their email address.

        Args:
            email: The user's email address

        Returns:
            UserContext if found, None otherwise
        """
        ...

    async def authenticate(self, credentials: Credentials) -> Token:
        """Authenticate user with provided credentials.

        Args:
            credentials: Authentication credentials (password, API key, etc.)

        Returns:
            Token containing access_token and optional refresh_token

        Raises:
            AuthenticationError: If credentials are invalid
        """
        ...

    async def get_attributes(self, user_id: str) -> dict[str, Any]:
        """Get user's ABAC (Attribute-Based Access Control) attributes.

        Returns all attributes used for authorization decisions:
        - roles: List of role names
        - teams: List of team memberships
        - tenants: List of accessible tenants
        - department, location, etc.: Custom attributes

        Args:
            user_id: The user's unique identifier

        Returns:
            Dictionary of attribute name -> value(s)
        """
        ...

    async def validate_token(self, token: str) -> UserContext | None:
        """Validate an access token and return the associated user.

        Used by authentication middleware to verify incoming tokens.

        Args:
            token: The access token string to validate

        Returns:
            UserContext if token is valid, None if invalid/expired
        """
        ...


__all__ = [
    "Credentials",
    "IdentityProtocol",
    "MagicLinkCredentials",
    "PasswordCredentials",
    "Token",
]
