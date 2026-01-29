"""OAuth Routes - OAuth2/OIDC authentication endpoints.

This module provides REST endpoints for OAuth2 social login:
- GET /api/v1/auth/oauth/{provider}/start - Redirect to OAuth provider
- GET /api/v1/auth/oauth/{provider}/callback - Handle OAuth callback

Configuration in framework_config.toml:
    [auth.oauth]
    enabled = true
    providers = ["google", "github"]

    [auth.oauth.google]
    client_id = "${GOOGLE_CLIENT_ID}"
    client_secret = "${GOOGLE_CLIENT_SECRET}"

Example:
    from litestar import Litestar
    from framework_m.adapters.web.oauth_routes import oauth_routes_router

    app = Litestar(route_handlers=[oauth_routes_router])
"""

from __future__ import annotations

import secrets
from typing import TYPE_CHECKING, Any

from litestar import Router, get
from litestar.exceptions import NotFoundException
from litestar.response import Redirect

from framework_m.cli.config import load_config

if TYPE_CHECKING:
    pass


# =============================================================================
# Configuration
# =============================================================================


def get_oauth_config() -> dict[str, Any]:
    """Get OAuth configuration from framework_config.toml.

    Returns:
        OAuth configuration dict with enabled, providers, and provider configs
    """
    config = load_config()
    auth_config = config.get("auth", {})
    oauth_config = auth_config.get("oauth", {})

    return {
        "enabled": oauth_config.get("enabled", False),
        "providers": oauth_config.get("providers", []),
        **{k: v for k, v in oauth_config.items() if k not in ("enabled", "providers")},
    }


def get_provider_config(provider: str) -> dict[str, Any] | None:
    """Get configuration for a specific OAuth provider.

    Args:
        provider: Provider name (google, github, etc.)

    Returns:
        Provider config dict or None if not configured
    """
    oauth_config = get_oauth_config()

    if provider not in oauth_config.get("providers", []):
        return None

    result: dict[str, Any] | None = oauth_config.get(provider, {})
    return result if result else None


# =============================================================================
# OAuth2 Provider Registry
# =============================================================================

# Well-known OAuth2 provider configurations
PROVIDER_CONFIGS: dict[str, dict[str, str]] = {
    "google": {
        "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://www.googleapis.com/oauth2/v3/userinfo",
        "scope": "openid email profile",
    },
    "github": {
        "authorization_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "userinfo_url": "https://api.github.com/user",
        "scope": "read:user user:email",
    },
    "microsoft": {
        "authorization_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "userinfo_url": "https://graph.microsoft.com/v1.0/me",
        "scope": "openid email profile",
    },
}


def get_oidc_well_known(provider_cfg: dict[str, Any]) -> dict[str, str] | None:
    """Get OIDC well-known config for generic OIDC provider.

    For generic OIDC providers, the config must include:
    - authorization_url: Authorization endpoint
    - token_url: Token endpoint
    - userinfo_url: UserInfo endpoint (optional)
    - scope: OAuth scopes (defaults to "openid email profile")

    Alternatively, provide discovery_url to auto-discover endpoints.

    Args:
        provider_cfg: Provider configuration from framework_config.toml

    Returns:
        Dict with authorization_url, token_url, userinfo_url, scope
    """
    # Check for required OIDC fields
    if "authorization_url" in provider_cfg and "token_url" in provider_cfg:
        return {
            "authorization_url": provider_cfg["authorization_url"],
            "token_url": provider_cfg["token_url"],
            "userinfo_url": provider_cfg.get("userinfo_url", ""),
            "scope": provider_cfg.get("scope", "openid email profile"),
        }

    # If discovery_url provided, we'd fetch from /.well-known/openid-configuration
    # For now, return None if not fully configured
    return None


def is_generic_oidc_provider(provider: str) -> bool:
    """Check if provider is a generic OIDC provider (not in well-known list).

    Args:
        provider: Provider name

    Returns:
        True if not a well-known provider
    """
    return provider not in PROVIDER_CONFIGS


# =============================================================================
# Route Handlers
# =============================================================================


@get("/{provider:str}/start")
async def oauth_start(provider: str) -> Redirect:
    """Start OAuth2 flow - redirect to provider.

    Generates a state parameter for CSRF protection and redirects
    the user to the OAuth provider's authorization page.

    Supports both well-known providers (google, github, microsoft) and
    generic OIDC providers with custom configuration.

    Args:
        provider: OAuth provider name (google, github, microsoft, or custom)

    Returns:
        Redirect response to provider's auth URL

    Raises:
        NotFoundException: If provider not configured or not supported
    """
    provider_cfg = get_provider_config(provider)
    if provider_cfg is None:
        raise NotFoundException(detail=f"OAuth provider '{provider}' not configured")

    # Get well-known config or try generic OIDC
    well_known = PROVIDER_CONFIGS.get(provider)
    if well_known is None:
        # Try generic OIDC configuration
        well_known = get_oidc_well_known(provider_cfg)
        if well_known is None:
            raise NotFoundException(
                detail=f"OAuth provider '{provider}' requires authorization_url and token_url"
            )

    # Generate CSRF state
    state = secrets.token_urlsafe(32)

    # Build authorization URL
    # Note: In production, store state in session for validation
    client_id = provider_cfg.get("client_id", "")
    redirect_uri = provider_cfg.get(
        "redirect_uri", f"/api/v1/auth/oauth/{provider}/callback"
    )
    scope = well_known["scope"]

    auth_url = (
        f"{well_known['authorization_url']}"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope={scope}"
        f"&state={state}"
    )

    return Redirect(path=auth_url)


@get("/{provider:str}/callback")
async def oauth_callback(
    provider: str,
    code: str | None = None,
    oauth_state: str | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    """Handle OAuth2 callback from provider.

    Receives the authorization code, exchanges it for tokens,
    fetches user info, and creates/links a local user account.

    Args:
        provider: OAuth provider name
        code: Authorization code from provider
        oauth_state: State parameter for CSRF validation (renamed from 'state' to avoid Litestar conflict)
        error: Error from provider if authorization failed

    Returns:
        Dict with user info and session token

    Raises:
        NotAuthorizedException: If OAuth flow fails
    """
    from litestar.exceptions import NotAuthorizedException

    if error:
        raise NotAuthorizedException(detail=f"OAuth error: {error}")

    if code is None:
        raise NotAuthorizedException(detail="No authorization code received")

    provider_cfg = get_provider_config(provider)
    if provider_cfg is None:
        raise NotFoundException(detail=f"OAuth provider '{provider}' not configured")

    # In a full implementation:
    # 1. Validate oauth_state against session
    # 2. Exchange code for tokens
    # 3. Fetch user info from provider
    # 4. Find or create SocialAccount + User
    # 5. Create session/JWT

    # Placeholder response for now
    return {
        "provider": provider,
        "message": "OAuth callback received",
        "code_received": code is not None,
        "note": "Full implementation requires authlib integration",
    }


# =============================================================================
# Router
# =============================================================================


oauth_routes_router = Router(
    path="/api/v1/auth/oauth",
    route_handlers=[oauth_start, oauth_callback],
    tags=["auth"],
)


__all__ = [
    "get_oauth_config",
    "get_provider_config",
    "oauth_callback",
    "oauth_routes_router",
    "oauth_start",
]
