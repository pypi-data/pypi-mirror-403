"""Elasticsearch-backed configuration service for task configuration at runtime.

Provides the same interface as the file-based ConfigurationService but stores
configuration data in Elasticsearch with application-level encryption.
"""

import base64
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from task_framework.logging import logger
from task_framework.models.credential import (
    ConfigurationStatus,
    Requirement,
    ResolvedConfiguration,
    TaskConfiguration,
)
from task_framework.repositories.elasticsearch.base import ElasticsearchRepository
from task_framework.repositories.elasticsearch.mappings import CONFIG_MAPPINGS
from task_framework.services.encryption_service import EncryptionService

if TYPE_CHECKING:
    from elasticsearch import AsyncElasticsearch
    from task_framework.models.task_definition import TaskDefinition


class ConfigurationError(Exception):
    """Exception raised for configuration errors."""
    pass


class ElasticsearchConfigurationService:
    """Elasticsearch-backed configuration service.
    
    Provides the same interface as the file-based ConfigurationService:
    - get_config / set_config / delete_config
    - get_configuration_status
    - resolve_configuration
    - get_vault_usage
    
    Configuration data is encrypted before storage in Elasticsearch.
    """
    
    def __init__(
        self,
        client: "AsyncElasticsearch",
        credential_store: Any,  # ElasticsearchCredentialStore or CredentialService
        encryption_service: EncryptionService,
        index_prefix: Optional[str] = None,
    ):
        """Initialize configuration service.
        
        Args:
            client: AsyncElasticsearch client
            credential_store: Credential store for vault lookups
            encryption_service: Service for encrypting/decrypting values
            index_prefix: Index prefix (default from env)
        """
        self._repo = _ConfigRepo(client, index_prefix)
        self.credential_service = credential_store
        self.encryption = encryption_service
    
    def _doc_id(self, task_id: str, version: str) -> str:
        """Generate document ID from task_id and version."""
        return f"{task_id}:{version}"
    
    async def get_config(self, task_id: str, version: str) -> Optional[TaskConfiguration]:
        """Get task configuration.
        
        Args:
            task_id: Task identifier
            version: Task version
            
        Returns:
            TaskConfiguration if exists, None otherwise
        """
        await self._repo.ensure_index(CONFIG_MAPPINGS)
        doc = await self._repo.get(self._doc_id(task_id, version))
        
        if not doc:
            return None
        
        try:
            # Decrypt the config values
            encrypted_values = doc.get("encrypted_values", "")
            if encrypted_values:
                encrypted_bytes = base64.b64decode(encrypted_values)
                decrypted_json = self.encryption.decrypt(encrypted_bytes.decode())
                config_values = json.loads(decrypted_json)
            else:
                config_values = {}
            
            return TaskConfiguration(
                task_id=task_id,
                version=version,
                config_values=config_values,
                updated_at=datetime.fromisoformat(doc["updated_at"].replace("Z", "+00:00")) if doc.get("updated_at") else datetime.now(timezone.utc),
            )
        except Exception as e:
            logger.error(
                "elasticsearch.config.decrypt_failed",
                task_id=task_id,
                version=version,
                error=str(e),
            )
            return None
    
    async def set_config(
        self,
        task_id: str,
        version: str,
        config_values: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> TaskConfiguration:
        """Set or update task configuration.
        
        Args:
            task_id: Task identifier
            version: Task version
            config_values: Configuration values (direct or vault refs)
            
        Returns:
            Updated TaskConfiguration
        """
        await self._repo.ensure_index(CONFIG_MAPPINGS)
        
        existing = await self.get_config(task_id, version)
        
        if existing:
            new_config_values = config_values if config_values is not None else existing.config_values
        else:
            new_config_values = config_values or {}
        
        now = datetime.now(timezone.utc)
        
        # Encrypt config values
        config_json = json.dumps(new_config_values, default=str)
        encrypted_value = self.encryption.encrypt(config_json)
        encrypted_b64 = base64.b64encode(encrypted_value.encode()).decode()
        
        doc = {
            "task_id": task_id,
            "version": version,
            "encrypted_values": encrypted_b64,
            "updated_at": now.isoformat().replace("+00:00", "Z"),
        }
        
        await self._repo.upsert(self._doc_id(task_id, version), doc)
        
        logger.info(
            "elasticsearch.config.updated",
            task_id=task_id,
            version=version,
            config_count=len(new_config_values),
        )
        
        return TaskConfiguration(
            task_id=task_id,
            version=version,
            config_values=new_config_values,
            updated_at=now,
        )
    
    async def delete_config(self, task_id: str, version: str) -> bool:
        """Delete task configuration.
        
        Args:
            task_id: Task identifier
            version: Task version
            
        Returns:
            True if deleted
        """
        await self._repo.ensure_index(CONFIG_MAPPINGS)
        
        existing = await self._repo.get(self._doc_id(task_id, version))
        if not existing:
            return False
        
        await self._repo.delete(self._doc_id(task_id, version))
        
        logger.info(
            "elasticsearch.config.deleted",
            task_id=task_id,
            version=version,
        )
        
        return True
    
    async def get_configuration_status(
        self,
        task_def: "TaskDefinition",
    ) -> ConfigurationStatus:
        """Get the configuration status for a task.
        
        Shows what's configured, what's missing, and whether the task is ready.
        
        Args:
            task_def: Task definition with requirements
            
        Returns:
            ConfigurationStatus with detailed info
        """
        config = await self.get_config(task_def.task_id, task_def.version)
        config_values = config.config_values if config else {}
        
        # Parse requirements from task definition
        requirements = self._parse_requirements(task_def)
        
        # Check each requirement
        requirements_status = []
        missing_required = []
        
        for req in requirements:
            config_entry = config_values.get(req.name)
            is_set = False
            current_value = None
            vault_key = None
            
            if config_entry:
                if config_entry.get("is_vault_ref"):
                    vault_key = config_entry.get("vault_key")
                    # Check if vault key exists
                    is_set = await self.credential_service.exists(vault_key) if vault_key else False
                else:
                    current_value = config_entry.get("value")
                    is_set = current_value is not None and current_value != ""
            
            # Check if required and missing
            if req.required and not is_set and req.default is None:
                missing_required.append(req.name)
            
            requirements_status.append({
                "name": req.name,
                "required": req.required,
                "description": req.description,
                "default": req.default,
                "is_vault_ref": config_entry.get("is_vault_ref") if config_entry else False,
                "vault_key": vault_key,
                "current_value": current_value,
                "is_set": is_set,
            })
        
        return ConfigurationStatus(
            task_id=task_def.task_id,
            version=task_def.version,
            requirements=requirements_status,
            config_values=config_values,
            ready=len(missing_required) == 0,
            missing_required=missing_required,
        )
    
    async def resolve_configuration(
        self,
        task_def: "TaskDefinition",
        runtime_overrides: Optional[Dict[str, str]] = None,
        validate: bool = True,
    ) -> ResolvedConfiguration:
        """Resolve complete configuration for task execution.
        
        Args:
            task_def: Task definition with requirements
            runtime_overrides: Optional per-thread overrides
            validate: Whether to validate required values
            
        Returns:
            ResolvedConfiguration with values ready for injection
            
        Raises:
            ConfigurationError: If required values are missing (when validate=True)
        """
        config = await self.get_config(task_def.task_id, task_def.version)
        config_values = config.config_values if config else {}
        
        # Parse requirements
        requirements = self._parse_requirements(task_def)
        
        # Resolve all values (priority: runtime override > config > default)
        resolved_env = {}
        resolved_secrets = {}
        missing = []
        
        for req in requirements:
            value = None
            is_secret = False
            
            # Check runtime override first
            if runtime_overrides and req.name in runtime_overrides:
                value = runtime_overrides[req.name]
            # Then stored config
            elif req.name in config_values:
                config_entry = config_values[req.name]
                if config_entry.get("is_vault_ref"):
                    vault_key = config_entry.get("vault_key")
                    if vault_key:
                        value = await self.credential_service.get_value(vault_key)
                        is_secret = True
                else:
                    value = config_entry.get("value")
            # Then default
            elif req.default is not None:
                value = req.default
            
            if value is not None:
                if is_secret:
                    resolved_secrets[req.name] = value
                else:
                    resolved_env[req.name] = value
            elif req.required and validate:
                missing.append(req.name)
        
        if missing and validate:
            raise ConfigurationError(
                f"Missing required configuration: {', '.join(missing)}"
            )
        
        logger.debug(
            "elasticsearch.config.resolved",
            task_id=task_def.task_id,
            version=task_def.version,
            env_count=len(resolved_env),
            secret_count=len(resolved_secrets),
        )
        
        return ResolvedConfiguration(
            env_vars=resolved_env,
            secrets=resolved_secrets,
        )
    
    def _parse_requirements(self, task_def: "TaskDefinition") -> List[Requirement]:
        """Parse requirements from task definition."""
        raw = getattr(task_def, "requirements", None) or []
        requirements = []
        
        for item in raw:
            if isinstance(item, dict):
                requirements.append(Requirement.model_validate(item))
            elif isinstance(item, Requirement):
                requirements.append(item)
        
        return requirements
    
    async def get_vault_usage(self, vault_key: str) -> List[Dict[str, str]]:
        """Get list of tasks using a specific vault entry.
        
        Scans all config documents in ES to find usage.
        
        Args:
            vault_key: Name of the vault entry
            
        Returns:
            List of dicts with task_id, version, and config_key fields
        """
        await self._repo.ensure_index(CONFIG_MAPPINGS)
        
        usage = []
        docs = await self._repo.list_all()
        
        for doc in docs:
            task_id = doc.get("task_id")
            version = doc.get("version")
            
            if not task_id or not version:
                continue
            
            try:
                # Decrypt and scan config values
                encrypted_values = doc.get("encrypted_values", "")
                if encrypted_values:
                    encrypted_bytes = base64.b64decode(encrypted_values)
                    decrypted_json = self.encryption.decrypt(encrypted_bytes.decode())
                    config_values = json.loads(decrypted_json)
                else:
                    config_values = {}
                
                for config_key, entry in config_values.items():
                    if entry.get("is_vault_ref") and entry.get("vault_key") == vault_key:
                        usage.append({
                            "task_id": task_id,
                            "version": version,
                            "config_key": config_key,
                        })
            except Exception as e:
                logger.warning(
                    "elasticsearch.config.scan_failed",
                    task_id=task_id,
                    version=version,
                    error=str(e),
                )
        
        return usage


class _ConfigRepo(ElasticsearchRepository):
    """Internal config repository."""
    
    INDEX_SUFFIX = "config"
    
    async def get(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get config document by ID."""
        return await self._get_document(doc_id)
    
    async def list_all(self) -> List[Dict[str, Any]]:
        """List all config documents."""
        result = await self._search(
            query={"match_all": {}},
            sort=[{"task_id": {"order": "asc"}}],
            size=1000,
        )
        return [hit["_source"] for hit in result.get("hits", {}).get("hits", [])]
    
    async def upsert(self, doc_id: str, doc: Dict[str, Any]) -> None:
        """Create or update config document."""
        await self._index_document(doc_id, doc, refresh=True)
    
    async def delete(self, doc_id: str) -> None:
        """Delete config document."""
        await self._delete_document(doc_id, refresh=True)
