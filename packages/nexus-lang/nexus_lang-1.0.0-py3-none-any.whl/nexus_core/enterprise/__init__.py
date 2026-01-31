"""
Nexus Enterprise Module
Authentication, encryption, and persistence for production deployments.
"""

from .auth import (
    AuthProvider,
    User,
    Token,
    Role,
    Permission,
    ROLE_PERMISSIONS,
    require_permission,
    get_auth
)

from .crypto import (
    NexusCrypto,
    EncryptedData,
    EncryptedMemory,
    KeyDerivation,
    get_crypto
)

from .persistence import (
    PersistenceBackend,
    FileBackend,
    SQLiteBackend,
    RedisBackend,
    MemorySyncer,
    StateSnapshot,
    create_backend
)

__all__ = [
    # Auth
    "AuthProvider",
    "User",
    "Token",
    "Role",
    "Permission",
    "ROLE_PERMISSIONS",
    "require_permission",
    "get_auth",
    
    # Crypto
    "NexusCrypto",
    "EncryptedData",
    "EncryptedMemory",
    "KeyDerivation",
    "get_crypto",
    
    # Persistence
    "PersistenceBackend",
    "FileBackend", 
    "SQLiteBackend",
    "RedisBackend",
    "MemorySyncer",
    "StateSnapshot",
    "create_backend",
]
