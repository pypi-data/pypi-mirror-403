"""Event publisher for webhook system using async in-memory queue."""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from task_framework.logging import logger


class WebhookEvent:
    """Webhook event model for event publishing."""

    def __init__(
        self,
        event_type: str,
        thread_id: Optional[str] = None,
        run_id: Optional[str] = None,
        thread: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Initialize webhook event.

        Args:
            event_type: Event type (e.g., "thread.succeeded", "thread.failed")
            thread_id: Thread identifier (if applicable)
            run_id: Run identifier (if applicable)
            thread: Thread instance (if applicable)
            metadata: Event metadata
            timestamp: Event timestamp (defaults to now)
        """
        self.event_type = event_type
        self.thread_id = thread_id
        self.run_id = run_id
        self.thread = thread
        self.metadata = metadata or {}
        self.timestamp = timestamp or datetime.now(timezone.utc)


class EventPublisher:
    """Event publisher with async in-memory queue."""

    def __init__(self, queue_size: int = 1000) -> None:
        """Initialize event publisher.

        Args:
            queue_size: Maximum queue size (default: 1000)
        """
        self._queue: asyncio.Queue[WebhookEvent] = asyncio.Queue(maxsize=queue_size)
        self._processor_task: Optional[asyncio.Task[None]] = None
        self._running = False
        self._event_handler: Optional[callable] = None

    async def publish(
        self,
        event_type: str,
        thread_id: Optional[str] = None,
        run_id: Optional[str] = None,
        thread: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Publish an event to the queue.

        Args:
            event_type: Event type (e.g., "thread.succeeded")
            thread_id: Thread identifier (if applicable)
            run_id: Run identifier (if applicable)
            thread: Thread instance (if applicable)
            metadata: Event metadata
        """
        # Auto-start processor if handler is set but not running
        if self._event_handler and not self._running:
            await self.start()

        event = WebhookEvent(
            event_type=event_type,
            thread_id=thread_id,
            run_id=run_id,
            thread=thread,
            metadata=metadata,
        )

        try:
            self._queue.put_nowait(event)
            logger.debug(
                "webhook.event.published",
                event_type=event_type,
                thread_id=thread_id,
                queue_size=self._queue.qsize(),
            )
        except asyncio.QueueFull:
            logger.warning(
                "webhook.event.queue_full",
                event_type=event_type,
                thread_id=thread_id,
                queue_size=self._queue.qsize(),
            )

    def set_event_handler(self, handler: callable) -> None:
        """Set event handler for processing events.

        Args:
            handler: Async callable that processes WebhookEvent instances
        """
        self._event_handler = handler
        # Auto-start processor if not already running (non-blocking)
        if not self._running:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, create task
                    asyncio.create_task(self.start())
            except RuntimeError:
                # No event loop, will start when first event is published
                pass

    async def start(self) -> None:
        """Start the background event processor."""
        if self._running:
            return

        self._running = True
        self._processor_task = asyncio.create_task(self._process_events())
        logger.info("webhook.event_publisher.started")

    async def stop(self) -> None:
        """Stop the background event processor."""
        if not self._running:
            return

        self._running = False
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        logger.info("webhook.event_publisher.stopped")

    async def _process_events(self) -> None:
        """Background task to process events from queue."""
        while self._running:
            try:
                # Wait for event with timeout to allow periodic checks
                try:
                    event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                if self._event_handler:
                    try:
                        await self._event_handler(event)
                    except Exception as e:
                        logger.error(
                            "webhook.event_processing.failed",
                            event_type=event.event_type,
                            thread_id=event.thread_id,
                            error=str(e),
                            error_type=type(e).__name__,
                        )
                else:
                    logger.debug(
                        "webhook.event.no_handler",
                        event_type=event.event_type,
                        thread_id=event.thread_id,
                    )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    "webhook.event_processor.error",
                    error=str(e),
                    error_type=type(e).__name__,
                )

    @property
    def queue_size(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()

    @property
    def is_running(self) -> bool:
        """Check if processor is running."""
        return self._running

