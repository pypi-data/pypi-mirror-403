"""Permission Decorators for Indie Mode.

This module provides convenience decorators that simplify permission checks
for Controller methods. These follow the 0-Cliff Principle: Indie devs get
simplicity while enterprise devs can use the full PolicyEvaluateRequest API.

Example:
    class InvoiceController(BaseController[Invoice]):
        user: UserContext
        doctype_name: str = "Invoice"

        @requires_permission(PermissionAction.WRITE)
        async def update_invoice(self, data: dict) -> Invoice:
            # Permission already checked
            ...
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from functools import wraps
from typing import TYPE_CHECKING, Any, ParamSpec, TypeVar

from framework_m.adapters.auth.rbac_permission import RbacPermissionAdapter
from framework_m.core.exceptions import PermissionDeniedError
from framework_m.core.interfaces.permission import (
    PermissionAction,
    PolicyEvaluateRequest,
)

if TYPE_CHECKING:
    from framework_m.core.interfaces.auth_context import UserContext

P = ParamSpec("P")
R = TypeVar("R")


def requires_permission(
    action: PermissionAction | str,
) -> Callable[
    [Callable[P, Coroutine[Any, Any, R]]], Callable[P, Coroutine[Any, Any, R]]
]:
    """Decorator that checks permission before executing a Controller method.

    The decorated method must be on a class with:
    - `user: UserContext` attribute
    - `doctype_name: str` attribute

    Args:
        action: The permission action to check (READ, WRITE, CREATE, DELETE)

    Returns:
        Decorated function that checks permission before execution

    Raises:
        PermissionDeniedError: If user is not authorized for the action

    Example:
        class InvoiceController(BaseController[Invoice]):
            user: UserContext
            doctype_name: str = "Invoice"

            @requires_permission(PermissionAction.WRITE)
            async def update_amount(self, new_amount: float) -> float:
                return self.doc.amount = new_amount
    """

    def decorator(
        func: Callable[P, Coroutine[Any, Any, R]],
    ) -> Callable[P, Coroutine[Any, Any, R]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # First arg is self (the controller)
            if not args:
                raise ValueError("@requires_permission must be used on a method")

            self = args[0]

            # Get user and doctype from controller
            user: UserContext | None = getattr(self, "user", None)
            doctype_name: str | None = getattr(self, "doctype_name", None)

            if user is None:
                raise PermissionDeniedError(
                    "No user context available for permission check"
                )

            if doctype_name is None:
                raise PermissionDeniedError(
                    "No doctype_name available for permission check"
                )

            # Build PolicyEvaluateRequest
            action_str = (
                action.value if isinstance(action, PermissionAction) else action
            )
            request = PolicyEvaluateRequest(
                principal=user.id,
                action=action_str,
                resource=doctype_name,
                principal_attributes={
                    "roles": user.roles,
                    "tenants": user.tenants,
                    "teams": user.teams,
                    "is_system_user": user.is_system_user,
                },
            )

            # Evaluate permission
            adapter = RbacPermissionAdapter()
            result = await adapter.evaluate(request)

            if not result.authorized:
                raise PermissionDeniedError(
                    f"User '{user.id}' does not have '{action_str}' permission on '{doctype_name}'"
                )

            # Permission granted, execute the method
            return await func(*args, **kwargs)

        return wrapper

    return decorator


# =============================================================================
# Whitelist Decorator for RPC
# =============================================================================

# Attribute name for whitelist metadata
WHITELIST_ATTR = "_whitelist"

# Type variable for callable
F = TypeVar("F", bound=Callable[..., Any])


def whitelist(
    allow_guest: bool = False,
    methods: list[str] | None = None,
) -> Callable[[F], F]:
    """Mark controller method as publicly callable via RPC.

    Whitelisted methods can be called via the RPC endpoint:
    POST /api/v1/rpc/{doctype}/{method}

    Args:
        allow_guest: If True, method can be called without authentication.
                    Default is False (requires authenticated user).
        methods: HTTP methods allowed for this RPC call.
                Default is ["POST"].

    Returns:
        Decorator that adds whitelist metadata to the method.

    Example:
        class TodoController(BaseController[Todo]):
            @whitelist()
            async def mark_complete(self) -> bool:
                self.doc.completed = True
                return True

            @whitelist(allow_guest=True)
            async def get_public_stats(self) -> dict:
                # Public endpoint, no auth required
                return {"total": 100}
    """

    def decorator(func: F) -> F:
        setattr(
            func,
            WHITELIST_ATTR,
            {
                "allow_guest": allow_guest,
                "methods": methods or ["POST"],
            },
        )
        return func

    return decorator


def is_whitelisted(method: Callable[..., Any]) -> bool:
    """Check if a method has the @whitelist decorator.

    Args:
        method: The method to check

    Returns:
        True if the method is whitelisted, False otherwise
    """
    return hasattr(method, WHITELIST_ATTR)


def get_whitelist_options(method: Callable[..., Any]) -> dict[str, Any]:
    """Get whitelist options from a decorated method.

    Args:
        method: The method to get options from

    Returns:
        Dict with whitelist options, or empty dict if not whitelisted
    """
    return getattr(method, WHITELIST_ATTR, {})


# =============================================================================
# RPC Decorator for Standalone Functions
# =============================================================================

# Attribute name for RPC metadata
RPC_ATTR = "_rpc"


def rpc(
    permission: str | None = None,
    allow_guest: bool = False,
) -> Callable[[F], F]:
    """Mark standalone function as RPC-callable via dotted path.

    Functions decorated with @rpc can be called via:
    POST /api/v1/rpc/{module.path.function_name}

    Args:
        permission: Custom permission to check before calling.
                   If None, no permission check is performed.
        allow_guest: If True, function can be called without authentication.
                    Default is False (requires authenticated user).

    Returns:
        Decorator that adds RPC metadata and registers the function.

    Example:
        @rpc()
        async def get_server_time() -> str:
            return datetime.now().isoformat()

        @rpc(permission="send_email")
        async def send_email(to: str, subject: str) -> bool:
            # Requires "send_email" permission
            return True

        @rpc(allow_guest=True)
        async def public_health_check() -> dict:
            # No auth required
            return {"status": "ok"}
    """
    from framework_m.core.rpc_registry import RpcRegistry

    def decorator(func: F) -> F:
        # Build the dotted path from module and function name
        path = f"{func.__module__}.{func.__qualname__}"

        # Store metadata on function
        setattr(
            func,
            RPC_ATTR,
            {
                "permission": permission,
                "allow_guest": allow_guest,
                "path": path,
            },
        )

        # Auto-register in RpcRegistry
        RpcRegistry.get_instance().register(path, func)

        return func

    return decorator


def is_rpc_function(func: Callable[..., Any]) -> bool:
    """Check if a function has the @rpc decorator.

    Args:
        func: The function to check

    Returns:
        True if the function is RPC-callable, False otherwise
    """
    return hasattr(func, RPC_ATTR)


def get_rpc_options(func: Callable[..., Any]) -> dict[str, Any]:
    """Get RPC options from a decorated function.

    Args:
        func: The function to get options from

    Returns:
        Dict with RPC options, or empty dict if not decorated
    """
    return getattr(func, RPC_ATTR, {})


__all__ = [
    "RPC_ATTR",
    "WHITELIST_ATTR",
    "get_rpc_options",
    "get_whitelist_options",
    "is_rpc_function",
    "is_whitelisted",
    "requires_permission",
    "rpc",
    "whitelist",
]
