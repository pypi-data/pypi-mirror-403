"""Schedule API endpoints for managing cron-based schedules."""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from task_framework.dependencies import (
    AuthenticatedRequest,
    TaskContext,
    get_authenticated_request,
    get_framework,
    get_task_context,
    get_task_database,
)
from task_framework.errors import (
    SCHEDULE_INVALID_CRON,
    SCHEDULE_INVALID_TIMEZONE,
    SCHEDULE_NOT_FOUND,
    problem_json_dict,
)
from task_framework.logging import logger
from task_framework.metrics import api_requests_total
from task_framework.models.schedule import Schedule, ScheduleCreateRequest, ScheduleUpdateRequest, ScheduleListResponse
from task_framework.repositories.file_db import FileDatabase
from task_framework.scheduler.scheduler import Scheduler
from task_framework.services.scheduler_service import ScheduleService

router = APIRouter(prefix="/schedules", tags=["schedules"])


async def get_schedule_service(
    task_context: TaskContext = Depends(get_task_context),
    framework: Any = Depends(get_framework),
) -> ScheduleService:
    """Get ScheduleService instance with dependencies.
    
    Uses task-specific database in multi-task mode.
    
    Args:
        task_context: Resolved task context with optional TaskDefinition
        framework: TaskFramework instance
        
    Returns:
        ScheduleService instance
    """
    # Get database (task-specific in multi-task mode)
    task_def = task_context.task_definition
    database = get_task_database(task_def, framework) 
    
    # Get or create scheduler
    scheduler = None
    if framework.scheduler:
        scheduler = framework.scheduler
    else:
        scheduler = Scheduler()
        # Don't start scheduler here - it requires an async event loop
        # The scheduler will be started lazily when needed (e.g., when adding jobs)
    
    # Create run service
    from task_framework.services.run_service import RunService
    from task_framework.services.thread_service import ThreadService
    from task_framework.repositories.file_idempotency import FileIdempotencyStore
    
    idempotency_store = FileIdempotencyStore(database=database)
    thread_service = ThreadService(
        database=database,
        idempotency_store=idempotency_store,
        execution_engine=framework.execution_engine,
    )
    
    run_service = RunService(
        database=database,
        thread_service=thread_service,
    )
    
    return ScheduleService(
        database=database,
        scheduler=scheduler,
        run_service=run_service,
        framework=framework,
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=Schedule)
async def create_schedule(
    request: ScheduleCreateRequest,
    auth: AuthenticatedRequest = Depends(get_authenticated_request),
    schedule_service: ScheduleService = Depends(get_schedule_service),
    task_context: TaskContext = Depends(get_task_context),
) -> Schedule:
    """Create a new schedule.
    
    Args:
        request: Schedule creation request
        auth: Authenticated request context
        schedule_service: ScheduleService instance
        task_context: Task context for auto-populating task_id/version
        
    Returns:
        Created Schedule instance
        
    Raises:
        HTTPException: 400 if validation fails
    """
    try:
        # Auto-populate task_id and task_version from task context if not provided
        # This ensures threads created from this schedule will have task metadata
        if task_context.task_definition:
            if not request.task_id:
                request.task_id = task_context.task_definition.task_id
            if not request.task_version:
                request.task_version = task_context.task_definition.version
        
        schedule = await schedule_service.create_schedule(request)
        
        # Metrics
        api_requests_total.labels(method="POST", endpoint="/schedules", status="201").inc()
        
        return schedule
    except ValueError as e:
        error_msg = str(e)
        api_requests_total.labels(method="POST", endpoint="/schedules", status="400").inc()
        
        # Determine error code
        if "cron" in error_msg.lower():
            code = SCHEDULE_INVALID_CRON
        elif "timezone" in error_msg.lower():
            code = SCHEDULE_INVALID_TIMEZONE
        else:
            code = "SCHEDULE_VALIDATION_ERROR"
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=problem_json_dict(
                status_code=status.HTTP_400_BAD_REQUEST,
                title="Bad Request",
                detail=error_msg,
                code=code,
            ),
        )


