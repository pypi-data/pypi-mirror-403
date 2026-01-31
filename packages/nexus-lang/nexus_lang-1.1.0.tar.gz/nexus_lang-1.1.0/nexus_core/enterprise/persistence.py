"""
Nexus Persistence Backends
Durable storage options for Nexus state.
"""

import json
import time
import os
import sqlite3
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from pathlib import Path


@dataclass
class StateSnapshot:
    """A snapshot of state at a point in time."""
    snapshot_id: str
    timestamp: float
    data: dict
    metadata: dict = None


class PersistenceBackend(ABC):
    """Abstract base class for persistence backends."""
    
    @abstractmethod
    def save(self, key: str, data: dict) -> bool:
        """Save state data."""
        pass
    
    @abstractmethod
    def load(self, key: str) -> Optional[dict]:
        """Load state data."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete state data."""
        pass
    
    @abstractmethod
    def list_keys(self, prefix: str = "") -> List[str]:
        """List all keys with optional prefix filter."""
        pass
    
    def snapshot(self, key: str, data: dict) -> StateSnapshot:
        """Create a timestamped snapshot."""
        snapshot_id = f"{key}:{int(time.time() * 1000)}"
        snapshot = StateSnapshot(
            snapshot_id=snapshot_id,
            timestamp=time.time(),
            data=data
        )
        self.save(snapshot_id, {
            "snapshot_id": snapshot_id,
            "timestamp": snapshot.timestamp,
            "data": snapshot.data
        })
        return snapshot


class FileBackend(PersistenceBackend):
    """
    File-based persistence using JSON files.
    Simple and suitable for development/small deployments.
    """
    
    def __init__(self, base_dir: str = ".nexus_data"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def _key_to_path(self, key: str) -> Path:
        """Convert key to file path."""
        safe_key = key.replace(":", "_").replace("/", "_")
        return self.base_dir / f"{safe_key}.json"
    
    def save(self, key: str, data: dict) -> bool:
        try:
            path = self._key_to_path(key)
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"[NEXUS] FileBackend save error: {e}")
            return False
    
    def load(self, key: str) -> Optional[dict]:
        try:
            path = self._key_to_path(key)
            if not path.exists():
                return None
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[NEXUS] FileBackend load error: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        try:
            path = self._key_to_path(key)
            if path.exists():
                path.unlink()
            return True
        except:
            return False
    
    def list_keys(self, prefix: str = "") -> List[str]:
        keys = []
        for path in self.base_dir.glob("*.json"):
            key = path.stem.replace("_", ":")
            if key.startswith(prefix):
                keys.append(key)
        return keys


class SQLiteBackend(PersistenceBackend):
    """
    SQLite-based persistence.
    Good for medium deployments with ACID requirements.
    """
    
    def __init__(self, db_path: str = ".nexus_data/nexus.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS state (
                    key TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    updated_at REAL NOT NULL,
                    created_at REAL NOT NULL
                )
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_key_prefix 
                ON state(key)
            ''')
            conn.commit()
    
    def save(self, key: str, data: dict) -> bool:
        try:
            now = time.time()
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO state (key, data, updated_at, created_at)
                    VALUES (?, ?, ?, COALESCE(
                        (SELECT created_at FROM state WHERE key = ?),
                        ?
                    ))
                ''', (key, json.dumps(data), now, key, now))
                conn.commit()
            return True
        except Exception as e:
            print(f"[NEXUS] SQLiteBackend save error: {e}")
            return False
    
    def load(self, key: str) -> Optional[dict]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    'SELECT data FROM state WHERE key = ?', 
                    (key,)
                )
                row = cursor.fetchone()
                if row:
                    return json.loads(row[0])
                return None
        except Exception as e:
            print(f"[NEXUS] SQLiteBackend load error: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('DELETE FROM state WHERE key = ?', (key,))
                conn.commit()
            return True
        except:
            return False
    
    def list_keys(self, prefix: str = "") -> List[str]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    'SELECT key FROM state WHERE key LIKE ?',
                    (f"{prefix}%",)
                )
                return [row[0] for row in cursor.fetchall()]
        except:
            return []
    
    def get_history(self, key_prefix: str, limit: int = 100) -> List[dict]:
        """Get historical snapshots."""
        keys = self.list_keys(key_prefix)
        snapshots = []
        for key in sorted(keys, reverse=True)[:limit]:
            data = self.load(key)
            if data:
                snapshots.append(data)
        return snapshots


