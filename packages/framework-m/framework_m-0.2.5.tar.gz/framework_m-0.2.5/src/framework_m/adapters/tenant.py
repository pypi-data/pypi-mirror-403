"""Tenant Adapters - Implementations for tenant resolution.

This module provides tenant adapter implementations:
- ImplicitTenantAdapter: Single-tenant mode (Indie/Mode A)
- HeaderTenantAdapter: Multi-tenant from gateway headers (Enterprise/Mode B)

Configuration in framework_config.toml:
    [tenancy]
    mode = "single"  # Uses ImplicitTenantAdapter
    # OR
    mode = "multi"   # Uses HeaderTenantAdapter

Example:
    from framework_m.adapters.tenant import ImplicitTenantAdapter, HeaderTenantAdapter

    # Mode A: Single tenant
    adapter = ImplicitTenantAdapter()
    tenant_id = adapter.get_current_tenant()  # "default"

    # Mode B: Multi-tenant from headers
    adapter = HeaderTenantAdapter(headers={"x-tenant-id": "acme"})
    tenant_id = adapter.get_current_tenant()  # "acme"
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from framework_m.core.interfaces.tenant import (
    TenantContext,
    get_default_tenant_id,
)

# =============================================================================
# Mode A: Single Tenant (Indie)
# =============================================================================


class ImplicitTenantAdapter:
    """Tenant adapter for single-tenant mode (Indie/Mode A).

    Returns a fixed "default" tenant with unlimited features.
    No database lookup required - perfect for indie apps.

    Args:
        tenant_id: Override default tenant ID (defaults to config)
        attributes: Override default attributes

    Example:
        adapter = ImplicitTenantAdapter()
        tenant_id = adapter.get_current_tenant()  # "default"
        attrs = adapter.get_tenant_attributes("default")
        # {"plan": "unlimited", "features": "*"}
    """

    def __init__(
        self,
        tenant_id: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """Initialize ImplicitTenantAdapter.

        Args:
            tenant_id: Override tenant ID (defaults to config)
            attributes: Override tenant attributes
        """
        self._tenant_id = tenant_id or get_default_tenant_id()
        self._attributes = attributes or {
            "plan": "unlimited",
            "features": "*",
        }

    def get_current_tenant(self) -> str:
        """Get the implicit tenant ID.

        Returns:
            The configured default tenant ID
        """
        return self._tenant_id

    def get_tenant_attributes(self, tenant_id: str) -> dict[str, Any]:
        """Get attributes for the tenant.

        Args:
            tenant_id: Tenant identifier (ignored in single-tenant mode)

        Returns:
            Default unlimited attributes
        """
        return self._attributes.copy()

    def get_context(self) -> TenantContext:
        """Get full tenant context.

        Returns:
            TenantContext with default tenant info
        """
        return TenantContext(
            tenant_id=self._tenant_id,
            attributes=self._attributes.copy(),
            is_default=True,
        )


# =============================================================================
# Mode B: Multi-Tenant (Enterprise)
# =============================================================================


class HeaderTenantAdapter:
    """Tenant adapter for multi-tenant mode (Enterprise/Mode B).

    Extracts tenant ID and attributes from gateway headers.
    The gateway (Keycloak, Auth0, etc.) is responsible for
    authentication and populating tenant headers.

    Expected headers:
        - X-Tenant-ID: Tenant identifier (required)
        - X-Tenant-Attributes: JSON-encoded tenant attributes (optional)

    Args:
        headers: Request headers (lowercase keys)
        tenant_header: Header name for tenant ID (default: x-tenant-id)
        attributes_header: Header name for attributes (default: x-tenant-attributes)

    Example:
        headers = {
            "x-tenant-id": "acme-corp",
            "x-tenant-attributes": '{"plan": "enterprise", "features": ["reports"]}',
        }
        adapter = HeaderTenantAdapter(headers=headers)
        tenant_id = adapter.get_current_tenant()  # "acme-corp"
    """

    def __init__(
        self,
        headers: Mapping[str, str],
        tenant_header: str = "x-tenant-id",
        attributes_header: str = "x-tenant-attributes",
        default_tenant_id: str = "default",
    ) -> None:
        """Initialize HeaderTenantAdapter.

        Args:
            headers: Request headers (lowercase keys expected)
            tenant_header: Header name for tenant ID
            attributes_header: Header name for attributes JSON
            default_tenant_id: Fallback if no header present
        """
        self._headers = headers
        self._tenant_header = tenant_header
        self._attributes_header = attributes_header
        self._default_tenant_id = default_tenant_id

    def get_current_tenant(self) -> str:
        """Get tenant ID from gateway header.

        Returns:
            Tenant ID from X-Tenant-ID header, or default
        """
        return self._headers.get(self._tenant_header, self._default_tenant_id)

    def get_tenant_attributes(self, tenant_id: str) -> dict[str, Any]:
        """Get tenant attributes from gateway header.

        The gateway populates X-Tenant-Attributes with JSON
        containing plan, features, and other tenant-specific flags.

        Args:
            tenant_id: Tenant identifier (for validation, not used in lookup)

        Returns:
            Parsed attributes dict, or empty dict if not present
        """
        attrs_json = self._headers.get(self._attributes_header, "")
        if not attrs_json:
            return {}

        try:
            result = json.loads(attrs_json)
            if isinstance(result, dict):
                return result
            return {}
        except json.JSONDecodeError:
            return {}

    def get_context(self) -> TenantContext:
        """Get full tenant context from headers.

        Returns:
            TenantContext parsed from gateway headers
        """
        tenant_id = self.get_current_tenant()
        return TenantContext(
            tenant_id=tenant_id,
            attributes=self.get_tenant_attributes(tenant_id),
            is_default=(tenant_id == self._default_tenant_id),
        )


# =============================================================================
# Factory Function
# =============================================================================


def create_tenant_adapter_from_headers(
    headers: Mapping[str, str] | None = None,
) -> ImplicitTenantAdapter | HeaderTenantAdapter:
    """Create appropriate tenant adapter based on config and headers.

    If multi-tenant mode is enabled AND headers are provided,
    uses HeaderTenantAdapter. Otherwise uses ImplicitTenantAdapter.

    Args:
        headers: Optional request headers for multi-tenant mode

    Returns:
        Appropriate tenant adapter instance
    """
    from framework_m.core.interfaces.tenant import is_multi_tenant

    if is_multi_tenant() and headers is not None:
        return HeaderTenantAdapter(headers=headers)
    return ImplicitTenantAdapter()


__all__ = [
    "HeaderTenantAdapter",
    "ImplicitTenantAdapter",
    "create_tenant_adapter_from_headers",
]
