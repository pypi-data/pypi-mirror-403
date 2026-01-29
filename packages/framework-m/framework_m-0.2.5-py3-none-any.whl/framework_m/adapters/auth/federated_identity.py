"""FederatedIdentityAdapter - Identity management for Enterprise mode.

This adapter implements IdentityProtocol for federated/enterprise deployments
where authentication is handled by an external gateway (SSO, OAuth2, etc.).

Features:
- Hydrates UserContext from auth gateway headers
- No local password storage (auth delegated externally)
- Optional local storage for user preferences

Headers used:
- X-User-ID: Unique user identifier
- X-Email: User's email address
- X-Full-Name: Display name (optional)
- X-Roles: Comma-separated role list (optional)
- X-Tenants: Comma-separated tenant IDs (optional)
- X-Teams: Comma-separated team names (optional)
"""

from collections.abc import Mapping
from typing import Any

from framework_m.core.interfaces.auth_context import UserContext
from framework_m.core.interfaces.identity import Credentials, Token


def hydrate_from_headers(headers: Mapping[str, str]) -> UserContext | None:
    """Create UserContext from auth gateway headers.

    Expected headers:
        - X-User-ID: Required, unique user identifier
        - X-Email: Required, user's email
        - X-Full-Name: Optional, display name
        - X-Roles: Optional, comma-separated roles
        - X-Tenants: Optional, comma-separated tenant IDs
        - X-Teams: Optional, comma-separated team names

    Args:
        headers: Request headers (case-insensitive dict)

    Returns:
        UserContext if required headers present, None otherwise

    Example:
        headers = {
            "X-User-ID": "user-123",
            "X-Email": "john@example.com",
            "X-Roles": "Employee,Manager",
        }
        user = hydrate_from_headers(headers)
    """
    # Required headers
    user_id = headers.get("X-User-ID")
    email = headers.get("X-Email")

    if not user_id or not email:
        return None

    # Optional headers
    full_name = headers.get("X-Full-Name")
    roles_str = headers.get("X-Roles", "")
    tenants_str = headers.get("X-Tenants", "")
    teams_str = headers.get("X-Teams", "")

    # Parse comma-separated lists
    roles = [r.strip() for r in roles_str.split(",") if r.strip()]
    tenants = [t.strip() for t in tenants_str.split(",") if t.strip()]
    teams = [t.strip() for t in teams_str.split(",") if t.strip()]

    return UserContext(
        id=user_id,
        email=email,
        name=full_name,
        roles=roles,
        tenants=tenants,
        teams=teams,
    )


class FederatedIdentityAdapter:
    """IdentityProtocol implementation for Enterprise mode (Mode B).

    Does NOT store users locally - authentication is delegated to an
    external gateway (Keycloak, Auth0, Okta, etc.).

    User context is hydrated from request headers set by the gateway.
    Only user preferences/settings are stored locally.

    Args:
        preferences_repository: Repository for UserPreferences storage

    Example:
        adapter = FederatedIdentityAdapter(
            preferences_repository=prefs_repo,
        )
        # authenticate() raises NotImplementedError
        # Use hydrate_from_headers() in middleware instead
    """

    def __init__(self, preferences_repository: Any = None) -> None:
        """Initialize the adapter.

        Args:
            preferences_repository: Optional repository for user preferences
        """
        self._prefs_repo = preferences_repository

    async def get_user(self, user_id: str) -> UserContext | None:
        """Get user from local preferences cache.

        In federated mode, we don't have a full user store.
        This returns cached info from preferences if available.

        Args:
            user_id: The user's unique identifier

        Returns:
            UserContext if preferences exist, None otherwise
        """
        if self._prefs_repo is None:
            return None

        prefs = await self._prefs_repo.get_by_user_id(user_id)
        if prefs is None:
            return None

        settings = prefs.settings or {}
        return UserContext(
            id=prefs.user_id,
            email=settings.get("email", ""),
            name=settings.get("display_name"),
            roles=settings.get("roles", []),
            tenants=settings.get("tenants", []),
            teams=settings.get("teams", []),
        )

    async def get_user_by_email(self, email: str) -> UserContext | None:
        """Get user by email.

        Not directly supported in federated mode - use get_user() with ID.

        Args:
            email: The user's email address

        Returns:
            None (not supported in federated mode)
        """
        return None

    async def authenticate(self, credentials: Credentials) -> Token:
        """Authenticate user with credentials.

        NOT SUPPORTED in federated mode - authentication is handled
        by the external auth gateway.

        Args:
            credentials: Not used

        Raises:
            NotImplementedError: Always, use external auth gateway
        """
        raise NotImplementedError(
            "Authentication in federated mode must use external auth gateway. "
            "Use hydrate_from_headers() in your auth middleware instead."
        )

    async def get_attributes(self, user_id: str) -> dict[str, Any]:
        """Get user's ABAC attributes from preferences.

        Args:
            user_id: The user's unique identifier

        Returns:
            Dictionary of attributes from preferences, or empty dict
        """
        if self._prefs_repo is None:
            return {}

        prefs = await self._prefs_repo.get_by_user_id(user_id)
        if prefs is None:
            return {}

        settings = prefs.settings or {}
        return {
            "email": settings.get("email", ""),
            "full_name": settings.get("display_name"),
            "roles": settings.get("roles", []),
            "teams": settings.get("teams", []),
            "tenants": settings.get("tenants", []),
        }

    async def validate_token(self, token: str) -> UserContext | None:
        """Validate a token.

        In federated mode, token validation is handled by the gateway.
        This method always returns None.

        Args:
            token: The access token (ignored)

        Returns:
            None (token validation delegated to gateway)
        """
        return None


__all__ = [
    "FederatedIdentityAdapter",
    "hydrate_from_headers",
]
