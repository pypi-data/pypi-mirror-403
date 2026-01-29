"""UI routes for Task Framework web interface.

This module provides the web UI for interacting with the Task Framework API.
All UI routes are public (no authentication required) as they consume the API via htmx.
"""

from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse
from typing import Any
from fastapi import Depends
from fastapi.responses import JSONResponse

from task_framework.dependencies import get_framework
from task_framework.repositories.file_db import FileDatabase
from task_framework.services.file_service import FileService

# Create router for UI endpoints (no prefix - routes define full paths)
# Hide from OpenAPI schema - these are HTML pages, not API endpoints
router = APIRouter(tags=["UI"], include_in_schema=False)

# Get the directory where this file is located
UI_DIR = Path(__file__).parent


@router.get("/ui", response_class=FileResponse)
async def ui_index():
    """Serve the main UI page.
    
    This is the entry point for the web interface. It provides:
    - Layout structure with left sidebar and main content area
    - Settings management (API key, App ID, User ID)
    - Thread management interface
    - Artifact management interface
    """
    file_path = UI_DIR / "pages" / "index.html"
    return FileResponse(file_path, media_type="text/html")


@router.get("/ui/settings", response_class=FileResponse)
async def ui_settings():
    """Serve the settings page.
    
    This page allows users to configure:
    - X-API-Key: Required for API authentication
    - X-App-ID: Optional application identifier for filtering
    - X-User-ID: Optional user identifier for filtering
    
    All settings are stored in browser localStorage and automatically
    included as headers in API requests via htmx.
    """
    file_path = UI_DIR / "pages" / "settings.html"
    return FileResponse(file_path, media_type="text/html")


@router.get("/ui/threads", response_class=FileResponse)
async def ui_threads():
    """Serve the threads list page.
    
    This page provides:
    - List of all threads with filtering (state, user_id, app_id, etc.)
    - Pagination support
    - Quick actions (view, stop, retry)
    - Link to create new threads
    
    All data is fetched from the /threads API endpoint via htmx.
    """
    file_path = UI_DIR / "pages" / "threads.html"
    return FileResponse(file_path, media_type="text/html")


@router.get("/ui/threads/create", response_class=FileResponse)
async def ui_thread_create():
    """Serve the create thread page.
    
    This page provides a form to create new threads with:
    - Execution mode selection (sync/async)
    - Input text configuration
    - Custom metadata (JSON)
    - Advanced options (idempotency key, webhook)
    
    On successful creation, redirects to the thread detail page.
    """
    file_path = UI_DIR / "pages" / "thread-create.html"
    return FileResponse(file_path, media_type="text/html")


@router.get("/ui/threads/{thread_id}", response_class=FileResponse)
async def ui_thread_detail(thread_id: str):
    """Serve the thread detail page.
    
    This page displays:
    - Thread overview (id, state, timestamps, duration)
    - Error details (if failed)
    - Metadata
    - Input artifacts
    - Output artifacts
    - Actions (stop, retry, refresh)
    
    Args:
        thread_id: The thread identifier
    
    Returns:
        Thread detail HTML page
    """
    file_path = UI_DIR / "pages" / "thread-detail.html"
    return FileResponse(file_path, media_type="text/html")


@router.get("/ui/threads/{thread_id}/artifacts", response_class=FileResponse)
async def ui_thread_artifacts(thread_id: str):
    """Serve the thread artifacts page.
    
    This page provides advanced artifact management:
    - List all inputs and outputs for a thread
    - Filter by kind, direction, ref pattern, media type
    - View artifact details in modal
    - Copy artifact references
    - Include/exclude archived artifacts
    - Pagination for large artifact sets
    
    Args:
        thread_id: The thread identifier
    
    Returns:
        Thread artifacts HTML page
    """
    file_path = UI_DIR / "pages" / "thread-artifacts.html"
    return FileResponse(file_path, media_type="text/html")


