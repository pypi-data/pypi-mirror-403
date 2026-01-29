"""File storage API endpoints for upload, download, and metadata operations."""

import time
from datetime import UTC, datetime, timedelta
from typing import Any, Optional
from urllib.parse import quote
import os
import json

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, UploadFile, status, Request
from fastapi.responses import Response
from fastapi.responses import JSONResponse

from task_framework.dependencies import AuthenticatedRequest, get_authenticated_request, get_framework
from task_framework.errors import FILE_NOT_FOUND, FILE_SIZE_EXCEEDED, FILE_STORAGE_ERROR, problem_json_dict
from task_framework.interfaces.storage import FileStorage
from task_framework.logging import logger
from task_framework.metrics import file_download_duration_seconds, file_downloads_total, file_upload_duration_seconds, file_uploads_total
from task_framework.models.file_upload import CreateUploadRequest, FileUploadResponse, UploadUrlResponse
from task_framework.services.file_service import FileService, generate_file_ref, infer_media_type, normalize_expiration_time

router = APIRouter(prefix="/files", tags=["files"])

# Router for /uploads endpoint (separate prefix)
uploads_router = APIRouter(prefix="/uploads", tags=["files"])

# Maximum file size: 5GB (in bytes)
MAX_FILE_SIZE = 5 * 1024 * 1024 * 1024


def get_file_service(framework: Any = Depends(get_framework)) -> FileService:
    """Get FileService instance with dependencies.
    
    Args:
        framework: TaskFramework instance
        
    Returns:
        FileService instance
        
    Raises:
        HTTPException: If file storage is not configured
    """
    file_storage = framework.file_storage
    if file_storage is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="File storage backend is not configured",
        )
    return FileService(storage=file_storage)


def get_file_metadata_store(framework: Any = Depends(get_framework)) -> Optional[Any]:
    """Get file metadata store from framework.
    
    Returns ElasticsearchFileMetadataStore when STORAGE_TYPE=elasticsearch,
    None otherwise.
    """
    return framework.file_metadata_store


@uploads_router.post("", status_code=status.HTTP_201_CREATED)
async def create_upload_url(
    request: CreateUploadRequest,
    auth: AuthenticatedRequest = Depends(get_authenticated_request),
    file_service: FileService = Depends(get_file_service),
) -> UploadUrlResponse:
    """Create a pre-signed upload URL for uploading a file.
    
    Args:
        request: Upload request with filename, media_type, size, expires_in
        auth: Authenticated request context
        file_service: FileService instance
        
    Returns:
        UploadUrlResponse with file_ref, upload_url, expires_at, method, headers
        
    Raises:
        HTTPException: On validation or storage backend errors
    """
    # Generate file_ref
    file_ref = generate_file_ref()
    
    # Handle expiration time (default 3600s, configurable, 0 for permanent)
    expires_in, expires_at = normalize_expiration_time(
        expires_in=request.expires_in,
        default_seconds=3600,
    )
    
    # Start timing for duration measurement
    start_time = time.time()
    
    # Log upload started event
    logger.info(
        "file.upload.started",
        file_ref=file_ref,
        size=request.size,
        media_type=request.media_type,
        upload_type="pre_signed_url",
    )
    
    try:
        # Store preliminary metadata (filename, media_type, size) before actual upload
        # This ensures the filename is available when the file is later uploaded and downloaded
        if request.filename:
            # For local storage, we need to write metadata file directly
            # since we don't have the file content yet
            storage = file_service.storage
            if hasattr(storage, '_get_metadata_path'):  # LocalFileStorage
                from pathlib import Path
                import aiofiles
                import json
                from datetime import datetime, timezone
                
                # Ensure directories exist
                if hasattr(storage, '_ensure_directories'):
                    await storage._ensure_directories()
                
                metadata_path = storage._get_metadata_path(file_ref)
                preliminary_metadata = {
                    "filename": request.filename,
                    "media_type": request.media_type,
                    "size": request.size,
                    "created_at": datetime.now(timezone.utc).isoformat() + "Z",
                }
                async with aiofiles.open(metadata_path, "w") as f:
                    await f.write(json.dumps(preliminary_metadata, indent=2))
        
        # Generate upload URL via storage backend
        upload_url = await file_service.generate_upload_url(file_ref=file_ref, expires_in=expires_in)
        
        # Calculate duration
        duration_seconds = time.time() - start_time
        duration_ms = int(duration_seconds * 1000)
        
        # Increment metrics
        file_uploads_total.inc()
        file_upload_duration_seconds.observe(duration_seconds)
        
        # Log upload completed event
        logger.info(
            "file.upload.completed",
            file_ref=file_ref,
            size=request.size,
            sha256=None,  # SHA256 computed after actual upload to pre-signed URL
            duration_ms=duration_ms,
            upload_type="pre_signed_url",
        )
        
        return UploadUrlResponse(
            file_ref=file_ref,
            upload_url=upload_url,
            expires_at=expires_at,
            method="PUT",
            headers={},
        )
    except Exception as e:
        # Map storage backend errors to framework errors
        logger.error(
            "file.upload.failed",
            file_ref=file_ref,
            error=str(e),
            upload_type="pre_signed_url",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=problem_json_dict(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                title="Storage Backend Error",
                detail=f"Storage backend error: {str(e)}",
                code=FILE_STORAGE_ERROR,
            ),
        )


