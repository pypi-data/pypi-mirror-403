"""System Context - Elevated operations for background jobs and migrations.

This module provides a context manager for running operations with system-level
privileges, bypassing normal user authentication and RLS.

Key Features:
- SystemPrincipal: Principal representing system/service operations
- system_context(): Async context manager for elevated access
- Context tracking via contextvars for thread-safe access

Example:
    async def sync_external_data():
        async with system_context() as ctx:
            # Runs with system principal, bypasses RLS
            await repo.save(session, data, user=ctx.to_user_context())

Important:
    - Use ONLY in background jobs, migrations, webhooks
    - All operations are logged with principal="system"
    - Never expose system_context to user-facing code
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass, field

from framework_m.core.interfaces.auth_context import UserContext

# Context variable to track current system context
_system_context_var: ContextVar[SystemPrincipal | None] = ContextVar(
    "system_context", default=None
)


@dataclass
class SystemPrincipal:
    """Principal for system-level operations.

    Used for background jobs, migrations, and service-to-service calls
    that need elevated access without user authentication.

    Attributes:
        id: Principal identifier, defaults to "system"
        roles: List of roles, defaults to ["System"]
        is_system: Always True for system principals
        description: Optional description for audit logging

    Example:
        principal = SystemPrincipal()  # Default system user
        principal = SystemPrincipal(id="scheduler")  # Named system process
    """

    id: str = "system"
    roles: list[str] = field(default_factory=lambda: ["System"])
    is_system: bool = True
    description: str | None = None

    def to_user_context(self) -> UserContext:
        """Convert to UserContext for permission checks.

        Returns:
            UserContext with is_system_user=True flag
        """
        return UserContext(
            id=self.id,
            email=f"{self.id}@system.internal",
            name=self.description or f"System ({self.id})",
            roles=self.roles,
            tenants=[],
        )


@asynccontextmanager
async def system_context(
    principal_id: str = "system",
    description: str | None = None,
    roles: list[str] | None = None,
) -> AsyncIterator[SystemPrincipal]:
    """Context manager for system-level operations.

    Creates a SystemPrincipal and sets it as the current context,
    allowing elevated operations that bypass normal permission checks.

    Args:
        principal_id: Identifier for this system operation (for audit)
        description: Optional description for logging
        roles: Additional roles beyond "System"

    Yields:
        SystemPrincipal for the current operation

    Example:
        async def process_webhook():
            async with system_context(principal_id="webhook") as ctx:
                # All operations logged as principal="webhook"
                await repo.save(session, data)

        async def run_migration():
            async with system_context(description="v1.2 migration") as ctx:
                # Bypass RLS, log as principal="system"
                await migrate_documents(ctx)
    """
    # Build role list
    all_roles = roles or ["System"]
    if "System" not in all_roles:
        all_roles = ["System", *all_roles]

    # Create the principal
    principal = SystemPrincipal(
        id=principal_id,
        roles=all_roles,
        is_system=True,
        description=description,
    )

    # Set the context variable
    token: Token[SystemPrincipal | None] = _system_context_var.set(principal)
    try:
        yield principal
    finally:
        # Reset to previous value (supports nesting)
        _system_context_var.reset(token)


def is_system_context() -> bool:
    """Check if we're currently inside a system context.

    Returns:
        True if inside system_context(), False otherwise
    """
    return _system_context_var.get() is not None


def get_current_system_context() -> SystemPrincipal | None:
    """Get the current system principal if inside a system context.

    Returns:
        Current SystemPrincipal or None if not in a system context
    """
    return _system_context_var.get()


__all__ = [
    "SystemPrincipal",
    "get_current_system_context",
    "is_system_context",
    "system_context",
]
