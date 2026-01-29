"""Extended tests for build.py to increase coverage.

These tests cover previously untested code paths and edge cases.
"""

import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# =============================================================================
# Tests for _build_indie_mode
# =============================================================================


class TestBuildIndieMode:
    """Tests for _build_indie_mode function."""

    def test_build_indie_mode_with_pnpm(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """_build_indie_mode should use pnpm if available."""
        from framework_m.cli.build import _build_indie_mode

        # Create frontend directory structure
        frontend_dir = tmp_path / "frontend"
        frontend_dir.mkdir()
        (frontend_dir / "package.json").write_text('{"name": "test"}')
        (frontend_dir / "node_modules").mkdir()
        dist_dir = frontend_dir / "dist"
        dist_dir.mkdir()

        mock_run = MagicMock()
        mock_run.return_value.returncode = 0

        with (
            patch("framework_m.cli.build._has_command", return_value=True),
            patch("subprocess.run", mock_run),
            patch("framework_m.cli.build.Path.cwd", return_value=tmp_path),
        ):
            _build_indie_mode("production", Path("dist"))

        # Should call pnpm
        captured = capsys.readouterr()
        assert "pnpm" in captured.out.lower()

    def test_build_indie_mode_fallback_to_npm(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """_build_indie_mode should fallback to npm if pnpm not available."""
        from framework_m.cli.build import _build_indie_mode

        frontend_dir = tmp_path / "frontend"
        frontend_dir.mkdir()
        (frontend_dir / "package.json").write_text('{"name": "test"}')
        (frontend_dir / "node_modules").mkdir()

        mock_run = MagicMock()
        mock_run.return_value.returncode = 0

        # _has_command returns False for pnpm
        with (
            patch("framework_m.cli.build._has_command", return_value=False),
            patch("subprocess.run", mock_run),
            patch("framework_m.cli.build.Path.cwd", return_value=tmp_path),
        ):
            _build_indie_mode("production", Path("dist"))

        # Should call npm
        call_args = [c.args[0] for c in mock_run.call_args_list]
        assert any("npm" in str(c) for c in call_args)

    def test_build_indie_mode_installs_dependencies(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """_build_indie_mode should install dependencies if node_modules missing."""
        from framework_m.cli.build import _build_indie_mode

        frontend_dir = tmp_path / "frontend"
        frontend_dir.mkdir()
        (frontend_dir / "package.json").write_text('{"name": "test"}')
        # No node_modules directory

        mock_run = MagicMock()

        with (
            patch("framework_m.cli.build._has_command", return_value=True),
            patch("subprocess.run", mock_run),
            patch("framework_m.cli.build.Path.cwd", return_value=tmp_path),
        ):
            _build_indie_mode("production", Path("dist"))

        # Should call install before build
        calls = [c.args[0] for c in mock_run.call_args_list]
        assert any("install" in str(c) for c in calls)

    def test_build_indie_mode_copies_to_output(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """_build_indie_mode should copy dist to output directory."""
        from framework_m.cli.build import _build_indie_mode

        frontend_dir = tmp_path / "frontend"
        frontend_dir.mkdir()
        (frontend_dir / "package.json").write_text('{"name": "test"}')
        (frontend_dir / "node_modules").mkdir()

        dist_dir = frontend_dir / "dist"
        dist_dir.mkdir()
        (dist_dir / "index.html").write_text("<html></html>")

        output_dir = tmp_path / "output"

        mock_run = MagicMock()

        with (
            patch("framework_m.cli.build._has_command", return_value=True),
            patch("subprocess.run", mock_run),
            patch("framework_m.cli.build.Path.cwd", return_value=tmp_path),
        ):
            _build_indie_mode("production", output_dir)

        # Output directory should have been created
        captured = capsys.readouterr()
        assert "complete" in captured.out.lower()

    def test_build_indie_mode_development_mode(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """_build_indie_mode should use dev command in development mode."""
        from framework_m.cli.build import _build_indie_mode

        frontend_dir = tmp_path / "frontend"
        frontend_dir.mkdir()
        (frontend_dir / "package.json").write_text('{"name": "test"}')
        (frontend_dir / "node_modules").mkdir()

        mock_run = MagicMock()

        with (
            patch("framework_m.cli.build._has_command", return_value=True),
            patch("subprocess.run", mock_run),
            patch("framework_m.cli.build.Path.cwd", return_value=tmp_path),
        ):
            _build_indie_mode("development", Path("dist"))

        # Should call dev instead of build
        calls = [c.args[0] for c in mock_run.call_args_list]
        assert any("dev" in str(c) for c in calls)


# =============================================================================
# Tests for _build_eject_mode
# =============================================================================


class TestBuildEjectMode:
    """Tests for _build_eject_mode function."""

    def test_build_eject_mode_prints_message(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """_build_eject_mode should print informative message."""
        from framework_m.cli.build import _build_eject_mode

        _build_eject_mode()

        captured = capsys.readouterr()
        assert "eject" in captured.out.lower()
        assert "user is responsible" in captured.out.lower()


# =============================================================================
# Tests for _build_plugin_mode
# =============================================================================


class TestBuildPluginMode:
    """Tests for _build_plugin_mode function."""

    def test_build_plugin_mode_finds_plugins(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """_build_plugin_mode should find app plugins."""
        from framework_m.cli.build import _build_plugin_mode

        # Create apps with frontend plugins
        apps_dir = tmp_path / "apps"
        apps_dir.mkdir()

        app1_dir = apps_dir / "app1"
        app1_dir.mkdir()
        app1_frontend = app1_dir / "frontend"
        app1_frontend.mkdir()
        (app1_frontend / "index.ts").write_text("export const register = () => {};")

        app2_dir = apps_dir / "app2"
        app2_dir.mkdir()
        app2_frontend = app2_dir / "frontend"
        app2_frontend.mkdir()
        (app2_frontend / "index.ts").write_text("export const register = () => {};")

        # Create frontend base
        frontend_dir = tmp_path / "frontend"
        frontend_dir.mkdir()
        (frontend_dir / "package.json").write_text('{"name": "test"}')
        (frontend_dir / "node_modules").mkdir()

        mock_run = MagicMock()

        with (
            patch("framework_m.cli.build._has_command", return_value=True),
            patch("subprocess.run", mock_run),
            patch("framework_m.cli.build.Path.cwd", return_value=tmp_path),
        ):
            _build_plugin_mode("production", Path("dist"))

        captured = capsys.readouterr()
        assert "2 app plugins" in captured.out or "app1" in captured.out

    def test_build_plugin_mode_no_plugins_fallback(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """_build_plugin_mode should fallback to indie mode if no plugins."""
        from framework_m.cli.build import _build_plugin_mode

        # No apps directory
        frontend_dir = tmp_path / "frontend"
        frontend_dir.mkdir()
        (frontend_dir / "package.json").write_text('{"name": "test"}')
        (frontend_dir / "node_modules").mkdir()

        mock_run = MagicMock()

        with (
            patch("framework_m.cli.build._has_command", return_value=True),
            patch("subprocess.run", mock_run),
            patch("framework_m.cli.build.Path.cwd", return_value=tmp_path),
        ):
            _build_plugin_mode("production", Path("dist"))

        captured = capsys.readouterr()
        assert "no app frontend plugins" in captured.out.lower()
        assert "falling back" in captured.out.lower()

    def test_build_plugin_mode_no_base_frontend(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """_build_plugin_mode should fail if no base frontend."""
        from framework_m.cli.build import _build_plugin_mode

        # Create apps with plugins but no frontend base
        apps_dir = tmp_path / "apps"
        apps_dir.mkdir()
        app1_dir = apps_dir / "app1"
        app1_dir.mkdir()
        app1_frontend = app1_dir / "frontend"
        app1_frontend.mkdir()
        (app1_frontend / "index.ts").write_text("export const register = () => {};")

        with (
            patch("framework_m.cli.build.Path.cwd", return_value=tmp_path),
            pytest.raises(SystemExit) as exc,
        ):
            _build_plugin_mode("production", Path("dist"))

        assert exc.value.code == 1

        captured = capsys.readouterr()
        assert "no frontend/package.json" in captured.out.lower()


# =============================================================================
# Tests for _generate_plugin_entry
# =============================================================================


class TestGeneratePluginEntry:
    """Tests for _generate_plugin_entry function."""

    def test_generate_plugin_entry_creates_file(self, tmp_path: Path) -> None:
        """_generate_plugin_entry should create entry file."""
        from framework_m.cli.build import _generate_plugin_entry

        entry_file = tmp_path / "entry.tsx"
        plugins = [
            ("app1", Path("/workspace/apps/app1/frontend/index.ts")),
            ("app2", Path("/workspace/apps/app2/frontend/index.ts")),
        ]

        with patch("framework_m.cli.build.Path.cwd", return_value=Path("/workspace")):
            _generate_plugin_entry(entry_file, plugins)

        assert entry_file.exists()
        content = entry_file.read_text()
        assert "import" in content
        assert "register_app1" in content
        assert "register_app2" in content
        assert "registerAllPlugins" in content

    def test_generate_plugin_entry_handles_special_characters(
        self, tmp_path: Path
    ) -> None:
        """_generate_plugin_entry should handle special characters in app names."""
        from framework_m.cli.build import _generate_plugin_entry

        entry_file = tmp_path / "entry.tsx"
        plugins = [
            ("my-app.v1", Path("/workspace/apps/my-app.v1/frontend/index.ts")),
        ]

        with patch("framework_m.cli.build.Path.cwd", return_value=Path("/workspace")):
            _generate_plugin_entry(entry_file, plugins)

        content = entry_file.read_text()
        # Special characters should be replaced with underscores
        assert "my_app_v1" in content


# =============================================================================
# Tests for _has_command
# =============================================================================


class TestHasCommand:
    """Tests for _has_command helper function."""

    def test_has_command_returns_true_for_existing_command(self) -> None:
        """_has_command should return True for existing command."""
        from framework_m.cli.build import _has_command

        mock_run = MagicMock()
        mock_run.return_value.returncode = 0

        with patch("subprocess.run", mock_run):
            result = _has_command("python")

        assert result is True

    def test_has_command_returns_false_for_missing_command(self) -> None:
        """_has_command should return False for missing command."""
        from framework_m.cli.build import _has_command

        with patch("subprocess.run", side_effect=FileNotFoundError()):
            result = _has_command("nonexistent-command")

        assert result is False

    def test_has_command_returns_false_on_error(self) -> None:
        """_has_command should return False on CalledProcessError."""
        from framework_m.cli.build import _has_command

        with patch(
            "subprocess.run",
            side_effect=subprocess.CalledProcessError(1, ["cmd"]),
        ):
            result = _has_command("failing-command")

        assert result is False


# =============================================================================
# Tests for build_command with frontend modes
# =============================================================================


class TestBuildCommandFrontendModes:
    """Tests for build_command with different frontend modes."""

    def test_build_command_eject_mode(self, capsys: pytest.CaptureFixture[str]) -> None:
        """build_command should handle eject mode."""
        from framework_m.cli.build import build_command

        mock_config: dict[str, Any] = {"frontend": {"mode": "eject"}}

        with patch("framework_m.cli.build.load_config", return_value=mock_config):
            build_command(mode="production", output=Path("dist"))

        captured = capsys.readouterr()
        assert "eject" in captured.out.lower()

    def test_build_command_plugin_mode(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """build_command should handle plugin mode."""
        from framework_m.cli.build import build_command

        mock_config: dict[str, Any] = {"frontend": {"mode": "plugin"}}

        # Create minimal structure with build script
        frontend_dir = tmp_path / "frontend"
        frontend_dir.mkdir()
        (frontend_dir / "package.json").write_text(
            '{"name": "test", "scripts": {"build": "echo build"}}'
        )
        (frontend_dir / "node_modules").mkdir()

        mock_run = MagicMock()

        with (
            patch("framework_m.cli.build.load_config", return_value=mock_config),
            patch("framework_m.cli.build._has_command", return_value=True),
            patch("subprocess.run", mock_run),
            patch("framework_m.cli.build.Path.cwd", return_value=tmp_path),
        ):
            build_command(mode="production", output=Path("dist"))

        captured = capsys.readouterr()
        assert "plugin" in captured.out.lower()

    def test_build_command_override_frontend_mode(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """build_command should allow frontend_mode override."""
        from framework_m.cli.build import build_command

        mock_config: dict[str, Any] = {"frontend": {"mode": "indie"}}

        with patch("framework_m.cli.build.load_config", return_value=mock_config):
            build_command(
                mode="production",
                output=Path("dist"),
                frontend_mode="eject",  # Override
            )

        captured = capsys.readouterr()
        assert "eject" in captured.out.lower()


# =============================================================================
# Tests for build_docker_command with push failure
# =============================================================================


class TestBuildDockerCommandPushFailure:
    """Tests for build_docker_command push failure scenarios."""

    def test_build_docker_command_push_fails(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """build_docker_command should handle push failure."""
        from framework_m.cli.build import build_docker_command

        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text("FROM python:3.12")

        def mock_run_side_effect(
            cmd: list[str], *args: Any, **kwargs: Any
        ) -> MagicMock:
            result = MagicMock()
            if "push" in cmd:
                result.returncode = 1  # Push fails
            else:
                result.returncode = 0  # Build succeeds
            return result

        with patch("subprocess.run", side_effect=mock_run_side_effect):
            with pytest.raises(SystemExit) as exc:
                build_docker_command(
                    tag="myapp:v1",
                    dockerfile=str(dockerfile),
                    context=".",
                    no_cache=False,
                    push=True,
                )

            assert exc.value.code == 1


# =============================================================================
# Tests for build_docker_cmd with multiple build args
# =============================================================================


class TestBuildDockerCmdMultipleBuildArgs:
    """Tests for build_docker_cmd with multiple build arguments."""

    def test_build_docker_cmd_multiple_build_args(self) -> None:
        """build_docker_cmd should handle multiple build args."""
        from framework_m.cli.build import build_docker_cmd

        cmd = build_docker_cmd(
            tag="myapp:v1",
            build_args=["VERSION=1.0", "ENV=production", "DEBUG=false"],
        )

        # Each build arg should appear with --build-arg
        assert cmd.count("--build-arg") == 3
        assert "VERSION=1.0" in cmd
        assert "ENV=production" in cmd
        assert "DEBUG=false" in cmd


# =============================================================================
# Tests for get_default_image_name edge cases
# =============================================================================


class TestGetDefaultImageNameEdgeCases:
    """Tests for get_default_image_name edge cases."""

    def test_get_default_image_name_empty_config(self) -> None:
        """get_default_image_name should handle empty framework section."""
        from framework_m.cli.build import get_default_image_name

        mock_config: dict[str, Any] = {"framework": {}}

        with patch("framework_m.cli.build.load_config", return_value=mock_config):
            result = get_default_image_name()

        assert "framework-m-app" in result
        assert "latest" in result

    def test_get_default_image_name_partial_config(self) -> None:
        """get_default_image_name should handle partial config."""
        from framework_m.cli.build import get_default_image_name

        mock_config: dict[str, Any] = {"framework": {"name": "myapp"}}  # No version

        with patch("framework_m.cli.build.load_config", return_value=mock_config):
            result = get_default_image_name()

        assert "myapp" in result
        assert "latest" in result


# =============================================================================
# Tests for _build_indie_mode error handling
# =============================================================================


class TestBuildIndieModeErrorHandling:
    """Tests for _build_indie_mode error handling."""

    def test_build_indie_mode_npm_not_found_raises(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """_build_indie_mode should raise SystemExit if npm not found."""
        from framework_m.cli.build import _build_indie_mode

        frontend_dir = tmp_path / "frontend"
        frontend_dir.mkdir()
        (frontend_dir / "package.json").write_text('{"name": "test"}')

        with (
            patch("framework_m.cli.build._has_command", return_value=False),
            patch("subprocess.run", side_effect=FileNotFoundError()),
            patch("framework_m.cli.build.Path.cwd", return_value=tmp_path),
            pytest.raises(SystemExit) as exc,
        ):
            _build_indie_mode("production", Path("dist"))

        assert exc.value.code == 1

    def test_build_indie_mode_build_fails_raises(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """_build_indie_mode should raise SystemExit if build fails."""
        from framework_m.cli.build import _build_indie_mode

        frontend_dir = tmp_path / "frontend"
        frontend_dir.mkdir()
        (frontend_dir / "package.json").write_text('{"name": "test"}')
        (frontend_dir / "node_modules").mkdir()

        with (
            patch("framework_m.cli.build._has_command", return_value=True),
            patch(
                "subprocess.run",
                side_effect=subprocess.CalledProcessError(1, ["pnpm"]),
            ),
            patch("framework_m.cli.build.Path.cwd", return_value=tmp_path),
            pytest.raises(SystemExit) as exc,
        ):
            _build_indie_mode("production", Path("dist"))

        assert exc.value.code == 1
