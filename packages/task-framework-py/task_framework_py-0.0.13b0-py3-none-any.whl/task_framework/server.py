"""FastAPI server creation and startup with OpenAPI 3.1.0 specification generation."""

import time
from typing import TYPE_CHECKING, Any, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from task_framework.thread_state import ThreadState
from task_framework.version import VERSION

if TYPE_CHECKING:
    from task_framework.framework import TaskFramework


def create_server(framework: "TaskFramework", port: int = 3000, host: str = "0.0.0.0", **options: Any) -> FastAPI:
    """Create FastAPI server with OpenAPI 3.1.0 specification.

    Args:
        framework: TaskFramework instance
        port: Server port (default: 3000)
        host: Server host (default: 0.0.0.0)
        **options: Additional options

    Returns:
        FastAPI application instance
    """
    # Set framework instance for dependency injection
    from task_framework.dependencies import set_framework_instance

    set_framework_instance(framework)

    # API description for OpenAPI/Swagger documentation
    api_description = """
## API Description

A Python library for building and executing task-based workflows with built-in support for 
scheduling, webhooks, artifact management, and observability.

## Operating Mode

The server supports multiple task definitions deployed dynamically:
- Tasks are deployed as zip packages to `task_definitions/` directory or loaded from source for development
- API calls may require `task_id` query parameter when multiple tasks are registered
- Optional `version` parameter to target specific task version (defaults to latest)

## Development Mode

Start the server with `--dev-task` to load a task directly from source:
```bash
task-framework serve --dev-task /path/to/my-task/
```

## Authentication

Most endpoints require authentication via the `X-API-Key` header:
- **Regular API keys**: Require `user_id` and `app_id` metadata (query params or headers)
- **Admin API keys**: Full access to all endpoints including `/admin/*` routes

**Public endpoints** (no authentication required):
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `GET /task/metadata` - Task metadata discovery

## Error Handling

All errors follow [RFC 7807](https://tools.ietf.org/html/rfc7807) Problem Details format.
"""

    # OpenAPI tags for better documentation organization
    openapi_tags = [
        {
            "name": "health",
            "description": "Health check and monitoring endpoints",
        },
        {
            "name": "threads",
            "description": "Thread execution management. Create, list, stop, and retry task executions.",
        },
        {
            "name": "artifacts",
            "description": "Artifact management. Query, download, archive, and delete task artifacts.",
        },
        {
            "name": "files",
            "description": "File storage operations. Upload and download files.",
        },
        {
            "name": "schedules",
            "description": "Schedule management. Create and manage recurring task executions.",
        },
        {
            "name": "runs",
            "description": "Run management. View execution runs within schedules.",
        },
        {
            "name": "webhooks",
            "description": "Webhook configuration and delivery. Subscribe to task events.",
        },
        {
            "name": "admin-tasks",
            "description": "**Admin only.** Task definition management. Deploy, list, and undeploy task packages.",
        },
        {
            "name": "admin-credentials",
            "description": "**Admin only.** Credentials and task configuration management. Manage server secrets and task-specific config.",
        },
        {
            "name": "metadata",
            "description": "Task metadata discovery. Get task capabilities and schema information.",
        },
    ]

    app = FastAPI(
        title="Task Framework API",
        version=VERSION,
        openapi_version="3.1.0",
        description=api_description,
        openapi_tags=openapi_tags,
        license_info={
            "name": "MIT",
            "identifier": "MIT",
        },
        contact={
            "name": "Task Framework",
        },
    )

    # Add middleware for API request duration tracking
    @app.middleware("http")
    async def track_api_request_duration(request: Request, call_next):
        """Middleware to track API request duration."""
        import asyncio
        
        # Skip tracking for /metrics, /health, and /ui endpoints
        if request.url.path in ["/metrics", "/health"] or request.url.path.startswith("/ui"):
            return await call_next(request)
        
        start_time = time.time()
        try:
            response = await call_next(request)
        except asyncio.CancelledError:
            # Client disconnected, don't track this as an error
            raise
        duration_seconds = time.time() - start_time
        
        # Track duration metric
        from task_framework.metrics import api_request_duration_seconds
        
        status_code = str(response.status_code)
        api_request_duration_seconds.labels(
            method=request.method,
            endpoint=str(request.url.path),
            status=status_code,
        ).observe(duration_seconds)
        
        return response

    @app.get("/health", tags=["health"])
    async def health_check() -> Dict[str, Any]:
        """Health check endpoint.
        
        Returns:
            - 200 OK with status: "ok" if all required components are healthy
            - 503 Service Unavailable if required components fail (library not initialized or task function not registered)
            
        Required components:
            - Library initialized
            - Task function registered
            
        Optional components (reported but don't cause 503):
            - Database (if configured)
            - File storage (if configured)
            - Scheduler (if configured)
        """
        from datetime import datetime, timezone
        import asyncio
        
        # Check required components first
        if not framework._initialized:
            # Format timestamp with millisecond precision (ISO 8601)
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unavailable",
                    "timestamp": timestamp,
                    "version": VERSION,
                    "reason": "Library not initialized",
                },
            )
        # Check if any tasks are registered
        if framework.task_registry.count() == 0:
            # No tasks registered - this is fine during startup but should eventually have tasks
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
            return {
                "status": "ok",
                "timestamp": timestamp,
                "version": VERSION,
                "warning": "No tasks registered",
            }

        # Format timestamp with millisecond precision (ISO 8601)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        health_status: Dict[str, Any] = {
            "status": "ok",
            "timestamp": timestamp,
            "version": VERSION,
        }
        
        # Check optional components with 5ms timeout each
        timeout_seconds = 0.005  # 5ms timeout per component
        
        # Check database (optional)
        if framework.database is not None:
            try:
                # Lightweight connectivity check with timeout
                async def check_database():
                    # Simple check - try to access database connection or status
                    if hasattr(framework.database, 'check_connection'):
                        return await framework.database.check_connection()
                    return True
                
                await asyncio.wait_for(check_database(), timeout=timeout_seconds)
                health_status["database"] = "available"
            except asyncio.TimeoutError:
                health_status["database"] = "timeout"
            except Exception:
                health_status["database"] = "unavailable"
        else:
            health_status["database"] = "not_configured"
        
        # Check file storage (optional)
        if framework.file_storage is not None:
            try:
                # Lightweight connectivity check with timeout
                async def check_file_storage():
                    # Simple check - try to access storage status
                    if hasattr(framework.file_storage, 'check_connection'):
                        return await framework.file_storage.check_connection()
                    return True
                
                await asyncio.wait_for(check_file_storage(), timeout=timeout_seconds)
                health_status["file_storage"] = "available"
            except asyncio.TimeoutError:
                health_status["file_storage"] = "timeout"
            except Exception:
                health_status["file_storage"] = "unavailable"
        else:
            health_status["file_storage"] = "not_configured"
        
        # Check scheduler (optional)
        if framework.scheduler is not None:
            try:
                # Lightweight status check with timeout
                async def check_scheduler():
                    # Check if scheduler is running
                    if hasattr(framework.scheduler, 'is_running'):
                        return framework.scheduler.is_running()
                    return True
                
                await asyncio.wait_for(check_scheduler(), timeout=timeout_seconds)
                if hasattr(framework.scheduler, 'is_running'):
                    health_status["scheduler"] = "running" if framework.scheduler.is_running() else "stopped"
                else:
                    health_status["scheduler"] = "available"
            except asyncio.TimeoutError:
                health_status["scheduler"] = "timeout"
            except Exception:
                health_status["scheduler"] = "unavailable"
        else:
            health_status["scheduler"] = "not_configured"

        return health_status

    @app.get("/metrics", tags=["health"])
    async def metrics() -> str:
        """Prometheus metrics endpoint."""
        from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
        from fastapi.responses import Response

        from task_framework.logging import logger

        try:
            content = generate_latest()
            return Response(
                content=content,
                media_type="text/plain; version=0.0.4; charset=utf-8",
            )
        except Exception as e:
            logger.error("metrics.collection.failed", error=str(e), exc_info=True)
            # Return empty valid Prometheus format (no metrics)
            return Response(
                content="# Metrics collection failed\n",
                media_type="text/plain; version=0.0.4; charset=utf-8",
            )

    # Register thread management API routes
    from task_framework.api import threads
    
    # Import artifacts module to register /threads/{thread_id}/artifacts endpoint
    # This must happen before including the router
    from task_framework.api import artifacts
    
    app.include_router(threads.router)

    # Register artifact management API routes
    app.include_router(artifacts.router)

    # Register metadata endpoint for service discovery
    from task_framework.api import metadata
    app.include_router(metadata.router)

    # Register file storage API routes
    from task_framework.api import files
    
    app.include_router(files.router)
    app.include_router(files.uploads_router)

    # Register schedule management API routes
    from task_framework.api import schedules
    
    app.include_router(schedules.router)

    # Register run management API routes
    from task_framework.api import runs
    
    app.include_router(runs.router)

    # Register webhook API routes
    from task_framework.api import webhooks
    
    app.include_router(webhooks.router)

    # Register admin task management API routes
    from task_framework.api import admin_tasks
    
    app.include_router(admin_tasks.router)

    # Register admin credentials and task configuration API routes
    from task_framework.api import credentials as credentials_api
    
    app.include_router(credentials_api.router)

    # Register admin settings API routes
    from task_framework.api import settings as settings_api
    
    app.include_router(settings_api.router)

    # Startup event: Enable multi-task mode and discover task definitions
    @app.on_event("startup")
    async def discover_tasks_on_startup():
        """Discover and deploy task definitions from task_definitions directory."""
        from task_framework.logging import logger
        
        try:
            # Enable multi-task mode and perform launch-time discovery
            # This will:
            # 1. Load deployment tracker state
            # 2. Reload any previously deployed tasks
            # 3. Scan for new zip files and deploy them
            await framework.enable_multi_task_mode()
            
            logger.info(
                "server.startup.multi_task_mode_enabled",
                tasks_registered=framework.task_registry.count(),
            )
        except Exception as e:
            logger.error(
                "server.startup.task_discovery_failed",
                error=str(e),
                exc_info=True,
            )
            # Don't fail startup if task discovery fails - server should still start
    
    # Startup event: Load registry from file
    @app.on_event("startup")
    async def load_registry_from_file():
        """Load task registry from file for multi-worker consistency."""
        from task_framework.logging import logger
        
        try:
            # Load registry state from file (if exists)
            await framework.task_registry.ensure_loaded()
            
            logger.info(
                "server.startup.registry_loaded",
                task_count=framework.task_registry.count(),
            )
        except Exception as e:
            logger.error(
                "server.startup.registry_load_failed",
                error=str(e),
                exc_info=True,
            )
            # Don't fail startup if load fails - will reload on first request
    
    # Startup event: Restore metrics and load active schedules into scheduler
    @app.on_event("startup")
    async def load_schedules_on_startup():
        """Load all active schedules from database into APScheduler on server startup."""
        try:
            from task_framework.services.scheduler_service import ScheduleService
            from task_framework.services.run_service import RunService
            from task_framework.services.thread_service import ThreadService
            from task_framework.repositories.file_db import FileDatabase
            from task_framework.repositories.file_idempotency import FileIdempotencyStore
            from task_framework.scheduler.scheduler import Scheduler
            
            # Use the same database instance as the framework
            database = framework.database 
            
            # Restore thread metrics from database (ensures metrics persist across restarts)
            if database:
                try:
                    from task_framework.utils.metrics_helpers import restore_thread_metrics_from_db
                    await restore_thread_metrics_from_db(database)
                except Exception as e:
                    from task_framework.logging import logger
                    logger.warning(
                        "server.startup.metrics_restore_failed",
                        error=str(e),
                        exc_info=True,
                    )
                    # Don't fail startup if metrics restoration fails
            
            # Get or create scheduler (use framework's scheduler if available)
            scheduler = framework.scheduler
            if scheduler is None:
                scheduler = Scheduler()
            
            # Create services needed for schedule loading
            idempotency_store = FileIdempotencyStore(database=database)
            thread_service = ThreadService(
                database=database,
                idempotency_store=idempotency_store,
                execution_engine=framework.execution_engine,
            )
            
            run_service = RunService(
                database=database,
                thread_service=thread_service,
            )
            
            schedule_service = ScheduleService(
                database=database,
                scheduler=scheduler,
                run_service=run_service,
                framework=framework,
            )
            
            # Load all active schedules
            loaded_count = await schedule_service.load_active_schedules()
            
            from task_framework.logging import logger
            logger.info(
                "server.startup.schedules_loaded",
                count=loaded_count,
            )
        except Exception as e:
            from task_framework.logging import logger
            logger.error(
                "server.startup.schedule_loading_failed",
                error=str(e),
                exc_info=True,
            )
            # Don't fail startup if schedule loading fails - server should still start
    
    # Startup event: Recover orphaned queued threads from previous server sessions
    @app.on_event("startup")
    async def recover_queued_threads():
        """Recover and resume execution of orphaned queued threads.
        
        Finds threads with state='queued' that were left from previous server sessions
        and resumes their execution.
        """
        try:
            from task_framework.logging import logger
            import asyncio
            
            database = framework.database
            if not database:
                return
            
            # Find all queued threads
            queued_threads = await database.query_threads({"state": "queued", "limit": 100})
            
            if not queued_threads:
                logger.info("server.startup.no_queued_threads")
                return
            
            logger.info(
                "server.startup.recovering_queued_threads",
                count=len(queued_threads),
            )
            
            # Get task registry
            if not hasattr(framework, 'task_registry') or framework.task_registry is None:
                logger.warning("server.startup.no_task_registry_for_recovery")
                return
            
            recovered = 0
            for thread in queued_threads:
                try:
                    # Get task_id and version from thread metadata
                    metadata = thread.metadata or {}
                    task_id = metadata.get("task_id")
                    task_version = metadata.get("task_version")
                    
                    if not task_id:
                        logger.warning(
                            "server.startup.thread_no_task_id",
                            thread_id=thread.id,
                        )
                        continue
                    
                    # Look up task definition
                    task_def = framework.task_registry.get(task_id, task_version)
                    if not task_def:
                        task_def = framework.task_registry.get_latest_version(task_id)
                    
                    if not task_def:
                        logger.warning(
                            "server.startup.task_not_found_for_recovery",
                            thread_id=thread.id,
                            task_id=task_id,
                        )
                        continue
                    
                    # Get task function from task definition
                    from task_framework.utils.metrics_helpers import update_thread_state_gauge
                    
                    task_function = task_def.get_task_function()
                    
                    if not task_function:
                        logger.warning(
                            "server.startup.task_function_not_found",
                            thread_id=thread.id,
                            task_id=task_id,
                        )
                        continue
                    
                    # Resume execution in background
                    async def _resume_thread(t, tf, td):
                        try:
                            # Wait for concurrency slot
                            if framework.concurrency_manager:
                                await framework.concurrency_manager.wait_for_slot(t.id)
                            
                            # Update state to running
                            t.state = ThreadState.RUNNING
                            await database.update_thread(t)
                            update_thread_state_gauge("queued", "running")
                            
                            # Execute
                            from task_framework.execution import ExecutionEngine
                            engine = framework.execution_engine
                            finished = await engine.execute_task(t, tf, td)
                            await database.update_thread(finished)
                            
                            logger.info(
                                "server.startup.thread_recovered",
                                thread_id=t.id,
                                state=finished.state.value,
                            )
                        except Exception as e:
                            logger.error(
                                "server.startup.thread_recovery_failed",
                                thread_id=t.id,
                                error=str(e),
                            )
                            t.state = ThreadState.FAILED
                            await database.update_thread(t)
                        finally:
                            if framework.concurrency_manager:
                                await framework.concurrency_manager.release_slot(t.id)
                    
                    asyncio.create_task(_resume_thread(thread, task_function, task_def))
                    recovered += 1
                    
                except Exception as e:
                    logger.error(
                        "server.startup.thread_recovery_error",
                        thread_id=thread.id,
                        error=str(e),
                    )
            
            logger.info(
                "server.startup.recovery_complete",
                recovered=recovered,
                total=len(queued_threads),
            )
            
        except Exception as e:
            from task_framework.logging import logger
            logger.error(
                "server.startup.queue_recovery_failed",
                error=str(e),
                exc_info=True,
            )
            # Don't fail startup if recovery fails
    
    # Register UI routes (public endpoint)
    from task_framework.ui import router as ui_router
    
    app.include_router(ui_router)

    return app

