"""Thread management API endpoints.

Provides endpoints for creating, listing, and managing thread executions.
A thread represents a single execution of a task with inputs, outputs, and state.

In multi-task mode, use the `task_id` and `version` query parameters to specify
which task to execute. If only one task is registered, these parameters are optional.

For POST /threads (create), the task_id/version determine which task function to run.
For GET/POST operations on existing threads, the task_id helps locate the thread faster
when multiple task databases exist.
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from task_framework.dependencies import (
    AuthenticatedRequest,
    TaskContext,
    get_authenticated_request,
    get_framework,
    get_task_context,
    get_task_database,
    get_task_file_storage,
    get_task_function,
)
from task_framework.errors import (
    THREAD_INVALID_STATE,
    THREAD_NOT_FOUND,
    VALIDATION_FAILED,
    problem_json_dict,
)
from task_framework.logging import logger
from task_framework.metrics import api_requests_total
from task_framework.models.artifact_schema import ArtifactSchema, validate_artifact_against_schema, validate_artifact_against_schemas
from task_framework.models.thread import Thread
from task_framework.models.thread_create_request import ThreadCreateRequest
from task_framework.models.thread_list_response import ThreadListResponse
from task_framework.models.thread_query_filters import ThreadQueryFilters
from task_framework.models.thread_retry_request import ThreadRetryRequest
from task_framework.repositories.file_db import FileDatabase
from task_framework.repositories.file_idempotency import FileIdempotencyStore
from task_framework.services.thread_service import ThreadService

router = APIRouter(prefix="/threads", tags=["threads"])


def get_thread_service(
    task_context: TaskContext = Depends(get_task_context),
    framework: Any = Depends(get_framework),
) -> ThreadService:
    """Get ThreadService instance with dependencies.
    
    Uses task-specific database in multi-task mode, or framework database in single-task mode.
    
    Args:
        task_context: Resolved task context with optional TaskDefinition
        framework: TaskFramework instance
        
    Returns:
        ThreadService instance
    """
    # Get database from framework (uses StorageFactory - either ES or file-based)
    # The framework.database property lazily creates the appropriate database
    task_def = task_context.task_definition
    database = get_task_database(task_def, framework)
    
    # Fall back to framework.database if get_task_database returns None
    # This ensures we always use the configured storage backend
    if database is None:
        database = framework.database
    
    # Debug logging to trace database type
    logger.info(
        "threads.get_thread_service.database",
        database_type=type(database).__name__ if database else "None",
        has_database=database is not None,
    )
    
    idempotency_store = FileIdempotencyStore(database=database)

    # Get execution engine from the framework
    execution_engine = framework.execution_engine

    return ThreadService(
        database=database,
        idempotency_store=idempotency_store,
        execution_engine=execution_engine,
        concurrency_manager=getattr(framework, "concurrency_manager", None),
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_thread(
    request: ThreadCreateRequest,
    auth: AuthenticatedRequest = Depends(get_authenticated_request),
    task_context: TaskContext = Depends(get_task_context),
    thread_service: ThreadService = Depends(get_thread_service),
    framework: Any = Depends(get_framework),
):
    """Create and execute a thread.
    
    Creates a new thread to execute a task with the provided inputs. The thread will
    be executed synchronously (waiting for completion) or asynchronously (returning 
    immediately) based on the `mode` field in the request body.
    
    **Multi-Task Mode**: When multiple tasks are registered, you must specify:
    - `task_id` (query param): Required to identify which task to execute
    - `version` (query param): Optional, defaults to latest version
    
    **Single-Task Mode**: When only one task is registered, `task_id` is optional.
    
    Args:
        request: Thread creation request with inputs, mode, and optional params
        auth: Authenticated request context with user_id/app_id
        task_context: Resolved task context with TaskDefinition
        thread_service: ThreadService instance
        framework: TaskFramework instance
        
    Returns:
        - 201 Created: Sync mode - Thread executed and completed
        - 202 Accepted: Async mode - Thread queued for execution
        
    Raises:
        HTTPException: 
            - 400 Bad Request: Validation error or task_id required but not provided
            - 409 Conflict: Idempotency key already used
            - 503 Service Unavailable: Task function not registered
    """
    # Get task function from task definition (multi-task) or framework (single-task)
    task_def = task_context.task_definition
    task_function = await get_task_function(task_def, framework)
    
    if not task_function:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=problem_json_dict(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                title="Service Unavailable",
                detail="Task function not registered",
            ),
        )

    # Get input schemas from task definition (multi-task) or framework (single-task)
    input_schemas = []
    if task_def:
        # Convert dict schemas to ArtifactSchema objects
        input_schemas = [
            ArtifactSchema.model_validate(s) if isinstance(s, dict) else s
            for s in task_def.input_schemas
        ]
    else:
        # Fallback to framework schemas
        input_schemas = getattr(framework, "input_schemas", None) or []
        if not input_schemas:
            # Fallback to singular for backward compatibility
            input_schema_singular = getattr(framework, "input_schema", None)
            input_schemas = [input_schema_singular] if input_schema_singular is not None else []
    
    if input_schemas:
        # Validate each input artifact dict (use model_dump to get dicts if needed)
        try:
            for art in request.inputs:
                # Convert Pydantic Artifact to dict when necessary
                art_dict = art.model_dump() if hasattr(art, "model_dump") else dict(art)
                validate_artifact_against_schemas(art_dict, input_schemas)
        except ValueError as validation_error:
            api_requests_total.labels(method="POST", endpoint="/threads", status="400").inc()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=problem_json_dict(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    title="Bad Request",
                    detail=f"Input artifact validation failed: {str(validation_error)}",
                    code=VALIDATION_FAILED,
                ),
            )

    try:
        thread = await thread_service.create_thread(
            request=request,
            user_id=auth.user_id,
            app_id=auth.app_id,
            is_admin=auth.key_type == "admin",
            task_function=task_function,
            task_definition=task_def,
            requested_version=task_context.version,  # Pass the requested version
        )

        # Log thread creation
        logger.info(
            "thread.created",
            thread_id=thread.id,
            mode=request.mode,
            user_id=auth.user_id,
            app_id=auth.app_id,
            state=str(thread.state),
            task_id=task_context.task_id,
            task_version=task_context.version,
        )

        # For async mode, return 202 Accepted
        if request.mode == "async":
            import json

            from fastapi.responses import JSONResponse

            api_requests_total.labels(method="POST", endpoint="/threads", status="202").inc()
            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED,
                content=json.loads(thread.model_dump_json(exclude_none=True)),
            )

        # For sync mode, return 201 Created
        api_requests_total.labels(method="POST", endpoint="/threads", status="201").inc()
        return thread
    except ValueError as e:
        api_requests_total.labels(method="POST", endpoint="/threads", status="400").inc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=problem_json_dict(
                status_code=status.HTTP_400_BAD_REQUEST,
                title="Bad Request",
                detail=str(e),
                code=VALIDATION_FAILED,
            ),
        )


@router.get("", response_model=ThreadListResponse)
async def list_threads(
    state: str | None = Query(None, description="Filter by thread state"),
    name: str | None = Query(None, description="Filter by thread name (exact match or prefix with * suffix)"),
    user_id: str | None = Query(None, description="Filter by user_id"),
    app_id: str | None = Query(None, description="Filter by app_id"),
    schedule_id: str | None = Query(None, description="Filter by schedule_id"),
    run_id: str | None = Query(None, description="Filter by run_id"),
    task_id: str | None = Query(None, description="Filter by task_id"),
    task_version: str | None = Query(None, description="Filter by task_version"),
    created_after: str | None = Query(None, description="Filter threads created after (ISO 8601 UTC)"),
    created_before: str | None = Query(None, description="Filter threads created before (ISO 8601 UTC)"),
    started_after: str | None = Query(None, description="Filter threads started after (ISO 8601 UTC)"),
    finished_before: str | None = Query(None, description="Filter threads finished before (ISO 8601 UTC)"),
    limit: int | None = Query(50, ge=1, le=1000, description="Maximum number of results"),
    cursor: str | None = Query(None, description="Cursor for pagination"),
    offset: int | None = Query(None, ge=0, description="Offset for pagination"),
    auth: AuthenticatedRequest = Depends(get_authenticated_request),
    framework: Any = Depends(get_framework),
) -> ThreadListResponse:
    """List threads with filtering and pagination.
    
    In multi-task mode, aggregates threads from all task databases unless task_id is specified.
    
    Args:
        state: Filter by thread state
        user_id: Filter by user_id
        app_id: Filter by app_id
        schedule_id: Filter by schedule_id
        run_id: Filter by run_id
        task_id: Filter by task_id (limits search to specific task)
        task_version: Filter by task_version
        created_after: Filter threads created after
        created_before: Filter threads created before
        started_after: Filter threads started after
        finished_before: Filter threads finished before
        limit: Maximum number of results
        cursor: Cursor for pagination
        offset: Offset for pagination
        auth: Authenticated request context
        framework: TaskFramework instance
        
    Returns:
        ThreadListResponse with paginated results
    """
    from datetime import datetime
    from task_framework.models.pagination import Pagination

    # Parse datetime strings
    filters = ThreadQueryFilters(
        state=state,
        name=name,
        user_id=user_id,
        app_id=app_id,
        schedule_id=schedule_id,
        run_id=run_id,
        task_id=task_id,
        task_version=task_version,
        created_after=datetime.fromisoformat(created_after.replace("Z", "+00:00")) if created_after else None,
        created_before=datetime.fromisoformat(created_before.replace("Z", "+00:00")) if created_before else None,
        started_after=datetime.fromisoformat(started_after.replace("Z", "+00:00")) if started_after else None,
        finished_before=datetime.fromisoformat(finished_before.replace("Z", "+00:00")) if finished_before else None,
        limit=limit,
        cursor=cursor,
        offset=offset,
    )

    all_threads = []
    
    # If task_id is provided, search in that specific task's database(s)
    if task_id:
        # If version is also provided, search only that version
        if task_version:
            task_def = framework.get_task(task_id, task_version)
            if task_def:
                database = get_task_database(task_def, framework)
                if database:
                    thread_service = ThreadService(
                        database=database,
                        idempotency_store=FileIdempotencyStore(database=database),
                        execution_engine=framework.execution_engine,
                    )
                    response = await thread_service.list_threads(
                        filters=filters,
                        user_id=auth.user_id,
                        app_id=auth.app_id,
                        is_admin=auth.key_type == "admin",
                    )
                    api_requests_total.labels(method="GET", endpoint="/threads", status="200").inc()
                    return response
        else:
            # Search all versions of the task
            for task_def in framework.task_registry.list_by_task(task_id):
                database = get_task_database(task_def, framework)
                if database:
                    thread_service = ThreadService(
                        database=database,
                        idempotency_store=FileIdempotencyStore(database=database),
                        execution_engine=framework.execution_engine,
                    )
                    response = await thread_service.list_threads(
                        filters=filters,
                        user_id=auth.user_id,
                        app_id=auth.app_id,
                        is_admin=auth.key_type == "admin",
                    )
                    all_threads.extend(response.items)
    elif framework.database:
        # Use framework database directly (all tasks share the same database)
        thread_service = ThreadService(
            database=framework.database,
            idempotency_store=FileIdempotencyStore(database=framework.database),
            execution_engine=framework.execution_engine,
        )
        response = await thread_service.list_threads(
            filters=filters,
            user_id=auth.user_id,
            app_id=auth.app_id,
            is_admin=auth.key_type == "admin",
        )
        api_requests_total.labels(method="GET", endpoint="/threads", status="200").inc()
        return response
    
    # Sort by created_at descending and apply limit
    all_threads.sort(key=lambda t: t.created_at, reverse=True)
    limited_threads = all_threads[:limit] if limit else all_threads
    
    api_requests_total.labels(method="GET", endpoint="/threads", status="200").inc()
    return ThreadListResponse(
        items=limited_threads,
        pagination=Pagination(
            cursor=None,
            has_more=len(all_threads) > len(limited_threads),
            total=len(all_threads),
        ),
    )


# Register /threads/{thread_id}/artifacts endpoint BEFORE /{thread_id} route
# This ensures FastAPI matches the more specific route first
# Import here to ensure artifacts module is loaded and endpoint is registered
from task_framework.api import artifacts  # noqa: F401


@router.get("/{thread_id}", response_model=Thread)
async def get_thread(
    thread_id: str,
    task_id: Optional[str] = Query(None, description="Task identifier (optional, helps locate thread faster)"),
    version: Optional[str] = Query(None, description="Task version (optional)"),
    auth: AuthenticatedRequest = Depends(get_authenticated_request),
    framework: Any = Depends(get_framework),
) -> Thread:
    """Get thread by ID.
    
    In multi-task mode, if task_id/version are not provided, searches across all task databases.
    
    Args:
        thread_id: Thread identifier
        task_id: Optional task identifier to narrow search
        version: Optional task version
        auth: Authenticated request context
        framework: TaskFramework instance
        
    Returns:
        Thread instance
        
    Raises:
        HTTPException: 404 if thread not found or not accessible
    """
    thread = None
    
    # If task_id is provided, search in that specific task's database
    if task_id:
        task_def = framework.get_task(task_id, version)
        if task_def:
            database = get_task_database(task_def, framework) 
            thread_service = ThreadService(
                database=database,
                idempotency_store=FileIdempotencyStore(database=database),
                execution_engine=framework.execution_engine,
            )
            thread = await thread_service.get_thread(
                thread_id=thread_id,
                user_id=auth.user_id,
                app_id=auth.app_id,
                is_admin=auth.key_type == "admin",
            )
    
    # If not found, search across all task databases
    if not thread:
        for task_def in framework.task_registry.list_all():
            database = get_task_database(task_def, framework)
            if database:
                thread_service = ThreadService(
                    database=database,
                    idempotency_store=FileIdempotencyStore(database=database),
                    execution_engine=framework.execution_engine,
                )
                thread = await thread_service.get_thread(
                    thread_id=thread_id,
                    user_id=auth.user_id,
                    app_id=auth.app_id,
                    is_admin=auth.key_type == "admin",
                )
                if thread:
                    break
        
        # Also check the shared framework database (for threads from deleted tasks
        # or threads created before task-specific databases were introduced)
        if not thread and framework.database:
            thread_service = ThreadService(
                database=framework.database,
                idempotency_store=FileIdempotencyStore(database=framework.database),
                execution_engine=framework.execution_engine,
            )
            thread = await thread_service.get_thread(
                thread_id=thread_id,
                user_id=auth.user_id,
                app_id=auth.app_id,
                is_admin=auth.key_type == "admin",
            )

    if not thread:
        api_requests_total.labels(method="GET", endpoint=f"/threads/{thread_id}", status="404").inc()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=problem_json_dict(
                status_code=status.HTTP_404_NOT_FOUND,
                title="Not Found",
                detail=f"Thread {thread_id} not found",
                code=THREAD_NOT_FOUND,
            ),
        )

    api_requests_total.labels(method="GET", endpoint=f"/threads/{thread_id}", status="200").inc()
    return thread


@router.post("/{thread_id}:stop", response_model=Thread, status_code=status.HTTP_202_ACCEPTED)
async def stop_thread(
    thread_id: str,
    task_id: Optional[str] = Query(None, description="Task identifier (optional, helps locate thread faster)"),
    version: Optional[str] = Query(None, description="Task version (optional)"),
    auth: AuthenticatedRequest = Depends(get_authenticated_request),
    framework: Any = Depends(get_framework),
) -> Thread:
    """Stop a running thread.
    
    In multi-task mode, if task_id/version are not provided, searches across all task databases.
    
    Args:
        thread_id: Thread identifier
        task_id: Optional task identifier to narrow search
        version: Optional task version
        auth: Authenticated request context
        framework: TaskFramework instance
        
    Returns:
        Updated Thread instance
        
    Raises:
        HTTPException: 404 if thread not found, 400 if invalid state
    """
    # Find the thread service that contains this thread
    thread_service = None
    thread = None
    
    # If task_id is provided, search in that specific task's database
    if task_id:
        task_def = framework.get_task(task_id, version)
        if task_def:
            database = get_task_database(task_def, framework) 
            thread_service = ThreadService(
                database=database,
                idempotency_store=FileIdempotencyStore(database=database),
                execution_engine=framework.execution_engine,
            )
            thread = await thread_service.get_thread(
                thread_id=thread_id,
                user_id=auth.user_id,
                app_id=auth.app_id,
                is_admin=auth.key_type == "admin",
            )
    
    # If not found, search across all task databases
    if not thread:
        for task_def in framework.task_registry.list_all():
            database = get_task_database(task_def, framework)
            if database:
                ts = ThreadService(
                    database=database,
                    idempotency_store=FileIdempotencyStore(database=database),
                    execution_engine=framework.execution_engine,
                )
                thread = await ts.get_thread(
                    thread_id=thread_id,
                    user_id=auth.user_id,
                    app_id=auth.app_id,
                    is_admin=auth.key_type == "admin",
                )
                if thread:
                    thread_service = ts
                    break
        
        # Also check the shared framework database (for threads from deleted tasks)
        if not thread and framework.database:
            thread_service = ThreadService(
                database=framework.database,
                idempotency_store=FileIdempotencyStore(database=framework.database),
                execution_engine=framework.execution_engine,
            )
            thread = await thread_service.get_thread(
                thread_id=thread_id,
                user_id=auth.user_id,
                app_id=auth.app_id,
                is_admin=auth.key_type == "admin",
            )
    
    if not thread or not thread_service:
        api_requests_total.labels(method="POST", endpoint=f"/threads/{thread_id}:stop", status="404").inc()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=problem_json_dict(
                status_code=status.HTTP_404_NOT_FOUND,
                title="Not Found",
                detail=f"Thread {thread_id} not found",
                code=THREAD_NOT_FOUND,
            ),
        )
    
    try:
        thread = await thread_service.stop_thread(
            thread_id=thread_id,
            user_id=auth.user_id,
            app_id=auth.app_id,
            is_admin=auth.key_type == "admin",
        )

        # Log thread stop
        logger.info(
            "thread.stopped",
            thread_id=thread_id,
            stopped_by_user_id=auth.user_id,
            stopped_by_app_id=auth.app_id,
            state=str(thread.state),
        )

        api_requests_total.labels(method="POST", endpoint=f"/threads/{thread_id}:stop", status="202").inc()
        return thread
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            api_requests_total.labels(method="POST", endpoint=f"/threads/{thread_id}:stop", status="404").inc()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=problem_json_dict(
                    status_code=status.HTTP_404_NOT_FOUND,
                    title="Not Found",
                    detail=error_msg,
                    code=THREAD_NOT_FOUND,
                ),
            )
        else:
            api_requests_total.labels(method="POST", endpoint=f"/threads/{thread_id}:stop", status="400").inc()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=problem_json_dict(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    title="Bad Request",
                    detail=error_msg,
                    code=THREAD_INVALID_STATE,
                ),
            )


@router.post("/{thread_id}:retry", response_model=Thread, status_code=status.HTTP_201_CREATED)
async def retry_thread(
    thread_id: str,
    request: ThreadRetryRequest,
    task_id: Optional[str] = Query(None, description="Task identifier (optional, helps locate thread faster)"),
    version: Optional[str] = Query(None, description="Task version (optional)"),
    auth: AuthenticatedRequest = Depends(get_authenticated_request),
    framework: Any = Depends(get_framework),
) -> Thread:
    """Retry a failed thread.
    
    In multi-task mode, if task_id/version are not provided, searches across all task databases.
    
    Args:
        thread_id: Original thread identifier
        request: Retry request options
        task_id: Optional task identifier to narrow search
        version: Optional task version
        auth: Authenticated request context
        framework: TaskFramework instance
        
    Returns:
        New Thread instance (new attempt)
        
    Raises:
        HTTPException: 404 if thread not found, 400 if invalid state
    """
    # Find the thread service and task definition that contains this thread
    thread_service = None
    thread = None
    task_def = None
    
    # If task_id is provided, search in that specific task's database
    if task_id:
        task_def = framework.get_task(task_id, version)
        if task_def:
            database = get_task_database(task_def, framework) 
            thread_service = ThreadService(
                database=database,
                idempotency_store=FileIdempotencyStore(database=database),
                execution_engine=framework.execution_engine,
            )
            thread = await thread_service.get_thread(
                thread_id=thread_id,
                user_id=auth.user_id,
                app_id=auth.app_id,
                is_admin=auth.key_type == "admin",
            )
    
    # If not found, search across all task databases
    if not thread:
        for td in framework.task_registry.list_all():
            database = get_task_database(td, framework)
            if database:
                ts = ThreadService(
                    database=database,
                    idempotency_store=FileIdempotencyStore(database=database),
                    execution_engine=framework.execution_engine,
                )
                thread = await ts.get_thread(
                    thread_id=thread_id,
                    user_id=auth.user_id,
                    app_id=auth.app_id,
                    is_admin=auth.key_type == "admin",
                )
                if thread:
                    thread_service = ts
                    task_def = td
                    break
        
        # Also check the shared framework database (for threads from deleted tasks)
        if not thread and framework.database:
            thread_service = ThreadService(
                database=framework.database,
                idempotency_store=FileIdempotencyStore(database=framework.database),
                execution_engine=framework.execution_engine,
            )
            thread = await thread_service.get_thread(
                thread_id=thread_id,
                user_id=auth.user_id,
                app_id=auth.app_id,
                is_admin=auth.key_type == "admin",
            )
    
    if not thread or not thread_service:
        api_requests_total.labels(method="POST", endpoint=f"/threads/{thread_id}:retry", status="404").inc()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=problem_json_dict(
                status_code=status.HTTP_404_NOT_FOUND,
                title="Not Found",
                detail=f"Thread {thread_id} not found",
                code=THREAD_NOT_FOUND,
            ),
        )
    
    # Get task function from task definition (multi-task) or framework (single-task)
    task_function = await get_task_function(task_def, framework)
    
    if not task_function:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=problem_json_dict(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                title="Service Unavailable",
                detail="Task function not registered",
            ),
        )

    try:
        thread = await thread_service.retry_thread(
            thread_id=thread_id,
            request=request,
            user_id=auth.user_id,
            app_id=auth.app_id,
            is_admin=auth.key_type == "admin",
            task_function=task_function,
            task_definition=task_def,
        )

        # Log thread retry
        logger.info(
            "thread.retried",
            original_thread_id=thread_id,
            new_thread_id=thread.id,
            retried_by_user_id=auth.user_id,
            retried_by_app_id=auth.app_id,
            attempt=thread.attempt,
            task_id=task_def.task_id if task_def else None,
            task_version=task_def.version if task_def else None,
        )

        api_requests_total.labels(method="POST", endpoint=f"/threads/{thread_id}:retry", status="201").inc()
        return thread
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            api_requests_total.labels(method="POST", endpoint=f"/threads/{thread_id}:retry", status="404").inc()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=problem_json_dict(
                    status_code=status.HTTP_404_NOT_FOUND,
                    title="Not Found",
                    detail=error_msg,
                    code=THREAD_NOT_FOUND,
                ),
            )
        else:
            api_requests_total.labels(method="POST", endpoint=f"/threads/{thread_id}:retry", status="400").inc()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=problem_json_dict(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    title="Bad Request",
                    detail=error_msg,
                    code=THREAD_INVALID_STATE,
                ),
            )

