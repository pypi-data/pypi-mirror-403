"""Scheduler interface abstract base class."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional


class Scheduler(ABC):
    """Abstract base class for scheduler interface."""

    @abstractmethod
    async def schedule(
        self,
        schedule_id: str,
        run_id: str,
        task_params: Dict[str, Any],
        scheduled_for: datetime,
    ) -> None:
        """Schedule a task execution."""
        pass

    @abstractmethod
    async def cancel_schedule(self, schedule_id: str) -> None:
        """Cancel a scheduled task."""
        pass

    @abstractmethod
    async def get_schedule(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """Get schedule details."""
        pass