@router.post("", status_code=status.HTTP_200_OK)
async def upload_file_direct(
    file: UploadFile = File(..., description="File content to upload"),
    filename: Optional[str] = Form(None, description="Original filename (optional)"),
    media_type: Optional[str] = Form(None, description="MIME type (optional, inferred if not provided)"),
    auth: AuthenticatedRequest = Depends(get_authenticated_request),
    file_service: FileService = Depends(get_file_service),
    metadata_store: Optional[Any] = Depends(get_file_metadata_store),
) -> FileUploadResponse:
    """Upload a file directly in a single request.
    
    Args:
        file: File content from multipart/form-data
        filename: Original filename (optional, extracted from file field if not provided)
        media_type: MIME type (optional, inferred from Content-Type or filename if not provided)
        auth: Authenticated request context
        file_service: FileService instance
        metadata_store: ES file metadata store (optional, ES-only)
        
    Returns:
        FileUploadResponse with file_ref, size, media_type, sha256, created_at
        
    Raises:
        HTTPException: On validation or storage backend errors
    """
    # Extract filename from file if not provided
    if not filename and file.filename:
        filename = file.filename
    
    # Extract media type from file Content-Type or infer
    if not media_type:
        if file.content_type:
            media_type = infer_media_type(content_type=file.content_type, filename=filename)
        else:
            media_type = infer_media_type(filename=filename)
    
    # Read file content
    file_content = await file.read()
    file_size = len(file_content)
    
    # Validate file size (max 5GB)
    if file_size > MAX_FILE_SIZE:
        logger.error(
            "file.upload.failed",
            error=f"File size {file_size} exceeds maximum {MAX_FILE_SIZE}",
            upload_type="direct",
        )
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=problem_json_dict(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                title="File Size Exceeded",
                detail=f"File size exceeds maximum allowed size of 5GB",
                code=FILE_SIZE_EXCEEDED,
            ),
        )
    
    # Generate file_ref
    file_ref = generate_file_ref()
    
    # Start timing for duration measurement
    start_time = time.time()
    
    # Log upload started event
    logger.info(
        "file.upload.started",
        file_ref=file_ref,
        size=file_size,
        media_type=media_type,
        upload_type="direct",
    )
    
    try:
        # Upload file via service
        metadata = await file_service.upload_file_direct(
            file_ref=file_ref,
            data=file_content,
            filename=filename,
            media_type=media_type,
        )
        
        # Save metadata to ES if available
        if metadata_store:
            await metadata_store.save(
                file_ref=file_ref,
                filename=filename,
                media_type=media_type,
                size=file_size,
                sha256=metadata.get("sha256"),
                created_by=auth.user_id or auth.app_id,
            )
        
        # Calculate duration
        duration_seconds = time.time() - start_time
        duration_ms = int(duration_seconds * 1000)
        
        # Increment metrics
        file_uploads_total.inc()
        file_upload_duration_seconds.observe(duration_seconds)
        
        # Log upload completed event
        logger.info(
            "file.upload.completed",
            file_ref=file_ref,
            size=file_size,
            sha256=metadata.get("sha256"),
            duration_ms=duration_ms,
            upload_type="direct",
        )
        
        return FileUploadResponse(
            file_ref=file_ref,
            size=file_size,
            media_type=media_type,
            sha256=metadata.get("sha256"),
            created_at=datetime.now(UTC),
        )
    except Exception as e:
        # Map storage backend errors to framework errors
        logger.error(
            "file.upload.failed",
            file_ref=file_ref,
            error=str(e),
            upload_type="direct",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=problem_json_dict(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                title="Storage Backend Error",
                detail=f"Storage backend error: {str(e)}",
                code=FILE_STORAGE_ERROR,
            ),
        )


