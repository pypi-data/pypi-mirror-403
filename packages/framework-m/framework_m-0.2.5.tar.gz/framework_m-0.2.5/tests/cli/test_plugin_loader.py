"""Tests for CLI plugin loader.

This module tests the entry point discovery and registration
mechanism for extending the CLI with 3rd-party commands.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import cyclopts
import pytest


class TestDiscoverPlugins:
    """Tests for discover_plugins() function."""

    def test_discover_plugins_returns_list(self) -> None:
        """discover_plugins should return a list of entry points."""
        from framework_m.cli.plugin_loader import discover_plugins

        # With no plugins installed, should return empty list
        result = discover_plugins()
        assert isinstance(result, list)

    def test_discover_plugins_finds_registered_entry_points(self) -> None:
        """discover_plugins should find entry points in framework_m.cli_commands group."""
        from framework_m.cli.plugin_loader import discover_plugins

        # Mock entry_points to return a fake plugin
        mock_ep = MagicMock()
        mock_ep.name = "test_command"
        mock_ep.load.return_value = lambda: None

        with patch("framework_m.cli.plugin_loader.entry_points") as mock_entry_points:
            mock_entry_points.return_value.select.return_value = [mock_ep]
            result = discover_plugins()

        assert len(result) == 1
        assert result[0].name == "test_command"


class TestRegisterPlugins:
    """Tests for register_plugins() function."""

    @pytest.fixture
    def test_app(self) -> cyclopts.App:
        """Create a test cyclopts app."""
        return cyclopts.App()

    def test_register_plugins_with_empty_list(self, test_app: cyclopts.App) -> None:
        """register_plugins should handle empty plugin list gracefully."""
        from framework_m.cli.plugin_loader import register_plugins

        # Should not raise
        register_plugins(test_app, [])

    def test_register_cyclopts_app_plugin(self, test_app: cyclopts.App) -> None:
        """register_plugins should register cyclopts apps as sub-commands."""
        from framework_m.cli.plugin_loader import register_plugins

        # Create a mock entry point that returns a cyclopts App
        plugin_app = cyclopts.App(help="Plugin app")

        @plugin_app.command
        def plugin_cmd() -> None:
            """Plugin command."""
            pass

        mock_ep = MagicMock()
        mock_ep.name = "plugin"
        mock_ep.load.return_value = plugin_app

        register_plugins(test_app, [mock_ep])

        # Verify the plugin was registered
        assert mock_ep.load.called

    def test_register_function_plugin(self, test_app: cyclopts.App) -> None:
        """register_plugins should register functions as commands."""
        from framework_m.cli.plugin_loader import register_plugins

        def my_custom_command() -> None:
            """Custom command from plugin."""
            pass

        mock_ep = MagicMock()
        mock_ep.name = "custom_cmd"
        mock_ep.load.return_value = my_custom_command

        register_plugins(test_app, [mock_ep])

        # Verify load was called
        assert mock_ep.load.called

    def test_register_plugins_handles_load_errors(self, test_app: cyclopts.App) -> None:
        """register_plugins should gracefully handle plugins that fail to load."""
        from framework_m.cli.plugin_loader import register_plugins

        mock_ep = MagicMock()
        mock_ep.name = "broken_plugin"
        mock_ep.load.side_effect = ImportError("Module not found")

        # Should not raise, just log warning
        register_plugins(test_app, [mock_ep])


class TestLoadPlugins:
    """Tests for load_plugins() convenience function."""

    def test_load_plugins_discovers_and_registers(self) -> None:
        """load_plugins should discover and register all plugins."""
        from framework_m.cli.plugin_loader import load_plugins

        app = cyclopts.App()

        with patch("framework_m.cli.plugin_loader.discover_plugins") as mock_discover:
            mock_discover.return_value = []
            load_plugins(app)

        mock_discover.assert_called_once()


class TestPluginEntryPointGroup:
    """Tests verifying the correct entry point group is used."""

    def test_uses_framework_m_cli_commands_group(self) -> None:
        """Plugin loader should use 'framework_m.cli_commands' entry point group."""
        from framework_m.cli.plugin_loader import CLI_COMMANDS_GROUP

        assert CLI_COMMANDS_GROUP == "framework_m.cli_commands"
