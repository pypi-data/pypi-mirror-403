"""Permission Lookup Service - CustomPermission registry and lookup.

This module provides an in-memory registry for CustomPermission rules
that can be used by the RbacPermissionAdapter to check database overrides.

Rules can be:
1. Registered programmatically via `register_rule()`
2. Loaded from database at application startup
3. Cached for performance

Example:
    from framework_m.core.permission_lookup import PermissionLookupService
    from framework_m.core.doctypes.custom_permission import CustomPermission, PermissionEffect

    # Register a rule programmatically
    rule = CustomPermission(
        name="allow-alice-invoice-read",
        for_user="alice",
        doctype_name="Invoice",
        action="read",
        effect=PermissionEffect.ALLOW,
    )
    PermissionLookupService.register_rule(rule)

    # Find matching rules
    rules = PermissionLookupService.find_rules(
        user_id="alice",
        roles=["Employee"],
        doctype="Invoice",
        action="read",
    )
"""

from __future__ import annotations

from typing import ClassVar

from framework_m.core.doctypes.custom_permission import (
    CustomPermission,
    PermissionEffect,
)


class PermissionLookupService:
    """In-memory registry for CustomPermission rules.

    Provides fast lookup of permission overrides without database queries.
    Rules should be loaded from database at application startup.

    Thread-safe for reads. For production, consider using proper caching.

    Attributes:
        _rules: Class-level list of registered permission rules
        _deny_first: Whether DENY rules are evaluated before ALLOW (default: True)

    Example:
        # Register at startup
        for rule in await repo.list_all_permissions():
            PermissionLookupService.register_rule(rule)

        # Check in permission adapter
        rules = PermissionLookupService.find_rules(user_id, roles, doctype, action)
    """

    _rules: ClassVar[list[CustomPermission]] = []
    _deny_first: ClassVar[bool] = True

    @classmethod
    def register_rule(cls, rule: CustomPermission) -> None:
        """Register a permission rule.

        Args:
            rule: CustomPermission rule to register

        Example:
            PermissionLookupService.register_rule(CustomPermission(
                name="deny-intern-delete",
                for_role="Intern",
                doctype_name="*",
                action="delete",
                effect=PermissionEffect.DENY,
            ))
        """
        cls._rules.append(rule)

    @classmethod
    def register_rules(cls, rules: list[CustomPermission]) -> None:
        """Register multiple permission rules.

        Args:
            rules: List of CustomPermission rules to register
        """
        cls._rules.extend(rules)

    @classmethod
    def clear_rules(cls) -> None:
        """Clear all registered rules. Useful for testing."""
        cls._rules = []

    @classmethod
    def find_rules(
        cls,
        user_id: str,
        roles: list[str],
        doctype: str,
        action: str,
    ) -> list[CustomPermission]:
        """Find matching permission rules for a user/action.

        Returns rules sorted by:
        1. DENY rules first (if _deny_first is True)
        2. Higher priority first
        3. More specific rules first (user > role > wildcard)

        Args:
            user_id: User ID to check
            roles: User's roles
            doctype: DocType name
            action: Action (read, write, create, delete, etc.)

        Returns:
            List of matching CustomPermission rules, sorted by priority
        """
        matching: list[CustomPermission] = []

        for rule in cls._rules:
            # Skip disabled rules
            if not rule.enabled:
                continue

            # Check doctype match
            if rule.doctype_name != "*" and rule.doctype_name != doctype:
                continue

            # Check action match
            if rule.action != "*" and rule.action != action:
                continue

            # Check user/role match
            user_match = rule.for_user is not None and rule.for_user == user_id
            role_match = rule.for_role is not None and rule.for_role in roles
            applies_to_all = rule.for_user is None and rule.for_role is None

            if user_match or role_match or applies_to_all:
                matching.append(rule)

        # Sort by priority (higher first), then DENY first if enabled
        def sort_key(r: CustomPermission) -> tuple[int, int, int]:
            deny_priority = 0 if r.effect == PermissionEffect.DENY else 1
            # Specificity: user > role > wildcard
            specificity = 0
            if r.for_user is not None:
                specificity = 2
            elif r.for_role is not None:
                specificity = 1
            return (
                deny_priority if cls._deny_first else 0,
                -r.priority,  # Negative for descending
                -specificity,  # Negative for descending
            )

        return sorted(matching, key=sort_key)

    @classmethod
    def check_permission(
        cls,
        user_id: str,
        roles: list[str],
        doctype: str,
        action: str,
    ) -> tuple[bool | None, str]:
        """Check if custom permissions grant or deny access.

        Returns:
            Tuple of (authorized, reason):
            - (True, reason) if explicitly allowed
            - (False, reason) if explicitly denied
            - (None, "") if no matching rule (fall back to code-first)
        """
        rules = cls.find_rules(user_id, roles, doctype, action)

        if not rules:
            return None, ""

        # First rule wins (already sorted by priority/deny-first)
        first_rule = rules[0]

        if first_rule.effect == PermissionEffect.DENY:
            reason = f"Denied by rule '{first_rule.name}'"
            if first_rule.description:
                reason += f": {first_rule.description}"
            return False, reason

        if first_rule.effect == PermissionEffect.ALLOW:
            reason = f"Allowed by rule '{first_rule.name}'"
            if first_rule.description:
                reason += f": {first_rule.description}"
            return True, reason

        return None, ""


__all__ = ["PermissionLookupService"]
