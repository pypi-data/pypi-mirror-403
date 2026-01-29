"""Configuration Management CLI Commands.

This module provides CLI commands for managing Framework M configuration:
- m config:show: Display current configuration
- m config:set <key> <value>: Update configuration value

Usage:
    m config:show                 # Show all config
    m config:set framework.name myapp
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

import cyclopts

# Default config file name
CONFIG_FILE_NAME = "framework_config.toml"

# Default config structure
DEFAULT_CONFIG = {
    "framework": {
        "name": "my_app",
        "version": "0.1.0",
    },
    "apps": {
        "installed": [],
    },
}


def find_config_file() -> Path:
    """Find the config file in current directory or parents.

    Returns:
        Path to config file (may not exist)
    """
    for path in [Path.cwd(), *Path.cwd().parents]:
        config_path = path / CONFIG_FILE_NAME
        if config_path.exists():
            return config_path

    # Default to cwd if not found
    return Path.cwd() / CONFIG_FILE_NAME


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load configuration from TOML file.

    Args:
        config_path: Path to config file (auto-detect if None)

    Returns:
        Configuration dict
    """
    if config_path is None:
        config_path = find_config_file()

    if not config_path.exists():
        return {}

    try:
        import tomllib

        return tomllib.loads(config_path.read_text())
    except Exception:
        return {}


def save_config(config_path: Path, config: dict[str, Any]) -> None:
    """Save configuration to TOML file.

    Args:
        config_path: Path to config file
        config: Configuration dict to save
    """
    # Simple TOML writing (no external dependencies)
    lines: list[str] = []
    for section, values in config.items():
        lines.append(f"[{section}]")
        if isinstance(values, dict):
            for key, value in values.items():
                if isinstance(value, str):
                    lines.append(f'{key} = "{value}"')
                elif isinstance(value, list):
                    items = ", ".join(f'"{v}"' for v in value)
                    lines.append(f"{key} = [{items}]")
                elif isinstance(value, bool):
                    lines.append(f"{key} = {str(value).lower()}")
                elif isinstance(value, (int, float)):
                    lines.append(f"{key} = {value}")
                else:
                    lines.append(f'{key} = "{value}"')
        lines.append("")

    config_path.write_text("\n".join(lines))


def get_nested_value(config: dict[str, Any], key: str) -> Any | None:
    """Get a nested value from config using dot notation.

    Args:
        config: Configuration dict
        key: Dot-separated key (e.g., "framework.name")

    Returns:
        Value or None if not found
    """
    parts = key.split(".")
    current = config

    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None

    return current


def set_nested_value(config: dict[str, Any], key: str, value: str) -> None:
    """Set a nested value in config using dot notation.

    Args:
        config: Configuration dict to modify
        key: Dot-separated key (e.g., "framework.name")
        value: Value to set
    """
    parts = key.split(".")
    current = config

    # Navigate/create nested dicts
    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]

    # Set the final value
    current[parts[-1]] = value


def format_config(config: dict[str, Any], indent: int = 0) -> str:
    """Format config dict for display.

    Args:
        config: Configuration dict
        indent: Indentation level

    Returns:
        Formatted string
    """
    lines = []
    prefix = "  " * indent

    for key, value in config.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}[{key}]")
            lines.append(format_config(value, indent + 1))
        elif isinstance(value, list):
            items = ", ".join(str(v) for v in value)
            lines.append(f"{prefix}{key} = [{items}]")
        else:
            lines.append(f"{prefix}{key} = {value}")

    return "\n".join(lines)


# =============================================================================
# CLI Commands
# =============================================================================


def config_show_command(
    key: Annotated[
        str | None,
        cyclopts.Parameter(help="Specific key to show (e.g., framework.name)"),
    ] = None,
    config_file: Annotated[
        Path | None,
        cyclopts.Parameter(name="--config", help="Path to config file"),
    ] = None,
) -> None:
    """Display current configuration.

    Shows the current Framework M configuration from framework_config.toml.

    Examples:
        m config:show                    # Show all config
        m config:show framework.name     # Show specific key
    """
    config_path = config_file or find_config_file()
    config = load_config(config_path)

    if not config:
        print(f"No config found at: {config_path}")
        print()
        print("Create a config file with default values:")
        print("  m config:set framework.name myapp")
        return

    print(f"Config file: {config_path}")
    print()

    if key:
        value = get_nested_value(config, key)
        if value is not None:
            print(f"{key} = {value}")
        else:
            print(f"Key not found: {key}")
            raise SystemExit(1)
    else:
        print(format_config(config))


def config_set_command(
    key: Annotated[str, cyclopts.Parameter(help="Key to set (e.g., framework.name)")],
    value: Annotated[str, cyclopts.Parameter(help="Value to set")],
    config_file: Annotated[
        Path | None,
        cyclopts.Parameter(name="--config", help="Path to config file"),
    ] = None,
) -> None:
    """Set a configuration value.

    Updates a value in framework_config.toml, creating the file if needed.

    Examples:
        m config:set framework.name myapp
        m config:set apps.installed "myapp,otherapp"
    """
    config_path = config_file or find_config_file()
    config = load_config(config_path) or DEFAULT_CONFIG.copy()

    # Parse value (handle lists)
    if "," in value:
        parsed_value: Any = [v.strip() for v in value.split(",")]
    else:
        parsed_value = value

    old_value = get_nested_value(config, key)
    set_nested_value(config, key, parsed_value)

    save_config(config_path, config)

    print(f"Config file: {config_path}")
    print()
    if old_value is not None:
        print(f"  {key}: {old_value} -> {parsed_value}")
    else:
        print(f"  {key} = {parsed_value}")
    print()
    print("✓ Configuration updated")


__all__ = [
    "CONFIG_FILE_NAME",
    "DEFAULT_CONFIG",
    "config_set_command",
    "config_show_command",
    "find_config_file",
    "format_config",
    "get_nested_value",
    "load_config",
    "save_config",
    "set_nested_value",
]
