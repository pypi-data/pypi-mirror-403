"""Tests for Utility CLI Commands - Comprehensive Coverage."""

from __future__ import annotations

import subprocess
import sys

import pytest


class TestUtilityImport:
    """Tests for utility module imports."""

    def test_import_console_command(self) -> None:
        """console_command should be importable."""
        from framework_m.cli.utility import console_command

        assert console_command is not None

    def test_import_info_command(self) -> None:
        """info_command should be importable."""
        from framework_m.cli.utility import info_command

        assert info_command is not None

    def test_import_routes_command(self) -> None:
        """routes_command should be importable."""
        from framework_m.cli.utility import routes_command

        assert routes_command is not None


class TestVersionFunctions:
    """Tests for version helper functions."""

    def test_get_python_version(self) -> None:
        """get_python_version should return version string."""
        from framework_m.cli.utility import get_python_version

        result = get_python_version()
        assert isinstance(result, str)
        assert "." in result

    def test_get_framework_version(self) -> None:
        """get_framework_version should return version string."""
        from framework_m.cli.utility import get_framework_version

        result = get_framework_version()
        assert isinstance(result, str)


class TestCheckIPython:
    """Tests for check_ipython_installed function."""

    def test_check_ipython_installed_returns_bool(self) -> None:
        """check_ipython_installed should return bool."""
        from framework_m.cli.utility import check_ipython_installed

        result = check_ipython_installed()
        assert isinstance(result, bool)


class TestGetPythonPath:
    """Tests for get_pythonpath function."""

    def test_get_pythonpath_returns_string(self) -> None:
        """get_pythonpath should return a string."""
        from framework_m.cli.utility import get_pythonpath

        result = get_pythonpath()
        assert isinstance(result, str)


class TestInfoCommand:
    """Tests for info_command function."""

    def test_info_command_is_callable(self) -> None:
        """info_command should be callable."""
        from framework_m.cli.utility import info_command

        assert callable(info_command)

    def test_info_command_basic(self, capsys: pytest.CaptureFixture[str]) -> None:
        """info_command should display system info."""
        from framework_m.cli.utility import info_command

        info_command(verbose=False)

        captured = capsys.readouterr()
        assert "Framework M" in captured.out
        assert "Python" in captured.out

    def test_info_command_verbose(self, capsys: pytest.CaptureFixture[str]) -> None:
        """info_command with verbose should show more info."""
        from framework_m.cli.utility import info_command

        info_command(verbose=True)

        captured = capsys.readouterr()
        assert "Platform" in captured.out
        assert "Services" in captured.out


class TestConsoleCommand:
    """Tests for console_command function."""

    def test_console_command_is_callable(self) -> None:
        """console_command should be callable."""
        from framework_m.cli.utility import console_command

        assert callable(console_command)


class TestRoutesCommand:
    """Tests for routes_command function."""

    def test_routes_command_is_callable(self) -> None:
        """routes_command should be callable."""
        from framework_m.cli.utility import routes_command

        assert callable(routes_command)

    def test_routes_command_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """routes_command should print route info."""
        from framework_m.cli.utility import routes_command

        routes_command(app_path=None)

        captured = capsys.readouterr()
        assert "swagger" in captured.out.lower() or "routes" in captured.out.lower()


class TestCommandExecution:
    """Tests for command execution."""

    def test_info_help(self) -> None:
        """info --help should work."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "info", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_console_help(self) -> None:
        """console --help should work."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "console", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_routes_help(self) -> None:
        """routes --help should work."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "routes", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0


class TestUtilityExports:
    """Tests for utility module exports."""

    def test_all_exports(self) -> None:
        """utility module should export expected items."""
        from framework_m.cli import utility

        assert "console_command" in utility.__all__
        assert "info_command" in utility.__all__
        assert "routes_command" in utility.__all__
