"""Integration tests for Phase 04 - Jobs, Events, Webhooks.

These tests verify end-to-end functionality using in-memory adapters
or testcontainers for external dependencies.
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

# =============================================================================
# Test: Job Execution Integration
# =============================================================================


class TestJobExecutionIntegration:
    """Integration tests for job execution flow."""

    @pytest.mark.asyncio
    async def test_enqueue_and_execute_job(self) -> None:
        """Enqueue job, verify it runs, check result."""
        from framework_m.adapters.jobs import InMemoryJobQueue

        queue = InMemoryJobQueue()
        results: list[str] = []

        async def my_job(message: str) -> dict[str, str]:
            results.append(message)
            return {"status": "done"}

        queue.register_job("test_job", my_job)

        # Enqueue
        job_id = await queue.enqueue("test_job", message="hello")
        assert job_id is not None

        # Wait for execution
        await asyncio.sleep(0.1)

        # Verify job ran
        assert "hello" in results

        # Check result
        status = await queue.get_status(job_id)
        assert status is not None
        assert status.result == {"status": "done"}

    @pytest.mark.asyncio
    async def test_job_failure_captured(self) -> None:
        """Failed job should capture error."""
        from framework_m.adapters.jobs import InMemoryJobQueue
        from framework_m.core.interfaces.job_queue import JobStatus

        queue = InMemoryJobQueue()

        async def failing_job() -> None:
            raise ValueError("Intentional failure")

        queue.register_job("failing_job", failing_job)

        job_id = await queue.enqueue("failing_job")
        await asyncio.sleep(0.1)

        status = await queue.get_status(job_id)
        assert status is not None
        assert status.status == JobStatus.FAILED
        assert "Intentional failure" in (status.error or "")

    @pytest.mark.asyncio
    async def test_job_retry(self) -> None:
        """Failed job can be retried."""
        from framework_m.adapters.jobs import InMemoryJobQueue

        queue = InMemoryJobQueue()
        call_count = [0]

        async def retry_job() -> str:
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError("First attempt fails")
            return "success"

        queue.register_job("retry_job", retry_job)

        # First attempt fails
        job_id = await queue.enqueue("retry_job")
        await asyncio.sleep(0.1)

        # Retry
        new_job_id = await queue.retry(job_id)
        await asyncio.sleep(0.1)

        status = await queue.get_status(new_job_id)
        assert status is not None
        assert status.result == {"result": "success"}


# =============================================================================
# Test: Scheduled Jobs Integration
# =============================================================================


class TestScheduledJobsIntegration:
    """Integration tests for scheduled job execution."""

    def test_cron_expression_builder(self) -> None:
        """build_cron_expression should create valid cron strings."""
        from framework_m.adapters.jobs.taskiq_adapter import build_cron_expression

        # Every hour at minute 0
        expr = build_cron_expression(minute=0)
        assert expr == "0 * * * *"

        # Every day at 9am
        expr = build_cron_expression(minute=0, hour=9)
        assert expr == "0 9 * * *"

        # Every Monday at 2pm
        expr = build_cron_expression(minute=0, hour=14, day_of_week=1)
        assert expr == "0 14 * * 1"

    def test_cron_schedule_registration(self) -> None:
        """cron() should return schedule definition."""
        from framework_m.adapters.jobs.taskiq_adapter import cron

        schedule = cron("daily_report", hour=6, minute=0)

        assert schedule["task_name"] == "daily_report"
        assert schedule["cron"] == "0 6 * * *"


# =============================================================================
# Test: Webhook Integration
# =============================================================================


class TestWebhookIntegration:
    """Integration tests for webhook system."""

    @pytest.mark.asyncio
    async def test_webhook_delivery_flow(self) -> None:
        """Create webhook, trigger event, verify HTTP call."""
        from framework_m.adapters.webhooks import HttpWebhookDeliverer
        from framework_m.core.doctypes import Webhook
        from framework_m.core.interfaces.event_bus import Event

        # Create webhook (using correct field name: event not events)
        webhook = Webhook(
            name="test-webhook",
            event="doc.created",
            url="https://example.com/webhook",
            method="POST",
            enabled=True,
        )

        # Create event to deliver
        event = Event(type="doc.created", source="test")

        # Mock HTTP delivery
        deliverer = HttpWebhookDeliverer()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client

            # deliver() takes webhook and event
            await deliverer.deliver(webhook, event)

            # Verify HTTP call was made
            mock_client.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_webhook_with_signature(self) -> None:
        """Webhook with secret should include signature header."""
        from framework_m.adapters.webhooks import generate_signature
        from framework_m.core.doctypes import Webhook

        webhook = Webhook(
            name="signed-webhook",
            event="doc.created",
            url="https://example.com/webhook",
            method="POST",
            enabled=True,
            secret="my-secret-key",
        )

        # generate_signature takes bytes, not str
        payload = b'{"test": "data"}'
        signature = generate_signature(payload, webhook.secret or "")

        assert signature is not None
        # HMAC-SHA256 produces 64-char hex string
        assert len(signature) == 64


# =============================================================================
# Test: Event Bus Integration
# =============================================================================


class TestEventBusIntegration:
    """Integration tests for event bus."""

    @pytest.mark.asyncio
    async def test_event_bus_connect_disconnect(self) -> None:
        """Event bus should track connection state."""
        from framework_m.adapters.events import InMemoryEventBus

        bus = InMemoryEventBus()

        # Initially not connected
        assert bus.is_connected() is False

        await bus.connect()
        assert bus.is_connected() is True

        await bus.disconnect()
        assert bus.is_connected() is False

    @pytest.mark.asyncio
    async def test_subscribe_returns_subscription_id(self) -> None:
        """Subscribe should return a subscription ID."""
        from framework_m.adapters.events import InMemoryEventBus
        from framework_m.core.interfaces.event_bus import Event

        bus = InMemoryEventBus()
        await bus.connect()

        async def handler(event: Event) -> None:
            pass

        sub_id = await bus.subscribe("doc.*", handler)

        # Subscription should return an ID
        assert sub_id is not None
        assert isinstance(sub_id, str)


# =============================================================================
# Test: JobLogger Integration
# =============================================================================


class TestJobLoggerIntegration:
    """Integration tests for job logging."""

    @pytest.mark.asyncio
    async def test_job_lifecycle_logging(self) -> None:
        """Job should be logged through entire lifecycle."""
        from framework_m.adapters.jobs import JobLogger

        logger = JobLogger()

        # Enqueue
        log = await logger.log_enqueue("job-123", "send_email")
        assert log.status == "queued"
        assert log.enqueued_at is not None

        # Start
        log = await logger.log_start("job-123")
        assert log is not None
        assert log.status == "running"
        assert log.started_at is not None

        # Success
        log = await logger.log_success("job-123", result={"sent": 42})
        assert log is not None
        assert log.status == "success"
        assert log.completed_at is not None
        assert log.result == {"sent": 42}

    @pytest.mark.asyncio
    async def test_job_failure_logging(self) -> None:
        """Failed job should log error."""
        from framework_m.adapters.jobs import JobLogger

        logger = JobLogger()

        await logger.log_enqueue("job-456", "failing_job")
        await logger.log_start("job-456")

        log = await logger.log_failure("job-456", error="Connection refused")
        assert log is not None
        assert log.status == "failed"
        assert log.error == "Connection refused"
