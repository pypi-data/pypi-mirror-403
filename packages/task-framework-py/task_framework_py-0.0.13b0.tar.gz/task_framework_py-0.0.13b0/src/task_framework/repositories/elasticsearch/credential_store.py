"""Elasticsearch implementation of credential storage.

Stores encrypted credentials in Elasticsearch with application-level encryption.
"""

import base64
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from task_framework.logging import logger
from task_framework.models.credential import Credential, CredentialInfo
from task_framework.repositories.elasticsearch.base import ElasticsearchRepository
from task_framework.repositories.elasticsearch.mappings import CREDENTIAL_MAPPINGS
from task_framework.services.encryption_service import EncryptionService


class ElasticsearchCredentialStore:
    """Elasticsearch-backed credential storage with encryption.
    
    Credentials are encrypted before storage in ES and decrypted on retrieval.
    The encryption key must be managed externally (via ENCRYPTION_KEY env var).
    """
    
    def __init__(
        self,
        client: "AsyncElasticsearch",
        encryption_service: EncryptionService,
        index_prefix: Optional[str] = None,
    ):
        """Initialize credential store.
        
        Args:
            client: AsyncElasticsearch client
            encryption_service: Service for encrypting/decrypting values
            index_prefix: Index prefix (default from env)
        """
        self._repo = _CredentialRepo(client, index_prefix)
        self.encryption = encryption_service
    
    async def get(self, name: str) -> Optional[Credential]:
        """Get a credential by name.
        
        Args:
            name: Credential name (used as document ID)
            
        Returns:
            Decrypted Credential if found, None otherwise
        """
        await self._repo.ensure_index(CREDENTIAL_MAPPINGS)
        doc = await self._repo.get(name)
        
        if not doc:
            return None
        
        try:
            # Decrypt the value
            encrypted_value = doc.get("encrypted_value", "")
            if encrypted_value:
                # Base64 decode and decrypt
                encrypted_bytes = base64.b64decode(encrypted_value)
                decrypted_value = self.encryption.decrypt(encrypted_bytes.decode())
            else:
                decrypted_value = ""
            
            credential = Credential(
                name=doc["name"],
                value=decrypted_value,
                description=doc.get("description", ""),
                tags=doc.get("tags", []),
                created_at=datetime.fromisoformat(doc["created_at"].replace("Z", "+00:00")) if doc.get("created_at") else datetime.now(timezone.utc),
                updated_at=datetime.fromisoformat(doc["updated_at"].replace("Z", "+00:00")) if doc.get("updated_at") else datetime.now(timezone.utc),
                expires_at=datetime.fromisoformat(doc["expires_at"].replace("Z", "+00:00")) if doc.get("expires_at") else None,
            )
            
            logger.debug(
                "elasticsearch.credential.accessed",
                credential_name=name,
            )
            
            return credential
            
        except Exception as e:
            logger.error(
                "elasticsearch.credential.decrypt_failed",
                credential_name=name,
                error=str(e),
            )
            return None
    
    async def get_value(self, name: str) -> Optional[str]:
        """Get just the credential value.
        
        Args:
            name: Credential name
            
        Returns:
            Decrypted credential value if found, None otherwise
        """
        credential = await self.get(name)
        return credential.value if credential else None
    
    async def list_all(self) -> List[CredentialInfo]:
        """List all credentials (without values).
        
        Returns:
            List of CredentialInfo objects
        """
        await self._repo.ensure_index(CREDENTIAL_MAPPINGS)
        docs = await self._repo.list_all()
        
        result = []
        for doc in docs:
            try:
                result.append(CredentialInfo(
                    name=doc["name"],
                    description=doc.get("description", ""),
                    tags=doc.get("tags", []),
                    created_at=datetime.fromisoformat(doc["created_at"].replace("Z", "+00:00")) if doc.get("created_at") else datetime.now(timezone.utc),
                    updated_at=datetime.fromisoformat(doc["updated_at"].replace("Z", "+00:00")) if doc.get("updated_at") else datetime.now(timezone.utc),
                    expires_at=datetime.fromisoformat(doc["expires_at"].replace("Z", "+00:00")) if doc.get("expires_at") else None,
                ))
            except Exception as e:
                logger.warning(
                    "elasticsearch.credential.list_parse_error",
                    name=doc.get("name"),
                    error=str(e),
                )
                continue
        
        return result
    
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
            value: Credential value (will be encrypted)
            description: Human-readable description
            tags: Optional tags for organization
            expires_at: Optional expiration time
            
        Returns:
            The created/updated credential
        """
        await self._repo.ensure_index(CREDENTIAL_MAPPINGS)
        
        now = datetime.now(timezone.utc)
        existing = await self._repo.get(name)
        
        # Encrypt the value
        encrypted_value = self.encryption.encrypt(value)
        # Base64 encode for storage as binary
        encrypted_b64 = base64.b64encode(encrypted_value.encode()).decode()
        
        if existing:
            # Update existing - preserve created_at
            created_at = existing.get("created_at", now.isoformat().replace("+00:00", "Z"))
            action = "updated"
        else:
            created_at = now.isoformat().replace("+00:00", "Z")
            action = "created"
        
        doc = {
            "name": name,
            "encrypted_value": encrypted_b64,
            "description": description if description else (existing.get("description", "") if existing else ""),
            "tags": tags if tags is not None else (existing.get("tags", []) if existing else []),
            "created_at": created_at,
            "updated_at": now.isoformat().replace("+00:00", "Z"),
            "expires_at": expires_at.isoformat().replace("+00:00", "Z") if expires_at else (existing.get("expires_at") if existing else None),
        }
        
        await self._repo.upsert(name, doc)
        
        logger.info(
            f"elasticsearch.credential.{action}",
            credential_name=name,
        )
        
        # Return credential with decrypted value
        return Credential(
            name=name,
            value=value,
            description=doc["description"],
            tags=doc["tags"],
            created_at=datetime.fromisoformat(doc["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(doc["updated_at"].replace("Z", "+00:00")),
            expires_at=datetime.fromisoformat(doc["expires_at"].replace("Z", "+00:00")) if doc.get("expires_at") else None,
        )
    
    async def delete(self, name: str) -> bool:
        """Delete a credential.
        
        Args:
            name: Credential name
            
        Returns:
            True if deleted, False if not found
        """
        await self._repo.ensure_index(CREDENTIAL_MAPPINGS)
        
        existing = await self._repo.get(name)
        if not existing:
            return False
        
        await self._repo.delete(name)
        
        logger.info(
            "elasticsearch.credential.deleted",
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
        await self._repo.ensure_index(CREDENTIAL_MAPPINGS)
        doc = await self._repo.get(name)
        return doc is not None
    
    async def get_multiple(self, names: List[str]) -> Dict[str, str]:
        """Get multiple credential values at once.
        
        Args:
            names: List of credential names
            
        Returns:
            Dict mapping names to values (missing/expired credentials omitted)
        """
        result = {}
        
        for name in names:
            credential = await self.get(name)
            if credential and not credential.is_expired():
                result[name] = credential.value
        
        return result


class _CredentialRepo(ElasticsearchRepository):
    """Internal credential repository."""
    
    INDEX_SUFFIX = "credentials"
    
    async def get(self, name: str) -> Optional[Dict[str, Any]]:
        """Get credential document by name."""
        return await self._get_document(name)
    
    async def list_all(self) -> List[Dict[str, Any]]:
        """List all credential documents."""
        result = await self._search(
            query={"match_all": {}},
            sort=[{"name": {"order": "asc"}}],
            size=1000,
        )
        return [hit["_source"] for hit in result.get("hits", {}).get("hits", [])]
    
    async def upsert(self, name: str, doc: Dict[str, Any]) -> None:
        """Create or update credential document."""
        await self._index_document(name, doc, refresh=True)
    
    async def delete(self, name: str) -> None:
        """Delete credential document."""
        await self._delete_document(name, refresh=True)
