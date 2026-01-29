"""Task registry service for managing registered task definitions.

This implementation uses file-based persistence to ensure consistency
across multiple uvicorn workers without requiring explicit synchronization.
"""

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
from aiofiles import os as aios
from packaging import version as pkg_version

from task_framework.logging import logger
from task_framework.models.task_definition import TaskDefinition


class TaskRegistry:
    """Registry for managing multiple task definitions with versioning.
    
    Uses file-based persistence to ensure consistency across workers.
    Provides methods to register, look up, and manage task definitions.
    Supports multiple versions of the same task running simultaneously.
    """
    
    def __init__(self, data_dir: Optional[str] = None) -> None:
        """Initialize TaskRegistry.
        
        Args:
            data_dir: Directory for storing registry file. If None, uses in-memory only.
        """
        self._data_dir = Path(data_dir) if data_dir else None
        self._registry_file = self._data_dir / "task_registry.json" if self._data_dir else None
        
        # In-memory cache (always maintained for fast function access)
        self._tasks: Dict[str, Dict[str, TaskDefinition]] = {}
        self._by_full_id: Dict[str, TaskDefinition] = {}
        
        # File modification tracking
        self._last_mtime: float = 0.0
        self._lock = threading.Lock()
    
    def _serialize_task_def(self, task_def: TaskDefinition) -> Dict[str, Any]:
        """Serialize TaskDefinition for JSON storage."""
        return {
            "task_id": task_def.task_id,
            "version": task_def.version,
            "name": task_def.name,
            "description": task_def.description,
            "entry_point": task_def.entry_point,
            "input_schemas": task_def.input_schemas,
            "output_schemas": task_def.output_schemas,
            "requirements": task_def.requirements,
            "sdk_version": task_def.sdk_version,
            "base_path": task_def.base_path,
            "code_path": task_def.code_path,
            "venv_path": task_def.venv_path,
            "data_path": task_def.data_path,
            "storage_path": task_def.storage_path,
            "zip_path": task_def.zip_path,
            "zip_hash": task_def.zip_hash,
            "deployed_at": task_def.deployed_at.isoformat() if task_def.deployed_at else None,
        }
    
    def _deserialize_task_def(self, data: Dict[str, Any]) -> TaskDefinition:
        """Deserialize TaskDefinition from JSON storage."""
        deployed_at = None
        if data.get("deployed_at"):
            try:
                deployed_at = datetime.fromisoformat(data["deployed_at"])
            except (ValueError, TypeError):
                pass
        
        return TaskDefinition(
            task_id=data["task_id"],
            version=data["version"],
            name=data["name"],
            description=data.get("description", ""),
            entry_point=data["entry_point"],
            input_schemas=data.get("input_schemas", []),
            output_schemas=data.get("output_schemas", []),
            requirements=data.get("requirements", []),
            sdk_version=data.get("sdk_version"),
            base_path=data["base_path"],
            code_path=data["code_path"],
            venv_path=data["venv_path"],
            data_path=data["data_path"],
            storage_path=data["storage_path"],
            zip_path=data.get("zip_path"),
            zip_hash=data.get("zip_hash"),
            deployed_at=deployed_at,
        )
    
    async def _load_from_file(self) -> bool:
        """Load registry from file if it has been modified.
        
        Returns:
            True if registry was reloaded, False if already up-to-date
        """
        if not self._registry_file or not self._registry_file.exists():
            return False
        
        try:
            mtime = self._registry_file.stat().st_mtime
            if mtime <= self._last_mtime:
                return False  # File hasn't changed
            
            async with aiofiles.open(self._registry_file, "r") as f:
                content = await f.read()
                data = json.loads(content)
            
            # Rebuild in-memory structures
            new_tasks: Dict[str, Dict[str, TaskDefinition]] = {}
            new_by_full_id: Dict[str, TaskDefinition] = {}
            
            for task_data in data.get("tasks", []):
                try:
                    task_def = self._deserialize_task_def(task_data)
                    task_id = task_def.task_id
                    version = task_def.version
                    
                    if task_id not in new_tasks:
                        new_tasks[task_id] = {}
                    new_tasks[task_id][version] = task_def
                    new_by_full_id[task_def.full_id] = task_def
                except Exception as e:
                    logger.warning(
                        "task_registry.deserialize_failed",
                        error=str(e),
                        task_data=task_data,
                    )
            
            with self._lock:
                # Preserve task functions from old registry
                for full_id, new_def in new_by_full_id.items():
                    if full_id in self._by_full_id:
                        old_def = self._by_full_id[full_id]
                        if old_def._task_function:
                            new_def.set_task_function(old_def._task_function)
                
                self._tasks = new_tasks
                self._by_full_id = new_by_full_id
                self._last_mtime = mtime
            
            logger.debug(
                "task_registry.loaded_from_file",
                task_count=len(new_by_full_id),
            )
            return True
            
        except Exception as e:
            logger.error(
                "task_registry.load_failed",
                error=str(e),
                exc_info=True,
            )
            return False
    
    async def _save_to_file(self) -> None:
        """Save registry state to file."""
        if not self._registry_file:
            return
        
        try:
            # Ensure directory exists
            await aios.makedirs(self._data_dir, exist_ok=True)
            
            # Serialize all tasks
            tasks_data = []
            with self._lock:
                for task_def in self._by_full_id.values():
                    tasks_data.append(self._serialize_task_def(task_def))
            
            data = {
                "version": 1,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "tasks": tasks_data,
            }
            
            # Write atomically
            temp_file = self._registry_file.with_suffix(".tmp")
            async with aiofiles.open(temp_file, "w") as f:
                await f.write(json.dumps(data, indent=2))
            
            await aios.rename(str(temp_file), str(self._registry_file))
            
            # Update mtime cache
            self._last_mtime = self._registry_file.stat().st_mtime
            
            logger.debug(
                "task_registry.saved_to_file",
                task_count=len(tasks_data),
            )
            
        except Exception as e:
            logger.error(
                "task_registry.save_failed",
                error=str(e),
                exc_info=True,
            )
    
    async def ensure_loaded(self) -> None:
        """Ensure registry is loaded from file (if stale).
        
        Call this before read operations to ensure consistency.
        """
        await self._load_from_file()
    
    def register(self, task_definition: TaskDefinition) -> None:
        """Register a task definition.
        
        Args:
            task_definition: TaskDefinition to register
            
        Raises:
            ValueError: If a task with the same task_id and version already exists
        """
        task_id = task_definition.task_id
        version = task_definition.version
        full_id = task_definition.full_id
        
        with self._lock:
            # Check for existing registration
            if full_id in self._by_full_id:
                raise ValueError(f"Task {task_id} version {version} is already registered")
            
            # Register in primary registry
            if task_id not in self._tasks:
                self._tasks[task_id] = {}
            self._tasks[task_id][version] = task_definition
            
            # Add to quick lookup
            self._by_full_id[full_id] = task_definition
        
        logger.info(
            "task_registry.registered",
            task_id=task_id,
            version=version,
            full_id=full_id,
        )
    
    async def register_and_save(self, task_definition: TaskDefinition) -> None:
        """Register a task definition and save to file.
        
        Args:
            task_definition: TaskDefinition to register
        """
        self.register(task_definition)
        await self._save_to_file()
    
    def unregister(self, task_id: str, version: Optional[str] = None) -> List[TaskDefinition]:
        """Unregister task definitions.
        
        Args:
            task_id: Task identifier
            version: Optional version to unregister. If None, unregisters all versions.
            
        Returns:
            List of unregistered TaskDefinition objects
        """
        unregistered = []
        
        with self._lock:
            if task_id not in self._tasks:
                return unregistered
            
            if version:
                # Unregister specific version
                if version in self._tasks[task_id]:
                    task_def = self._tasks[task_id].pop(version)
                    full_id = task_def.full_id
                    if full_id in self._by_full_id:
                        del self._by_full_id[full_id]
                    unregistered.append(task_def)
                    
                    # Clean up empty task entry
                    if not self._tasks[task_id]:
                        del self._tasks[task_id]
                        
                    logger.info(
                        "task_registry.unregistered",
                        task_id=task_id,
                        version=version,
                    )
            else:
                # Unregister all versions
                for ver, task_def in list(self._tasks[task_id].items()):
                    full_id = task_def.full_id
                    if full_id in self._by_full_id:
                        del self._by_full_id[full_id]
                    unregistered.append(task_def)
                    
                del self._tasks[task_id]
                
                logger.info(
                    "task_registry.unregistered_all",
                    task_id=task_id,
                    versions_count=len(unregistered),
                )
        
        return unregistered
    
    async def unregister_and_save(self, task_id: str, version: Optional[str] = None) -> List[TaskDefinition]:
        """Unregister task definitions and save to file.
        
        Args:
            task_id: Task identifier
            version: Optional version to unregister.
            
        Returns:
            List of unregistered TaskDefinition objects
        """
        result = self.unregister(task_id, version)
        if result:
            await self._save_to_file()
        return result
    
    def get(self, task_id: str, version: Optional[str] = None) -> Optional[TaskDefinition]:
        """Get a task definition by task_id and optional version.
        
        Args:
            task_id: Task identifier
            version: Optional version. If None, returns the latest version.
            
        Returns:
            TaskDefinition if found, None otherwise
        """
        with self._lock:
            if task_id not in self._tasks:
                return None
            
            if version:
                return self._tasks[task_id].get(version)
            
            # Return latest version
            return self._get_latest_version_unlocked(task_id)
    
    def get_by_full_id(self, full_id: str) -> Optional[TaskDefinition]:
        """Get a task definition by full_id (task_id:version).
        
        Args:
            full_id: Full task identifier in format 'task_id:version'
            
        Returns:
            TaskDefinition if found, None otherwise
        """
        with self._lock:
            return self._by_full_id.get(full_id)
    
    def _get_latest_version_unlocked(self, task_id: str) -> Optional[TaskDefinition]:
        """Get latest version (must hold lock)."""
        if task_id not in self._tasks:
            return None
        
        versions = list(self._tasks[task_id].keys())
        if not versions:
            return None
        
        try:
            sorted_versions = sorted(versions, key=lambda v: pkg_version.parse(v), reverse=True)
            latest_version = sorted_versions[0]
        except Exception:
            sorted_versions = sorted(versions, reverse=True)
            latest_version = sorted_versions[0]
        
        return self._tasks[task_id].get(latest_version)
    
    def get_latest_version(self, task_id: str) -> Optional[TaskDefinition]:
        """Get the latest version of a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            TaskDefinition for latest version, or None if task not found
        """
        with self._lock:
            return self._get_latest_version_unlocked(task_id)
    
    def get_versions(self, task_id: str) -> List[str]:
        """Get all available versions for a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            List of version strings, sorted newest first
        """
        with self._lock:
            if task_id not in self._tasks:
                return []
            
            versions = list(self._tasks[task_id].keys())
            
            try:
                return sorted(versions, key=lambda v: pkg_version.parse(v), reverse=True)
            except Exception:
                return sorted(versions, reverse=True)
    
    def list_tasks(self) -> List[str]:
        """List all registered task IDs.
        
        Returns:
            List of task identifiers
        """
        with self._lock:
            return list(self._tasks.keys())
    
    def list_all(self) -> List[TaskDefinition]:
        """List all registered task definitions.
        
        Returns:
            List of all TaskDefinition objects
        """
        with self._lock:
            return list(self._by_full_id.values())
    
    def list_by_task(self, task_id: str) -> List[TaskDefinition]:
        """List all versions of a specific task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            List of TaskDefinition objects for all versions
        """
        with self._lock:
            if task_id not in self._tasks:
                return []
            return list(self._tasks[task_id].values())
    
    def is_registered(self, task_id: str, version: Optional[str] = None) -> bool:
        """Check if a task is registered.
        
        Args:
            task_id: Task identifier
            version: Optional version to check
            
        Returns:
            True if registered, False otherwise
        """
        with self._lock:
            if task_id not in self._tasks:
                return False
            
            if version:
                return version in self._tasks[task_id]
            
            return True
    
    def count(self) -> int:
        """Get total number of registered task definitions.
        
        Returns:
            Total count of task definitions (all versions)
        """
        with self._lock:
            return len(self._by_full_id)
    
    def count_tasks(self) -> int:
        """Get number of unique tasks (not counting versions).
        
        Returns:
            Count of unique task IDs
        """
        with self._lock:
            return len(self._tasks)
    
    def get_single_task(self) -> Optional[TaskDefinition]:
        """Get the single registered task if only one exists.
        
        Returns:
            TaskDefinition if exactly one task (any version) is registered,
            None otherwise
        """
        with self._lock:
            if len(self._tasks) != 1:
                return None
            
            task_id = list(self._tasks.keys())[0]
            return self._get_latest_version_unlocked(task_id)
    
    def resolve_task(self, task_id: Optional[str], version: Optional[str] = None) -> Optional[TaskDefinition]:
        """Resolve a task from optional task_id and version.
        
        Args:
            task_id: Optional task identifier
            version: Optional version
            
        Returns:
            TaskDefinition if resolved, None otherwise
        """
        if task_id:
            return self.get(task_id, version)
        
        return self.get_single_task()
    
    def clear(self) -> None:
        """Clear all registered tasks."""
        with self._lock:
            self._tasks.clear()
            self._by_full_id.clear()
        logger.info("task_registry.cleared")
    
    async def clear_and_save(self) -> None:
        """Clear all registered tasks and save to file."""
        self.clear()
        await self._save_to_file()
