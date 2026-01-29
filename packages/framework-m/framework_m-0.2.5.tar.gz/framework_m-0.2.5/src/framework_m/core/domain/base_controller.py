"""Base Controller - Lifecycle hooks for document operations.

This module defines the BaseController class that provides
lifecycle hooks for document operations like insert, save, delete.

Controllers are separate from DocTypes to maintain clean separation
between data models and business logic.
"""

from typing import Any

from framework_m.core.domain.base_doctype import BaseDocType


class BaseController[T: BaseDocType]:
    """
    Base controller providing lifecycle hooks for DocType operations.

    Controllers handle business logic and side effects during document
    lifecycle events. Override hook methods in subclasses.

    All hooks receive an optional context parameter for passing request
    context (user info, request ID, etc.) without global state.

    Example:
        class TodoController(BaseController[Todo]):
            async def validate(self, context: Any = None) -> None:
                if not self.doc.title.strip():
                    raise ValueError("Title cannot be empty")

            async def after_insert(self, context: Any = None) -> None:
                # Access user from context instead of global state
                user_id = context.get("user_id") if context else None
                await notify_user(user_id, "New todo created")
    """

    def __init__(self, doc: T) -> None:
        """
        Initialize controller with a document.

        Args:
            doc: The document instance this controller manages
        """
        self.doc = doc

    async def validate(self, context: Any = None) -> None:
        """
        Validate document before any save operation.

        Called before insert and update. Raise exceptions for validation errors.

        Args:
            context: Optional context (user info, request metadata, etc.)
        """

    async def before_insert(self, context: Any = None) -> None:
        """
        Hook called before inserting a new document.

        Use for setting defaults, generating values, etc.

        Args:
            context: Optional context (user info, request metadata, etc.)
        """

    async def after_insert(self, context: Any = None) -> None:
        """
        Hook called after successfully inserting a new document.

        Use for side effects like notifications, logging, etc.

        Args:
            context: Optional context (user info, request metadata, etc.)
        """

    async def before_save(self, context: Any = None) -> None:
        """
        Hook called before saving (insert or update).

        Called after validate, before database write.

        Args:
            context: Optional context (user info, request metadata, etc.)
        """

    async def after_save(self, context: Any = None) -> None:
        """
        Hook called after successfully saving a document.

        Use for cache invalidation, event publishing, etc.

        Args:
            context: Optional context (user info, request metadata, etc.)
        """

    async def before_delete(self, context: Any = None) -> None:
        """
        Hook called before deleting a document.

        Use for validation, preventing deletion of linked docs, etc.

        Args:
            context: Optional context (user info, request metadata, etc.)
        """

    async def after_delete(self, context: Any = None) -> None:
        """
        Hook called after successfully deleting a document.

        Use for cleanup, cascade operations, etc.

        Args:
            context: Optional context (user info, request metadata, etc.)
        """

    async def on_submit(self, context: Any = None) -> None:
        """
        Hook called when a submittable document is submitted.

        Only applies to DocTypes with SubmittableMixin.

        Args:
            context: Optional context (user info, request metadata, etc.)
        """

    async def on_cancel(self, context: Any = None) -> None:
        """
        Hook called when a submittable document is cancelled.

        Only applies to DocTypes with SubmittableMixin.

        Args:
            context: Optional context (user info, request metadata, etc.)
        """

    # =========================================================================
    # Permission Convenience Methods (Indie Mode)
    # =========================================================================

    async def check_permission(
        self,
        action: str,
        doc_id: str | None = None,
    ) -> bool:
        """Check if current user has permission for an action.

        Simple helper that builds PolicyEvaluateRequest internally.
        Returns bool instead of raising - use require_permission() to raise.

        Requires the controller to have:
        - `user: UserContext` attribute
        - `doctype_name: str` attribute
        - `permission: PermissionProtocol` attribute (injected via DI)

        Args:
            action: Action to check (read, write, create, delete)
            doc_id: Optional document ID for resource-level checks

        Returns:
            True if authorized, False otherwise

        Example:
            if await self.check_permission("write"):
                # User can write
                ...
        """
        from framework_m.core.interfaces.permission import PolicyEvaluateRequest

        user = getattr(self, "user", None)
        doctype_name = getattr(self, "doctype_name", None)
        permission = getattr(self, "permission", None)

        if user is None or doctype_name is None or permission is None:
            return False

        request = PolicyEvaluateRequest(
            principal=user.id,
            action=action,
            resource=doctype_name,
            resource_id=doc_id,
            principal_attributes={
                "roles": user.roles,
                "tenants": user.tenants,
                "teams": user.teams,
                "is_system_user": user.is_system_user,
            },
        )

        result = await permission.evaluate(request)
        return bool(result.authorized)

    async def require_permission(
        self,
        action: str,
        doc_id: str | None = None,
    ) -> None:
        """Require that user has permission for an action, raising if not.

        Similar to check_permission() but raises PermissionDeniedError
        instead of returning False.

        Args:
            action: Action to check (read, write, create, delete)
            doc_id: Optional document ID for resource-level checks

        Raises:
            PermissionDeniedError: If user is not authorized

        Example:
            await self.require_permission("write")
            # If we get here, user is authorized
        """
        from framework_m.core.exceptions import PermissionDeniedError

        authorized = await self.check_permission(action, doc_id)
        if not authorized:
            user_id = getattr(getattr(self, "user", None), "id", "unknown")
            doctype_name = getattr(self, "doctype_name", "unknown")
            raise PermissionDeniedError(
                f"User '{user_id}' does not have '{action}' permission on '{doctype_name}'"
            )


__all__ = ["BaseController"]
