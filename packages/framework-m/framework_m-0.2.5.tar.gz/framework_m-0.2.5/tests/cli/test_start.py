"""Tests for Start CLI Command - Comprehensive Integration Coverage."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestStartImport:
    """Tests for start module imports."""

    def test_import_start_command(self) -> None:
        """start_command should be importable."""
        from framework_m.cli.start import start_command

        assert start_command is not None

    def test_import_find_app(self) -> None:
        """find_app should be importable."""
        from framework_m.cli.start import find_app

        assert find_app is not None

    def test_import_build_uvicorn_command(self) -> None:
        """build_uvicorn_command should be importable."""
        from framework_m.cli.start import build_uvicorn_command

        assert build_uvicorn_command is not None


class TestConstants:
    """Tests for start module constants."""

    def test_default_app_path(self) -> None:
        """DEFAULT_APP_PATH should be set."""
        from framework_m.cli.start import DEFAULT_APP_PATH

        assert DEFAULT_APP_PATH == "app:app"


class TestFindApp:
    """Tests for find_app function."""

    def test_find_app_explicit(self) -> None:
        """find_app should return explicit app path."""
        from framework_m.cli.start import find_app

        result = find_app("myapp.main:app")
        assert result == "myapp.main:app"

    def test_find_app_with_app_py(self, tmp_path: Path) -> None:
        """find_app should find app.py."""
        from framework_m.cli.start import find_app

        (tmp_path / "app.py").write_text("app = None")

        with patch("framework_m.cli.start.Path.cwd", return_value=tmp_path):
            result = find_app()

        assert result == "app:app"

    def test_find_app_with_app_package(self, tmp_path: Path) -> None:
        """find_app should find app/__init__.py."""
        from framework_m.cli.start import find_app

        (tmp_path / "app").mkdir()
        (tmp_path / "app" / "__init__.py").write_text("app = None")

        with patch("framework_m.cli.start.Path.cwd", return_value=tmp_path):
            result = find_app()

        assert result == "app:app"

    def test_find_app_with_src_app(self, tmp_path: Path) -> None:
        """find_app should find src/app."""
        from framework_m.cli.start import find_app

        (tmp_path / "src" / "app").mkdir(parents=True)
        (tmp_path / "src" / "app" / "__init__.py").write_text("app = None")

        with patch("framework_m.cli.start.Path.cwd", return_value=tmp_path):
            result = find_app()

        assert result == "src.app:app"

    def test_find_app_with_main_py(self, tmp_path: Path) -> None:
        """find_app should find main.py."""
        from framework_m.cli.start import find_app

        (tmp_path / "main.py").write_text("app = None")

        with patch("framework_m.cli.start.Path.cwd", return_value=tmp_path):
            result = find_app()

        assert result == "main:app"

    def test_find_app_default_fallback(self, tmp_path: Path) -> None:
        """find_app should return default when nothing found."""
        from framework_m.cli.start import find_app

        with patch("framework_m.cli.start.Path.cwd", return_value=tmp_path):
            result = find_app()

        assert result == "app:app"


class TestGetPythonPath:
    """Tests for get_pythonpath function."""

    def test_get_pythonpath_returns_string(self) -> None:
        """get_pythonpath should return a string."""
        from framework_m.cli.start import get_pythonpath

        result = get_pythonpath()
        assert isinstance(result, str)

    def test_get_pythonpath_includes_cwd(self) -> None:
        """get_pythonpath should include current directory."""
        from framework_m.cli.start import get_pythonpath

        result = get_pythonpath()
        cwd = str(Path.cwd())
        assert cwd in result

    def test_get_pythonpath_includes_src(self, tmp_path: Path) -> None:
        """get_pythonpath should include src if it exists."""
        from framework_m.cli.start import get_pythonpath

        src_path = tmp_path / "src"
        src_path.mkdir()

        with patch("framework_m.cli.start.Path.cwd", return_value=tmp_path):
            result = get_pythonpath()

        assert str(src_path) in result

    def test_get_pythonpath_preserves_existing(self, tmp_path: Path) -> None:
        """get_pythonpath should preserve existing PYTHONPATH."""
        from framework_m.cli.start import get_pythonpath

        with (
            patch("framework_m.cli.start.Path.cwd", return_value=tmp_path),
            patch.dict(os.environ, {"PYTHONPATH": "/existing/path"}),
        ):
            result = get_pythonpath()

        assert "/existing/path" in result


class TestBuildUvicornCommand:
    """Tests for build_uvicorn_command function."""

    def test_build_uvicorn_command_basic(self) -> None:
        """build_uvicorn_command should build basic command."""
        from framework_m.cli.start import build_uvicorn_command

        cmd = build_uvicorn_command(app="app:app")

        assert "uvicorn" in cmd[1] or "python" in cmd[0]
        assert "app:app" in cmd
        assert "--host" in cmd
        assert "--port" in cmd

    def test_build_uvicorn_command_custom_host_port(self) -> None:
        """build_uvicorn_command should use custom host and port."""
        from framework_m.cli.start import build_uvicorn_command

        cmd = build_uvicorn_command(app="app:app", host="0.0.0.0", port=9000)

        idx_host = cmd.index("--host")
        idx_port = cmd.index("--port")
        assert cmd[idx_host + 1] == "0.0.0.0"
        assert cmd[idx_port + 1] == "9000"

    def test_build_uvicorn_command_reload(self) -> None:
        """build_uvicorn_command should add --reload."""
        from framework_m.cli.start import build_uvicorn_command

        cmd = build_uvicorn_command(app="app:app", reload=True)

        assert "--reload" in cmd

    def test_build_uvicorn_command_workers(self) -> None:
        """build_uvicorn_command should add --workers."""
        from framework_m.cli.start import build_uvicorn_command

        cmd = build_uvicorn_command(app="app:app", workers=4)

        assert "--workers" in cmd
        idx = cmd.index("--workers")
        assert cmd[idx + 1] == "4"

    def test_build_uvicorn_command_no_workers_if_1(self) -> None:
        """build_uvicorn_command should not add --workers if 1."""
        from framework_m.cli.start import build_uvicorn_command

        cmd = build_uvicorn_command(app="app:app", workers=1)

        assert "--workers" not in cmd

    def test_build_uvicorn_command_log_level(self) -> None:
        """build_uvicorn_command should add --log-level."""
        from framework_m.cli.start import build_uvicorn_command

        cmd = build_uvicorn_command(app="app:app", log_level="debug")

        assert "--log-level" in cmd
        idx = cmd.index("--log-level")
        assert cmd[idx + 1] == "debug"

    def test_build_uvicorn_command_extra_args(self) -> None:
        """build_uvicorn_command should add extra args."""
        from framework_m.cli.start import build_uvicorn_command

        cmd = build_uvicorn_command(app="app:app", extra_args=("--ssl-keyfile", "key"))

        assert "--ssl-keyfile" in cmd
        assert "key" in cmd


class TestStartCommand:
    """Tests for start_command function."""

    def test_start_command_is_callable(self) -> None:
        """start_command should be callable."""
        from framework_m.cli.start import start_command

        assert callable(start_command)

    def test_start_command_runs_subprocess(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """start_command should run subprocess."""
        from framework_m.cli.start import start_command

        mock_run = MagicMock()

        with patch("subprocess.run", mock_run):
            start_command(app="myapp:app")

        mock_run.assert_called_once()
        captured = capsys.readouterr()
        assert "Starting server" in captured.out

    def test_start_command_handles_error(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """start_command should handle subprocess error."""
        from framework_m.cli.start import start_command

        with patch(
            "subprocess.run",
            side_effect=subprocess.CalledProcessError(1, ["uvicorn"]),
        ):
            with pytest.raises(SystemExit) as exc:
                start_command(app="myapp:app")
            assert exc.value.code == 1

    def test_start_command_handles_keyboard_interrupt(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """start_command should handle KeyboardInterrupt."""
        from framework_m.cli.start import start_command

        with patch("subprocess.run", side_effect=KeyboardInterrupt()):
            start_command(app="myapp:app")

        captured = capsys.readouterr()
        assert "stopped" in captured.out.lower()

    def test_start_command_prints_workers(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """start_command should print worker count."""
        from framework_m.cli.start import start_command

        mock_run = MagicMock()

        with patch("subprocess.run", mock_run):
            start_command(app="myapp:app", workers=4)

        captured = capsys.readouterr()
        assert "Workers: 4" in captured.out


class TestStartExecution:
    """Tests for start command execution."""

    def test_start_help(self) -> None:
        """start --help should work."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "start", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "start" in result.stdout.lower()


class TestStartExports:
    """Tests for start module exports."""

    def test_all_exports(self) -> None:
        """start module should export expected items."""
        from framework_m.cli import start

        assert "start_command" in start.__all__
        assert "find_app" in start.__all__
        assert "build_uvicorn_command" in start.__all__
        assert "get_pythonpath" in start.__all__
