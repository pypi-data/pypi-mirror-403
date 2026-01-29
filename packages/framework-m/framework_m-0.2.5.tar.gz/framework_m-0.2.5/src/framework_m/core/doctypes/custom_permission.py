"""CustomPermission DocType - Database overrides for permissions.

This DocType allows administrators to override the code-first permissions
defined in DocType.Meta with database-stored permission rules.

Use Cases:
- Grant a specific user extra permissions beyond their role
- Deny a specific user access even if their role allows it
- Add temporary permissions during a project
- Create tenant-specific permission overrides

Example:
    # Give user "alice" read access to "Invoice" regardless of role
    perm = CustomPermission(
        name="allow-alice-invoice-read",
        for_user="alice",
        doctype_name="Invoice",
        action="read",
        effect=PermissionEffect.ALLOW,
    )

    # Deny all users with "Intern" role from deleting any DocType
    perm = CustomPermission(
        name="deny-intern-delete",
        for_role="Intern",
        doctype_name="*",  # All DocTypes
        action="delete",
        effect=PermissionEffect.DENY,
    )
"""

from __future__ import annotations

from enum import StrEnum
from typing import ClassVar

from pydantic import Field

from framework_m.core.domain.base_doctype import BaseDocType


class PermissionEffect(StrEnum):
    """Effect of the custom permission rule."""

    ALLOW = "allow"  # Explicitly grant permission
    DENY = "deny"  # Explicitly deny permission


class CustomPermission(BaseDocType):
    """Database-stored permission override.

    Allows admins to override code-first permissions with database rules.
    Evaluated in the RbacPermissionAdapter alongside Meta.permissions.

    Evaluation Priority:
    1. Explicit DENY rules are checked first (deny wins)
    2. If no deny, explicit ALLOW rules are checked
    3. If no explicit rule, fall back to code-first Meta.permissions

    Attributes:
        for_user: Optional user ID this rule applies to
        for_role: Optional role name this rule applies to
        doctype_name: The DocType this permission applies to ("*" for all)
        action: The action (read, write, create, delete, submit, etc.)
        effect: Whether to ALLOW or DENY the permission
        enabled: Whether this rule is active
        priority: Rule priority (higher = evaluated first)
        description: Human-readable description of why this rule exists
    """

    # Target specification (at least one of for_user or for_role required)
    for_user: str | None = Field(
        default=None,
        description="User ID this rule applies to (None = all users)",
    )
    for_role: str | None = Field(
        default=None,
        description="Role name this rule applies to (None = all roles)",
    )

    # Permission specification
    doctype_name: str = Field(
        description="DocType name or '*' for all DocTypes",
    )
    action: str = Field(
        description="Action: read, write, create, delete, submit, cancel, amend",
    )
    effect: PermissionEffect = Field(
        default=PermissionEffect.ALLOW,
        description="Whether to allow or deny this permission",
    )

    # Control
    enabled: bool = Field(
        default=True,
        description="Whether this rule is active",
    )
    priority: int = Field(
        default=0,
        description="Rule priority (higher = evaluated first)",
    )
    description: str | None = Field(
        default=None,
        description="Why this rule exists (for audit)",
    )

    class Meta:
        requires_auth: ClassVar[bool] = True
        apply_rls: ClassVar[bool] = False  # Admins see all permission rules
        permissions: ClassVar[dict[str, list[str]]] = {
            "read": ["Admin", "System"],
            "write": ["Admin"],
            "create": ["Admin"],
            "delete": ["Admin"],
        }


__all__ = ["CustomPermission", "PermissionEffect"]
