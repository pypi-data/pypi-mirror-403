"""Admin settings API endpoints."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from task_framework.dependencies import get_framework
from task_framework.framework import TaskFramework
from task_framework.logging import logger
from task_framework.middleware.admin_auth import get_admin_authenticated_request
from task_framework.models.settings import (
    SettingsResponse,
    SettingsUpdateRequest,
    SystemSettings,
)


router = APIRouter(prefix="/admin/settings", tags=["Settings"])


async def get_settings_store(framework: TaskFramework = Depends(get_framework)):
    """Get the settings store from framework."""
    return framework.settings_store


@router.get(
    "",
    response_model=SettingsResponse,
    summary="Get system settings",
    description="Get current system settings including thread concurrency limits.",
)
async def get_settings(
    admin_key: str = Depends(get_admin_authenticated_request),
    framework: TaskFramework = Depends(get_framework),
) -> SettingsResponse:
    """Get current system settings."""
    settings_store = framework.settings_store
    concurrency_manager = framework.concurrency_manager
    
    if settings_store:
        settings = await settings_store.get_settings()
    else:
        settings = SystemSettings.default()
    
    # Get runtime stats
    running_count = 0
    queued_count = 0
    if concurrency_manager:
        running_count = await concurrency_manager.get_running_thread_count()
        queued_count = await concurrency_manager.get_queued_thread_count()
    
    return SettingsResponse(
        max_concurrent_threads=settings.max_concurrent_threads,
        updated_at=settings.updated_at,
        updated_by=settings.updated_by,
        current_running_threads=running_count,
        current_queued_threads=queued_count,
    )


@router.put(
    "",
    response_model=SettingsResponse,
    summary="Update system settings",
    description="Update system settings. Changes take effect immediately.",
)
async def update_settings(
    request: SettingsUpdateRequest,
    admin_key: str = Depends(get_admin_authenticated_request),
    framework: TaskFramework = Depends(get_framework),
) -> SettingsResponse:
    """Update system settings."""
    settings_store = framework.settings_store
    concurrency_manager = framework.concurrency_manager
    
    if not settings_store:
        raise HTTPException(
            status_code=501,
            detail="Settings storage not available (requires STORAGE_TYPE=elasticsearch)",
        )
    
    # Get current settings
    settings = await settings_store.get_settings()
    
    # Apply updates
    if request.max_concurrent_threads is not None:
        settings.max_concurrent_threads = request.max_concurrent_threads
    
    # Save updates
    settings = await settings_store.update_settings(settings, updated_by="admin")
    
    # Signal concurrency manager that settings changed (to wake up waiting threads)
    if concurrency_manager:
        concurrency_manager.signal_settings_changed()
    
    logger.info(
        "settings.updated",
        max_concurrent_threads=settings.max_concurrent_threads,
    )
    
    # Get runtime stats
    running_count = 0
    queued_count = 0
    if concurrency_manager:
        running_count = await concurrency_manager.get_running_thread_count()
        queued_count = await concurrency_manager.get_queued_thread_count()
        
        # If limit was increased, process the queue
        await concurrency_manager.process_queue()
    
    return SettingsResponse(
        max_concurrent_threads=settings.max_concurrent_threads,
        updated_at=settings.updated_at,
        updated_by=settings.updated_by,
        current_running_threads=running_count,
        current_queued_threads=queued_count,
    )


@router.get(
    "/threads",
    response_model=SettingsResponse,
    summary="Get thread concurrency settings",
    description="Get thread concurrency limit settings.",
)
async def get_thread_settings(
    admin_key: str = Depends(get_admin_authenticated_request),
    framework: TaskFramework = Depends(get_framework),
) -> SettingsResponse:
    """Get thread concurrency settings."""
    return await get_settings(framework)


@router.put(
    "/threads",
    response_model=SettingsResponse,
    summary="Update thread concurrency settings",
    description="Update maximum concurrent threads. Set to 0 for unlimited.",
)
async def update_thread_settings(
    request: SettingsUpdateRequest,
    admin_key: str = Depends(get_admin_authenticated_request),
    framework: TaskFramework = Depends(get_framework),
) -> SettingsResponse:
    """Update thread concurrency settings."""
    return await update_settings(request, framework)