@router.put("/{file_ref}", status_code=status.HTTP_200_OK)
async def upload_via_presigned(
    file_ref: str,
    request: Request,
    auth: AuthenticatedRequest = Depends(get_authenticated_request),
    file_service: FileService = Depends(get_file_service),
    metadata_store: Optional[Any] = Depends(get_file_metadata_store),
) -> FileUploadResponse:
    """Upload a file via a presigned PUT URL (two-step upload).

    This endpoint allows clients to PUT raw bytes to `/files/{file_ref}` when they
    have obtained a pre-signed `upload_url` from POST `/uploads`.
    """
    logger.info("file.upload.presigned.requested", file_ref=file_ref)
    try:
        # Read entire body (uploads are expected to be reasonably sized for examples)
        data = await request.body()
        content_type = request.headers.get("Content-Type")

        # Try to get preliminary metadata (filename) if it was stored during presigned URL creation
        existing_filename = None
        try:
            existing_metadata = await file_service.get_file_metadata(file_ref=file_ref)
            existing_filename = existing_metadata.get("filename")
        except Exception:
            # Metadata doesn't exist yet, which is fine
            pass

        metadata = await file_service.upload_file_direct(
            file_ref=file_ref,
            data=data,
            filename=existing_filename,  # Use preliminary filename if available
            media_type=content_type,
        )

        # Save metadata to ES if available
        if metadata_store:
            await metadata_store.save(
                file_ref=file_ref,
                filename=existing_filename or metadata.get("filename"),
                media_type=metadata.get("media_type"),
                size=metadata.get("size"),
                sha256=metadata.get("sha256"),
                created_by=auth.user_id or auth.app_id,
            )

        response = FileUploadResponse(
            file_ref=file_ref,
            size=metadata.get("size"),
            media_type=metadata.get("media_type"),
            sha256=metadata.get("sha256"),
            created_at=datetime.now(UTC),
        )

        logger.info("file.upload.presigned.completed", file_ref=file_ref, size=metadata.get("size"))
        return response
    except Exception as e:
        logger.error("file.upload.presigned.failed", file_ref=file_ref, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=problem_json_dict(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                title="Storage Backend Error",
                detail=f"Storage backend error: {str(e)}",
                code=FILE_STORAGE_ERROR,
            ),
        )


@router.get("", response_class=JSONResponse)
async def list_files(
    auth: AuthenticatedRequest = Depends(get_authenticated_request),
    file_service: FileService = Depends(get_file_service),
    metadata_store: Optional[Any] = Depends(get_file_metadata_store),
) -> JSONResponse:
    """List files stored in the storage backend (metadata)."""
    items = []

    # Use ES metadata store if available (preferred)
    if metadata_store:
        try:
            items = await metadata_store.list_all(limit=100)
            total = await metadata_store.count()
            return JSONResponse({"items": items, "total": total})
        except Exception as e:
            logger.warning("file.list.es_failed", error=str(e))
            # Fall through to local fallback
    
    # Fallback: If the storage exposes a metadata directory (LocalFileStorage), read JSON metadata files
    storage = file_service.storage
    if hasattr(storage, "metadata_dir"):
        metadata_dir = getattr(storage, "metadata_dir")
        try:
            for entry in os.listdir(str(metadata_dir)):
                if not entry.endswith(".json"):
                    continue
                path = metadata_dir / entry
                try:
                    with open(path, "r") as f:
                        data = json.load(f)
                        file_ref = entry[:-5]  # strip .json
                        data["file_ref"] = file_ref
                        items.append(data)
                except Exception:
                    # skip invalid metadata files
                    continue
        except FileNotFoundError:
            # No metadata directory present
            items = []

    # Sort files by created_at DESC (newest first)
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    return JSONResponse({"items": items, "total": len(items)})


