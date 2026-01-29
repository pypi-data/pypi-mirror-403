"""Credential service for managing server-level credentials."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from task_framework.logging import logger
from task_framework.models.credential import Credential, CredentialInfo
from task_framework.services.encryption_service import EncryptionService


class CredentialServiceError(Exception):
    """Exception raised for credential service errors."""
    pass


class CredentialService:
    """Service for CRUD operations on server-level credentials.
    
    Credentials are stored in an encrypted JSON file.
    """
    
    def __init__(
        self,
        base_path: str,
        encryption_service: Optional[EncryptionService] = None,
    ) -> None:
        """Initialize credential service.
        
        Args:
            base_path: Base path for data storage (e.g., ./data)
            encryption_service: Optional encryption service. If not provided,
                              will create one with auto-generated key.
        """
        self.base_path = Path(base_path)
        self.credentials_dir = self.base_path / "credentials"
        self.credentials_file = self.credentials_dir / "credentials.json"
        self.key_file = self.credentials_dir / "credentials.key"
        
        # Initialize encryption service
        if encryption_service:
            self.encryption = encryption_service
        else:
            self.encryption = EncryptionService(key_file_path=str(self.key_file))
        
        # In-memory cache of credentials
        self._credentials: Dict[str, Credential] = {}
        self._loaded = False
    
    async def _ensure_loaded(self) -> None:
        """Ensure credentials are loaded from disk."""
        if self._loaded:
            return
        
        self.credentials_dir.mkdir(parents=True, exist_ok=True)
        
        if self.credentials_file.exists():
            await self._load_from_disk()
        
        self._loaded = True
    
    async def _load_from_disk(self) -> None:
        """Load credentials from encrypted file."""
        try:
            encrypted_data = self.credentials_file.read_text()
            if not encrypted_data.strip():
                return
                
            decrypted_json = self.encryption.decrypt(encrypted_data)
            data = json.loads(decrypted_json)
            
            for name, cred_data in data.items():
                self._credentials[name] = Credential.model_validate(cred_data)
            
            logger.info(
                "credential_service.loaded",
                count=len(self._credentials),
            )
        except Exception as e:
            logger.error(
                "credential_service.load_failed",
                error=str(e),
            )
            raise CredentialServiceError(f"Failed to load credentials: {e}")
    
    async def _save_to_disk(self) -> None:
        """Save credentials to encrypted file."""
        try:
            self.credentials_dir.mkdir(parents=True, exist_ok=True)
            
            # Serialize credentials
            data = {
                name: cred.model_dump(mode="json")
                for name, cred in self._credentials.items()
            }
            json_data = json.dumps(data, default=str)
            
            # Encrypt and save
            encrypted_data = self.encryption.encrypt(json_data)
            self.credentials_file.write_text(encrypted_data)
            
            # Set restrictive permissions
            self.credentials_file.chmod(0o600)
            
            logger.debug(
                "credential_service.saved",
                count=len(self._credentials),
            )
        except Exception as e:
            logger.error(
                "credential_service.save_failed",
                error=str(e),
            )
            raise CredentialServiceError(f"Failed to save credentials: {e}")
    
    async def get(self, name: str) -> Optional[Credential]:
        """Get a credential by name.
        
        Args:
            name: Credential name
            
        Returns:
            Credential if found, None otherwise
        """
        await self._ensure_loaded()
        credential = self._credentials.get(name)
        
        if credential:
            logger.debug(
                "credential_service.accessed",
                credential_name=name,
            )
        
        return credential
    
    async def get_value(self, name: str) -> Optional[str]:
        """Get just the credential value.
        
        Args:
            name: Credential name
            
        Returns:
            Credential value if found, None otherwise
        """
        credential = await self.get(name)
        return credential.value if credential else None
    
    async def list_all(self) -> List[CredentialInfo]:
        """List all credentials (without values).
        
        Returns:
            List of CredentialInfo objects
        """
        await self._ensure_loaded()
        return [
            CredentialInfo.from_credential(cred)
            for cred in self._credentials.values()
        ]
    
    async def create_or_update(
        self,
        name: str,
        value: str,
        description: str = "",
        tags: Optional[List[str]] = None,
        expires_at: Optional[datetime] = None,
    ) -> Credential:
        """Create or update a credential.
        
        Args:
            name: Credential name
            value: Credential value
            description: Human-readable description
            tags: Optional tags for organization
            expires_at: Optional expiration time
            
        Returns:
            The created/updated credential
        """
        await self._ensure_loaded()
        
        now = datetime.now(timezone.utc)
        existing = self._credentials.get(name)
        
        if existing:
            # Update existing
            credential = Credential(
                name=name,
                value=value,
                description=description or existing.description,
                tags=tags if tags is not None else existing.tags,
                created_at=existing.created_at,
                updated_at=now,
                expires_at=expires_at if expires_at is not None else existing.expires_at,
            )
            logger.info(
                "credential_service.updated",
                credential_name=name,
            )
        else:
            # Create new
            credential = Credential(
                name=name,
                value=value,
                description=description,
                tags=tags or [],
                created_at=now,
                updated_at=now,
                expires_at=expires_at,
            )
            logger.info(
                "credential_service.created",
                credential_name=name,
            )
        
        self._credentials[name] = credential
        await self._save_to_disk()
        
        return credential
    
    async def delete(self, name: str) -> bool:
        """Delete a credential.
        
        Args:
            name: Credential name
            
        Returns:
            True if deleted, False if not found
        """
        await self._ensure_loaded()
        
        if name not in self._credentials:
            return False
        
        del self._credentials[name]
        await self._save_to_disk()
        
        logger.info(
            "credential_service.deleted",
            credential_name=name,
        )
        
        return True
    
    async def exists(self, name: str) -> bool:
        """Check if a credential exists.
        
        Args:
            name: Credential name
            
        Returns:
            True if exists
        """
        await self._ensure_loaded()
        return name in self._credentials
    
    async def get_multiple(self, names: List[str]) -> Dict[str, str]:
        """Get multiple credential values at once.
        
        Args:
            names: List of credential names
            
        Returns:
            Dict mapping names to values (missing credentials omitted)
        """
        await self._ensure_loaded()
        result = {}
        
        for name in names:
            credential = self._credentials.get(name)
            if credential and not credential.is_expired():
                result[name] = credential.value
        
        return result