@router.get("", response_model=ScheduleListResponse)
async def list_schedules(
    state: Optional[str] = Query(None, description="Filter by schedule state"),
    task_id: Optional[str] = Query(None, description="Filter by task definition ID"),
    task_version: Optional[str] = Query(None, description="Filter by task version"),
    limit: Optional[int] = Query(50, ge=1, le=1000, description="Maximum number of results"),
    cursor: Optional[str] = Query(None, description="Cursor for pagination"),
    offset: Optional[int] = Query(None, ge=0, description="Offset for pagination"),
    auth: AuthenticatedRequest = Depends(get_authenticated_request),
    framework: Any = Depends(get_framework),
) -> ScheduleListResponse:
    """List schedules with filtering and pagination.
    
    Args:
        state: Filter by schedule state
        task_id: Filter by task definition ID
        task_version: Filter by task version
        limit: Maximum number of results
        cursor: Cursor for pagination
        offset: Offset for pagination (alternative to cursor)
        auth: Authenticated request context
        framework: TaskFramework instance
        
    Returns:
        ScheduleListResponse with paginated results
    """
    filters: dict[str, Any] = {}
    if state is not None:
        filters["state"] = state
    if task_id is not None:
        filters["task_id"] = task_id
    if task_version is not None:
        filters["task_version"] = task_version
    if limit is not None:
        filters["limit"] = limit
    if cursor is not None:
        filters["cursor"] = cursor
    if offset is not None:
        filters["offset"] = offset
    
    # Use framework database directly to list schedules across all tasks
    database = framework.database 
    
    # Query schedules using the database
    from task_framework.services.scheduler_service import ScheduleService
    from task_framework.scheduler.scheduler import Scheduler
    from task_framework.services.run_service import RunService
    from task_framework.services.thread_service import ThreadService
    from task_framework.repositories.file_idempotency import FileIdempotencyStore
    
    idempotency_store = FileIdempotencyStore(database=database)
    thread_service = ThreadService(
        database=database,
        idempotency_store=idempotency_store,
        execution_engine=framework.execution_engine,
    )
    run_service = RunService(
        database=database,
        thread_service=thread_service,
    )
    
    schedule_service = ScheduleService(
        database=database,
        scheduler=framework.scheduler or Scheduler(),
        run_service=run_service,
        framework=None,  # Not needed for listing
    )
    
    response = await schedule_service.list_schedules(filters)
    
    # Metrics
    api_requests_total.labels(method="GET", endpoint="/schedules", status="200").inc()
    
    return response


@router.get("/{schedule_id}", response_model=Schedule)
async def get_schedule(
    schedule_id: str,
    auth: AuthenticatedRequest = Depends(get_authenticated_request),
    framework: Any = Depends(get_framework),
) -> Schedule:
    """Get schedule by ID.
    
    Args:
        schedule_id: Schedule identifier
        auth: Authenticated request context
        framework: TaskFramework instance
        
    Returns:
        Schedule instance
        
    Raises:
        HTTPException: 404 if schedule not found
    """
    # Use framework database directly
    database = framework.database 
    schedule = await database.get_schedule(schedule_id)
    
    if not schedule:
        api_requests_total.labels(method="GET", endpoint="/schedules/{schedule_id}", status="404").inc()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=problem_json_dict(
                status_code=status.HTTP_404_NOT_FOUND,
                title="Schedule Not Found",
                detail=f"Schedule {schedule_id} not found",
                code=SCHEDULE_NOT_FOUND,
            ),
        )
    
    # Metrics
    api_requests_total.labels(method="GET", endpoint="/schedules/{schedule_id}", status="200").inc()
    
    return schedule


