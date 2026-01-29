"""Tests for CustomPermission DocType.

TDD tests for customizable permission overrides stored in the database.
Tests written FIRST per CONTRIBUTING.md guidelines.
"""

from typing import ClassVar

from framework_m.core.doctypes.custom_permission import (
    CustomPermission,
    PermissionEffect,
)
from framework_m.core.domain.base_doctype import BaseDocType

# =============================================================================
# Test DocTypes
# =============================================================================


class Invoice(BaseDocType):
    """Test DocType with standard permissions."""

    amount: float = 0.0

    class Meta:
        requires_auth: ClassVar[bool] = True
        apply_rls: ClassVar[bool] = True
        permissions: ClassVar[dict[str, list[str]]] = {
            "read": ["Employee", "Manager"],
            "write": ["Manager"],
            "delete": ["Admin"],
        }


# =============================================================================
# Tests for CustomPermission DocType
# =============================================================================


class TestCustomPermissionDocType:
    """Test CustomPermission DocType structure."""

    def test_custom_permission_is_doctype(self) -> None:
        """CustomPermission should be a BaseDocType."""
        assert issubclass(CustomPermission, BaseDocType)

    def test_can_create_user_allow_rule(self) -> None:
        """Can create a rule to allow a specific user."""
        perm = CustomPermission(
            name="allow-alice-invoice-read",
            for_user="alice",
            doctype_name="Invoice",
            action="read",
            effect=PermissionEffect.ALLOW,
        )

        assert perm.for_user == "alice"
        assert perm.doctype_name == "Invoice"
        assert perm.action == "read"
        assert perm.effect == PermissionEffect.ALLOW
        assert perm.enabled is True

    def test_can_create_role_deny_rule(self) -> None:
        """Can create a rule to deny a role."""
        perm = CustomPermission(
            name="deny-intern-delete",
            for_role="Intern",
            doctype_name="*",
            action="delete",
            effect=PermissionEffect.DENY,
        )

        assert perm.for_role == "Intern"
        assert perm.doctype_name == "*"
        assert perm.effect == PermissionEffect.DENY

    def test_can_disable_rule(self) -> None:
        """Rules can be disabled."""
        perm = CustomPermission(
            name="disabled-rule",
            for_role="Guest",
            doctype_name="Invoice",
            action="read",
            effect=PermissionEffect.ALLOW,
            enabled=False,
        )

        assert perm.enabled is False

    def test_priority_default_is_zero(self) -> None:
        """Default priority should be 0."""
        perm = CustomPermission(
            name="test-rule",
            for_role="Guest",
            doctype_name="Invoice",
            action="read",
        )

        assert perm.priority == 0

    def test_can_set_priority(self) -> None:
        """Custom priority can be set."""
        perm = CustomPermission(
            name="high-priority-rule",
            for_role="VIP",
            doctype_name="SecretDoc",
            action="read",
            priority=100,
        )

        assert perm.priority == 100

    def test_only_admin_can_manage(self) -> None:
        """CustomPermission should only be manageable by Admin."""
        permissions = CustomPermission.get_permissions()

        assert permissions["read"] == ["Admin", "System"]
        assert permissions["write"] == ["Admin"]
        assert permissions["create"] == ["Admin"]
        assert permissions["delete"] == ["Admin"]


class TestCustomPermissionMatching:
    """Test CustomPermission matching logic."""

    def test_matches_specific_user(self) -> None:
        """Rule with for_user matches that specific user."""
        perm = CustomPermission(
            name="test",
            for_user="alice",
            doctype_name="Invoice",
            action="read",
        )

        # Should match alice
        assert perm.for_user == "alice"
        # Should not match bob (no wildcard)
        assert perm.for_user != "bob"

    def test_matches_wildcard_doctype(self) -> None:
        """Rule with doctype='*' should match any doctype."""
        perm = CustomPermission(
            name="test",
            for_role="Intern",
            doctype_name="*",
            action="delete",
            effect=PermissionEffect.DENY,
        )

        # The '*' means it applies to all doctypes
        assert perm.doctype_name == "*"

    def test_matches_specific_doctype(self) -> None:
        """Rule with specific doctype matches that doctype only."""
        perm = CustomPermission(
            name="test",
            for_role="Sales",
            doctype_name="Customer",
            action="read",
        )

        assert perm.doctype_name == "Customer"


class TestPermissionEffectEnum:
    """Test PermissionEffect enum."""

    def test_allow_value(self) -> None:
        """ALLOW should have correct string value."""
        assert PermissionEffect.ALLOW == "allow"

    def test_deny_value(self) -> None:
        """DENY should have correct string value."""
        assert PermissionEffect.DENY == "deny"
