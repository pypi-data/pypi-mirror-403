"""ScheduleService for managing schedule business logic."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from task_framework.errors import SCHEDULE_INVALID_CRON, SCHEDULE_INVALID_TIMEZONE, SCHEDULE_NOT_FOUND
from task_framework.logging import logger
from task_framework.metrics import schedules_active, schedule_runs_total
from task_framework.models.schedule import Schedule, ScheduleCreateRequest, ScheduleState, ScheduleUpdateRequest, ScheduleListResponse
from task_framework.models.pagination import Pagination
from task_framework.scheduler.scheduler import Scheduler

if TYPE_CHECKING:
    from task_framework.interfaces.database import Database
    from task_framework.services.run_service import RunService


class ScheduleService:
    """Service layer for schedule management operations."""

    def __init__(
        self,
        database: "Database",
        scheduler: Optional[Scheduler] = None,
        run_service: Optional["RunService"] = None,
        framework: Optional[Any] = None,
    ) -> None:
        """Initialize ScheduleService.
        
        Args:
            database: Database implementation for schedule persistence
            scheduler: Optional Scheduler instance for APScheduler integration
            run_service: Optional RunService for triggering runs
            framework: Optional TaskFramework for task function lookup
        """
        self.database = database
        self.scheduler = scheduler
        self.run_service = run_service
        self.framework = framework

    async def load_active_schedules(self) -> int:
        """Load all active schedules from database into APScheduler.
        
        This method should be called on server startup to restore schedules
        after a restart. Only ACTIVE schedules are loaded.
        
        Returns:
            Number of schedules loaded
        """
        if not self.scheduler:
            logger.warning("scheduler.not_available", message="Scheduler not configured, skipping schedule loading")
            return 0
        
        # Query all active schedules
        active_schedules = await self.database.query_schedules({"state": "active"})
        
        loaded_count = 0
        for schedule in active_schedules:
            try:
                await self._add_schedule_to_scheduler(schedule)
                loaded_count += 1
                logger.info(
                    "schedule.loaded_on_startup",
                    schedule_id=schedule.id,
                    cron=schedule.cron,
                    timezone=schedule.timezone,
                )
            except Exception as e:
                logger.error(
                    "schedule.load_failed_on_startup",
                    schedule_id=schedule.id,
                    error=str(e),
                    exc_info=True,
                )
                # Continue loading other schedules even if one fails
        
        logger.info(
            "schedules.loaded_on_startup",
            total_active=len(active_schedules),
            loaded=loaded_count,
        )
        
        return loaded_count

    async def create_schedule(self, request: ScheduleCreateRequest) -> Schedule:
        """Create a new schedule.
        
        Args:
            request: Schedule creation request
            
        Returns:
            Created Schedule instance
            
        Raises:
            ValueError: If cron expression or timezone is invalid
        """
        # Generate schedule ID
        from task_framework.utils.id_generator import generate_schedule_id
        schedule_id = generate_schedule_id()
        
        # Validate cron and timezone (Pydantic validators handle this, but we check here too)
        try:
            from apscheduler.triggers.cron import CronTrigger
            CronTrigger.from_crontab(request.cron)
        except Exception as e:
            raise ValueError(f"Invalid cron expression: {request.cron}") from e
        
        try:
            from zoneinfo import ZoneInfo
            ZoneInfo(request.timezone)
        except Exception as e:
            raise ValueError(f"Invalid timezone identifier: {request.timezone}") from e
        
        # Create schedule
        now = datetime.now(timezone.utc)
        schedule = Schedule(
            id=schedule_id,
            cron=request.cron,
            timezone=request.timezone,
            state=request.state,
            task_id=request.task_id,
            task_version=request.task_version,
            inputs_template=request.inputs_template or [],
            params=request.params or {},
            metadata=request.metadata or {},
            webhooks=request.webhooks,
            concurrency_policy=request.concurrency_policy,
            max_attempts=request.max_attempts,
            created_at=now,
            updated_at=now,
        )
        
        # Save to database
        await self.database.create_schedule(schedule)
        
        # Create webhook records for schedule webhooks
        if request.webhooks:
            await self._create_schedule_webhooks(schedule)
        
        # If schedule is active, add to APScheduler
        if schedule.state == ScheduleState.ACTIVE and self.scheduler:
            await self._add_schedule_to_scheduler(schedule)
        
        # Metrics - update active schedules count
        if schedule.state == ScheduleState.ACTIVE:
            # Count active schedules from database
            active_schedules = await self.database.query_schedules({"state": "active"})
            schedules_active.set(len(active_schedules))
        
        # Logging
        logger.info(
            "schedule.created",
            schedule_id=schedule.id,
            cron=schedule.cron,
            timezone=schedule.timezone,
            state=str(schedule.state),
        )
        
        return schedule

    async def get_schedule(self, schedule_id: str) -> Optional[Schedule]:
        """Get a schedule by ID.
        
        Args:
            schedule_id: Schedule identifier
            
        Returns:
            Schedule instance if found, None otherwise
        """
        return await self.database.get_schedule(schedule_id)

    async def list_schedules(self, filters: Dict[str, Any]) -> ScheduleListResponse:
        """List schedules with filters and pagination.
        
        Args:
            filters: Filter dictionary containing:
                - state: Optional[str] - Filter by schedule state
                - limit: Optional[int] - Maximum number of results
                - cursor: Optional[str] - Pagination cursor
                - offset: Optional[int] - Offset for pagination
                
        Returns:
            ScheduleListResponse with paginated results
        """
        # Get all schedules (before pagination)
        state_filter = filters.get("state")
        task_id_filter = filters.get("task_id")
        task_version_filter = filters.get("task_version")
        filter_dict: Dict[str, Any] = {}
        if state_filter is not None:
            filter_dict["state"] = state_filter
        if task_id_filter is not None:
            filter_dict["task_id"] = task_id_filter
        if task_version_filter is not None:
            filter_dict["task_version"] = task_version_filter
        
        schedules = await self.database.query_schedules(filter_dict)
        
        # Apply cursor-based pagination
        limit = filters.get("limit") or 50
        cursor = filters.get("cursor")
        offset = filters.get("offset")
        
        if cursor:
            # Decode cursor (Base64 JSON with schedule_id and created_at)
            import base64
            import json as json_lib
            
            try:
                cursor_data = json_lib.loads(base64.b64decode(cursor).decode())
                cursor_schedule_id = cursor_data.get("schedule_id")
                cursor_created_at = cursor_data.get("created_at")
                
                # Filter schedules after cursor
                if cursor_created_at:
                    cursor_time = datetime.fromisoformat(cursor_created_at.replace("Z", "+00:00"))
                    schedules = [s for s in schedules if s.created_at < cursor_time]
            except (ValueError, KeyError, TypeError):
                # Invalid cursor, return empty
                schedules = []
        
        # Offset-based pagination fallback
        elif offset is not None:
            schedules = schedules[offset:]
        
        # Apply limit
        has_more = len(schedules) > limit
        schedules = schedules[:limit]
        
        # Generate next cursor if has_more
        next_cursor = None
        if has_more and schedules:
            import base64
            import json as json_lib
            
            last_schedule = schedules[-1]
            cursor_data = {
                "schedule_id": last_schedule.id,
                "created_at": last_schedule.created_at.isoformat() + "Z",
            }
            next_cursor = base64.b64encode(json_lib.dumps(cursor_data).encode()).decode()
        
        pagination = Pagination(
            cursor=next_cursor,
            has_more=has_more,
            total=None,
        )
        
        return ScheduleListResponse(items=schedules, pagination=pagination)

    async def update_schedule(self, schedule_id: str, request: ScheduleUpdateRequest) -> Schedule:
        """Update an existing schedule.
        
        Args:
            schedule_id: Schedule identifier
            request: Schedule update request
            
        Returns:
            Updated Schedule instance
            
        Raises:
            ValueError: If schedule not found or validation fails
        """
        schedule = await self.database.get_schedule(schedule_id)
        if not schedule:
            raise ValueError(f"Schedule {schedule_id} not found")
        
        # Validate cron if provided
        if request.cron is not None:
            try:
                from apscheduler.triggers.cron import CronTrigger
                CronTrigger.from_crontab(request.cron)
            except Exception as e:
                raise ValueError(f"Invalid cron expression: {request.cron}") from e
        
        # Validate timezone if provided
        if request.timezone is not None:
            try:
                from zoneinfo import ZoneInfo
                ZoneInfo(request.timezone)
            except Exception as e:
                raise ValueError(f"Invalid timezone identifier: {request.timezone}") from e
        
        # Update fields
        if request.cron is not None:
            schedule.cron = request.cron
        if request.timezone is not None:
            schedule.timezone = request.timezone
        if request.task_id is not None:
            schedule.task_id = request.task_id
        if request.task_version is not None:
            schedule.task_version = request.task_version
        if request.state is not None:
            schedule.state = request.state
        if request.inputs_template is not None:
            schedule.inputs_template = request.inputs_template
        if request.params is not None:
            schedule.params = request.params
        if request.metadata is not None:
            schedule.metadata = request.metadata
        if request.webhooks is not None:
            schedule.webhooks = request.webhooks
        if request.concurrency_policy is not None:
            schedule.concurrency_policy = request.concurrency_policy
        if request.max_attempts is not None:
            schedule.max_attempts = request.max_attempts
        
        schedule.updated_at = datetime.now(timezone.utc)
        
        # Update in database
        await self.database.update_schedule(schedule)
        
        # Update APScheduler job if scheduler is available
        if self.scheduler:
            # Remove existing job
            self.scheduler.remove_job(schedule_id)
            
            # Add new job if schedule is active
            # Schedule updates take effect immediately, ensuring next scheduled run uses new config
            if schedule.state == ScheduleState.ACTIVE:
                await self._add_schedule_to_scheduler(schedule)
        
        # Logging
        logger.info(
            "schedule.updated",
            schedule_id=schedule.id,
            state=str(schedule.state),
        )
        
        return schedule

    async def cancel_schedule(self, schedule_id: str) -> Schedule:
        """Cancel a schedule permanently.
        
        Args:
            schedule_id: Schedule identifier
            
        Returns:
            Canceled Schedule instance
            
        Raises:
            ValueError: If schedule not found
            
        Note:
            When a schedule is canceled:
            - Pending runs are stopped (state: stopped)
            - Currently running runs are allowed to complete
            - No new runs will be triggered
        """
        schedule = await self.database.get_schedule(schedule_id)
        if not schedule:
            raise ValueError(f"Schedule {schedule_id} not found")
        
        # Update state to canceled
        schedule.state = ScheduleState.CANCELED
        schedule.updated_at = datetime.now(timezone.utc)
        
        # Update in database
        await self.database.update_schedule(schedule)
        
        # Remove from APScheduler
        if self.scheduler:
            self.scheduler.remove_job(schedule_id)
        
        # Logging
        logger.info(
            "schedule.canceled",
            schedule_id=schedule.id,
        )
        
        return schedule

    async def pause_schedule(self, schedule_id: str) -> Schedule:
        """Pause a schedule.
        
        Args:
            schedule_id: Schedule identifier
            
        Returns:
            Paused Schedule instance
            
        Raises:
            ValueError: If schedule not found
            
        Note:
            When a schedule is paused:
            - Pending runs are stopped (state: stopped)
            - Currently running runs are allowed to complete
            - No new runs will be triggered until schedule is resumed
        """
        schedule = await self.database.get_schedule(schedule_id)
        if not schedule:
            raise ValueError(f"Schedule {schedule_id} not found")
        
        # Update state to paused
        schedule.state = ScheduleState.PAUSED
        schedule.updated_at = datetime.now(timezone.utc)
        
        # Update in database
        await self.database.update_schedule(schedule)
        
        # Remove from APScheduler
        if self.scheduler:
            self.scheduler.remove_job(schedule_id)
        
        # Logging
        logger.info(
            "schedule.paused",
            schedule_id=schedule.id,
        )
        
        return schedule

    async def _create_schedule_webhooks(self, schedule: Schedule) -> None:
        """Create webhook records in webhook repository for schedule webhooks.
        
        Args:
            schedule: Schedule instance with webhooks to create
        """
        if not schedule.webhooks:
            return
        
        try:
            from task_framework.services.webhook_service import WebhookService
            from task_framework.storage_factory import StorageFactory
            
            # Get webhook service via storage factory
            storage_factory = StorageFactory.from_env()
            webhook_repository = storage_factory.create_webhook_repository()
            delivery_repository = storage_factory.create_webhook_delivery_repository()
            webhook_service = WebhookService(
                webhook_repository=webhook_repository,
                delivery_repository=delivery_repository,
            )
            
            for webhook_config in schedule.webhooks:
                try:
                    await webhook_service.create_schedule_webhook(
                        url=webhook_config.callback_url,
                        schedule_id=schedule.id,
                        events=webhook_config.events,
                        api_key=webhook_config.api_key,
                    )
                    
                    logger.info(
                        "schedule.webhook.created",
                        schedule_id=schedule.id,
                        url=webhook_config.callback_url,
                    )
                except Exception as e:
                    logger.error(
                        "schedule.webhook.creation.failed",
                        schedule_id=schedule.id,
                        url=webhook_config.callback_url,
                        error=str(e),
                    )
        except Exception as e:
            logger.error(
                "schedule.webhooks.setup.failed",
                schedule_id=schedule.id,
                error=str(e),
            )

    async def _add_schedule_to_scheduler(self, schedule: Schedule) -> None:
        """Add a schedule to APScheduler.
        
        Args:
            schedule: Schedule instance to add
        """
        if not self.scheduler:
            return
        
        from apscheduler.triggers.cron import CronTrigger
        
        # Ensure scheduler is running
        if not self.scheduler.is_running():
            self.scheduler.start()
        
        # Create cron trigger
        trigger = CronTrigger.from_crontab(schedule.cron, timezone=schedule.timezone)
        
        # Create async callback function for triggering runs
        async def trigger_run():
            """Trigger run execution when cron fires."""
            try:
                # Get fresh schedule from database
                schedule_fresh = await self.database.get_schedule(schedule.id)
                if not schedule_fresh:
                    logger.warning(
                        "schedule.run.triggered.schedule_not_found",
                        schedule_id=schedule.id,
                    )
                    return
                
                # Skip if schedule is not active
                if schedule_fresh.state != ScheduleState.ACTIVE:
                    state_str = schedule_fresh.state.value if hasattr(schedule_fresh.state, 'value') else str(schedule_fresh.state)
                    logger.info(
                        "schedule.run.triggered.skipped",
                        schedule_id=schedule.id,
                        state=state_str,
                    )
                    return
                
                # Create run
                if not self.run_service:
                    logger.error(
                        "schedule.run.triggered.run_service_unavailable",
                        schedule_id=schedule.id,
                    )
                    return
                
                # Create run with deterministic timestamp (truncated to second)
                # This ensures all workers generate the same run_id for this trigger
                scheduled_for_utc = datetime.now(timezone.utc).replace(microsecond=0)
                run = await self.run_service.create_run(schedule_fresh, scheduled_for_utc)
                
                # Check if this run is already being processed by another worker
                # If the run state is not PENDING, another worker is handling it
                run_state_str = run.state.value if hasattr(run.state, 'value') else str(run.state)
                if run_state_str != "pending":
                    logger.debug(
                        "schedule.run.triggered.already_processing",
                        schedule_id=schedule.id,
                        run_id=run.run_id,
                        state=run_state_str,
                    )
                    return
                
                # Metrics: Track run creation
                schedule_runs_total.labels(
                    schedule_id=schedule_fresh.id,
                    state=run_state_str,
                ).inc()
                
                # Check concurrency policy before executing
                from task_framework.scheduler.concurrency import ConcurrencyPolicyHandler
                from task_framework.services.artifact_service import ArtifactService
                
                artifact_service = ArtifactService(self.database)
                
                # Get thread service from run_service
                thread_service = self.run_service.thread_service if hasattr(self.run_service, 'thread_service') else None
                
                concurrency_handler = ConcurrencyPolicyHandler(
                    database=self.database,
                    artifact_service=artifact_service,
                    thread_service=thread_service,
                )
                
                # Check and enforce concurrency policy
                should_proceed = await concurrency_handler.check_and_enforce(schedule_fresh, run)
                
                if not should_proceed:
                    # Run was skipped (forbid policy)
                    logger.info(
                        "schedule.run.triggered.skipped",
                        schedule_id=schedule.id,
                        run_id=run.run_id,
                    )
                    return
                
                # Get task function from framework registry
                task_function = None
                if self.framework:
                    task_def = self.framework.get_task(schedule_fresh.task_id, schedule_fresh.task_version)
                    if task_def:
                        task_function = task_def.get_task_function()
                        
                        # Lazy load if function not in memory (deployed tasks)
                        if not task_function:
                            try:
                                from task_framework.services.task_loader import TaskLoader
                                from pathlib import Path
                                import json
                                
                                task_storage = self.framework.task_storage
                                if task_storage:
                                    task_loader = TaskLoader(task_storage)
                                    
                                    # Get metadata for this task version
                                    metadata_path = Path(task_storage.get_task_base_path(task_def.task_id, task_def.version)) / "metadata.json"
                                    if metadata_path.exists():
                                        with open(metadata_path, 'r') as f:
                                            metadata_dict = json.load(f)
                                        from task_framework.models.task_definition import TaskMetadata
                                        metadata = TaskMetadata.model_validate(metadata_dict)
                                        
                                        # Load the task function from deployed code
                                        code_path = task_storage.get_code_path(task_def.task_id, task_def.version)
                                        task_function = await task_loader._load_task_function(str(code_path), metadata.entry_point)
                                        
                                        # Cache it on the task_def for next time
                                        if task_function:
                                            task_def.set_task_function(task_function)
                                            logger.info(
                                                "schedule.run.triggered.task_function_loaded",
                                                schedule_id=schedule.id,
                                                task_id=schedule_fresh.task_id,
                                                task_version=schedule_fresh.task_version,
                                            )
                            except Exception as e:
                                logger.error(
                                    "schedule.run.triggered.task_function_load_error",
                                    schedule_id=schedule.id,
                                    task_id=schedule_fresh.task_id,
                                    task_version=schedule_fresh.task_version,
                                    error=str(e),
                                )
                
                if task_function:
                    await self.run_service.trigger_run_execution(
                        run, schedule_fresh, task_function
                    )
                    
                    # Update metrics with final run state
                    run_final = await self.run_service.get_run(run.schedule_id, run.run_id)
                    if run_final:
                        final_state_str = run_final.state.value if hasattr(run_final.state, 'value') else str(run_final.state)
                        schedule_runs_total.labels(
                            schedule_id=schedule_fresh.id,
                            state=final_state_str,
                        ).inc()
                else:
                    logger.warning(
                        "schedule.run.triggered.task_function_unavailable",
                        schedule_id=schedule.id,
                        run_id=run.run_id,
                        task_id=schedule_fresh.task_id,
                        task_version=schedule_fresh.task_version,
                    )
            except Exception as e:
                logger.error(
                    "schedule.run.triggered.error",
                    schedule_id=schedule.id,
                    error=str(e),
                )
        
        # Add job to scheduler
        self.scheduler.add_job(
            trigger_run,
            trigger=trigger,
            id=schedule.id,
            replace_existing=True,
        )

