"""Problem+JSON error format handler (RFC 7807) for HTTP error responses."""

from typing import Any, Dict, Optional

from fastapi import Request, status
from fastapi.responses import JSONResponse

# Error codes for authentication
AUTH_REQUIRED = "AUTH_REQUIRED"
AUTH_INVALID = "AUTH_INVALID"
METADATA_REQUIRED = "METADATA_REQUIRED"

# Error codes for thread management
THREAD_NOT_FOUND = "THREAD_NOT_FOUND"
THREAD_INVALID_STATE = "THREAD_INVALID_STATE"
IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
VALIDATION_FAILED = "VALIDATION_FAILED"

# Error codes for artifact management
ARTIFACT_NOT_FOUND = "ARTIFACT_NOT_FOUND"
ARTIFACT_INVALID_TYPE = "ARTIFACT_INVALID_TYPE"
ARTIFACT_VALIDATION_FAILED = "ARTIFACT_VALIDATION_FAILED"
ARTIFACT_REF_CONFLICT = "ARTIFACT_REF_CONFLICT"
ARTIFACT_DELETE_FAILED = "ARTIFACT_DELETE_FAILED"
ARTIFACT_DOWNLOAD_NOT_SUPPORTED = "ARTIFACT_DOWNLOAD_NOT_SUPPORTED"

# Error codes for file storage
FILE_NOT_FOUND = "FILE_NOT_FOUND"
FILE_UPLOAD_EXPIRED = "FILE_UPLOAD_EXPIRED"
FILE_DOWNLOAD_EXPIRED = "FILE_DOWNLOAD_EXPIRED"
FILE_STORAGE_ERROR = "FILE_STORAGE_ERROR"
FILE_SIZE_EXCEEDED = "FILE_SIZE_EXCEEDED"

# Error codes for schedule management
SCHEDULE_NOT_FOUND = "SCHEDULE_NOT_FOUND"
SCHEDULE_INVALID_CRON = "SCHEDULE_INVALID_CRON"
SCHEDULE_INVALID_TIMEZONE = "SCHEDULE_INVALID_TIMEZONE"
RUN_NOT_FOUND = "RUN_NOT_FOUND"
RUN_ALREADY_EXISTS = "RUN_ALREADY_EXISTS"

# Error codes for webhook management
WEBHOOK_NOT_FOUND = "WEBHOOK_NOT_FOUND"
WEBHOOK_INVALID_URL = "WEBHOOK_INVALID_URL"

# Error codes for proxy management
BAD_REQUEST = "BAD_REQUEST"
ROUTING_REQUIRED = "ROUTING_REQUIRED"
SERVER_NOT_FOUND = "SERVER_NOT_FOUND"
SERVER_ALREADY_EXISTS = "SERVER_ALREADY_EXISTS"
UPSTREAM_ERROR = "UPSTREAM_ERROR"
UPSTREAM_TIMEOUT = "UPSTREAM_TIMEOUT"


def problem_json_dict(
    status_code: int,
    title: str,
    detail: Optional[str] = None,
    type: Optional[str] = None,
    instance: Optional[str] = None,
    **extensions: Any,
) -> Dict[str, Any]:
    """Create a Problem+JSON dictionary (RFC 7807).
    
    This helper function returns the problem dict that can be used
    both for JSONResponse creation and HTTPException detail.
    
    Args:
        status_code: HTTP status code
        title: Short, human-readable summary of the problem type
        detail: Human-readable explanation specific to this occurrence
        type: URI reference that identifies the problem type
        instance: URI reference that identifies the specific occurrence
        **extensions: Additional problem members
        
    Returns:
        Problem dict with Problem+JSON format
    """
    problem: Dict[str, Any] = {
        "type": type or f"https://httpstatus.es/{status_code}",
        "title": title,
        "status": status_code,
    }

    if detail:
        problem["detail"] = detail

    if instance:
        problem["instance"] = instance

    # Add extensions
    problem.update(extensions)
    
    return problem


def problem_json_response(
    status_code: int,
    title: str,
    detail: Optional[str] = None,
    type: Optional[str] = None,
    instance: Optional[str] = None,
    **extensions: Any,
) -> JSONResponse:
    """Create a Problem+JSON response (RFC 7807).

    Args:
        status_code: HTTP status code
        title: Short, human-readable summary of the problem type
        detail: Human-readable explanation specific to this occurrence
        type: URI reference that identifies the problem type
        instance: URI reference that identifies the specific occurrence
        **extensions: Additional problem members

    Returns:
        JSONResponse with Problem+JSON format
    """
    problem = problem_json_dict(
        status_code=status_code,
        title=title,
        detail=detail,
        type=type,
        instance=instance,
        **extensions,
    )

    return JSONResponse(status_code=status_code, content=problem)


async def problem_json_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Exception handler that returns Problem+JSON format."""
    status_code = getattr(exc, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR)
    title = getattr(exc, "title", "Internal Server Error")
    detail = str(exc) if exc else None

    instance = str(request.url) if hasattr(request, "url") else request.path if hasattr(request, "path") else "/unknown"

    return problem_json_response(
        status_code=status_code,
        title=title,
        detail=detail,
        instance=instance,
    )

