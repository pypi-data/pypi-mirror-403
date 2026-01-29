"""Admin API endpoints for managing task definitions."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from pydantic import BaseModel, Field

from task_framework.dependencies import get_framework
from task_framework.errors import problem_json_dict
from task_framework.logging import logger
from task_framework.middleware.admin_auth import get_admin_authenticated_request
from task_framework.models.task_definition import DeploymentRecord, TaskDefinition

router = APIRouter(prefix="/admin/tasks", tags=["admin-tasks"])


async def ensure_registry_synced(framework: Any) -> None:
    """Ensure task registry is loaded from file if modified.
    
    This ensures the current worker has the latest task registry
    before serving API responses. Registry is file-based for consistency.
    
    Args:
        framework: TaskFramework instance
    """
    await framework.task_registry.ensure_loaded()


# Error codes
TASK_NOT_FOUND = "TASK_NOT_FOUND"
TASK_ALREADY_EXISTS = "TASK_ALREADY_EXISTS"
TASK_DEPLOYMENT_FAILED = "TASK_DEPLOYMENT_FAILED"
INVALID_TASK_PACKAGE = "INVALID_TASK_PACKAGE"


class TaskSummary(BaseModel):
    """Summary information about a registered task."""
    
    task_id: str = Field(..., description="Task identifier")
    name: str = Field(..., description="Task display name")
    description: str = Field(default="", description="Task description")
    versions: List[str] = Field(..., description="Available versions (newest first)")
    latest_version: str = Field(..., description="Latest version")
    total_versions: int = Field(..., description="Total number of versions")
    entry_point: Optional[str] = Field(None, description="Entry point of latest version (module:function)")
    deployed_at: Optional[datetime] = Field(None, description="Deployment timestamp of latest version")
    sdk_version: Optional[str] = Field(None, description="SDK version used to package latest version")


class TaskVersionInfo(BaseModel):
    """Detailed information about a specific task version."""
    
    task_id: str = Field(..., description="Task identifier")
    version: str = Field(..., description="Task version")
    name: str = Field(..., description="Task display name")
    description: str = Field(default="", description="Task description")
    entry_point: str = Field(..., description="Entry point (module:function)")
    deployed_at: Optional[datetime] = Field(None, description="Deployment timestamp")
    zip_path: Optional[str] = Field(None, description="Original zip file path")
    base_path: str = Field(..., description="Task installation directory")
    input_schemas: List[Dict[str, Any]] = Field(default_factory=list, description="Input schemas")
    output_schemas: List[Dict[str, Any]] = Field(default_factory=list, description="Output schemas")
    sdk_version: Optional[str] = Field(None, description="SDK version used to package this task")


class TaskListResponse(BaseModel):
    """Response for listing all registered tasks."""
    
    tasks: List[TaskSummary] = Field(..., description="List of task summaries")
    total: int = Field(..., description="Total number of unique tasks")
    total_versions: int = Field(..., description="Total number of task versions")


class TaskDeploymentResponse(BaseModel):
    """Response for task deployment."""
    
    task_id: str = Field(..., description="Deployed task identifier")
    version: str = Field(..., description="Deployed task version")
    was_new: bool = Field(..., description="True if newly deployed, False if already existed")
    message: str = Field(..., description="Deployment status message")


class TaskUndeployResponse(BaseModel):
    """Response for task undeployment."""
    
    undeployed: List[str] = Field(..., description="List of undeployed task:version identifiers")
    message: str = Field(..., description="Undeploy status message")


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_task(
    file: UploadFile = File(..., description="Task definition zip file"),
    force: bool = Query(False, description="Force redeploy even if already deployed"),
    admin_key: str = Depends(get_admin_authenticated_request),
    framework: Any = Depends(get_framework),
) -> TaskDeploymentResponse:
    """Upload and deploy a task definition zip file.
    
    The zip file is saved to the task_definitions directory and then deployed.
    This ensures the task will be auto-discovered on server restart.
    
    Args:
        file: The task definition zip file
        force: If True, redeploy even if already deployed
        admin_key: Verified admin API key
        framework: TaskFramework instance
        
    Returns:
        TaskDeploymentResponse with deployment details
        
    Raises:
        HTTPException: If upload or deployment fails
    """
    # Validate file extension
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=problem_json_dict(
                status_code=status.HTTP_400_BAD_REQUEST,
                title="Bad Request",
                detail="File must be a .zip file",
                code=INVALID_TASK_PACKAGE,
            ),
        )
    
    try:
        # Read file content
        content = await file.read()
        
        # Save to task_definitions directory
        zip_path = await framework.task_storage.save_zip_file(file.filename, content)
        
        logger.info(
            "admin_tasks.upload_received",
            filename=file.filename,
            size=len(content),
            zip_path=str(zip_path),
        )
        
        # Deploy the task
        from task_framework.services.task_deployment import TaskDeploymentError
        
        try:
            task_def, was_new = await framework.task_deployment_service.deploy_from_zip(
                str(zip_path),
                force=force,
            )
            
            if was_new:
                message = f"Task {task_def.task_id}:{task_def.version} deployed successfully"
            else:
                message = f"Task {task_def.task_id}:{task_def.version} already deployed (skipped)"
            
            return TaskDeploymentResponse(
                task_id=task_def.task_id,
                version=task_def.version,
                was_new=was_new,
                message=message,
            )
            
        except TaskDeploymentError as e:
            # Deployment failed
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=problem_json_dict(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    title="Deployment Failed",
                    detail=str(e),
                    code=TASK_DEPLOYMENT_FAILED,
                ),
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "admin_tasks.upload_failed",
            filename=file.filename,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=problem_json_dict(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                title="Internal Server Error",
                detail=f"Upload failed: {str(e)}",
            ),
        )


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    admin_key: str = Depends(get_admin_authenticated_request),
    framework: Any = Depends(get_framework),
) -> TaskListResponse:
    """List all registered tasks.
    
    Args:
        admin_key: Verified admin API key
        framework: TaskFramework instance
        
    Returns:
        TaskListResponse with all registered tasks
    """
    # Ensure registry is synced before reading
    await ensure_registry_synced(framework)
    
    task_ids = framework.task_registry.list_tasks()
    
    tasks = []
    total_versions = 0
    
    for task_id in task_ids:
        versions = framework.task_registry.get_versions(task_id)
        latest = framework.task_registry.get_latest_version(task_id)
        
        if latest:
            tasks.append(TaskSummary(
                task_id=task_id,
                name=latest.name,
                description=latest.description,
                versions=versions,
                latest_version=latest.version,
                total_versions=len(versions),
                entry_point=latest.entry_point,
                deployed_at=latest.deployed_at,
                sdk_version=latest.sdk_version,
            ))
            total_versions += len(versions)
    
    return TaskListResponse(
        tasks=tasks,
        total=len(tasks),
        total_versions=total_versions,
    )


@router.get("/{task_id}")
async def get_task(
    task_id: str,
    admin_key: str = Depends(get_admin_authenticated_request),
    framework: Any = Depends(get_framework),
) -> TaskSummary:
    """Get details for a specific task.
    
    Args:
        task_id: Task identifier
        admin_key: Verified admin API key
        framework: TaskFramework instance
        
    Returns:
        TaskSummary with task details
        
    Raises:
        HTTPException: If task not found
    """
    # Ensure registry is synced before reading
    await ensure_registry_synced(framework)
    
    if not framework.task_registry.is_registered(task_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=problem_json_dict(
                status_code=status.HTTP_404_NOT_FOUND,
                title="Not Found",
                detail=f"Task '{task_id}' not found",
                code=TASK_NOT_FOUND,
            ),
        )
    
    versions = framework.task_registry.get_versions(task_id)
    latest = framework.task_registry.get_latest_version(task_id)
    
    return TaskSummary(
        task_id=task_id,
        name=latest.name if latest else task_id,
        description=latest.description if latest else "",
        versions=versions,
        latest_version=latest.version if latest else "",
        total_versions=len(versions),
        entry_point=latest.entry_point if latest else None,
        deployed_at=latest.deployed_at if latest else None,
        sdk_version=latest.sdk_version if latest else None,
    )


@router.get("/{task_id}/versions")
async def list_task_versions(
    task_id: str,
    admin_key: str = Depends(get_admin_authenticated_request),
    framework: Any = Depends(get_framework),
) -> List[TaskVersionInfo]:
    """List all versions of a specific task.
    
    Args:
        task_id: Task identifier
        admin_key: Verified admin API key
        framework: TaskFramework instance
        
    Returns:
        List of TaskVersionInfo for all versions
        
    Raises:
        HTTPException: If task not found
    """
    # Ensure registry is synced before reading
    await ensure_registry_synced(framework)
    
    if not framework.task_registry.is_registered(task_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=problem_json_dict(
                status_code=status.HTTP_404_NOT_FOUND,
                title="Not Found",
                detail=f"Task '{task_id}' not found",
                code=TASK_NOT_FOUND,
            ),
        )
    
    task_defs = framework.task_registry.list_by_task(task_id)
    
    return [
        TaskVersionInfo(
            task_id=td.task_id,
            version=td.version,
            name=td.name,
            description=td.description,
            entry_point=td.entry_point,
            deployed_at=td.deployed_at,
            zip_path=td.zip_path,
            base_path=td.base_path,
            input_schemas=td.input_schemas,
            output_schemas=td.output_schemas,
            sdk_version=td.sdk_version,
        )
        for td in task_defs
    ]


@router.get("/{task_id}/versions/{version}")
async def get_task_version(
    task_id: str,
    version: str,
    admin_key: str = Depends(get_admin_authenticated_request),
    framework: Any = Depends(get_framework),
) -> TaskVersionInfo:
    """Get details for a specific task version.
    
    Args:
        task_id: Task identifier
        version: Task version
        admin_key: Verified admin API key
        framework: TaskFramework instance
        
    Returns:
        TaskVersionInfo with version details
        
    Raises:
        HTTPException: If task version not found
    """
    # Ensure registry is synced before reading
    await ensure_registry_synced(framework)
    
    task_def = framework.task_registry.get(task_id, version)
    
    if not task_def:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=problem_json_dict(
                status_code=status.HTTP_404_NOT_FOUND,
                title="Not Found",
                detail=f"Task '{task_id}' version '{version}' not found",
                code=TASK_NOT_FOUND,
            ),
        )
    
    return TaskVersionInfo(
        task_id=task_def.task_id,
        version=task_def.version,
        name=task_def.name,
        description=task_def.description,
        entry_point=task_def.entry_point,
        deployed_at=task_def.deployed_at,
        zip_path=task_def.zip_path,
        base_path=task_def.base_path,
        input_schemas=task_def.input_schemas,
        output_schemas=task_def.output_schemas,
        sdk_version=task_def.sdk_version,
    )


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    admin_key: str = Depends(get_admin_authenticated_request),
    framework: Any = Depends(get_framework),
) -> TaskUndeployResponse:
    """Delete a task (all versions).
    
    Args:
        task_id: Task identifier
        admin_key: Verified admin API key
        framework: TaskFramework instance
        
    Returns:
        TaskUndeployResponse with undeployed versions
        
    Raises:
        HTTPException: If task not found
    """
    # Ensure registry is synced before checking/deleting
    await ensure_registry_synced(framework)
    
    if not framework.task_registry.is_registered(task_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=problem_json_dict(
                status_code=status.HTTP_404_NOT_FOUND,
                title="Not Found",
                detail=f"Task '{task_id}' not found",
                code=TASK_NOT_FOUND,
            ),
        )
    
    undeployed = await framework.undeploy_task(task_id)
    
    return TaskUndeployResponse(
        undeployed=undeployed,
        message=f"Undeployed {len(undeployed)} version(s) of task '{task_id}'",
    )


@router.delete("/{task_id}/versions/{version}")
async def delete_task_version(
    task_id: str,
    version: str,
    admin_key: str = Depends(get_admin_authenticated_request),
    framework: Any = Depends(get_framework),
) -> TaskUndeployResponse:
    """Delete a specific task version.
    
    Args:
        task_id: Task identifier
        version: Task version
        admin_key: Verified admin API key
        framework: TaskFramework instance
        
    Returns:
        TaskUndeployResponse with undeployed version
        
    Raises:
        HTTPException: If task version not found
    """
    # Ensure registry is synced before checking/deleting
    await ensure_registry_synced(framework)
    
    if not framework.task_registry.is_registered(task_id, version):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=problem_json_dict(
                status_code=status.HTTP_404_NOT_FOUND,
                title="Not Found",
                detail=f"Task '{task_id}' version '{version}' not found",
                code=TASK_NOT_FOUND,
            ),
        )
    
    undeployed = await framework.undeploy_task(task_id, version)
    
    return TaskUndeployResponse(
        undeployed=undeployed,
        message=f"Undeployed task '{task_id}' version '{version}'",
    )


@router.get("/deployments/history")
async def get_deployment_history(
    admin_key: str = Depends(get_admin_authenticated_request),
    framework: Any = Depends(get_framework),
) -> List[DeploymentRecord]:
    """Get deployment history.
    
    Args:
        admin_key: Verified admin API key
        framework: TaskFramework instance
        
    Returns:
        List of all DeploymentRecord objects
    """
    return await framework.deployment_tracker.list_all()


@router.get("/{task_id}/versions/{version}/download")
async def download_task_version(
    task_id: str,
    version: str,
    admin_key: str = Depends(get_admin_authenticated_request),
    framework: Any = Depends(get_framework),
):
    """Download a specific task version as a zip file.
    
    Args:
        task_id: Task identifier
        version: Task version
        admin_key: Verified admin API key
        framework: TaskFramework instance
        
    Returns:
        Zip file as binary download
        
    Raises:
        HTTPException: If task version not found or zip file missing
    """
    from fastapi.responses import Response
    
    # Ensure registry is synced before checking
    await ensure_registry_synced(framework)
    
    # Check if task version exists
    if not framework.task_registry.is_registered(task_id, version):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=problem_json_dict(
                status_code=status.HTTP_404_NOT_FOUND,
                title="Not Found",
                detail=f"Task '{task_id}' version '{version}' not found",
                code=TASK_NOT_FOUND,
            ),
        )
    
    # Get the zip file content
    result = await framework.task_storage.get_zip_file(task_id, version)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=problem_json_dict(
                status_code=status.HTTP_404_NOT_FOUND,
                title="Not Found",
                detail=f"Zip file for task '{task_id}' version '{version}' not found",
                code=TASK_NOT_FOUND,
            ),
        )
    
    content, filename = result
    
    logger.info(
        "admin_tasks.download_task_version",
        task_id=task_id,
        version=version,
        filename=filename,
        size=len(content),
    )
    
    return Response(
        content=content,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get("/{task_id}/download")
async def download_task_latest(
    task_id: str,
    admin_key: str = Depends(get_admin_authenticated_request),
    framework: Any = Depends(get_framework),
):
    """Download the latest version of a task as a zip file.
    
    Args:
        task_id: Task identifier
        admin_key: Verified admin API key
        framework: TaskFramework instance
        
    Returns:
        Zip file as binary download
        
    Raises:
        HTTPException: If task not found or zip file missing
    """
    from fastapi.responses import Response
    
    # Ensure registry is synced before checking
    await ensure_registry_synced(framework)
    
    # Get the latest version
    latest = framework.task_registry.get_latest_version(task_id)
    
    if not latest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=problem_json_dict(
                status_code=status.HTTP_404_NOT_FOUND,
                title="Not Found",
                detail=f"Task '{task_id}' not found",
                code=TASK_NOT_FOUND,
            ),
        )
    
    # Get the zip file content
    result = await framework.task_storage.get_zip_file(task_id, latest.version)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=problem_json_dict(
                status_code=status.HTTP_404_NOT_FOUND,
                title="Not Found",
                detail=f"Zip file for task '{task_id}' version '{latest.version}' not found",
                code=TASK_NOT_FOUND,
            ),
        )
    
    content, filename = result
    
    logger.info(
        "admin_tasks.download_task_latest",
        task_id=task_id,
        version=latest.version,
        filename=filename,
        size=len(content),
    )
    
    return Response(
        content=content,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
