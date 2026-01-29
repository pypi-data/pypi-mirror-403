"""API Key Routes - API key management endpoints.

This module provides REST endpoints for managing API keys:
- POST /api/v1/auth/api-keys - Create new API key
- GET /api/v1/auth/api-keys - List user's API keys
- DELETE /api/v1/auth/api-keys/{id} - Revoke API key

API keys are used for programmatic access (scripts, integrations, CLI tools).

Example:
    from litestar import Litestar
    from framework_m.adapters.web.api_key_routes import api_key_routes_router

    app = Litestar(route_handlers=[api_key_routes_router])
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from litestar import Router, delete, get, post
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    pass


# =============================================================================
# Request/Response Models
# =============================================================================


class CreateApiKeyRequest(BaseModel):
    """Request model for creating an API key.

    Attributes:
        name: Human-readable label for the key
        scopes: Optional list of permission scopes
        expires_in_days: Optional expiration in days (None = no expiration)
    """

    name: str = Field(description="Human-readable key label")
    scopes: list[str] = Field(
        default_factory=list,
        description="Optional permission scopes",
    )
    expires_in_days: int | None = Field(
        default=None,
        description="Expiration in days (None = no expiration)",
    )


class CreateApiKeyResponse(BaseModel):
    """Response model for created API key.

    IMPORTANT: This is the ONLY time the raw key is returned.
    The key is hashed before storage and cannot be recovered.

    Attributes:
        id: API key document ID
        name: Human-readable label
        key: The raw API key (only returned once!)
        scopes: Permission scopes
        expires_at: Expiration datetime
        created_at: Creation datetime
    """

    id: str = Field(description="API key document ID")
    name: str = Field(description="Human-readable label")
    key: str = Field(description="The raw API key (only shown once!)")
    scopes: list[str] = Field(description="Permission scopes")
    expires_at: datetime | None = Field(description="Expiration time")
    created_at: datetime = Field(description="Creation time")


class ApiKeyInfo(BaseModel):
    """API key information (without the raw key).

    Attributes:
        id: API key document ID
        name: Human-readable label
        scopes: Permission scopes
        expires_at: Expiration datetime
        last_used_at: Last usage datetime
        created_at: Creation datetime
    """

    id: str = Field(description="API key document ID")
    name: str = Field(description="Human-readable label")
    scopes: list[str] = Field(description="Permission scopes")
    expires_at: datetime | None = Field(description="Expiration time")
    last_used_at: datetime | None = Field(description="Last usage time")
    created_at: datetime = Field(description="Creation time")


# =============================================================================
# Helper Functions
# =============================================================================


def generate_api_key() -> str:
    """Generate a secure API key.

    Format: fm_<random_32_bytes>

    Returns:
        URL-safe API key string
    """
    return f"fm_{secrets.token_urlsafe(32)}"


# =============================================================================
# Route Handlers
# =============================================================================


@post("/")
async def create_api_key(
    data: CreateApiKeyRequest,
    # user_context: "UserContext",  # Injected by middleware
) -> CreateApiKeyResponse:
    """Create a new API key for the authenticated user.

    The raw key is returned ONLY in this response.
    It cannot be recovered later - only the hash is stored.

    Args:
        data: API key creation request

    Returns:
        CreateApiKeyResponse with the raw key (only time it's shown!)
    """
    # Generate unique key
    raw_key = generate_api_key()

    # In a full implementation:
    # 1. Hash the key (using argon2)
    # 2. Create ApiKey DocType with hash
    # 3. Save to database
    # 4. Return the raw key

    now = datetime.now(UTC)
    expires_at = None
    if data.expires_in_days:
        expires_at = now + timedelta(days=data.expires_in_days)

    # Placeholder response
    return CreateApiKeyResponse(
        id=f"apikey_{secrets.token_urlsafe(8)}",
        name=data.name,
        key=raw_key,
        scopes=data.scopes,
        expires_at=expires_at,
        created_at=now,
    )


@get("/")
async def list_api_keys() -> list[ApiKeyInfo]:
    """List all API keys for the authenticated user.

    Note: Raw keys are never returned - only metadata.

    Returns:
        List of API key info objects
    """
    # In a full implementation:
    # 1. Get user ID from context
    # 2. Query ApiKey DocType by user_id
    # 3. Return list of key info

    # Placeholder response
    return []


@delete("/{key_id:str}")
async def revoke_api_key(key_id: str) -> dict[str, Any]:
    """Revoke (delete) an API key.

    Args:
        key_id: API key document ID to revoke

    Returns:
        Confirmation message

    Raises:
        NotFoundException: If key not found or not owned by user
    """
    # In a full implementation:
    # 1. Verify key belongs to current user
    # 2. Delete ApiKey DocType
    # 3. Return confirmation

    # Placeholder: pretend we deleted it
    return {
        "message": "API key revoked",
        "id": key_id,
    }


# =============================================================================
# Router
# =============================================================================


api_key_routes_router = Router(
    path="/api/v1/auth/api-keys",
    route_handlers=[create_api_key, list_api_keys, revoke_api_key],
    tags=["auth"],
)


__all__ = [
    "ApiKeyInfo",
    "CreateApiKeyRequest",
    "CreateApiKeyResponse",
    "api_key_routes_router",
    "create_api_key",
    "list_api_keys",
    "revoke_api_key",
]
