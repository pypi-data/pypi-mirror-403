"""Admin API endpoints for managing enrolled task servers."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status

from task_framework.errors import SERVER_ALREADY_EXISTS, SERVER_NOT_FOUND, problem_json_dict
from task_framework.middleware.admin_auth import get_admin_authenticated_request
from task_framework.proxy_registry import EnrollmentRequest, ServerEntry, ServiceRegistry

router = APIRouter(prefix="/admin/servers", tags=["proxy-admin"])


def get_registry(request: Request) -> ServiceRegistry:
    """Dependency to get ServiceRegistry instance from app state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        ServiceRegistry instance
    """
    return request.app.state.registry


@router.post("", status_code=status.HTTP_201_CREATED)
async def enroll_server(
    enrollment: EnrollmentRequest,
    request: Request,
    admin_key: str = Depends(get_admin_authenticated_request),
    registry: ServiceRegistry = Depends(get_registry),
) -> ServerEntry:
    """Enroll a new task server.

    Args:
        enrollment: Enrollment request with server details
        request: FastAPI request object
        admin_key: Verified admin API key
        registry: ServiceRegistry instance

    Returns:
        Created ServerEntry

    Raises:
        HTTPException: If enrollment fails (conflict, validation error)
    """
    # Check if server already exists
    existing = registry.get_server(enrollment.id)
    if existing:
        problem = problem_json_dict(
            status_code=status.HTTP_409_CONFLICT,
            title="Conflict",
            detail=f"Server '{enrollment.id}' is already enrolled",
            code=SERVER_ALREADY_EXISTS,
            instance=str(request.url),
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=problem)
    
    # Create ServerEntry from EnrollmentRequest
    server = ServerEntry(
        id=enrollment.id,
        base_url=enrollment.base_url,
        task_types=enrollment.task_types,
        name=enrollment.name,
        metadata=enrollment.metadata or {},
        weight=enrollment.weight,
        max_concurrent=enrollment.max_concurrent,
        status="unknown",
    )
    
    # Add to registry
    registry.add_server(server)
    
    from task_framework.logging import logger
    logger.info("proxy.admin.server_enrolled", server_id=enrollment.id, task_types=enrollment.task_types)
    
    return server


@router.get("")
async def list_servers(
    request: Request,
    admin_key: str = Depends(get_admin_authenticated_request),
    registry: ServiceRegistry = Depends(get_registry),
) -> List[ServerEntry]:
    """List all enrolled servers.

    Args:
        request: FastAPI request object
        admin_key: Verified admin API key
        registry: ServiceRegistry instance

    Returns:
        List of all ServerEntry instances
    """
    return registry.list_servers()


@router.get("/{server_id}")
async def get_server(
    server_id: str,
    request: Request,
    admin_key: str = Depends(get_admin_authenticated_request),
    registry: ServiceRegistry = Depends(get_registry),
) -> ServerEntry:
    """Get details of a specific server.

    Args:
        server_id: Server identifier
        request: FastAPI request object
        admin_key: Verified admin API key
        registry: ServiceRegistry instance

    Returns:
        ServerEntry if found

    Raises:
        HTTPException: 404 if server not found
    """
    server = registry.get_server(server_id)
    if not server:
        problem = problem_json_dict(
            status_code=status.HTTP_404_NOT_FOUND,
            title="Not Found",
            detail=f"Server '{server_id}' is not enrolled",
            code=SERVER_NOT_FOUND,
            instance=str(request.url),
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=problem)
    
    return server


@router.put("/{server_id}")
async def update_server(
    server_id: str,
    updates: Dict[str, Any],
    request: Request,
    admin_key: str = Depends(get_admin_authenticated_request),
    registry: ServiceRegistry = Depends(get_registry),
) -> ServerEntry:
    """Update an existing server entry.

    Args:
        server_id: Server identifier
        updates: Dictionary of fields to update
        request: FastAPI request object
        admin_key: Verified admin API key
        registry: ServiceRegistry instance

    Returns:
        Updated ServerEntry

    Raises:
        HTTPException: 404 if server not found
    """
    server = registry.update_server(server_id, updates)
    if not server:
        problem = problem_json_dict(
            status_code=status.HTTP_404_NOT_FOUND,
            title="Not Found",
            detail=f"Server '{server_id}' is not enrolled",
            code=SERVER_NOT_FOUND,
            instance=str(request.url),
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=problem)
    
    from task_framework.logging import logger
    logger.info("proxy.admin.server_updated", server_id=server_id, updates=list(updates.keys()))
    
    return server


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_server(
    server_id: str,
    request: Request,
    admin_key: str = Depends(get_admin_authenticated_request),
    registry: ServiceRegistry = Depends(get_registry),
) -> None:
    """Deregister a server.

    Args:
        server_id: Server identifier
        request: FastAPI request object
        admin_key: Verified admin API key
        registry: ServiceRegistry instance

    Raises:
        HTTPException: 404 if server not found
    """
    deleted = registry.delete_server(server_id)
    if not deleted:
        problem = problem_json_dict(
            status_code=status.HTTP_404_NOT_FOUND,
            title="Not Found",
            detail=f"Server '{server_id}' is not enrolled",
            code=SERVER_NOT_FOUND,
            instance=str(request.url),
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=problem)
    
    from task_framework.logging import logger
    logger.info("proxy.admin.server_deleted", server_id=server_id)

