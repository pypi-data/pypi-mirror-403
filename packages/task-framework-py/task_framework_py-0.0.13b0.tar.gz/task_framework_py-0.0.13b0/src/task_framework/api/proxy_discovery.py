"""Public discovery API endpoints for clients to discover enrolled task servers."""

import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from task_framework.proxy_registry import ServerEntry, ServiceRegistry

router = APIRouter(tags=["proxy-discovery"])


def get_registry(request: Request) -> ServiceRegistry:
    """Dependency to get ServiceRegistry instance from app state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        ServiceRegistry instance
    """
    return request.app.state.registry


@router.get("/servers")
async def list_servers(
    request: Request,
    registry: ServiceRegistry = Depends(get_registry),
) -> Dict[str, Any]:
    """List all enrolled task servers with their status and capabilities.
    
    This endpoint allows clients (including LLMs) to discover available task servers
    and their capabilities without requiring admin authentication.
    
    Returns:
        Dictionary with 'servers' list containing ServerEntry records
    """
    servers = registry.list_servers()
    
    # Convert ServerEntry models to dicts for JSON serialization
    server_list = []
    for server in servers:
        server_dict = server.model_dump()
        # Convert datetime to ISO string if present
        if server_dict.get("last_checked_at"):
            server_dict["last_checked_at"] = server_dict["last_checked_at"].isoformat()
        server_list.append(server_dict)
    
    return {
        "servers": server_list,
        "count": len(server_list),
    }


@router.get("/openapi.json")
async def get_task_framework_openapi(
    request: Request,
    registry: ServiceRegistry = Depends(get_registry),
) -> JSONResponse:
    """Get Task Framework OpenAPI specification with proxy routing examples.
    
    This endpoint returns the Task Framework API OpenAPI specification, but with
    examples and descriptions showing how to call task servers via the proxy
    using all three routing methods (path-prefix, header-based, query-based).
    
    The OpenAPI spec is the same for all task servers since they all implement
    the Task Framework API. This endpoint provides clients (including LLMs) with
    the API contract and routing instructions.
    
    Returns:
        OpenAPI 3.1.0 JSON specification with proxy routing documentation
    """
    # Load the base Task Framework OpenAPI spec
    from pathlib import Path
    
    # Find the openapi-enhanced.yaml file
    spec_path = Path(__file__).parent.parent.parent.parent / "specs" / "initial" / "openapi-enhanced.yaml"
    
    base_spec = None
    
    if spec_path.exists():
        # Try to load from YAML file
        try:
            import yaml
            with open(spec_path, "r", encoding="utf-8") as f:
                base_spec = yaml.safe_load(f)
        except ImportError:
            # PyYAML not available, try JSON fallback
            pass
        except Exception as e:
            from task_framework.logging import logger
            logger.warning("proxy.discovery.openapi_load_failed", path=str(spec_path), error=str(e))
    
    if not base_spec:
        # Fallback: create minimal OpenAPI spec structure
        # We'll build a basic spec that documents the proxy routing
        base_spec = {
            "openapi": "3.1.0",
            "info": {
                "title": "Task Framework API",
                "version": "0.1.0",
                "description": "Task Framework HTTP API for task execution"
            },
            "paths": {}
        }
    
    # Modify the spec to show proxy routing
    # Add proxy-specific info and examples
    base_spec["info"]["title"] = "Task Framework API (via Proxy)"
    base_spec["info"]["description"] = """Task Framework HTTP API for task execution.

This OpenAPI specification describes the Task Framework API endpoints that are available
on all enrolled task servers. To call these endpoints via the proxy, use one of three
routing methods:

**1. Path-prefix routing (recommended):**
```
POST /servers/{server_id}/threads
GET /servers/{server_id}/threads
```

**2. Header-based routing:**
```
POST /threads
X-Task-Server: {server_id}
```

**3. Query-based routing:**
```
POST /threads?server={server_id}
GET /threads?server={server_id}&state=succeeded
```

Replace `{server_id}` with the ID of an enrolled task server (see `/servers` endpoint).

All endpoints require authentication via `X-API-Key` header. Some endpoints also require
`X-User-Id` and `X-App-Id` headers for regular API keys.
"""
    
    # Add proxy-specific servers section
    base_spec["servers"] = [
        {
            "url": "{proxy_url}",
            "description": "Proxy server base URL. Replace {proxy_url} with your proxy server address (e.g., http://localhost:9000)",
            "variables": {
                "proxy_url": {
                    "default": "http://localhost:9000",
                    "description": "Base URL of the proxy server"
                }
            }
        }
    ]
    
    # Modify each path to include proxy routing examples
    if "paths" in base_spec:
        for path_key, path_item in base_spec["paths"].items():
            # Skip proxy-specific paths
            if path_key.startswith("/admin/") or path_key.startswith("/servers") or path_key in ["/health", "/metrics", "/docs", "/openapi.json"]:
                continue
            
            # Add proxy routing examples to path description
            if isinstance(path_item, dict):
                for method in ["get", "post", "put", "delete", "patch"]:
                    if method in path_item:
                        operation = path_item[method]
                        if "description" not in operation:
                            operation["description"] = ""
                        
                        # Add proxy routing examples
                        proxy_examples = f"""

**Proxy Routing Examples:**

Path-prefix:
- `{method.upper()} /servers/{{server_id}}{path_key}`

Header-based:
- `{method.upper()} {path_key}`
- Header: `X-Task-Server: {{server_id}}`

Query-based:
- `{method.upper()} {path_key}?server={{server_id}}`
"""
                        operation["description"] = operation.get("description", "") + proxy_examples
    
    # Add proxy-specific components/schemas if needed
    if "components" not in base_spec:
        base_spec["components"] = {}
    if "schemas" not in base_spec["components"]:
        base_spec["components"]["schemas"] = {}
    
    # Add proxy routing info schema
    base_spec["components"]["schemas"]["ProxyRoutingInfo"] = {
        "type": "object",
        "description": "Information about proxy routing methods",
        "properties": {
            "path_prefix": {
                "type": "string",
                "example": "/servers/{server_id}/threads",
                "description": "Path-prefix routing format"
            },
            "header_based": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "example": "/threads"},
                    "header": {"type": "string", "example": "X-Task-Server: {server_id}"}
                }
            },
            "query_based": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "example": "/threads"},
                    "query": {"type": "string", "example": "?server={server_id}"}
                }
            }
        }
    }
    
    return JSONResponse(content=base_spec)

