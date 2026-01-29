"""Run API endpoints for querying scheduled runs."""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from task_framework.dependencies import AuthenticatedRequest, TaskContext, get_authenticated_request, get_framework, get_task_context, get_task_database
from task_framework.errors import RUN_NOT_FOUND, SCHEDULE_NOT_FOUND, problem_json_dict
from task_framework.logging import logger
from task_framework.metrics import api_requests_total
from task_framework.models.schedule import Run, Schedule, RunListResponse
from task_framework.repositories.file_db import FileDatabase
from task_framework.services.run_service import RunService
from task_framework.services.scheduler_service import ScheduleService
from task_framework.services.thread_service import ThreadService
from task_framework.repositories.file_idempotency import FileIdempotencyStore

router = APIRouter(prefix="/schedules/{schedule_id}/runs", tags=["runs"])


async def get_run_service(
    framework: Any = Depends(get_framework),
) -> RunService:
    """Get RunService instance with dependencies.
    
    Uses framework database to query runs across all tasks.
    
    Args:
        framework: TaskFramework instance
        
    Returns:
        RunService instance
    """
    # Use framework database directly to work across all tasks
    database = framework.database 
    
    # Create thread service
    idempotency_store = FileIdempotencyStore(database=database)
    thread_service = ThreadService(
        database=database,
        idempotency_store=idempotency_store,
        execution_engine=framework.execution_engine,
    )
    
    return RunService(
        database=database,
        thread_service=thread_service,
    )


async def get_schedule_service_for_runs(
    framework: Any = Depends(get_framework),
) -> ScheduleService:
    """Get ScheduleService instance for verifying schedule exists.
    
    Uses framework database to query schedules across all tasks.
    
    Args:
        framework: TaskFramework instance
        
    Returns:
        ScheduleService instance
    """
    # Use framework database directly
    database = framework.database 
    
    return ScheduleService(database=database)


@router.get("", response_model=RunListResponse)
async def list_runs(
    schedule_id: str,
    task_id: Optional[str] = Query(None, description="Task identifier (optional, helps locate schedule in multi-task mode)"),
    version: Optional[str] = Query(None, description="Task version (optional, helps locate schedule in multi-task mode)"),
    state: Optional[str] = Query(None, description="Filter by run state"),
    scheduled_after: Optional[str] = Query(None, description="Filter runs scheduled after (ISO 8601 UTC)"),
    scheduled_before: Optional[str] = Query(None, description="Filter runs scheduled before (ISO 8601 UTC)"),
    limit: Optional[int] = Query(50, ge=1, le=1000, description="Maximum number of results"),
    cursor: Optional[str] = Query(None, description="Cursor for pagination"),
    offset: Optional[int] = Query(None, ge=0, description="Offset for pagination"),
    auth: AuthenticatedRequest = Depends(get_authenticated_request),
    run_service: RunService = Depends(get_run_service),
    schedule_service: ScheduleService = Depends(get_schedule_service_for_runs),
    framework: Any = Depends(get_framework),
) -> RunListResponse:
    """List runs for a schedule with filtering and pagination.
    
    Args:
        schedule_id: Schedule identifier
        state: Filter by run state
        scheduled_after: Filter runs scheduled after (ISO 8601 UTC)
        scheduled_before: Filter runs scheduled before (ISO 8601 UTC)
        limit: Maximum number of results
        cursor: Cursor for pagination
        offset: Offset for pagination (alternative to cursor)
        auth: Authenticated request context
        run_service: RunService instance
        schedule_service: ScheduleService instance
        
    Returns:
        RunListResponse with paginated results
        
    Raises:
        HTTPException: 404 if schedule not found
    """
    # Verify schedule exists
    schedule = await schedule_service.get_schedule(schedule_id)
    if not schedule:
        api_requests_total.labels(method="GET", endpoint="/schedules/{schedule_id}/runs", status="404").inc()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=problem_json_dict(
                status_code=status.HTTP_404_NOT_FOUND,
                title="Schedule Not Found",
                detail=f"Schedule {schedule_id} not found",
                code=SCHEDULE_NOT_FOUND,
            ),
        )
    
    # Use the same database that found the schedule (they're stored together)
    # This ensures runs are queried from the same database as the schedule
    # Get the database instance that was used to find the schedule
    schedule_db = schedule_service.database
    
    # If schedule has task_id, ensure we're using the task-specific database
    # Recreate run_service with schedule's database to ensure consistency
    idempotency_store = FileIdempotencyStore(database=schedule_db)
    thread_service = ThreadService(
        database=schedule_db,
        idempotency_store=idempotency_store,
        execution_engine=framework.execution_engine,
    )
    run_service = RunService(database=schedule_db, thread_service=thread_service)
    
    # Debug: Log database path if available
    if hasattr(schedule_db, 'base_path'):
        logger.debug(f"Querying runs from database path: {schedule_db.base_path}")
    
    # Parse datetime strings
    filters: dict[str, Any] = {}
    if state is not None:
        filters["state"] = state
    if scheduled_after is not None:
        try:
            filters["scheduled_after"] = datetime.fromisoformat(scheduled_after.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=problem_json_dict(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    title="Bad Request",
                    detail="Invalid scheduled_after format. Use ISO 8601 UTC format.",
                ),
            )
    if scheduled_before is not None:
        try:
            filters["scheduled_before"] = datetime.fromisoformat(scheduled_before.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=problem_json_dict(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    title="Bad Request",
                    detail="Invalid scheduled_before format. Use ISO 8601 UTC format.",
                ),
            )
    if limit is not None:
        filters["limit"] = limit
    if cursor is not None:
        filters["cursor"] = cursor
    if offset is not None:
        filters["offset"] = offset
    
    response = await run_service.list_runs(schedule_id, filters)
    
    # Metrics
    api_requests_total.labels(method="GET", endpoint="/schedules/{schedule_id}/runs", status="200").inc()
    
    return response


