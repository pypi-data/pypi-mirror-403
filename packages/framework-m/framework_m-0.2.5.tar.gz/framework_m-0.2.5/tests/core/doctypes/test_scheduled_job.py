"""Tests for ScheduledJob DocType."""

from datetime import UTC, datetime

# =============================================================================
# Test: ScheduledJob DocType
# =============================================================================


class TestScheduledJobDocType:
    """Tests for ScheduledJob DocType."""

    def test_import_scheduled_job(self) -> None:
        """ScheduledJob should be importable."""
        from framework_m.core.doctypes.scheduled_job import ScheduledJob

        assert ScheduledJob is not None

    def test_scheduled_job_creation(self) -> None:
        """ScheduledJob should be creatable with required fields."""
        from framework_m.core.doctypes.scheduled_job import ScheduledJob

        job = ScheduledJob(
            name="daily_report",
            function="myapp.jobs.send_report",
            cron_expression="0 9 * * *",
        )

        assert job.name == "daily_report"
        assert job.function == "myapp.jobs.send_report"
        assert job.cron_expression == "0 9 * * *"
        assert job.enabled is True  # Default
        assert job.last_run is None
        assert job.next_run is None

    def test_scheduled_job_with_optional_fields(self) -> None:
        """ScheduledJob should accept optional fields."""
        from framework_m.core.doctypes.scheduled_job import ScheduledJob

        now = datetime.now(UTC)
        job = ScheduledJob(
            name="test_job",
            function="test.job",
            cron_expression="* * * * *",
            enabled=False,
            last_run=now,
            next_run=now,
        )

        assert job.enabled is False
        assert job.last_run == now
        assert job.next_run == now

    def test_scheduled_job_disabled_by_default_false(self) -> None:
        """ScheduledJob.enabled should default to True."""
        from framework_m.core.doctypes.scheduled_job import ScheduledJob

        job = ScheduledJob(
            name="test",
            function="test.func",
            cron_expression="0 0 * * *",
        )

        assert job.enabled is True

    def test_scheduled_job_has_meta(self) -> None:
        """ScheduledJob should have Meta configuration."""
        from framework_m.core.doctypes.scheduled_job import ScheduledJob

        assert hasattr(ScheduledJob, "Meta")
        # Should have table_name configured
        # Note: Implementation may vary based on BaseDocType
