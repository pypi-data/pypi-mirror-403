"""LocalIdentityAdapter - Identity management for Indie mode.

This adapter implements IdentityProtocol for local/indie deployments
where users are stored in the application's database.

Features:
- Password hashing with argon2
- JWT token generation and validation
- User retrieval by ID or email

Security:
- Uses argon2id for password hashing (memory-hard, side-channel resistant)
- JWT tokens with configurable expiration
- Never stores plaintext passwords
"""

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from framework_m.core.exceptions import AuthenticationError
from framework_m.core.interfaces.auth_context import UserContext
from framework_m.core.interfaces.identity import Credentials, PasswordCredentials, Token

if TYPE_CHECKING:
    from framework_m.core.doctypes.user import LocalUser

# Password hasher instance (singleton)
_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Hash a password using argon2id.

    Args:
        password: Plain-text password to hash

    Returns:
        Argon2-formatted hash string

    Example:
        hashed = hash_password("secret123")
        # Returns: "$argon2id$v=19$m=65536,t=3,p=4$..."
    """
    return _password_hasher.hash(password)


def verify_password(password: str, hash: str) -> bool:
    """Verify a password against its hash.

    Args:
        password: Plain-text password to verify
        hash: Argon2 hash to verify against

    Returns:
        True if password matches, False otherwise
    """
    try:
        _password_hasher.verify(hash, password)
        return True
    except VerifyMismatchError:
        return False


class LocalIdentityAdapter:
    """IdentityProtocol implementation for Indie mode (Mode A).

    Uses LocalUser DocType for storage and argon2 for password hashing.
    Generates JWT tokens for authentication.

    Args:
        user_repository: Repository for LocalUser CRUD operations
        jwt_secret: Secret key for JWT signing
        jwt_algorithm: JWT algorithm (default: HS256)
        token_expiry_hours: Access token lifetime in hours (default: 24)

    Example:
        adapter = LocalIdentityAdapter(
            user_repository=user_repo,
            jwt_secret="your-secret-key",
        )
        token = await adapter.authenticate(
            PasswordCredentials(username="user@example.com", password="secret")
        )
    """

    def __init__(
        self,
        user_repository: Any,
        jwt_secret: str = "change-me-in-production",
        jwt_algorithm: str = "HS256",
        token_expiry_hours: int = 24,
    ) -> None:
        """Initialize the adapter.

        Args:
            user_repository: Repository for LocalUser operations
            jwt_secret: Secret key for JWT token signing
            jwt_algorithm: Algorithm for JWT (default HS256)
            token_expiry_hours: Token lifetime in hours
        """
        self._user_repo = user_repository
        self._jwt_secret = jwt_secret
        self._jwt_algorithm = jwt_algorithm
        self._token_expiry_hours = token_expiry_hours

    async def get_user(self, user_id: str) -> UserContext | None:
        """Get user by their unique identifier.

        Args:
            user_id: The user's UUID as string

        Returns:
            UserContext if found, None otherwise
        """
        user = await self._user_repo.get(user_id)
        if user is None:
            return None

        return self._to_user_context(user)

    async def get_user_by_email(self, email: str) -> UserContext | None:
        """Get user by their email address.

        Args:
            email: The user's email address

        Returns:
            UserContext if found, None otherwise
        """
        user = await self._user_repo.get_by_email(email)
        if user is None:
            return None

        return self._to_user_context(user)

    async def authenticate(self, credentials: Credentials) -> Token:
        """Authenticate user with provided credentials.

        Currently supports PasswordCredentials only.

        Args:
            credentials: Authentication credentials

        Returns:
            Token containing access_token

        Raises:
            AuthenticationError: If credentials are invalid
        """
        if not isinstance(credentials, PasswordCredentials):
            raise AuthenticationError("Unsupported credential type")

        # Get user by email/username
        user = await self._user_repo.get_by_email(credentials.username)
        if user is None:
            raise AuthenticationError("Invalid credentials")

        # Verify password
        if not verify_password(credentials.password, user.password_hash):
            raise AuthenticationError("Invalid credentials")

        # Check if user is active
        if not user.is_active:
            raise AuthenticationError("User account is disabled")

        # Generate JWT token
        return self._generate_token(user)

    async def get_attributes(self, user_id: str) -> dict[str, Any]:
        """Get user's ABAC attributes.

        For LocalUser, returns basic attributes.
        Override in subclass for custom attribute sources.

        Args:
            user_id: The user's unique identifier

        Returns:
            Dictionary of attribute name -> value(s)
        """
        user = await self._user_repo.get(user_id)
        if user is None:
            return {}

        return {
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "roles": [],  # Override for role support
            "teams": [],
            "tenants": [],
        }

    async def validate_token(self, token: str) -> UserContext | None:
        """Validate an access token and return the associated user.

        Args:
            token: The JWT access token string

        Returns:
            UserContext if token is valid, None if invalid/expired
        """
        try:
            payload = jwt.decode(
                token,
                self._jwt_secret,
                algorithms=[self._jwt_algorithm],
            )
            user_id = payload.get("sub")
            if not user_id:
                return None

            return await self.get_user(user_id)
        except jwt.PyJWTError:
            return None

    def _to_user_context(self, user: "LocalUser") -> UserContext:
        """Convert LocalUser to UserContext.

        Args:
            user: The LocalUser instance

        Returns:
            UserContext for the user
        """
        return UserContext(
            id=str(user.id),
            email=user.email,
            name=user.full_name,
            roles=[],  # Can be extended to load roles
            tenants=[],
        )

    def _generate_token(self, user: "LocalUser") -> Token:
        """Generate a JWT token for the user.

        Args:
            user: The authenticated LocalUser

        Returns:
            Token with access_token
        """
        now = datetime.now(UTC)
        expires_at = now + timedelta(hours=self._token_expiry_hours)

        payload = {
            "sub": str(user.id),
            "email": user.email,
            "iat": now,
            "exp": expires_at,
        }

        access_token = jwt.encode(
            payload,
            self._jwt_secret,
            algorithm=self._jwt_algorithm,
        )

        return Token(
            access_token=access_token,
            token_type="Bearer",
            expires_in=self._token_expiry_hours * 3600,
        )


__all__ = [
    "LocalIdentityAdapter",
    "hash_password",
    "verify_password",
]
