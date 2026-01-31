"""
Tests for Nexus synchronization primitives.
"""

import pytest
import threading
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nexus_core.sync import NexusMutex, NexusRWLock, AtomicCounter
from nexus_core.errors import NexusError


class TestNexusMutex:
    def test_acquire_release(self):
        mutex = NexusMutex("test_mutex")
        assert mutex.acquire(timeout=1.0)
        mutex.release()
    
    def test_context_manager(self):
        mutex = NexusMutex("test_context")
        with mutex:
            pass  # Should acquire and release
    
    def test_concurrent_access(self):
        mutex = NexusMutex("test_concurrent")
        counter = [0]
        
        def increment():
            for _ in range(100):
                with mutex:
                    counter[0] += 1
        
        threads = [threading.Thread(target=increment) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert counter[0] == 500


class TestNexusRWLock:
    def test_multiple_readers(self):
        rw_lock = NexusRWLock("test_rw")
        results = []
        
        def reader(id):
            with rw_lock.read_locked():
                results.append(f"read_{id}")
                time.sleep(0.01)
        
        threads = [threading.Thread(target=reader, args=(i,)) for i in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(results) == 3


class TestAtomicCounter:
    def test_increment(self):
        counter = AtomicCounter(0)
        assert counter.increment() == 1
        assert counter.increment() == 2
        assert counter.get() == 2
    
    def test_decrement(self):
        counter = AtomicCounter(10)
        assert counter.decrement() == 9
        assert counter.get() == 9
    
    def test_concurrent_increments(self):
        counter = AtomicCounter(0)
        
        def increment():
            for _ in range(100):
                counter.increment()
        
        threads = [threading.Thread(target=increment) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert counter.get() == 1000
    
    def test_compare_and_swap(self):
        counter = AtomicCounter(5)
        assert counter.compare_and_swap(5, 10) == True
        assert counter.get() == 10
        assert counter.compare_and_swap(5, 20) == False
        assert counter.get() == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
