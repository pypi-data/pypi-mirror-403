"""Middleware Registry - Discovery and registration system for ASGI middleware.

This module provides a registry for apps to register ASGI middleware that will
be automatically discovered and applied to the Litestar application.

Features:
- Singleton registry for middleware registration
- Priority-based ordering (lower priority = runs first/outer layer)
- Support for middleware kwargs
- Integration with Litestar's DefineMiddleware

Example:
    from framework_m.adapters.web.middleware_registry import MiddlewareRegistry

    # In your app's startup
    registry = MiddlewareRegistry()
    registry.register(
        RateLimitMiddleware,
        name="rate_limit",
        priority=50,  # Runs early (outer layer)
        kwargs={"requests_per_minute": 100},
    )

    # In create_app(), middlewares are auto-discovered
    stack = create_middleware_stack()
    app = Litestar(middleware=stack)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from litestar.middleware.base import DefineMiddleware

if TYPE_CHECKING:
    pass


@dataclass
class MiddlewareConfig:
    """Configuration for a registered middleware.

    Attributes:
        middleware_class: The ASGI middleware class
        name: Unique identifier for the middleware
        priority: Ordering priority (lower = runs first, default 100)
        kwargs: Keyword arguments to pass to the middleware constructor
        enabled: Whether the middleware is enabled (default True)

    Priority Guidelines:
        - 0-50: Security/early processing (rate limiting, CORS)
        - 50-100: Authentication/identity
        - 100-150: General purpose
        - 150-200: Compression/transformation
        - 200+: Observability/tracing (runs last, closest to handler)
    """

    middleware_class: type[Any]
    name: str
    priority: int = 100
    kwargs: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True


class MiddlewareRegistry:
    """Singleton registry for ASGI middleware.

    Apps can register middleware to be automatically discovered and applied
    to the Litestar application. Middlewares are ordered by priority.

    Example:
        registry = MiddlewareRegistry()
        registry.register(MyMiddleware, name="my_middleware", priority=50)

        # Later, get all registered middlewares
        for config in registry.list_middlewares():
            print(f"{config.name}: priority {config.priority}")
    """

    _instance: MiddlewareRegistry | None = None
    _initialized: bool = False

    # Instance attributes
    _middlewares: dict[str, MiddlewareConfig]

    def __new__(cls) -> MiddlewareRegistry:
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the registry (only once)."""
        if not MiddlewareRegistry._initialized:
            self._middlewares = {}
            MiddlewareRegistry._initialized = True

    @classmethod
    def get_instance(cls) -> MiddlewareRegistry:
        """Get the singleton instance."""
        return cls()

    def register(
        self,
        middleware_class: type[Any],
        name: str,
        priority: int = 100,
        kwargs: dict[str, Any] | None = None,
        enabled: bool = True,
    ) -> None:
        """Register a middleware for auto-discovery.

        Args:
            middleware_class: The ASGI middleware class
            name: Unique identifier for the middleware
            priority: Ordering priority (lower = runs first)
            kwargs: Keyword arguments to pass to middleware constructor
            enabled: Whether the middleware is enabled

        Raises:
            ValueError: If middleware with same name is already registered
        """
        if name in self._middlewares:
            raise ValueError(f"Middleware '{name}' is already registered")

        config = MiddlewareConfig(
            middleware_class=middleware_class,
            name=name,
            priority=priority,
            kwargs=kwargs or {},
            enabled=enabled,
        )
        self._middlewares[name] = config

    def unregister(self, name: str) -> None:
        """Unregister a middleware by name.

        Args:
            name: The middleware name to remove

        Raises:
            KeyError: If middleware is not registered
        """
        if name not in self._middlewares:
            raise KeyError(f"Middleware '{name}' is not registered")
        del self._middlewares[name]

    def get(self, name: str) -> MiddlewareConfig | None:
        """Get a middleware config by name.

        Args:
            name: The middleware name

        Returns:
            MiddlewareConfig if found, None otherwise
        """
        return self._middlewares.get(name)

    def list_middlewares(self, enabled_only: bool = True) -> list[MiddlewareConfig]:
        """List all registered middlewares, ordered by priority.

        Args:
            enabled_only: If True, only return enabled middlewares

        Returns:
            List of MiddlewareConfig ordered by priority (lowest first)
        """
        configs = list(self._middlewares.values())
        if enabled_only:
            configs = [c for c in configs if c.enabled]
        return sorted(configs, key=lambda c: c.priority)

    def clear(self) -> None:
        """Clear all registered middlewares.

        Primarily used for testing.
        """
        self._middlewares.clear()


def create_middleware_stack(
    registry: MiddlewareRegistry | None = None,
) -> list[DefineMiddleware]:
    """Create a Litestar middleware stack from registered middlewares.

    This function collects all registered middlewares, orders them by priority,
    and creates DefineMiddleware instances for use with Litestar.

    Args:
        registry: Optional registry instance (defaults to singleton)

    Returns:
        List of DefineMiddleware instances ordered by priority
    """
    if registry is None:
        registry = MiddlewareRegistry.get_instance()

    stack: list[DefineMiddleware] = []
    for config in registry.list_middlewares(enabled_only=True):
        middleware = DefineMiddleware(config.middleware_class, **config.kwargs)
        stack.append(middleware)

    return stack


__all__ = [
    "MiddlewareConfig",
    "MiddlewareRegistry",
    "create_middleware_stack",
]
