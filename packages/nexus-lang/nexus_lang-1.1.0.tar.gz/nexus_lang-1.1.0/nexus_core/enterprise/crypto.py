"""
Nexus Encryption Layer
AES-GCM encryption for memory and slot data.
"""

import os
import hashlib
import base64
import json
from typing import Optional, Tuple
from dataclasses import dataclass

# Use cryptography library if available, fall back to basic implementation
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False


@dataclass
class EncryptedData:
    """Container for encrypted data with metadata."""
    ciphertext: bytes
    nonce: bytes
    tag: bytes = b""
    key_id: str = "default"
    algorithm: str = "AES-256-GCM"
    
    def to_bytes(self) -> bytes:
        """Serialize to bytes for storage."""
        header = json.dumps({
            "key_id": self.key_id,
            "algorithm": self.algorithm,
            "nonce": base64.b64encode(self.nonce).decode(),
            "tag": base64.b64encode(self.tag).decode() if self.tag else ""
        }).encode()
        header_len = len(header).to_bytes(4, 'little')
        return header_len + header + self.ciphertext
    
    @classmethod 
    def from_bytes(cls, data: bytes) -> 'EncryptedData':
        """Deserialize from bytes."""
        header_len = int.from_bytes(data[:4], 'little')
        header = json.loads(data[4:4+header_len].decode())
        ciphertext = data[4+header_len:]
        
        return cls(
            ciphertext=ciphertext,
            nonce=base64.b64decode(header["nonce"]),
            tag=base64.b64decode(header["tag"]) if header.get("tag") else b"",
            key_id=header.get("key_id", "default"),
            algorithm=header.get("algorithm", "AES-256-GCM")
        )


class KeyDerivation:
    """Key derivation functions."""
    
    @staticmethod
    def derive_key(password: str, salt: bytes = None, iterations: int = 100000) -> Tuple[bytes, bytes]:
        """Derive a 256-bit key from password using PBKDF2."""
        if salt is None:
            salt = os.urandom(16)
        
        if HAS_CRYPTOGRAPHY:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=iterations
            )
            key = kdf.derive(password.encode())
        else:
            key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, iterations)
        
        return key, salt
    
    @staticmethod
    def derive_key_from_master(master_key: bytes, context: str) -> bytes:
        """Derive a context-specific key from master key."""
        return hashlib.sha256(master_key + context.encode()).digest()


class NexusCrypto:
    """
    Encryption manager for Nexus data.
    
    Features:
    - AES-256-GCM authenticated encryption
    - Key derivation from passwords
    - Key rotation support
    - Encrypted memory and slot operations
    """
    
    def __init__(self, master_key: bytes = None, password: str = None):
        if master_key:
            self.master_key = master_key
        elif password:
            self.master_key, self._salt = KeyDerivation.derive_key(password)
        else:
            self.master_key = os.urandom(32)
            self._salt = None
        
        self._key_cache: dict = {}
    
    def encrypt(self, plaintext: bytes, key_id: str = "default") -> EncryptedData:
        """Encrypt data using AES-256-GCM."""
        key = self._get_key(key_id)
        nonce = os.urandom(12)  # 96-bit nonce for GCM
        
        if HAS_CRYPTOGRAPHY:
            aesgcm = AESGCM(key)
            ciphertext = aesgcm.encrypt(nonce, plaintext, None)
            # Tag is appended to ciphertext in cryptography library
            return EncryptedData(
                ciphertext=ciphertext,
                nonce=nonce,
                key_id=key_id
            )
        else:
            # Fallback: XOR encryption (NOT SECURE - for demo only)
            # In production, require cryptography library
            keystream = self._generate_keystream(key, nonce, len(plaintext))
            ciphertext = bytes(p ^ k for p, k in zip(plaintext, keystream))
            tag = hashlib.sha256(key + nonce + ciphertext).digest()[:16]
            return EncryptedData(
                ciphertext=ciphertext,
                nonce=nonce,
                tag=tag,
                key_id=key_id
            )
    
    def decrypt(self, encrypted: EncryptedData) -> bytes:
        """Decrypt data."""
        key = self._get_key(encrypted.key_id)
        
        if HAS_CRYPTOGRAPHY:
            aesgcm = AESGCM(key)
            return aesgcm.decrypt(encrypted.nonce, encrypted.ciphertext, None)
        else:
            # Verify tag first
            expected_tag = hashlib.sha256(key + encrypted.nonce + encrypted.ciphertext).digest()[:16]
            if encrypted.tag and encrypted.tag != expected_tag:
                raise ValueError("Authentication failed - data may be corrupted")
            
            keystream = self._generate_keystream(key, encrypted.nonce, len(encrypted.ciphertext))
            return bytes(c ^ k for c, k in zip(encrypted.ciphertext, keystream))
    
    def encrypt_json(self, data: dict, key_id: str = "default") -> str:
        """Encrypt a JSON object and return base64 string."""
        plaintext = json.dumps(data).encode()
        encrypted = self.encrypt(plaintext, key_id)
        return base64.b64encode(encrypted.to_bytes()).decode()
    
    def decrypt_json(self, encrypted_b64: str) -> dict:
        """Decrypt a base64 encrypted JSON string."""
        encrypted_bytes = base64.b64decode(encrypted_b64)
        encrypted = EncryptedData.from_bytes(encrypted_bytes)
        plaintext = self.decrypt(encrypted)
        return json.loads(plaintext.decode())
    
    def _get_key(self, key_id: str) -> bytes:
        """Get or derive a key for the given ID."""
        if key_id not in self._key_cache:
            self._key_cache[key_id] = KeyDerivation.derive_key_from_master(
                self.master_key, key_id
            )
        return self._key_cache[key_id]
    
    def _generate_keystream(self, key: bytes, nonce: bytes, length: int) -> bytes:
        """Generate a keystream for XOR encryption (fallback)."""
        keystream = b""
        counter = 0
        while len(keystream) < length:
            block = hashlib.sha256(key + nonce + counter.to_bytes(4, 'little')).digest()
            keystream += block
            counter += 1
        return keystream[:length]
    
    def rotate_key(self, old_key_id: str, new_key_id: str, data: bytes) -> bytes:
        """Re-encrypt data with a new key."""
        encrypted = EncryptedData.from_bytes(data)
        plaintext = self.decrypt(encrypted)
        new_encrypted = self.encrypt(plaintext, new_key_id)
        return new_encrypted.to_bytes()


class EncryptedMemory:
    """
    Wrapper for NexusMemory with transparent encryption.
    """
    
    def __init__(self, crypto: NexusCrypto = None, password: str = None):
        from nexus_core import NexusMemory
        self._memory = NexusMemory(create=False)
        self._crypto = crypto or NexusCrypto(password=password or "nexus-default-key")
    
    def read(self) -> dict:
        """Read and decrypt memory."""
        raw = self._memory.read()
        if not raw or raw == b"{}":
            return {}
        
        try:
            # Try to decrypt
            return self._crypto.decrypt_json(raw.decode())
        except:
            # Maybe it's not encrypted
            return json.loads(raw.decode())
    
    def write(self, data: dict) -> None:
        """Encrypt and write to memory."""
        encrypted = self._crypto.encrypt_json(data)
        self._memory.write(encrypted.encode())
    
    def close(self):
        """Close memory connection."""
        self._memory.close()


# Global crypto instance
_crypto: Optional[NexusCrypto] = None

def get_crypto(password: str = None) -> NexusCrypto:
    """Get or create the global crypto instance."""
    global _crypto
    if _crypto is None:
        _crypto = NexusCrypto(password=password)
    return _crypto
