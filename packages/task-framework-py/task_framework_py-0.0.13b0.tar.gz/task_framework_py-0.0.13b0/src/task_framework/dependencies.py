"""FastAPI dependency injection for authentication and framework access."""

from typing import Literal, Optional, Tuple

from fastapi import Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict, Field, field_validator

from task_framework.errors import AUTH_INVALID, AUTH_REQUIRED, METADATA_REQUIRED, problem_json_dict
from task_framework.framework import TaskFramework
from task_framework.models.task_definition import TaskDefinition

# Global framework instance (set during server creation)
_framework_instance: Optional[TaskFramework] = None


def set_framework_instance(framework: TaskFramework) -> None:
    """Set the global framework instance for dependency injection.

    Args:
        framework: TaskFramework instance to use for dependency injection
    """
    global _framework_instance
    _framework_instance = framework


def get_framework() -> TaskFramework:
    """Get TaskFramework instance for dependency injection.

    Returns:
        TaskFramework instance

    Raises:
        RuntimeError: If framework instance is not set
    """
    if _framework_instance is None:
        raise RuntimeError("Framework instance not set. Call set_framework_instance() first.")
    return _framework_instance


class AuthenticatedRequest(BaseModel):
    """Request context after successful authentication, containing key type and metadata."""

    api_key: str = Field(..., description="The verified API key value")
    key_type: Literal["regular", "admin"] = Field(..., description="Key type: regular or admin")
    user_id: Optional[str] = Field(None, description="User identifier (required for regular keys)")
    app_id: Optional[str] = Field(None, description="Application identifier (required for regular keys)")

    model_config = ConfigDict(frozen=True)

    @field_validator("user_id", "app_id", mode="before")
    @classmethod
    def validate_metadata(cls, v: Optional[str], info) -> Optional[str]:
        """Validate metadata fields based on key type."""
        if v == "":
            return None
        return v

    def model_post_init(self, __context: Optional[object]) -> None:
        """Validate that regular keys have required metadata."""
        if self.key_type == "regular":
            if not self.user_id:
                raise ValueError("user_id is required for regular API keys")
            if not self.app_id:
                raise ValueError("app_id is required for regular API keys")


