"""Row-Level Security (RLS) Helpers.

This module provides helper functions for applying Row-Level Security filters
to repository queries based on user context and DocType configuration.

Key Functions:
- get_rls_filters(): Get RLS filter dict for a user/DocType
- apply_rls_filters(): Merge RLS filters with existing filters

Example:
    from framework_m.core.rls import apply_rls_filters

    async def list_invoices(user, existing_filters):
        filters = await apply_rls_filters(user, "Invoice", existing_filters)
        return await repo.list_entities(session, filters=filters)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from framework_m.adapters.auth.rbac_permission import RbacPermissionAdapter
from framework_m.core.interfaces.repository import FilterOperator, FilterSpec

if TYPE_CHECKING:
    from framework_m.core.doctypes.document_share import DocumentShare
    from framework_m.core.interfaces.auth_context import UserContext


async def get_rls_filters(
    user: UserContext | None,
    doctype: str,
    adapter: RbacPermissionAdapter | None = None,
) -> dict[str, str | list[str]]:
    """Get RLS filter dict for a user and DocType.

    Determines what RLS filters should be applied based on:
    - DocType.Meta.apply_rls flag
    - DocType.Meta.rls_field (owner or team/custom)
    - User's roles (admins bypass RLS)
    - System user flag

    Args:
        user: Current user context, or None for public access
        doctype: Name of the DocType
        adapter: Optional permission adapter (creates default if not provided)

    Returns:
        Dict of filters to apply:
        - {"owner": "user-123"} for owner-based RLS
        - {"team": ["sales", "marketing"]} for team-based RLS
        - {} if no RLS should be applied

    Example:
        filters = await get_rls_filters(user, "Invoice")
        # {"owner": "user-123"} for regular users
        # {} for admins
    """
    # No user, no RLS (for public DocTypes)
    if user is None:
        return {}

    if adapter is None:
        adapter = RbacPermissionAdapter()

    principal_attributes = {
        "roles": user.roles,
        "tenants": user.tenants,
        "teams": user.teams,
        "is_system_user": user.is_system_user,
    }

    return await adapter.get_permitted_filters(
        principal=user.id,
        principal_attributes=principal_attributes,
        resource=doctype,
    )


async def apply_rls_filters(
    user: UserContext | None,
    doctype: str,
    existing_filters: list[FilterSpec] | None = None,
    adapter: RbacPermissionAdapter | None = None,
) -> list[FilterSpec]:
    """Apply RLS filters to an existing filter list.

    Merges RLS filters with user-provided filters for use in repository queries.

    Args:
        user: Current user context, or None for public access
        doctype: Name of the DocType
        existing_filters: User-provided filters (optional)
        adapter: Optional permission adapter

    Returns:
        Combined list of FilterSpec including RLS filters

    Example:
        filters = [FilterSpec(field="status", operator=EQ, value="active")]
        merged = await apply_rls_filters(user, "Invoice", filters)
        # Returns filters + owner filter for regular users
    """
    result = list(existing_filters) if existing_filters else []

    # Get RLS filters
    rls_dict = await get_rls_filters(user, doctype, adapter)

    # Convert dict to FilterSpecs and append
    for field, value in rls_dict.items():
        result.append(
            FilterSpec(
                field=field,
                operator=FilterOperator.EQ,
                value=value,
            )
        )

    return result


async def get_rls_filters_with_shares(
    user: UserContext | None,
    doctype: str,
    shares: list[DocumentShare],
    action: str = "read",
    adapter: RbacPermissionAdapter | None = None,
) -> dict[str, str | list[str]]:
    """Get RLS filters including document shares.

    Combines standard RLS filtering (owner/team) with explicit document
    shares, returning filters that include shared document IDs.

    Args:
        user: Current user context, or None for public access
        doctype: Name of the DocType
        shares: List of DocumentShare objects to check
        action: Action to check permission for (default: "read")
        adapter: Optional permission adapter

    Returns:
        Dict of filters including:
        - Standard RLS filters (owner or team)
        - "_shared_doc_ids" key with list of explicitly shared doc IDs

    Example:
        shares = await share_repo.list_for_doctype("Invoice")
        filters = await get_rls_filters_with_shares(user, "Invoice", shares)
        # {"owner": "user-123", "_shared_doc_ids": ["INV-001", "INV-002"]}
    """
    from framework_m.core.doctypes.document_share import ShareType

    # No user means no RLS
    if user is None:
        return {}

    # Get standard RLS filters first
    base_filters = await get_rls_filters(user, doctype, adapter)

    # If admin (empty filters), no need to check shares
    if not base_filters:
        return {}

    # Find shares that grant access to this user
    shared_doc_ids: list[str] = []

    for share in shares:
        # Skip shares for other doctypes
        if share.doctype_name != doctype:
            continue

        # Check if share grants the requested action
        if not share.has_permission(action):
            continue

        # Check if share matches this user
        is_user_share = (
            share.share_type == ShareType.USER and share.shared_with == user.id
        )
        is_role_share = (
            share.share_type == ShareType.ROLE and share.shared_with in user.roles
        )

        if is_user_share or is_role_share:
            shared_doc_ids.append(share.doc_id)

    # Add shared doc IDs to filters if any
    if shared_doc_ids:
        base_filters["_shared_doc_ids"] = shared_doc_ids

    return base_filters


__all__ = [
    "apply_rls_filters",
    "get_rls_filters",
    "get_rls_filters_with_shares",
]
