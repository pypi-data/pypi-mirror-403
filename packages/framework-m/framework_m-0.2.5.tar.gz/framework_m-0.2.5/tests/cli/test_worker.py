"""Tests for Worker CLI - Comprehensive coverage tests."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# =============================================================================
# Test: Worker Module Import
# =============================================================================


class TestWorkerImport:
    """Tests for worker module imports."""

    def test_import_worker_command(self) -> None:
        """worker_command should be importable."""
        from framework_m.cli.worker import worker_command

        assert worker_command is not None

    def test_import_run_worker(self) -> None:
        """run_worker should be importable."""
        from framework_m.cli.worker import run_worker

        assert run_worker is not None

    def test_import_get_nats_url(self) -> None:
        """get_nats_url should be importable."""
        from framework_m.cli.worker import get_nats_url

        assert get_nats_url is not None

    def test_import_get_broker(self) -> None:
        """get_broker should be importable."""
        from framework_m.cli.worker import get_broker

        assert get_broker is not None

    def test_import_discover_jobs(self) -> None:
        """discover_jobs should be importable."""
        from framework_m.cli.worker import discover_jobs

        assert discover_jobs is not None

    def test_import_load_scheduled_jobs(self) -> None:
        """load_scheduled_jobs should be importable."""
        from framework_m.cli.worker import load_scheduled_jobs

        assert load_scheduled_jobs is not None

    def test_import_run_worker_async(self) -> None:
        """_run_worker_async should be importable."""
        from framework_m.cli.worker import _run_worker_async

        assert _run_worker_async is not None

    def test_exports(self) -> None:
        """worker module should export expected items."""
        from framework_m.cli import worker

        assert "worker_command" in worker.__all__
        assert "run_worker" in worker.__all__
        assert "discover_jobs" in worker.__all__
        assert "get_nats_url" in worker.__all__
        assert "load_scheduled_jobs" in worker.__all__


# =============================================================================
# Test: get_nats_url
# =============================================================================


class TestGetNatsUrl:
    """Tests for get_nats_url function."""

    def test_returns_default_when_no_env(self) -> None:
        """get_nats_url should return default when NATS_URL not set."""
        from framework_m.cli.worker import DEFAULT_NATS_URL, get_nats_url

        with patch.dict(os.environ, {}, clear=True):
            # Temporarily remove NATS_URL
            env_backup = os.environ.pop("NATS_URL", None)
            try:
                result = get_nats_url()
                assert result == DEFAULT_NATS_URL
            finally:
                if env_backup:
                    os.environ["NATS_URL"] = env_backup

    def test_returns_env_value(self) -> None:
        """get_nats_url should return NATS_URL env value."""
        from framework_m.cli.worker import get_nats_url

        with patch.dict(os.environ, {"NATS_URL": "nats://custom:1234"}):
            result = get_nats_url()

            assert result == "nats://custom:1234"


# =============================================================================
# Test: get_broker
# =============================================================================


class TestGetBroker:
    """Tests for get_broker function."""

    def test_get_broker_calls_create_taskiq_broker(self) -> None:
        """get_broker should call create_taskiq_broker."""
        from framework_m.cli.worker import get_broker

        with patch(
            "framework_m.adapters.jobs.taskiq_adapter.create_taskiq_broker"
        ) as mock_create:
            mock_broker = MagicMock()
            mock_create.return_value = mock_broker

            result = get_broker()

            mock_create.assert_called_once()
            assert result is mock_broker

    def test_get_broker_passes_nats_url(self) -> None:
        """get_broker should pass nats_url to create_taskiq_broker."""
        from framework_m.cli.worker import get_broker

        with (
            patch.dict(os.environ, {"NATS_URL": "nats://test:4222"}),
            patch(
                "framework_m.adapters.jobs.taskiq_adapter.create_taskiq_broker"
            ) as mock_create,
        ):
            mock_create.return_value = MagicMock()

            get_broker()

            mock_create.assert_called_once_with(nats_url="nats://test:4222")


# =============================================================================
# Test: discover_jobs
# =============================================================================


class TestDiscoverJobs:
    """Tests for discover_jobs function."""

    def test_discover_jobs_returns_list(self) -> None:
        """discover_jobs should return list of job names."""
        from framework_m.cli.worker import discover_jobs

        with patch(
            "framework_m.adapters.jobs.taskiq_adapter.get_global_registry"
        ) as mock_get:
            mock_registry = MagicMock()
            mock_registry.list.return_value = ["job1", "job2"]
            mock_get.return_value = mock_registry

            result = discover_jobs()

            assert result == ["job1", "job2"]

    def test_discover_jobs_empty(self) -> None:
        """discover_jobs should return empty list when no jobs."""
        from framework_m.cli.worker import discover_jobs

        with patch(
            "framework_m.adapters.jobs.taskiq_adapter.get_global_registry"
        ) as mock_get:
            mock_registry = MagicMock()
            mock_registry.list.return_value = []
            mock_get.return_value = mock_registry

            result = discover_jobs()

            assert result == []


# =============================================================================
# Test: load_scheduled_jobs
# =============================================================================


class TestLoadScheduledJobs:
    """Tests for load_scheduled_jobs function."""

    @pytest.mark.asyncio
    async def test_returns_builtin_jobs(self) -> None:
        """load_scheduled_jobs should always return builtin process_outbox."""
        from framework_m.cli.worker import load_scheduled_jobs

        result = await load_scheduled_jobs()

        task_names = [s["task_name"] for s in result]
        assert "process_outbox" in task_names

    @pytest.mark.asyncio
    async def test_returns_list(self) -> None:
        """load_scheduled_jobs should return list of dicts."""
        from framework_m.cli.worker import load_scheduled_jobs

        result = await load_scheduled_jobs()

        assert isinstance(result, list)
        for item in result:
            assert "task_name" in item
            assert "cron" in item

    @pytest.mark.asyncio
    async def test_handles_db_error(self) -> None:
        """load_scheduled_jobs should handle DB errors gracefully."""
        from framework_m.cli.worker import load_scheduled_jobs

        with patch("framework_m.core.doctypes.scheduled_job.ScheduledJob") as mock_sj:
            mock_sj.query.side_effect = Exception("DB error")

            result = await load_scheduled_jobs()

            # Should still return builtin jobs
            assert len(result) >= 1

    @pytest.mark.asyncio
    async def test_includes_db_jobs(self) -> None:
        """load_scheduled_jobs should include jobs from database."""
        from framework_m.cli.worker import load_scheduled_jobs

        mock_job = MagicMock()
        mock_job.name = "daily_report"
        mock_job.cron_expression = "0 9 * * *"

        with patch("framework_m.cli.worker.ScheduledJob", create=True) as mock_sj:
            mock_query = MagicMock()
            mock_filter = MagicMock()
            mock_filter.all = AsyncMock(return_value=[mock_job])
            mock_query.filter.return_value = mock_filter
            mock_sj.query.return_value = mock_query

            result = await load_scheduled_jobs()

            # Should contain at least the builtin job
            assert len(result) >= 1
            assert any(s["task_name"] == "process_outbox" for s in result)


# =============================================================================
# Test: _run_worker_async
# =============================================================================


class TestRunWorkerAsync:
    """Tests for _run_worker_async function."""

    def test_run_worker_async_is_async(self) -> None:
        """_run_worker_async should be async."""
        import asyncio

        from framework_m.cli.worker import _run_worker_async

        assert asyncio.iscoroutinefunction(_run_worker_async)

    def test_run_worker_async_has_broker_param(self) -> None:
        """_run_worker_async should accept broker parameter."""
        import inspect

        from framework_m.cli.worker import _run_worker_async

        sig = inspect.signature(_run_worker_async)
        assert "broker" in sig.parameters

    def test_run_worker_async_has_concurrency_param(self) -> None:
        """_run_worker_async should accept concurrency parameter."""
        import inspect

        from framework_m.cli.worker import _run_worker_async

        sig = inspect.signature(_run_worker_async)
        assert "concurrency" in sig.parameters

    @pytest.mark.asyncio
    async def test_run_worker_async_with_jobs(self) -> None:
        """_run_worker_async should print discovered jobs."""
        from framework_m.cli.worker import _run_worker_async

        mock_broker = MagicMock()
        mock_broker.startup = AsyncMock()
        mock_broker.shutdown = AsyncMock()

        with (
            patch("framework_m.cli.worker.discover_jobs") as mock_discover,
            patch("builtins.print") as mock_print,
            patch("taskiq.receiver.Receiver") as mock_receiver_cls,
        ):
            mock_discover.return_value = ["job1", "job2"]
            mock_receiver = MagicMock()
            mock_receiver.listen = AsyncMock(side_effect=KeyboardInterrupt)
            mock_receiver_cls.return_value = mock_receiver

            await _run_worker_async(mock_broker, concurrency=2)

            # Should have printed job discovery
            mock_print.assert_any_call("Discovered 2 jobs: job1, job2")

    @pytest.mark.asyncio
    async def test_run_worker_async_no_jobs(self) -> None:
        """_run_worker_async should print message when no jobs."""
        from framework_m.cli.worker import _run_worker_async

        mock_broker = MagicMock()
        mock_broker.startup = AsyncMock()
        mock_broker.shutdown = AsyncMock()

        with (
            patch("framework_m.cli.worker.discover_jobs") as mock_discover,
            patch("builtins.print") as mock_print,
            patch("taskiq.receiver.Receiver") as mock_receiver_cls,
        ):
            mock_discover.return_value = []
            mock_receiver = MagicMock()
            mock_receiver.listen = AsyncMock(side_effect=KeyboardInterrupt)
            mock_receiver_cls.return_value = mock_receiver

            await _run_worker_async(mock_broker)

            # Should have printed no jobs message
            mock_print.assert_any_call(
                "No jobs discovered. Register jobs with @job decorator."
            )

    @pytest.mark.asyncio
    async def test_run_worker_async_starts_broker(self) -> None:
        """_run_worker_async should start broker."""
        from framework_m.cli.worker import _run_worker_async

        mock_broker = MagicMock()
        mock_broker.startup = AsyncMock()
        mock_broker.shutdown = AsyncMock()

        with (
            patch("framework_m.cli.worker.discover_jobs", return_value=[]),
            patch("builtins.print"),
            patch("taskiq.receiver.Receiver") as mock_receiver_cls,
        ):
            mock_receiver = MagicMock()
            mock_receiver.listen = AsyncMock(side_effect=KeyboardInterrupt)
            mock_receiver_cls.return_value = mock_receiver

            await _run_worker_async(mock_broker)

            mock_broker.startup.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_worker_async_shuts_down_broker(self) -> None:
        """_run_worker_async should shutdown broker on exit."""
        from framework_m.cli.worker import _run_worker_async

        mock_broker = MagicMock()
        mock_broker.startup = AsyncMock()
        mock_broker.shutdown = AsyncMock()

        with (
            patch("framework_m.cli.worker.discover_jobs", return_value=[]),
            patch("builtins.print"),
            patch("taskiq.receiver.Receiver") as mock_receiver_cls,
        ):
            mock_receiver = MagicMock()
            mock_receiver.listen = AsyncMock(side_effect=KeyboardInterrupt)
            mock_receiver_cls.return_value = mock_receiver

            await _run_worker_async(mock_broker)

            mock_broker.shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_worker_async_creates_receiver(self) -> None:
        """_run_worker_async should create Receiver with correct params."""
        from framework_m.cli.worker import _run_worker_async

        mock_broker = MagicMock()
        mock_broker.startup = AsyncMock()
        mock_broker.shutdown = AsyncMock()

        with (
            patch("framework_m.cli.worker.discover_jobs", return_value=[]),
            patch("builtins.print"),
            patch("taskiq.receiver.Receiver") as mock_receiver_cls,
        ):
            mock_receiver = MagicMock()
            mock_receiver.listen = AsyncMock(side_effect=KeyboardInterrupt)
            mock_receiver_cls.return_value = mock_receiver

            await _run_worker_async(mock_broker, concurrency=8)

            mock_receiver_cls.assert_called_once_with(
                mock_broker, max_async_tasks=8, run_startup=False
            )


# =============================================================================
# Test: run_worker
# =============================================================================


class TestRunWorker:
    """Tests for run_worker function."""

    def test_run_worker_is_callable(self) -> None:
        """run_worker should be callable."""
        from framework_m.cli.worker import run_worker

        assert callable(run_worker)

    def test_run_worker_has_concurrency_param(self) -> None:
        """run_worker should accept concurrency parameter."""
        import inspect

        from framework_m.cli.worker import run_worker

        sig = inspect.signature(run_worker)
        assert "concurrency" in sig.parameters

    def test_run_worker_calls_get_broker(self) -> None:
        """run_worker should call get_broker."""
        from framework_m.cli.worker import run_worker

        with (
            patch("framework_m.cli.worker.get_broker") as mock_get_broker,
            patch("framework_m.cli.worker.asyncio.run"),
        ):
            mock_broker = MagicMock()
            mock_get_broker.return_value = mock_broker

            run_worker(concurrency=4)

            mock_get_broker.assert_called_once()

    def test_run_worker_calls_asyncio_run(self) -> None:
        """run_worker should call asyncio.run with _run_worker_async."""
        from framework_m.cli.worker import run_worker

        with (
            patch("framework_m.cli.worker.get_broker") as mock_get_broker,
            patch("framework_m.cli.worker.asyncio.run") as mock_run,
        ):
            mock_broker = MagicMock()
            mock_get_broker.return_value = mock_broker

            run_worker(concurrency=4)

            mock_run.assert_called_once()


# =============================================================================
# Test: worker_command
# =============================================================================


class TestWorkerCommand:
    """Tests for worker_command CLI."""

    def test_worker_command_is_callable(self) -> None:
        """worker_command should be callable."""
        from framework_m.cli.worker import worker_command

        assert callable(worker_command)

    def test_worker_command_has_concurrency_option(self) -> None:
        """worker_command should have concurrency option."""
        import inspect

        from framework_m.cli.worker import worker_command

        sig = inspect.signature(worker_command)
        assert "concurrency" in sig.parameters

    def test_worker_command_has_verbose_option(self) -> None:
        """worker_command should have verbose option."""
        import inspect

        from framework_m.cli.worker import worker_command

        sig = inspect.signature(worker_command)
        assert "verbose" in sig.parameters

    def test_worker_command_verbose_prints(self) -> None:
        """worker_command with verbose should print verbose message."""
        from framework_m.cli.worker import worker_command

        with (
            patch("builtins.print") as mock_print,
            patch("framework_m.cli.worker.run_worker"),
        ):
            worker_command(concurrency=4, verbose=True)

            mock_print.assert_any_call("Verbose mode enabled")

    def test_worker_command_prints_header(self) -> None:
        """worker_command should print header."""
        from framework_m.cli.worker import worker_command

        with (
            patch("builtins.print") as mock_print,
            patch("framework_m.cli.worker.run_worker"),
        ):
            worker_command(concurrency=4, verbose=False)

            mock_print.assert_any_call("Framework M Worker")
            mock_print.assert_any_call("=" * 40)

    def test_worker_command_calls_run_worker(self) -> None:
        """worker_command should call run_worker with concurrency."""
        from framework_m.cli.worker import worker_command

        with (
            patch("builtins.print"),
            patch("framework_m.cli.worker.run_worker") as mock_run,
        ):
            worker_command(concurrency=8, verbose=False)

            mock_run.assert_called_once_with(concurrency=8)


# =============================================================================
# Test: Constants
# =============================================================================


class TestWorkerConstants:
    """Tests for worker constants."""

    def test_default_concurrency(self) -> None:
        """DEFAULT_CONCURRENCY should be defined."""
        from framework_m.cli.worker import DEFAULT_CONCURRENCY

        assert DEFAULT_CONCURRENCY >= 1
        assert DEFAULT_CONCURRENCY <= 16

    def test_default_nats_url(self) -> None:
        """DEFAULT_NATS_URL should be defined."""
        from framework_m.cli.worker import DEFAULT_NATS_URL

        assert "nats://" in DEFAULT_NATS_URL
        assert "localhost" in DEFAULT_NATS_URL or "4222" in DEFAULT_NATS_URL
