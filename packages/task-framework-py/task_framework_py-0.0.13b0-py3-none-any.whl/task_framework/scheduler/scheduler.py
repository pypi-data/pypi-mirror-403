"""Scheduler infrastructure module for APScheduler integration."""

from typing import Any, Callable, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler


class Scheduler:
    """Scheduler wrapper for APScheduler integration."""

    def __init__(self) -> None:
        """Initialize scheduler."""
        self._scheduler: Optional[AsyncIOScheduler] = None

    def start(self) -> None:
        """Start the scheduler."""
        if self._scheduler is None:
            self._scheduler = AsyncIOScheduler()
            self._scheduler.start()

    def stop(self) -> None:
        """Stop the scheduler."""
        if self._scheduler is not None:
            self._scheduler.shutdown()
            self._scheduler = None

    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._scheduler is not None and self._scheduler.running

    def add_job(
        self,
        func: Callable[..., Any],
        trigger: Any,
        id: str,
        replace_existing: bool = True,
        **kwargs: Any,
    ) -> None:
        """Add a job to the scheduler.
        
        Args:
            func: Function to execute
            trigger: APScheduler trigger (e.g., CronTrigger)
            id: Job identifier
            replace_existing: Whether to replace existing job with same ID
            **kwargs: Additional arguments to pass to add_job
        """
        if self._scheduler is None:
            raise RuntimeError("Scheduler not started")
        
        self._scheduler.add_job(
            func,
            trigger=trigger,
            id=id,
            replace_existing=replace_existing,
            **kwargs
        )

    def remove_job(self, id: str) -> None:
        """Remove a job from the scheduler.
        
        Args:
            id: Job identifier
        """
        if self._scheduler is None:
            return
        
        try:
            self._scheduler.remove_job(id)
        except Exception:
            # Job may not exist, ignore
            pass

    def get_job(self, id: str) -> Optional[Any]:
        """Get a job by ID.
        
        Args:
            id: Job identifier
            
        Returns:
            Job instance if found, None otherwise
        """
        if self._scheduler is None:
            return None
        
        return self._scheduler.get_job(id)

