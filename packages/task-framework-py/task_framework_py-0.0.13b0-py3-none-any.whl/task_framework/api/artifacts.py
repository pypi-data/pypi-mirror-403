"""Artifact API endpoints.

Provides endpoints for querying, downloading, archiving, and deleting artifacts
produced by task executions. Artifacts are associated with threads and contain
the inputs and outputs of task runs.

In multi-task mode, use the `task_id` and `version` query parameters to specify
which task's artifacts to query. If only one task is registered, these parameters
are optional.
"""

import base64
import json as json_lib
from datetime import datetime
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
)
from task_framework.errors import ARTIFACT_NOT_FOUND, problem_json_dict
from task_framework.logging import logger
from task_framework.models.artifact import Artifact
from task_framework.models.artifact_download_response import ArtifactDownloadResponse
from task_framework.models.artifact_list_response import ArtifactListResponse
from task_framework.models.artifact_query_filters import ArtifactQueryFilters
from task_framework.models.pagination import Pagination
from task_framework.repositories.file_db import FileDatabase
from task_framework.services.artifact_service import ArtifactService

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


def get_artifact_service(
    framework: Any = Depends(get_framework),
) -> ArtifactService:
    """Get ArtifactService instance with dependencies.
    
    Uses framework database and storage to work across all tasks.
    
    Args:
        framework: TaskFramework instance
        
    Returns:
        ArtifactService instance
    """
    # Use framework database and file_storage directly
    database = framework.database 
    file_storage = framework.file_storage
    
    return ArtifactService(database=database, file_storage=file_storage)


# Register /threads/{thread_id}/artifacts endpoint in threads router
from task_framework.api import threads as threads_api
from task_framework.models.artifact_list_response import ArtifactListResponse

@threads_api.router.get("/{thread_id}/artifacts", response_model=ArtifactListResponse)
async def list_thread_artifacts(
    thread_id: str,
    ref: Optional[str] = Query(None, description="Ref filter (supports prefix wildcards with *)"),
    kind: Optional[str] = Query(None, description="Artifact kind filter"),
    media_type: Optional[str] = Query(None, description="Media type filter"),
    direction: Optional[str] = Query(None, description="Direction filter: 'input', 'output', or 'both'"),
    include_archived: bool = Query(default=False, description="Include archived artifacts"),
    limit: Optional[int] = Query(None, description="Maximum number of results"),
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    offset: Optional[int] = Query(None, ge=0, description="Offset for pagination"),
    auth: AuthenticatedRequest = Depends(get_authenticated_request),
    artifact_service: ArtifactService = Depends(get_artifact_service),
):
    """List artifacts for a thread with filtering.
    
    Args:
        thread_id: Thread identifier
        ref: Ref filter (supports prefix wildcards)
        kind: Artifact kind filter
        media_type: Media type filter
        direction: Direction filter
        include_archived: Include archived artifacts
        limit: Maximum number of results
        cursor: Pagination cursor
        offset: Offset for pagination (alternative to cursor)
        auth: Authenticated request context
        artifact_service: ArtifactService instance
        
    Returns:
        ArtifactListResponse with filtered artifacts
    """
    filters = {
        "ref": ref,
        "kind": kind,
        "media_type": media_type,
        "direction": direction,
        "include_archived": include_archived,
        "limit": limit,
        "cursor": cursor,
        "offset": offset,
    }
    
    artifacts = await artifact_service.list_thread_artifacts(thread_id, filters)
    
    # Apply pagination
    has_more = False
    next_cursor = None
    
    # Apply cursor-based pagination
    limit = limit or 50
    
    if cursor:
        # Decode cursor (Base64 JSON with artifact_id and created_at)
        try:
            cursor_data = json_lib.loads(base64.b64decode(cursor).decode())
            cursor_artifact_id = cursor_data.get("artifact_id")
            cursor_created_at = cursor_data.get("created_at")
            
            # Filter artifacts after cursor
            if cursor_created_at:
                cursor_time = datetime.fromisoformat(cursor_created_at.replace("Z", "+00:00"))
                artifacts = [a for a in artifacts if a.created_at and a.created_at < cursor_time]
        except (ValueError, KeyError, TypeError):
            # Invalid cursor, return empty
            artifacts = []
    
    # Offset-based pagination fallback
    elif offset is not None:
        artifacts = artifacts[offset:]
    
    # Apply limit
    has_more = len(artifacts) > limit
    artifacts = artifacts[:limit]
    
    # Generate next cursor if has_more
    if has_more and artifacts:
        last_artifact = artifacts[-1]
        cursor_data = {
            "artifact_id": last_artifact.id,
            "created_at": last_artifact.created_at.isoformat() + "Z" if last_artifact.created_at else None,
        }
        next_cursor = base64.b64encode(json_lib.dumps(cursor_data).encode()).decode()
    
    pagination = Pagination(
        cursor=next_cursor,
        has_more=has_more,
        total=None,
    )
    
    # Log artifact retrieval
    logger.info(
        "artifact.retrieved",
        artifact_id=None,  # Bulk retrieval
        thread_id=thread_id,
        count=len(artifacts),
    )
    
    return ArtifactListResponse(items=artifacts, pagination=pagination)


