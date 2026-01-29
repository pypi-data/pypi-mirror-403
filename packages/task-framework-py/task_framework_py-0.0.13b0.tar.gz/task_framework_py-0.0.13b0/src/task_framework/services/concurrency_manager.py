"""Concurrency manager for controlling thread execution capacity."""

import asyncio
import os
from typing import TYPE_CHECKING, Optional

from task_framework.logging import logger
from task_framework.thread_state import ThreadState

if TYPE_CHECKING:
    from task_framework.interfaces.database import Database


class ConcurrencyManager:
    """Manages thread execution concurrency.
    
    Controls how many threads can run concurrently. Uses asyncio.Event for
    efficient signaling when slots become available, with periodic checks
    for settings changes.
    """
    
    def __init__(
        self,
        database: "Database",
        settings_store: Optional["ElasticsearchSettingsStore"] = None,
        max_concurrent_threads: int = 0,
    ):
        """Initialize concurrency manager.
        
        Args:
            database: Database for thread queries
            settings_store: Optional ES settings store for dynamic config
            max_concurrent_threads: Default max (0 = unlimited)
        """
        self.database = database
        self.settings_store = settings_store
        self._default_max = max_concurrent_threads or int(
            os.getenv("MAX_CONCURRENT_THREADS", "0")
        )
        # In-memory tracking of running thread IDs
        self._running_threads: set[str] = set()
        # Event for signaling when a slot becomes available
        self._slot_available: asyncio.Event = asyncio.Event()
        # Track last known max for detecting changes
        self._last_known_max: int = 0
    
    def get_max_concurrent_threads(self) -> int:
        """Get current max concurrent threads limit.
        
        Returns:
            Max concurrent threads (0 = unlimited)
        """
        if self.settings_store:
            return self.settings_store.get_cached_max_concurrent_threads()
        return self._default_max
    
    async def get_running_thread_count(self) -> int:
        """Get count of currently running threads.
        
        Returns:
            Number of threads in running state
        """
        threads = await self.database.query_threads({"state": "running"})
        return len(threads)
    
    async def get_queued_thread_count(self) -> int:
        """Get count of queued threads.
        
        Returns:
            Number of threads in queued state
        """
        threads = await self.database.query_threads({"state": "queued"})
        return len(threads)
    
    async def can_start_thread(self) -> bool:
        """Check if a new thread can start immediately.
        
        Fetches max_concurrent_threads from ES each time to ensure
        up-to-date value across all workers.
        
        Returns:
            True if capacity available, False if thread should be queued
        """
        max_threads = await self.get_max_concurrent_threads_async()
        
        # 0 = unlimited
        if max_threads <= 0:
            return True
        
        # Use in-memory count for faster check (single process)
        running_count = len(self._running_threads)
        return running_count < max_threads
    
    async def get_max_concurrent_threads_async(self) -> int:
        """Get max concurrent threads from ES (or env fallback)."""
        if self.settings_store and hasattr(self.settings_store, 'get_max_concurrent_threads_async'):
            return await self.settings_store.get_max_concurrent_threads_async()
        return self._default_max
    
    async def _get_semaphore(self) -> Optional[asyncio.Semaphore]:
        """Get or create semaphore with current max setting."""
        max_threads = await self.get_max_concurrent_threads_async()
        
        # 0 = unlimited, no semaphore needed
        if max_threads <= 0:
            return None
        
        # Create or recreate semaphore if max changed
        if self._semaphore is None or self._semaphore_max != max_threads:
            # Note: changing limit on existing semaphore is complex
            # For now, we recreate if limit changed
            self._semaphore = asyncio.Semaphore(max_threads)
            self._semaphore_max = max_threads
            logger.info(
                "concurrency.semaphore_created",
                max_concurrent_threads=max_threads,
            )
        
        return self._semaphore
    
    async def wait_for_slot(self, thread_id: str) -> None:
        """Wait for a concurrency slot (blocks efficiently until available).
        
        Uses asyncio.Event for efficient signaling within a worker, with
        periodic checks for settings changes (to handle cross-worker and
        dynamic config scenarios).
        
        Args:
            thread_id: Thread ID for logging
        """
        settings_check_interval = 5.0  # seconds between settings re-checks
        
        while True:
            # Check current limit
            max_threads = await self.get_max_concurrent_threads_async()
            self._last_known_max = max_threads
            
            # 0 = unlimited, proceed immediately
            if max_threads <= 0:
                self._running_threads.add(thread_id)
                logger.info(
                    "concurrency.slot_acquired_unlimited",
                    thread_id=thread_id,
                )
                return
            
            # Check if we have capacity based on in-memory tracking
            current_running = len(self._running_threads)
            if current_running < max_threads:
                # We have capacity, proceed
                self._running_threads.add(thread_id)
                logger.info(
                    "concurrency.slot_acquired",
                    thread_id=thread_id,
                    running_count=len(self._running_threads),
                    max_threads=max_threads,
                )
                return
            
            # At capacity - wait for slot release event or timeout for settings check
            # Clear the event before waiting (we'll be notified when a slot is released)
            self._slot_available.clear()
            
            try:
                # Wait for either: slot released (event) or timeout (to re-check settings)
                await asyncio.wait_for(
                    self._slot_available.wait(),
                    timeout=settings_check_interval
                )
                # Event was set - a slot was released, loop to re-check
            except asyncio.TimeoutError:
                # Timeout - loop to re-check settings (they may have changed)
                pass
    
    async def release_slot(self, thread_id: str) -> None:
        """Release a concurrency slot for a thread.
        
        Call this when a thread finishes (success, failure, or cancellation).
        Signals waiting threads that a slot is available.
        
        Args:
            thread_id: Thread ID to remove from tracking
        """
        self._running_threads.discard(thread_id)
        
        # Signal waiting threads that a slot is available
        self._slot_available.set()
        
        logger.info(
            "concurrency.slot_released",
            thread_id=thread_id,
            running_count=len(self._running_threads),
        )
    
    def signal_settings_changed(self) -> None:
        """Signal all waiting threads that settings have changed.
        
        Call this when concurrency settings are updated to wake up
        threads that may now be able to proceed.
        """
        self._slot_available.set()
        logger.info("concurrency.settings_changed_signal")
    
    async def get_next_queued_thread_id(self) -> Optional[str]:
        """Get the next queued thread that should be started.
        
        Returns oldest queued thread by creation time.
        
        Returns:
            Thread ID or None if no queued threads
        """
        # Query queued threads sorted by created_at
        threads = await self.database.query_threads({
            "state": "queued",
            "limit": 1,
        })
        
        if threads:
            return threads[0].id
        return None
    
    async def process_queue(self) -> int:
        """Process queued threads when capacity is available.
        
        Called when a running thread completes to potentially
        start queued threads.
        
        Returns:
            Number of threads dequeued and started
        """
        max_threads = self.get_max_concurrent_threads()
        
        # 0 = unlimited, nothing to process
        if max_threads <= 0:
            return 0
        
        running_count = await self.get_running_thread_count()
        available_slots = max_threads - running_count
        
        if available_slots <= 0:
            return 0
        
        # Get queued threads up to available slots
        queued_threads = await self.database.query_threads({
            "state": "queued",
            "limit": available_slots,
        })
        
        started_count = 0
        for thread in queued_threads:
            try:
                # Update thread state to running
                thread.state = ThreadState.RUNNING
                await self.database.update_thread(thread)
                started_count += 1
                
                logger.info(
                    "concurrency.thread_dequeued",
                    thread_id=thread.id,
                    queue_position=started_count,
                )
            except Exception as e:
                logger.error(
                    "concurrency.dequeue_failed",
                    thread_id=thread.id,
                    error=str(e),
                )
        
        if started_count > 0:
            logger.info(
                "concurrency.queue_processed",
                threads_started=started_count,
                remaining_capacity=available_slots - started_count,
            )
        
        return started_count
