"""
Nexus Memory Module
Thread-safe shared memory with proper synchronization primitives.
"""

import mmap
import json
import struct
import sys
import os
from typing import Optional, Dict, Any

from .sync import NexusMutex, NexusRWLock
from .errors import NexusError, ErrorCode, MemoryError, JSONError, Result
from .logging import get_logger

DEFAULT_SIZE = 10 * 1024 * 1024  # 10 MB
MEM_FILE = "nexus.mem"

logger = get_logger("nexus.memory")


class NexusMemory:
    """
    Thread-safe shared memory segment with proper synchronization.
    
    Memory Layout:
    [0-4]:   Magic bytes "NEXS"
    [4-8]:   Lock flag (legacy, now using file locks)
    [8-12]:  Version number
    [12-16]: Registry offset
    [16-20]: Data length
    [20...]: JSON data
    """
    
    MAGIC = b"NEXS"
    VERSION = 2
    HEADER_SIZE = 20
    
    def __init__(
        self, 
        name: str = "nexus_singularity", 
        size: int = DEFAULT_SIZE, 
        create: bool = True
    ):
        self.filename = MEM_FILE
        self.size = size
        self.name = name
        self.mmap: Optional[mmap.mmap] = None
        self.file_obj = None
        
        # Use proper file-based mutex for cross-process synchronization
        self._mutex = NexusMutex(f"nexus_{name}")
        self._rw_lock = NexusRWLock(f"nexus_{name}_rw")
        
        try:
            if create:
                with open(self.filename, "wb") as f:
                    f.write(b'\x00' * self.size)
            
            self.file_obj = open(self.filename, "r+b")
            
            try:
                # Windows named shared memory
                self.mmap = mmap.mmap(
                    self.file_obj.fileno(), 
                    self.size, 
                    tagname=name
                )
            except TypeError:
                # Unix fallback
                self.mmap = mmap.mmap(self.file_obj.fileno(), self.size)
            
            if create:
                self._initialize_memory()
            
            logger.info("memory_initialized", size=self.size, file=self.filename)
                
        except Exception as e:
            logger.critical("memory_init_failed", error=str(e))
            raise MemoryError(
                ErrorCode.MEMORY_NOT_FOUND,
                f"Failed to access Singularity: {e}"
            )

    def _initialize_memory(self):
        """Initialize memory with NBP v2 header."""
        with self._mutex:
            # Magic bytes
            self.mmap[0:4] = self.MAGIC
            # Lock (legacy, always 0)
            self.mmap[4:8] = (0).to_bytes(4, 'little')
            # Version
            self.mmap[8:12] = self.VERSION.to_bytes(4, 'little')
            # Registry offset
            self.mmap[12:16] = (1024).to_bytes(4, 'little')
            # Data length
            self.mmap[16:20] = (0).to_bytes(4, 'little')
        
        logger.debug("memory_header_written", version=self.VERSION)
        
    def read_slot(self, slot_id: int, size: int = 1024) -> bytes:
        """Read data from a fixed slot."""
        offset = 1024 + (slot_id * 1024)
        
        with self._rw_lock.read_locked():
            return bytes(self.mmap[offset:offset+size])

    def write_slot(self, slot_id: int, data: bytes) -> Result:
        """Write data to a fixed slot."""
        if len(data) > 1024:
            return Result.err(MemoryError(
                ErrorCode.SLOT_OVERFLOW,
                f"Data too large for slot {slot_id}: {len(data)} bytes"
            ))
        
        offset = 1024 + (slot_id * 1024)
        
        with self._rw_lock.write_locked():
            self.mmap[offset:offset+len(data)] = data
            # Zero-pad remaining space
            if len(data) < 1024:
                self.mmap[offset+len(data):offset+1024] = b'\x00' * (1024 - len(data))
        
        return Result.ok(None)

    def write(self, data_bytes: bytes) -> Result:
        """Write raw bytes to memory with length header."""
        if len(data_bytes) + self.HEADER_SIZE > self.size:
            return Result.err(MemoryError(
                ErrorCode.MEMORY_FULL,
                f"Data exceeds capacity: {len(data_bytes)} bytes"
            ))
        
        try:
            with self._mutex:
                # Write length at offset 16
                self.mmap[16:20] = struct.pack('<I', len(data_bytes))
                # Write data at offset 20
                self.mmap[20:20+len(data_bytes)] = data_bytes
            
            logger.debug("memory_write", size=len(data_bytes))
            return Result.ok(len(data_bytes))
            
        except Exception as e:
            logger.error("memory_write_failed", error=str(e))
            return Result.err(MemoryError(
                ErrorCode.MEMORY_CORRUPTION,
                f"Write failed: {e}"
            ))

    def read(self) -> bytes:
        """Read data from memory."""
        try:
            with self._rw_lock.read_locked():
                length = struct.unpack('<I', self.mmap[16:20])[0]
                
                if length == 0 or length > self.size - self.HEADER_SIZE:
                    return b"{}"
                    
                return bytes(self.mmap[20:20+length])
                
        except Exception as e:
            logger.error("memory_read_failed", error=str(e))
            return b"{}"

    def read_json(self) -> Result:
        """Read and parse JSON from memory."""
        try:
            data = self.read()
            parsed = json.loads(data.decode('utf-8'))
            return Result.ok(parsed)
        except json.JSONDecodeError as e:
            return Result.err(JSONError(
                ErrorCode.JSON_PARSE_ERROR,
                f"Invalid JSON: {e}"
            ))

    def write_json(self, data: Dict[str, Any]) -> Result:
        """Serialize and write JSON to memory."""
        try:
            encoded = json.dumps(data).encode('utf-8')
            return self.write(encoded)
        except (TypeError, ValueError) as e:
            return Result.err(JSONError(
                ErrorCode.JSON_ENCODE_ERROR,
                f"JSON encode failed: {e}"
            ))

    def close(self):
        """Close memory mapping."""
        if self.mmap:
            self.mmap.close()
        if self.file_obj:
            self.file_obj.close()
        logger.info("memory_closed")

    def get_ptr_info(self):
        """Get memory file info."""
        return self.filename, self.size
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        length = struct.unpack('<I', self.mmap[16:20])[0] if self.mmap else 0
        return {
            "file": self.filename,
            "total_size": self.size,
            "data_size": length,
            "free_size": self.size - self.HEADER_SIZE - length,
            "utilization": length / (self.size - self.HEADER_SIZE) if self.size > self.HEADER_SIZE else 0
        }