@router.get("/{artifact_id}", response_model=Artifact)
async def get_artifact(
    artifact_id: str,
    auth: AuthenticatedRequest = Depends(get_authenticated_request),
    artifact_service: ArtifactService = Depends(get_artifact_service),
):
    """Get individual artifact by ID.
    
    Args:
        artifact_id: Artifact identifier
        auth: Authenticated request context
        artifact_service: ArtifactService instance
        
    Returns:
        Artifact instance
        
    Raises:
        HTTPException: 404 if artifact not found or not accessible
    """
    artifact = await artifact_service.get_artifact(artifact_id)
    
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=problem_json_dict(
                status_code=status.HTTP_404_NOT_FOUND,
                title="Artifact Not Found",
                detail=f"Artifact with ID '{artifact_id}' does not exist or is not accessible",
                code=ARTIFACT_NOT_FOUND,
                instance=f"/artifacts/{artifact_id}",
            ),
        )
    
    # Apply access control filtering (unless admin)
    # Note: Artifacts don't have direct user_id/app_id, so we check via thread metadata
    if auth.key_type != "admin":
        if artifact.thread_id:
            # Get thread to check access control
            database = FileDatabase()
            thread = await database.get_thread(artifact.thread_id)
            if thread:
                thread_user_id = thread.metadata.get("user_id")
                thread_app_id = thread.metadata.get("app_id")
                if auth.user_id and thread_user_id != auth.user_id:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=problem_json_dict(
                            status_code=status.HTTP_404_NOT_FOUND,
                            title="Artifact Not Found",
                            detail=f"Artifact with ID '{artifact_id}' does not exist or is not accessible",
                            code=ARTIFACT_NOT_FOUND,
                            instance=f"/artifacts/{artifact_id}",
                        ),
                    )
                if auth.app_id and thread_app_id != auth.app_id:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=problem_json_dict(
                            status_code=status.HTTP_404_NOT_FOUND,
                            title="Artifact Not Found",
                            detail=f"Artifact with ID '{artifact_id}' does not exist or is not accessible",
                            code=ARTIFACT_NOT_FOUND,
                            instance=f"/artifacts/{artifact_id}",
                        ),
                    )
    
    # Log artifact retrieval
    logger.info(
        "artifact.retrieved",
        artifact_id=artifact_id,
        thread_id=artifact.thread_id,
    )
    
    return artifact

