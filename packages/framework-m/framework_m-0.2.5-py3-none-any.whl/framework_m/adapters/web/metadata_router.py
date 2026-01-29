"""Metadata API Routes.

This module provides metadata discovery endpoints:
- GET /api/meta/doctypes - List all registered DocTypes
- GET /api/meta/{doctype} - Get DocType schema (in meta_router.py)

These endpoints enable the frontend to dynamically discover
available DocTypes and build UI from schema.

Per ARCHITECTURE.md:
- Code-first Pydantic models
- MetaRegistry singleton holds all DocTypes
- Opt-in API exposure via api_resource=True
"""

from __future__ import annotations

from typing import Any

from litestar import Router, get
from pydantic import BaseModel

from framework_m.core.registry import MetaRegistry


class DocTypeInfo(BaseModel):
    """Brief DocType info for listing."""

    name: str
    module: str | None = None
    label: str | None = None
    is_child_table: bool = False
    api_resource: bool = False
    show_in_desk: bool = True  # Whether to show in Desk UI sidebar


class DocTypeListResponse(BaseModel):
    """Response for listing all DocTypes."""

    doctypes: list[DocTypeInfo]
    count: int


@get("/doctypes", tags=["Metadata"])
async def list_doctypes() -> DocTypeListResponse:
    """List all registered DocTypes.

    Returns summary info for each DocType including name, module,
    and whether it's exposed as an API resource.

    Returns:
        List of DocType info objects
    """
    registry = MetaRegistry.get_instance()
    doctype_names = registry.list_doctypes()

    doctypes: list[DocTypeInfo] = []
    for name in doctype_names:
        try:
            doctype_class = registry.get_doctype(name)
            meta = getattr(doctype_class, "Meta", None)

            doctypes.append(
                DocTypeInfo(
                    name=name,
                    module=getattr(doctype_class, "__module__", None),
                    label=getattr(meta, "label", name) if meta else name,
                    is_child_table=(
                        getattr(meta, "is_child_table", False) if meta else False
                    ),
                    api_resource=(
                        getattr(meta, "api_resource", False) if meta else False
                    ),
                    show_in_desk=getattr(meta, "show_in_desk", True) if meta else True,
                )
            )
        except KeyError:
            # DocType was removed during iteration
            continue

    return DocTypeListResponse(
        doctypes=doctypes,
        count=len(doctypes),
    )


@get("/{doctype_name:str}", tags=["Metadata"])
async def get_doctype_schema(doctype_name: str) -> dict[str, Any]:
    """Get schema for a specific DocType.

    Returns the full JSON Schema, layout, and permissions for the DocType.

    Args:
        doctype_name: Name of the DocType

    Returns:
        DocType schema including fields, layout, permissions

    Raises:
        NotFoundException: If DocType is not registered
    """
    from litestar.exceptions import NotFoundException

    registry = MetaRegistry.get_instance()

    try:
        doctype_class = registry.get_doctype(doctype_name)
    except KeyError as e:
        raise NotFoundException(f"DocType '{doctype_name}' not found") from e

    # Generate JSON Schema from Pydantic model
    schema = doctype_class.model_json_schema()

    # Extract metadata from Meta class
    meta = getattr(doctype_class, "Meta", None)

    return {
        "doctype": doctype_name,
        "module": getattr(doctype_class, "__module__", None),
        "schema": schema,
        "layout": getattr(meta, "layout", None) if meta else None,
        "permissions": getattr(meta, "permissions", {}) if meta else {},
        "metadata": {
            "label": getattr(meta, "label", doctype_name) if meta else doctype_name,
            "is_child_table": getattr(meta, "is_child_table", False) if meta else False,
            "api_resource": getattr(meta, "api_resource", False) if meta else False,
            "requires_auth": getattr(meta, "requires_auth", True) if meta else True,
            "apply_rls": getattr(meta, "apply_rls", True) if meta else True,
        },
    }


# Create router with /api/meta prefix
metadata_router = Router(
    path="/api/meta",
    route_handlers=[list_doctypes, get_doctype_schema],
    tags=["Metadata"],
)


__all__ = ["get_doctype_schema", "list_doctypes", "metadata_router"]
