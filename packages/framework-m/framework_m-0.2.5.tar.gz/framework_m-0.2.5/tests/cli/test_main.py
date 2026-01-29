"""Tests for Main CLI Module - Comprehensive Coverage."""

from __future__ import annotations

import subprocess
import sys


class TestMainImport:
    """Tests for main module imports."""

    def test_import_app(self) -> None:
        """app should be importable."""
        from framework_m.cli.main import app

        assert app is not None

    def test_import_cyclopts_app(self) -> None:
        """app should be a cyclopts App."""
        import cyclopts

        from framework_m.cli.main import app

        assert isinstance(app, cyclopts.App)


class TestAppConfiguration:
    """Tests for app configuration."""

    def test_app_has_name(self) -> None:
        """app should have name 'm'."""
        from framework_m.cli.main import app

        assert "m" in app.name

    def test_app_has_help(self) -> None:
        """app should have help text."""
        from framework_m.cli.main import app

        assert app.help is not None


class TestWorkerCommand:
    """Tests for inline worker command."""

    def test_worker_command_exists(self) -> None:
        """worker command should exist."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "worker", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0


class TestDefaultCommand:
    """Tests for default command."""

    def test_default_shows_help(self) -> None:
        """Running m without command should show help."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main"],
            capture_output=True,
            text=True,
        )
        # Either succeeds or shows help
        assert "Usage" in result.stdout or result.returncode == 0


class TestMainExecution:
    """Tests for main module execution."""

    def test_version(self) -> None:
        """--version should show version."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "--version"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_help(self) -> None:
        """--help should show help."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Framework M" in result.stdout


class TestRegisteredCommands:
    """Tests for registered commands."""

    def test_migrate_registered(self) -> None:
        """migrate command should be registered."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "migrate", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_job_registered(self) -> None:
        """job command should be registered."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "job", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_start_registered(self) -> None:
        """start command should be registered."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "start", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_studio_registered(self) -> None:
        """studio command should be registered."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "studio", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_new_doctype_registered(self) -> None:
        """new:doctype command should be registered."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "new:doctype", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_new_app_registered(self) -> None:
        """new:app command should be registered."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "new:app", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_test_registered(self) -> None:
        """test command should be registered."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "test", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_lint_registered(self) -> None:
        """lint command should be registered."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "lint", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_format_registered(self) -> None:
        """format command should be registered."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "format", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_typecheck_registered(self) -> None:
        """typecheck command should be registered."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "typecheck", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_config_show_registered(self) -> None:
        """config:show command should be registered."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "config:show", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_config_set_registered(self) -> None:
        """config:set command should be registered."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "config:set", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_console_registered(self) -> None:
        """console command should be registered."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "console", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_info_registered(self) -> None:
        """info command should be registered."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "info", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_routes_registered(self) -> None:
        """routes command should be registered."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "routes", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_build_registered(self) -> None:
        """build command should be registered."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "build", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_build_docker_registered(self) -> None:
        """build:docker command should be registered."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "build:docker", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
