"""Proxy API router for forwarding requests to enrolled task servers."""

import time
import uuid
from typing import Any, Optional
from urllib.parse import urlparse, parse_qs

import httpx
from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import StreamingResponse

from task_framework.errors import SERVER_NOT_FOUND, UPSTREAM_ERROR, UPSTREAM_TIMEOUT, problem_json_dict
from task_framework.logging import get_logger_with_request_id, logger
from task_framework.metrics_proxy import (
    proxy_request_latency_seconds,
    proxy_requests_total,
    proxy_tasktype_requests_total,
    proxy_upstream_errors_total,
)
from task_framework.proxy_registry import ServiceRegistry

router = APIRouter()


def get_registry(request: Request) -> ServiceRegistry:
    """Get ServiceRegistry instance from app state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        ServiceRegistry instance
    """
    return request.app.state.registry


async def _forward_request(
    server_id: str,
    target_path: str,
    request: Request,
    registry: ServiceRegistry,
    query_string_override: Optional[str] = None,
) -> Response:
    """Internal helper to forward a request to an enrolled server.
    
    Args:
        server_id: Target server identifier
        target_path: Path to forward (relative to server base_url)
        request: Original FastAPI request object
        registry: ServiceRegistry instance
        query_string_override: Optional query string to use instead of request.url.query
        
    Returns:
        Response from upstream server or error response
        
    Raises:
        HTTPException: If server not found or forwarding fails
    """
    # Generate request ID for tracing
    request_id = str(uuid.uuid4())
    log = get_logger_with_request_id(request_id)
    
    # Get target server
    server = registry.get_server(server_id)
    if not server:
        log.warning("proxy.server_not_found", server_id=server_id)
        problem = problem_json_dict(
            status_code=status.HTTP_404_NOT_FOUND,
            title="Server Not Found",
            detail=f"Server '{server_id}' is not enrolled",
            code=SERVER_NOT_FOUND,
            instance=str(request.url),
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=problem)
    
    # Build upstream URL
    upstream_url = f"{server.base_url.rstrip('/')}/{target_path.lstrip('/')}"
    query_to_use = query_string_override if query_string_override is not None else request.url.query
    if query_to_use:
        upstream_url += f"?{query_to_use}"
    
    # Debug: log incoming request headers and selected upstream URL
    try:
        logger.info(
            "proxy.debug.request_received",
            server_id=server_id,
            upstream_url=upstream_url,
            incoming_headers={k: v for k, v in request.headers.items()},
        )
    except Exception:
        # Never let logging debug crash the proxy
        pass
    log.info(
        "proxy.request.forwarding",
        server_id=server_id,
        method=request.method,
        upstream_url=upstream_url,
    )
    
    # Prepare headers to forward
    headers = {}
    for name, value in request.headers.items():
        # Skip hop-by-hop headers (RFC 2616) and routing headers
        if name.lower() in [
            "connection",
            "keep-alive",
            "proxy-authenticate",
            "proxy-authorization",
            "te",
            "trailers",
            "transfer-encoding",
            "upgrade",
            "host",  # Replace with upstream host
            "x-task-server",  # Remove routing header before forwarding
        ]:
            continue
        headers[name] = value
    
    # Set upstream Host header
    parsed = urlparse(server.base_url)
    headers["Host"] = parsed.netloc
    
    # Debug: log headers that will be forwarded upstream (redact sensitive keys)
    try:
        redacted = {k: ("REDACTED" if k.lower() in ["x-api-key", "authorization"] else v) for k, v in headers.items()}
        logger.info("proxy.debug.forwarding_headers", server_id=server_id, forwarding_headers=redacted)
    except Exception:
        pass
    # Preserve tracing headers (X-Request-ID, X-Trace-ID, etc.)
    if "X-Request-ID" not in headers:
        headers["X-Request-ID"] = request_id
    
    # Get request body
    body = await request.body()
    
    # Forward request
    start_time = time.time()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=request.method,
                url=upstream_url,
                headers=headers,
                content=body if body else None,
                follow_redirects=False,
            )
            
            duration_seconds = time.time() - start_time
            
            # Update metrics
            proxy_requests_total.labels(
                server_id=server_id,
                method=request.method,
                code=str(response.status_code),
            ).inc()
            
            proxy_request_latency_seconds.labels(server_id=server_id).observe(duration_seconds)
            
            # Update task type metrics if applicable
            for task_type in server.task_types:
                proxy_tasktype_requests_total.labels(
                    task_type=task_type,
                    server_id=server_id,
                    code=str(response.status_code),
                ).inc()
            
            log.info(
                "proxy.request.completed",
                server_id=server_id,
                method=request.method,
                status_code=response.status_code,
                duration_seconds=duration_seconds,
            )
            
            # Prepare response headers
            response_headers = {}
            for name, value in response.headers.items():
                # Skip hop-by-hop headers
                if name.lower() in [
                    "connection",
                    "keep-alive",
                    "proxy-authenticate",
                    "proxy-authorization",
                    "te",
                    "trailers",
                    "transfer-encoding",
                    "upgrade",
                ]:
                    continue
                # Adjust Location header if present
                if name.lower() == "location":
                    # If Location is relative, keep as-is; if absolute, may need adjustment
                    response_headers[name] = value
                else:
                    response_headers[name] = value
            
            # Handle streaming response
            if response.headers.get("content-type", "").startswith("text/event-stream"):
                # Streaming response
                async def stream_generator():
                    async for chunk in response.aiter_bytes():
                        yield chunk
                
                return StreamingResponse(
                    stream_generator(),
                    status_code=response.status_code,
                    headers=response_headers,
                    media_type=response.headers.get("content-type"),
                )
            else:
                # Regular response
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=response_headers,
                    media_type=response.headers.get("content-type"),
                )
                
    except httpx.TimeoutException:
        duration_seconds = time.time() - start_time
        proxy_upstream_errors_total.labels(server_id=server_id, reason="timeout").inc()
        log.error(
            "proxy.request.timeout",
            server_id=server_id,
            method=request.method,
            duration_seconds=duration_seconds,
        )
        problem = problem_json_dict(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            title="Gateway Timeout",
            detail=f"Upstream server '{server_id}' did not respond in time",
            code=UPSTREAM_TIMEOUT,
            instance=str(request.url),
        )
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=problem)
        
    except httpx.ConnectError:
        duration_seconds = time.time() - start_time
        proxy_upstream_errors_total.labels(server_id=server_id, reason="connection_error").inc()
        log.error(
            "proxy.request.connection_error",
            server_id=server_id,
            method=request.method,
        )
        problem = problem_json_dict(
            status_code=status.HTTP_502_BAD_GATEWAY,
            title="Bad Gateway",
            detail=f"Could not connect to upstream server '{server_id}'",
            code=UPSTREAM_ERROR,
            instance=str(request.url),
        )
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=problem)
        
    except Exception as e:
        duration_seconds = time.time() - start_time
        proxy_upstream_errors_total.labels(server_id=server_id, reason="unknown").inc()
        log.error(
            "proxy.request.error",
            server_id=server_id,
            method=request.method,
            error=str(e),
            exc_info=True,
        )
        problem = problem_json_dict(
            status_code=status.HTTP_502_BAD_GATEWAY,
            title="Bad Gateway",
            detail=f"Error forwarding request to upstream server '{server_id}': {str(e)}",
            code=UPSTREAM_ERROR,
            instance=str(request.url),
        )
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=problem)


