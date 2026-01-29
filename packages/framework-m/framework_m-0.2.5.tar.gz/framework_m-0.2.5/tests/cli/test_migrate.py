"""Tests for Migration CLI Commands - Comprehensive Coverage."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestMigrateImport:
    """Tests for migrate module imports."""

    def test_import_migrate_app(self) -> None:
        """migrate_app should be importable."""
        from framework_m.cli.migrate import migrate_app

        assert migrate_app is not None

    def test_import_get_manager(self) -> None:
        """get_manager should be importable."""
        from framework_m.cli.migrate import get_manager

        assert get_manager is not None


class TestMigrateAppStructure:
    """Tests for migrate app structure."""

    def test_migrate_app_is_cyclopts_app(self) -> None:
        """migrate_app should be a cyclopts App."""
        import cyclopts

        from framework_m.cli.migrate import migrate_app

        assert isinstance(migrate_app, cyclopts.App)


class TestGetManager:
    """Tests for get_manager function."""

    def test_get_manager_returns_manager(self, tmp_path: Path) -> None:
        """get_manager should return a MigrationManager."""
        from framework_m.cli.migrate import get_manager

        # Create fake alembic directory (required by get_manager)
        (tmp_path / "alembic").mkdir()

        with patch("framework_m.cli.migrate.MigrationManager") as MockManager:
            mock_instance = MagicMock()
            MockManager.return_value = mock_instance

            result = get_manager(tmp_path, "postgresql://localhost/test")

            MockManager.assert_called_once_with(
                base_path=tmp_path, database_url="postgresql://localhost/test"
            )
            assert result == mock_instance

    def test_get_manager_without_database_url(self, tmp_path: Path) -> None:
        """get_manager should work without database URL."""
        from framework_m.cli.migrate import get_manager

        # Create fake alembic directory (required by get_manager)
        (tmp_path / "alembic").mkdir()

        with patch("framework_m.cli.migrate.MigrationManager") as MockManager:
            mock_instance = MagicMock()
            MockManager.return_value = mock_instance

            result = get_manager(tmp_path)

            MockManager.assert_called_once_with(base_path=tmp_path, database_url=None)
            assert result == mock_instance


class TestMigrateCommand:
    """Tests for migrate (upgrade) command."""

    def test_migrate_success(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """migrate should run upgrade successfully."""
        from framework_m.cli.migrate import migrate

        mock_manager = MagicMock()

        with patch("framework_m.cli.migrate.get_manager", return_value=mock_manager):
            migrate(path=tmp_path, database_url=None, revision="head")

        captured = capsys.readouterr()
        assert "Running migrations" in captured.out
        assert "completed successfully" in captured.out
        mock_manager.upgrade.assert_called_once_with("head")

    def test_migrate_failure(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """migrate should handle failure gracefully."""
        from framework_m.cli.migrate import migrate

        mock_manager = MagicMock()
        mock_manager.upgrade.side_effect = Exception("Connection failed")

        with patch("framework_m.cli.migrate.get_manager", return_value=mock_manager):
            with pytest.raises(SystemExit) as exc:
                migrate(path=tmp_path, database_url=None, revision="head")
            assert exc.value.code == 1

        captured = capsys.readouterr()
        assert "failed" in captured.err.lower()


class TestCreateCommand:
    """Tests for create command."""

    def test_create_success(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """create should create migration successfully."""
        from framework_m.cli.migrate import create

        mock_manager = MagicMock()

        with patch("framework_m.cli.migrate.get_manager", return_value=mock_manager):
            create(
                message="Add users table",
                path=tmp_path,
                database_url=None,
                autogenerate=True,
            )

        captured = capsys.readouterr()
        assert "Creating migration" in captured.out
        assert "created successfully" in captured.out
        mock_manager.revision.assert_called_once_with(
            message="Add users table", autogenerate=True
        )

    def test_create_failure(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """create should handle failure gracefully."""
        from framework_m.cli.migrate import create

        mock_manager = MagicMock()
        mock_manager.revision.side_effect = Exception("Revision error")

        with patch("framework_m.cli.migrate.get_manager", return_value=mock_manager):
            with pytest.raises(SystemExit) as exc:
                create(
                    message="test", path=tmp_path, database_url=None, autogenerate=True
                )
            assert exc.value.code == 1


class TestRollbackCommand:
    """Tests for rollback command."""

    def test_rollback_success(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """rollback should run downgrade successfully."""
        from framework_m.cli.migrate import rollback

        mock_manager = MagicMock()

        with patch("framework_m.cli.migrate.get_manager", return_value=mock_manager):
            rollback(path=tmp_path, database_url=None, steps=1)

        captured = capsys.readouterr()
        assert "Rolling back" in captured.out
        assert "completed successfully" in captured.out
        mock_manager.downgrade.assert_called_once_with("-1")

    def test_rollback_multiple_steps(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """rollback should support multiple steps."""
        from framework_m.cli.migrate import rollback

        mock_manager = MagicMock()

        with patch("framework_m.cli.migrate.get_manager", return_value=mock_manager):
            rollback(path=tmp_path, database_url=None, steps=3)

        mock_manager.downgrade.assert_called_once_with("-3")

    def test_rollback_failure(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """rollback should handle failure gracefully."""
        from framework_m.cli.migrate import rollback

        mock_manager = MagicMock()
        mock_manager.downgrade.side_effect = Exception("Rollback error")

        with patch("framework_m.cli.migrate.get_manager", return_value=mock_manager):
            with pytest.raises(SystemExit) as exc:
                rollback(path=tmp_path, database_url=None, steps=1)
            assert exc.value.code == 1


class TestStatusCommand:
    """Tests for status command."""

    def test_status_success(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """status should show current revision."""
        from framework_m.cli.migrate import status

        mock_manager = MagicMock()

        with patch("framework_m.cli.migrate.get_manager", return_value=mock_manager):
            status(path=tmp_path, database_url=None)

        captured = capsys.readouterr()
        assert "Migration Status" in captured.out
        mock_manager.current.assert_called_once()

    def test_status_failure(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """status should handle failure gracefully."""
        from framework_m.cli.migrate import status

        mock_manager = MagicMock()
        mock_manager.current.side_effect = Exception("Status error")

        with patch("framework_m.cli.migrate.get_manager", return_value=mock_manager):
            with pytest.raises(SystemExit) as exc:
                status(path=tmp_path, database_url=None)
            assert exc.value.code == 1


class TestHistoryCommand:
    """Tests for history command."""

    def test_history_success(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """history should show migration history."""
        from framework_m.cli.migrate import history

        mock_manager = MagicMock()

        with patch("framework_m.cli.migrate.get_manager", return_value=mock_manager):
            history(path=tmp_path, database_url=None)

        captured = capsys.readouterr()
        assert "Migration History" in captured.out
        mock_manager.history.assert_called_once()

    def test_history_failure(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """history should handle failure gracefully."""
        from framework_m.cli.migrate import history

        mock_manager = MagicMock()
        mock_manager.history.side_effect = Exception("History error")

        with patch("framework_m.cli.migrate.get_manager", return_value=mock_manager):
            with pytest.raises(SystemExit) as exc:
                history(path=tmp_path, database_url=None)
            assert exc.value.code == 1


class TestInitCommand:
    """Tests for init command."""

    def test_init_success(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """init should initialize alembic."""
        from framework_m.cli.migrate import init_alembic

        mock_manager = MagicMock()
        mock_manager.alembic_path = tmp_path / "alembic"

        with patch("framework_m.cli.migrate.get_manager", return_value=mock_manager):
            init_alembic(path=tmp_path, database_url=None)

        captured = capsys.readouterr()
        assert "Initializing Alembic" in captured.out
        assert "initialized successfully" in captured.out
        mock_manager.init.assert_called_once()

    def test_init_failure(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """init should handle failure gracefully."""
        from framework_m.cli.migrate import init_alembic

        mock_manager = MagicMock()
        mock_manager.init.side_effect = Exception("Init error")

        with patch("framework_m.cli.migrate.get_manager", return_value=mock_manager):
            with pytest.raises(SystemExit) as exc:
                init_alembic(path=tmp_path, database_url=None)
            assert exc.value.code == 1


class TestMigrateExecution:
    """Tests for migrate command execution."""

    def test_migrate_help(self) -> None:
        """migrate --help should work."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "migrate", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_migrate_create_help(self) -> None:
        """migrate create --help should work."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "framework_m.cli.main",
                "migrate",
                "create",
                "--help",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_migrate_rollback_help(self) -> None:
        """migrate rollback --help should work."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "framework_m.cli.main",
                "migrate",
                "rollback",
                "--help",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_migrate_status_help(self) -> None:
        """migrate status --help should work."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "framework_m.cli.main",
                "migrate",
                "status",
                "--help",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_migrate_history_help(self) -> None:
        """migrate history --help should work."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "framework_m.cli.main",
                "migrate",
                "history",
                "--help",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_migrate_init_help(self) -> None:
        """migrate init --help should work."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "migrate", "init", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0


class TestMigrateExports:
    """Tests for migrate module exports."""

    def test_all_exports(self) -> None:
        """migrate module should export expected items."""
        from framework_m.cli import migrate

        assert "migrate_app" in migrate.__all__
        assert "get_manager" in migrate.__all__
