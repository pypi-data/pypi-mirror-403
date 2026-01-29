"""Deployment Tracker Store interface abstract base class."""

from abc import ABC, abstractmethod
from typing import List, Optional

from task_framework.models.task_definition import DeploymentRecord


class DeploymentTrackerStore(ABC):
    """Abstract base class for deployment tracking storage.
    
    Provides persistence operations for tracking task deployments.
    Implementations can use file storage, Elasticsearch, or other backends.
    """

    @abstractmethod
    async def record_deployment(
        self,
        zip_path: str,
        task_id: str,
        version: str,
        status: str,
        error: Optional[str] = None,
    ) -> None:
        """Record a deployment attempt.
        
        Args:
            zip_path: Path to the deployed zip file
            task_id: Task identifier
            version: Task version
            status: Deployment status ('pending', 'deployed', 'failed')
            error: Optional error message for failed deployments
        """
        pass

    @abstractmethod
    async def list_deployed(self) -> List[DeploymentRecord]:
        """List all successfully deployed tasks.
        
        Returns:
            List of DeploymentRecord for deployed tasks
        """
        pass

    @abstractmethod
    async def is_deployed(self, zip_path: str) -> bool:
        """Check if a zip file has been successfully deployed.
        
        Args:
            zip_path: Path to the zip file
            
        Returns:
            True if deployed successfully, False otherwise
        """
        pass

    @abstractmethod
    async def get_deployment(self, zip_path: str) -> Optional[DeploymentRecord]:
        """Get deployment record for a zip file.
        
        Args:
            zip_path: Path to the zip file
            
        Returns:
            DeploymentRecord if found, None otherwise
        """
        pass

    @abstractmethod
    async def remove(self, zip_path: str) -> None:
        """Remove a deployment record.
        
        Args:
            zip_path: Path to the zip file to remove
        """
        pass

    @abstractmethod
    async def list_all(self) -> List[DeploymentRecord]:
        """List all deployment records (including failed).
        
        Returns:
            List of all DeploymentRecord objects
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all deployment records."""
        pass
