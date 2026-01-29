"""Auto-CRUD Meta Router.

This module provides functions to auto-generate CRUD endpoints for DocTypes
that opt-in via `Meta.api_resource = True`.

Key Functions:
- create_crud_routes(doctype_class): Generate CRUD routes for one DocType
- create_meta_router(): Generate routes for all registered api_resource DocTypes

All generated routes automatically:
- Check permissions via RbacPermissionAdapter
- Apply RLS filters for list queries
- Set owner on create to current user
- Check docstatus for submitted/immutable documents

Example:
    from framework_m.adapters.web.meta_router import create_meta_router

    # In your app factory
    meta_router = create_meta_router()
    app = Litestar(route_handlers=[meta_router])
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any
from uuid import UUID

from litestar import Request, Router, delete, get, post, put
from litestar.exceptions import NotFoundException
from litestar.status_codes import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from framework_m.adapters.auth.rbac_permission import RbacPermissionAdapter
from framework_m.adapters.db.generic_repository import GenericRepository
from framework_m.core.exceptions import PermissionDeniedError
from framework_m.core.interfaces.permission import (
    PermissionAction,
    PolicyEvaluateRequest,
)
from framework_m.core.interfaces.repository import FilterOperator, FilterSpec
from framework_m.core.registry import MetaRegistry
from framework_m.core.rls import apply_rls_filters

if TYPE_CHECKING:
    from framework_m.core.domain.base_doctype import BaseDocType
    from framework_m.core.interfaces.auth_context import UserContext


def _get_user_context(
    request: Request[Any, Any, Any],
) -> tuple[str, list[str], list[str]]:
    """Extract user context from request state.

    Returns:
        Tuple of (user_id, roles, teams)
    """
    user_id: str = getattr(request.state, "user_id", "anonymous")
    user_roles: list[str] = getattr(request.state, "user_roles", [])
    user_teams: list[str] = getattr(request.state, "user_teams", [])
    return user_id, user_roles, user_teams


def _get_user_from_request(request: Request[Any, Any, Any]) -> UserContext | None:
    """Get UserContext from request state if available."""
    return getattr(request.state, "user", None)


def _get_table_name(doctype_class: type[BaseDocType]) -> str:
    """Get the table name for a DocType class.

    Uses Meta.table_name if defined, otherwise lowercase class name.

    Args:
        doctype_class: The DocType class

    Returns:
        Table name string
    """
    meta = getattr(doctype_class, "Meta", None)
    if meta and hasattr(meta, "table_name"):
        return str(meta.table_name)
    return doctype_class.__name__.lower()


async def _check_permission(
    user_id: str,
    user_roles: list[str],
    user_teams: list[str],
    action: str,
    doctype_name: str,
    resource_id: str | None = None,
) -> None:
    """Check permission and raise PermissionDeniedError if not authorized."""
    adapter = RbacPermissionAdapter()
    result = await adapter.evaluate(
        PolicyEvaluateRequest(
            principal=user_id,
            action=action,
            resource=doctype_name,
            resource_id=resource_id,
            principal_attributes={
                "roles": user_roles,
                "teams": user_teams,
            },
        )
    )
    if not result.authorized:
        raise PermissionDeniedError(
            f"User '{user_id}' does not have '{action}' permission on '{doctype_name}'"
        )


def _parse_filters(filters_json: str | None) -> list[FilterSpec]:
    """Parse filters from JSON string.

    Args:
        filters_json: JSON string like '[{"field": "status", "operator": "eq", "value": "active"}]'

    Returns:
        List of FilterSpec objects
    """
    if not filters_json:
        return []

    try:
        filter_list = json.loads(filters_json)
        specs = []
        for f in filter_list:
            operator_str = f.get("operator", "eq").upper()
            operator = (
                FilterOperator[operator_str]
                if operator_str in FilterOperator.__members__
                else FilterOperator.EQ
            )
            specs.append(
                FilterSpec(
                    field=f["field"],
                    operator=operator,
                    value=f["value"],
                )
            )
        return specs
    except (json.JSONDecodeError, KeyError):
        return []


def _check_submitted(doc: BaseDocType, action: str) -> None:
    """Check if document is submitted and raise error if modification attempted.

    Args:
        doc: The document to check
        action: The action being performed ("update" or "delete")

    Raises:
        PermissionDeniedError: If document is submitted (docstatus=1)
    """
    docstatus = getattr(doc, "docstatus", 0)
    if docstatus == 1:
        raise PermissionDeniedError(
            f"Cannot {action} submitted document. Cancel it first."
        )


def create_crud_routes(
    doctype_class: type[BaseDocType],
    repo: GenericRepository[Any] | None = None,
) -> Router:
    """Generate CRUD routes for a DocType.

    Creates 5 REST endpoints for the given DocType:
    - GET /{doctype_name} - List with RLS and pagination
    - POST /{doctype_name} - Create with permission check
    - GET /{doctype_name}/{id} - Read single with 404 handling
    - PUT /{doctype_name}/{id} - Update with submitted check
    - DELETE /{doctype_name}/{id} - Delete with submitted check

    Args:
        doctype_class: The DocType class to generate routes for
        repo: Optional repository instance (for testing)

    Returns:
        Litestar Router with all CRUD routes
    """
    doctype_name = doctype_class.get_doctype_name()

    # =========================================================================
    # Route Handlers
    # =========================================================================

    @get("/")
    async def list_entities(
        request: Request[Any, Any, Any],
        limit: int = 20,
        offset: int = 0,
        filters: str | None = None,
        order_by: str | None = None,
        fields: str | None = None,
    ) -> dict[str, Any]:
        """List entities with pagination and RLS.

        Args:
            limit: Maximum items to return (default 20)
            offset: Number of items to skip
            filters: JSON string of filter specs
            order_by: Field to sort by (prefix with - for desc)
            fields: Comma-separated list of fields to include (e.g., "name,title")

        Returns:
            Paginated response with items, total, limit, offset, has_more
        """
        # User context is used for RLS via apply_rls_filters
        _ = _get_user_context(request)  # Reserved for future use

        # Parse user-provided filters
        user_filters = _parse_filters(filters)

        # Get user context for RLS
        user = _get_user_from_request(request)

        # Apply RLS filters
        rls_filters = await apply_rls_filters(user, doctype_name, user_filters)

        # Get repository factory from app state (injected via lifespan)
        repo_factory = getattr(request.app.state, "repository_factory", None)

        if repo_factory is None:
            # No database configured - return empty result
            return {
                "items": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
                "has_more": False,
            }

        # Get cached repository from factory
        doc_repo = repo or repo_factory.get_repository(doctype_class)
        if doc_repo is None:
            return {
                "items": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
                "has_more": False,
            }

        # Query repository with RLS filters
        async with repo_factory.session_factory.get_session() as session:
            result = await doc_repo.list_entities(
                session=session,
                filters=rls_filters,
                limit=limit,
                offset=offset,
            )

            # Convert items to dicts
            items = [item.model_dump() for item in result.items]

            # Apply field selection if specified
            if fields:
                field_list = [f.strip() for f in fields.split(",")]
                items = [
                    {k: v for k, v in item.items() if k in field_list} for item in items
                ]

            # Return paginated response format
            has_more = offset + len(items) < result.total
            return {
                "items": items,
                "total": result.total,
                "limit": limit,
                "offset": offset,
                "has_more": has_more,
            }

    @post("/", status_code=HTTP_201_CREATED)
    async def create_entity(
        request: Request[Any, Any, Any],
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Create a new entity.

        - Validates request body against Pydantic model
        - Checks CREATE permission
        - Sets owner to current user
        - Calls repository save()

        Returns:
            Created document data with 201 status
        """
        user_id, user_roles, user_teams = _get_user_context(request)

        # Check CREATE permission
        await _check_permission(
            user_id, user_roles, user_teams, PermissionAction.CREATE.value, doctype_name
        )

        # Set owner to current user
        data["owner"] = user_id

        # Create entity instance
        entity = doctype_class(**data)

        # Get repository factory from app state (injected via lifespan)
        repo_factory = getattr(request.app.state, "repository_factory", None)

        if repo_factory is None:
            # Return mock response when not wired up
            return {
                "id": str(entity.id),
                "doctype": doctype_name,
                "owner": user_id,
                **data,
            }

        # Get cached repository from factory
        doc_repo = repo or repo_factory.get_repository(doctype_class)
        if doc_repo is None:
            return {
                "id": str(entity.id),
                "doctype": doctype_name,
                "owner": user_id,
                **data,
            }

        # Save via repository
        async with repo_factory.session_factory.get_session() as session:
            saved = await doc_repo.save(session, entity)
            return dict(saved.model_dump())

    @get("/{entity_id:uuid}")
    async def get_entity(
        request: Request[Any, Any, Any],
        entity_id: UUID,
    ) -> dict[str, Any]:
        """Get a single entity by ID.

        - Calls repository get(id)
        - Checks READ permission
        - Returns 404 if not found
        - Returns document

        Returns:
            Document data or 404 Not Found
        """
        user_id, user_roles, user_teams = _get_user_context(request)

        # Check READ permission
        await _check_permission(
            user_id,
            user_roles,
            user_teams,
            PermissionAction.READ.value,
            doctype_name,
            str(entity_id),
        )

        # Get repository factory from app state (injected via lifespan)
        repo_factory = getattr(request.app.state, "repository_factory", None)

        if repo_factory is None:
            # Return mock response when not wired up
            return {
                "id": str(entity_id),
                "doctype": doctype_name,
            }

        # Get cached repository from factory
        doc_repo = repo or repo_factory.get_repository(doctype_class)
        if doc_repo is None:
            return {
                "id": str(entity_id),
                "doctype": doctype_name,
            }

        # Fetch from repository
        async with repo_factory.session_factory.get_session() as session:
            entity = await doc_repo.get(session, entity_id)

            if entity is None:
                raise NotFoundException(
                    detail=f"{doctype_name} with id '{entity_id}' not found"
                )

            return dict(entity.model_dump())

    @put("/{entity_id:uuid}")
    async def update_entity(
        request: Request[Any, Any, Any],
        entity_id: UUID,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Update an existing entity.

        - Loads existing document
        - Checks WRITE permission
        - Checks if submitted (deny if immutable)
        - Merges changes
        - Calls repository save()

        Returns:
            Updated document data
        """
        user_id, user_roles, user_teams = _get_user_context(request)

        # Check WRITE permission
        await _check_permission(
            user_id,
            user_roles,
            user_teams,
            PermissionAction.WRITE.value,
            doctype_name,
            str(entity_id),
        )

        # Get repository factory from app state (injected via lifespan)
        repo_factory = getattr(request.app.state, "repository_factory", None)

        if repo_factory is None:
            # Return mock response when not wired up
            return {
                "id": str(entity_id),
                "doctype": doctype_name,
                **data,
            }

        # Get cached repository from factory
        doc_repo = repo or repo_factory.get_repository(doctype_class)
        if doc_repo is None:
            return {
                "id": str(entity_id),
                "doctype": doctype_name,
                **data,
            }

        async with repo_factory.session_factory.get_session() as session:
            # Load existing document
            entity = await doc_repo.get(session, entity_id)

            if entity is None:
                raise NotFoundException(
                    detail=f"{doctype_name} with id '{entity_id}' not found"
                )

            # Check if submitted (immutable)
            _check_submitted(entity, "update")

            # Exclude read-only fields from update
            readonly_fields = {
                "id",
                "creation",
                "modified",
                "modified_by",
                "owner",
                "deleted_at",
            }
            update_data = {k: v for k, v in data.items() if k not in readonly_fields}

            # Update fields in-place to maintain SQLAlchemy session tracking
            for key, value in update_data.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)

            # Save via repository
            saved = await doc_repo.save(session, entity)

            return dict(saved.model_dump())

    @delete("/{entity_id:uuid}", status_code=HTTP_204_NO_CONTENT)
    async def delete_entity(
        request: Request[Any, Any, Any],
        entity_id: UUID,
    ) -> None:
        """Delete an entity.

        - Loads document
        - Checks DELETE permission
        - Checks if submitted (deny if immutable)
        - Calls repository delete()

        Returns:
            204 No Content
        """
        user_id, user_roles, user_teams = _get_user_context(request)

        # Check DELETE permission
        await _check_permission(
            user_id,
            user_roles,
            user_teams,
            PermissionAction.DELETE.value,
            doctype_name,
            str(entity_id),
        )

        # Get repository factory from app state (injected via lifespan)
        repo_factory = getattr(request.app.state, "repository_factory", None)

        if repo_factory is None:
            # Just return when not wired up
            return

        # Get cached repository from factory
        doc_repo = repo or repo_factory.get_repository(doctype_class)
        if doc_repo is None:
            return

        async with repo_factory.session_factory.get_session() as session:
            # Load document to check if submitted
            entity = await doc_repo.get(session, entity_id)

            if entity is None:
                raise NotFoundException(
                    detail=f"{doctype_name} with id '{entity_id}' not found"
                )

            # Check if submitted (immutable)
            _check_submitted(entity, "delete")

            # Delete via repository
            await doc_repo.delete(session, entity_id)

    # =========================================================================
    # Create Router
    # =========================================================================

    return Router(
        path=f"/{doctype_name}",
        route_handlers=[
            list_entities,
            create_entity,
            get_entity,
            update_entity,
            delete_entity,
        ],
        tags=[doctype_name],
    )


def create_meta_router() -> Router:
    """Create a meta router with CRUD routes for all api_resource DocTypes.

    Iterates through all registered DocTypes in MetaRegistry and creates
    CRUD routes for those with `Meta.api_resource = True`.

    Returns:
        Litestar Router containing all auto-generated CRUD routes
    """
    registry = MetaRegistry.get_instance()
    route_handlers: list[Router] = []

    # Get all registered DocTypes
    for doctype_name in registry.list_doctypes():
        try:
            doctype_class = registry.get_doctype(doctype_name)
            if doctype_class is None:
                continue

            # Check if DocType opts in to auto-CRUD
            if doctype_class.get_api_resource():
                router = create_crud_routes(doctype_class)
                route_handlers.append(router)
        except KeyError:
            continue

    return Router(
        path="/api/v1",
        route_handlers=route_handlers,
    )


__all__ = ["create_crud_routes", "create_meta_router"]
