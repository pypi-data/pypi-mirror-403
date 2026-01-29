"""Authentication Strategies - Built-in implementations.

This module provides authentication strategies for different auth methods:
- BearerTokenAuth: JWT/OAuth2 access tokens (Authorization: Bearer)
- ApiKeyAuth: API keys for scripts/integrations (X-API-Key header)
- HeaderAuth: Federated mode - hydrate from gateway headers (X-User-ID)
- AuthChain: Chain multiple strategies (first match wins)

Each strategy implements AuthenticationProtocol with:
- supports(): Check if the strategy can handle the request
- authenticate(): Extract user identity from request

Example:
    from framework_m.adapters.auth.strategies import BearerTokenAuth, AuthChain

    chain = AuthChain(strategies=[
        BearerTokenAuth(jwt_secret="..."),
        ApiKeyAuth(api_key_lookup=lookup_fn),
    ])

    user = await chain.authenticate(headers)
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import TYPE_CHECKING, Any

import jwt

from framework_m.core.interfaces.auth_context import UserContext

if TYPE_CHECKING:
    pass


class BearerTokenAuth:
    """Authentication strategy for JWT Bearer tokens.

    Handles Authorization: Bearer <token> header.
    Validates JWT and extracts user identity from claims.

    Args:
        jwt_secret: Secret key for JWT verification
        jwt_algorithm: Algorithm used for JWT (default: HS256)

    Example:
        strategy = BearerTokenAuth(jwt_secret="your-secret")
        if strategy.supports(headers):
            user = await strategy.authenticate(headers)
    """

    def __init__(
        self,
        jwt_secret: str,
        jwt_algorithm: str = "HS256",
    ) -> None:
        """Initialize BearerTokenAuth.

        Args:
            jwt_secret: Secret key for JWT verification
            jwt_algorithm: Algorithm for JWT verification
        """
        self._jwt_secret = jwt_secret
        self._jwt_algorithm = jwt_algorithm

    def supports(self, headers: Mapping[str, str]) -> bool:
        """Check if request has Bearer token.

        Args:
            headers: Request headers (lowercase keys)

        Returns:
            True if Authorization: Bearer header present
        """
        auth_header = headers.get("authorization", "")
        return auth_header.lower().startswith("bearer ")

    async def authenticate(self, headers: Mapping[str, str]) -> UserContext | None:
        """Authenticate using JWT Bearer token.

        Args:
            headers: Request headers

        Returns:
            UserContext if token valid, None otherwise
        """
        auth_header = headers.get("authorization", "")
        if not auth_header.lower().startswith("bearer "):
            return None

        token = auth_header[7:]  # Remove "Bearer " prefix

        try:
            payload = jwt.decode(
                token,
                self._jwt_secret,
                algorithms=[self._jwt_algorithm],
            )
        except jwt.PyJWTError:
            return None

        # Extract user info from claims
        user_id = payload.get("sub")
        if not user_id:
            return None

        return UserContext(
            id=str(user_id),
            email=payload.get("email", ""),
            name=payload.get("name"),
            roles=payload.get("roles", []),
            tenants=payload.get("tenants", []),
            teams=payload.get("teams", []),
        )


# Type alias for API key lookup function
ApiKeyLookupFn = Callable[[str], Awaitable[UserContext | None]]


class ApiKeyAuth:
    """Authentication strategy for API keys.

    Handles X-API-Key header for scripts and integrations.

    Args:
        api_key_lookup: Async function to look up API key and return user

    Example:
        async def lookup_key(key: str) -> UserContext | None:
            # Look up key in database, return associated user
            ...

        strategy = ApiKeyAuth(api_key_lookup=lookup_key)
    """

    def __init__(self, api_key_lookup: ApiKeyLookupFn) -> None:
        """Initialize ApiKeyAuth.

        Args:
            api_key_lookup: Function to look up API key
        """
        self._lookup = api_key_lookup

    def supports(self, headers: Mapping[str, str]) -> bool:
        """Check if request has API key.

        Args:
            headers: Request headers (lowercase keys)

        Returns:
            True if X-API-Key header present
        """
        return "x-api-key" in headers

    async def authenticate(self, headers: Mapping[str, str]) -> UserContext | None:
        """Authenticate using API key.

        Args:
            headers: Request headers

        Returns:
            UserContext if key valid, None otherwise
        """
        api_key = headers.get("x-api-key")
        if not api_key:
            return None

        return await self._lookup(api_key)


# Type alias for basic auth authenticate function
BasicAuthenticateFn = Callable[[str, str], Awaitable[UserContext | None]]


class BasicAuth:
    """Authentication strategy for HTTP Basic authentication.

    Handles Authorization: Basic <base64_credentials> header.
    Useful for CLI tools and simple integrations.

    Args:
        authenticate_fn: Async function to validate username/password

    Example:
        async def check_credentials(username: str, password: str) -> UserContext | None:
            user = await get_user_by_email(username)
            if user and verify_password(password, user.password_hash):
                return UserContext(id=user.id, email=user.email)
            return None

        strategy = BasicAuth(authenticate_fn=check_credentials)
    """

    def __init__(self, authenticate_fn: BasicAuthenticateFn) -> None:
        """Initialize BasicAuth.

        Args:
            authenticate_fn: Function to validate credentials
        """
        self._authenticate_fn = authenticate_fn

    def supports(self, headers: Mapping[str, str]) -> bool:
        """Check if request has Basic auth header.

        Args:
            headers: Request headers (lowercase keys)

        Returns:
            True if Authorization: Basic header present
        """
        auth_header = headers.get("authorization", "")
        return auth_header.lower().startswith("basic ")

    async def authenticate(self, headers: Mapping[str, str]) -> UserContext | None:
        """Authenticate using HTTP Basic credentials.

        Args:
            headers: Request headers

        Returns:
            UserContext if credentials valid, None otherwise
        """
        import base64

        auth_header = headers.get("authorization", "")
        if not auth_header.lower().startswith("basic "):
            return None

        try:
            # Decode base64 credentials
            encoded = auth_header[6:]  # Remove "Basic " prefix
            decoded = base64.b64decode(encoded).decode("utf-8")

            # Split into username:password
            if ":" not in decoded:
                return None

            username, password = decoded.split(":", 1)
        except (ValueError, UnicodeDecodeError):
            return None

        return await self._authenticate_fn(username, password)


class HeaderAuth:
    """Authentication strategy for federated mode.

    Hydrates UserContext from gateway headers. Used when an upstream
    auth gateway (Keycloak, Auth0, etc.) has already authenticated
    the user and passes identity via headers.

    Expected headers:
        - x-user-id: Required, user identifier
        - x-email: User's email
        - x-full-name: Optional display name
        - x-roles: Comma-separated roles
        - x-tenants: Comma-separated tenant IDs
        - x-teams: Comma-separated team names

    Example:
        strategy = HeaderAuth()
        # Gateway sets: X-User-ID: user-123, X-Email: user@example.com
        user = await strategy.authenticate(headers)
    """

    def supports(self, headers: Mapping[str, str]) -> bool:
        """Check if request has gateway headers.

        Args:
            headers: Request headers (lowercase keys)

        Returns:
            True if x-user-id header present
        """
        return "x-user-id" in headers

    async def authenticate(self, headers: Mapping[str, str]) -> UserContext | None:
        """Authenticate from gateway headers.

        Args:
            headers: Request headers

        Returns:
            UserContext hydrated from headers, None if required headers missing
        """
        user_id = headers.get("x-user-id")
        email = headers.get("x-email", "")

        if not user_id:
            return None

        # Parse comma-separated lists
        roles_str = headers.get("x-roles", "")
        tenants_str = headers.get("x-tenants", "")
        teams_str = headers.get("x-teams", "")

        roles = [r.strip() for r in roles_str.split(",") if r.strip()]
        tenants = [t.strip() for t in tenants_str.split(",") if t.strip()]
        teams = [t.strip() for t in teams_str.split(",") if t.strip()]

        return UserContext(
            id=user_id,
            email=email,
            name=headers.get("x-full-name"),
            roles=roles,
            tenants=tenants,
            teams=teams,
        )


class AuthChain:
    """Chain of authentication strategies.

    Tries each strategy in order. First strategy that:
    1. supports() returns True
    2. authenticate() returns a UserContext

    ...wins. If no strategy matches, returns None.

    Args:
        strategies: List of authentication strategies to try

    Example:
        chain = AuthChain(strategies=[
            BearerTokenAuth(jwt_secret="..."),
            ApiKeyAuth(api_key_lookup=lookup),
            HeaderAuth(),  # Fallback for federated mode
        ])

        user = await chain.authenticate(headers)
    """

    def __init__(self, strategies: list[Any]) -> None:
        """Initialize AuthChain.

        Args:
            strategies: Ordered list of strategies to try
        """
        self._strategies = strategies

    def supports(self, headers: Mapping[str, str]) -> bool:
        """Check if any strategy supports the request.

        Args:
            headers: Request headers

        Returns:
            True if any strategy supports the request
        """
        return any(s.supports(headers) for s in self._strategies)

    async def authenticate(self, headers: Mapping[str, str]) -> UserContext | None:
        """Authenticate using first matching strategy.

        Args:
            headers: Request headers

        Returns:
            UserContext from first successful strategy, None if none match
        """
        for strategy in self._strategies:
            if strategy.supports(headers):
                result: UserContext | None = await strategy.authenticate(headers)
                if result is not None:
                    return result

        return None


# =============================================================================
# Factory: Create AuthChain from Config
# =============================================================================

# Default strategy order when not configured
DEFAULT_STRATEGY_ORDER = ["bearer", "api_key", "header"]


def create_auth_chain_from_config(
    jwt_secret: str,
    jwt_algorithm: str = "HS256",
    api_key_lookup: ApiKeyLookupFn | None = None,
) -> AuthChain:
    """Create an AuthChain configured from framework_config.toml.

    Reads auth.strategies from config to determine strategy order.
    Falls back to default order if not configured.

    Config example (framework_config.toml):
        [auth]
        strategies = ["bearer", "api_key", "header"]

    Available strategy names:
        - "bearer": JWT Bearer tokens
        - "api_key": X-API-Key header
        - "header": Gateway headers (federated mode)

    Args:
        jwt_secret: Secret for JWT verification
        jwt_algorithm: JWT algorithm (default HS256)
        api_key_lookup: Optional function to look up API keys

    Returns:
        Configured AuthChain

    Example:
        chain = create_auth_chain_from_config(
            jwt_secret="your-secret",
            api_key_lookup=my_lookup_fn,
        )
    """
    from framework_m.cli.config import load_config

    config = load_config()
    auth_config = config.get("auth", {})
    strategy_names = auth_config.get("strategies", DEFAULT_STRATEGY_ORDER)

    # Build strategy instances
    strategies: list[BearerTokenAuth | ApiKeyAuth | HeaderAuth] = []

    for name in strategy_names:
        if name == "bearer":
            strategies.append(BearerTokenAuth(jwt_secret, jwt_algorithm))
        elif name == "api_key" and api_key_lookup is not None:
            strategies.append(ApiKeyAuth(api_key_lookup))
        elif name == "header":
            strategies.append(HeaderAuth())
        # Unknown strategies are silently ignored

    return AuthChain(strategies=strategies)


# =============================================================================
# SessionCookieAuth Strategy
# =============================================================================

# Type alias for user lookup function
UserLookupFn = Callable[[str], Awaitable[Any]]


class SessionCookieAuth:
    """Authentication strategy for browser sessions via cookies.

    Reads session ID from cookie, validates against session store,
    and returns user context.

    Args:
        session_store: Session storage adapter (Database or Redis)
        cookie_name: Name of the session cookie (default: session_id)
        user_lookup: Optional function to look up user by ID

    Example:
        strategy = SessionCookieAuth(
            session_store=DatabaseSessionAdapter(repo),
            cookie_name="session_id",
            user_lookup=get_user_by_id,
        )
        if strategy.supports(headers):
            user = await strategy.authenticate(headers)
    """

    def __init__(
        self,
        session_store: Any,
        cookie_name: str = "session_id",
        user_lookup: UserLookupFn | None = None,
    ) -> None:
        """Initialize SessionCookieAuth.

        Args:
            session_store: Session storage adapter
            cookie_name: Cookie name to read session ID from
            user_lookup: Optional function to get user details
        """
        self._session_store = session_store
        self._cookie_name = cookie_name
        self._user_lookup = user_lookup

    def supports(self, headers: Mapping[str, str]) -> bool:
        """Check if request has session cookie.

        Args:
            headers: Request headers (lowercase keys)

        Returns:
            True if session cookie present
        """
        cookie_header = headers.get("cookie", "")
        return f"{self._cookie_name}=" in cookie_header

    def _parse_cookie(self, cookie_header: str) -> str | None:
        """Parse session ID from cookie header.

        Args:
            cookie_header: Raw cookie header string

        Returns:
            Session ID or None if not found
        """
        for part in cookie_header.split(";"):
            part = part.strip()
            if part.startswith(f"{self._cookie_name}="):
                return part[len(self._cookie_name) + 1 :]
        return None

    async def authenticate(self, headers: Mapping[str, str]) -> UserContext | None:
        """Authenticate using session cookie.

        Args:
            headers: Request headers

        Returns:
            UserContext if session valid, None otherwise
        """
        cookie_header = headers.get("cookie", "")
        session_id = self._parse_cookie(cookie_header)

        if not session_id:
            return None

        # Get session from store
        session_data = await self._session_store.get(session_id)
        if session_data is None:
            return None

        # If we have a user lookup function, use it for full user details
        if self._user_lookup:
            user = await self._user_lookup(session_data.user_id)
            if user is None:
                return None

            return UserContext(
                id=user.id,
                email=getattr(user, "email", ""),
                name=getattr(user, "full_name", None),
                roles=getattr(user, "roles", []),
            )

        # Otherwise return basic context from session
        return UserContext(
            id=session_data.user_id,
            email="",
        )


__all__ = [
    "ApiKeyAuth",
    "AuthChain",
    "BasicAuth",
    "BearerTokenAuth",
    "HeaderAuth",
    "SessionCookieAuth",
    "create_auth_chain_from_config",
]
