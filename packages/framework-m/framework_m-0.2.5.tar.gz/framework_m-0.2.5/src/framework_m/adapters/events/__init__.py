"""Events adapters package.

Provides implementations of EventBusProtocol for pub/sub messaging.

Adapters:
- InMemoryEventBus: For development and testing (no external deps)
- NatsEventBusAdapter: For production with NATS JetStream
"""

from framework_m.adapters.events.inmemory_event_bus import InMemoryEventBus
from framework_m.adapters.events.nats_event_bus import NatsEventBusAdapter

__all__ = ["InMemoryEventBus", "NatsEventBusAdapter"]
