"""Task Registry Store interface abstract base class."""

from abc import ABC, abstractmethod
from typing import List, Optional

from task_framework.models.task_definition import TaskDefinition


class TaskRegistryStore(ABC):
    """Abstract base class for task registry storage.
    
    Provides persistence operations for task definitions.
    Implementations can use file storage, Elasticsearch, or other backends.
    """

    @abstractmethod
    async def load(self) -> List[TaskDefinition]:
        """Load all task definitions from storage.
        
        Returns:
            List of all stored TaskDefinition objects
        """
        pass

    @abstractmethod
    async def save_all(self, tasks: List[TaskDefinition]) -> None:
        """Save all task definitions to storage (full replacement).
        
        Args:
            tasks: Complete list of TaskDefinition objects to store
        """
        pass

    @abstractmethod
    async def register(self, task_def: TaskDefinition) -> None:
        """Register a single task definition.
        
        Args:
            task_def: TaskDefinition to register
            
        Raises:
            ValueError: If task with same task_id and version already exists
        """
        pass

    @abstractmethod
    async def unregister(self, task_id: str, version: Optional[str] = None) -> List[TaskDefinition]:
        """Unregister task definition(s).
        
        Args:
            task_id: Task identifier
            version: Optional version. If None, unregisters all versions.
            
        Returns:
            List of unregistered TaskDefinition objects
        """
        pass

    @abstractmethod
    async def get(self, task_id: str, version: Optional[str] = None) -> Optional[TaskDefinition]:
        """Get a task definition.
        
        Args:
            task_id: Task identifier
            version: Optional version. If None, returns latest version.
            
        Returns:
            TaskDefinition if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_full_id(self, full_id: str) -> Optional[TaskDefinition]:
        """Get a task definition by full ID (task_id:version).
        
        Args:
            full_id: Full task identifier in format 'task_id:version'
            
        Returns:
            TaskDefinition if found, None otherwise
        """
        pass

    @abstractmethod
    async def list_all(self) -> List[TaskDefinition]:
        """List all registered task definitions.
        
        Returns:
            List of all TaskDefinition objects
        """
        pass

    @abstractmethod
    async def list_task_ids(self) -> List[str]:
        """List all unique task IDs.
        
        Returns:
            List of task identifiers
        """
        pass

    @abstractmethod
    async def list_versions(self, task_id: str) -> List[str]:
        """List all versions for a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            List of version strings, sorted newest first
        """
        pass

    @abstractmethod
    async def is_registered(self, task_id: str, version: Optional[str] = None) -> bool:
        """Check if a task is registered.
        
        Args:
            task_id: Task identifier
            version: Optional version to check
            
        Returns:
            True if registered, False otherwise
        """
        pass

    @abstractmethod
    async def count(self) -> int:
        """Get total number of registered task definitions.
        
        Returns:
            Total count of task definitions (all versions)
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all registered tasks from storage."""
        pass
