"""Tests for CLI main entry point.

This module tests the main CLI application including:
- Version flag
- Help documentation
- Command registration
- Plugin loading integration
"""

from __future__ import annotations

import subprocess
import sys

import framework_m


class TestVersionCommand:
    """Tests for --version flag."""

    def test_version_flag_outputs_version(self) -> None:
        """--version should output the framework version."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "--version"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert framework_m.__version__ in result.stdout

    def test_help_flag(self) -> None:
        """--help should show help text."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Framework M CLI" in result.stdout


class TestCoreCommands:
    """Tests for core CLI commands."""

    def test_info_command(self) -> None:
        """info command should show version and Python info."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "info"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert framework_m.__version__ in result.stdout
        assert "Python" in result.stdout

    def test_migrate_help(self) -> None:
        """migrate --help should work."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "migrate", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_worker_help(self) -> None:
        """worker --help should work."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "worker", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0


class TestJobCommands:
    """Tests for job management commands."""

    def test_job_list_command(self) -> None:
        """job list command should work."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "job", "list"],
            capture_output=True,
            text=True,
        )
        # Should work even with no jobs
        assert result.returncode == 0

    def test_job_help(self) -> None:
        """job --help should show available subcommands."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "job", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "list" in result.stdout.lower() or "run" in result.stdout.lower()
