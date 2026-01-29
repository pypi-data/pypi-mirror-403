"""Tests for example scheduled jobs module."""


class TestSchedulesModule:
    """Tests for schedules.py example module."""

    def test_import_schedules(self) -> None:
        """SCHEDULES should be importable."""
        from framework_m.adapters.jobs.schedules import SCHEDULES

        assert SCHEDULES is not None

    def test_schedules_is_list(self) -> None:
        """SCHEDULES should be a list."""
        from framework_m.adapters.jobs.schedules import SCHEDULES

        assert isinstance(SCHEDULES, list)

    def test_schedules_has_entries(self) -> None:
        """SCHEDULES should contain schedule definitions."""
        from framework_m.adapters.jobs.schedules import SCHEDULES

        assert len(SCHEDULES) >= 4

    def test_schedule_entries_have_task_name(self) -> None:
        """Each schedule should have task_name."""
        from framework_m.adapters.jobs.schedules import SCHEDULES

        for schedule in SCHEDULES:
            assert "task_name" in schedule

    def test_schedule_entries_have_cron(self) -> None:
        """Each schedule should have cron expression."""
        from framework_m.adapters.jobs.schedules import SCHEDULES

        for schedule in SCHEDULES:
            assert "cron" in schedule

    def test_daily_report_schedule(self) -> None:
        """Daily report schedule should be at 9:00 AM."""
        from framework_m.adapters.jobs.schedules import SCHEDULES

        daily_report = next(
            s for s in SCHEDULES if s["task_name"] == "send_daily_report"
        )
        assert daily_report["cron"] == "0 9 * * *"

    def test_cleanup_schedule(self) -> None:
        """Cleanup schedule should be at 2:00 AM."""
        from framework_m.adapters.jobs.schedules import SCHEDULES

        cleanup = next(s for s in SCHEDULES if s["task_name"] == "cleanup_old_files")
        assert cleanup["cron"] == "0 2 * * *"

    def test_health_check_schedule(self) -> None:
        """Health check should run every 6 hours."""
        from framework_m.adapters.jobs.schedules import SCHEDULES

        health_check = next(
            s for s in SCHEDULES if s["task_name"] == "periodic_health_check"
        )
        assert health_check["cron"] == "0 */6 * * *"

    def test_weekly_summary_schedule(self) -> None:
        """Weekly summary should be on Monday at 10:00 AM."""
        from framework_m.adapters.jobs.schedules import SCHEDULES

        weekly = next(s for s in SCHEDULES if s["task_name"] == "send_weekly_summary")
        assert weekly["cron"] == "0 10 * * 1"
