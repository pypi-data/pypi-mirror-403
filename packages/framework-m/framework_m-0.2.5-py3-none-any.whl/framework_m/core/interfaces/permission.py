"""Permission Protocol - Core interface for authorization.

This module defines the PermissionProtocol for checking user permissions
on DocTypes and documents.

Key Design Principles:
- **Stateless**: Pass all attributes in the request, no sync on user ID
- **Adapter Pattern**: RBAC, ABAC (OPA), ReBAC (SpiceDB), or Combo
- **RLS Support**: get_permitted_filters for Row-Level Security
"""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol


class PermissionAction(StrEnum):
    """Standard permission actions for DocTypes."""

    READ = "read"
    WRITE = "write"
    CREATE = "create"
    DELETE = "delete"
    SUBMIT = "submit"
    CANCEL = "cancel"
    AMEND = "amend"


class DecisionSource(StrEnum):
    """Source of the authorization decision."""

    RBAC = "rbac"
    ABAC = "abac"
    REBAC = "rebac"
    COMBO = "combo"
    CUSTOM = "custom"  # CustomPermission database rules


@dataclass
class PolicyEvaluateRequest:
    """Stateless request for policy evaluation.

    Contains all context needed to make an authorization decision.
    No external lookups should be needed by the adapter.
    """

    principal: str  # User ID or identifier
    action: PermissionAction | str  # Action being performed
    resource: str  # DocType name (e.g., "Invoice")
    resource_id: str | None = None  # Specific doc ID for object-level checks
    tenant_id: str | None = None  # Multi-tenant support
    principal_attributes: dict[str, Any] = field(
        default_factory=dict
    )  # roles, groups, etc.
    resource_attributes: dict[str, Any] = field(
        default_factory=dict
    )  # doc owner, status, etc.
    context: dict[str, Any] = field(default_factory=dict)  # IP, time, device, etc.


@dataclass
class PolicyEvaluateResult:
    """Result of policy evaluation."""

    authorized: bool
    decision_source: DecisionSource | None = None
    reason: str | None = None  # Explanation for debugging


class PermissionProtocol(Protocol):
    """Protocol defining the contract for permission checking.

    This is the primary port for authorization in the hexagonal architecture.

    Implementations:
    - RbacPermissionAdapter: Code-first RBAC from DocType.Meta.permissions
    - OpaPermissionAdapter: ABAC via Open Policy Agent
    - SpiceDbPermissionAdapter: ReBAC using SpiceDB
    - ComboPermissionAdapter: ReBAC first, fallback to ABAC

    Example usage:
        perm: PermissionProtocol = container.get(PermissionProtocol)

        result = await perm.evaluate(PolicyEvaluateRequest(
            principal="user-001",
            action=PermissionAction.WRITE,
            resource="Invoice",
            resource_id="inv-123",
            principal_attributes={"roles": ["Manager"], "department": "Sales"},
        ))

        if result.authorized:
            # Allow access
            pass
    """

    async def evaluate(
        self,
        request: PolicyEvaluateRequest,
    ) -> PolicyEvaluateResult:
        """Evaluate a policy request.

        Args:
            request: Stateless request containing all context

        Returns:
            PolicyEvaluateResult with authorized flag and decision source
        """
        ...

    async def get_permitted_filters(
        self,
        principal: str,
        principal_attributes: dict[str, Any],
        resource: str,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        """Get filters for Row-Level Security.

        Returns SQL filters to apply to list queries for this principal.
        For ReBAC, may query the graph engine for allowed IDs.

        Args:
            principal: User ID
            principal_attributes: User attributes (roles, groups, etc.)
            resource: DocType name
            tenant_id: Optional tenant context

        Returns:
            Filter dict to apply (e.g., {"owner": principal} or {"id": ["doc1", "doc2"]})
        """
        ...


__all__ = [
    "DecisionSource",
    "PermissionAction",
    "PermissionProtocol",
    "PolicyEvaluateRequest",
    "PolicyEvaluateResult",
]
