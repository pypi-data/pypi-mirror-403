"""Tests for dynamic schedule loading."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

# =============================================================================
# Test: load_scheduled_jobs Function
# =============================================================================


class TestLoadScheduledJobs:
    """Tests for load_scheduled_jobs() function."""

    def test_import_load_scheduled_jobs(self) -> None:
        """load_scheduled_jobs should be importable."""
        from framework_m.cli.worker import load_scheduled_jobs

        assert load_scheduled_jobs is not None

    @pytest.mark.asyncio
    async def test_load_scheduled_jobs_returns_list(self) -> None:
        """load_scheduled_jobs should return list of schedule dicts."""
        from framework_m.cli.worker import load_scheduled_jobs

        # Mock the ScheduledJob at its import location
        with patch(
            "framework_m.core.doctypes.scheduled_job.ScheduledJob"
        ) as MockScheduledJob:
            # Mock the query chain
            mock_query = Mock()
            mock_filter = Mock()
            mock_filter.all = AsyncMock(return_value=[])
            mock_query.filter = Mock(return_value=mock_filter)
            MockScheduledJob.query = Mock(return_value=mock_query)

            schedules = await load_scheduled_jobs()

            assert isinstance(schedules, list)

    @pytest.mark.asyncio
    async def test_load_scheduled_jobs_filters_enabled(self) -> None:
        """load_scheduled_jobs should only return enabled jobs."""
        from framework_m.cli.worker import load_scheduled_jobs

        # Create mock jobs
        mock_job = Mock()
        mock_job.name = "test_job"
        mock_job.cron_expression = "0 9 * * *"
        mock_job.enabled = True

        with patch(
            "framework_m.core.doctypes.scheduled_job.ScheduledJob"
        ) as MockScheduledJob:
            mock_query = Mock()
            mock_filter = Mock()
            mock_filter.all = AsyncMock(return_value=[mock_job])
            mock_query.filter = Mock(return_value=mock_filter)
            MockScheduledJob.query = Mock(return_value=mock_query)

            schedules = await load_scheduled_jobs()

            # Should call filter with enabled=True
            mock_query.filter.assert_called_once()
            # 1 built-in (process_outbox) + 1 from DB
            assert len(schedules) >= 2
            task_names = [s["task_name"] for s in schedules]
            assert "test_job" in task_names
            assert "process_outbox" in task_names

    @pytest.mark.asyncio
    async def test_load_scheduled_jobs_empty_database(self) -> None:
        """load_scheduled_jobs should handle empty database (still has built-in jobs)."""
        from framework_m.cli.worker import load_scheduled_jobs

        with patch(
            "framework_m.core.doctypes.scheduled_job.ScheduledJob"
        ) as MockScheduledJob:
            mock_query = Mock()
            mock_filter = Mock()
            mock_filter.all = AsyncMock(return_value=[])
            mock_query.filter = Mock(return_value=mock_filter)
            MockScheduledJob.query = Mock(return_value=mock_query)

            schedules = await load_scheduled_jobs()

            # Should still have built-in process_outbox job
            assert len(schedules) >= 1
            task_names = [s["task_name"] for s in schedules]
            assert "process_outbox" in task_names

    @pytest.mark.asyncio
    async def test_load_scheduled_jobs_multiple_jobs(self) -> None:
        """load_scheduled_jobs should handle multiple jobs."""
        from framework_m.cli.worker import load_scheduled_jobs

        # Mock multiple jobs
        job1 = Mock()
        job1.name = "job1"
        job1.cron_expression = "0 9 * * *"

        job2 = Mock()
        job2.name = "job2"
        job2.cron_expression = "0 10 * * *"

        with patch(
            "framework_m.core.doctypes.scheduled_job.ScheduledJob"
        ) as MockScheduledJob:
            mock_query = Mock()
            mock_filter = Mock()
            mock_filter.all = AsyncMock(return_value=[job1, job2])
            mock_query.filter = Mock(return_value=mock_filter)
            MockScheduledJob.query = Mock(return_value=mock_query)

            schedules = await load_scheduled_jobs()

            # 1 built-in + 2 from DB = 3
            assert len(schedules) >= 3
            task_names = [s["task_name"] for s in schedules]
            assert "job1" in task_names
            assert "job2" in task_names
            assert "process_outbox" in task_names
