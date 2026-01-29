"""Tenant Protocol - Multi-tenancy interface and context.

This module defines the tenancy protocol and context for Framework M's
multi-tenant architecture.

Modes:
- Single Tenant (Indie): Implicit "default" tenant with unlimited features
- Multi-Tenant (Enterprise): Tenant from gateway headers, feature flags per tenant

Configuration in framework_config.toml:
    [tenancy]
    mode = "single"  # or "multi"
    default_tenant_id = "default"

Example:
    from framework_m.core.interfaces.tenant import TenantProtocol, TenantContext

    class MyTenantAdapter(TenantProtocol):
        def get_current_tenant(self) -> str:
            return "default"

        def get_tenant_attributes(self, tenant_id: str) -> dict:
            return {"plan": "unlimited", "features": "*"}
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from framework_m.cli.config import load_config

# =============================================================================
# Tenant Context
# =============================================================================


class TenantContext(BaseModel):
    """Context object representing the current tenant.

    Carries tenant information through the request lifecycle.

    Attributes:
        tenant_id: Unique tenant identifier
        attributes: Feature flags, plan info, and other tenant-specific data
        is_default: Whether this is the implicit default tenant

    Example:
        ctx = TenantContext(
            tenant_id="acme-corp",
            attributes={"plan": "enterprise", "features": ["advanced_reports"]},
        )
    """

    tenant_id: str = Field(description="Unique tenant identifier")
    attributes: dict[str, Any] = Field(
        default_factory=dict,
        description="Tenant attributes (plan, features, flags)",
    )
    is_default: bool = Field(
        default=False,
        description="True if this is the implicit default tenant",
    )


# =============================================================================
# Tenant Protocol
# =============================================================================


@runtime_checkable
class TenantProtocol(Protocol):
    """Protocol for tenant resolution and attribute retrieval.

    Implementations must provide:
    - get_current_tenant(): Resolve tenant from request context
    - get_tenant_attributes(): Fetch tenant-specific attributes

    Two standard implementations:
    - ImplicitTenantAdapter: Single-tenant mode (Indie)
    - HeaderTenantAdapter: Multi-tenant from gateway headers (Enterprise)

    Example:
        class MyTenantAdapter:
            def get_current_tenant(self) -> str:
                return "my-tenant"

            def get_tenant_attributes(self, tenant_id: str) -> dict[str, Any]:
                return {"plan": "pro"}
    """

    def get_current_tenant(self) -> str:
        """Get the current tenant ID from request context.

        Returns:
            Tenant identifier string
        """
        ...

    def get_tenant_attributes(self, tenant_id: str) -> dict[str, Any]:
        """Get attributes for a specific tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Dict of tenant attributes (plan, features, flags, etc.)
        """
        ...


# =============================================================================
# Configuration
# =============================================================================


def get_tenancy_config() -> dict[str, Any]:
    """Get tenancy configuration from framework_config.toml.

    Returns:
        Dict with mode, default_tenant_id, and other settings
    """
    config = load_config()
    tenancy_config = config.get("tenancy", {})

    return {
        "mode": tenancy_config.get("mode", "single"),
        "default_tenant_id": tenancy_config.get("default_tenant_id", "default"),
        **{
            k: v
            for k, v in tenancy_config.items()
            if k not in ("mode", "default_tenant_id")
        },
    }


def is_multi_tenant() -> bool:
    """Check if the application is configured for multi-tenancy.

    Returns:
        True if mode is "multi", False for "single" (default)
    """
    config = get_tenancy_config()
    result: bool = config["mode"] == "multi"
    return result


def get_default_tenant_id() -> str:
    """Get the default tenant ID for single-tenant mode.

    Returns:
        Default tenant ID (usually "default")
    """
    config = get_tenancy_config()
    return str(config["default_tenant_id"])


__all__ = [
    "TenantContext",
    "TenantProtocol",
    "get_default_tenant_id",
    "get_tenancy_config",
    "is_multi_tenant",
]