@router.api_route("/servers/{server_id}/{rest_of_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def proxy_request(
    server_id: str,
    rest_of_path: str,
    request: Request,
) -> Response:
    """Forward client request to enrolled task server using path-prefix routing.
    
    Args:
        server_id: Target server identifier
        rest_of_path: Remaining path after /servers/{server_id}
        request: Original FastAPI request object
        
    Returns:
        Response from upstream server or error response
    """
    registry = get_registry(request)
    return await _forward_request(server_id, rest_of_path, request, registry)


@router.api_route("/{rest_of_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def proxy_request_header_query(
    rest_of_path: str,
    request: Request,
) -> Response:
    """Forward client request to enrolled task server using header or query-based routing.
    
    This route handles requests where the server_id is specified via:
    - Header: `X-Task-Server: {server_id}`
    - Query parameter: `?server={server_id}`
    
    The path-prefix route `/servers/{server_id}/...` takes precedence over this route.
    Admin endpoints (`/admin/*`) are excluded from header/query routing.
    
    Args:
        rest_of_path: Full path from request URL
        request: Original FastAPI request object
        
    Returns:
        Response from upstream server or error response
        
    Raises:
        HTTPException: 400 if neither header nor query param provided, 404 if server not found
    """
    # Exclude proxy's own endpoints (admin endpoints are handled by admin router registered before this router)
    # Also exclude discovery endpoints (/servers, /openapi.json) and UI endpoints (/ui/*)
    if rest_of_path in ["health", "metrics", "docs", "openapi.json", "redoc", "servers"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=problem_json_dict(
                status_code=status.HTTP_404_NOT_FOUND,
                title="Not Found",
                detail=f"Endpoint '/{rest_of_path}' not found",
                code="NOT_FOUND",
                instance=str(request.url),
            ),
        )
    
    # Exclude UI endpoints from proxy forwarding
    if rest_of_path.startswith("ui/") or rest_of_path == "ui":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=problem_json_dict(
                status_code=status.HTTP_404_NOT_FOUND,
                title="Not Found",
                detail=f"Endpoint '/{rest_of_path}' not found",
                code="NOT_FOUND",
                instance=str(request.url),
            ),
        )
    
    registry = get_registry(request)
    
    # Extract server_id from header or query parameter
    server_id: Optional[str] = None
    
    # Check header first (X-Task-Server)
    header_value = request.headers.get("X-Task-Server")
    if header_value:
        server_id = header_value.strip()
    
    # Parse query params for server param and for cleanup
    query_params = parse_qs(request.url.query)
    
    # Fall back to query parameter (?server=...)
    if not server_id:
        server_params = query_params.get("server", [])
        if server_params:
            server_id = server_params[0].strip()
    
    # Remove server query param before forwarding to avoid sending it upstream
    query_string_override: Optional[str] = None
    if "server" in query_params:
        # Rebuild query string without server param
        filtered_params = {k: v for k, v in query_params.items() if k != "server"}
        if filtered_params:
            from urllib.parse import urlencode
            query_string_override = urlencode(filtered_params, doseq=True)
        else:
            query_string_override = ""  # Empty query string
    
    if not server_id:
        problem = problem_json_dict(
            status_code=status.HTTP_400_BAD_REQUEST,
            title="Bad Request",
            detail="Server ID must be specified via 'X-Task-Server' header or 'server' query parameter",
            code="ROUTING_REQUIRED",
            instance=str(request.url),
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=problem)
    
    # Forward request using the extracted server_id
    return await _forward_request(server_id, rest_of_path, request, registry, query_string_override=query_string_override)

