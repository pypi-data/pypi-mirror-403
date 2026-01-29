"""Integration tests for app-defined ports.

Tests the port/adapter pattern including:
- Registering custom implementations
- Dependency injection with ports
- Port swapping for testing
"""

from __future__ import annotations

from typing import Protocol

# ============================================================================
# Port Interfaces (Protocols)
# ============================================================================


class EmailPort(Protocol):
    """Port for email sending."""

    async def send(self, to: str, subject: str, body: str) -> bool:
        """Send an email."""
        ...


class StoragePort(Protocol):
    """Port for file storage."""

    async def save(self, key: str, data: bytes) -> str:
        """Save data and return URL."""
        ...

    async def load(self, key: str) -> bytes | None:
        """Load data by key."""
        ...


class NotificationPort(Protocol):
    """Port for notifications."""

    async def notify(self, user_id: str, message: str) -> bool:
        """Send notification to user."""
        ...


# ============================================================================
# Mock Implementations
# ============================================================================


class MockEmailAdapter:
    """Mock email adapter for testing."""

    def __init__(self) -> None:
        self.sent_emails: list[dict] = []

    async def send(self, to: str, subject: str, body: str) -> bool:
        """Record email instead of sending."""
        self.sent_emails.append({"to": to, "subject": subject, "body": body})
        return True


class MockStorageAdapter:
    """Mock storage adapter for testing."""

    def __init__(self) -> None:
        self._storage: dict[str, bytes] = {}

    async def save(self, key: str, data: bytes) -> str:
        """Save to in-memory storage."""
        self._storage[key] = data
        return f"mock://storage/{key}"

    async def load(self, key: str) -> bytes | None:
        """Load from in-memory storage."""
        return self._storage.get(key)


class MockNotificationAdapter:
    """Mock notification adapter for testing."""

    def __init__(self) -> None:
        self.notifications: list[dict] = []

    async def notify(self, user_id: str, message: str) -> bool:
        """Record notification."""
        self.notifications.append({"user_id": user_id, "message": message})
        return True


# ============================================================================
# Simple Port Registry (for testing)
# ============================================================================


class PortRegistry:
    """Simple registry for port implementations."""

    def __init__(self) -> None:
        self._ports: dict[str, object] = {}

    def register(self, port_name: str, implementation: object) -> None:
        """Register a port implementation."""
        self._ports[port_name] = implementation

    def get(self, port_name: str) -> object | None:
        """Get a registered port implementation."""
        return self._ports.get(port_name)

    def clear(self) -> None:
        """Clear all registrations."""
        self._ports.clear()


# ============================================================================
# Tests
# ============================================================================


class TestPortRegistration:
    """Test registering port implementations."""

    def test_register_email_port(self) -> None:
        """Test registering an email port."""
        registry = PortRegistry()
        email_adapter = MockEmailAdapter()

        registry.register("email", email_adapter)

        assert registry.get("email") is email_adapter

    def test_register_multiple_ports(self) -> None:
        """Test registering multiple ports."""
        registry = PortRegistry()
        email = MockEmailAdapter()
        storage = MockStorageAdapter()
        notification = MockNotificationAdapter()

        registry.register("email", email)
        registry.register("storage", storage)
        registry.register("notification", notification)

        assert registry.get("email") is email
        assert registry.get("storage") is storage
        assert registry.get("notification") is notification

    def test_get_unregistered_port(self) -> None:
        """Test getting an unregistered port returns None."""
        registry = PortRegistry()

        assert registry.get("nonexistent") is None


class TestPortSwapping:
    """Test swapping port implementations."""

    def test_replace_port_implementation(self) -> None:
        """Test replacing a port with different implementation."""
        registry = PortRegistry()

        original = MockEmailAdapter()
        replacement = MockEmailAdapter()

        registry.register("email", original)
        assert registry.get("email") is original

        registry.register("email", replacement)
        assert registry.get("email") is replacement

    def test_clear_ports(self) -> None:
        """Test clearing all port registrations."""
        registry = PortRegistry()
        registry.register("email", MockEmailAdapter())
        registry.register("storage", MockStorageAdapter())

        registry.clear()

        assert registry.get("email") is None
        assert registry.get("storage") is None


class TestPortUsage:
    """Test using ports for functionality."""

    async def test_email_port_usage(self) -> None:
        """Test using email port to send email."""
        email: EmailPort = MockEmailAdapter()

        result = await email.send("user@example.com", "Hello", "Test body")

        assert result is True
        assert len(email.sent_emails) == 1
        assert email.sent_emails[0]["to"] == "user@example.com"

    async def test_storage_port_usage(self) -> None:
        """Test using storage port to save/load data."""
        storage: StoragePort = MockStorageAdapter()

        url = await storage.save("test-key", b"test data")
        loaded = await storage.load("test-key")

        assert url == "mock://storage/test-key"
        assert loaded == b"test data"

    async def test_notification_port_usage(self) -> None:
        """Test using notification port."""
        notification: NotificationPort = MockNotificationAdapter()

        result = await notification.notify("user-123", "Hello!")

        assert result is True
        assert len(notification.notifications) == 1
        assert notification.notifications[0]["user_id"] == "user-123"


class TestPortIsolation:
    """Test port isolation between registries."""

    def test_separate_registries_are_isolated(self) -> None:
        """Test that separate registries don't share state."""
        registry1 = PortRegistry()
        registry2 = PortRegistry()

        email1 = MockEmailAdapter()
        email2 = MockEmailAdapter()

        registry1.register("email", email1)
        registry2.register("email", email2)

        assert registry1.get("email") is email1
        assert registry2.get("email") is email2
        assert registry1.get("email") is not registry2.get("email")
