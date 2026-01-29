"""ScheduledJob DocType - Persistent cron job definitions.

Stores scheduled job configurations in the database, enabling
dynamic job scheduling without code changes.

Example:
    # Create a daily report job
    job = ScheduledJob(
        name="daily_report",
        function="myapp.jobs.send_daily_report",
        cron_expression="0 9 * * *",
        enabled=True,
    )

    # Query enabled jobs
    active_jobs = await ScheduledJob.query().filter(enabled=True).all()
"""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from pydantic import Field

from framework_m.core.domain.base_doctype import BaseDocType


class ScheduledJob(BaseDocType):
    """Persistent scheduled job configuration.

    Stores cron job definitions that are loaded by the worker
    process at startup, enabling dynamic job scheduling.

    Attributes:
        name: Unique job identifier
        function: Dotted path to job function (e.g., 'myapp.jobs.send_email')
        cron_expression: Cron syntax string (e.g., '0 9 * * *')
        enabled: Whether the job is active
        last_run: Timestamp of last execution (updated by worker)
        next_run: Timestamp of next scheduled run (calculated)
    """

    # Job identification
    name: str = Field(
        ...,
        description="Unique job identifier",
        min_length=1,
        max_length=255,
    )

    function: str = Field(
        ...,
        description="Dotted path to job function (e.g., 'myapp.jobs.send_email')",
        min_length=1,
    )

    # Schedule configuration
    cron_expression: str = Field(
        ...,
        description="Cron syntax (e.g., '0 9 * * *' for daily at 9 AM)",
        min_length=1,
    )

    enabled: bool = Field(
        default=True,
        description="Whether the job is active and should be scheduled",
    )

    # Execution tracking
    last_run: datetime | None = Field(
        default=None,
        description="Timestamp of last execution (set by worker)",
    )

    next_run: datetime | None = Field(
        default=None,
        description="Timestamp of next scheduled run (calculated)",
    )

    class Meta:
        """DocType metadata configuration."""

        # Authentication and authorization
        requires_auth: ClassVar[bool] = True
        apply_rls: ClassVar[bool] = True

        # Permissions
        permissions: ClassVar[dict[str, list[str]]] = {
            "read": ["Employee", "Manager", "Admin"],
            "write": ["Manager", "Admin"],
            "create": ["Manager", "Admin"],
            "delete": ["Admin"],
        }


__all__ = ["ScheduledJob"]
