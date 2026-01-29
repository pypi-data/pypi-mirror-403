"""File-based Task Registry Store implementation."""

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
from aiofiles import os as aios
from packaging import version as pkg_version

from task_framework.interfaces.task_registry_store import TaskRegistryStore
from task_framework.logging import logger
from task_framework.models.task_definition import TaskDefinition


class FileTaskRegistryStore(TaskRegistryStore):
    """File-based implementation of TaskRegistryStore.
    
    Stores task definitions in a JSON file for persistence across restarts
    and consistency across multiple workers.
    """
    
    def __init__(self, data_dir: str) -> None:
        """Initialize FileTaskRegistryStore.
        
        Args:
            data_dir: Directory for storing the registry file
        """
        self._data_dir = Path(data_dir)
        self._registry_file = self._data_dir / "task_registry.json"
        
        # In-memory cache for fast lookups
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
            base_path=data["base_path"],
            code_path=data["code_path"],
            venv_path=data["venv_path"],
            data_path=data["data_path"],
            storage_path=data["storage_path"],
            zip_path=data.get("zip_path"),
            zip_hash=data.get("zip_hash"),
            deployed_at=deployed_at,
        )
    
    async def _ensure_loaded(self) -> None:
        """Ensure registry is loaded from file if modified."""
        if not self._registry_file.exists():
            return
        
        try:
            mtime = self._registry_file.stat().st_mtime
            if mtime <= self._last_mtime:
                return
            
            async with aiofiles.open(self._registry_file, "r") as f:
                content = await f.read()
                data = json.loads(content)
            
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
                        "file_task_registry_store.deserialize_failed",
                        error=str(e),
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
                "file_task_registry_store.loaded",
                task_count=len(new_by_full_id),
            )
            
        except Exception as e:
            logger.error(
                "file_task_registry_store.load_failed",
                error=str(e),
                exc_info=True,
            )
    
    async def _save_to_file(self) -> None:
        """Save registry state to file."""
        try:
            await aios.makedirs(self._data_dir, exist_ok=True)
            
            tasks_data = []
            with self._lock:
                for task_def in self._by_full_id.values():
                    tasks_data.append(self._serialize_task_def(task_def))
            
            data = {
                "version": 1,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "tasks": tasks_data,
            }
            
            temp_file = self._registry_file.with_suffix(".tmp")
            async with aiofiles.open(temp_file, "w") as f:
                await f.write(json.dumps(data, indent=2))
            
            await aios.rename(str(temp_file), str(self._registry_file))
            self._last_mtime = self._registry_file.stat().st_mtime
            
            logger.debug(
                "file_task_registry_store.saved",
                task_count=len(tasks_data),
            )
            
        except Exception as e:
            logger.error(
                "file_task_registry_store.save_failed",
                error=str(e),
                exc_info=True,
            )
    
    async def load(self) -> List[TaskDefinition]:
        """Load all task definitions from storage."""
        await self._ensure_loaded()
        with self._lock:
            return list(self._by_full_id.values())
    
    async def save_all(self, tasks: List[TaskDefinition]) -> None:
        """Save all task definitions to storage (full replacement)."""
        with self._lock:
            self._tasks.clear()
            self._by_full_id.clear()
            
            for task_def in tasks:
                task_id = task_def.task_id
                if task_id not in self._tasks:
                    self._tasks[task_id] = {}
                self._tasks[task_id][task_def.version] = task_def
                self._by_full_id[task_def.full_id] = task_def
        
        await self._save_to_file()
    
    async def register(self, task_def: TaskDefinition) -> None:
        """Register a single task definition."""
        await self._ensure_loaded()
        
        task_id = task_def.task_id
        version = task_def.version
        full_id = task_def.full_id
        
        with self._lock:
            if full_id in self._by_full_id:
                raise ValueError(f"Task {task_id} version {version} is already registered")
            
            if task_id not in self._tasks:
                self._tasks[task_id] = {}
            self._tasks[task_id][version] = task_def
            self._by_full_id[full_id] = task_def
        
        await self._save_to_file()
        
        logger.info(
            "file_task_registry_store.registered",
            task_id=task_id,
            version=version,
        )
    
    async def unregister(self, task_id: str, version: Optional[str] = None) -> List[TaskDefinition]:
        """Unregister task definition(s)."""
        await self._ensure_loaded()
        
        unregistered = []
        
        with self._lock:
            if task_id not in self._tasks:
                return unregistered
            
            if version:
                if version in self._tasks[task_id]:
                    task_def = self._tasks[task_id].pop(version)
                    if task_def.full_id in self._by_full_id:
                        del self._by_full_id[task_def.full_id]
                    unregistered.append(task_def)
                    
                    if not self._tasks[task_id]:
                        del self._tasks[task_id]
            else:
                for ver, task_def in list(self._tasks[task_id].items()):
                    if task_def.full_id in self._by_full_id:
                        del self._by_full_id[task_def.full_id]
                    unregistered.append(task_def)
                
                del self._tasks[task_id]
        
        if unregistered:
            await self._save_to_file()
            logger.info(
                "file_task_registry_store.unregistered",
                task_id=task_id,
                version=version,
                count=len(unregistered),
            )
        
        return unregistered
    
    async def get(self, task_id: str, version: Optional[str] = None) -> Optional[TaskDefinition]:
        """Get a task definition."""
        await self._ensure_loaded()
        
        with self._lock:
            if task_id not in self._tasks:
                return None
            
            if version:
                return self._tasks[task_id].get(version)
            
            # Return latest version
            versions = list(self._tasks[task_id].keys())
            if not versions:
                return None
            
            try:
                sorted_versions = sorted(versions, key=lambda v: pkg_version.parse(v), reverse=True)
                latest = sorted_versions[0]
            except Exception:
                latest = sorted(versions, reverse=True)[0]
            
            return self._tasks[task_id].get(latest)
    
    async def get_by_full_id(self, full_id: str) -> Optional[TaskDefinition]:
        """Get a task definition by full ID."""
        await self._ensure_loaded()
        with self._lock:
            return self._by_full_id.get(full_id)
    
    async def list_all(self) -> List[TaskDefinition]:
        """List all registered task definitions."""
        await self._ensure_loaded()
        with self._lock:
            return list(self._by_full_id.values())
    
    async def list_task_ids(self) -> List[str]:
        """List all unique task IDs."""
        await self._ensure_loaded()
        with self._lock:
            return list(self._tasks.keys())
    
    async def list_versions(self, task_id: str) -> List[str]:
        """List all versions for a task."""
        await self._ensure_loaded()
        with self._lock:
            if task_id not in self._tasks:
                return []
            
            versions = list(self._tasks[task_id].keys())
            try:
                return sorted(versions, key=lambda v: pkg_version.parse(v), reverse=True)
            except Exception:
                return sorted(versions, reverse=True)
    
    async def is_registered(self, task_id: str, version: Optional[str] = None) -> bool:
        """Check if a task is registered."""
        await self._ensure_loaded()
        with self._lock:
            if task_id not in self._tasks:
                return False
            
            if version:
                return version in self._tasks[task_id]
            
            return True
    
    async def count(self) -> int:
        """Get total number of registered task definitions."""
        await self._ensure_loaded()
        with self._lock:
            return len(self._by_full_id)
    
    async def clear(self) -> None:
        """Clear all registered tasks from storage."""
        with self._lock:
            self._tasks.clear()
            self._by_full_id.clear()
        
        await self._save_to_file()
        logger.info("file_task_registry_store.cleared")
