"""Auth Context Protocol - Core interface for authentication context.

This module defines the AuthContextProtocol for accessing the current
authenticated user and their permissions context.

The framework is stateless - user context comes from JWT/headers,
not server-side sessions.
"""

from typing import Any, Protocol

from pydantic import BaseModel, Field, computed_field


class UserContext(BaseModel):
    """Represents the current authenticated user.

    Contains identity and authorization information.
    Populated from JWT claims or request headers.

    Attributes:
        id: Unique user identifier
        email: User's email address
        name: Optional display name
        roles: List of assigned roles (legacy, now in attributes)
        tenants: List of accessible tenant IDs (for multi-tenancy)
        teams: List of team memberships
        attributes: ABAC attributes dict (department, level, roles, etc.)

    The `attributes` dict is the primary source for ABAC decisions:
        {"department": "sales", "level": 5, "roles": ["admin", "user"]}

    Example:
        user = UserContext(
            id="user-001",
            email="john@example.com",
            name="John Doe",
            attributes={
                "department": "engineering",
                "level": 3,
                "roles": ["developer", "reviewer"],
            },
        )
        user.has_role("developer")  # True
        user.get_attribute("department")  # "engineering"
    """

    id: str
    email: str
    name: str | None = None
    roles: list[str] = Field(default_factory=list)
    tenants: list[str] = Field(default_factory=list)
    teams: list[str] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(
        default_factory=dict,
        description="ABAC attributes (department, level, roles, etc.)",
    )

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role.

        Checks both legacy `roles` list and `attributes.roles` for
        backward compatibility.

        Args:
            role: Role name to check

        Returns:
            True if user has the role
        """
        # Check legacy roles field first
        if role in self.roles:
            return True
        # Then check attributes.roles (ABAC style)
        attr_roles = self.attributes.get("roles", [])
        if isinstance(attr_roles, list):
            return role in attr_roles
        return False

    def get_attribute(self, key: str, default: Any = None) -> Any:
        """Get a user attribute value.

        Args:
            key: Attribute key (e.g., "department", "level")
            default: Default value if attribute not present

        Returns:
            Attribute value or default
        """
        return self.attributes.get(key, default)

    def has_attribute(self, key: str, value: Any) -> bool:
        """Check if user has specific attribute value.

        Args:
            key: Attribute key
            value: Expected value

        Returns:
            True if attribute matches value
        """
        result: bool = self.attributes.get(key) == value
        return result

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_system_user(self) -> bool:
        """Check if this is the system user.

        System user has special privileges for background tasks
        and internal operations.

        Returns:
            True if user has System role
        """
        return self.has_role("System")


class AuthContextProtocol(Protocol):
    """Protocol defining the contract for authentication context.

    This is the primary port for accessing user identity in the hexagonal
    architecture. Implementations extract user context from various sources:

    - JWT tokens (production)
    - Request headers (microservice communication)
    - Test fixtures (testing)

    Example usage:
        auth: AuthContextProtocol = container.get(AuthContextProtocol)
        user = await auth.get_current_user()
        if user.has_role("Admin"):
            # Allow admin action
            pass
    """

    async def get_current_user(self) -> UserContext:
        """Get the current authenticated user from request context.

        Returns:
            UserContext for the authenticated user

        Raises:
            AuthenticationError: If no valid authentication is present
        """
        ...

    async def get_user_by_id(self, user_id: str) -> UserContext | None:
        """Look up a user by their ID.

        Used for permission checks on document ownership, etc.

        Args:
            user_id: The user's unique identifier

        Returns:
            UserContext if user found, None otherwise
        """
        ...


__all__ = [
    "AuthContextProtocol",
    "UserContext",
]