@router.get("/{run_id}", response_model=Run)
async def get_run(
    schedule_id: str,
    run_id: str,
    task_id: Optional[str] = Query(None, description="Task identifier (optional, helps locate schedule in multi-task mode)"),
    version: Optional[str] = Query(None, description="Task version (optional, helps locate schedule in multi-task mode)"),
    auth: AuthenticatedRequest = Depends(get_authenticated_request),
    run_service: RunService = Depends(get_run_service),
    schedule_service: ScheduleService = Depends(get_schedule_service_for_runs),
    framework: Any = Depends(get_framework),
) -> Run:
    """Get run details by schedule_id and run_id.
    
    Args:
        schedule_id: Schedule identifier
        run_id: Run identifier
        auth: Authenticated request context
        run_service: RunService instance
        schedule_service: ScheduleService instance
        
    Returns:
        Run instance
        
    Raises:
        HTTPException: 404 if schedule or run not found
    """
    # Verify schedule exists
    schedule = await schedule_service.get_schedule(schedule_id)
    if not schedule:
        api_requests_total.labels(method="GET", endpoint="/schedules/{schedule_id}/runs/{run_id}", status="404").inc()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=problem_json_dict(
                status_code=status.HTTP_404_NOT_FOUND,
                title="Schedule Not Found",
                detail=f"Schedule {schedule_id} not found",
                code=SCHEDULE_NOT_FOUND,
            ),
        )
    
    # Get run
    run = await run_service.get_run(schedule_id, run_id)
    
    if not run:
        api_requests_total.labels(method="GET", endpoint="/schedules/{schedule_id}/runs/{run_id}", status="404").inc()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=problem_json_dict(
                status_code=status.HTTP_404_NOT_FOUND,
                title="Run Not Found",
                detail=f"Run {run_id} not found for schedule {schedule_id}",
                code=RUN_NOT_FOUND,
            ),
        )
    
    # Metrics
    api_requests_total.labels(method="GET", endpoint="/schedules/{schedule_id}/runs/{run_id}", status="200").inc()
    
    return run

