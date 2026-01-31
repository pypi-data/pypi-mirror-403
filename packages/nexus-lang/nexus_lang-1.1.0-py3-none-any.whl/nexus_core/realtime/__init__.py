"""
Nexus Real-time Module
WebSocket gateway, event streaming, and pub/sub.
"""

from .events import (
    EventBus,
    EventType, 
    NexusEvent,
    MemoryWatcher,
    get_event_bus
)

from .pubsub import (
    PubSub,
    Message,
    RoomManager,
    get_pubsub
)

from .gateway import (
    WebSocketGateway,
    Client,
    create_gateway,
    get_gateway
)

__all__ = [
    # Events
    "EventBus",
    "EventType",
    "NexusEvent", 
    "MemoryWatcher",
    "get_event_bus",
    
    # Pub/Sub
    "PubSub",
    "Message",
    "RoomManager",
    "get_pubsub",
    
    # Gateway
    "WebSocketGateway",
    "Client",
    "create_gateway",
    "get_gateway",
]