@router.patch("/{schedule_id}", response_model=Schedule)
async def update_schedule(
    schedule_id: str,
    request: ScheduleUpdateRequest,
    auth: AuthenticatedRequest = Depends(get_authenticated_request),
    framework: Any = Depends(get_framework),
) -> Schedule:
    """Update a schedule.
    
    Args:
        schedule_id: Schedule identifier
        request: Schedule update request
        auth: Authenticated request context
        framework: TaskFramework instance
        
    Returns:
        Updated Schedule instance
        
    Raises:
        HTTPException: 400 if validation fails, 404 if schedule not found
    """
    # Use framework database directly
    database = framework.database 
    
    # Create schedule service
    from task_framework.scheduler.scheduler import Scheduler
    from task_framework.services.run_service import RunService
    from task_framework.services.thread_service import ThreadService
    from task_framework.repositories.file_idempotency import FileIdempotencyStore
    
    idempotency_store = FileIdempotencyStore(database=database)
    thread_service = ThreadService(
        database=database,
        idempotency_store=idempotency_store,
        execution_engine=framework.execution_engine,
    )
    run_service = RunService(
        database=database,
        thread_service=thread_service,
    )
    schedule_service = ScheduleService(
        database=database,
        scheduler=framework.scheduler or Scheduler(),
        run_service=run_service,
        framework=None,
    )
    
    try:
        schedule = await schedule_service.update_schedule(schedule_id, request)
        
        # Metrics
        api_requests_total.labels(method="PATCH", endpoint="/schedules/{schedule_id}", status="200").inc()
        
        return schedule
    except ValueError as e:
        error_msg = str(e)
        
        if "not found" in error_msg.lower():
            api_requests_total.labels(method="PATCH", endpoint="/schedules/{schedule_id}", status="404").inc()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=problem_json_dict(
                    status_code=status.HTTP_404_NOT_FOUND,
                    title="Schedule Not Found",
                    detail=error_msg,
                    code=SCHEDULE_NOT_FOUND,
                ),
            )
        
        # Determine error code
        if "cron" in error_msg.lower():
            code = SCHEDULE_INVALID_CRON
        elif "timezone" in error_msg.lower():
            code = SCHEDULE_INVALID_TIMEZONE
        else:
            code = "SCHEDULE_VALIDATION_ERROR"
        
        api_requests_total.labels(method="PATCH", endpoint="/schedules/{schedule_id}", status="400").inc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=problem_json_dict(
                status_code=status.HTTP_400_BAD_REQUEST,
                title="Bad Request",
                detail=error_msg,
                code=code,
            ),
        )


@router.post("/{schedule_id}:cancel", response_model=Schedule)
async def cancel_schedule(
    schedule_id: str,
    auth: AuthenticatedRequest = Depends(get_authenticated_request),
    framework: Any = Depends(get_framework),
) -> Schedule:
    """Cancel a schedule permanently.
    
    Args:
        schedule_id: Schedule identifier
        auth: Authenticated request context
        framework: TaskFramework instance
        
    Returns:
        Canceled Schedule instance
        
    Raises:
        HTTPException: 404 if schedule not found
    """
    # Use framework database directly
    database = framework.database 
    
    # Create schedule service
    from task_framework.scheduler.scheduler import Scheduler
    from task_framework.services.run_service import RunService
    from task_framework.services.thread_service import ThreadService
    from task_framework.repositories.file_idempotency import FileIdempotencyStore
    
    idempotency_store = FileIdempotencyStore(database=database)
    thread_service = ThreadService(
        database=database,
        idempotency_store=idempotency_store,
        execution_engine=framework.execution_engine,
    )
    run_service = RunService(
        database=database,
        thread_service=thread_service,
    )
    schedule_service = ScheduleService(
        database=database,
        scheduler=framework.scheduler or Scheduler(),
        run_service=run_service,
        framework=None,
    )
    
    try:
        schedule = await schedule_service.cancel_schedule(schedule_id)
        
        # Metrics
        api_requests_total.labels(method="POST", endpoint="/schedules/{schedule_id}:cancel", status="200").inc()
        
        return schedule
    except ValueError as e:
        error_msg = str(e)
        api_requests_total.labels(method="POST", endpoint="/schedules/{schedule_id}:cancel", status="404").inc()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=problem_json_dict(
                status_code=status.HTTP_404_NOT_FOUND,
                title="Schedule Not Found",
                detail=error_msg,
                code=SCHEDULE_NOT_FOUND,
            ),
        )

