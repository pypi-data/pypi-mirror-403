"""Configuration service for resolving task configuration at runtime."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from task_framework.logging import logger
from task_framework.models.credential import (
    ConfigurationStatus,
    Requirement,
    ResolvedConfiguration,
    TaskConfiguration,
)
from task_framework.services.credential_service import CredentialService

if TYPE_CHECKING:
    from task_framework.models.task_definition import TaskDefinition


class ConfigurationError(Exception):
    """Exception raised for configuration errors."""
    pass


class ConfigurationService:
    """Service for resolving task configuration at runtime.
    
    Unified architecture:
    - Task requirements (from task.yaml) - just key names
    - Task configuration - maps keys to values (direct or vault reference)
    - Vault (credentials) - encrypted key:value store
    
    Each config value can be:
    - Direct value: {"value": "actual_value", "is_vault_ref": false}
    - Vault reference: {"vault_key": "vault_entry_name", "is_vault_ref": true}
    
    Note: This service reads directly from disk on each request to ensure
    consistency across multiple workers. Configs are small JSON files and
    rarely accessed, so disk I/O is acceptable.
    """
    
    def __init__(
        self,
        base_path: str,
        credential_service: CredentialService,
    ) -> None:
        """Initialize configuration service.
        
        Args:
            base_path: Base path for data storage
            credential_service: Credential service (vault) for value resolution
        """
        self.base_path = Path(base_path)
        self.config_dir = self.base_path / "task_configs"
        self.credential_service = credential_service
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def _config_file(self, task_id: str, version: str) -> Path:
        """Get the config file path for a task."""
        return self.config_dir / task_id / version / "config.json"
    
    def _migrate_config(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate old config format to new unified format."""
        # If already has config_values, no migration needed
        if "config_values" in data:
            return data
        
        # Migrate from old format (env_vars + secret_mappings)
        config_values = {}
        
        # Migrate env_vars (direct values)
        old_env_vars = data.pop("env_vars", {})
        for key, value in old_env_vars.items():
            config_values[key] = {"value": value, "is_vault_ref": False}
        
        # Migrate secret_mappings (vault references)
        old_secret_mappings = data.pop("secret_mappings", {})
        for key, vault_key in old_secret_mappings.items():
            config_values[key] = {"vault_key": vault_key, "is_vault_ref": True}
        
        data["config_values"] = config_values
        return data
    
    def _read_config_from_disk(self, task_id: str, version: str) -> Optional[TaskConfiguration]:
        """Read a task configuration directly from disk.
        
        Args:
            task_id: Task identifier
            version: Task version
            
        Returns:
            TaskConfiguration if exists, None otherwise
        """
        config_file = self._config_file(task_id, version)
        if not config_file.exists():
            return None
        
        try:
            data = json.loads(config_file.read_text())
            # Handle migration from old format
            data = self._migrate_config(data)
            return TaskConfiguration.model_validate(data)
        except Exception as e:
            logger.warning(
                "configuration_service.read_config_failed",
                path=str(config_file),
                error=str(e),
            )
            return None
    
    def _save_config_to_disk(self, config: TaskConfiguration) -> None:
        """Save a task configuration to disk.
        
        Args:
            config: TaskConfiguration to save
        """
        config_file = self._config_file(config.task_id, config.version)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = config.model_dump(mode="json")
        config_file.write_text(json.dumps(data, indent=2, default=str))
        
        logger.debug(
            "configuration_service.saved",
            task_id=config.task_id,
            version=config.version,
        )
    
    async def get_config(self, task_id: str, version: str) -> Optional[TaskConfiguration]:
        """Get task configuration.
        
        Reads directly from disk to ensure consistency across workers.
        
        Args:
            task_id: Task identifier
            version: Task version
            
        Returns:
            TaskConfiguration if exists, None otherwise
        """
        return self._read_config_from_disk(task_id, version)
    
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
        existing = self._read_config_from_disk(task_id, version)
        
        if existing:
            # Replace config_values if provided
            new_config_values = config_values if config_values is not None else existing.config_values
        else:
            new_config_values = config_values or {}
        
        config = TaskConfiguration(
            task_id=task_id,
            version=version,
            config_values=new_config_values,
            updated_at=datetime.now(timezone.utc),
        )
        
        self._save_config_to_disk(config)
        
        logger.info(
            "configuration_service.config_updated",
            task_id=task_id,
            version=version,
            config_count=len(new_config_values),
        )
        
        return config
    
    async def delete_config(self, task_id: str, version: str) -> bool:
        """Delete task configuration.
        
        Args:
            task_id: Task identifier
            version: Task version
            
        Returns:
            True if deleted
        """
        config_file = self._config_file(task_id, version)
        if not config_file.exists():
            return False
        
        config_file.unlink()
        
        logger.info(
            "configuration_service.config_deleted",
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
            "configuration_service.resolved",
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
        
        Scans all config files on disk to find usage.
        
        Args:
            vault_key: Name of the vault entry
            
        Returns:
            List of dicts with task_id, version, and config_key fields
        """
        usage = []
        
        if not self.config_dir.exists():
            return usage
        
        # Scan all config files on disk
        for task_dir in self.config_dir.iterdir():
            if task_dir.is_dir():
                for version_dir in task_dir.iterdir():
                    if version_dir.is_dir():
                        config_file = version_dir / "config.json"
                        if config_file.exists():
                            try:
                                data = json.loads(config_file.read_text())
                                config_values = data.get("config_values", {})
                                for config_key, entry in config_values.items():
                                    if entry.get("is_vault_ref") and entry.get("vault_key") == vault_key:
                                        usage.append({
                                            "task_id": task_dir.name,
                                            "version": version_dir.name,
                                            "config_key": config_key,
                                        })
                            except Exception as e:
                                logger.warning(
                                    "configuration_service.scan_config_failed",
                                    path=str(config_file),
                                    error=str(e),
                                )
        
        return usage
