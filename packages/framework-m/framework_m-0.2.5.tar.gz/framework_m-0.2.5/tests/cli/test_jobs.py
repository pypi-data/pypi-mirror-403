"""Tests for Job CLI Commands - Comprehensive Coverage."""

from __future__ import annotations

import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest


class TestJobCLIImport:
    """Tests for job CLI import."""

    def test_import_job_app(self) -> None:
        """job_app should be importable."""
        from framework_m.cli.jobs import job_app

        assert job_app is not None


class TestJobAppStructure:
    """Tests for job app command structure."""

    def test_job_app_is_cyclopts_app(self) -> None:
        """job_app should be a cyclopts App."""
        import cyclopts

        from framework_m.cli.jobs import job_app

        assert isinstance(job_app, cyclopts.App)


class TestJobCLIExports:
    """Tests for job CLI exports."""

    def test_all_exports(self) -> None:
        """job CLI module should export job_app."""
        from framework_m.cli import jobs

        assert "job_app" in jobs.__all__


class TestListJobsFunction:
    """Unit tests for list_jobs function."""

    def test_list_jobs_no_jobs(self, capsys: pytest.CaptureFixture[str]) -> None:
        """list_jobs should show message when no jobs registered."""
        from framework_m.cli.jobs import list_jobs

        mock_registry = MagicMock()
        mock_registry.list.return_value = []

        with patch(
            "framework_m.adapters.jobs.taskiq_adapter.get_global_registry",
            return_value=mock_registry,
        ):
            list_jobs()

        captured = capsys.readouterr()
        assert "No jobs registered" in captured.out

    def test_list_jobs_with_jobs(self, capsys: pytest.CaptureFixture[str]) -> None:
        """list_jobs should list registered jobs."""
        from framework_m.cli.jobs import list_jobs

        mock_registry = MagicMock()
        mock_registry.list.return_value = ["job_one", "job_two"]
        mock_registry.get_metadata.return_value = {"retry": 3, "timeout": 300}

        with patch(
            "framework_m.adapters.jobs.taskiq_adapter.get_global_registry",
            return_value=mock_registry,
        ):
            list_jobs()

        captured = capsys.readouterr()
        assert "Registered jobs (2)" in captured.out
        assert "job_one" in captured.out
        assert "job_two" in captured.out


class TestRunJobFunction:
    """Unit tests for run_job function."""

    def test_run_job_not_registered(self, capsys: pytest.CaptureFixture[str]) -> None:
        """run_job should fail if job is not registered."""
        from framework_m.cli.jobs import run_job

        mock_registry = MagicMock()
        mock_registry.list.return_value = []

        with patch(
            "framework_m.adapters.jobs.taskiq_adapter.get_global_registry",
            return_value=mock_registry,
        ):
            with pytest.raises(SystemExit) as exc:
                run_job("missing_job", "{}")
            assert exc.value.code == 1

        captured = capsys.readouterr()
        assert "not registered" in captured.err

    def test_run_job_invalid_json(self, capsys: pytest.CaptureFixture[str]) -> None:
        """run_job should fail with invalid JSON kwargs."""
        from framework_m.cli.jobs import run_job

        mock_registry = MagicMock()
        mock_registry.list.return_value = ["my_job"]

        with patch(
            "framework_m.adapters.jobs.taskiq_adapter.get_global_registry",
            return_value=mock_registry,
        ):
            with pytest.raises(SystemExit) as exc:
                run_job("my_job", "not valid json")
            assert exc.value.code == 1

        captured = capsys.readouterr()
        assert "Invalid JSON" in captured.err