async def get_authenticated_request(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    framework: TaskFramework = Depends(get_framework),
) -> AuthenticatedRequest:
    """Authenticate request and return AuthenticatedRequest context.

    This FastAPI dependency validates the API key and extracts metadata from the request.
    It implements the authentication flow:
    1. Validate API key header
    2. Check key type (admin first, then regular)
    3. Extract metadata (query params first, then headers)
    4. Validate metadata for regular keys
    5. Return AuthenticatedRequest

    Args:
        request: FastAPI request object (for accessing query params and headers)
        x_api_key: API key from X-API-Key header
        framework: TaskFramework instance (dependency injection)

    Returns:
        AuthenticatedRequest with api_key, key_type, user_id, app_id

    Raises:
        HTTPException: 401 if API key missing/invalid, 400 if metadata missing for regular key
    """
    # Step 1: Validate API key header
    if not x_api_key:
        from task_framework.logging import logger
        from task_framework.metrics import api_requests_total

        logger.info("auth.failed", reason="missing_key", endpoint=str(request.url.path))
        problem = problem_json_dict(
            status_code=status.HTTP_401_UNAUTHORIZED,
            title="Unauthorized",
            detail="Missing API key",
            code=AUTH_REQUIRED,
        )
        # Increment metrics for auth failure
        api_requests_total.labels(
            method=request.method,
            endpoint=str(request.url.path),
            status="401",
        ).inc()
        # FastAPI HTTPException accepts dict for detail
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=problem,
        )

    # Step 2: Check key type (admin first, then regular)
    key_type: Literal["regular", "admin"]
    if x_api_key in framework.admin_api_keys:
        key_type = "admin"
    elif x_api_key in framework.api_keys:
        key_type = "regular"
    else:
        from task_framework.logging import logger
        from task_framework.metrics import api_requests_total

        logger.info("auth.failed", reason="invalid_key", endpoint=str(request.url.path))
        problem = problem_json_dict(
            status_code=status.HTTP_401_UNAUTHORIZED,
            title="Unauthorized",
            detail="Invalid API key",
            code=AUTH_INVALID,
        )
        # Increment metrics for auth failure
        api_requests_total.labels(
            method=request.method,
            endpoint=str(request.url.path),
            status="401",
        ).inc()
        # FastAPI HTTPException accepts dict for detail
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=problem,
        )

    # Step 3: Extract metadata (query params first, then headers)
    user_id: Optional[str] = request.query_params.get("user_id")
    app_id: Optional[str] = request.query_params.get("app_id")

    # Fallback to headers if not in query params
    if not user_id:
        user_id = request.headers.get("X-User-Id")
    if not app_id:
        app_id = request.headers.get("X-App-Id")

    # Step 4: Validate metadata for regular keys
    if key_type == "regular":
        if not user_id or not app_id:
            from task_framework.logging import logger
            from task_framework.metrics import api_requests_total

            logger.info("auth.failed", reason="missing_metadata", endpoint=str(request.url.path))
            problem = problem_json_dict(
                status_code=status.HTTP_400_BAD_REQUEST,
                title="Bad Request",
                detail="Missing required metadata (user_id or app_id) for regular API key",
                code=METADATA_REQUIRED,
            )
            # Increment metrics for bad request
            api_requests_total.labels(
                method=request.method,
                endpoint=str(request.url.path),
                status="400",
            ).inc()
            # FastAPI HTTPException accepts dict for detail
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=problem,
            )

    # Step 5: Create and return AuthenticatedRequest
    auth_request = AuthenticatedRequest(
        api_key=x_api_key,
        key_type=key_type,
        user_id=user_id,
        app_id=app_id,
    )

    # Log successful authentication
    from task_framework.logging import logger

    logger.info("auth.succeeded", key_type=key_type, endpoint=str(request.url.path))

    # Increment metrics
    from task_framework.metrics import api_requests_total

    api_requests_total.labels(
        method=request.method,
        endpoint=str(request.url.path),
        status="200",
    ).inc()

    return auth_request


# Error codes for task resolution
TASK_NOT_FOUND = "TASK_NOT_FOUND"
TASK_ID_REQUIRED = "TASK_ID_REQUIRED"


class TaskContext(BaseModel):
    """Context for task-specific operations with resolved TaskDefinition."""
    
    task_definition: Optional[TaskDefinition] = Field(None, description="Resolved task definition")
    task_id: Optional[str] = Field(None, description="Task identifier from query params")
    version: Optional[str] = Field(None, description="Task version from query params")
    
    model_config = ConfigDict(arbitrary_types_allowed=True)


async def get_task_context(
    request: Request,
    task_id: Optional[str] = Query(None, description="Task identifier"),
    version: Optional[str] = Query(None, description="Task version (defaults to latest)"),
    task_version: Optional[str] = Query(None, description="Task version (alias for version)"),
    framework: TaskFramework = Depends(get_framework),
) -> TaskContext:
    """Resolve task from query parameters.
    
    Resolves the TaskDefinition based on task_id and version.
    
    Args:
        request: FastAPI request object
        task_id: Optional task identifier from query params
        version: Optional task version from query params
        task_version: Optional task version (alias for version, for backward compatibility)
        framework: TaskFramework instance
        
    Returns:
        TaskContext with resolved task definition
        
    Raises:
        HTTPException: If task not found or task_id required but not provided
    """
    # Use task_version if version is not provided (for backward compatibility)
    resolved_version = version or task_version
    
    # If multiple tasks registered, task_id is required
    if framework.task_registry.count_tasks() > 1 and not task_id:
        from task_framework.logging import logger
        
        logger.info("task_resolution.failed", reason="task_id_required", endpoint=str(request.url.path))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=problem_json_dict(
                status_code=status.HTTP_400_BAD_REQUEST,
                title="Bad Request",
                detail="task_id query parameter is required when multiple tasks are registered",
                code=TASK_ID_REQUIRED,
            ),
        )
    
    # Try to resolve task
    task_def = framework.get_task(task_id, resolved_version)
    
    # If task_id was explicitly provided but task not found, error
    if task_id and not task_def:
        from task_framework.logging import logger
        
        version_msg = f" version '{resolved_version}'" if resolved_version else ""
        logger.info("task_resolution.failed", reason="not_found", task_id=task_id, version=resolved_version)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=problem_json_dict(
                status_code=status.HTTP_404_NOT_FOUND,
                title="Not Found",
                detail=f"Task '{task_id}'{version_msg} not found",
                code=TASK_NOT_FOUND,
            ),
        )
    
    return TaskContext(
        task_definition=task_def,
        task_id=task_id,
        version=resolved_version,
    )


