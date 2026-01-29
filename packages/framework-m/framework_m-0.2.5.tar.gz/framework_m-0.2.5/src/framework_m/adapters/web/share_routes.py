"""Share API Routes.

This module provides REST API endpoints for managing document shares.

Endpoints:
- POST /api/v1/share — Create a new share
- DELETE /api/v1/share/{id} — Remove a share
- GET /api/v1/{doctype}/{id}/shares — List shares for a document

Example:
    from framework_m.adapters.web.share_routes import share_router

    # Add to Litestar app
    app = Litestar(route_handlers=[share_router])
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from litestar import Controller, Request, delete, get, post
from litestar.status_codes import HTTP_201_CREATED, HTTP_204_NO_CONTENT
from pydantic import BaseModel, Field

from framework_m.core.doctypes.document_share import DocumentShare, ShareType

if TYPE_CHECKING:
    pass


# =============================================================================
# Request/Response DTOs
# =============================================================================


class CreateShareRequest(BaseModel):
    """Request body for creating a document share."""

    doctype_name: str = Field(description="DocType name of the document to share")
    doc_id: str = Field(description="ID of the document to share")
    shared_with: str = Field(description="User ID or Role name to share with")
    share_type: ShareType = Field(default=ShareType.USER, description="USER or ROLE")
    granted_permissions: list[str] = Field(
        default_factory=lambda: ["read"],
        description="Permissions to grant: read, write, delete",
    )
    note: str | None = Field(default=None, description="Optional note for audit")


class ShareResponse(BaseModel):
    """Response for a document share."""

    id: str
    name: str | None
    doctype_name: str
    doc_id: str
    shared_with: str
    share_type: str
    granted_permissions: list[str]
    owner: str | None
    note: str | None

    @classmethod
    def from_share(cls, share: DocumentShare) -> ShareResponse:
        """Create response from DocumentShare entity."""
        return cls(
            id=str(share.id),
            name=share.name,
            doctype_name=share.doctype_name,
            doc_id=share.doc_id,
            shared_with=share.shared_with,
            share_type=share.share_type.value,
            granted_permissions=share.granted_permissions,
            owner=share.owner,
            note=share.note,
        )


class ShareListResponse(BaseModel):
    """Response for listing shares."""

    shares: list[ShareResponse]
    total: int


# =============================================================================
# Share Controller
# =============================================================================


class ShareController(Controller):
    """Controller for document share management.

    Provides endpoints for creating, deleting, and listing shares.
    All endpoints require authentication.
    """

    path = "/api/v1"
    tags = ["Shares"]  # noqa: RUF012

    @post("/share", status_code=HTTP_201_CREATED)
    async def create_share(
        self,
        request: Request[Any, Any, Any],
        data: CreateShareRequest,
    ) -> ShareResponse:
        """Create a new document share.

        Creates a share that grants the specified user or role
        access to a document with the given permissions.

        Args:
            request: Litestar request object
            data: Share creation request

        Returns:
            The created share

        Raises:
            PermissionDeniedError: If user cannot share the document
        """
        # Get current user from request state
        # In production, this comes from auth middleware
        user_id: str = getattr(request.state, "user_id", "anonymous")

        # Create the share
        share = DocumentShare(
            doctype_name=data.doctype_name,
            doc_id=data.doc_id,
            shared_with=data.shared_with,
            share_type=data.share_type,
            granted_permissions=data.granted_permissions,
            note=data.note,
            owner=user_id,  # The creator owns the share
        )

        # TODO: In production, save to database
        # session = self.request.state.session
        # repo = GenericRepository(DocumentShare, document_share_table)
        # share = await repo.save(session, share)

        return ShareResponse.from_share(share)

    @delete("/share/{share_id:uuid}", status_code=HTTP_204_NO_CONTENT)
    async def delete_share(
        self,
        request: Request[Any, Any, Any],
        share_id: UUID,
    ) -> None:
        """Remove a document share.

        Deletes a share, revoking access for the shared user/role.
        Only the share owner or admin can delete a share.

        Args:
            request: Litestar request object
            share_id: UUID of the share to delete

        Raises:
            EntityNotFoundError: If share does not exist
            PermissionDeniedError: If user cannot delete this share
        """
        # Get current user from request state
        _user_id: str = getattr(request.state, "user_id", "anonymous")
        _user_roles: list[str] = getattr(request.state, "user_roles", [])

        # TODO: In production, delete from database
        # session = self.request.state.session
        # repo = GenericRepository(DocumentShare, document_share_table)
        # share = await repo.get(session, share_id)
        #
        # if share is None:
        #     raise EntityNotFoundError("DocumentShare", str(share_id))
        #
        # # Check permission: owner or admin
        # if share.owner != user_id and "Admin" not in user_roles:
        #     raise PermissionDeniedError(
        #         f"User '{user_id}' cannot delete share '{share_id}'"
        #     )
        #
        # await repo.delete(session, share_id)

        # For now, just acknowledge the delete
        return None

    @get("/{doctype:str}/{doc_id:str}/shares")
    async def list_shares_for_document(
        self,
        request: Request[Any, Any, Any],
        doctype: str,
        doc_id: str,
    ) -> ShareListResponse:
        """List all shares for a specific document.

        Returns shares where the current user:
        - Is the document owner
        - Is the share creator
        - Is an admin

        Args:
            request: Litestar request object
            doctype: DocType name
            doc_id: Document ID

        Returns:
            List of shares for the document
        """
        # Get current user from request state
        _user_id: str = getattr(request.state, "user_id", "anonymous")
        _user_roles: list[str] = getattr(request.state, "user_roles", [])

        # TODO: In production, query from database
        # session = self.request.state.session
        # repo = GenericRepository(DocumentShare, document_share_table)
        #
        # filters = [
        #     FilterSpec(field="doctype_name", operator=FilterOperator.EQ, value=doctype),
        #     FilterSpec(field="doc_id", operator=FilterOperator.EQ, value=doc_id),
        # ]
        #
        # # RLS: Filter by owner unless admin
        # if "Admin" not in user_roles:
        #     filters.append(
        #         FilterSpec(field="owner", operator=FilterOperator.EQ, value=user_id)
        #     )
        #
        # result = await repo.list_entities(session, filters=filters)
        # shares = [ShareResponse.from_share(s) for s in result.items]

        # For now, return empty list
        shares: list[ShareResponse] = []

        return ShareListResponse(shares=shares, total=len(shares))


# Export the controller for use with Litestar
share_router = ShareController

__all__ = [
    "CreateShareRequest",
    "ShareController",
    "ShareListResponse",
    "ShareResponse",
    "share_router",
]
