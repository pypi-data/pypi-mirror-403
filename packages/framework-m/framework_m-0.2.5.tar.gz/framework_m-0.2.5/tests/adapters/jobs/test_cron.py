"""Tests for cron job scheduling functionality."""


# =============================================================================
# Test: Cron Helper Function
# =============================================================================


class TestCronHelper:
    """Tests for cron() helper function."""

    def test_import_cron(self) -> None:
        """cron should be importable."""
        from framework_m.adapters.jobs.taskiq_adapter import cron

        assert cron is not None

    def test_cron_creates_schedule_source(self) -> None:
        """cron should create a schedule definition dict."""
        from framework_m.adapters.jobs.taskiq_adapter import cron

        # Create a cron schedule
        schedule = cron("test_job", hour=9, minute=0)

        # Should return a dict with task_name and cron
        assert isinstance(schedule, dict)
        assert schedule["task_name"] == "test_job"
        assert schedule["cron"] == "0 9 * * *"

    def test_cron_with_all_parameters(self) -> None:
        """cron should accept all cron parameters."""
        from framework_m.adapters.jobs.taskiq_adapter import cron

        schedule = cron(
            "complex_job",
            hour=9,
            minute=30,
            day=15,
            month=6,
            day_of_week=1,
        )

        assert schedule is not None

    def test_cron_with_wildcard_strings(self) -> None:
        """cron should accept wildcard strings."""
        from framework_m.adapters.jobs.taskiq_adapter import cron

        # Every 6 hours
        schedule = cron("periodic_job", hour="*/6", minute=0)

        assert schedule is not None

    def test_cron_default_values(self) -> None:
        """cron should use wildcards as defaults."""
        from framework_m.adapters.jobs.taskiq_adapter import cron

        # Only specify hour, rest should default to *
        schedule = cron("hourly_job", hour=10)

        assert schedule is not None


# =============================================================================
# Test: Cron Expression Generation
# =============================================================================


class TestCronExpression:
    """Tests for cron expression building."""

    def test_build_cron_expression(self) -> None:
        """build_cron_expression should create valid cron strings."""
        from framework_m.adapters.jobs.taskiq_adapter import build_cron_expression

        # Daily at 9:00 AM
        expr = build_cron_expression(hour=9, minute=0)
        assert expr == "0 9 * * *"

    def test_build_cron_all_wildcards(self) -> None:
        """build_cron_expression with no args should return all wildcards."""
        from framework_m.adapters.jobs.taskiq_adapter import build_cron_expression

        expr = build_cron_expression()
        assert expr == "* * * * *"

    def test_build_cron_complex(self) -> None:
        """build_cron_expression should handle complex expressions."""
        from framework_m.adapters.jobs.taskiq_adapter import build_cron_expression

        # Every Monday at 2:30 PM on the 15th
        expr = build_cron_expression(
            minute=30, hour=14, day=15, month="*", day_of_week=1
        )
        assert expr == "30 14 15 * 1"

    def test_build_cron_with_ranges(self) -> None:
        """build_cron_expression should handle range strings."""
        from framework_m.adapters.jobs.taskiq_adapter import build_cron_expression

        expr = build_cron_expression(hour="9-17", minute="*/15")
        assert expr == "*/15 9-17 * * *"
