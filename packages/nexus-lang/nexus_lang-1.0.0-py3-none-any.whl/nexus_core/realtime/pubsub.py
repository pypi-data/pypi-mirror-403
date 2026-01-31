"""
Nexus Pub/Sub System
Channel-based publish/subscribe for decoupled messaging.
"""

import re
import threading
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass
import time
import json


@dataclass
class Message:
    """A pub/sub message."""
    channel: str
    data: Any
    sender: str = "anonymous"
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_dict(self) -> dict:
        return {
            "channel": self.channel,
            "data": self.data,
            "sender": self.sender,
            "timestamp": self.timestamp
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class PubSub:
    """
    Publish/Subscribe messaging system with pattern matching.
    
    Features:
    - Exact channel matching: "chat.message"
    - Wildcard patterns: "chat.*", "*.error"
    - Multi-level wildcards: "logs.**"
    """
    
    def __init__(self):
        self._exact_subs: Dict[str, List[Callable]] = {}
        self._pattern_subs: List[tuple] = []  # (pattern, regex, callback)
        self._lock = threading.Lock()
        self._message_count = 0
    
    def subscribe(self, channel: str, callback: Callable[[Message], None]) -> None:
        """
        Subscribe to a channel or pattern.
        
        Patterns:
        - "chat.room1" - exact match
        - "chat.*" - single level wildcard
        - "logs.**" - multi-level wildcard
        """
        with self._lock:
            if '*' in channel:
                # Pattern subscription
                regex = self._pattern_to_regex(channel)
                self._pattern_subs.append((channel, regex, callback))
            else:
                # Exact subscription
                if channel not in self._exact_subs:
                    self._exact_subs[channel] = []
                self._exact_subs[channel].append(callback)
    
    def unsubscribe(self, channel: str, callback: Callable) -> bool:
        """Unsubscribe from a channel."""
        with self._lock:
            if '*' in channel:
                for i, (pat, _, cb) in enumerate(self._pattern_subs):
                    if pat == channel and cb == callback:
                        self._pattern_subs.pop(i)
                        return True
            else:
                if channel in self._exact_subs and callback in self._exact_subs[channel]:
                    self._exact_subs[channel].remove(callback)
                    return True
            return False
    
    def publish(self, channel: str, data: Any, sender: str = "anonymous") -> int:
        """
        Publish a message to a channel.
        Returns number of subscribers notified.
        """
        message = Message(channel=channel, data=data, sender=sender)
        
        with self._lock:
            self._message_count += 1
            
            # Collect matching subscribers
            callbacks = []
            
            # Exact matches
            if channel in self._exact_subs:
                callbacks.extend(self._exact_subs[channel])
            
            # Pattern matches
            for _, regex, callback in self._pattern_subs:
                if regex.match(channel):
                    callbacks.append(callback)
        
        # Execute callbacks outside lock
        for callback in callbacks:
            try:
                callback(message)
            except Exception as e:
                print(f"[NEXUS] PubSub callback error: {e}")
        
        return len(callbacks)
    
    def _pattern_to_regex(self, pattern: str) -> re.Pattern:
        """Convert a channel pattern to regex."""
        # Escape special regex chars except * and **
        escaped = re.escape(pattern)
        
        # Replace \*\* with multi-level wildcard
        escaped = escaped.replace(r'\*\*', r'.*')
        
        # Replace remaining \* with single-segment wildcard
        escaped = escaped.replace(r'\*', r'[^.]+')
        
        return re.compile(f'^{escaped}$')
    
    def get_stats(self) -> dict:
        """Get pub/sub statistics."""
        with self._lock:
            return {
                "exact_channels": len(self._exact_subs),
                "pattern_subscriptions": len(self._pattern_subs),
                "total_messages": self._message_count
            }


class RoomManager:
    """
    Manages rooms/channels for real-time collaboration.
    Useful for chat, multiplayer games, collaborative editing.
    """
    
    def __init__(self, pubsub: PubSub):
        self.pubsub = pubsub
        self._rooms: Dict[str, Set[str]] = {}  # room_id -> set of user_ids
        self._user_rooms: Dict[str, Set[str]] = {}  # user_id -> set of room_ids
        self._lock = threading.Lock()
    
    def join(self, room_id: str, user_id: str) -> List[str]:
        """User joins a room. Returns list of other users in room."""
        with self._lock:
            if room_id not in self._rooms:
                self._rooms[room_id] = set()
            
            others = list(self._rooms[room_id])
            self._rooms[room_id].add(user_id)
            
            if user_id not in self._user_rooms:
                self._user_rooms[user_id] = set()
            self._user_rooms[user_id].add(room_id)
        
        # Notify room
        self.pubsub.publish(f"room.{room_id}.join", {
            "user_id": user_id,
            "room_id": room_id
        })
        
        return others
    
    def leave(self, room_id: str, user_id: str) -> None:
        """User leaves a room."""
        with self._lock:
            if room_id in self._rooms:
                self._rooms[room_id].discard(user_id)
                if not self._rooms[room_id]:
                    del self._rooms[room_id]
            
            if user_id in self._user_rooms:
                self._user_rooms[user_id].discard(room_id)
        
        # Notify room
        self.pubsub.publish(f"room.{room_id}.leave", {
            "user_id": user_id,
            "room_id": room_id
        })
    
    def broadcast(self, room_id: str, data: Any, sender: str = "system") -> int:
        """Broadcast message to all users in a room."""
        return self.pubsub.publish(f"room.{room_id}.message", data, sender)
    
    def get_users(self, room_id: str) -> List[str]:
        """Get list of users in a room."""
        with self._lock:
            return list(self._rooms.get(room_id, set()))
    
    def get_user_rooms(self, user_id: str) -> List[str]:
        """Get rooms a user is in."""
        with self._lock:
            return list(self._user_rooms.get(user_id, set()))


# Global pub/sub instance
_global_pubsub: Optional[PubSub] = None

def get_pubsub() -> PubSub:
    """Get or create the global pub/sub instance."""
    global _global_pubsub
    if _global_pubsub is None:
        _global_pubsub = PubSub()
    return _global_pubsub
