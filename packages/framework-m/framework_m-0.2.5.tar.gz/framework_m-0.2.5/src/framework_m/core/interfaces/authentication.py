"""AuthenticationProtocol - Interface for pluggable authentication strategies.

This module defines the protocol that all authentication strategies must implement.
Strategies are responsible for:
1. Detecting if they can handle a request (supports)
2. Extracting user identity from the request (authenticate)

The framework uses a chain-of-responsibility pattern where multiple strategies
are tried in order until one succeeds.

Example:
    class MyCustomAuth:
        def supports(self, headers: Mapping[str, str]) -> bool:
            return "x-my-token" in headers

        async def authenticate(self, headers: Mapping[str, str]) -> UserContext | None:
            token = headers.get("x-my-token")
            # Validate and return user...
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from framework_m.core.interfaces.auth_context import UserContext


@runtime_checkable
class AuthenticationProtocol(Protocol):
    """Protocol for pluggable authentication strategies.

    Strategies are responsible for:
    1. Detecting if they can handle a request (via supports())
    2. Extracting user identity from the request (via authenticate())

    The framework uses multiple strategies in a chain. The first strategy
    that supports the request and successfully authenticates wins.

    Methods:
        supports: Check if this strategy can handle the request
        authenticate: Extract user identity from request

    Example implementation:
        class BearerTokenAuth:
            def supports(self, headers: Mapping[str, str]) -> bool:
                auth_header = headers.get("authorization", "")
                return auth_header.startswith("Bearer ")

            async def authenticate(
                self, headers: Mapping[str, str]
            ) -> UserContext | None:
                token = headers.get("authorization", "")[7:]
                # Validate token and return user...
    """

    def supports(self, headers: Mapping[str, str]) -> bool:
        """Check if this strategy can handle the request.

        Called before authenticate() to determine if this strategy
        should be used. Should be a fast, synchronous check.

        Args:
            headers: Request headers (lowercase keys)

        Returns:
            True if this strategy can handle the request
        """
        ...

    async def authenticate(self, headers: Mapping[str, str]) -> UserContext | None:
        """Authenticate the request and extract user identity.

        Called only if supports() returned True.

        Args:
            headers: Request headers (lowercase keys)

        Returns:
            UserContext if authentication successful, None otherwise
        """
        ...


__all__ = ["AuthenticationProtocol"]