@router.get("/ui/artifacts", response_class=FileResponse)
async def ui_artifacts():
    """Serve the artifacts list page.
    
    This page provides comprehensive artifact management across all threads:
    - List all artifacts with advanced filtering:
      - ref: Artifact reference pattern (supports wildcards)
      - kind: Artifact type (text, file, json, etc.)
      - media_type: MIME type filter
      - thread_id: Filter by specific thread
      - app_id: Filter by application identifier
    - View artifact details in modal
    - Download artifacts (files and URLs)
    - Archive artifacts (soft delete)
    - Delete artifacts permanently
    - Pagination support for large artifact sets
    - Include/exclude archived artifacts
    
    All data is fetched from the /artifacts API endpoint.
    
    Returns:
        Artifacts list HTML page
    """
    file_path = UI_DIR / "pages" / "artifacts.html"
    return FileResponse(file_path, media_type="text/html")


@router.get("/ui/webhooks", response_class=FileResponse)
async def ui_webhooks():
    """Serve the webhooks list page.
    
    This page provides webhook management:
    - List all webhooks with filtering by enabled status
    - Navigate to create/edit pages
    - Delete webhooks
    - View webhook details and delivery history
    - Pagination support for large webhook sets
    
    All data is fetched from the /webhooks API endpoint.
    
    Returns:
        Webhooks list HTML page
    """
    file_path = UI_DIR / "pages" / "webhooks.html"
    return FileResponse(file_path, media_type="text/html")


@router.get("/ui/webhooks/create", response_class=FileResponse)
async def ui_webhook_create():
    """Serve the webhook creation page.
    
    This page provides a form to create new webhooks with:
    - URL configuration with validation
    - Enable/disable toggle
    - Timeout settings (1-60 seconds)
    - Event filters (include/exclude specific events)
    - Scope filters (thread, user, app, tenant)
    
    On successful creation, redirects to the webhooks list.
    
    Returns:
        Webhook creation HTML page
    """
    file_path = UI_DIR / "pages" / "webhook-create.html"
    return FileResponse(file_path, media_type="text/html")


@router.get("/ui/webhooks/edit/{webhook_id}", response_class=FileResponse)
async def ui_webhook_edit(webhook_id: str):
    """Serve the webhook edit page.
    
    This page loads existing webhook configuration and allows editing:
    - URL, enabled status, timeout
    - Event filters and scope configuration
    - Form pre-populated with current values
    
    Args:
        webhook_id: The webhook identifier
    
    Returns:
        Webhook edit HTML page (same as create, but loads existing data)
    """
    file_path = UI_DIR / "pages" / "webhook-create.html"
    return FileResponse(file_path, media_type="text/html")


@router.get("/ui/webhooks/{webhook_id}", response_class=FileResponse)
async def ui_webhook_detail(webhook_id: str):
    """Serve the webhook detail page.
    
    This page displays:
    - Webhook configuration (URL, secret, events, scope, data filters)
    - Enable/disable webhook
    - Regenerate secret
    - Delivery history with filtering by status and thread_id
    - Pagination for delivery records
    - View delivery details including payload and response
    
    Args:
        webhook_id: The webhook identifier
    
    Returns:
        Webhook detail HTML page
    """
    file_path = UI_DIR / "pages" / "webhook-details.html"
    return FileResponse(file_path, media_type="text/html")


@router.get("/ui/components/deliveries-table.html", response_class=FileResponse)
async def ui_component_deliveries_table():
    """Serve the deliveries table component.
    
    This is a reusable component for displaying webhook delivery history.
    It includes:
    - Delivery list with filtering (status, thread_id)
    - Pagination support
    - View delivery details in modal
    - Status badges and response time display
    
    Returns:
        Deliveries table HTML component
    """
    file_path = UI_DIR / "components" / "deliveries-table.html"
    return FileResponse(file_path, media_type="text/html")


@router.get("/ui/schedules", response_class=FileResponse)
async def ui_schedules():
    """Serve the schedules list page.
    
    This page provides schedule management:
    - List all schedules with filtering by state
    - Navigate to create/edit pages
    - Cancel schedules
    - View schedule details and run history
    - Pagination support for large schedule sets
    
    All data is fetched from the /schedules API endpoint.
    
    Returns:
        Schedules list HTML page
    """
    file_path = UI_DIR / "pages" / "schedules.html"
    return FileResponse(file_path, media_type="text/html")


