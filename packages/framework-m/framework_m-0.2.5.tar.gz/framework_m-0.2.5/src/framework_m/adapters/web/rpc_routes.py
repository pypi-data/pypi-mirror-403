"""RPC Routes - Whitelisted Controller Method Calls.

This module provides the RPC endpoint for calling whitelisted controller
methods via HTTP POST.

Endpoint:
    POST /api/v1/rpc/{doctype}/{method}

Only methods decorated with @whitelist can be called.

Example:
    # Controller
    class TodoController(BaseController[Todo]):
        @whitelist()
        async def mark_complete(self) -> bool:
            self.doc.completed = True
            return True

    # HTTP Call
    POST /api/v1/rpc/Todo/mark_complete
    {"doc_id": "uuid-123"}
"""

from __future__ import annotations

from typing import Any

from litestar import Request, Router, post
from litestar.exceptions import NotFoundException

from framework_m.core.decorators import get_whitelist_options, is_whitelisted
from framework_m.core.exceptions import PermissionDeniedError
from framework_m.core.registry import MetaRegistry


@post("/{doctype:str}/{method:str}")
async def call_rpc_method(
    request: Request[Any, Any, Any],
    doctype: str,
    method: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    """Call a whitelisted controller method.

    Args:
        doctype: The DocType name (e.g., "Todo")
        method: The method name (e.g., "mark_complete")
        data: Request body with method arguments and optional doc_id

    Returns:
        The method result wrapped in a response dict

    Raises:
        NotFoundException: If doctype or method doesn't exist
        PermissionDeniedError: If method is not whitelisted
    """
    registry = MetaRegistry.get_instance()

    # 1. Get DocType class
    try:
        doctype_class = registry.get_doctype(doctype)
    except KeyError:
        raise NotFoundException(detail=f"DocType '{doctype}' not found") from None

    if doctype_class is None:
        raise NotFoundException(detail=f"DocType '{doctype}' not found")

    # 2. Get Controller class
    try:
        controller_class = registry.get_controller(doctype)
    except KeyError:
        raise NotFoundException(
            detail=f"No controller registered for DocType '{doctype}'"
        ) from None

    if controller_class is None:
        raise NotFoundException(
            detail=f"No controller registered for DocType '{doctype}'"
        )

    # 3. Check if method exists
    if not hasattr(controller_class, method):
        raise NotFoundException(
            detail=f"Method '{method}' not found on {doctype}Controller"
        )

    controller_method = getattr(controller_class, method)

    # 4. Check if method is whitelisted
    if not is_whitelisted(controller_method):
        raise PermissionDeniedError(
            f"Method '{method}' is not whitelisted for RPC calls"
        )

    # 5. Get whitelist options
    options = get_whitelist_options(controller_method)
    allow_guest = options.get("allow_guest", False)

    # 6. Check auth if required
    if not allow_guest:
        user_id = getattr(request.state, "user_id", None)
        if user_id is None:
            raise PermissionDeniedError("Authentication required")

    # 7. Create document instance (or load from DB if doc_id provided)
    doc_id = data.pop("doc_id", None)
    # TODO: Load document from repository when DB wiring is complete
    # For now, create empty doc if doc_id provided, else use data
    doc = doctype_class() if doc_id else doctype_class(**data)

    # 8. Instantiate controller
    controller = controller_class(doc)

    # 9. Call method
    result = await controller_method(controller)

    # 10. Return result
    return {
        "success": True,
        "doctype": doctype,
        "method": method,
        "result": result,
    }


# =============================================================================
# Dotted Path RPC Endpoint (Standalone Functions)
# =============================================================================


@post("/fn/{path:path}")
async def call_rpc_function(
    request: Request[Any, Any, Any],
    path: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    """Call an @rpc decorated function by dotted path.

    Args:
        path: The dotted path (e.g., "my_app.api.send_email")
        data: Request body with function arguments

    Returns:
        The function result wrapped in a response dict

    Raises:
        NotFoundException: If function is not registered
        PermissionDeniedError: If permission check fails
    """
    from framework_m.core.decorators import get_rpc_options, is_rpc_function
    from framework_m.core.rpc_registry import RpcRegistry

    registry = RpcRegistry.get_instance()

    # Normalize path - strip leading slash from path param
    normalized_path = path.lstrip("/")

    # 1. Look up function in registry
    func = registry.get(normalized_path)
    if func is None:
        raise NotFoundException(detail=f"RPC function '{normalized_path}' not found")

    # 2. Verify it's decorated with @rpc
    if not is_rpc_function(func):
        raise PermissionDeniedError(f"Function '{path}' is not decorated with @rpc")

    # 3. Get RPC options
    options = get_rpc_options(func)
    allow_guest = options.get("allow_guest", False)
    permission = options.get("permission")

    # 4. Check auth if required
    if not allow_guest:
        user_context = getattr(request.state, "user", None)
        if user_context is None:
            raise PermissionDeniedError("Authentication required")

        # 5. Check custom permission if specified
        if permission is not None:
            from framework_m.adapters.auth.rbac_permission import RbacPermissionAdapter
            from framework_m.core.interfaces.permission import PolicyEvaluateRequest

            # Build permission request for custom permission action
            perm_request = PolicyEvaluateRequest(
                principal=user_context.id,
                action=permission,  # Use custom permission as action
                resource="rpc",  # RPC resource type
                resource_id=normalized_path,  # Function path as resource ID
                principal_attributes={
                    "roles": getattr(user_context, "roles", []),
                    "tenants": getattr(user_context, "tenants", []),
                    "teams": getattr(user_context, "teams", []),
                    "is_system_user": getattr(user_context, "is_system_user", False),
                },
            )

            adapter = RbacPermissionAdapter()
            result = await adapter.evaluate(perm_request)

            if not result.authorized:
                raise PermissionDeniedError(
                    f"Permission '{permission}' required for RPC function '{normalized_path}'"
                )

    # 6. Call function with data as kwargs
    result = await func(**data)

    # 7. Return result
    return {
        "success": True,
        "path": normalized_path,
        "result": result,
    }


rpc_router = Router(
    path="/api/v1/rpc",
    route_handlers=[call_rpc_function, call_rpc_method],
    tags=["RPC"],
)


__all__ = ["call_rpc_function", "call_rpc_method", "rpc_router"]
