"""Task execution engine for managing task lifecycle and state."""

import asyncio
import inspect
import os
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

from task_framework.context import TaskContext
from task_framework.logging import logger
from task_framework.metrics import thread_execution_duration_seconds, threads_current, threads_total
from task_framework.models.thread import Thread
from task_framework.models.thread_error import ThreadError
from task_framework.thread_state import ThreadState
from task_framework.utils.metrics_helpers import update_thread_state_gauge

if TYPE_CHECKING:
    from task_framework.framework import TaskFramework


class ExecutionEngine:
    """Task execution engine managing task lifecycle and state."""

    def __init__(self, framework: "TaskFramework", timeout_seconds: Optional[int] = None) -> None:
        """Initialize execution engine.

        Args:
            framework: TaskFramework instance
            timeout_seconds: Optional timeout for task execution (default: None, no timeout)
        """
        self.framework = framework
        self.timeout_seconds = timeout_seconds
        # Configurable max_workers: 0 or unset = Python default (min(32, cpu_count + 4))
        max_workers = int(os.getenv("TASK_EXECUTOR_MAX_WORKERS", "0")) or None
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        # Registry to track active TaskContext instances by thread_id
        self._active_contexts: Dict[str, TaskContext] = {}

    async def execute_task(self, thread: Thread, task_function: Callable, task_definition: Optional[Any] = None) -> Thread:
        """Execute a task function with the given thread.

        Args:
            thread: Thread instance to execute
            task_function: Task function to execute
            task_definition: Optional TaskDefinition (for multi-task mode, to provide output schemas)

        Returns:
            Updated Thread instance with execution results
        """
        # Transition to running state
        previous_state = thread.state
        thread.state = ThreadState.RUNNING
        thread.started_at = datetime.now(timezone.utc)

        # Persist running state immediately so the API reflects the executing state
        try:
            # Update thread in database to reflect the RUNNING transition
            await self.framework.database.update_thread(thread)
        except Exception:
            # Log but continue execution; DB update failures should not block task execution
            logger.exception("thread.execution.db_update_failed", thread_id=thread.id)

        # Update gauge for state transition (decrement previous, increment running)
        update_thread_state_gauge(previous_state, thread.state)

        # Logging
        state_value = thread.state.value if hasattr(thread.state, "value") else str(thread.state)
        logger.info(
            "thread.execution.started",
            thread_id=thread.id,
            state=state_value,
        )

        # Publish thread.started event
        if self.framework.event_publisher:
            try:
                await self.framework.event_publisher.publish(
                    event_type="thread.started",
                    thread_id=thread.id,
                    thread=thread,
                    metadata=thread.metadata,
                )
            except Exception:
                logger.exception("thread.execution.started_event_failed", thread_id=thread.id)

        # Resolve task configuration (env vars and secrets)
        resolved_env_vars: Dict[str, str] = {}
        resolved_secrets: Dict[str, str] = {}
        
        if task_definition and self.framework.configuration_service:
            try:
                # Get runtime env overrides from thread params if present
                runtime_overrides = thread.params.get("_env_overrides")
                
                resolved_config = await self.framework.configuration_service.resolve_configuration(
                    task_def=task_definition,
                    runtime_overrides=runtime_overrides,
                    validate=False,  # Don't fail, let task handle missing config
                )
                resolved_env_vars = resolved_config.env_vars
                resolved_secrets = resolved_config.secrets
                
                logger.debug(
                    "thread.execution.config_resolved",
                    thread_id=thread.id,
                    env_count=len(resolved_env_vars),
                    secret_count=len(resolved_secrets),
                )
            except Exception as e:
                logger.warning(
                    "thread.execution.config_resolution_failed",
                    thread_id=thread.id,
                    error=str(e),
                )

        # Create context with resolved configuration
        context = TaskContext(
            thread_id=thread.id,
            metadata=thread.metadata,
            params=thread.params,
            framework=self.framework,
            task_definition=task_definition,
            env_vars=resolved_env_vars,
            secrets=resolved_secrets,
        )
        
        # Register context for cancellation propagation
        self._active_contexts[thread.id] = context

        try:
            # Check if task function is async or sync
            if inspect.iscoroutinefunction(task_function):
                # Execute async function
                if self.timeout_seconds:
                    result = await asyncio.wait_for(
                        task_function(context),
                        timeout=self.timeout_seconds,
                    )
                else:
                    result = await task_function(context)
            else:
                # Execute sync function in thread pool
                loop = asyncio.get_event_loop()
                if self.timeout_seconds:
                    result = await asyncio.wait_for(
                        loop.run_in_executor(self._executor, task_function, context),
                        timeout=self.timeout_seconds,
                    )
                else:
                    result = await loop.run_in_executor(self._executor, task_function, context)

            # Check database state before marking success (prevent race condition with stop)
            # Reload thread from database to check if it was stopped while executing
            db_thread = await self.framework.database.get_thread(thread.id)
            if db_thread and db_thread.state == ThreadState.STOPPED:
                # Thread was stopped while executing, honor the STOPPED state
                logger.info(
                    "thread.execution.cancelled",
                    thread_id=thread.id,
                    message="Thread was stopped during execution, preserving STOPPED state",
                )
                # Use the database thread state instead of marking as succeeded
                thread = db_thread
                # Don't publish succeeded event or update metrics for succeeded
                # The stop_thread() method already published thread.stopped event
            else:
                # Transition to succeeded state
                previous_state = thread.state
                thread.state = ThreadState.SUCCEEDED
                thread.finished_at = datetime.now(timezone.utc)
                
                # Update thread in database
                await self.framework.database.update_thread(thread)

                # Update gauge for state transition (decrement running, increment succeeded)
                update_thread_state_gauge(previous_state, thread.state)
                
                # Metrics
                duration = (thread.finished_at - thread.started_at).total_seconds()
                thread_execution_duration_seconds.observe(duration)

                # Logging
                state_value = thread.state.value if hasattr(thread.state, "value") else str(thread.state)
                logger.info(
                    "thread.execution.completed",
                    thread_id=thread.id,
                    state=state_value,
                    duration_seconds=duration,
                )

                # Publish thread.succeeded event
                if self.framework.event_publisher:
                    await self.framework.event_publisher.publish(
                        event_type="thread.succeeded",
                        thread_id=thread.id,
                        thread=thread,
                        metadata=thread.metadata,
                    )

        except asyncio.TimeoutError:
            # Handle timeout
            # Check database state before marking timeout (prevent race condition with stop)
            db_thread = await self.framework.database.get_thread(thread.id)
            if db_thread and db_thread.state == ThreadState.STOPPED:
                # Thread was stopped while executing, honor the STOPPED state
                logger.info(
                    "thread.execution.cancelled",
                    thread_id=thread.id,
                    message="Thread was stopped during execution (timeout), preserving STOPPED state",
                )
                thread = db_thread
            else:
                previous_state = thread.state
                thread.state = ThreadState.TIMEOUT
                thread.finished_at = datetime.now(timezone.utc)
                thread.error = ThreadError(
                    message="Task execution timed out",
                    exception_type="TimeoutError",
                    stack_trace="",
                )
                
                # Update thread in database
                await self.framework.database.update_thread(thread)

                # Update gauge for state transition (decrement running, increment timeout)
                update_thread_state_gauge(previous_state, thread.state)
                
                # Metrics
                duration = (thread.finished_at - thread.started_at).total_seconds()
                thread_execution_duration_seconds.observe(duration)

                # Logging
                state_value = thread.state.value if hasattr(thread.state, "value") else str(thread.state)
                logger.info(
                    "thread.execution.failed",
                    thread_id=thread.id,
                    state=state_value,
                    error="TimeoutError",
                )

                # Publish thread.timeout event
                if self.framework.event_publisher:
                    await self.framework.event_publisher.publish(
                        event_type="thread.timeout",
                        thread_id=thread.id,
                        thread=thread,
                        metadata=thread.metadata,
                    )

        except BaseException as exc:
            # Handle exception
            # Check database state before marking failed (prevent race condition with stop)
            db_thread = await self.framework.database.get_thread(thread.id)
            if db_thread and db_thread.state == ThreadState.STOPPED:
                # Thread was stopped while executing, honor the STOPPED state
                logger.info(
                    "thread.execution.cancelled",
                    thread_id=thread.id,
                    message="Thread was stopped during execution (exception), preserving STOPPED state",
                )
                thread = db_thread
            else:
                previous_state = thread.state
                thread.state = ThreadState.FAILED
                thread.finished_at = datetime.now(timezone.utc)

                # Create ThreadError
                thread.error = ThreadError(
                    message=str(exc),
                    exception_type=type(exc).__name__,
                    stack_trace=traceback.format_exc(),
                )
                
                # Update thread in database
                await self.framework.database.update_thread(thread)

                # Update gauge for state transition (decrement running, increment failed)
                update_thread_state_gauge(previous_state, thread.state)
                
                # Metrics
                duration = (thread.finished_at - thread.started_at).total_seconds()
                thread_execution_duration_seconds.observe(duration)

                # Logging
                state_value = thread.state.value if hasattr(thread.state, "value") else str(thread.state)
                logger.error(
                    "thread.execution.failed",
                    thread_id=thread.id,
                    state=state_value,
                    error=type(exc).__name__,
                    error_message=str(exc),
                )

                # Publish thread.failed event
                if self.framework.event_publisher:
                    await self.framework.event_publisher.publish(
                        event_type="thread.failed",
                        thread_id=thread.id,
                        thread=thread,
                        metadata=thread.metadata,
                    )

        # Mark context as completed and unregister
        context._completed = True
        self._active_contexts.pop(thread.id, None)

        return thread
    
    def cancel_context(self, thread_id: str) -> bool:
        """Cancel an active TaskContext by thread_id.
        
        Args:
            thread_id: Thread identifier
            
        Returns:
            True if context was found and cancelled, False otherwise
        """
        context = self._active_contexts.get(thread_id)
        if context:
            # Set cancelled flag using object.__setattr__ to bypass Pydantic restrictions
            object.__setattr__(context, "_cancelled", True)
            logger.info(
                "thread.execution.cancellation_propagated",
                thread_id=thread_id,
            )
            return True
        return False

    def create_thread(
        self,
        thread_id: str,
        metadata: dict[str, Any],
        params: dict[str, Any],
        name: Optional[str] = None,
    ) -> Thread:
        """Create a new thread for execution.

        Args:
            thread_id: Unique thread identifier
            metadata: Thread metadata
            params: Task-specific parameters
            name: Optional thread name for display and grouping

        Returns:
            New Thread instance in QUEUED state
        """
        thread = Thread(
            id=thread_id,
            name=name,
            state=ThreadState.QUEUED,
            metadata=metadata,
            params=params,
            created_at=datetime.now(timezone.utc),
        )

        # Metrics - increment counter for thread creation (only place threads_total is incremented)
        state_value = thread.state.value if hasattr(thread.state, 'value') else str(thread.state)
        threads_total.labels(state=state_value).inc()
        
        # Update gauge to reflect new queued thread
        threads_current.labels(state=state_value).inc()

        return thread

