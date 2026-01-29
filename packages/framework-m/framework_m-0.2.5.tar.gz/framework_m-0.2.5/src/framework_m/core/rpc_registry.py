"""RPC Registry - Central registry for @rpc decorated functions.

This module provides a singleton registry that tracks all functions
decorated with @rpc for RPC endpoint discovery.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


class RpcRegistry:
    """Singleton registry for RPC-callable functions.

    The RpcRegistry stores all functions decorated with @rpc,
    allowing them to be discovered and called via the RPC endpoint.

    Functions are stored by their dotted path (e.g., `my_app.api.send_email`).

    Example:
        registry = RpcRegistry.get_instance()

        # Register a function
        registry.register("my_app.api.send_email", send_email_func)

        # Look up a function
        func = registry.get("my_app.api.send_email")
    """

    _instance: RpcRegistry | None = None
    _initialized: bool = False

    # Instance attributes
    _functions: dict[str, Callable[..., Any]]

    def __new__(cls) -> RpcRegistry:
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the registry (only once)."""
        if not RpcRegistry._initialized:
            self._functions = {}
            RpcRegistry._initialized = True

    @classmethod
    def get_instance(cls) -> RpcRegistry:
        """Get the singleton instance."""
        return cls()

    def register(self, path: str, func: Callable[..., Any]) -> None:
        """Register a function by its dotted path.

        Args:
            path: The dotted path (e.g., "my_app.api.send_email")
            func: The function to register
        """
        self._functions[path] = func

    def get(self, path: str) -> Callable[..., Any] | None:
        """Get a registered function by path.

        Args:
            path: The dotted path to look up

        Returns:
            The registered function, or None if not found
        """
        return self._functions.get(path)

    def list_functions(self) -> list[str]:
        """List all registered function paths.

        Returns:
            List of dotted paths
        """
        return list(self._functions.keys())

    def reset(self) -> None:
        """Clear all registered functions.

        Primarily used for testing.
        """
        self._functions.clear()


__all__ = ["RpcRegistry"]