@router.get("", response_model=ArtifactListResponse)
async def list_artifacts(
    ref: Optional[str] = Query(None, description="Ref filter (supports prefix wildcards with *)"),
    kind: Optional[str] = Query(None, description="Artifact kind filter"),
    media_type: Optional[str] = Query(None, description="Media type filter"),
    thread_id: Optional[str] = Query(None, description="Filter by thread ID"),
    app_id: Optional[str] = Query(None, description="Filter by app_id"),
    task_id: Optional[str] = Query(None, description="Filter by task definition ID (from thread metadata)"),
    task_version: Optional[str] = Query(None, description="Filter by task version (from thread metadata)"),
    direction: Optional[str] = Query(None, description="Direction filter: 'input', 'output', or 'both' (requires thread_id)"),
    include_archived: bool = Query(default=False, description="Include archived artifacts"),
    limit: Optional[int] = Query(None, description="Maximum number of results"),
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    offset: Optional[int] = Query(None, ge=0, description="Offset for pagination"),
    auth: AuthenticatedRequest = Depends(get_authenticated_request),
    framework: Any = Depends(get_framework),
):
    """Query artifacts across threads with filtering.
    
    In multi-task mode, you can filter by `task_id` and `task_version` to narrow results
    to a specific task definition. Non-admin users can only see artifacts from threads
    they own (matching user_id/app_id).
    
    Args:
        ref: Filter by artifact ref (supports prefix wildcards with `*`, e.g., `result*`)
        kind: Filter by artifact kind (e.g., `json`, `text`, `file`)
        media_type: Filter by MIME type (e.g., `application/json`)
        thread_id: Filter by specific thread ID
        app_id: Filter by application ID (admin only for cross-app queries)
        task_id: Filter by task definition ID (multi-task mode)
        task_version: Filter by task version (multi-task mode)
        direction: Filter by direction (`input`, `output`, or `both`). Requires `thread_id`.
        include_archived: Include archived artifacts (default: false)
        limit: Maximum results per page (default: 50)
        cursor: Cursor for pagination (from previous response)
        offset: Offset-based pagination (alternative to cursor)
        auth: Authenticated request context
        artifact_service: ArtifactService instance
        
    Returns:
        ArtifactListResponse with filtered artifacts and pagination info
    """
    filters = {
        "ref": ref,
        "kind": kind,
        "media_type": media_type,
        "thread_id": thread_id,
        "app_id": app_id if app_id else (auth.app_id if auth.key_type == "regular" else None),
        "task_id": task_id,
        "task_version": task_version,
        "direction": direction,  # Pass direction to database query
        "include_archived": include_archived,
        "limit": limit,
        "cursor": cursor,
        "offset": offset,
    }
    
    # Use database query_artifacts for cross-thread queries.
    # Prefer framework's configured database (so per-task DBs are respected), fall back to default FileDatabase.
    database = framework.database if getattr(framework, "database", None) is not None else FileDatabase()
    artifacts = await database.query_artifacts(filters)
    
    # Enrich artifacts with task_id and task_version from thread metadata
    # Cache thread lookups to avoid repeated queries
    thread_cache = {}
    enriched_artifacts = []
    for artifact in artifacts:
        artifact_dict = artifact.model_dump()
        if artifact.thread_id:
            if artifact.thread_id not in thread_cache:
                thread = await database.get_thread(artifact.thread_id)
                thread_cache[artifact.thread_id] = thread
            thread = thread_cache.get(artifact.thread_id)
            if thread and thread.metadata:
                artifact_dict["task_id"] = thread.metadata.get("task_id")
                artifact_dict["task_version"] = thread.metadata.get("task_version")
        enriched_artifacts.append(Artifact.model_validate(artifact_dict))
    artifacts = enriched_artifacts
    
    # Apply fallback direction filtering for legacy artifacts that don't have direction field
    # This handles artifacts created before direction field was added
    if direction and direction != "both":
        filtered_artifacts = []
        for a in artifacts:
            # If artifact has direction field, use it (already filtered by database)
            if a.direction:
                filtered_artifacts.append(a)
            elif thread_id:
                # Legacy fallback: use timestamp-based logic
                thread = thread_cache.get(thread_id) or await database.get_thread(thread_id)
                if thread:
                    thread_start_time = thread.started_at or thread.created_at
                    if direction == "input" and a.created_at and a.created_at < thread_start_time:
                        filtered_artifacts.append(a)
                    elif direction == "output" and a.created_at and a.created_at >= thread_start_time:
                        filtered_artifacts.append(a)
        artifacts = filtered_artifacts
    
    # Store total count before pagination
    total_count = len(artifacts)
    
    # Apply pagination
    has_more = False
    next_cursor = None
    
    # Apply cursor-based pagination
    limit = limit or 50
    
    if cursor:
        # Decode cursor (Base64 JSON with artifact_id and created_at)
        try:
            cursor_data = json_lib.loads(base64.b64decode(cursor).decode())
            cursor_artifact_id = cursor_data.get("artifact_id")
            cursor_created_at = cursor_data.get("created_at")
            
            # Filter artifacts after cursor
            if cursor_created_at:
                cursor_time = datetime.fromisoformat(cursor_created_at.replace("Z", "+00:00"))
                artifacts = [a for a in artifacts if a.created_at and a.created_at < cursor_time]
        except (ValueError, KeyError, TypeError):
            # Invalid cursor, return empty
            artifacts = []
    
    # Offset-based pagination fallback
    elif offset is not None:
        # Calculate if there are more results after this page
        has_more = (offset + limit) < total_count
        # Slice the artifacts array to get the requested page
        artifacts = artifacts[offset:offset + limit]
    else:
        # No offset, just apply limit from the start
        has_more = len(artifacts) > limit
        artifacts = artifacts[:limit]
    
    # Generate next cursor if has_more (for cursor-based pagination)
    if has_more and artifacts and cursor:
        last_artifact = artifacts[-1]
        cursor_data = {
            "artifact_id": last_artifact.id,
            "created_at": last_artifact.created_at.isoformat() + "Z" if last_artifact.created_at else None,
        }
        next_cursor = base64.b64encode(json_lib.dumps(cursor_data).encode()).decode()
    
    pagination = Pagination(
        cursor=next_cursor,
        has_more=has_more,
        total=total_count,
    )
    
    return ArtifactListResponse(items=artifacts, pagination=pagination)


