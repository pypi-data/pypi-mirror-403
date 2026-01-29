"""Encryption service for securing secrets at rest."""

import base64
import os
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from task_framework.logging import logger


class EncryptionService:
    """Service for encrypting and decrypting sensitive data.
    
    Uses Fernet (AES-128-CBC) for symmetric encryption.
    Key is derived from a master key using PBKDF2.
    """
    
    def __init__(
        self, 
        encryption_key: Optional[str] = None,
        key_file_path: Optional[str] = None,
    ) -> None:
        """Initialize encryption service.
        
        Args:
            encryption_key: Optional master encryption key (from env var).
                           If not provided, will generate/load from key_file_path.
            key_file_path: Path to store/load the encryption key file.
                          Defaults to data/credentials/credentials.key
        """
        self._key_file_path = Path(key_file_path) if key_file_path else None
        self._fernet: Optional[Fernet] = None
        self._master_key = encryption_key or os.getenv("ENCRYPTION_KEY")
        
    def _ensure_initialized(self) -> None:
        """Ensure the Fernet cipher is initialized."""
        if self._fernet is not None:
            return
            
        if self._master_key:
            # Derive key from provided master key
            self._fernet = self._create_fernet_from_key(self._master_key)
            logger.info("encryption_service.initialized_from_key")
        elif self._key_file_path:
            # Load or generate key file
            self._fernet = self._load_or_generate_key()
        else:
            raise ValueError(
                "EncryptionService requires either encryption_key or key_file_path"
            )
    
    def _create_fernet_from_key(self, master_key: str) -> Fernet:
        """Create Fernet cipher from a master key using PBKDF2.
        
        Args:
            master_key: The master key string
            
        Returns:
            Fernet cipher instance
        """
        # Use a fixed salt for reproducibility (the master key is the secret)
        salt = b"task-framework-salt-v1"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
        return Fernet(key)
    
    def _load_or_generate_key(self) -> Fernet:
        """Load existing key file or generate a new one.
        
        Returns:
            Fernet cipher instance
        """
        if not self._key_file_path:
            raise ValueError("key_file_path is required")
            
        self._key_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if self._key_file_path.exists():
            # Load existing key
            key = self._key_file_path.read_bytes()
            logger.info(
                "encryption_service.loaded_key",
                key_file=str(self._key_file_path),
            )
        else:
            # Generate new key
            key = Fernet.generate_key()
            self._key_file_path.write_bytes(key)
            # Set restrictive permissions (owner read/write only)
            self._key_file_path.chmod(0o600)
            logger.info(
                "encryption_service.generated_key",
                key_file=str(self._key_file_path),
            )
        
        return Fernet(key)
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext string.
        
        Args:
            plaintext: The string to encrypt
            
        Returns:
            Base64-encoded encrypted string
        """
        self._ensure_initialized()
        if self._fernet is None:
            raise RuntimeError("Encryption service not initialized")
            
        encrypted = self._fernet.encrypt(plaintext.encode())
        return encrypted.decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt an encrypted string.
        
        Args:
            ciphertext: Base64-encoded encrypted string
            
        Returns:
            Decrypted plaintext string
        """
        self._ensure_initialized()
        if self._fernet is None:
            raise RuntimeError("Encryption service not initialized")
            
        decrypted = self._fernet.decrypt(ciphertext.encode())
        return decrypted.decode()
    
    def is_initialized(self) -> bool:
        """Check if the encryption service is initialized.
        
        Returns:
            True if initialized
        """
        return self._fernet is not None