async def require_task(
    task_context: TaskContext = Depends(get_task_context),
) -> TaskDefinition:
    """Require a resolved task definition.
    
    This dependency wraps get_task_context and ensures a task is resolved.
    Use this for endpoints that require a task to operate.
    
    Args:
        task_context: Resolved TaskContext from get_task_context
        
    Returns:
        TaskDefinition (guaranteed to be non-None)
        
    Raises:
        HTTPException: If no task could be resolved
    """
    if task_context.task_definition is None:
        # In single-task mode with a registered task function, this shouldn't happen
        # but we handle it for robustness
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=problem_json_dict(
                status_code=status.HTTP_400_BAD_REQUEST,
                title="Bad Request",
                detail="No task could be resolved. Ensure task_id is provided or a task is registered.",
                code=TASK_NOT_FOUND,
            ),
        )
    
    return task_context.task_definition


def get_task_database(task_def: Optional[TaskDefinition], framework: TaskFramework):
    """Get the database for a task.
    
    Always returns the framework-level database since artifacts, threads,
    webhooks, and schedules should be stored at the framework level,
    not isolated per-task.
    
    Args:
        task_def: TaskDefinition if in multi-task mode (ignored)
        framework: TaskFramework instance
        
    Returns:
        Database instance at framework level
    """
    # Always use framework database - artifacts, threads, webhooks, schedules
    # are stored at framework level, not per-task
    return framework.database


def get_task_file_storage(task_def: Optional[TaskDefinition], framework: TaskFramework):
    """Get the file storage for a task.
    
    Always returns the framework-level file storage since all files
    should be stored at the framework level, not per-task.
    
    Args:
        task_def: TaskDefinition if in multi-task mode (ignored)
        framework: TaskFramework instance
        
    Returns:
        FileStorage instance at framework level
    """
    # Always use framework file storage
    return framework.file_storage


async def get_task_function(task_def: Optional[TaskDefinition], framework: TaskFramework):
    """Get the task function (from TaskDefinition).
    
    If task_def is provided but doesn't have a loaded function, attempts to lazy-load it.
    This handles cases where a non-latest version's task function wasn't loaded on startup.
    
    Args:
        task_def: TaskDefinition for the task
        framework: TaskFramework instance
        
    Returns:
        Task function callable or None if not found
    """
    if task_def:
        task_function = task_def.get_task_function()
        if task_function:
            return task_function
        
        # Lazy load: task definition exists but function not loaded
        # This can happen if we're accessing a non-latest version that wasn't fully loaded
        try:
            from task_framework.services.task_loader import TaskLoader
            from pathlib import Path
            import json
            
            # Try to reload the task function
            task_storage = framework.task_storage
            task_loader = TaskLoader(task_storage)
            
            # Get metadata for this task version
            metadata_path = task_storage.get_task_base_path(task_def.task_id, task_def.version) / "metadata.json"
            if metadata_path.exists() and metadata_path.is_file():
                with open(metadata_path, 'r') as f:
                    metadata_dict = json.load(f)
                from task_framework.models.task_definition import TaskMetadata
                metadata = TaskMetadata.model_validate(metadata_dict)
                
                # Reload the task function
                code_path = task_storage.get_code_path(task_def.task_id, task_def.version)
                task_function = await task_loader._load_task_function(str(code_path), metadata.entry_point)
                task_def.set_task_function(task_function)
                return task_function
        except Exception as e:
            from task_framework.logging import logger
            logger.warning(
                "task_function.lazy_load_failed",
                task_id=task_def.task_id,
                version=task_def.version,
                error=str(e),
                exc_info=True,
            )
    
    return None

