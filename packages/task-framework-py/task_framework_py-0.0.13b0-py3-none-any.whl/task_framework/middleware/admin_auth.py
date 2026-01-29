"""Admin authentication dependency for proxy admin endpoints."""

from typing import Optional

from fastapi import Depends, Header, HTTPException, Request, status

from task_framework.dependencies import get_framework
from task_framework.errors import AUTH_INVALID, AUTH_REQUIRED, problem_json_dict
from task_framework.framework import TaskFramework


async def get_admin_authenticated_request(
    request: Request,
    x_admin_api_key: Optional[str] = Header(None, alias="X-Admin-API-Key"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    framework: TaskFramework = Depends(get_framework),
) -> str:
    """Authenticate admin request and return admin API key.

    This FastAPI dependency validates admin API keys. It accepts either:
    - X-Admin-API-Key header (preferred)
    - X-API-Key header if the value matches an admin key

    Args:
        request: FastAPI request object
        x_admin_api_key: Admin API key from X-Admin-API-Key header
        x_api_key: API key from X-API-Key header (fallback)
        framework: TaskFramework instance (dependency injection)

    Returns:
        Verified admin API key string

    Raises:
        HTTPException: 401 if admin API key missing/invalid (Problem+JSON format)
    """
    # Try X-Admin-API-Key first
    api_key = x_admin_api_key
    
    # Fallback to X-API-Key if X-Admin-API-Key not provided
    if not api_key:
        api_key = x_api_key
    
    # Validate API key is present
    if not api_key:
        from task_framework.logging import logger
        from task_framework.metrics import api_requests_total

        logger.info("admin_auth.failed", reason="missing_key", endpoint=str(request.url.path))
        problem = problem_json_dict(
            status_code=status.HTTP_401_UNAUTHORIZED,
            title="Unauthorized",
            detail="Missing admin API key",
            code=AUTH_REQUIRED,
        )
        api_requests_total.labels(
            method=request.method,
            endpoint=str(request.url.path),
            status="401",
        ).inc()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=problem,
        )
    
    # Validate API key is an admin key
    if api_key not in framework.admin_api_keys:
        from task_framework.logging import logger
        from task_framework.metrics import api_requests_total

        logger.info("admin_auth.failed", reason="invalid_key", endpoint=str(request.url.path))
        problem = problem_json_dict(
            status_code=status.HTTP_401_UNAUTHORIZED,
            title="Unauthorized",
            detail="Invalid admin API key",
            code=AUTH_INVALID,
        )
        api_requests_total.labels(
            method=request.method,
            endpoint=str(request.url.path),
            status="401",
        ).inc()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=problem,
        )
    
    # Log successful authentication
    from task_framework.logging import logger

    logger.info("admin_auth.succeeded", endpoint=str(request.url.path))
    
    return api_key

