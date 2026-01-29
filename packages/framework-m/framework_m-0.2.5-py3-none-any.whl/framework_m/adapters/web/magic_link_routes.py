"""Magic Link Routes - Passwordless authentication API.

This module provides REST endpoints for passwordless authentication:
- POST /api/v1/auth/magic-link - Request magic link email
- GET /api/v1/auth/magic-link/{token} - Verify token and create session

Magic links allow users to authenticate without a password by receiving
a secure, time-limited link via email.

Example:
    # Request a magic link
    POST /api/v1/auth/magic-link
    {"email": "user@example.com"}

    # User clicks link in email
    GET /api/v1/auth/magic-link/abc123...

    # Returns session token
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
import time
from typing import Any

from litestar import Response, Router, get, post
from litestar.exceptions import NotAuthorizedException, NotFoundException
from litestar.status_codes import HTTP_200_OK, HTTP_202_ACCEPTED
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================


class MagicLinkConfig:
    """Magic link configuration.

    Attributes:
        secret_key: Secret key for signing tokens
        token_expiry: Token validity in seconds (default 15 minutes)
        link_base_url: Base URL for magic link (e.g., https://app.example.com)
    """

    def __init__(
        self,
        secret_key: str,
        token_expiry: int = 900,  # 15 minutes
        link_base_url: str = "http://localhost:8000",
    ) -> None:
        self.secret_key = secret_key
        self.token_expiry = token_expiry
        self.link_base_url = link_base_url


# Module-level config
_config: MagicLinkConfig | None = None

# In-memory token store (replace with Redis in production)
_pending_tokens: dict[str, dict[str, Any]] = {}


def configure_magic_link(config: MagicLinkConfig) -> None:
    """Configure magic link settings.

    Args:
        config: Magic link configuration
    """
    global _config
    _config = config


def get_config() -> MagicLinkConfig:
    """Get magic link configuration."""
    if _config is None:
        # Default config for development
        return MagicLinkConfig(
            secret_key="dev-secret-change-in-production",
            token_expiry=900,
        )
    return _config


# =============================================================================
# DTOs
# =============================================================================


class MagicLinkRequest(BaseModel):
    """Request body for magic link."""

    email: str = Field(description="Email address to send magic link to")
    redirect_url: str | None = Field(
        default=None,
        description="URL to redirect after authentication",
    )


class MagicLinkResponse(BaseModel):
    """Response for magic link request."""

    message: str
    expires_in: int


class MagicLinkVerifyResponse(BaseModel):
    """Response for magic link verification."""

    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str | None = None


# =============================================================================
# Token Generation
# =============================================================================


def generate_magic_token(email: str, expiry: int) -> str:
    """Generate a secure magic link token.

    Args:
        email: User's email address
        expiry: Token expiry time (Unix timestamp)

    Returns:
        Secure token string
    """
    config = get_config()

    # Create random token
    random_bytes = secrets.token_bytes(32)

    # Create payload
    payload = f"{email}:{expiry}:{random_bytes.hex()}"

    # Sign with HMAC
    signature = hmac.new(
        config.secret_key.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()

    # Combine: random + signature (both needed to verify)
    token = f"{random_bytes.hex()}.{signature}"

    return token


def verify_magic_token(token: str, stored_data: dict[str, Any]) -> bool:
    """Verify a magic link token.

    Args:
        token: Token from magic link
        stored_data: Stored token data

    Returns:
        True if valid, False otherwise
    """
    config = get_config()

    try:
        random_hex, signature = token.split(".")

        # Recreate payload
        payload = f"{stored_data['email']}:{stored_data['expiry']}:{random_hex}"

        # Verify signature
        expected_sig = hmac.new(
            config.secret_key.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_sig):
            return False

        # Check expiry
        expiry: float = float(stored_data["expiry"])
        return time.time() <= expiry

    except (ValueError, KeyError):
        return False


# =============================================================================
# Route Handlers
# =============================================================================


@post("/magic-link")
async def request_magic_link(data: MagicLinkRequest) -> Response[Any]:
    """Request a magic link email.

    Sends a one-time login link to the specified email address.
    The link expires after 15 minutes by default.

    Args:
        data: Request with email address

    Returns:
        202 Accepted with expiry info
    """
    config = get_config()

    # Generate token
    expiry = int(time.time()) + config.token_expiry
    token = generate_magic_token(data.email, expiry)

    # Store token data
    _pending_tokens[token] = {
        "email": data.email,
        "expiry": expiry,
        "redirect_url": data.redirect_url,
        "used": False,
    }

    # Build magic link URL
    magic_link = f"{config.link_base_url}/api/v1/auth/magic-link/{token}"

    # Queue email
    try:
        from framework_m.adapters.email import queue_email

        await queue_email(
            to=data.email,
            subject="Your Magic Link",
            body=f"""
            <h1>Login to Your Account</h1>
            <p>Click the link below to log in. This link expires in {config.token_expiry // 60} minutes.</p>
            <p><a href="{magic_link}">Click here to log in</a></p>
            <p>If you didn't request this link, you can safely ignore this email.</p>
            <p><small>Link: {magic_link}</small></p>
            """,
            priority="high",
        )
        logger.info("Magic link email queued for %s", data.email)
    except Exception as e:
        logger.error("Failed to queue magic link email: %s", str(e))
        # Continue anyway - in dev mode, log the link
        logger.info("DEV MODE - Magic link: %s", magic_link)

    response = MagicLinkResponse(
        message="If an account exists with this email, a login link has been sent.",
        expires_in=config.token_expiry,
    )

    return Response(
        content=response.model_dump_json(),
        status_code=HTTP_202_ACCEPTED,
        media_type="application/json",
    )


@get("/magic-link/{token:str}")
async def verify_magic_link(token: str) -> Response[Any]:
    """Verify magic link token and create session.

    When user clicks the magic link, this endpoint validates the token
    and returns an access token for authentication.

    Args:
        token: Magic link token from URL

    Returns:
        Access token and session info

    Raises:
        NotAuthorizedException: If token is invalid or expired
        NotFoundException: If token not found
    """
    # Check if token exists
    if token not in _pending_tokens:
        raise NotFoundException(detail="Invalid or expired magic link")

    stored_data = _pending_tokens[token]

    # Check if already used
    if stored_data.get("used"):
        del _pending_tokens[token]
        raise NotAuthorizedException(detail="Magic link has already been used")

    # Verify token
    if not verify_magic_token(token, stored_data):
        del _pending_tokens[token]
        raise NotAuthorizedException(detail="Invalid or expired magic link")

    # Mark as used
    stored_data["used"] = True
    email = stored_data["email"]

    # Create session/token for user
    # TODO: When UserManager.authenticate_magic_link is implemented, use it
    # For now, use fallback token generation
    logger.info("Magic link verified for %s", email)

    response = MagicLinkVerifyResponse(
        access_token=f"magic-link-token-{secrets.token_urlsafe(32)}",
        token_type="bearer",
        expires_in=86400,  # 24 hours
    )

    # Clean up used token
    del _pending_tokens[token]

    return Response(
        content=response.model_dump_json(),
        status_code=HTTP_200_OK,
        media_type="application/json",
    )


# =============================================================================
# Router
# =============================================================================


magic_link_router = Router(
    path="/api/v1/auth",
    route_handlers=[request_magic_link, verify_magic_link],
    tags=["auth"],
)


def create_magic_link_router() -> Router:
    """Create the magic link router.

    Returns:
        Litestar Router with magic link endpoints
    """
    return magic_link_router


# =============================================================================
# Helpers
# =============================================================================


def clear_expired_tokens() -> int:
    """Clear expired tokens from memory.

    Returns:
        Number of tokens cleared
    """
    now = time.time()
    expired = [token for token, data in _pending_tokens.items() if data["expiry"] < now]
    for token in expired:
        del _pending_tokens[token]
    return len(expired)


__all__ = [
    "MagicLinkConfig",
    "MagicLinkRequest",
    "MagicLinkResponse",
    "MagicLinkVerifyResponse",
    "clear_expired_tokens",
    "configure_magic_link",
    "create_magic_link_router",
    "magic_link_router",
    "request_magic_link",
    "verify_magic_link",
]
