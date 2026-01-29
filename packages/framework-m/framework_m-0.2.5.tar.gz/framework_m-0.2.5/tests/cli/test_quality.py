"""Tests for Quality CLI Commands - Comprehensive Integration Coverage."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestQualityImport:
    """Tests for quality module imports."""

    def test_import_test_command(self) -> None:
        """test_command should be importable."""
        from framework_m.cli.quality import test_command

        assert test_command is not None

    def test_import_lint_command(self) -> None:
        """lint_command should be importable."""
        from framework_m.cli.quality import lint_command

        assert lint_command is not None

    def test_import_format_command(self) -> None:
        """format_command should be importable."""
        from framework_m.cli.quality import format_command

        assert format_command is not None

    def test_import_typecheck_command(self) -> None:
        """typecheck_command should be importable."""
        from framework_m.cli.quality import typecheck_command

        assert typecheck_command is not None


class TestGetPythonPath:
    """Tests for get_pythonpath function."""

    def test_get_pythonpath_returns_string(self) -> None:
        """get_pythonpath should return a string."""
        from framework_m.cli.quality import get_pythonpath

        result = get_pythonpath()
        assert isinstance(result, str)

    def test_get_pythonpath_includes_cwd(self) -> None:
        """get_pythonpath should include current directory."""
        from framework_m.cli.quality import get_pythonpath

        result = get_pythonpath()
        cwd = str(Path.cwd())
        assert cwd in result

    def test_get_pythonpath_includes_src(self, tmp_path: Path) -> None:
        """get_pythonpath should include src if it exists."""
        from framework_m.cli.quality import get_pythonpath

        src_path = tmp_path / "src"
        src_path.mkdir()

        with patch("framework_m.cli.quality.Path.cwd", return_value=tmp_path):
            result = get_pythonpath()

        assert str(src_path) in result


class TestBuildCommands:
    """Tests for build command functions."""

    def test_build_pytest_command_basic(self) -> None:
        """build_pytest_command should build basic command."""
        from framework_m.cli.quality import build_pytest_command

        cmd = build_pytest_command()

        assert "pytest" in cmd[1] or "python" in cmd[0]
        assert "." in cmd

    def test_build_pytest_command_verbose(self) -> None:
        """build_pytest_command should add -v for verbose."""
        from framework_m.cli.quality import build_pytest_command

        cmd = build_pytest_command(verbose=True)

        assert "-v" in cmd

    def test_build_pytest_command_coverage(self) -> None:
        """build_pytest_command should add --cov for coverage."""
        from framework_m.cli.quality import build_pytest_command

        cmd = build_pytest_command(coverage=True)

        assert "--cov" in cmd

    def test_build_pytest_command_filter(self) -> None:
        """build_pytest_command should add -k for filter."""
        from framework_m.cli.quality import build_pytest_command

        cmd = build_pytest_command(filter_expr="test_foo")

        assert "-k" in cmd
        assert "test_foo" in cmd

    def test_build_pytest_command_extra_args(self) -> None:
        """build_pytest_command should add extra args."""
        from framework_m.cli.quality import build_pytest_command

        cmd = build_pytest_command(extra_args=("--tb=short", "-x"))

        assert "--tb=short" in cmd
        assert "-x" in cmd

    def test_build_ruff_check_command_basic(self) -> None:
        """build_ruff_check_command should build basic command."""
        from framework_m.cli.quality import build_ruff_check_command

        cmd = build_ruff_check_command()

        assert "ruff" in cmd[1] or "python" in cmd[0]
        assert "check" in cmd

    def test_build_ruff_check_command_fix(self) -> None:
        """build_ruff_check_command should add --fix."""
        from framework_m.cli.quality import build_ruff_check_command

        cmd = build_ruff_check_command(fix=True)

        assert "--fix" in cmd

    def test_build_ruff_check_command_no_fix(self) -> None:
        """build_ruff_check_command should not add --fix when False."""
        from framework_m.cli.quality import build_ruff_check_command

        cmd = build_ruff_check_command(fix=False)

        assert "--fix" not in cmd

    def test_build_ruff_check_command_extra_args(self) -> None:
        """build_ruff_check_command should add extra args."""
        from framework_m.cli.quality import build_ruff_check_command

        cmd = build_ruff_check_command(extra_args=("--config=ruff.toml",))

        assert "--config=ruff.toml" in cmd

    def test_build_ruff_format_command_basic(self) -> None:
        """build_ruff_format_command should build basic command."""
        from framework_m.cli.quality import build_ruff_format_command

        cmd = build_ruff_format_command()

        assert "ruff" in cmd[1] or "python" in cmd[0]
        assert "format" in cmd

    def test_build_ruff_format_command_check(self) -> None:
        """build_ruff_format_command should add --check."""
        from framework_m.cli.quality import build_ruff_format_command

        cmd = build_ruff_format_command(check=True)

        assert "--check" in cmd

    def test_build_ruff_format_command_extra_args(self) -> None:
        """build_ruff_format_command should add extra args."""
        from framework_m.cli.quality import build_ruff_format_command

        cmd = build_ruff_format_command(extra_args=("--diff",))

        assert "--diff" in cmd

    def test_build_mypy_command_basic(self) -> None:
        """build_mypy_command should build basic command."""
        from framework_m.cli.quality import build_mypy_command

        cmd = build_mypy_command()

        assert "mypy" in cmd[1] or "python" in cmd[0]

    def test_build_mypy_command_strict(self) -> None:
        """build_mypy_command should add --strict."""
        from framework_m.cli.quality import build_mypy_command

        cmd = build_mypy_command(strict=True)

        assert "--strict" in cmd

    def test_build_mypy_command_extra_args(self) -> None:
        """build_mypy_command should add extra args."""
        from framework_m.cli.quality import build_mypy_command

        cmd = build_mypy_command(extra_args=("--ignore-missing-imports",))

        assert "--ignore-missing-imports" in cmd


class TestTestCommand:
    """Tests for test_command function."""

    def test_test_command_is_callable(self) -> None:
        """test_command should be callable."""
        from framework_m.cli.quality import test_command

        assert callable(test_command)

    def test_test_command_runs_subprocess(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """test_command should run subprocess."""
        from framework_m.cli.quality import test_command

        mock_run = MagicMock()
        mock_run.return_value.returncode = 0

        with patch("subprocess.run", mock_run):
            with pytest.raises(SystemExit) as exc:
                test_command(path="tests/")
            assert exc.value.code == 0

        mock_run.assert_called_once()

    def test_test_command_handles_keyboard_interrupt(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """test_command should handle KeyboardInterrupt."""
        from framework_m.cli.quality import test_command

        with patch("subprocess.run", side_effect=KeyboardInterrupt()):
            with pytest.raises(SystemExit) as exc:
                test_command()
            assert exc.value.code == 130

        captured = capsys.readouterr()
        assert "interrupted" in captured.out.lower()


class TestLintCommand:
    """Tests for lint_command function."""

    def test_lint_command_is_callable(self) -> None:
        """lint_command should be callable."""
        from framework_m.cli.quality import lint_command

        assert callable(lint_command)

    def test_lint_command_runs_subprocess(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """lint_command should run subprocess."""
        from framework_m.cli.quality import lint_command

        mock_run = MagicMock()
        mock_run.return_value.returncode = 0

        with patch("subprocess.run", mock_run):
            with pytest.raises(SystemExit) as exc:
                lint_command()
            assert exc.value.code == 0

        mock_run.assert_called_once()

    def test_lint_command_handles_keyboard_interrupt(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """lint_command should handle KeyboardInterrupt."""
        from framework_m.cli.quality import lint_command

        with patch("subprocess.run", side_effect=KeyboardInterrupt()):
            with pytest.raises(SystemExit) as exc:
                lint_command()
            assert exc.value.code == 130

        captured = capsys.readouterr()
        assert "interrupted" in captured.out.lower()


class TestFormatCommand:
    """Tests for format_command function."""

    def test_format_command_is_callable(self) -> None:
        """format_command should be callable."""
        from framework_m.cli.quality import format_command

        assert callable(format_command)

    def test_format_command_runs_subprocess(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """format_command should run subprocess."""
        from framework_m.cli.quality import format_command

        mock_run = MagicMock()
        mock_run.return_value.returncode = 0

        with patch("subprocess.run", mock_run):
            with pytest.raises(SystemExit) as exc:
                format_command()
            assert exc.value.code == 0

        mock_run.assert_called_once()

    def test_format_command_handles_keyboard_interrupt(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """format_command should handle KeyboardInterrupt."""
        from framework_m.cli.quality import format_command

        with patch("subprocess.run", side_effect=KeyboardInterrupt()):
            with pytest.raises(SystemExit) as exc:
                format_command()
            assert exc.value.code == 130

        captured = capsys.readouterr()
        assert "interrupted" in captured.out.lower()


class TestTypecheckCommand:
    """Tests for typecheck_command function."""

    def test_typecheck_command_is_callable(self) -> None:
        """typecheck_command should be callable."""
        from framework_m.cli.quality import typecheck_command

        assert callable(typecheck_command)

    def test_typecheck_command_runs_subprocess(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """typecheck_command should run subprocess."""
        from framework_m.cli.quality import typecheck_command

        mock_run = MagicMock()
        mock_run.return_value.returncode = 0

        with patch("subprocess.run", mock_run):
            with pytest.raises(SystemExit) as exc:
                typecheck_command()
            assert exc.value.code == 0

        mock_run.assert_called_once()

    def test_typecheck_command_handles_keyboard_interrupt(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """typecheck_command should handle KeyboardInterrupt."""
        from framework_m.cli.quality import typecheck_command

        with patch("subprocess.run", side_effect=KeyboardInterrupt()):
            with pytest.raises(SystemExit) as exc:
                typecheck_command()
            assert exc.value.code == 130

        captured = capsys.readouterr()
        assert "interrupted" in captured.out.lower()


class TestCommandExecution:
    """Tests for command execution."""

    def test_test_help(self) -> None:
        """test --help should work."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "test", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "test" in result.stdout.lower() or "pytest" in result.stdout.lower()

    def test_lint_help(self) -> None:
        """lint --help should work."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "lint", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_format_help(self) -> None:
        """format --help should work."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "format", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_typecheck_help(self) -> None:
        """typecheck --help should work."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "typecheck", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0


class TestQualityExports:
    """Tests for quality module exports."""

    def test_all_exports(self) -> None:
        """quality module should export expected items."""
        from framework_m.cli import quality

        assert "test_command" in quality.__all__
        assert "lint_command" in quality.__all__
        assert "format_command" in quality.__all__
        assert "typecheck_command" in quality.__all__
