"""RunService for managing run execution and retries."""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from task_framework.logging import logger
from task_framework.models.schedule import Run, RunState, Schedule, RunListResponse
from task_framework.models.pagination import Pagination
from task_framework.models.thread_create_request import ThreadCreateRequest
from task_framework.scheduler.utils import generate_run_id, get_scheduled_time_local
from task_framework.scheduler.retry import retry_with_backoff

if TYPE_CHECKING:
    from task_framework.interfaces.database import Database
    from task_framework.services.thread_service import ThreadService


class RunService:
    """Service layer for run management and execution."""

    def __init__(
        self,
        database: "Database",
        thread_service: Optional["ThreadService"] = None,
    ) -> None:
        """Initialize RunService.
        
        Args:
            database: Database implementation for run persistence
            thread_service: Optional ThreadService for creating threads
        """
        self.database = database
        self.thread_service = thread_service

    async def create_run(
        self,
        schedule: Schedule,
        scheduled_for_utc: datetime,
    ) -> Run:
        """Create a new run for a schedule.
        
        Args:
            schedule: Schedule instance
            scheduled_for_utc: UTC timestamp when run should execute
            
        Returns:
            Created Run instance, or existing Run if already created
            
        Note:
            With multiple workers, the same cron trigger may fire simultaneously
            on all workers. This method uses second-precision timestamps to
            generate deterministic run_ids, and checks for existing runs before
            creating to avoid duplicates.
        """
        # Generate deterministic run_id
        run_id = generate_run_id(schedule.id, scheduled_for_utc)
        
        # Check if run already exists (another worker may have created it)
        existing_run = await self.database.get_run(schedule.id, run_id)
        if existing_run:
            logger.debug(
                "schedule.run.already_exists",
                schedule_id=schedule.id,
                run_id=run_id,
            )
            return existing_run
        
        # Convert to local timezone
        scheduled_for_local = get_scheduled_time_local(scheduled_for_utc, schedule)
        
        # Create run
        now = datetime.now(timezone.utc)
        run = Run(
            schedule_id=schedule.id,
            run_id=run_id,
            scheduled_for_utc=scheduled_for_utc,
            scheduled_for_local=scheduled_for_local,
            state=RunState.PENDING,
            attempt=1,
            max_attempts=schedule.max_attempts,
            threads=[],
            labels={},
            created_at=now,
            started_at=None,
            finished_at=None,
        )
        
        # Save to database
        await self.database.create_run(run)
        
        # Logging
        logger.info(
            "schedule.run.created",
            schedule_id=schedule.id,
            run_id=run_id,
            scheduled_for_utc=scheduled_for_utc.isoformat(),
        )
        
        return run

    async def trigger_run_execution(
        self,
        run: Run,
        schedule: Schedule,
        task_function: Callable[..., Any],
    ) -> Run:
        """Trigger run execution by creating and executing thread.
        
        Args:
            run: Run instance
            schedule: Schedule instance
            task_function: Task function to execute
            
        Returns:
            Updated Run instance, or existing run if already processing
            
        Note:
            This method uses atomic claim_run to ensure only one worker
            can execute a given run, even in multi-worker deployments.
        """
        # Try to atomically claim the run (pending → running)
        # Only one worker will succeed; others will return early
        if hasattr(self.database, 'claim_run'):
            # ES database with atomic claim
            claimed = await self.database.claim_run(run.schedule_id, run.run_id)
            if not claimed:
                logger.debug(
                    "schedule.run.already_claimed",
                    schedule_id=run.schedule_id,
                    run_id=run.run_id,
                )
                # Re-fetch and return current run state
                current_run = await self.database.get_run(run.schedule_id, run.run_id)
                return current_run or run
            
            # Claim succeeded - refresh our run object
            run.state = RunState.RUNNING
            run.started_at = datetime.now(timezone.utc)
        else:
            # File-based fallback: re-fetch and check
            current_run = await self.database.get_run(run.schedule_id, run.run_id)
            if not current_run:
                logger.warning(
                    "schedule.run.not_found",
                    schedule_id=run.schedule_id,
                    run_id=run.run_id,
                )
                return run
            
            current_state_str = current_run.state.value if hasattr(current_run.state, 'value') else str(current_run.state)
            if current_state_str != "pending":
                logger.debug(
                    "schedule.run.already_executing",
                    schedule_id=run.schedule_id,
                    run_id=run.run_id,
                    state=current_state_str,
                )
                return current_run
            
            # Update run state to running
            run.state = RunState.RUNNING
            run.started_at = datetime.now(timezone.utc)
            await self.database.update_run(run)
        
        # Logging
        logger.info(
            "schedule.run.started",
            schedule_id=run.schedule_id,
            run_id=run.run_id,
            attempt=run.attempt,
        )
        
        try:
            # Create thread from run
            thread_id = await self._create_thread_from_run(run, schedule, task_function)
            
            # Update run with thread ID
            run.threads.append(thread_id)
            await self.database.update_run(run)
            
            # Execute run with retry logic
            await self._execute_run_with_retry(run, schedule, task_function, thread_id)
            
        except Exception as e:
            # Mark run as failed
            run.state = RunState.FAILED
            run.finished_at = datetime.now(timezone.utc)
            await self.database.update_run(run)
            
            # Logging
            logger.error(
                "schedule.run.failed",
                schedule_id=run.schedule_id,
                run_id=run.run_id,
                attempt=run.attempt,
                error=str(e),
            )
            
            raise
        
        return run

    async def _create_thread_from_run(
        self,
        run: Run,
        schedule: Schedule,
        task_function: Callable[..., Any],
    ) -> str:
        """Create a thread from a run.
        
        Args:
            run: Run instance
            schedule: Schedule instance
            task_function: Task function to execute
            
        Returns:
            Thread ID
        """
        if not self.thread_service:
            raise RuntimeError("ThreadService not available")
        
        # Populate inputs from schedule template
        inputs = self._populate_inputs_template(schedule.inputs_template, run)
        
        # Prepare metadata - include schedule metadata and task_id/task_version if present
        metadata = schedule.metadata.copy() if schedule.metadata else {}
        if schedule.task_id:
            metadata["task_id"] = schedule.task_id
        if schedule.task_version:
            metadata["task_version"] = schedule.task_version
        # Add schedule_id and run_id to metadata for tracking
        metadata["schedule_id"] = schedule.id
        metadata["run_id"] = run.run_id
        
        # Create thread request
        # NOTE: We intentionally do NOT pass schedule.webhooks to ThreadCreateRequest.
        # Schedule webhooks are stored once at the schedule level, not duplicated per-thread.
        # The webhook delivery system should look up schedule webhooks when delivering
        # events for threads with schedule_id in their metadata.
        thread_request = ThreadCreateRequest(
            name=f"schedule_execution_{schedule.id}",
            metadata=metadata,
            params=schedule.params.copy(),
            inputs=inputs,
            webhooks=None,  # Schedule webhooks are NOT passed as ad-hoc webhooks
            mode="sync",  # Scheduled runs execute synchronously
        )
        
        # Create thread (without user_id/app_id for scheduled runs)
        # Pass task_definition and requested_version if available
        task_definition = None
        requested_version = None
        if schedule.task_id:
            # Try to get task definition from framework if available
            from task_framework.framework import TaskFramework
            if hasattr(self.thread_service, 'execution_engine') and hasattr(self.thread_service.execution_engine, 'framework'):
                framework = self.thread_service.execution_engine.framework
                if isinstance(framework, TaskFramework):
                    task_definition = framework.get_task(schedule.task_id, schedule.task_version)
                    requested_version = schedule.task_version
        
        thread = await self.thread_service.create_thread(
            request=thread_request,
            user_id=None,
            app_id=None,
            is_admin=False,
            task_function=task_function,
            task_definition=task_definition,
            requested_version=requested_version,
        )
        
        return thread.id

    def _populate_inputs_template(
        self,
        inputs_template: List[Any],
        run: Run,
    ) -> List[Any]:
        """Populate inputs template with run-specific data.
        
        Args:
            inputs_template: Template artifacts from schedule (as dicts or Artifact objects)
            run: Run instance for context
            
        Returns:
            List of Artifact objects populated from template
        """
        from task_framework.models.artifact import Artifact
        
        if not inputs_template:
            return []
        
        populated = []
        for template in inputs_template:
            # Convert dict to Artifact if needed
            if isinstance(template, dict):
                artifact = Artifact.model_validate(template)
            elif isinstance(template, Artifact):
                artifact = template.model_copy()
            else:
                # Skip invalid items
                continue
            
            populated.append(artifact)
        
        return populated

    async def _execute_run_with_retry(
        self,
        run: Run,
        schedule: Schedule,
        task_function: Callable[..., Any],
        thread_id: str,
    ) -> None:
        """Execute run with retry logic.
        
        Args:
            run: Run instance
            schedule: Schedule instance
            task_function: Task function to execute
            thread_id: Thread ID to execute
        """
        async def execute_attempt() -> None:
            """Execute a single attempt."""
            # Get thread and check state
            thread = await self.database.get_thread(thread_id)
            if not thread:
                raise RuntimeError(f"Thread {thread_id} not found")
            
            # Helper to safely get state string
            def get_state_str(state_obj):
                return state_obj.value if hasattr(state_obj, 'value') else str(state_obj)
            
            # If thread already succeeded, we're done
            if get_state_str(thread.state) == "succeeded":
                run.state = RunState.SUCCEEDED
                run.finished_at = datetime.now(timezone.utc)
                await self.database.update_run(run)
                return
            
            # If thread failed, raise exception to trigger retry
            if get_state_str(thread.state) == "failed":
                raise RuntimeError(f"Thread {thread_id} failed")
            
            # Thread execution should have been handled by ThreadService.create_thread
            # which runs in sync mode, so the thread should already be completed
            # Wait a bit and check again
            import asyncio
            await asyncio.sleep(0.1)
            
            thread = await self.database.get_thread(thread_id)
            thread_state_str = get_state_str(thread.state)
            if thread_state_str == "succeeded":
                run.state = RunState.SUCCEEDED
                run.finished_at = datetime.now(timezone.utc)
                await self.database.update_run(run)
            elif thread_state_str == "failed":
                raise RuntimeError(f"Thread {thread_id} failed")
        
        # Execute with retry
        try:
            await retry_with_backoff(
                execute_attempt,
                max_attempts=run.max_attempts,
            )
        except Exception as e:
            # All retries exhausted
            run.state = RunState.FAILED
            run.finished_at = datetime.now(timezone.utc)
            await self.database.update_run(run)
            raise

    async def get_run(self, schedule_id: str, run_id: str) -> Optional[Run]:
        """Get a run by schedule_id and run_id.
        
        Args:
            schedule_id: Schedule identifier
            run_id: Run identifier
            
        Returns:
            Run instance if found, None otherwise
        """
        return await self.database.get_run(schedule_id, run_id)

    async def list_runs(
        self,
        schedule_id: str,
        filters: Dict[str, Any],
    ) -> RunListResponse:
        """List runs for a schedule with filters and pagination.
        
        Args:
            schedule_id: Schedule identifier
            filters: Filter dictionary containing:
                - state: Optional[str] - Filter by run state
                - scheduled_after: Optional[datetime] - Filter runs scheduled after
                - scheduled_before: Optional[datetime] - Filter runs scheduled before
                - limit: Optional[int] - Maximum number of results
                - cursor: Optional[str] - Pagination cursor
                - offset: Optional[int] - Offset for pagination
                
        Returns:
            RunListResponse with paginated results
        """
        # Get all runs (before pagination)
        filter_dict: Dict[str, Any] = {}
        if "state" in filters:
            filter_dict["state"] = filters["state"]
        if "scheduled_after" in filters:
            filter_dict["scheduled_after"] = filters["scheduled_after"]
        if "scheduled_before" in filters:
            filter_dict["scheduled_before"] = filters["scheduled_before"]
        
        runs = await self.database.query_runs(schedule_id, filter_dict)
        
        # Apply cursor-based pagination
        limit = filters.get("limit") or 50
        cursor = filters.get("cursor")
        offset = filters.get("offset")
        
        if cursor:
            # Decode cursor (Base64 JSON with run_id and scheduled_for_utc)
            import base64
            import json as json_lib
            
            try:
                cursor_data = json_lib.loads(base64.b64decode(cursor).decode())
                cursor_run_id = cursor_data.get("run_id")
                cursor_scheduled_for_utc = cursor_data.get("scheduled_for_utc")
                
                # Filter runs after cursor
                if cursor_scheduled_for_utc:
                    cursor_time = datetime.fromisoformat(cursor_scheduled_for_utc.replace("Z", "+00:00"))
                    runs = [r for r in runs if r.scheduled_for_utc < cursor_time]
            except (ValueError, KeyError, TypeError):
                # Invalid cursor, return empty
                runs = []
        
        # Offset-based pagination fallback
        elif offset is not None:
            runs = runs[offset:]
        
        # Apply limit
        has_more = len(runs) > limit
        runs = runs[:limit]
        
        # Generate next cursor if has_more
        next_cursor = None
        if has_more and runs:
            import base64
            import json as json_lib
            
            last_run = runs[-1]
            cursor_data = {
                "run_id": last_run.run_id,
                "scheduled_for_utc": last_run.scheduled_for_utc.isoformat() + "Z",
            }
            next_cursor = base64.b64encode(json_lib.dumps(cursor_data).encode()).decode()
        
        pagination = Pagination(
            cursor=next_cursor,
            has_more=has_more,
            total=None,
        )
        
        return RunListResponse(items=runs, pagination=pagination)

