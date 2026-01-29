"""Tests for Scaffolding CLI Commands - Comprehensive Coverage."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


class TestNewImport:
    """Tests for new module imports."""

    def test_import_new_doctype_command(self) -> None:
        """new_doctype_command should be importable."""
        from framework_m.cli.new import new_doctype_command

        assert new_doctype_command is not None

    def test_import_detect_app(self) -> None:
        """detect_app should be importable."""
        from framework_m.cli.new import detect_app

        assert detect_app is not None

    def test_import_scaffold_doctype(self) -> None:
        """scaffold_doctype should be importable."""
        from framework_m.cli.new import scaffold_doctype

        assert scaffold_doctype is not None

    def test_import_render_template(self) -> None:
        """render_template should be importable."""
        from framework_m.cli.new import render_template

        assert render_template is not None


class TestNameUtilities:
    """Tests for name conversion utilities."""

    def test_to_pascal_case_snake(self) -> None:
        """to_pascal_case should convert snake_case."""
        from framework_m.cli.new import to_pascal_case

        assert to_pascal_case("sales_order") == "SalesOrder"

    def test_to_pascal_case_single(self) -> None:
        """to_pascal_case should handle single word."""
        from framework_m.cli.new import to_pascal_case

        assert to_pascal_case("user") == "User"

    def test_to_pascal_case_already_pascal(self) -> None:
        """to_pascal_case should handle already PascalCase."""
        from framework_m.cli.new import to_pascal_case

        assert to_pascal_case("User") == "User"

    def test_to_pascal_case_multi_word_pascal(self) -> None:
        """to_pascal_case should preserve multi-word PascalCase like ItemSupplier."""
        from framework_m.cli.new import to_pascal_case

        assert to_pascal_case("ItemSupplier") == "ItemSupplier"
        assert to_pascal_case("SalesOrder") == "SalesOrder"

    def test_to_snake_case_pascal(self) -> None:
        """to_snake_case should convert PascalCase."""
        from framework_m.cli.new import to_snake_case

        assert to_snake_case("SalesOrder") == "sales_order"

    def test_to_snake_case_single(self) -> None:
        """to_snake_case should handle single word."""
        from framework_m.cli.new import to_snake_case

        assert to_snake_case("User") == "user"

    def test_normalize_app_name(self) -> None:
        """normalize_app_name should convert hyphens to underscores."""
        from framework_m.cli.new import normalize_app_name

        assert normalize_app_name("my-app") == "my_app"


class TestRenderTemplate:
    """Tests for render_template function."""

    def test_render_template_basic(self) -> None:
        """render_template should replace placeholders."""
        from framework_m.cli.new import render_template

        template = "Hello {{ name }}!"
        result = render_template(template, {"name": "World"})
        assert result == "Hello World!"

    def test_render_template_multiple(self) -> None:
        """render_template should handle multiple placeholders."""
        from framework_m.cli.new import render_template

        template = "class {{ class_name }}:\n    name = '{{ name }}'"
        result = render_template(template, {"class_name": "Invoice", "name": "invoice"})
        assert "class Invoice:" in result
        assert "name = 'invoice'" in result


class TestDetectApp:
    """Tests for detect_app function."""

    def test_detect_app_explicit(self) -> None:
        """detect_app should return explicit app name if provided."""
        from framework_m.cli.new import detect_app

        result = detect_app(explicit_app="myapp")
        assert result == "myapp"

    def test_detect_app_from_pyproject(self, tmp_path: Path) -> None:
        """detect_app should find app name from pyproject.toml."""
        from framework_m.cli.new import detect_app_from_cwd

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "my-app"')

        with patch("framework_m.cli.new.Path.cwd", return_value=tmp_path):
            result = detect_app_from_cwd()

        assert result == "my_app"  # Normalized name

    def test_detect_app_returns_none_when_not_found(self, tmp_path: Path) -> None:
        """detect_app_from_cwd should return None if no pyproject.toml."""
        from framework_m.cli.new import detect_app_from_cwd

        with patch("framework_m.cli.new.Path.cwd", return_value=tmp_path):
            result = detect_app_from_cwd()

        assert result is None


class TestParseProjectName:
    """Tests for parse_project_name function."""

    def test_parse_project_name_valid(self, tmp_path: Path) -> None:
        """parse_project_name should parse valid pyproject.toml."""
        from framework_m.cli.new import parse_project_name

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "test-project"')

        result = parse_project_name(pyproject)
        assert result == "test_project"

    def test_parse_project_name_missing_name(self, tmp_path: Path) -> None:
        """parse_project_name should return None if no name."""
        from framework_m.cli.new import parse_project_name

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[project]\nversion = '1.0'")

        result = parse_project_name(pyproject)
        assert result is None


class TestAppDetectionStrategy:
    """Tests for the full App Detection Strategy."""

    def test_list_installed_apps_returns_list(self) -> None:
        """list_installed_apps should return a list."""
        from framework_m.cli.new import list_installed_apps

        result = list_installed_apps()
        assert isinstance(result, list)

    def test_is_interactive_returns_bool(self) -> None:
        """is_interactive should return bool."""
        from framework_m.cli.new import is_interactive

        result = is_interactive()
        assert isinstance(result, bool)

    def test_prompt_select_returns_none_for_empty(self) -> None:
        """prompt_select should return None for empty options."""
        from framework_m.cli.new import prompt_select

        result = prompt_select("Pick one:", [])
        assert result is None

    def test_prompt_select_valid_selection(self) -> None:
        """prompt_select should return selected option."""
        from framework_m.cli.new import prompt_select

        with patch("builtins.input", return_value="1"):
            result = prompt_select("Pick one:", ["app1", "app2"])

        assert result == "app1"

    def test_prompt_select_quit(self) -> None:
        """prompt_select should return None on 'q'."""
        from framework_m.cli.new import prompt_select

        with patch("builtins.input", return_value="q"):
            result = prompt_select("Pick one:", ["app1"])

        assert result is None

    def test_prompt_select_invalid_number(self) -> None:
        """prompt_select should return None on invalid number."""
        from framework_m.cli.new import prompt_select

        with patch("builtins.input", return_value="99"):
            result = prompt_select("Pick one:", ["app1"])

        assert result is None

    def test_prompt_select_not_a_number(self) -> None:
        """prompt_select should return None on non-number input."""
        from framework_m.cli.new import prompt_select

        with patch("builtins.input", return_value="abc"):
            result = prompt_select("Pick one:", ["app1"])

        assert result is None

    def test_prompt_select_eof(self) -> None:
        """prompt_select should return None on EOFError."""
        from framework_m.cli.new import prompt_select

        with patch("builtins.input", side_effect=EOFError()):
            result = prompt_select("Pick one:", ["app1"])

        assert result is None

    def test_prompt_select_keyboard_interrupt(self) -> None:
        """prompt_select should return None on KeyboardInterrupt."""
        from framework_m.cli.new import prompt_select

        with patch("builtins.input", side_effect=KeyboardInterrupt()):
            result = prompt_select("Pick one:", ["app1"])

        assert result is None

    def test_require_app_with_explicit_app(self) -> None:
        """require_app should return explicit app immediately."""
        from framework_m.cli.new import require_app

        result = require_app(explicit_app="myapp")
        assert result == "myapp"

    def test_require_app_normalizes_name(self) -> None:
        """require_app should normalize app name."""
        from framework_m.cli.new import require_app

        result = require_app(explicit_app="my-app")
        assert result == "my_app"

    def test_require_app_fails_in_non_interactive(self, tmp_path: Path) -> None:
        """require_app should fail in non-interactive mode without app."""
        from framework_m.cli.new import require_app

        with (
            patch("framework_m.cli.new.detect_app_from_cwd", return_value=None),
            patch("framework_m.cli.new.is_interactive", return_value=False),
        ):
            with pytest.raises(SystemExit) as exc:
                require_app()
            assert exc.value.code == 1

    def test_require_app_interactive_with_apps(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """require_app should prompt in interactive mode."""
        from framework_m.cli.new import require_app

        with (
            patch("framework_m.cli.new.detect_app_from_cwd", return_value=None),
            patch("framework_m.cli.new.is_interactive", return_value=True),
            patch(
                "framework_m.cli.new.list_installed_apps", return_value=["app1", "app2"]
            ),
            patch("framework_m.cli.new.prompt_select", return_value="app1"),
        ):
            result = require_app()

        assert result == "app1"

    def test_require_app_interactive_no_selection(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """require_app should fail if no selection made."""
        from framework_m.cli.new import require_app

        with (
            patch("framework_m.cli.new.detect_app_from_cwd", return_value=None),
            patch("framework_m.cli.new.is_interactive", return_value=True),
            patch("framework_m.cli.new.list_installed_apps", return_value=["app1"]),
            patch("framework_m.cli.new.prompt_select", return_value=None),
        ):
            with pytest.raises(SystemExit) as exc:
                require_app()
            assert exc.value.code == 1

    def test_require_app_interactive_no_apps(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """require_app should fail if no apps registered."""
        from framework_m.cli.new import require_app

        with (
            patch("framework_m.cli.new.detect_app_from_cwd", return_value=None),
            patch("framework_m.cli.new.is_interactive", return_value=True),
            patch("framework_m.cli.new.list_installed_apps", return_value=[]),
        ):
            with pytest.raises(SystemExit) as exc:
                require_app()
            assert exc.value.code == 1

    def test_detect_app_normalizes_explicit(self) -> None:
        """detect_app should normalize explicit app."""
        from framework_m.cli.new import detect_app

        result = detect_app(explicit_app="my-app")
        assert result == "my_app"

    def test_detect_app_from_cwd(self) -> None:
        """detect_app should try detect_app_from_cwd."""
        from framework_m.cli.new import detect_app

        with patch(
            "framework_m.cli.new.detect_app_from_cwd", return_value="detected_app"
        ):
            result = detect_app()

        assert result == "detected_app"


class TestScaffoldDoctype:
    """Tests for scaffold_doctype function."""

    def test_scaffold_doctype_creates_files(self, tmp_path: Path) -> None:
        """scaffold_doctype should create doctype files."""
        from framework_m.cli.new import scaffold_doctype

        scaffold_doctype(
            doctype_name="Invoice",
            output_dir=tmp_path,
        )

        assert (tmp_path / "__init__.py").exists()
        assert (tmp_path / "doctype.py").exists()
        assert (tmp_path / "controller.py").exists()
        assert (tmp_path / "test_invoice.py").exists()

    def test_scaffold_doctype_uses_correct_class_names(self, tmp_path: Path) -> None:
        """scaffold_doctype should use PascalCase for class names."""
        from framework_m.cli.new import scaffold_doctype

        scaffold_doctype(
            doctype_name="sales_order",
            output_dir=tmp_path,
        )

        doctype_content = (tmp_path / "doctype.py").read_text()
        assert "class SalesOrder" in doctype_content

        controller_content = (tmp_path / "controller.py").read_text()
        assert "class SalesOrderController" in controller_content


class TestNewDoctypeCommand:
    """Tests for new_doctype_command function."""

    def test_new_doctype_command_is_callable(self) -> None:
        """new_doctype_command should be callable."""
        from framework_m.cli.new import new_doctype_command

        assert callable(new_doctype_command)

    def test_new_doctype_command_creates_files(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """new_doctype_command should create doctype files."""
        from framework_m.cli.new import new_doctype_command

        # Create a subdirectory that doesn't exist yet
        output_dir = tmp_path / "doctypes" / "test_doc"

        with patch("framework_m.cli.new.require_app", return_value="testapp"):
            new_doctype_command(
                name="TestDoc",
                app="testapp",
                output=output_dir,
            )

        captured = capsys.readouterr()
        assert "Created files" in captured.out
        assert output_dir.exists()

    def test_new_doctype_command_directory_exists(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """new_doctype_command should fail if directory exists."""
        from framework_m.cli.new import new_doctype_command

        # Create directory that already exists
        output_dir = tmp_path / "existing"
        output_dir.mkdir()

        with pytest.raises(SystemExit) as exc:
            new_doctype_command(
                name="TestDoc",
                app="testapp",
                output=output_dir,
            )
        assert exc.value.code == 1

        captured = capsys.readouterr()
        assert "already exists" in captured.err.lower()

    def test_new_doctype_command_no_app_no_output_interactive(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """new_doctype_command should warn if no app detected (interactive)."""
        from framework_m.cli.new import new_doctype_command

        with (
            patch("framework_m.cli.new.detect_app", return_value=None),
            patch("framework_m.cli.new.is_interactive", return_value=True),
            patch("framework_m.cli.new.Path.cwd", return_value=tmp_path),
        ):
            # Should create in tmp_path/snake_name
            new_doctype_command(name="TestDoc", app=None, output=None)

        captured = capsys.readouterr()
        assert "Warning" in captured.out or "Created" in captured.out

    def test_new_doctype_command_no_app_no_output_non_interactive(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """new_doctype_command should fail if no app detected (non-interactive)."""
        from framework_m.cli.new import new_doctype_command

        with (
            patch("framework_m.cli.new.detect_app", return_value=None),
            patch("framework_m.cli.new.is_interactive", return_value=False),
        ):
            with pytest.raises(SystemExit) as exc:
                new_doctype_command(name="TestDoc", app=None, output=None)
            assert exc.value.code == 1

    def test_new_doctype_command_with_detected_app(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """new_doctype_command should use detected app."""
        from framework_m.cli.new import new_doctype_command

        with (
            patch("framework_m.cli.new.detect_app", return_value="detected_app"),
            patch("framework_m.cli.new.Path.cwd", return_value=tmp_path),
        ):
            new_doctype_command(name="Invoice", app=None, output=None)

        captured = capsys.readouterr()
        assert "Creating DocType" in captured.out
        assert (tmp_path / "doctypes" / "invoice").exists()


class TestNewDoctypeExecution:
    """Tests for new:doctype command execution."""

    def test_new_doctype_help(self) -> None:
        """new:doctype --help should work."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "new:doctype", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "doctype" in result.stdout.lower()


