"""Tests for Studio CLI Commands - Comprehensive Coverage."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestStudioImport:
    """Tests for studio module imports."""

    def test_import_studio_command(self) -> None:
        """studio_command should be importable."""
        from framework_m.cli.studio import studio_command

        assert studio_command is not None

    def test_import_build_studio_command(self) -> None:
        """build_studio_command should be importable."""
        from framework_m.cli.studio import build_studio_command

        assert build_studio_command is not None

    def test_import_get_studio_app(self) -> None:
        """get_studio_app should be importable."""
        from framework_m.cli.studio import get_studio_app

        assert get_studio_app is not None


class TestConstants:
    """Tests for studio constants."""

    def test_default_studio_port(self) -> None:
        """DEFAULT_STUDIO_PORT should be 9000."""
        from framework_m.cli.studio import DEFAULT_STUDIO_PORT

        assert DEFAULT_STUDIO_PORT == 9000

    def test_default_studio_app(self) -> None:
        """DEFAULT_STUDIO_APP should be set."""
        from framework_m.cli.studio import DEFAULT_STUDIO_APP

        assert "framework_m" in DEFAULT_STUDIO_APP
        assert "app" in DEFAULT_STUDIO_APP


class TestGetStudioApp:
    """Tests for get_studio_app function."""

    def test_get_studio_app_returns_string(self) -> None:
        """get_studio_app should return a string."""
        from framework_m.cli.studio import get_studio_app

        result = get_studio_app()
        assert isinstance(result, str)
        assert ":" in result  # Should be module:attribute format


class TestGetPythonPath:
    """Tests for get_pythonpath function."""

    def test_get_pythonpath_returns_string(self) -> None:
        """get_pythonpath should return a string."""
        from framework_m.cli.studio import get_pythonpath

        result = get_pythonpath()
        assert isinstance(result, str)

    def test_get_pythonpath_includes_cwd(self) -> None:
        """get_pythonpath should include current directory."""
        from framework_m.cli.studio import get_pythonpath

        result = get_pythonpath()
        cwd = str(Path.cwd())
        assert cwd in result

    def test_get_pythonpath_includes_src(self, tmp_path: Path) -> None:
        """get_pythonpath should include src/ if it exists."""
        from framework_m.cli.studio import get_pythonpath

        src_path = tmp_path / "src"
        src_path.mkdir()

        with patch("framework_m.cli.studio.Path.cwd", return_value=tmp_path):
            result = get_pythonpath()

        assert str(src_path) in result


class TestBuildStudioCommand:
    """Tests for build_studio_command function."""

    def test_build_studio_command_basic(self) -> None:
        """build_studio_command should build basic command."""
        from framework_m.cli.studio import build_studio_command

        cmd = build_studio_command()

        assert "python" in cmd[0]
        assert "-m" in cmd
        assert "uvicorn" in cmd
        assert "--host" in cmd
        assert "--port" in cmd

    def test_build_studio_command_custom_host(self) -> None:
        """build_studio_command should use custom host."""
        from framework_m.cli.studio import build_studio_command

        cmd = build_studio_command(host="0.0.0.0")

        idx = cmd.index("--host")
        assert cmd[idx + 1] == "0.0.0.0"

    def test_build_studio_command_custom_port(self) -> None:
        """build_studio_command should use custom port."""
        from framework_m.cli.studio import build_studio_command

        cmd = build_studio_command(port=9001)

        idx = cmd.index("--port")
        assert cmd[idx + 1] == "9001"

    def test_build_studio_command_reload(self) -> None:
        """build_studio_command should add reload flag."""
        from framework_m.cli.studio import build_studio_command

        cmd = build_studio_command(reload=True)

        assert "--reload" in cmd

    def test_build_studio_command_no_reload(self) -> None:
        """build_studio_command should not add reload by default."""
        from framework_m.cli.studio import build_studio_command

        cmd = build_studio_command(reload=False)

        assert "--reload" not in cmd

    def test_build_studio_command_log_level(self) -> None:
        """build_studio_command should add log level."""
        from framework_m.cli.studio import build_studio_command

        cmd = build_studio_command(log_level="debug")

        idx = cmd.index("--log-level")
        assert cmd[idx + 1] == "debug"


class TestStudioCommand:
    """Tests for studio_command function."""

    def test_studio_command_is_callable(self) -> None:
        """studio_command should be callable."""
        from framework_m.cli.studio import studio_command

        assert callable(studio_command)

    def test_studio_command_prints_banner(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """studio_command should print startup banner."""
        from framework_m.cli.studio import studio_command

        mock_run = MagicMock()

        with patch("subprocess.run", mock_run):
            studio_command(
                host="127.0.0.1",
                port=9000,
                reload=False,
                log_level=None,
            )

        captured = capsys.readouterr()
        assert "Framework M Studio" in captured.out
        assert "http://127.0.0.1:9000" in captured.out

    def test_studio_command_calls_subprocess(self) -> None:
        """studio_command should call subprocess.run."""
        from framework_m.cli.studio import studio_command

        mock_run = MagicMock()

        with patch("subprocess.run", mock_run):
            studio_command(
                host="127.0.0.1",
                port=9000,
                reload=False,
                log_level=None,
            )

        mock_run.assert_called_once()

    def test_studio_command_handles_error(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """studio_command should handle subprocess error."""
        from framework_m.cli.studio import studio_command

        mock_run = MagicMock()
        mock_run.side_effect = subprocess.CalledProcessError(1, ["uvicorn"])

        with patch("subprocess.run", mock_run):
            with pytest.raises(SystemExit) as exc:
                studio_command(
                    host="127.0.0.1",
                    port=9000,
                    reload=False,
                    log_level=None,
                )
            assert exc.value.code == 1

    def test_studio_command_handles_keyboard_interrupt(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """studio_command should handle KeyboardInterrupt gracefully."""
        from framework_m.cli.studio import studio_command

        mock_run = MagicMock()
        mock_run.side_effect = KeyboardInterrupt()

        with patch("subprocess.run", mock_run):
            studio_command(
                host="127.0.0.1",
                port=9000,
                reload=False,
                log_level=None,
            )

        captured = capsys.readouterr()
        assert "stopped" in captured.out.lower()


class TestStudioExecution:
    """Tests for studio command execution."""

    def test_studio_help(self) -> None:
        """studio --help should work."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "studio", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "studio" in result.stdout.lower()


class TestStudioExports:
    """Tests for studio module exports."""

    def test_all_exports(self) -> None:
        """studio module should export expected items."""
        from framework_m.cli import studio

        assert "studio_command" in studio.__all__
        assert "build_studio_command" in studio.__all__
        assert "get_studio_app" in studio.__all__