@router.get("/{file_ref}", status_code=status.HTTP_200_OK)
async def download_file(
    file_ref: str,
    expires_in: Optional[int] = Query(None, description="Expiration time in seconds (default: 900). Use 0 for permanent/no expiration."),
    range_header: Optional[str] = Header(None, alias="Range"),
    auth: AuthenticatedRequest = Depends(get_authenticated_request),
    file_service: FileService = Depends(get_file_service),
) -> Response:
    """Download a file by streaming it directly with proper headers.
    
    Args:
        file_ref: File reference identifier
        expires_in: Expiration time in seconds (default: 900, not used for direct streaming)
        range_header: HTTP Range header for partial downloads (optional)
        auth: Authenticated request context
        file_service: FileService instance
        
    Returns:
        Response with file content and proper Content-Disposition header
        
    Raises:
        HTTPException: On file not found or storage backend errors
    """
    # Log download requested event
    logger.info("file.download.requested", file_ref=file_ref)
    
    # Start timing for duration measurement
    start_time = time.time()
    
    # Check file exists and get metadata
    try:
        file_exists = await file_service.check_file_exists(file_ref=file_ref)
        if not file_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=problem_json_dict(
                    status_code=status.HTTP_404_NOT_FOUND,
                    title="File Not Found",
                    detail=f"File {file_ref} does not exist",
                    code=FILE_NOT_FOUND,
                ),
            )
        
        # Get file metadata
        metadata = await file_service.get_file_metadata(file_ref=file_ref)
        content_type = metadata.get("media_type", "application/octet-stream")
        content_length = metadata.get("size")
        filename = metadata.get("filename", file_ref)
        
    except HTTPException:
        raise
    except Exception as e:
        # Map storage backend errors to framework errors
        logger.error("file.download.failed", file_ref=file_ref, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=problem_json_dict(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                title="Storage Backend Error",
                detail=f"Storage backend error: {str(e)}",
                code=FILE_STORAGE_ERROR,
            ),
        )
    
    try:
        # Download file content from storage
        file_content = await file_service.storage.download(file_ref=file_ref)
        
        # Calculate duration
        duration_seconds = time.time() - start_time
        
        # Increment metrics
        file_downloads_total.inc()
        file_download_duration_seconds.observe(duration_seconds)
        
        # Build Content-Disposition header with filename
        # RFC 6266: filename should be ASCII, use filename* for UTF-8 if needed
        ascii_filename = filename.encode('ascii', 'ignore').decode('ascii')
        content_disposition = f'attachment; filename="{ascii_filename}"'
        # Also add UTF-8 filename for better browser support
        content_disposition += f"; filename*=UTF-8''{quote(filename)}"
        
        # Create response with file content
        response = Response(
            content=file_content,
            status_code=status.HTTP_200_OK,
            media_type=content_type,
        )
        response.headers["Content-Disposition"] = content_disposition
        if content_length:
            response.headers["Content-Length"] = str(content_length)
        
        # Log successful download
        logger.info("file.download.completed", file_ref=file_ref, size=content_length)
        
        return response
        
    except Exception as e:
        # Map storage backend errors to framework errors
        logger.error("file.download.failed", file_ref=file_ref, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=problem_json_dict(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                title="Storage Backend Error",
                detail=f"Storage backend error: {str(e)}",
                code=FILE_STORAGE_ERROR,
            ),
        )


@router.head("/{file_ref}", status_code=status.HTTP_200_OK)
async def inspect_file_metadata(
    file_ref: str,
    auth: AuthenticatedRequest = Depends(get_authenticated_request),
    file_service: FileService = Depends(get_file_service),
) -> Response:
    """Inspect file metadata without downloading the file.
    
    Args:
        file_ref: File reference identifier
        auth: Authenticated request context
        file_service: FileService instance
        
    Returns:
        Response with headers: Content-Length, Content-Type, ETag/SHA256
        
    Raises:
        HTTPException: On file not found or storage backend errors
    """
    # Check file exists
    try:
        file_exists = await file_service.check_file_exists(file_ref=file_ref)
        if not file_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=problem_json_dict(
                    status_code=status.HTTP_404_NOT_FOUND,
                    title="File Not Found",
                    detail=f"File {file_ref} does not exist",
                    code=FILE_NOT_FOUND,
                ),
            )
    except HTTPException:
        raise
    except Exception as e:
        # Map storage backend errors to framework errors
        logger.error("file.metadata.failed", file_ref=file_ref, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=problem_json_dict(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                title="Storage Backend Error",
                detail=f"Storage backend error: {str(e)}",
                code=FILE_STORAGE_ERROR,
            ),
        )
    
    try:
        # Get file metadata
        metadata = await file_service.get_file_metadata(file_ref=file_ref)
        
        # Create response with metadata headers
        response = Response(status_code=status.HTTP_200_OK)
        
        # Set Content-Length header
        if "size" in metadata:
            response.headers["Content-Length"] = str(metadata["size"])
        
        # Set Content-Type header
        if "media_type" in metadata:
            response.headers["Content-Type"] = metadata["media_type"]
        
        # Set ETag header (SHA256 hash)
        if "sha256" in metadata and metadata["sha256"]:
            response.headers["ETag"] = f'"{metadata["sha256"]}"'
        
        # Set Content-Disposition header with filename (for metadata inspection)
        filename = metadata.get("filename", file_ref)
        ascii_filename = filename.encode('ascii', 'ignore').decode('ascii')
        content_disposition = f'attachment; filename="{ascii_filename}"'
        content_disposition += f"; filename*=UTF-8''{quote(filename)}"
        response.headers["Content-Disposition"] = content_disposition
        
        return response
    except Exception as e:
        # Map storage backend errors to framework errors
        logger.error("file.metadata.failed", file_ref=file_ref, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=problem_json_dict(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                title="Storage Backend Error",
                detail=f"Storage backend error: {str(e)}",
                code=FILE_STORAGE_ERROR,
            ),
        )