class TestNewExports:
    """Tests for new module exports."""

    def test_all_exports(self) -> None:
        """new module should export expected items."""
        from framework_m.cli import new

        assert "new_doctype_command" in new.__all__
        assert "new_app_command" in new.__all__
        assert "detect_app" in new.__all__
        assert "scaffold_doctype" in new.__all__


class TestScaffoldApp:
    """Tests for scaffold_app function (replaces cruft-based tests)."""

    def test_scaffold_app_creates_files(self, tmp_path: Path) -> None:
        """scaffold_app should create app structure."""
        from framework_m.cli.new import scaffold_app

        created = scaffold_app("myapp", tmp_path)

        assert "pyproject.toml" in created
        assert "README.md" in created

    def test_scaffold_app_creates_directories(self, tmp_path: Path) -> None:
        """scaffold_app should create src/doctypes directory."""
        from framework_m.cli.new import scaffold_app

        scaffold_app("testapp", tmp_path)

        assert (tmp_path / "testapp" / "src" / "doctypes").exists()
        # .gitkeep is no longer created by scaffold_app

    def test_scaffold_app_pyproject_content(self, tmp_path: Path) -> None:
        """scaffold_app should create valid pyproject.toml."""
        from framework_m.cli.new import scaffold_app

        created = scaffold_app("mytest", tmp_path)

        pyproject_content = created["pyproject.toml"].read_text()
        assert 'name = "mytest"' in pyproject_content
        assert "framework-m" in pyproject_content


