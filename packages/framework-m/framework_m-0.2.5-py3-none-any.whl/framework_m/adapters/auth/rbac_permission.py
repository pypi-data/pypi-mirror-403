"""RBAC Permission Adapter - Role-Based Access Control implementation.

This module provides the RbacPermissionAdapter, a simple RBAC implementation
that reads permissions from DocType.Meta.permissions and checks against user roles.

Key Features:
- Code-first permissions defined in DocType.Meta
- Role matching against principal_attributes["roles"]
- Row-Level Security (RLS) via owner filtering
- Admin bypass for full access

Example:
    class Invoice(BaseDocType):
        class Meta:
            permissions = {
                "read": ["Employee", "Manager"],
                "write": ["Manager"],
            }

    adapter = RbacPermissionAdapter()
    result = await adapter.evaluate(PolicyEvaluateRequest(
        principal="user-123",
        action=PermissionAction.READ,
        resource="Invoice",
        principal_attributes={"roles": ["Employee"]},
    ))
    # result.authorized == True
"""

from __future__ import annotations

from typing import Any

from framework_m.core.interfaces.permission import (
    DecisionSource,
    PermissionAction,
    PermissionProtocol,
    PolicyEvaluateRequest,
    PolicyEvaluateResult,
)
from framework_m.core.registry import MetaRegistry


class RbacPermissionAdapter(PermissionProtocol):
    """Role-Based Access Control permission adapter.

    Implements PermissionProtocol using simple role matching against
    permissions defined in DocType.Meta.permissions.

    Attributes:
        admin_roles: Roles that bypass permission checks (default: ["Admin", "System"])

    Example:
        adapter = RbacPermissionAdapter()
        result = await adapter.evaluate(request)
        if result.authorized:
            # Allow access
    """

    def __init__(
        self,
        admin_roles: list[str] | None = None,
    ) -> None:
        """Initialize the RBAC adapter.

        Args:
            admin_roles: Roles that bypass all permission checks.
                        Defaults to ["Admin", "System"]
        """
        self.admin_roles = admin_roles or ["Admin", "System"]
        self._registry = MetaRegistry.get_instance()

    async def evaluate(
        self,
        request: PolicyEvaluateRequest,
    ) -> PolicyEvaluateResult:
        """Evaluate a permission request using RBAC.

        Checks if the user's roles match any of the allowed roles
        for the requested action on the DocType.

        Args:
            request: Stateless request containing principal, action, resource

        Returns:
            PolicyEvaluateResult with authorized=True if allowed
        """
        # Get user roles from principal_attributes
        user_roles: list[str] = request.principal_attributes.get("roles", [])

        # Check if user has admin role (bypass all checks)
        if self._has_admin_role(user_roles, request.principal_attributes):
            return PolicyEvaluateResult(
                authorized=True,
                decision_source=DecisionSource.RBAC,
                reason="Admin role grants full access",
            )

        # Normalize action to string
        action_str = (
            request.action.value
            if isinstance(request.action, PermissionAction)
            else str(request.action)
        )

        # Check CustomPermission overrides (database rules)
        from framework_m.core.permission_lookup import PermissionLookupService

        custom_result, custom_reason = PermissionLookupService.check_permission(
            user_id=request.principal,
            roles=user_roles,
            doctype=request.resource,
            action=action_str,
        )

        # If custom rule explicitly denies or allows, use that result
        if custom_result is not None:
            return PolicyEvaluateResult(
                authorized=custom_result,
                decision_source=DecisionSource.CUSTOM,
                reason=custom_reason,
            )

        # Fall back to code-first permissions from DocType.Meta
        try:
            doctype_class = self._registry.get_doctype(request.resource)
        except Exception:
            return PolicyEvaluateResult(
                authorized=False,
                decision_source=DecisionSource.RBAC,
                reason=f"DocType '{request.resource}' not found in registry",
            )

        if doctype_class is None:
            return PolicyEvaluateResult(
                authorized=False,
                decision_source=DecisionSource.RBAC,
                reason=f"DocType '{request.resource}' not found in registry",
            )

        # Get permissions from DocType.Meta
        permissions = doctype_class.get_permissions()

        # Check if action is defined in permissions
        if action_str not in permissions:
            return PolicyEvaluateResult(
                authorized=False,
                decision_source=DecisionSource.RBAC,
                reason=f"Action '{action_str}' not defined for DocType '{request.resource}'",
            )

        # Get allowed roles for this action
        allowed_roles: list[str] = permissions.get(action_str, [])

        # Check for 'All' role - means everyone is allowed (including anonymous)
        if "All" in allowed_roles:
            return PolicyEvaluateResult(
                authorized=True,
                decision_source=DecisionSource.RBAC,
                reason=f"'All' role grants access to {action_str} for everyone",
            )

        # Check if any user role is in allowed roles
        matching_roles = set(user_roles) & set(allowed_roles)
        if matching_roles:
            return PolicyEvaluateResult(
                authorized=True,
                decision_source=DecisionSource.RBAC,
                reason=f"Role(s) {list(matching_roles)} allowed for {action_str}",
            )

        return PolicyEvaluateResult(
            authorized=False,
            decision_source=DecisionSource.RBAC,
            reason=f"None of user's roles {user_roles} are in allowed roles {allowed_roles}",
        )

    async def get_permitted_filters(
        self,
        principal: str,
        principal_attributes: dict[str, Any],
        resource: str,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        """Get Row-Level Security filters for a query.

        For RBAC, RLS filtering is based on Meta.rls_field:
        - "owner" (default): WHERE owner = :user_id
        - "team" or custom field: WHERE field IN :user_teams

        Args:
            principal: User ID
            principal_attributes: User attributes including roles and teams
            resource: DocType name
            tenant_id: Optional tenant context

        Returns:
            Filter dict to apply to queries. Empty dict means no filtering.
        """
        user_roles: list[str] = principal_attributes.get("roles", [])

        # Admin/System users see all documents
        if self._has_admin_role(user_roles, principal_attributes):
            return {}

        # Check if DocType has RLS enabled and get rls_field
        rls_field = "owner"  # Default
        try:
            doctype_class = self._registry.get_doctype(resource)
            if doctype_class is not None:
                apply_rls = doctype_class.get_apply_rls()
                if not apply_rls:
                    return {}  # RLS disabled for this DocType
                rls_field = doctype_class.get_rls_field()
        except Exception:
            # DocType not found - apply owner filter for safety
            pass

        # Apply RLS based on rls_field
        if rls_field == "owner":
            # Default: filter by owner (user id)
            return {"owner": principal}
        else:
            # Team-based or custom field: filter by teams/list
            user_teams: list[str] = principal_attributes.get("teams", [])
            return {rls_field: user_teams}

    def _has_admin_role(
        self,
        user_roles: list[str],
        principal_attributes: dict[str, Any],
    ) -> bool:
        """Check if user has admin privileges.

        Args:
            user_roles: User's roles list
            principal_attributes: Full user attributes

        Returns:
            True if user has any admin role or is system user
        """
        # Check for system user flag
        if principal_attributes.get("is_system_user", False):
            return True

        # Check for admin roles
        return bool(set(user_roles) & set(self.admin_roles))


__all__ = ["RbacPermissionAdapter"]
