"""
Nexus Synchronization Primitives
Cross-platform mutex and semaphore implementations for safe shared memory access.
"""

import sys
import time
import ctypes
from contextlib import contextmanager
from .errors import NexusError, ErrorCode

if sys.platform == 'win32':
    import msvcrt
else:
    import fcntl


class NexusMutex:
    """
    Cross-platform mutex for synchronizing access to shared memory.
    Uses file locking for cross-process synchronization.
    """
    
    def __init__(self, name: str = "nexus_global", timeout: float = 5.0):
        self.name = name
        self.timeout = timeout
        self._lock_file = None
        self._lock_path = f".nexus_{name}.lock"
        self._acquired = False
    
    def acquire(self, timeout: float = None) -> bool:
        """
        Acquire the mutex lock.
        Returns True if lock acquired, False if timeout.
        """
        timeout = timeout or self.timeout
        start = time.time()
        
        try:
            self._lock_file = open(self._lock_path, 'w')
            
            while True:
                try:
                    if sys.platform == 'win32':
                        msvcrt.locking(self._lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    
                    self._acquired = True
                    return True
                    
                except (IOError, OSError):
                    if time.time() - start > timeout:
                        return False
                    time.sleep(0.01)
                    
        except Exception as e:
            if self._lock_file:
                self._lock_file.close()
            raise NexusError(ErrorCode.MEMORY_LOCK_TIMEOUT, f"Failed to acquire lock: {e}")
    
    def release(self):
        """Release the mutex lock."""
        if self._lock_file and self._acquired:
            try:
                if sys.platform == 'win32':
                    msvcrt.locking(self._lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_UN)
            finally:
                self._lock_file.close()
                self._lock_file = None
                self._acquired = False
    
    def __enter__(self):
        if not self.acquire():
            raise NexusError(ErrorCode.MEMORY_LOCK_TIMEOUT, "Lock acquisition timeout")
        return self
    
    def __exit__(self, *args):
        self.release()
    
    @contextmanager
    def locked(self, timeout: float = None):
        """Context manager for acquiring lock with optional timeout."""
        if not self.acquire(timeout):
            raise NexusError(ErrorCode.MEMORY_LOCK_TIMEOUT, "Lock acquisition timeout")
        try:
            yield self
        finally:
            self.release()


class NexusRWLock:
    """
    Read-Write lock allowing multiple readers but single writer.
    Useful for optimizing read-heavy workloads.
    """
    
    def __init__(self, name: str = "nexus_rw"):
        self.name = name
        self._readers = 0
        self._write_mutex = NexusMutex(f"{name}_write")
        self._count_mutex = NexusMutex(f"{name}_count")
    
    def acquire_read(self, timeout: float = 5.0) -> bool:
        """Acquire read lock (allows multiple readers)."""
        with self._count_mutex.locked(timeout):
            self._readers += 1
            if self._readers == 1:
                if not self._write_mutex.acquire(timeout):
                    self._readers -= 1
                    return False
        return True
    
    def release_read(self):
        """Release read lock."""
        with self._count_mutex.locked():
            self._readers -= 1
            if self._readers == 0:
                self._write_mutex.release()
    
    def acquire_write(self, timeout: float = 5.0) -> bool:
        """Acquire write lock (exclusive access)."""
        return self._write_mutex.acquire(timeout)
    
    def release_write(self):
        """Release write lock."""
        self._write_mutex.release()
    
    @contextmanager
    def read_locked(self, timeout: float = 5.0):
        """Context manager for read lock."""
        if not self.acquire_read(timeout):
            raise NexusError(ErrorCode.MEMORY_LOCK_TIMEOUT, "Read lock timeout")
        try:
            yield
        finally:
            self.release_read()
    
    @contextmanager
    def write_locked(self, timeout: float = 5.0):
        """Context manager for write lock."""
        if not self.acquire_write(timeout):
            raise NexusError(ErrorCode.MEMORY_LOCK_TIMEOUT, "Write lock timeout")
        try:
            yield
        finally:
            self.release_write()


class AtomicCounter:
    """Thread-safe atomic counter using ctypes."""
    
    def __init__(self, initial: int = 0):
        self._value = ctypes.c_long(initial)
        self._lock = NexusMutex("atomic_counter")
    
    def get(self) -> int:
        return self._value.value
    
    def set(self, value: int):
        with self._lock:
            self._value.value = value
    
    def increment(self, delta: int = 1) -> int:
        with self._lock:
            self._value.value += delta
            return self._value.value
    
    def decrement(self, delta: int = 1) -> int:
        return self.increment(-delta)
    
    def compare_and_swap(self, expected: int, new: int) -> bool:
        """Atomic compare-and-swap operation."""
        with self._lock:
            if self._value.value == expected:
                self._value.value = new
                return True
            return False
