"""Metadata Routes - DocType metadata API.

This module provides the metadata API endpoint for retrieving DocType
schema, layout, and permissions information.

Endpoint:
    GET /api/meta/{doctype}

Returns DocType metadata including:
- JSON Schema (from Pydantic model_json_schema())
- Layout configuration (from Meta.layout)
- Permissions (from Meta.permissions)
- Additional metadata (requires_auth, apply_rls, etc.)

Example:
    GET /api/meta/Invoice
    {
        "doctype": "Invoice",
        "schema": {...},
        "layout": {...},
        "permissions": {...},
        "metadata": {
            "requires_auth": true,
            "apply_rls": true,
            "rls_field": "owner",
            "api_resource": true
        }
    }
"""

from __future__ import annotations

from typing import Any

from litestar import Request, Router, get
from litestar.di import Provide
from litestar.exceptions import NotFoundException
from sqlalchemy.ext.asyncio import AsyncSession

from framework_m.adapters.web.middleware.locale import provide_locale
from framework_m.core.registry import MetaRegistry


@get("/{doctype:str}")
async def get_doctype_metadata(
    doctype: str,
    request: Request[Any, Any, Any],
    locale: str,
) -> dict[str, Any]:
    """Get DocType metadata including schema, layout, and permissions.

    Automatically translates field labels based on the resolved locale
    from Accept-Language header, user preference, tenant default, or system default.

    Args:
        doctype: The DocType name (e.g., "Invoice")
        request: Litestar request object (for accessing state/session)
        locale: Resolved locale from middleware (injected)

    Returns:
        Dict containing schema, layout, permissions, and metadata
        with translated field labels if available

    Raises:
        NotFoundException: If DocType is not registered
    """
    registry = MetaRegistry.get_instance()

    # Get DocType class from registry
    try:
        doctype_class = registry.get_doctype(doctype)
    except KeyError:
        raise NotFoundException(detail=f"DocType '{doctype}' not found") from None

    # Generate JSON Schema from Pydantic model
    # This includes field titles, descriptions, types, and constraints
    schema = doctype_class.model_json_schema()

    # Translate field labels if i18n adapter is available
    try:
        from framework_m.adapters.db.generic_repository import GenericRepository
        from framework_m.adapters.i18n import DefaultI18nAdapter
        from framework_m.core.doctypes.tenant_translation import TenantTranslation
        from framework_m.core.doctypes.translation import Translation

        # Get session and tenant from request state if available
        session: AsyncSession | None = getattr(request.state, "db_session", None)
        tenant_ctx = getattr(request.state, "tenant", None)
        tenant_id: str | None = tenant_ctx.tenant_id if tenant_ctx else None

        if session and "properties" in schema:
            # Create i18n adapter with tenant translation support
            from framework_m.adapters.db.table_registry import TableRegistry

            table_registry = TableRegistry()
            translation_table = table_registry.get_table("Translation")
            tenant_translation_table = table_registry.get_table("TenantTranslation")

            translation_repo = GenericRepository(Translation, translation_table)
            tenant_translation_repo = GenericRepository(
                TenantTranslation, tenant_translation_table
            )
            i18n_adapter = DefaultI18nAdapter(
                translation_repo=translation_repo,  # type: ignore[arg-type]
                tenant_translation_repo=tenant_translation_repo,  # type: ignore[arg-type]
                default_locale="en",
            )

            # Translate field descriptions (labels)
            for _field_name, field_schema in schema["properties"].items():
                if "description" in field_schema:
                    original_desc = field_schema["description"]
                    # Try to translate the description (with tenant override support)
                    translated_desc = await i18n_adapter.translate(
                        original_desc,
                        locale=locale,
                        session=session,
                        translation_context="field_label",
                        tenant_id=tenant_id,
                    )
                    # Only update if translation was found (not same as original)
                    if translated_desc != original_desc:
                        field_schema["description"] = translated_desc

                # Also translate title if present
                if "title" in field_schema:
                    original_title = field_schema["title"]
                    translated_title = await i18n_adapter.translate(
                        original_title,
                        locale=locale,
                        session=session,
                        translation_context="field_label",
                        tenant_id=tenant_id,
                    )
                    if translated_title != original_title:
                        field_schema["title"] = translated_title

    except (ImportError, AttributeError):
        # i18n not configured, skip translation
        pass

    # Get layout configuration from Meta class
    layout = doctype_class.get_layout()

    # Get permissions configuration from Meta class
    permissions = doctype_class.get_permissions()

    # Get additional metadata flags
    metadata = {
        "requires_auth": doctype_class.get_requires_auth(),
        "apply_rls": doctype_class.get_apply_rls(),
        "rls_field": doctype_class.get_rls_field(),
        "api_resource": doctype_class.get_api_resource(),
    }

    return {
        "doctype": doctype,
        "schema": schema,
        "layout": layout,
        "permissions": permissions,
        "metadata": metadata,
        "locale": locale,  # Include resolved locale in response
    }


# Create router
meta_routes_router = Router(
    path="/api/meta",
    route_handlers=[get_doctype_metadata],
    tags=["Metadata"],
    dependencies={"locale": Provide(provide_locale, sync_to_thread=False)},
)


__all__ = ["get_doctype_metadata", "meta_routes_router"]