@router.get("/ui/schedules/create", response_class=FileResponse)
async def ui_schedule_create():
    """Serve the schedule creation page.
    
    This page provides a form to create new schedules with:
    - Cron expression and timezone configuration
    - Input artifacts template
    - Task parameters and metadata
    - Concurrency policy and retry settings
    
    On successful creation, redirects to the schedule details page.
    
    Returns:
        Schedule creation HTML page
    """
    file_path = UI_DIR / "pages" / "schedule-create.html"
    return FileResponse(file_path, media_type="text/html")


@router.get("/ui/schedules/edit/{schedule_id}", response_class=FileResponse)
async def ui_schedule_edit(schedule_id: str):
    """Serve the schedule edit page.
    
    This page loads existing schedule configuration and allows editing:
    - Cron expression, timezone, state
    - Input artifacts template
    - Task parameters and metadata
    - Concurrency policy and max attempts
    - Form pre-populated with current values
    
    Args:
        schedule_id: The schedule identifier
    
    Returns:
        Schedule edit HTML page (same as create, but loads existing data)
    """
    file_path = UI_DIR / "pages" / "schedule-create.html"
    return FileResponse(file_path, media_type="text/html")


@router.get("/ui/schedules/{schedule_id}", response_class=FileResponse)
async def ui_schedule_detail(schedule_id: str):
    """Serve the schedule detail page.
    
    This page displays:
    - Schedule configuration (cron, timezone, state, inputs, params)
    - Pause/activate schedule
    - Run history with filtering by state
    - Pagination for run records
    - View run details including threads and metrics
    
    Args:
        schedule_id: The schedule identifier
    
    Returns:
        Schedule detail HTML page
    """
    file_path = UI_DIR / "pages" / "schedule-details.html"
    return FileResponse(file_path, media_type="text/html")


@router.get("/ui/components/runs-table.html", response_class=FileResponse)
async def ui_component_runs_table():
    """Serve the runs table component.
    
    This is a reusable component for displaying schedule run history.
    It includes:
    - Run list with filtering (state)
    - Pagination support
    - View run details in modal
    - State badges and thread links
    
    Returns:
        Runs table HTML component
    """
    file_path = UI_DIR / "components" / "runs-table.html"
    return FileResponse(file_path, media_type="text/html")


@router.get("/ui/files", response_class=FileResponse)
async def ui_files():
    """Serve the files list page.
    
    This page displays recently uploaded files from the session:
    - View recently uploaded files (session-based)
    - Copy file references for use in artifacts
    - Download files
    - Navigate to upload page
    
    Returns:
        Files list HTML page
    """
    file_path = UI_DIR / "pages" / "files.html"
    return FileResponse(file_path, media_type="text/html")


@router.get("/ui/files/list", response_class=JSONResponse)
async def ui_files_list(framework: Any = Depends(get_framework)):
    """Return a JSON list of file artifacts for the UI.

    This endpoint is a convenience for the UI when the browser does not have an
    API key configured in localStorage. It returns the same artifact list the UI
    would obtain from the /artifacts API, scoped to `kind=file`.
    """
    # Prefer framework's configured database, fall back to FileDatabase with default path
    database = framework.database if getattr(framework, "database", None) is not None else FileDatabase()
    artifacts = await database.query_artifacts({"kind": "file", "limit": 1000})
    items = []
    # Enrich artifacts with file metadata from storage (if available)
    file_service = None
    if getattr(framework, "file_storage", None) is not None:
        file_service = FileService(storage=framework.file_storage)

    for a in artifacts:
        entry = a.model_dump(exclude_none=True)
        # Try to fetch file metadata and attach filename/media_type/size/sha256
        file_ref = entry.get("file_ref")
        if file_ref and file_service is not None:
            try:
                metadata = await file_service.get_file_metadata(file_ref)
                # merge metadata fields into entry
                entry["filename"] = metadata.get("filename")
                entry["media_type"] = metadata.get("media_type", entry.get("media_type"))
                entry["size"] = metadata.get("size", entry.get("size"))
                entry["sha256"] = metadata.get("sha256", entry.get("sha256"))
            except Exception:
                # ignore storage errors, return artifact without metadata
                pass
        items.append(entry)

    pagination = {"cursor": None, "has_more": False, "total": len(items)}
    return JSONResponse({"items": items, "pagination": pagination})


