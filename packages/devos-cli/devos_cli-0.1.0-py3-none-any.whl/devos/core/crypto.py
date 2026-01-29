"""Simple encryption for environment variables."""

import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
from pathlib import Path


class Crypto:
    """Simple encryption for local secrets."""
    
    def __init__(self, config_dir: Path):
        """Initialize crypto with key file."""
        self.config_dir = config_dir
        self.key_file = config_dir / ".key"
        self._ensure_key()
    
    def _ensure_key(self):
        """Ensure encryption key exists."""
        if not self.key_file.exists():
            # Generate new key
            key = Fernet.generate_key()
            self.key_file.write_bytes(key)
            # Set restrictive permissions
            self.key_file.chmod(0o600)
    
    def _get_key(self) -> bytes:
        """Get encryption key."""
        return self.key_file.read_bytes()
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data."""
        key = self._get_key()
        f = Fernet(key)
        encrypted_data = f.encrypt(data.encode())
        return base64.b64encode(encrypted_data).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data."""
        key = self._get_key()
        f = Fernet(key)
        encrypted_bytes = base64.b64decode(encrypted_data.encode())
        decrypted_data = f.decrypt(encrypted_bytes)
        return decrypted_data.decode()
