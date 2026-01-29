"""Auth Adapters - Authentication and Authorization implementations.

This package provides adapter implementations for:
- RbacPermissionAdapter: Role-Based Access Control using DocType.Meta.permissions
- LocalIdentityAdapter: Identity management for Indie mode (SQL-backed users)
- FederatedIdentityAdapter: Identity management for Enterprise mode (header hydration)
- Authentication strategies: BearerTokenAuth, ApiKeyAuth, HeaderAuth, AuthChain
"""

from framework_m.adapters.auth.federated_identity import (
    FederatedIdentityAdapter,
    hydrate_from_headers,
)
from framework_m.adapters.auth.local_identity import (
    LocalIdentityAdapter,
    hash_password,
    verify_password,
)
from framework_m.adapters.auth.rbac_permission import RbacPermissionAdapter
from framework_m.adapters.auth.strategies import (
    ApiKeyAuth,
    AuthChain,
    BearerTokenAuth,
    HeaderAuth,
    create_auth_chain_from_config,
)

__all__ = [
    "ApiKeyAuth",
    "AuthChain",
    "BearerTokenAuth",
    "FederatedIdentityAdapter",
    "HeaderAuth",
    "LocalIdentityAdapter",
    "RbacPermissionAdapter",
    "create_auth_chain_from_config",
    "hash_password",
    "hydrate_from_headers",
    "verify_password",
]
