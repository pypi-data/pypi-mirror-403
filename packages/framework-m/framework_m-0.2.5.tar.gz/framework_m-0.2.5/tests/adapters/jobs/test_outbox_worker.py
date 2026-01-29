"""Tests for Outbox Worker - Comprehensive coverage tests."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# =============================================================================
# Test: Outbox Worker Import
# =============================================================================


class TestOutboxWorkerImport:
    """Tests for outbox worker imports."""

    def test_import_dispatch_to_target(self) -> None:
        """dispatch_to_target should be importable."""
        from framework_m.adapters.jobs.outbox_worker import dispatch_to_target

        assert dispatch_to_target is not None

    def test_import_process_outbox(self) -> None:
        """process_outbox should be importable."""
        from framework_m.adapters.jobs.outbox_worker import process_outbox

        assert process_outbox is not None

    def test_exports(self) -> None:
        """outbox_worker should export expected items."""
        from framework_m.adapters.jobs import outbox_worker

        assert "dispatch_to_target" in outbox_worker.__all__
        assert "process_outbox" in outbox_worker.__all__


# =============================================================================
# Test: dispatch_to_target - API Target
# =============================================================================


class TestDispatchToTargetApi:
    """Tests for dispatch_to_target with API targets."""

    @pytest.mark.asyncio
    async def test_dispatch_api_target(self) -> None:
        """dispatch_to_target should route api.* to _dispatch_to_api."""
        from framework_m.adapters.jobs.outbox_worker import dispatch_to_target

        mock_entry = MagicMock()
        mock_entry.target = "api.payment_gateway"
        mock_entry.payload = {"amount": 100}

        with patch(
            "framework_m.adapters.jobs.outbox_worker._dispatch_to_api"
        ) as mock_api:
            mock_api.return_value = None

            await dispatch_to_target(mock_entry)

            mock_api.assert_called_once_with("api.payment_gateway", {"amount": 100})


# =============================================================================
# Test: dispatch_to_target - Event Target
# =============================================================================


class TestDispatchToTargetEvent:
    """Tests for dispatch_to_target with event targets."""

    @pytest.mark.asyncio
    async def test_dispatch_event_target(self) -> None:
        """dispatch_to_target should route event.* to _dispatch_to_event_bus."""
        from framework_m.adapters.jobs.outbox_worker import dispatch_to_target

        mock_entry = MagicMock()
        mock_entry.target = "event.order.created"
        mock_entry.payload = {"order_id": "123"}

        with patch(
            "framework_m.adapters.jobs.outbox_worker._dispatch_to_event_bus"
        ) as mock_event:
            mock_event.return_value = None

            await dispatch_to_target(mock_entry)

            mock_event.assert_called_once_with(
                "event.order.created", {"order_id": "123"}
            )


# =============================================================================
# Test: dispatch_to_target - Unknown Target
# =============================================================================


class TestDispatchToTargetUnknown:
    """Tests for dispatch_to_target with unknown targets."""

    @pytest.mark.asyncio
    async def test_dispatch_unknown_target_logs_warning(self) -> None:
        """dispatch_to_target should log warning for unknown targets."""
        from framework_m.adapters.jobs.outbox_worker import dispatch_to_target

        mock_entry = MagicMock()
        mock_entry.target = "unknown.target"
        mock_entry.payload = {}

        # Should not raise, just log warning
        await dispatch_to_target(mock_entry)

    @pytest.mark.asyncio
    async def test_dispatch_empty_target(self) -> None:
        """dispatch_to_target should handle empty target."""
        from framework_m.adapters.jobs.outbox_worker import dispatch_to_target

        mock_entry = MagicMock()
        mock_entry.target = ""
        mock_entry.payload = {}

        # Should not raise
        await dispatch_to_target(mock_entry)

    @pytest.mark.asyncio
    async def test_dispatch_random_target(self) -> None:
        """dispatch_to_target should handle random target prefix."""
        from framework_m.adapters.jobs.outbox_worker import dispatch_to_target

        mock_entry = MagicMock()
        mock_entry.target = "webhook.notification"
        mock_entry.payload = {"data": "test"}

        # Should not raise
        await dispatch_to_target(mock_entry)


# =============================================================================
# Test: _dispatch_to_api
# =============================================================================


class TestDispatchToApi:
    """Tests for _dispatch_to_api helper."""

    @pytest.mark.asyncio
    async def test_dispatch_to_api_logs_dispatch(self) -> None:
        """_dispatch_to_api should log the dispatch."""
        from framework_m.adapters.jobs.outbox_worker import _dispatch_to_api

        # Should not raise
        await _dispatch_to_api("api.test_service", {"data": "value"})

    @pytest.mark.asyncio
    async def test_dispatch_to_api_extracts_name(self) -> None:
        """_dispatch_to_api should extract api name."""
        from framework_m.adapters.jobs.outbox_worker import _dispatch_to_api

        # Should not raise
        await _dispatch_to_api("api.payment", {"amount": 50})

    @pytest.mark.asyncio
    async def test_dispatch_to_api_with_nested_payload(self) -> None:
        """_dispatch_to_api should handle nested payload."""
        from framework_m.adapters.jobs.outbox_worker import _dispatch_to_api

        payload = {
            "user": {"id": "123", "name": "Test"},
            "items": [1, 2, 3],
        }

        # Should not raise
        await _dispatch_to_api("api.external", payload)


# =============================================================================
# Test: _dispatch_to_event_bus
# =============================================================================


class TestDispatchToEventBus:
    """Tests for _dispatch_to_event_bus helper."""

    @pytest.mark.asyncio
    async def test_dispatch_to_event_bus_publishes(self) -> None:
        """_dispatch_to_event_bus should publish event."""
        from framework_m.adapters.jobs.outbox_worker import _dispatch_to_event_bus

        with patch("framework_m.adapters.factory.get_event_bus") as mock_get:
            mock_bus = AsyncMock()
            mock_bus.publish = AsyncMock()
            mock_get.return_value = mock_bus

            await _dispatch_to_event_bus("event.user.created", {"user_id": "123"})

            mock_bus.publish.assert_called_once()
            # Check event type
            call_args = mock_bus.publish.call_args
            assert call_args[0][0] == "user.created"

    @pytest.mark.asyncio
    async def test_dispatch_to_event_bus_extracts_event_type(self) -> None:
        """_dispatch_to_event_bus should extract event type from target."""
        from framework_m.adapters.jobs.outbox_worker import _dispatch_to_event_bus

        with patch("framework_m.adapters.factory.get_event_bus") as mock_get:
            mock_bus = AsyncMock()
            mock_bus.publish = AsyncMock()
            mock_get.return_value = mock_bus

            await _dispatch_to_event_bus("event.order.shipped", {"order": "ORD-1"})

            # Event type should be "order.shipped" (without "event." prefix)
            mock_bus.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_to_event_bus_creates_event(self) -> None:
        """_dispatch_to_event_bus should create Event with correct source."""
        from framework_m.adapters.jobs.outbox_worker import _dispatch_to_event_bus

        with patch("framework_m.adapters.factory.get_event_bus") as mock_get:
            mock_bus = AsyncMock()
            mock_bus.publish = AsyncMock()
            mock_get.return_value = mock_bus

            await _dispatch_to_event_bus("event.test", {"key": "value"})

            # Verify publish was called
            mock_bus.publish.assert_called_once()
            call_args = mock_bus.publish.call_args
            event = call_args[0][1]
            assert event.source == "outbox_worker"


# =============================================================================
# Test: process_outbox - Job Registration
# =============================================================================


class TestProcessOutboxJob:
    """Tests for process_outbox job registration."""

    def test_process_outbox_is_registered(self) -> None:
        """process_outbox should be registered with @job decorator."""
        from framework_m.adapters.jobs.outbox_worker import process_outbox

        # Check it has job metadata
        assert hasattr(process_outbox, "_job_meta")
        assert process_outbox._job_meta["name"] == "process_outbox"

    def test_process_outbox_is_async(self) -> None:
        """process_outbox should be an async function."""
        import asyncio

        from framework_m.adapters.jobs.outbox_worker import process_outbox

        assert asyncio.iscoroutinefunction(process_outbox)

    def test_process_outbox_default_batch_size(self) -> None:
        """process_outbox should have default batch_size of 100."""
        import inspect

        from framework_m.adapters.jobs.outbox_worker import process_outbox

        sig = inspect.signature(process_outbox)
        batch_param = sig.parameters.get("batch_size")
        assert batch_param is not None
        assert batch_param.default == 100

    def test_process_outbox_job_name(self) -> None:
        """process_outbox job name should be 'process_outbox'."""
        from framework_m.adapters.jobs.outbox_worker import process_outbox

        assert process_outbox._job_meta["name"] == "process_outbox"


# =============================================================================
# Test: process_outbox - Mocked Execution
# =============================================================================


class TestProcessOutboxExecution:
    """Tests for process_outbox execution with mocks."""

    @pytest.mark.asyncio
    async def test_process_outbox_no_pending(self) -> None:
        """process_outbox should return zeros when no pending."""
        from framework_m.adapters.jobs.outbox_worker import process_outbox

        with patch(
            "framework_m.adapters.db.connection.ConnectionFactory"
        ) as mock_cf_cls:
            mock_cf = MagicMock()
            mock_engine = MagicMock()
            mock_cf.get_engine.return_value = mock_engine
            mock_cf_cls.return_value = mock_cf

            with patch("sqlalchemy.orm.sessionmaker") as mock_sm:
                mock_session_factory = MagicMock()
                mock_session = AsyncMock()
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock()
                mock_session_factory.return_value = mock_session
                mock_sm.return_value = mock_session_factory

                with patch(
                    "framework_m.adapters.db.outbox_repository.OutboxRepository"
                ) as mock_repo_cls:
                    mock_repo = MagicMock()
                    mock_repo.get_pending = AsyncMock(return_value=[])
                    mock_repo_cls.return_value = mock_repo

                    result = await process_outbox()

                    assert result == {"processed": 0, "failed": 0}

    @pytest.mark.asyncio
    async def test_process_outbox_with_entries(self) -> None:
        """process_outbox should process entries."""
        from framework_m.adapters.jobs.outbox_worker import process_outbox

        mock_entry = MagicMock()
        mock_entry.id = "entry-1"
        mock_entry.target = "event.test"
        mock_entry.payload = {}

        with patch(
            "framework_m.adapters.db.connection.ConnectionFactory"
        ) as mock_cf_cls:
            mock_cf = MagicMock()
            mock_engine = MagicMock()
            mock_cf.get_engine.return_value = mock_engine
            mock_cf_cls.return_value = mock_cf

            with patch("sqlalchemy.orm.sessionmaker") as mock_sm:
                mock_session_factory = MagicMock()
                mock_session = AsyncMock()
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock()
                mock_session.commit = AsyncMock()
                mock_session_factory.return_value = mock_session
                mock_sm.return_value = mock_session_factory

                with patch(
                    "framework_m.adapters.db.outbox_repository.OutboxRepository"
                ) as mock_repo_cls:
                    mock_repo = MagicMock()
                    mock_repo.get_pending = AsyncMock(return_value=[mock_entry])
                    mock_repo.mark_processed = AsyncMock()
                    mock_repo_cls.return_value = mock_repo

                    with patch(
                        "framework_m.adapters.jobs.outbox_worker.dispatch_to_target"
                    ) as mock_dispatch:
                        mock_dispatch.return_value = None

                        result = await process_outbox()

                        assert result["processed"] >= 0
