"""Tests for Configuration Management CLI Commands - Comprehensive Coverage."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest


class TestConfigImport:
    """Tests for config module imports."""

    def test_import_config_show_command(self) -> None:
        """config_show_command should be importable."""
        from framework_m.cli.config import config_show_command

        assert config_show_command is not None

    def test_import_config_set_command(self) -> None:
        """config_set_command should be importable."""
        from framework_m.cli.config import config_set_command

        assert config_set_command is not None

    def test_import_load_config(self) -> None:
        """load_config should be importable."""
        from framework_m.cli.config import load_config

        assert load_config is not None

    def test_import_save_config(self) -> None:
        """save_config should be importable."""
        from framework_m.cli.config import save_config

        assert save_config is not None


class TestFindConfigFile:
    """Tests for find_config_file function."""

    def test_find_config_file_returns_path(self) -> None:
        """find_config_file should return a Path."""
        from framework_m.cli.config import find_config_file

        result = find_config_file()
        assert isinstance(result, Path)


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_returns_dict(self, tmp_path: Path) -> None:
        """load_config should return a dict."""
        from framework_m.cli.config import load_config

        config_file = tmp_path / "framework_config.toml"
        config_file.write_text('[framework]\nname = "test"')

        result = load_config(config_file)
        assert isinstance(result, dict)
        assert result.get("framework", {}).get("name") == "test"

    def test_load_config_returns_empty_for_missing(self, tmp_path: Path) -> None:
        """load_config should return empty dict for missing file."""
        from framework_m.cli.config import load_config

        config_file = tmp_path / "nonexistent.toml"
        result = load_config(config_file)
        assert result == {}

    def test_load_config_returns_empty_for_invalid(self, tmp_path: Path) -> None:
        """load_config should return empty dict for invalid TOML."""
        from framework_m.cli.config import load_config

        config_file = tmp_path / "invalid.toml"
        config_file.write_text("this is not valid toml [[[")

        result = load_config(config_file)
        assert result == {}


class TestSaveConfig:
    """Tests for save_config function."""

    def test_save_config_creates_file(self, tmp_path: Path) -> None:
        """save_config should create config file."""
        from framework_m.cli.config import save_config

        config_file = tmp_path / "framework_config.toml"
        config: dict[str, Any] = {"framework": {"name": "test"}}

        save_config(config_file, config)

        assert config_file.exists()
        content = config_file.read_text()
        assert "test" in content

    def test_save_config_with_list(self, tmp_path: Path) -> None:
        """save_config should handle lists."""
        from framework_m.cli.config import save_config

        config_file = tmp_path / "framework_config.toml"
        config: dict[str, Any] = {"apps": {"installed": ["app1", "app2"]}}

        save_config(config_file, config)

        content = config_file.read_text()
        assert "app1" in content
        assert "app2" in content

    def test_save_config_with_bool(self, tmp_path: Path) -> None:
        """save_config should handle booleans."""
        from framework_m.cli.config import save_config

        config_file = tmp_path / "framework_config.toml"
        config: dict[str, Any] = {"settings": {"debug": True}}

        save_config(config_file, config)

        content = config_file.read_text()
        assert "true" in content

    def test_save_config_with_number(self, tmp_path: Path) -> None:
        """save_config should handle numbers."""
        from framework_m.cli.config import save_config

        config_file = tmp_path / "framework_config.toml"
        config: dict[str, Any] = {"settings": {"timeout": 30}}

        save_config(config_file, config)

        content = config_file.read_text()
        assert "30" in content


class TestNestedValue:
    """Tests for get/set nested value functions."""

    def test_get_nested_value(self) -> None:
        """get_nested_value should retrieve nested values."""
        from framework_m.cli.config import get_nested_value

        config: dict[str, Any] = {"framework": {"name": "test", "version": "1.0"}}

        assert get_nested_value(config, "framework.name") == "test"
        assert get_nested_value(config, "framework.version") == "1.0"
        assert get_nested_value(config, "missing.key") is None

    def test_get_nested_value_single_level(self) -> None:
        """get_nested_value should handle single-level keys."""
        from framework_m.cli.config import get_nested_value

        config: dict[str, Any] = {"name": "test"}

        assert get_nested_value(config, "name") == "test"

    def test_set_nested_value(self) -> None:
        """set_nested_value should set nested values."""
        from framework_m.cli.config import set_nested_value

        config: dict[str, Any] = {"framework": {}}

        set_nested_value(config, "framework.name", "myapp")
        assert config["framework"]["name"] == "myapp"

    def test_set_nested_value_creates_path(self) -> None:
        """set_nested_value should create nested dicts as needed."""
        from framework_m.cli.config import set_nested_value

        config: dict[str, Any] = {}

        set_nested_value(config, "deep.nested.key", "value")
        assert config["deep"]["nested"]["key"] == "value"


class TestFormatConfig:
    """Tests for format_config function."""

    def test_format_config_basic(self) -> None:
        """format_config should format basic config."""
        from framework_m.cli.config import format_config

        config: dict[str, Any] = {"framework": {"name": "test"}}

        result = format_config(config)
        assert "[framework]" in result
        assert "name = test" in result

    def test_format_config_with_list(self) -> None:
        """format_config should format lists."""
        from framework_m.cli.config import format_config

        config: dict[str, Any] = {"apps": {"installed": ["a", "b"]}}

        result = format_config(config)
        assert "[apps]" in result
        assert "installed = [a, b]" in result


class TestConfigShowCommand:
    """Tests for config_show_command function."""

    def test_config_show_no_config(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """config_show should handle missing config."""
        from framework_m.cli.config import config_show_command

        config_file = tmp_path / "nonexistent.toml"

        config_show_command(key=None, config_file=config_file)

        captured = capsys.readouterr()
        assert "No config found" in captured.out

    def test_config_show_all(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """config_show should display all config."""
        from framework_m.cli.config import config_show_command

        config_file = tmp_path / "framework_config.toml"
        config_file.write_text('[framework]\nname = "test"')

        config_show_command(key=None, config_file=config_file)

        captured = capsys.readouterr()
        assert "Config file:" in captured.out
        assert "framework" in captured.out

    def test_config_show_specific_key(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """config_show should display specific key."""
        from framework_m.cli.config import config_show_command

        config_file = tmp_path / "framework_config.toml"
        config_file.write_text('[framework]\nname = "test"')

        config_show_command(key="framework.name", config_file=config_file)

        captured = capsys.readouterr()
        assert "framework.name = test" in captured.out

    def test_config_show_missing_key(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """config_show should fail for missing key."""
        from framework_m.cli.config import config_show_command

        config_file = tmp_path / "framework_config.toml"
        config_file.write_text('[framework]\nname = "test"')

        with pytest.raises(SystemExit) as exc:
            config_show_command(key="missing.key", config_file=config_file)
        assert exc.value.code == 1

        captured = capsys.readouterr()
        assert "Key not found" in captured.out


class TestConfigSetCommand:
    """Tests for config_set_command function."""

    def test_config_set_new_key(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """config_set should add new key."""
        from framework_m.cli.config import config_set_command

        config_file = tmp_path / "framework_config.toml"

        config_set_command(key="framework.name", value="myapp", config_file=config_file)

        captured = capsys.readouterr()
        assert "Configuration updated" in captured.out
        assert config_file.exists()

    def test_config_set_update_existing(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """config_set should update existing key."""
        from framework_m.cli.config import config_set_command

        config_file = tmp_path / "framework_config.toml"
        config_file.write_text('[framework]\nname = "old"')

        config_set_command(key="framework.name", value="new", config_file=config_file)

        captured = capsys.readouterr()
        assert "old -> new" in captured.out

    def test_config_set_list_value(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """config_set should handle comma-separated list."""
        from framework_m.cli.config import config_set_command

        config_file = tmp_path / "framework_config.toml"

        config_set_command(
            key="apps.installed", value="app1,app2", config_file=config_file
        )

        captured = capsys.readouterr()
        assert "Configuration updated" in captured.out


class TestConfigExecution:
    """Tests for config command execution."""

    def test_config_show_help(self) -> None:
        """config:show --help should work."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "config:show", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_config_set_help(self) -> None:
        """config:set --help should work."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "config:set", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0


class TestConfigExports:
    """Tests for config module exports."""

    def test_all_exports(self) -> None:
        """config module should export expected items."""
        from framework_m.cli import config

        assert "config_show_command" in config.__all__
        assert "config_set_command" in config.__all__
        assert "load_config" in config.__all__
        assert "save_config" in config.__all__
