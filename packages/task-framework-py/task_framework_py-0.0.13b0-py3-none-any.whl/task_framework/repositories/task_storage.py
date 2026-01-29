"""Task storage repository for managing task directories and isolated environments."""

import shutil
from pathlib import Path
from typing import List, Optional

import aiofiles
from aiofiles import os as aios

from task_framework.logging import logger


class TaskStorage:
    """Repository for managing task storage directories.
    
    Handles creation and management of isolated task directories:
    - {base_path}/tasks/{task_id}/{version}/code/
    - {base_path}/tasks/{task_id}/{version}/venv/
    - {base_path}/tasks/{task_id}/{version}/data/
    - {base_path}/tasks/{task_id}/{version}/storage/
    """
    
    def __init__(self, base_path: str = ".") -> None:
        """Initialize TaskStorage.
        
        Args:
            base_path: Base directory for task storage
        """
        self.base_path = Path(base_path)
        self.tasks_dir = self.base_path / "tasks"
        self.task_definitions_dir = self.base_path / "task_definitions"
    
    async def _ensure_base_directories(self) -> None:
        """Ensure base directories exist."""
        await aios.makedirs(self.tasks_dir, exist_ok=True)
        await aios.makedirs(self.task_definitions_dir, exist_ok=True)
    
    def get_task_base_path(self, task_id: str, version: str) -> Path:
        """Get base path for a task version.
        
        Args:
            task_id: Task identifier
            version: Task version
            
        Returns:
            Path to task version directory
        """
        return self.tasks_dir / task_id / version
    
    def get_code_path(self, task_id: str, version: str) -> Path:
        """Get code path for a task version.
        
        Args:
            task_id: Task identifier
            version: Task version
            
        Returns:
            Path to code directory
        """
        return self.get_task_base_path(task_id, version) / "code"
    
    def get_venv_path(self, task_id: str, version: str) -> Path:
        """Get venv path for a task version.
        
        Args:
            task_id: Task identifier
            version: Task version
            
        Returns:
            Path to virtual environment directory
        """
        return self.get_task_base_path(task_id, version) / "venv"
    
    def get_data_path(self, task_id: str, version: str) -> Path:
        """Get data path for a task version (isolated database).
        
        Args:
            task_id: Task identifier
            version: Task version
            
        Returns:
            Path to data directory
        """
        return self.get_task_base_path(task_id, version) / "data"
    
    def get_storage_path(self, task_id: str, version: str) -> Path:
        """Get storage path for a task version (isolated file storage).
        
        Args:
            task_id: Task identifier
            version: Task version
            
        Returns:
            Path to storage directory
        """
        return self.get_task_base_path(task_id, version) / "storage"
    
    async def create_task_directories(self, task_id: str, version: str) -> dict:
        """Create all directories for a task version.
        
        Args:
            task_id: Task identifier
            version: Task version
            
        Returns:
            Dict with paths to created directories
        """
        await self._ensure_base_directories()
        
        base_path = self.get_task_base_path(task_id, version)
        code_path = self.get_code_path(task_id, version)
        venv_path = self.get_venv_path(task_id, version)
        data_path = self.get_data_path(task_id, version)
        storage_path = self.get_storage_path(task_id, version)
        
        # Create all directories
        await aios.makedirs(code_path, exist_ok=True)
        await aios.makedirs(venv_path, exist_ok=True)
        await aios.makedirs(data_path, exist_ok=True)
        await aios.makedirs(storage_path, exist_ok=True)
        
        logger.info(
            "task_storage.directories_created",
            task_id=task_id,
            version=version,
            base_path=str(base_path),
        )
        
        return {
            "base_path": str(base_path),
            "code_path": str(code_path),
            "venv_path": str(venv_path),
            "data_path": str(data_path),
            "storage_path": str(storage_path),
        }
    
    async def task_exists(self, task_id: str, version: str) -> bool:
        """Check if a task version directory exists.
        
        Args:
            task_id: Task identifier
            version: Task version
            
        Returns:
            True if task directory exists
        """
        base_path = self.get_task_base_path(task_id, version)
        return await aios.path.exists(base_path)
    
    async def code_exists(self, task_id: str, version: str) -> bool:
        """Check if task code has been extracted.
        
        Args:
            task_id: Task identifier
            version: Task version
            
        Returns:
            True if code directory exists and is not empty
        """
        code_path = self.get_code_path(task_id, version)
        if not await aios.path.exists(code_path):
            return False
        
        # Check if directory has contents
        try:
            contents = await aios.listdir(code_path)
            return len(contents) > 0
        except Exception:
            return False
    
    async def venv_exists(self, task_id: str, version: str) -> bool:
        """Check if task venv has been created.
        
        Args:
            task_id: Task identifier
            version: Task version
            
        Returns:
            True if venv directory exists and appears valid
        """
        venv_path = self.get_venv_path(task_id, version)
        if not await aios.path.exists(venv_path):
            return False
        
        # Check for python executable (basic validation)
        python_path = venv_path / "bin" / "python"
        return await aios.path.exists(python_path)
    
    async def delete_task(self, task_id: str, version: Optional[str] = None) -> bool:
        """Delete task directories.
        
        Args:
            task_id: Task identifier
            version: Optional version to delete. If None, deletes all versions.
            
        Returns:
            True if deletion was successful
        """
        if version:
            # Delete specific version
            task_path = self.get_task_base_path(task_id, version)
            if await aios.path.exists(task_path):
                shutil.rmtree(task_path)
                logger.info(
                    "task_storage.deleted",
                    task_id=task_id,
                    version=version,
                )
                
                # Clean up parent if empty
                task_dir = self.tasks_dir / task_id
                try:
                    contents = await aios.listdir(task_dir)
                    if not contents:
                        await aios.rmdir(task_dir)
                except Exception:
                    pass
                
                return True
        else:
            # Delete all versions
            task_dir = self.tasks_dir / task_id
            if await aios.path.exists(task_dir):
                shutil.rmtree(task_dir)
                logger.info(
                    "task_storage.deleted_all",
                    task_id=task_id,
                )
                return True
        
        return False
    
    async def list_tasks(self) -> List[str]:
        """List all task IDs with stored directories.
        
        Returns:
            List of task identifiers
        """
        if not await aios.path.exists(self.tasks_dir):
            return []
        
        try:
            entries = await aios.listdir(self.tasks_dir)
            # Filter to only directories
            tasks = []
            for entry in entries:
                entry_path = self.tasks_dir / entry
                if await aios.path.isdir(entry_path):
                    tasks.append(entry)
            return tasks
        except Exception as e:
            logger.error(
                "task_storage.list_failed",
                error=str(e),
            )
            return []
    
    async def list_versions(self, task_id: str) -> List[str]:
        """List all versions for a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            List of version strings
        """
        task_dir = self.tasks_dir / task_id
        if not await aios.path.exists(task_dir):
            return []
        
        try:
            entries = await aios.listdir(task_dir)
            # Filter to only directories
            versions = []
            for entry in entries:
                entry_path = task_dir / entry
                if await aios.path.isdir(entry_path):
                    versions.append(entry)
            return versions
        except Exception as e:
            logger.error(
                "task_storage.list_versions_failed",
                task_id=task_id,
                error=str(e),
            )
            return []
    
    async def list_zip_files(self) -> List[Path]:
        """List all zip files in the task_definitions directory.
        
        Returns:
            List of Path objects to zip files
        """
        if not await aios.path.exists(self.task_definitions_dir):
            return []
        
        try:
            entries = await aios.listdir(self.task_definitions_dir)
            zip_files = []
            for entry in entries:
                if entry.endswith(".zip"):
                    zip_files.append(self.task_definitions_dir / entry)
            return zip_files
        except Exception as e:
            logger.error(
                "task_storage.list_zip_files_failed",
                error=str(e),
            )
            return []
    
    async def save_zip_file(self, filename: str, content: bytes) -> Path:
        """Save a zip file to the task_definitions directory.
        
        Args:
            filename: Name for the zip file
            content: Zip file content
            
        Returns:
            Path to the saved zip file
        """
        await self._ensure_base_directories()
        
        # Ensure filename ends with .zip
        if not filename.endswith(".zip"):
            filename = f"{filename}.zip"
        
        zip_path = self.task_definitions_dir / filename
        
        async with aiofiles.open(zip_path, "wb") as f:
            await f.write(content)
        
        logger.info(
            "task_storage.zip_saved",
            filename=filename,
            path=str(zip_path),
            size=len(content),
        )
        
        return zip_path
    
    async def delete_zip_file(self, zip_path: Path) -> bool:
        """Delete a zip file.
        
        Args:
            zip_path: Path to the zip file
            
        Returns:
            True if deleted successfully
        """
        if await aios.path.exists(zip_path):
            await aios.remove(zip_path)
            logger.info(
                "task_storage.zip_deleted",
                path=str(zip_path),
            )
            return True
        return False
    
    async def get_zip_file(self, task_id: str, version: str) -> Optional[tuple[bytes, str]]:
        """Get zip file content for a task version.
        
        Args:
            task_id: Task identifier
            version: Task version
            
        Returns:
            Tuple of (file_content, filename) if found, None otherwise
        """
        # Standard naming convention: {task_id}-{version}.zip
        filename = f"{task_id}-{version}.zip"
        zip_path = self.task_definitions_dir / filename
        
        if not await aios.path.exists(zip_path):
            logger.debug(
                "task_storage.zip_not_found",
                task_id=task_id,
                version=version,
                expected_path=str(zip_path),
            )
            return None
        
        try:
            async with aiofiles.open(zip_path, "rb") as f:
                content = await f.read()
            
            logger.info(
                "task_storage.zip_read",
                task_id=task_id,
                version=version,
                size=len(content),
            )
            
            return (content, filename)
        except Exception as e:
            logger.error(
                "task_storage.zip_read_failed",
                task_id=task_id,
                version=version,
                error=str(e),
            )
            return None
    
    async def get_disk_usage(self, task_id: str, version: str) -> dict:
        """Get disk usage for a task version.
        
        Args:
            task_id: Task identifier
            version: Task version
            
        Returns:
            Dict with disk usage information
        """
        base_path = self.get_task_base_path(task_id, version)
        
        if not await aios.path.exists(base_path):
            return {
                "exists": False,
                "total_bytes": 0,
            }
        
        def get_size(path: Path) -> int:
            total = 0
            try:
                for item in path.rglob("*"):
                    if item.is_file():
                        total += item.stat().st_size
            except Exception:
                pass
            return total
        
        code_size = get_size(self.get_code_path(task_id, version))
        venv_size = get_size(self.get_venv_path(task_id, version))
        data_size = get_size(self.get_data_path(task_id, version))
        storage_size = get_size(self.get_storage_path(task_id, version))
        
        return {
            "exists": True,
            "code_bytes": code_size,
            "venv_bytes": venv_size,
            "data_bytes": data_size,
            "storage_bytes": storage_size,
            "total_bytes": code_size + venv_size + data_size + storage_size,
        }