@router.delete("/{artifact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_artifact(
    artifact_id: str,
    auth: AuthenticatedRequest = Depends(get_authenticated_request),
    artifact_service: ArtifactService = Depends(get_artifact_service),
):
    """Delete an artifact and its associated file.
    
    Args:
        artifact_id: Artifact identifier
        auth: Authenticated request context
        artifact_service: ArtifactService instance
        
    Raises:
        HTTPException: 404 if artifact not found or not accessible
    """
    # Get artifact first to check access control
    artifact = await artifact_service.get_artifact(artifact_id)
    
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=problem_json_dict(
                status_code=status.HTTP_404_NOT_FOUND,
                title="Artifact Not Found",
                detail=f"Artifact with ID '{artifact_id}' does not exist or is not accessible",
                code=ARTIFACT_NOT_FOUND,
                instance=f"/artifacts/{artifact_id}",
            ),
        )
    
    # Apply access control filtering (unless admin)
    if auth.key_type != "admin":
        if artifact.thread_id:
            database = FileDatabase()
            thread = await database.get_thread(artifact.thread_id)
            if thread:
                thread_user_id = thread.metadata.get("user_id")
                thread_app_id = thread.metadata.get("app_id")
                if auth.user_id and thread_user_id != auth.user_id:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=problem_json_dict(
                            status_code=status.HTTP_404_NOT_FOUND,
                            title="Artifact Not Found",
                            detail=f"Artifact with ID '{artifact_id}' does not exist or is not accessible",
                            code=ARTIFACT_NOT_FOUND,
                            instance=f"/artifacts/{artifact_id}",
                        ),
                    )
                if auth.app_id and thread_app_id != auth.app_id:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=problem_json_dict(
                            status_code=status.HTTP_404_NOT_FOUND,
                            title="Artifact Not Found",
                            detail=f"Artifact with ID '{artifact_id}' does not exist or is not accessible",
                            code=ARTIFACT_NOT_FOUND,
                            instance=f"/artifacts/{artifact_id}",
                        ),
                    )
    
    # Delete artifact (file deletion handled in service layer)
    await artifact_service.delete_artifact(artifact_id)
    
    # Log artifact deletion
    logger.info(
        "artifact.deleted",
        artifact_id=artifact_id,
        file_deleted=False,  # Will be updated when file deletion is implemented
        file_deletion_error=None,
    )


@router.post("/{artifact_id}:archive", status_code=status.HTTP_200_OK)
async def archive_artifact(
    artifact_id: str,
    auth: AuthenticatedRequest = Depends(get_authenticated_request),
    artifact_service: ArtifactService = Depends(get_artifact_service),
):
    """Archive an artifact (soft delete).
    
    Args:
        artifact_id: Artifact identifier
        auth: Authenticated request context
        artifact_service: ArtifactService instance
        
    Returns:
        Archived Artifact instance
        
    Raises:
        HTTPException: 404 if artifact not found or not accessible
    """
    # Get artifact first to check access control
    artifact = await artifact_service.get_artifact(artifact_id)
    
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=problem_json_dict(
                status_code=status.HTTP_404_NOT_FOUND,
                title="Artifact Not Found",
                detail=f"Artifact with ID '{artifact_id}' does not exist or is not accessible",
                code=ARTIFACT_NOT_FOUND,
                instance=f"/artifacts/{artifact_id}:archive",
            ),
        )
    
    # Apply access control filtering (unless admin)
    if auth.key_type != "admin":
        if artifact.thread_id:
            database = FileDatabase()
            thread = await database.get_thread(artifact.thread_id)
            if thread:
                thread_user_id = thread.metadata.get("user_id")
                thread_app_id = thread.metadata.get("app_id")
                if auth.user_id and thread_user_id != auth.user_id:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=problem_json_dict(
                            status_code=status.HTTP_404_NOT_FOUND,
                            title="Artifact Not Found",
                            detail=f"Artifact with ID '{artifact_id}' does not exist or is not accessible",
                            code=ARTIFACT_NOT_FOUND,
                            instance=f"/artifacts/{artifact_id}:archive",
                        ),
                    )
                if auth.app_id and thread_app_id != auth.app_id:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=problem_json_dict(
                            status_code=status.HTTP_404_NOT_FOUND,
                            title="Artifact Not Found",
                            detail=f"Artifact with ID '{artifact_id}' does not exist or is not accessible",
                            code=ARTIFACT_NOT_FOUND,
                            instance=f"/artifacts/{artifact_id}:archive",
                        ),
                    )
    
    # Archive artifact
    archived_artifact = await artifact_service.archive_artifact(artifact_id)
    
    # Log artifact archiving
    logger.info(
        "artifact.archived",
        artifact_id=artifact_id,
    )
    
    return archived_artifact


