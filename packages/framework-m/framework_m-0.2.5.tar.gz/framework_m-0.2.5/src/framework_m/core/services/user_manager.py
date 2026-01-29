"""UserManager - High-level service for user operations.

This service provides a clean abstraction layer for user management,
delegating to the configured IdentityProtocol implementation.

Benefits:
- Decouples business logic from identity provider details
- Provides a consistent API for user operations
- Supports both Indie and Federated modes transparently
- Handles user creation with password hashing (Indie mode)
"""

from typing import TYPE_CHECKING, Any

from framework_m.adapters.auth.local_identity import hash_password
from framework_m.core.interfaces.auth_context import UserContext
from framework_m.core.interfaces.identity import Credentials, IdentityProtocol, Token

if TYPE_CHECKING:
    from framework_m.core.doctypes.user import LocalUser


class UserManager:
    """High-level service for user management operations.

    Delegates to the configured IdentityProtocol for authentication
    and user retrieval. Provides additional methods for user creation
    (Indie mode only).

    Args:
        identity_provider: IdentityProtocol implementation to delegate to
        user_repository: Optional repository for LocalUser (Indie mode only)

    Example:
        # Dependency injection setup
        manager = UserManager(
            identity_provider=container.get(IdentityProtocol),
            user_repository=container.get(UserRepository),
        )

        # Get user by ID
        user = await manager.get("user-123")

        # Authenticate
        token = await manager.authenticate(
            PasswordCredentials(username="user@example.com", password="secret")
        )

        # Create new user (Indie mode)
        new_user = await manager.create(
            email="new@example.com",
            password="secret123",
            full_name="New User",
        )
    """

    def __init__(
        self,
        identity_provider: IdentityProtocol,
        user_repository: Any = None,
    ) -> None:
        """Initialize UserManager.

        Args:
            identity_provider: IdentityProtocol implementation
            user_repository: Optional repository for LocalUser operations
        """
        self._identity_provider = identity_provider
        self._user_repository = user_repository

    async def get(self, user_id: str) -> UserContext | None:
        """Get user by their unique identifier.

        Delegates to identity_provider.get_user().

        Args:
            user_id: The user's unique identifier

        Returns:
            UserContext if found, None otherwise
        """
        return await self._identity_provider.get_user(user_id)

    async def get_by_email(self, email: str) -> UserContext | None:
        """Get user by their email address.

        Delegates to identity_provider.get_user_by_email().

        Args:
            email: The user's email address

        Returns:
            UserContext if found, None otherwise
        """
        return await self._identity_provider.get_user_by_email(email)

    async def authenticate(self, credentials: Credentials) -> Token:
        """Authenticate user with provided credentials.

        Delegates to identity_provider.authenticate().

        Args:
            credentials: Authentication credentials

        Returns:
            Token containing access_token

        Raises:
            AuthenticationError: If credentials are invalid
        """
        return await self._identity_provider.authenticate(credentials)

    async def get_attributes(self, user_id: str) -> dict[str, Any]:
        """Get user's ABAC attributes.

        Delegates to identity_provider.get_attributes().

        Args:
            user_id: The user's unique identifier

        Returns:
            Dictionary of attribute name -> value(s)
        """
        return await self._identity_provider.get_attributes(user_id)

    async def validate_token(self, token: str) -> UserContext | None:
        """Validate an access token and return the associated user.

        Delegates to identity_provider.validate_token().

        Args:
            token: The access token string to validate

        Returns:
            UserContext if token is valid, None if invalid/expired
        """
        return await self._identity_provider.validate_token(token)

    async def create(
        self,
        email: str,
        password: str,
        full_name: str | None = None,
        is_active: bool = True,
    ) -> "LocalUser":
        """Create a new user (Indie mode only).

        This method is only available when user_repository is configured.
        For Federated mode, users are managed by the external auth gateway.

        Args:
            email: User's email address
            password: Plain-text password (will be hashed)
            full_name: Optional display name
            is_active: Whether user can log in (default True)

        Returns:
            Created LocalUser instance

        Raises:
            RuntimeError: If user_repository is not configured
        """
        if self._user_repository is None:
            raise RuntimeError(
                "user_repository is required for create(). "
                "In Federated mode, users are managed externally."
            )

        from framework_m.core.doctypes.user import LocalUser

        # Hash password
        password_hash = hash_password(password)

        # Create user
        user = LocalUser(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            is_active=is_active,
        )

        # Save via repository
        saved_user: LocalUser = await self._user_repository.save(user)
        return saved_user


__all__ = ["UserManager"]
