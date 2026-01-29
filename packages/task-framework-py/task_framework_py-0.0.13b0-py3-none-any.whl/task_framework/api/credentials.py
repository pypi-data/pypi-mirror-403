"""Admin API routes for credentials management."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from task_framework.dependencies import get_framework
from task_framework.logging import logger
from task_framework.middleware.admin_auth import get_admin_authenticated_request


router = APIRouter(prefix="/admin", tags=["admin-credentials"])


@router.get("/credentials")
async def list_credentials(
    admin_key: str = Depends(get_admin_authenticated_request),
    framework: Any = Depends(get_framework),
) -> JSONResponse:
    """List all credentials (without values).
    
    Returns:
        List of credential info objects
    """
    credential_service = framework.credential_service
    
    credentials = await credential_service.list_all()
    
    return JSONResponse({
        "credentials": [cred.model_dump(mode="json") for cred in credentials]
    })


@router.get("/credentials/{name}")
async def get_credential(
    name: str,
    admin_key: str = Depends(get_admin_authenticated_request),
    framework: Any = Depends(get_framework),
) -> JSONResponse:
    """Get credential info (without value).
    
    Returns:
        Credential info or 404
    """
    credential_service = framework.credential_service
    
    credential = await credential_service.get(name)
    
    if not credential:
        return JSONResponse(
            {"error": f"Credential '{name}' not found"},
            status_code=404
        )
    
    from task_framework.models.credential import CredentialInfo
    info = CredentialInfo.from_credential(credential)
    
    return JSONResponse(info.model_dump(mode="json"))


@router.put("/credentials/{name}")
async def create_or_update_credential(
    name: str,
    request: Request,
    admin_key: str = Depends(get_admin_authenticated_request),
    framework: Any = Depends(get_framework),
) -> JSONResponse:
    """Create or update a credential.
    
    Request body:
        {
            "value": "secret-value",  # Required for new credentials, optional for updates
            "description": "Optional description",
            "tags": ["optional", "tags"]
        }
    
    Returns:
        Credential info (without value)
    """
    credential_service = framework.credential_service
    
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            {"error": "Invalid JSON body"},
            status_code=400
        )
    
    value = body.get("value")
    description = body.get("description", "")
    tags = body.get("tags", [])
    expires_at_str = body.get("expires_at")
    expires_at = None
    if expires_at_str:
        try:
            expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
        except ValueError:
            return JSONResponse(
                {"error": "Invalid expires_at format. Use ISO 8601."},
                status_code=400
            )
    
    # Check if credential exists
    existing = await credential_service.get(name)
    
    if not existing and not value:
        # Creating new credential requires value
        return JSONResponse(
            {"error": "Field 'value' is required for new credentials"},
            status_code=400
        )
    
    if existing and not value:
        # Updating metadata only - keep existing value
        value = existing.value
    
    credential = await credential_service.create_or_update(
        name=name,
        value=value,
        description=description,
        tags=tags,
        expires_at=expires_at,
    )
    
    logger.info(
        "admin.credential.saved",
        credential_name=name,
    )
    
    from task_framework.models.credential import CredentialInfo
    info = CredentialInfo.from_credential(credential)
    
    return JSONResponse(info.model_dump(mode="json"))


@router.delete("/credentials/{name}")
async def delete_credential(
    name: str,
    admin_key: str = Depends(get_admin_authenticated_request),
    framework: Any = Depends(get_framework),
) -> JSONResponse:
    """Delete a credential.
    
    Returns:
        Success message or 404
    """
    credential_service = framework.credential_service
    
    deleted = await credential_service.delete(name)
    
    if not deleted:
        return JSONResponse(
            {"error": f"Credential '{name}' not found"},
            status_code=404
        )
    
    logger.info(
        "admin.credential.deleted",
        credential_name=name,
    )
    
    return JSONResponse({"message": f"Credential '{name}' deleted"})


@router.get("/credentials/{name}/reveal")
async def reveal_credential(
    name: str,
    admin_key: str = Depends(get_admin_authenticated_request),
    framework: Any = Depends(get_framework),
) -> JSONResponse:
    """Reveal the full credential value.
    
    Returns:
        The credential value (for authorized admin viewing)
    """
    credential_service = framework.credential_service
    
    value = await credential_service.get_value(name)
    if value is None:
        return JSONResponse(
            {"error": f"Credential '{name}' not found"},
            status_code=404
        )
    
    return JSONResponse({"name": name, "value": value})


@router.get("/credentials/{name}/usage")
async def get_credential_usage(
    name: str,
    admin_key: str = Depends(get_admin_authenticated_request),
    framework: Any = Depends(get_framework),
) -> JSONResponse:
    """Get which tasks use a credential (vault entry).
    
    Returns:
        List of tasks using this credential
    """
    credential_service = framework.credential_service
    configuration_service = framework.configuration_service
    
    # Check if credential exists
    exists = await credential_service.exists(name)
    if not exists:
        return JSONResponse(
            {"error": f"Credential '{name}' not found"},
            status_code=404
        )
    
    usage = await configuration_service.get_vault_usage(name)
    
    return JSONResponse({
        "credential_name": name,
        "used_by": usage
    })


@router.get("/tasks/{task_id}/{version}/config")
async def get_task_config(
    task_id: str,
    version: str,
    admin_key: str = Depends(get_admin_authenticated_request),
    framework: Any = Depends(get_framework),
) -> JSONResponse:
    """Get task configuration status.
    
    Returns:
        Configuration status with requirements and current values
    """
    configuration_service = framework.configuration_service
    task_registry = framework.task_registry
    
    # Ensure registry is up-to-date from file (multi-worker sync)
    await task_registry.ensure_loaded()
    
    # Get task definition
    task_def = task_registry.get(task_id, version)
    if not task_def:
        return JSONResponse(
            {"error": f"Task '{task_id}:{version}' not found"},
            status_code=404
        )
    
    status = await configuration_service.get_configuration_status(task_def)
    return JSONResponse(status.model_dump(mode="json"))


@router.put("/tasks/{task_id}/{version}/config")
async def set_task_config(
    task_id: str,
    version: str,
    request: Request,
    admin_key: str = Depends(get_admin_authenticated_request),
    framework: Any = Depends(get_framework),
) -> JSONResponse:
    """Set or update task configuration.
    
    Request body:
        {
            "config_values": {
                "DATABASE_HOST": {"value": "pg.example.com", "is_vault_ref": false},
                "API_KEY": {"vault_key": "openai_prod_key", "is_vault_ref": true}
            }
        }
    
    Returns:
        Updated configuration status
    """
    configuration_service = framework.configuration_service
    task_registry = framework.task_registry
    
    # Ensure registry is up-to-date from file (multi-worker sync)
    await task_registry.ensure_loaded()
    
    # Check task exists
    task_def = task_registry.get(task_id, version)
    if not task_def:
        return JSONResponse(
            {"error": f"Task '{task_id}:{version}' not found"},
            status_code=404
        )
    
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            {"error": "Invalid JSON body"},
            status_code=400
        )
    
    config_values = body.get("config_values", {})
    
    # Validate vault references point to existing credentials
    credential_service = framework.credential_service
    for key, entry in config_values.items():
        if entry.get("is_vault_ref"):
            vault_key = entry.get("vault_key")
            if vault_key:
                exists = await credential_service.exists(vault_key)
                if not exists:
                    return JSONResponse(
                        {"error": f"Vault entry '{vault_key}' not found (referenced by '{key}')"},
                        status_code=400
                    )
    
    await configuration_service.set_config(
        task_id=task_id,
        version=version,
        config_values=config_values,
    )
    
    logger.info(
        "admin.task_config.saved",
        task_id=task_id,
        version=version,
    )
    
    # Return updated status
    status = await configuration_service.get_configuration_status(task_def)
    return JSONResponse(status.model_dump(mode="json"))


@router.delete("/tasks/{task_id}/{version}/config")
async def delete_task_config(
    task_id: str,
    version: str,
    admin_key: str = Depends(get_admin_authenticated_request),
    framework: Any = Depends(get_framework),
) -> JSONResponse:
    """Delete task configuration.
    
    Returns:
        Success message or 404
    """
    configuration_service = framework.configuration_service
    
    deleted = await configuration_service.delete_config(task_id, version)
    
    if not deleted:
        return JSONResponse(
            {"error": f"No configuration found for '{task_id}:{version}'"},
            status_code=404
        )
    
    return JSONResponse({"message": f"Configuration for '{task_id}:{version}' deleted"})
