"""
Nexus Event System
Event-driven architecture for real-time state updates.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from collections import deque
from enum import Enum
import time
import threading
import json


class EventType(Enum):
    """Standard Nexus event types."""
    STATE_UPDATE = "state_update"
    STATE_PATCH = "state_patch"
    SLOT_WRITE = "slot_write"
    PROCESS_SPAWN = "process_spawn"
    PROCESS_EXIT = "process_exit"
    PROCESS_CRASH = "process_crash"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    CUSTOM = "custom"


@dataclass
class NexusEvent:
    """
    Represents a single event in the Nexus system.
    """
    type: EventType
    payload: Any
    source: str = "unknown"
    timestamp: float = field(default_factory=time.time)
    event_id: int = 0
    
    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "type": self.type.value,
            "source": self.source,
            "timestamp": self.timestamp,
            "payload": self.payload if not isinstance(self.payload, bytes) else self.payload.decode('utf-8', errors='replace')
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class EventBus:
    """
    Central event bus for publishing and subscribing to events.
    Thread-safe with support for async subscribers.
    """
    
    def __init__(self, max_history: int = 1000):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._history: deque = deque(maxlen=max_history)
        self._event_counter = 0
        self._lock = threading.Lock()
    
    def subscribe(self, event_type: EventType, callback: Callable[[NexusEvent], None]) -> None:
        """Subscribe to events of a specific type."""
        key = event_type.value
        with self._lock:
            if key not in self._subscribers:
                self._subscribers[key] = []
            self._subscribers[key].append(callback)
    
    def subscribe_all(self, callback: Callable[[NexusEvent], None]) -> None:
        """Subscribe to all event types."""
        with self._lock:
            if "*" not in self._subscribers:
                self._subscribers["*"] = []
            self._subscribers["*"].append(callback)
    
    def unsubscribe(self, event_type: EventType, callback: Callable) -> bool:
        """Unsubscribe from events."""
        key = event_type.value
        with self._lock:
            if key in self._subscribers and callback in self._subscribers[key]:
                self._subscribers[key].remove(callback)
                return True
            return False
    
    def emit(self, event: NexusEvent) -> None:
        """Emit an event to all subscribers."""
        with self._lock:
            self._event_counter += 1
            event.event_id = self._event_counter
            self._history.append(event)
            
            # Get subscribers (copy to avoid lock during callbacks)
            callbacks = []
            key = event.type.value
            if key in self._subscribers:
                callbacks.extend(self._subscribers[key])
            if "*" in self._subscribers:
                callbacks.extend(self._subscribers["*"])
        
        # Execute callbacks outside lock
        for callback in callbacks:
            try:
                callback(event)
            except Exception as e:
                print(f"[NEXUS] Event callback error: {e}")
    
    def emit_state_update(self, new_state: dict, source: str = "memory") -> None:
        """Convenience method to emit a state update event."""
        self.emit(NexusEvent(
            type=EventType.STATE_UPDATE,
            payload=new_state,
            source=source
        ))
    
    def get_history(self, since_id: int = 0, limit: int = 100) -> List[NexusEvent]:
        """Get event history since a given event ID."""
        with self._lock:
            events = [e for e in self._history if e.event_id > since_id]
            return events[-limit:]
    
    def get_last_event(self) -> Optional[NexusEvent]:
        """Get the most recent event."""
        with self._lock:
            return self._history[-1] if self._history else None


class MemoryWatcher:
    """
    Watches shared memory for changes and emits events.
    Replaces polling with efficient change detection.
    """
    
    def __init__(self, event_bus: EventBus, poll_interval: float = 0.1):
        self.event_bus = event_bus
        self.poll_interval = poll_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_hash: Optional[int] = None
        self._memory = None
    
    def start(self) -> None:
        """Start watching memory for changes."""
        if self._running:
            return
        
        from nexus_core import NexusMemory
        self._memory = NexusMemory(create=False)
        self._running = True
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()
        print("[NEXUS] Memory watcher started")
    
    def stop(self) -> None:
        """Stop watching memory."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)
        if self._memory:
            self._memory.close()
        print("[NEXUS] Memory watcher stopped")
    
    def _watch_loop(self) -> None:
        """Internal loop that checks for memory changes."""
        while self._running:
            try:
                data = self._memory.read()
                current_hash = hash(data)
                
                if current_hash != self._last_hash:
                    self._last_hash = current_hash
                    
                    try:
                        parsed = json.loads(data.decode('utf-8'))
                    except:
                        parsed = {"raw": data.decode('utf-8', errors='replace')}
                    
                    self.event_bus.emit_state_update(parsed, source="memory_watcher")
                
                time.sleep(self.poll_interval)
                
            except Exception as e:
                print(f"[NEXUS] Memory watcher error: {e}")
                time.sleep(1)


# Global event bus instance
_global_bus: Optional[EventBus] = None

def get_event_bus() -> EventBus:
    """Get or create the global event bus."""
    global _global_bus
    if _global_bus is None:
        _global_bus = EventBus()
    return _global_bus