class TestNewAppCommand:
    """Tests for new_app_command function."""

    def test_new_app_command_is_callable(self) -> None:
        """new_app_command should be callable."""
        from framework_m.cli.new import new_app_command

        assert callable(new_app_command)

    def test_new_app_command_creates_app(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """new_app_command should create app successfully."""
        from framework_m.cli.new import new_app_command

        new_app_command(name="testapp", output_dir=tmp_path)

        captured = capsys.readouterr()
        assert "Creating new app" in captured.out
        assert "Created files" in captured.out
        assert (tmp_path / "testapp").exists()

    def test_new_app_command_directory_exists(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """new_app_command should fail if directory exists."""
        from framework_m.cli.new import new_app_command

        # Create directory that already exists
        (tmp_path / "existing").mkdir()

        with pytest.raises(SystemExit) as exc:
            new_app_command(name="existing", output_dir=tmp_path)
        assert exc.value.code == 1

        captured = capsys.readouterr()
        assert "already exists" in captured.err.lower()

    def test_new_app_command_with_hyphenated_name(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """new_app_command should handle hyphenated names."""
        from framework_m.cli.new import new_app_command

        new_app_command(name="my-test-app", output_dir=tmp_path)

        # Should create snake_case directory
        assert (tmp_path / "my_test_app").exists()


class TestNewAppExecution:
    """Tests for new:app command execution."""

    def test_new_app_help(self) -> None:
        """new:app --help should work."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "new:app", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        # Updated: no longer checks for 'template' - local scaffold
        assert "name" in result.stdout.lower()
        assert "output-dir" in result.stdout.lower()
