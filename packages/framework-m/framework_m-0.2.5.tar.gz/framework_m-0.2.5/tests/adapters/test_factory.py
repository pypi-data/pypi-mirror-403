"""Tests for adapter factory auto-detection."""

import pytest

from framework_m.adapters.factory import (
    get_cache,
    get_event_bus,
    get_job_queue,
    is_dev_mode,
)

# =============================================================================
# Test: Dev Mode Detection
# =============================================================================


class TestIsDevMode:
    """Tests for is_dev_mode function."""

    def test_dev_mode_when_no_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """is_dev_mode should return True when no URLs set."""
        monkeypatch.delenv("NATS_URL", raising=False)
        monkeypatch.delenv("REDIS_URL", raising=False)

        assert is_dev_mode() is True

    def test_not_dev_mode_when_nats_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """is_dev_mode should return False when NATS_URL set."""
        monkeypatch.setenv("NATS_URL", "nats://localhost:4222")
        monkeypatch.delenv("REDIS_URL", raising=False)

        assert is_dev_mode() is False

    def test_not_dev_mode_when_redis_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """is_dev_mode should return False when REDIS_URL set."""
        monkeypatch.delenv("NATS_URL", raising=False)
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")

        assert is_dev_mode() is False


# =============================================================================
# Test: Job Queue Auto-Detection
# =============================================================================


class TestGetJobQueue:
    """Tests for get_job_queue factory."""

    def test_returns_inmemory_when_no_nats(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """get_job_queue should return InMemoryJobQueue when NATS_URL not set."""
        monkeypatch.delenv("NATS_URL", raising=False)

        from framework_m.adapters.jobs import InMemoryJobQueue

        queue = get_job_queue()
        assert isinstance(queue, InMemoryJobQueue)

    def test_returns_taskiq_when_nats_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """get_job_queue should return TaskiqJobQueueAdapter when NATS_URL set."""
        monkeypatch.setenv("NATS_URL", "nats://localhost:4222")

        from framework_m.adapters.jobs.taskiq_adapter import TaskiqJobQueueAdapter

        queue = get_job_queue()
        assert isinstance(queue, TaskiqJobQueueAdapter)


# =============================================================================
# Test: Event Bus Auto-Detection
# =============================================================================


class TestGetEventBus:
    """Tests for get_event_bus factory."""

    def test_returns_inmemory_when_no_nats(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """get_event_bus should return InMemoryEventBus when NATS_URL not set."""
        monkeypatch.delenv("NATS_URL", raising=False)

        from framework_m.adapters.events.inmemory_event_bus import InMemoryEventBus

        bus = get_event_bus()
        assert isinstance(bus, InMemoryEventBus)

    def test_returns_nats_when_nats_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """get_event_bus should return NatsEventBusAdapter when NATS_URL set."""
        monkeypatch.setenv("NATS_URL", "nats://localhost:4222")

        from framework_m.adapters.events.nats_event_bus import NatsEventBusAdapter

        bus = get_event_bus()
        assert isinstance(bus, NatsEventBusAdapter)


# =============================================================================
# Test: Cache Auto-Detection
# =============================================================================


class TestGetCache:
    """Tests for get_cache factory."""

    def test_returns_inmemory_when_no_redis(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """get_cache should return InMemoryCacheAdapter when REDIS_URL not set."""
        monkeypatch.delenv("REDIS_URL", raising=False)

        from framework_m.adapters.cache import InMemoryCacheAdapter

        cache = get_cache()
        assert isinstance(cache, InMemoryCacheAdapter)

    def test_raises_when_redis_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """get_cache should raise NotImplementedError when REDIS_URL set."""
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")

        with pytest.raises(NotImplementedError, match="RedisCacheAdapter"):
            get_cache()


# =============================================================================
# Test: Import
# =============================================================================


class TestImport:
    """Tests for factory imports."""

    def test_import_factory_functions(self) -> None:
        """Factory functions should be importable."""
        from framework_m.adapters.factory import (
            get_cache,
            get_event_bus,
            get_job_queue,
            is_dev_mode,
        )

        assert get_job_queue is not None
        assert get_event_bus is not None
        assert get_cache is not None
        assert is_dev_mode is not None
