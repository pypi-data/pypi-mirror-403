"""Example scheduled jobs using cron syntax.

This module defines scheduled jobs that will be loaded by the worker
at startup. Jobs are scheduled using the cron() helper function.

To start the scheduler:
    m worker

The worker will automatically load and register these schedules.
"""

from framework_m.adapters.jobs.taskiq_adapter import cron

# Example scheduled jobs
# These are definition dictionaries that will be loaded into Taskiq's scheduler

SCHEDULES = [
    # Daily report at 9:00 AM
    cron("send_daily_report", hour=9, minute=0),
    # Cleanup old files at 2:00 AM
    cron("cleanup_old_files", hour=2, minute=0),
    # Every 6 hours
    cron("periodic_health_check", hour="*/6", minute=0),
    # Weekly summary on Monday at 10:00 AM
    cron("send_weekly_summary", hour=10, minute=0, day_of_week=1),
]


# Note: The actual job functions must be registered using @job decorator
# Example:
#
# from framework_m.adapters.jobs.taskiq_adapter import job
#
# @job(name="send_daily_report")
# async def send_daily_report() -> bool:
#     """Send daily report to all users."""
#     # Job implementation
#     return True
