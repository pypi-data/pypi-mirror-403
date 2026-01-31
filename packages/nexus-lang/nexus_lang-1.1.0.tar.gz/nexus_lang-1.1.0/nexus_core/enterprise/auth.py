"""
Nexus Authentication & Authorization
JWT-based authentication with role-based access control.
"""

import hashlib
import hmac
import json
import base64
import time
import secrets
from typing import Optional, Dict, List, Set
from dataclasses import dataclass, field
from enum import Enum


class Role(Enum):
    """Standard roles for RBAC."""
    GUEST = "guest"
    USER = "user"
    EDITOR = "editor"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"


class Permission(Enum):
    """Standard permissions."""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"
    
    # Nexus-specific
    MEMORY_READ = "memory:read"
    MEMORY_WRITE = "memory:write"
    SLOT_READ = "slot:read"
    SLOT_WRITE = "slot:write"
    PROCESS_SPAWN = "process:spawn"
    PROCESS_KILL = "process:kill"
    GATEWAY_CONNECT = "gateway:connect"


# Default role permissions
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.GUEST: {Permission.READ, Permission.MEMORY_READ, Permission.GATEWAY_CONNECT},
    Role.USER: {Permission.READ, Permission.WRITE, Permission.MEMORY_READ, 
                Permission.MEMORY_WRITE, Permission.GATEWAY_CONNECT},
    Role.EDITOR: {Permission.READ, Permission.WRITE, Permission.EXECUTE,
                  Permission.MEMORY_READ, Permission.MEMORY_WRITE,
                  Permission.SLOT_READ, Permission.SLOT_WRITE, Permission.GATEWAY_CONNECT},
    Role.ADMIN: {p for p in Permission},
    Role.SUPERADMIN: {p for p in Permission},
}


@dataclass
class User:
    """Represents an authenticated user."""
    user_id: str
    username: str
    roles: List[Role] = field(default_factory=lambda: [Role.USER])
    permissions: Set[Permission] = field(default_factory=set)
    metadata: Dict = field(default_factory=dict)
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has a specific permission."""
        if permission in self.permissions:
            return True
        for role in self.roles:
            if permission in ROLE_PERMISSIONS.get(role, set()):
                return True
        return False
    
    def has_role(self, role: Role) -> bool:
        """Check if user has a specific role."""
        return role in self.roles


@dataclass
class Token:
    """JWT-like token structure."""
    user_id: str
    username: str
    roles: List[str]
    issued_at: float
    expires_at: float
    jti: str  # JWT ID for revocation
    
    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class AuthProvider:
    """
    Authentication provider with JWT-like tokens.
    
    Features:
    - HMAC-SHA256 signed tokens
    - Token expiration
    - Token revocation
    - User management
    """
    
    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or secrets.token_hex(32)
        self._users: Dict[str, Dict] = {}  # user_id -> user_data
        self._revoked_tokens: Set[str] = set()
        self._token_expiry = 3600 * 24  # 24 hours default
    
    def register(self, username: str, password: str, roles: List[Role] = None) -> User:
        """Register a new user."""
        user_id = secrets.token_hex(16)
        password_hash = self._hash_password(password)
        
        user_data = {
            "user_id": user_id,
            "username": username,
            "password_hash": password_hash,
            "roles": [r.value for r in (roles or [Role.USER])],
            "created_at": time.time()
        }
        self._users[user_id] = user_data
        
        return User(
            user_id=user_id,
            username=username,
            roles=roles or [Role.USER]
        )
    
    def authenticate(self, username: str, password: str) -> Optional[str]:
        """Authenticate user and return token."""
        user_data = None
        for ud in self._users.values():
            if ud["username"] == username:
                user_data = ud
                break
        
        if not user_data:
            return None
        
        if not self._verify_password(password, user_data["password_hash"]):
            return None
        
        return self._create_token(user_data)
    
    def verify_token(self, token: str) -> Optional[User]:
        """Verify token and return user."""
        parsed = self._parse_token(token)
        if not parsed:
            return None
        
        if parsed.is_expired():
            return None
        
        if parsed.jti in self._revoked_tokens:
            return None
        
        return User(
            user_id=parsed.user_id,
            username=parsed.username,
            roles=[Role(r) for r in parsed.roles]
        )
    
    def revoke_token(self, token: str) -> bool:
        """Revoke a token."""
        parsed = self._parse_token(token)
        if parsed:
            self._revoked_tokens.add(parsed.jti)
            return True
        return False
    
    def _hash_password(self, password: str) -> str:
        """Hash password with salt."""
        salt = secrets.token_hex(16)
        hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}:{hash_obj.hex()}"
    
    def _verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify password against stored hash."""
        try:
            salt, hash_hex = stored_hash.split(':')
            hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return hmac.compare_digest(hash_obj.hex(), hash_hex)
        except:
            return False
    
    def _create_token(self, user_data: Dict) -> str:
        """Create a signed token."""
        now = time.time()
        payload = {
            "user_id": user_data["user_id"],
            "username": user_data["username"],
            "roles": user_data["roles"],
            "iat": now,
            "exp": now + self._token_expiry,
            "jti": secrets.token_hex(16)
        }
        
        payload_json = json.dumps(payload, separators=(',', ':'))
        payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode()
        
        signature = hmac.new(
            self.secret_key.encode(),
            payload_b64.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"{payload_b64}.{signature}"
    
    def _parse_token(self, token: str) -> Optional[Token]:
        """Parse and verify token signature."""
        try:
            parts = token.split('.')
            if len(parts) != 2:
                return None
            
            payload_b64, signature = parts
            
            expected_sig = hmac.new(
                self.secret_key.encode(),
                payload_b64.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_sig):
                return None
            
            payload_json = base64.urlsafe_b64decode(payload_b64).decode()
            payload = json.loads(payload_json)
            
            return Token(
                user_id=payload["user_id"],
                username=payload["username"],
                roles=payload["roles"],
                issued_at=payload["iat"],
                expires_at=payload["exp"],
                jti=payload["jti"]
            )
        except:
            return None


def require_permission(permission: Permission):
    """Decorator for permission checking."""
    def decorator(func):
        def wrapper(*args, user: User = None, **kwargs):
            if user is None:
                raise PermissionError("Authentication required")
            if not user.has_permission(permission):
                raise PermissionError(f"Permission denied: {permission.value}")
            return func(*args, user=user, **kwargs)
        return wrapper
    return decorator


# Global auth provider
_auth_provider: Optional[AuthProvider] = None

def get_auth() -> AuthProvider:
    """Get or create the global auth provider."""
    global _auth_provider
    if _auth_provider is None:
        _auth_provider = AuthProvider()
    return _auth_provider
