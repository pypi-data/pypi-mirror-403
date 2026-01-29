import time
from datetime import UTC, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from task_framework.dependencies import get_framework
from task_framework.errors import problem_json_dict
from task_framework.logging import logger
from task_framework.metrics import metadata_requests_total, metadata_response_duration_seconds

router = APIRouter(tags=["metadata"])


@router.get("/task/metadata")
async def get_task_metadata(
    task_id: Optional[str] = Query(None, description="Task ID (required if multiple tasks)"),
    version: Optional[str] = Query(None, description="Task version (optional, defaults to latest)"),
    framework: Any = Depends(get_framework),
) -> dict[str, Any]:
    """Return runtime-discoverable metadata about a registered task.

    This endpoint is intentionally unauthenticated and intended for service
    discovery and monitoring use-cases.
    
    If only one task is registered, task_id is optional.
    If multiple tasks are registered, task_id is required.
    """
    start_time = time.time()
    
    # Get framework version
    try:
        import task_framework
        framework_version = getattr(task_framework, "__version__", "0.1.0")
    except Exception:
        framework_version = "0.1.0"

    try:
        # If multiple tasks registered, task_id is required
        if not task_id and framework.task_registry.count_tasks() > 1:
            metadata_requests_total.labels(status="400").inc()
            metadata_response_duration_seconds.observe(time.time() - start_time)
            timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
            logger.error(
                "metadata.extraction_failed",
                error="task_id required when multiple tasks registered",
                timestamp=timestamp,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=problem_json_dict(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    title="Bad Request",
                    detail="task_id parameter is required when multiple tasks are registered",
                ),
            )
        
        # Get the task definition
        task_def = framework.get_task(task_id, version)
        if not task_def:
            metadata_requests_total.labels(status="404").inc()
            metadata_response_duration_seconds.observe(time.time() - start_time)
            timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
            logger.error(
                "metadata.extraction_failed",
                error=f"Task not found: {task_id}:{version or 'latest'}",
                timestamp=timestamp,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=problem_json_dict(
                    status_code=status.HTTP_404_NOT_FOUND,
                    title="Not Found",
                    detail=f"Task {task_id or 'default'}:{version or 'latest'} not found",
                ),
            )
        
        # Get metadata from task definition
        task_fn = task_def.get_task_function()
        name = task_def.name
        description = task_def.description or ""
        
        # Get schemas from task definition
        input_schemas = task_def.input_schemas or []
        output_schemas = task_def.output_schemas or []
        
        timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        task_version = task_def.version

        response = {
            "name": name,
            "version": task_version,
            "description": description,
            "timestamp": timestamp,
            "framework_version": framework_version,
            "sdk_version": task_def.sdk_version,
            "api_version": getattr(framework, "api_version", "1"),
            "input_schemas": input_schemas,
            "output_schemas": output_schemas,
        }

        logger.info("metadata.requested", timestamp=timestamp, name=name)
        metadata_requests_total.labels(status="200").inc()
        metadata_response_duration_seconds.observe(time.time() - start_time)

        # Add Cache-Control header
        return JSONResponse(
            content=response,
            headers={"Cache-Control": "public, max-age=300"},
        )
    except HTTPException:
        # Re-raise HTTP exceptions (like 503)
        raise
    except Exception as e:
        # Handle unexpected errors during metadata extraction
        metadata_requests_total.labels(status="500").inc()
        metadata_response_duration_seconds.observe(time.time() - start_time)
        timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        logger.error(
            "metadata.extraction_failed",
            error=str(e),
            timestamp=timestamp,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=problem_json_dict(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                title="Internal Server Error",
                detail="Failed to extract task metadata",
            ),
        )