@router.get("/ui/files/upload", response_class=FileResponse)
async def ui_file_upload():
    """Serve the file upload page.
    
    This page provides two upload methods:
    - Direct Upload: Single-request file upload with drag-and-drop support
    - Pre-signed URL: Two-step upload for large files or external integrations
    
    Features:
    - Drag and drop file selection
    - Real-time upload progress
    - Generate pre-signed URLs for external uploads
    - Automatic file type detection
    
    Returns:
        File upload HTML page
    """
    file_path = UI_DIR / "pages" / "file-upload.html"
    return FileResponse(file_path, media_type="text/html")


@router.get("/ui/metrics", response_class=FileResponse)
async def ui_metrics():
    """Serve the metrics page.
    
    This page displays Prometheus metrics from the /metrics endpoint
    in a user-friendly format with:
    - Metrics grouped by category
    - Readable metric names and descriptions
    - Current values and trends
    - Histogram visualization
    - Auto-refresh capability
    
    Returns:
        Metrics HTML page
    """
    file_path = UI_DIR / "pages" / "metrics.html"
    return FileResponse(file_path, media_type="text/html")


@router.get("/ui/metadata", response_class=FileResponse)
async def ui_metadata():
    """Serve the task metadata page.
    
    This page displays runtime-discoverable metadata from the /task/metadata endpoint:
    - Task name, version, and description
    - Framework and API versions
    - Capabilities (database, file storage, scheduler, webhooks)
    - Input artifact schemas with field definitions
    - Output artifact schemas with field definitions
    - JSON schemas for deep validation
    
    This endpoint is useful for understanding what the task expects as input
    and what it will produce as output.
    
    Returns:
        Task metadata HTML page
    """
    file_path = UI_DIR / "pages" / "metadata.html"
    return FileResponse(file_path, media_type="text/html")


@router.get("/ui/servers", response_class=FileResponse)
async def ui_servers():
    """Serve the servers list page (proxy mode only).
    
    This page provides server management for the Task Framework Proxy:
    - List all enrolled task servers
    - Health status monitoring with real-time updates
    - Filter by status and task types
    - Server actions: View, Edit, Delete, Health Check
    - Pagination support
    
    Requires proxy mode to be enabled and X-Admin-API-Key configured.
    
    Returns:
        Servers list HTML page
    """
    file_path = UI_DIR / "pages" / "servers.html"
    return FileResponse(file_path, media_type="text/html")


@router.get("/ui/servers/enroll", response_class=FileResponse)
async def ui_server_enroll():
    """Serve the server enrollment form (proxy mode only).
    
    This page provides a form to enroll new task servers with the proxy:
    - Server ID and name configuration
    - Base URL with validation
    - Task type selection
    - Load balancing settings (weight, max concurrent)
    - Custom metadata (JSON)
    
    On successful enrollment, redirects to the servers list.
    
    Returns:
        Server enrollment HTML page
    """
    file_path = UI_DIR / "pages" / "server-enroll.html"
    return FileResponse(file_path, media_type="text/html")


@router.get("/ui/servers/edit/{server_id}", response_class=FileResponse)
async def ui_server_edit(server_id: str):
    """Serve the server edit form (proxy mode only).
    
    This page loads existing server configuration and allows editing:
    - Base URL, task types, name
    - Weight and max concurrent tasks
    - Custom metadata
    - Form pre-populated with current values
    
    Note: Server ID cannot be changed after enrollment.
    
    Args:
        server_id: The server identifier
    
    Returns:
        Server edit HTML page (same as enroll, but loads existing data)
    """
    file_path = UI_DIR / "pages" / "server-enroll.html"
    return FileResponse(file_path, media_type="text/html")