class RedisBackend(PersistenceBackend):
    """
    Redis-based persistence.
    For distributed deployments with high performance requirements.
    """
    
    def __init__(self, host: str = "localhost", port: int = 6379, 
                 db: int = 0, prefix: str = "nexus:"):
        try:
            import redis
            self.client = redis.Redis(host=host, port=port, db=db)
            self.prefix = prefix
            self._available = True
        except ImportError:
            print("[NEXUS] Redis not available - install redis-py")
            self._available = False
    
    def _full_key(self, key: str) -> str:
        return f"{self.prefix}{key}"
    
    def save(self, key: str, data: dict) -> bool:
        if not self._available:
            return False
        try:
            self.client.set(self._full_key(key), json.dumps(data))
            return True
        except Exception as e:
            print(f"[NEXUS] RedisBackend save error: {e}")
            return False
    
    def load(self, key: str) -> Optional[dict]:
        if not self._available:
            return None
        try:
            data = self.client.get(self._full_key(key))
            if data:
                return json.loads(data)
            return None
        except:
            return None
    
    def delete(self, key: str) -> bool:
        if not self._available:
            return False
        try:
            self.client.delete(self._full_key(key))
            return True
        except:
            return False
    
    def list_keys(self, prefix: str = "") -> List[str]:
        if not self._available:
            return []
        try:
            pattern = f"{self.prefix}{prefix}*"
            keys = self.client.keys(pattern)
            return [k.decode().replace(self.prefix, "") for k in keys]
        except:
            return []


class MemorySyncer:
    """
    Syncs Nexus shared memory with a persistence backend.
    Provides automatic snapshots and recovery.
    """
    
    def __init__(self, backend: PersistenceBackend, 
                 auto_save_interval: float = 30.0,
                 state_key: str = "nexus:state"):
        self.backend = backend
        self.state_key = state_key
        self.auto_save_interval = auto_save_interval
        self._running = False
        self._thread = None
    
    def save_state(self) -> bool:
        """Save current memory state to backend."""
        try:
            from nexus_core import NexusMemory
            mem = NexusMemory(create=False)
            data = json.loads(mem.read().decode())
            mem.close()
            
            return self.backend.save(self.state_key, {
                "data": data,
                "saved_at": time.time()
            })
        except Exception as e:
            print(f"[NEXUS] State save error: {e}")
            return False
    
    def load_state(self) -> Optional[dict]:
        """Load state from backend into memory."""
        try:
            saved = self.backend.load(self.state_key)
            if not saved:
                return None
            
            from nexus_core import NexusMemory
            mem = NexusMemory(create=False)
            mem.write(json.dumps(saved["data"]).encode())
            mem.close()
            
            return saved["data"]
        except Exception as e:
            print(f"[NEXUS] State load error: {e}")
            return None
    
    def create_snapshot(self) -> Optional[StateSnapshot]:
        """Create a snapshot for backup/rollback."""
        try:
            from nexus_core import NexusMemory
            mem = NexusMemory(create=False)
            data = json.loads(mem.read().decode())
            mem.close()
            
            return self.backend.snapshot(f"{self.state_key}:snapshot", data)
        except:
            return None
    
    def start_auto_save(self):
        """Start automatic state saving."""
        import threading
        
        if self._running:
            return
        
        self._running = True
        
        def save_loop():
            while self._running:
                time.sleep(self.auto_save_interval)
                if self._running:
                    self.save_state()
        
        self._thread = threading.Thread(target=save_loop, daemon=True)
        self._thread.start()
        print(f"[NEXUS] Auto-save started (interval: {self.auto_save_interval}s)")
    
    def stop_auto_save(self):
        """Stop automatic saving."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)
        print("[NEXUS] Auto-save stopped")


# Factory function
def create_backend(backend_type: str = "file", **kwargs) -> PersistenceBackend:
    """Create a persistence backend by type."""
    backends = {
        "file": FileBackend,
        "sqlite": SQLiteBackend,
        "redis": RedisBackend
    }
    
    if backend_type not in backends:
        raise ValueError(f"Unknown backend type: {backend_type}")
    
    return backends[backend_type](**kwargs)
