"""Database interface abstract base class."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from task_framework.models.artifact import Artifact
from task_framework.models.schedule import Run, Schedule
from task_framework.models.thread import Thread


class Database(ABC):
    """Abstract base class for database interface."""

    @abstractmethod
    async def create_thread(self, thread: Thread) -> None:
        """Create a new thread."""
        pass

    @abstractmethod
    async def get_thread(self, thread_id: str) -> Optional[Thread]:
        """Get a thread by ID."""
        pass

    @abstractmethod
    async def update_thread(self, thread: Thread) -> None:
        """Update an existing thread."""
        pass

    @abstractmethod
    async def delete_thread(self, thread_id: str) -> None:
        """Delete a thread."""
        pass

    @abstractmethod
    async def query_threads(self, filters: Dict[str, Any]) -> List[Thread]:
        """Query threads with filters."""
        pass

    @abstractmethod
    async def create_artifact(self, artifact: Artifact) -> None:
        """Create a new artifact."""
        pass

    @abstractmethod
    async def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        """Get an artifact by ID."""
        pass

    @abstractmethod
    async def get_thread_artifacts(self, thread_id: str) -> List[Artifact]:
        """Get all artifacts for a thread."""
        pass

    @abstractmethod
    async def delete_artifact(self, artifact_id: str) -> None:
        """Delete an artifact."""
        pass

    @abstractmethod
    async def query_artifacts(self, filters: Dict[str, Any]) -> List[Artifact]:
        """Query artifacts across threads with filters.
        
        Args:
            filters: Filter dictionary containing:
                - ref: Optional[str] - Ref filter (supports prefix wildcards with *)
                - kind: Optional[str] - Artifact kind filter
                - media_type: Optional[str] - Media type filter
                - thread_id: Optional[str] - Filter by thread ID
                - app_id: Optional[str] - Filter by app_id (from thread metadata)
                - include_archived: Optional[bool] - Include archived artifacts (default: False)
                - limit: Optional[int] - Maximum number of results
                - cursor: Optional[str] - Pagination cursor
                
        Returns:
            List of Artifact instances matching filters
        """
        pass

    # Schedule methods

    @abstractmethod
    async def create_schedule(self, schedule: Schedule) -> None:
        """Create a new schedule."""
        pass

    @abstractmethod
    async def get_schedule(self, schedule_id: str) -> Optional[Schedule]:
        """Get a schedule by ID."""
        pass

    @abstractmethod
    async def update_schedule(self, schedule: Schedule) -> None:
        """Update an existing schedule."""
        pass

    @abstractmethod
    async def delete_schedule(self, schedule_id: str) -> None:
        """Delete a schedule."""
        pass

    @abstractmethod
    async def query_schedules(self, filters: Dict[str, Any]) -> List[Schedule]:
        """Query schedules with filters.
        
        Args:
            filters: Filter dictionary containing:
                - state: Optional[str] - Filter by schedule state
                - limit: Optional[int] - Maximum number of results
                - cursor: Optional[str] - Pagination cursor
                
        Returns:
            List of Schedule instances matching filters
        """
        pass

    # Run methods

    @abstractmethod
    async def create_run(self, run: Run) -> None:
        """Create a new run."""
        pass

    @abstractmethod
    async def get_run(self, schedule_id: str, run_id: str) -> Optional[Run]:
        """Get a run by schedule_id and run_id."""
        pass

    @abstractmethod
    async def update_run(self, run: Run) -> None:
        """Update an existing run."""
        pass

    @abstractmethod
    async def delete_run(self, schedule_id: str, run_id: str) -> None:
        """Delete a run."""
        pass

    @abstractmethod
    async def query_runs(
        self, schedule_id: str, filters: Dict[str, Any]
    ) -> List[Run]:
        """Query runs for a schedule with filters.
        
        Args:
            schedule_id: Schedule identifier
            filters: Filter dictionary containing:
                - state: Optional[str] - Filter by run state
                - scheduled_after: Optional[datetime] - Filter runs scheduled after this time (UTC)
                - scheduled_before: Optional[datetime] - Filter runs scheduled before this time (UTC)
                - limit: Optional[int] - Maximum number of results
                - cursor: Optional[str] - Pagination cursor
                
        Returns:
            List of Run instances matching filters
        """
        pass

    @abstractmethod
    async def get_running_run_by_schedule(self, schedule_id: str) -> Optional[Run]:
        """Get the currently running run for a schedule (if any).
        
        Args:
            schedule_id: Schedule identifier
            
        Returns:
            Run instance if found, None otherwise
        """
        pass