@router.get("/ui/servers/{server_id}", response_class=FileResponse)
async def ui_server_details(server_id: str):
    """Serve the server details page (proxy mode only).
    
    This page displays complete server configuration and status:
    - Server overview (ID, name, base URL)
    - Health status with last checked timestamp
    - Configuration (weight, max concurrent, task types)
    - Custom metadata (JSON formatted)
    - Actions: Edit, Delete, Manual health check
    
    Args:
        server_id: The server identifier
    
    Returns:
        Server details HTML page
    """
    file_path = UI_DIR / "pages" / "server-details.html"
    return FileResponse(file_path, media_type="text/html")


@router.get("/ui/components/sidebar.html", response_class=FileResponse)
async def ui_component_sidebar():
    """Serve the sidebar component.
    
    This is a reusable component loaded via htmx in all pages.
    It includes:
    - Application header
    - Mode badge (Proxy Mode / Direct Mode)
    - Server selector dropdown (proxy mode only)
    - Navigation menu (mode-aware)
    - Connection status
    - Health status
    
    Returns:
        Sidebar HTML component
    """
    file_path = UI_DIR / "components" / "sidebar.html"
    return FileResponse(file_path, media_type="text/html")


@router.get("/ui/components/api-utils.html", response_class=FileResponse)
async def ui_component_api_utils():
    """Serve the API utilities component.
    
    This component provides shared JavaScript utilities for API communication:
    - buildApiUrl() - Build proxy-aware API URLs
    - apiFetch() - Unified fetch wrapper for client API requests
    - adminFetch() - Fetch wrapper for admin API requests
    - buildAuthHeaders() - Build authentication headers
    - buildAdminHeaders() - Build admin authentication headers
    - handleApiError() - Parse and throw user-friendly errors
    - isProxyMode() - Check if UI is in proxy mode
    
    Include this component in pages that need to make API calls.
    
    Returns:
        API utilities HTML component (JavaScript only)
    """
    file_path = UI_DIR / "components" / "api-utils.html"
    return FileResponse(file_path, media_type="text/html")


# ============================================================================
# Task Definition Management UI Routes
# ============================================================================


@router.get("/ui/tasks", response_class=FileResponse)
async def ui_tasks():
    """Serve the task definitions list page.
    
    This page provides task definition management:
    - List all deployed task definitions with versions
    - Filter by task ID, name, or status
    - Navigate to upload, details, and versions pages
    - Delete task definitions
    - View deployment status
    
    Returns:
        Tasks list HTML page
    """
    file_path = UI_DIR / "pages" / "tasks.html"
    return FileResponse(file_path, media_type="text/html")


@router.get("/ui/tasks/upload", response_class=FileResponse)
async def ui_task_upload():
    """Serve the task upload page.
    
    This page provides a form to upload new task definitions:
    - Drag-and-drop file upload for zip packages
    - Task ID and version configuration
    - Force redeploy option
    - Progress indicator during deployment
    - Validation feedback
    
    On successful upload, redirects to the task details page.
    
    Returns:
        Task upload HTML page
    """
    file_path = UI_DIR / "pages" / "task-upload.html"
    return FileResponse(file_path, media_type="text/html")


@router.get("/ui/tasks/{task_id}/versions", response_class=FileResponse)
async def ui_task_versions(task_id: str):
    """Serve the task versions list page.
    
    This page displays all deployed versions of a specific task:
    - Version list sorted by semantic version (latest first)
    - Deployment status and timestamps
    - Quick links to details and threads
    - Delete individual versions
    
    Args:
        task_id: The task identifier
    
    Returns:
        Task versions HTML page
    """
    file_path = UI_DIR / "pages" / "task-versions.html"
    return FileResponse(file_path, media_type="text/html")