class TestJobStatusFunction:
    """Unit tests for job_status function."""

    def test_job_status_not_found(self, capsys: pytest.CaptureFixture[str]) -> None:
        """job_status should fail if job ID not found."""
        from framework_m.cli.jobs import job_status

        mock_queue = MagicMock()

        async def mock_get_status(job_id: str) -> None:
            return None

        mock_queue.get_status.side_effect = mock_get_status

        with patch(
            "framework_m.adapters.factory.get_job_queue", return_value=mock_queue
        ):
            with pytest.raises(SystemExit) as exc:
                job_status("missing-job-id")
            assert exc.value.code == 1

        captured = capsys.readouterr()
        assert "not found" in captured.err

    def test_job_status_found(self, capsys: pytest.CaptureFixture[str]) -> None:
        """job_status should display status if job found."""
        from framework_m.cli.jobs import job_status
        from framework_m.core.interfaces.job_queue import JobInfo, JobStatus

        mock_info = JobInfo(
            id="job-123",
            name="test_job",
            status=JobStatus.SUCCESS,
            result={"data": "test"},
        )

        mock_queue = MagicMock()

        async def mock_get_status(job_id: str) -> JobInfo:
            return mock_info

        mock_queue.get_status.side_effect = mock_get_status

        with patch(
            "framework_m.adapters.factory.get_job_queue", return_value=mock_queue
        ):
            job_status("job-123")

        captured = capsys.readouterr()
        assert "job-123" in captured.out
        assert "SUCCESS" in captured.out or "success" in captured.out.lower()


class TestRunJobSuccess:
    """Unit tests for run_job success path."""

    def test_run_job_success(self, capsys: pytest.CaptureFixture[str]) -> None:
        """run_job should enqueue job successfully."""
        from framework_m.cli.jobs import run_job

        mock_registry = MagicMock()
        mock_registry.list.return_value = ["my_job"]

        mock_queue = MagicMock()

        async def mock_enqueue(name: str, **kwargs: object) -> str:
            return "job-id-123"

        mock_queue.enqueue.side_effect = mock_enqueue

        with (
            patch(
                "framework_m.adapters.jobs.taskiq_adapter.get_global_registry",
                return_value=mock_registry,
            ),
            patch(
                "framework_m.adapters.factory.get_job_queue", return_value=mock_queue
            ),
        ):
            run_job("my_job", "{}")

        captured = capsys.readouterr()
        assert "Job enqueued" in captured.out
        assert "job-id-123" in captured.out

    def test_run_job_with_kwargs(self, capsys: pytest.CaptureFixture[str]) -> None:
        """run_job should pass kwargs to job."""
        from framework_m.cli.jobs import run_job

        mock_registry = MagicMock()
        mock_registry.list.return_value = ["send_email"]

        mock_queue = MagicMock()
        received_kwargs: dict[str, object] = {}

        async def mock_enqueue(name: str, **kwargs: object) -> str:
            nonlocal received_kwargs
            received_kwargs = kwargs
            return "job-id-456"

        mock_queue.enqueue.side_effect = mock_enqueue

        with (
            patch(
                "framework_m.adapters.jobs.taskiq_adapter.get_global_registry",
                return_value=mock_registry,
            ),
            patch(
                "framework_m.adapters.factory.get_job_queue", return_value=mock_queue
            ),
        ):
            run_job("send_email", '{"to": "test@example.com", "subject": "Hello"}')

        assert received_kwargs.get("to") == "test@example.com"
        assert received_kwargs.get("subject") == "Hello"


class TestJobListCommandExecution:
    """Tests for job list command execution via subprocess."""

    def test_list_no_jobs(self) -> None:
        """list should show no jobs message when registry is empty."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "job", "list"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "No jobs registered" in result.stdout

    def test_list_help(self) -> None:
        """list --help should show help."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "job", "list", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0


class TestJobRunCommandExecution:
    """Tests for job run command execution."""

    def test_run_help(self) -> None:
        """run --help should show help."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "job", "run", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_run_nonexistent_job(self) -> None:
        """run should fail for unregistered job."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "job", "run", "nonexistent"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "not registered" in result.stderr


class TestJobStatusCommandExecution:
    """Tests for job status command execution."""

    def test_status_help(self) -> None:
        """status --help should show help."""
        result = subprocess.run(
            [sys.executable, "-m", "framework_m.cli.main", "job", "status", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
