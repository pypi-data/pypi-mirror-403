"""Tests for PermissionLookupService.

TDD tests for CustomPermission database overrides lookup.
"""

import pytest

from framework_m.core.doctypes.custom_permission import (
    CustomPermission,
    PermissionEffect,
)
from framework_m.core.permission_lookup import PermissionLookupService


class TestPermissionLookupService:
    """Tests for PermissionLookupService."""

    @pytest.fixture(autouse=True)
    def clear_rules(self) -> None:
        """Clear rules before each test."""
        PermissionLookupService.clear_rules()
        yield
        PermissionLookupService.clear_rules()

    def test_register_rule(self) -> None:
        """Should register a permission rule."""
        rule = CustomPermission(
            name="test-rule",
            for_user="alice",
            doctype_name="Invoice",
            action="read",
            effect=PermissionEffect.ALLOW,
        )
        PermissionLookupService.register_rule(rule)

        rules = PermissionLookupService.find_rules(
            user_id="alice",
            roles=[],
            doctype="Invoice",
            action="read",
        )
        assert len(rules) == 1
        assert rules[0].name == "test-rule"

    def test_find_rules_by_user(self) -> None:
        """Should find rules matching specific user."""
        PermissionLookupService.register_rule(
            CustomPermission(
                name="for-alice",
                for_user="alice",
                doctype_name="Invoice",
                action="read",
                effect=PermissionEffect.ALLOW,
            )
        )
        PermissionLookupService.register_rule(
            CustomPermission(
                name="for-bob",
                for_user="bob",
                doctype_name="Invoice",
                action="read",
                effect=PermissionEffect.ALLOW,
            )
        )

        rules = PermissionLookupService.find_rules(
            user_id="alice",
            roles=[],
            doctype="Invoice",
            action="read",
        )
        assert len(rules) == 1
        assert rules[0].name == "for-alice"

    def test_find_rules_by_role(self) -> None:
        """Should find rules matching user roles."""
        PermissionLookupService.register_rule(
            CustomPermission(
                name="for-managers",
                for_role="Manager",
                doctype_name="Invoice",
                action="delete",
                effect=PermissionEffect.ALLOW,
            )
        )

        rules = PermissionLookupService.find_rules(
            user_id="alice",
            roles=["Employee", "Manager"],
            doctype="Invoice",
            action="delete",
        )
        assert len(rules) == 1
        assert rules[0].name == "for-managers"

    def test_find_rules_wildcard_doctype(self) -> None:
        """Should match rules with wildcard doctype."""
        PermissionLookupService.register_rule(
            CustomPermission(
                name="deny-all-delete",
                for_role="Intern",
                doctype_name="*",
                action="delete",
                effect=PermissionEffect.DENY,
            )
        )

        rules = PermissionLookupService.find_rules(
            user_id="intern1",
            roles=["Intern"],
            doctype="Invoice",
            action="delete",
        )
        assert len(rules) == 1
        assert rules[0].effect == PermissionEffect.DENY

    def test_deny_rules_come_first(self) -> None:
        """DENY rules should be sorted before ALLOW rules."""
        PermissionLookupService.register_rule(
            CustomPermission(
                name="allow-rule",
                for_user="alice",
                doctype_name="Invoice",
                action="read",
                effect=PermissionEffect.ALLOW,
            )
        )
        PermissionLookupService.register_rule(
            CustomPermission(
                name="deny-rule",
                for_user="alice",
                doctype_name="Invoice",
                action="read",
                effect=PermissionEffect.DENY,
            )
        )

        rules = PermissionLookupService.find_rules(
            user_id="alice",
            roles=[],
            doctype="Invoice",
            action="read",
        )
        assert len(rules) == 2
        assert rules[0].effect == PermissionEffect.DENY  # DENY first

    def test_check_permission_deny(self) -> None:
        """check_permission should return False for deny rules."""
        PermissionLookupService.register_rule(
            CustomPermission(
                name="deny-alice",
                for_user="alice",
                doctype_name="Invoice",
                action="delete",
                effect=PermissionEffect.DENY,
                description="Alice cannot delete invoices",
            )
        )

        result, reason = PermissionLookupService.check_permission(
            user_id="alice",
            roles=["Employee"],
            doctype="Invoice",
            action="delete",
        )
        assert result is False
        assert "deny-alice" in reason

    def test_check_permission_allow(self) -> None:
        """check_permission should return True for allow rules."""
        PermissionLookupService.register_rule(
            CustomPermission(
                name="allow-alice-read",
                for_user="alice",
                doctype_name="Invoice",
                action="read",
                effect=PermissionEffect.ALLOW,
            )
        )

        result, reason = PermissionLookupService.check_permission(
            user_id="alice",
            roles=[],
            doctype="Invoice",
            action="read",
        )
        assert result is True
        assert "allow-alice-read" in reason

    def test_check_permission_no_match(self) -> None:
        """check_permission should return None if no matching rule."""
        result, reason = PermissionLookupService.check_permission(
            user_id="unknown",
            roles=["Guest"],
            doctype="Invoice",
            action="read",
        )
        assert result is None
        assert reason == ""

    def test_disabled_rules_skipped(self) -> None:
        """Disabled rules should not be matched."""
        PermissionLookupService.register_rule(
            CustomPermission(
                name="disabled-rule",
                for_user="alice",
                doctype_name="Invoice",
                action="read",
                effect=PermissionEffect.ALLOW,
                enabled=False,
            )
        )

        rules = PermissionLookupService.find_rules(
            user_id="alice",
            roles=[],
            doctype="Invoice",
            action="read",
        )
        assert len(rules) == 0

    def test_priority_sorting(self) -> None:
        """Higher priority rules should come first."""
        PermissionLookupService.register_rule(
            CustomPermission(
                name="low-priority",
                for_user="alice",
                doctype_name="Invoice",
                action="read",
                effect=PermissionEffect.ALLOW,
                priority=1,
            )
        )
        PermissionLookupService.register_rule(
            CustomPermission(
                name="high-priority",
                for_user="alice",
                doctype_name="Invoice",
                action="read",
                effect=PermissionEffect.ALLOW,
                priority=10,
            )
        )

        rules = PermissionLookupService.find_rules(
            user_id="alice",
            roles=[],
            doctype="Invoice",
            action="read",
        )
        assert len(rules) == 2
        assert rules[0].name == "high-priority"
