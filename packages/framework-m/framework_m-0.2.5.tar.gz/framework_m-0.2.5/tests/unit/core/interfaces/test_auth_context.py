"""Tests for AuthContextProtocol interface compliance."""

from framework_m.core.interfaces.auth_context import (
    AuthContextProtocol,
    UserContext,
)


class TestUserContext:
    """Tests for UserContext model."""

    def test_user_context_creation(self) -> None:
        """UserContext should create with required fields."""
        user = UserContext(
            id="user-001",
            email="test@example.com",
            roles=["Employee", "Manager"],
            tenants=["tenant-001"],
        )
        assert user.id == "user-001"
        assert user.email == "test@example.com"
        assert user.roles == ["Employee", "Manager"]
        assert user.tenants == ["tenant-001"]

    def test_user_context_with_empty_roles(self) -> None:
        """UserContext should accept empty roles list."""
        user = UserContext(
            id="user-001",
            email="test@example.com",
            roles=[],
            tenants=[],
        )
        assert user.roles == []
        assert user.tenants == []

    def test_user_context_has_role(self) -> None:
        """UserContext.has_role should check for role membership."""
        user = UserContext(
            id="user-001",
            email="test@example.com",
            roles=["Employee", "Manager"],
            tenants=[],
        )
        assert user.has_role("Manager") is True
        assert user.has_role("Admin") is False

    def test_user_context_is_system_user(self) -> None:
        """UserContext.is_system_user should check for System role."""
        regular_user = UserContext(
            id="user-001",
            email="test@example.com",
            roles=["Employee"],
            tenants=[],
        )
        system_user = UserContext(
            id="system",
            email="system@localhost",
            roles=["System"],
            tenants=[],
        )
        assert regular_user.is_system_user is False
        assert system_user.is_system_user is True

    def test_user_context_optional_name(self) -> None:
        """UserContext should have optional name field."""
        user = UserContext(
            id="user-001",
            email="test@example.com",
            name="John Doe",
            roles=[],
            tenants=[],
        )
        assert user.name == "John Doe"

    def test_user_context_name_defaults_none(self) -> None:
        """UserContext name should default to None."""
        user = UserContext(
            id="user-001",
            email="test@example.com",
            roles=[],
            tenants=[],
        )
        assert user.name is None


class TestUserContextAttributes:
    """Tests for UserContext ABAC attributes."""

    def test_user_context_with_attributes(self) -> None:
        """UserContext should accept attributes dict."""
        user = UserContext(
            id="user-001",
            email="test@example.com",
            attributes={
                "department": "engineering",
                "level": 3,
                "roles": ["developer"],
            },
        )
        assert user.attributes["department"] == "engineering"
        assert user.attributes["level"] == 3

    def test_get_attribute(self) -> None:
        """get_attribute should return attribute value."""
        user = UserContext(
            id="user-001",
            email="test@example.com",
            attributes={"department": "sales", "level": 5},
        )
        assert user.get_attribute("department") == "sales"
        assert user.get_attribute("level") == 5

    def test_get_attribute_with_default(self) -> None:
        """get_attribute should return default for missing key."""
        user = UserContext(
            id="user-001",
            email="test@example.com",
            attributes={},
        )
        assert user.get_attribute("department", "unknown") == "unknown"
        assert user.get_attribute("missing") is None

    def test_has_attribute(self) -> None:
        """has_attribute should check attribute value."""
        user = UserContext(
            id="user-001",
            email="test@example.com",
            attributes={"department": "engineering"},
        )
        assert user.has_attribute("department", "engineering") is True
        assert user.has_attribute("department", "sales") is False

    def test_has_role_from_attributes(self) -> None:
        """has_role should check attributes.roles list."""
        user = UserContext(
            id="user-001",
            email="test@example.com",
            roles=[],  # Legacy roles empty
            attributes={"roles": ["admin", "developer"]},
        )
        assert user.has_role("admin") is True
        assert user.has_role("developer") is True
        assert user.has_role("manager") is False

    def test_has_role_legacy_takes_precedence(self) -> None:
        """has_role should check legacy roles first."""
        user = UserContext(
            id="user-001",
            email="test@example.com",
            roles=["Manager"],  # Legacy role
            attributes={"roles": ["developer"]},  # ABAC role
        )
        assert user.has_role("Manager") is True  # From legacy
        assert user.has_role("developer") is True  # From ABAC

    def test_is_system_user_from_attributes(self) -> None:
        """is_system_user should work with attributes.roles."""
        user = UserContext(
            id="system",
            email="system@localhost",
            roles=[],  # Legacy empty
            attributes={"roles": ["System"]},
        )
        assert user.is_system_user is True


class TestAuthContextProtocol:
    """Tests for AuthContextProtocol interface."""

    def test_protocol_has_get_current_user_method(self) -> None:
        """AuthContextProtocol should define get_current_user method."""
        assert hasattr(AuthContextProtocol, "get_current_user")

    def test_protocol_has_get_user_by_id_method(self) -> None:
        """AuthContextProtocol should define get_user_by_id method."""
        assert hasattr(AuthContextProtocol, "get_user_by_id")
