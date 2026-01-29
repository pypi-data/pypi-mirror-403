"""Permission Helpers - High-level permission checking utilities.

This module provides convenient helper functions for checking permissions
without directly interacting with the PermissionProtocol adapter.

Example:
    from framework_m.core.permissions import has_permission

    if await has_permission(user, "Invoice", PermissionAction.WRITE):
        # Proceed with write operation
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from framework_m.adapters.auth.rbac_permission import RbacPermissionAdapter
from framework_m.core.domain.base_doctype import BaseDocType
from framework_m.core.interfaces.permission import (
    PermissionAction,
    PolicyEvaluateRequest,
)
from framework_m.core.registry import MetaRegistry

if TYPE_CHECKING:
    from framework_m.core.interfaces.auth_context import UserContext


async def has_permission(
    user: UserContext | None,
    doctype: str,
    action: PermissionAction | str,
    resource_id: str | None = None,
    adapter: RbacPermissionAdapter | None = None,
) -> bool:
    """Check if a user has permission to perform an action on a DocType.

    This is a convenience wrapper around PermissionProtocol.evaluate()
    that handles common cases like:
    - Public DocTypes (requires_auth=False)
    - Missing user authentication
    - Converting UserContext to principal attributes

    Args:
        user: The current user context, or None if not authenticated
        doctype: Name of the DocType to check (e.g., "Invoice")
        action: The action to check (read, write, create, delete, etc.)
        resource_id: Optional specific document ID for object-level checks
        adapter: Optional permission adapter (uses RbacPermissionAdapter by default)

    Returns:
        True if the user is authorized, False otherwise

    Example:
        user = UserContext(id="user-1", email="a@b.com", roles=["Manager"])

        # Check if user can write to Invoice
        if await has_permission(user, "Invoice", PermissionAction.WRITE):
            # Proceed with write
            pass

        # Public DocType check (no user required)
        if await has_permission(None, "PublicConfig", "read"):
            # Access public data
            pass
    """
    # Get the DocType class from registry
    registry = MetaRegistry.get_instance()
    try:
        doctype_class = registry.get_doctype(doctype)
    except Exception:
        return False

    if doctype_class is None:
        return False

    # Check if DocType requires authentication
    requires_auth = doctype_class.get_requires_auth()

    # If no auth required for this DocType and no user, allow access
    if not requires_auth and user is None:
        return True

    # If auth is required but no user, deny access
    if requires_auth and user is None:
        return False

    # Build principal attributes from user context
    principal_attributes: dict[str, object] = {}
    if user is not None:
        principal_attributes = {
            "roles": user.roles,
            "tenants": user.tenants,
            "is_system_user": user.is_system_user,
        }

    # Create permission adapter if not provided
    if adapter is None:
        adapter = RbacPermissionAdapter()

    # Build and evaluate the request
    request = PolicyEvaluateRequest(
        principal=user.id if user else "anonymous",
        action=action,
        resource=doctype,
        resource_id=resource_id,
        principal_attributes=principal_attributes,
    )

    result = await adapter.evaluate(request)
    return result.authorized


async def has_permission_for_doc(
    user: UserContext | None,
    doc: BaseDocType,
    action: PermissionAction | str,
    adapter: RbacPermissionAdapter | None = None,
) -> bool:
    """Check if a user has permission for a specific document (object-level).

    This function performs a full permission check including:
    - Role-based permission check (can user's role perform action on DocType?)
    - Ownership check (if RLS is enabled, is user the owner or admin?)

    Args:
        user: The current user context, or None if not authenticated
        doc: The actual document instance to check
        action: The action to check (read, write, create, delete, etc.)
        adapter: Optional permission adapter

    Returns:
        True if the user is authorized, False otherwise

    Example:
        invoice = await repo.get(session, invoice_id)
        if await has_permission_for_doc(user, invoice, PermissionAction.WRITE):
            # Proceed with write
            pass
    """
    doctype = doc.get_doctype_name()

    # First check role-based permission
    if not await has_permission(user, doctype, action, str(doc.id), adapter):
        return False

    # If no user, already handled by has_permission (public DocType case)
    if user is None:
        return True

    # Get DocType class for RLS check
    registry = MetaRegistry.get_instance()
    try:
        doctype_class = registry.get_doctype(doctype)
    except Exception:
        return False

    if doctype_class is None:
        return False

    # Check if RLS applies
    apply_rls = doctype_class.get_apply_rls()
    if not apply_rls:
        # No RLS - role check passed, so allow
        return True

    # Check admin bypass
    if adapter is None:
        adapter = RbacPermissionAdapter()

    if user.has_role("Admin") or user.has_role("System") or user.is_system_user:
        return True

    # RLS enabled - check ownership
    doc_owner = doc.owner
    if doc_owner is None:
        # No owner set - allow access (could be a new doc)
        return True

    return doc_owner == user.id


async def require_permission_for_doc(
    user: UserContext | None,
    doc: BaseDocType,
    action: PermissionAction | str,
    adapter: RbacPermissionAdapter | None = None,
) -> None:
    """Require permission for a document, raising an exception if denied.

    Same as has_permission_for_doc but raises PermissionDeniedError
    instead of returning False.

    Args:
        user: The current user context, or None if not authenticated
        doc: The actual document instance to check
        action: The action to check
        adapter: Optional permission adapter

    Raises:
        PermissionDeniedError: If user lacks permission

    Example:
        invoice = await repo.get(session, invoice_id)
        await require_permission_for_doc(user, invoice, PermissionAction.WRITE)
        # If we get here, permission is granted
        invoice.amount = new_amount
        await repo.save(session, invoice)
    """
    from framework_m.core.exceptions import PermissionDeniedError

    if not await has_permission_for_doc(user, doc, action, adapter):
        action_str = action.value if isinstance(action, PermissionAction) else action
        raise PermissionDeniedError(
            f"User '{user.id if user else 'anonymous'}' does not have "
            f"'{action_str}' permission for {doc.get_doctype_name()} '{doc.id}'"
        )


__all__ = [
    "has_permission",
    "has_permission_for_doc",
    "require_permission_for_doc",
]