@router.get("/{artifact_id}/download", response_model=ArtifactDownloadResponse)
async def get_download_url(
    artifact_id: str,
    expires_in: int = Query(default=900, description="URL expiration time in seconds (default: 900)"),
    auth: AuthenticatedRequest = Depends(get_authenticated_request),
    artifact_service: ArtifactService = Depends(get_artifact_service),
):
    """Get pre-signed download URL for artifact file.
    
    Args:
        artifact_id: Artifact identifier
        expires_in: URL expiration time in seconds (default: 900)
        auth: Authenticated request context
        artifact_service: ArtifactService instance
        
    Returns:
        Download URL response
        
    Raises:
        HTTPException: 404 if artifact not found, 400 if artifact doesn't support download
    """
    # Get artifact first to check access control and validate file_ref
    artifact = await artifact_service.get_artifact(artifact_id)
    
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=problem_json_dict(
                status_code=status.HTTP_404_NOT_FOUND,
                title="Artifact Not Found",
                detail=f"Artifact with ID '{artifact_id}' does not exist or is not accessible",
                code=ARTIFACT_NOT_FOUND,
                instance=f"/artifacts/{artifact_id}/download",
            ),
        )
    
    # Apply access control filtering (unless admin)
    if auth.key_type != "admin":
        if artifact.thread_id:
            database = FileDatabase()
            thread = await database.get_thread(artifact.thread_id)
            if thread:
                thread_user_id = thread.metadata.get("user_id")
                thread_app_id = thread.metadata.get("app_id")
                if auth.user_id and thread_user_id != auth.user_id:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=problem_json_dict(
                            status_code=status.HTTP_404_NOT_FOUND,
                            title="Artifact Not Found",
                            detail=f"Artifact with ID '{artifact_id}' does not exist or is not accessible",
                            code=ARTIFACT_NOT_FOUND,
                            instance=f"/artifacts/{artifact_id}/download",
                        ),
                    )
                if auth.app_id and thread_app_id != auth.app_id:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=problem_json_dict(
                            status_code=status.HTTP_404_NOT_FOUND,
                            title="Artifact Not Found",
                            detail=f"Artifact with ID '{artifact_id}' does not exist or is not accessible",
                            code=ARTIFACT_NOT_FOUND,
                            instance=f"/artifacts/{artifact_id}/download",
                        ),
                    )
    
    # Validate that artifact has file_ref
    if not artifact.file_ref:
        from task_framework.errors import ARTIFACT_DOWNLOAD_NOT_SUPPORTED
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=problem_json_dict(
                status_code=status.HTTP_400_BAD_REQUEST,
                title="Bad Request",
                detail=f"Artifact '{artifact_id}' does not have a file reference. Only file artifacts support download URLs.",
                code=ARTIFACT_DOWNLOAD_NOT_SUPPORTED,
                instance=f"/artifacts/{artifact_id}/download",
            ),
        )
    
    # Get download URL
    download_url_data = await artifact_service.get_download_url(artifact_id, expires_in)
    
    # Log download URL generation
    logger.info(
        "artifact.download_url.generated",
        artifact_id=artifact_id,
        expires_in=expires_in,
    )
    
    return ArtifactDownloadResponse(**download_url_data)

