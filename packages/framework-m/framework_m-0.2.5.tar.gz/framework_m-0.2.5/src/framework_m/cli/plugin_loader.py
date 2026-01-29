"""Plugin loader for CLI extensibility.

This module provides the mechanism for 3rd-party apps to register
CLI commands via entry points. Apps can register either cyclopts Apps
(sub-command groups) or standalone functions as commands.

Entry Point Group: framework_m.cli_commands

Example pyproject.toml:
    [project.entry-points."framework_m.cli_commands"]
    studio = "my_app.cli:studio_app"      # cyclopts.App
    custom = "my_app.cli:custom_command"  # Function

Example:
    >>> app = cyclopts.App()
    >>> load_plugins(app)  # Discovers and registers all plugins
"""

from __future__ import annotations

import logging
from importlib.metadata import entry_points
from typing import TYPE_CHECKING

import cyclopts

if TYPE_CHECKING:
    from importlib.metadata import EntryPoint

logger = logging.getLogger(__name__)

# Entry point group for CLI command plugins
CLI_COMMANDS_GROUP = "framework_m.cli_commands"


def discover_plugins() -> list[EntryPoint]:
    """Discover all registered CLI command plugins.

    Scans the entry points registered under the 'framework_m.cli_commands'
    group. Each entry point should point to either:
    - A `cyclopts.App` instance (registered as sub-command group)
    - A callable function (registered as single command)

    Returns:
        List of entry points for CLI plugins.

    Example:
        >>> plugins = discover_plugins()
        >>> for ep in plugins:
        ...     print(f"Found plugin: {ep.name}")
    """
    eps = entry_points()

    # Python 3.12+ uses .select()
    return list(eps.select(group=CLI_COMMANDS_GROUP))


def register_plugins(app: cyclopts.App, plugins: list[EntryPoint]) -> None:
    """Register discovered plugins with the main cyclopts app.

    For each plugin entry point:
    - If it's a cyclopts.App: register as sub-command group
    - If it's a callable: register as standalone command

    Args:
        app: The main cyclopts application instance.
        plugins: List of entry points to register.

    Example:
        >>> app = cyclopts.App()
        >>> plugins = discover_plugins()
        >>> register_plugins(app, plugins)
    """
    for ep in plugins:
        try:
            plugin = ep.load()
        except Exception as e:
            logger.warning(
                f"Failed to load CLI plugin '{ep.name}': {e}",
                exc_info=True,
            )
            continue

        try:
            if isinstance(plugin, cyclopts.App):
                # Register cyclopts App as sub-command group
                app.command(plugin, name=ep.name)
                logger.debug(f"Registered cyclopts App plugin: {ep.name}")
            elif callable(plugin):
                # Register function as command
                app.command(plugin, name=ep.name)
                logger.debug(f"Registered function plugin: {ep.name}")
            else:
                logger.warning(
                    f"Plugin '{ep.name}' is not a cyclopts App or callable, skipping"
                )
        except Exception as e:
            logger.warning(
                f"Failed to register CLI plugin '{ep.name}': {e}",
                exc_info=True,
            )


def load_plugins(app: cyclopts.App) -> None:
    """Discover and register all CLI plugins.

    Convenience function that combines discovery and registration.
    Call this during app initialization to enable all plugins.

    Args:
        app: The main cyclopts application instance.

    Example:
        >>> app = cyclopts.App(name="m")
        >>> load_plugins(app)  # All plugins now registered
        >>> app()  # Run CLI
    """
    plugins = discover_plugins()

    if plugins:
        logger.info(f"Discovered {len(plugins)} CLI plugin(s)")
        register_plugins(app, plugins)
    else:
        logger.debug("No CLI plugins discovered")


__all__ = [
    "CLI_COMMANDS_GROUP",
    "discover_plugins",
    "load_plugins",
    "register_plugins",
]