@router.get("/ui/tasks/{task_id}/{version}", response_class=FileResponse)
async def ui_task_details(task_id: str, version: str):
    """Serve the task details page.
    
    This page displays comprehensive task definition information:
    - Task overview (ID, version, name, description, status)
    - Entry point and deployment paths
    - Capabilities list
    - Input and output schemas
    - Custom metadata
    - Other deployed versions
    - Quick links to create thread and view threads
    
    Args:
        task_id: The task identifier
        version: The task version
    
    Returns:
        Task details HTML page
    """
    file_path = UI_DIR / "pages" / "task-details.html"
    return FileResponse(file_path, media_type="text/html")


@router.get("/ui/components/task-selector.html", response_class=FileResponse)
async def ui_component_task_selector():
    """Serve the task selector component.
    
    This is a reusable component for selecting task definitions:
    - Task dropdown with all available tasks
    - Version dropdown (optional)
    - Auto-populate versions when task changes
    - Task info display
    - Configurable via JavaScript API
    
    Usage:
        1. Include in page
        2. Call initTaskSelector(containerId, options)
    
    Returns:
        Task selector HTML component
    """
    file_path = UI_DIR / "components" / "task-selector.html"
    return FileResponse(file_path, media_type="text/html")


# ============================================================================
# Credentials Management UI Routes
# ============================================================================


@router.get("/ui/credentials", response_class=FileResponse)
async def ui_credentials():
    """Serve the credentials list page.
    
    This page provides credential management:
    - List all stored credentials (without values)
    - Create, edit, and delete credentials
    - View credential usage (which tasks use them)
    - Tags and expiration display
    
    Requires admin API key.
    
    Returns:
        Credentials list HTML page
    """
    file_path = UI_DIR / "pages" / "credentials.html"
    return FileResponse(file_path, media_type="text/html")


@router.get("/ui/credentials/create", response_class=FileResponse)
async def ui_credential_create():
    """Serve the credential creation page.
    
    This page provides a form to create new credentials:
    - Name (unique identifier)
    - Value (secret, encrypted at rest)
    - Description
    - Tags
    - Expiration date (optional)
    
    On successful creation, redirects to the credentials list.
    
    Returns:
        Credential creation HTML page
    """
    file_path = UI_DIR / "pages" / "credential-create.html"
    return FileResponse(file_path, media_type="text/html")


@router.get("/ui/credentials/{name}/edit", response_class=FileResponse)
async def ui_credential_edit(name: str):
    """Serve the credential edit page.
    
    This page loads existing credential configuration and allows editing:
    - Description, tags, expiration
    - Value (enter new value to update)
    - Form pre-populated with current values (except value)
    
    Note: Credential name cannot be changed after creation.
    
    Args:
        name: The credential name
    
    Returns:
        Credential edit HTML page (same as create, but loads existing data)
    """
    file_path = UI_DIR / "pages" / "credential-create.html"
    return FileResponse(file_path, media_type="text/html")


# ============================================================================
# System Settings UI Routes
# ============================================================================


@router.get("/ui/system-settings", response_class=FileResponse)
async def ui_system_settings():
    """Serve the system settings page.
    
    This page provides server-wide configuration:
    - Thread concurrency limits (max concurrent threads)
    - Real-time stats (running, queued)
    - Save settings to database
    
    Requires admin API key and Elasticsearch storage.
    
    Returns:
        System settings HTML page
    """
    file_path = UI_DIR / "pages" / "system-settings.html"
    return FileResponse(file_path, media_type="text/html")


@router.get("/ui/tasks/{task_id}/{version}/config", response_class=FileResponse)
async def ui_task_config(task_id: str, version: str):
    """Serve the task configuration page.
    
    This page allows configuring environment variables and secret mappings
    for a specific task version:
    - Environment variables (non-sensitive configuration)
    - Secret mappings (map task secrets to server credentials)
    - Configuration status display
    
    Args:
        task_id: The task identifier
        version: The task version
    
    Returns:
        Task configuration HTML page
    """
    file_path = UI_DIR / "pages" / "task-config.html"
    return FileResponse(file_path, media_type="text/html")


