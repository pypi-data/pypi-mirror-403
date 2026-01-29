"""Proxy server creation and integration."""

import os
from typing import Any, Optional

from fastapi import FastAPI

from task_framework.health import HealthChecker
from task_framework.lb import LoadBalancerFactory
from task_framework.proxy_registry import ServiceRegistry
from task_framework.version import VERSION


def create_proxy_server(
    registry: Optional[ServiceRegistry] = None,
    health_check_interval: int = 10,
    admin_api_keys: Optional[list[str]] = None,
    **options: Any,
) -> FastAPI:
    """Create FastAPI proxy server application.
    
    Args:
        registry: ServiceRegistry instance (creates new if None)
        health_check_interval: Health check interval in seconds
        admin_api_keys: List of admin API keys for authentication
        **options: Additional options
        
    Returns:
        FastAPI application instance configured as proxy server
    """
    # Create registry if not provided
    if registry is None:
        persistence_file = os.getenv("PROXY_REGISTRY_FILE", None)
        registry = ServiceRegistry(persistence_file=persistence_file)
    
    # Create health checker
    health_checker = HealthChecker(
        registry=registry,
        default_interval_seconds=health_check_interval,
    )
    
    # Create FastAPI app
    app = FastAPI(
        title="Task Framework Proxy",
        version=VERSION,
        openapi_version="3.1.0",
        description="Task Framework Proxy Server for forwarding requests to enrolled task servers",
    )
    
    # Store registry and health checker in app state
    app.state.registry = registry
    app.state.health_checker = health_checker
    
    # Register health endpoint FIRST (before proxy router to ensure it takes precedence)
    @app.get("/health")
    async def health_check() -> dict[str, Any]:
        """Proxy health check endpoint."""
        from datetime import datetime, timezone
        
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        
        return {
            "status": "ok",
            "timestamp": timestamp,
            "version": VERSION,
            "type": "proxy",
        }
    
    # Register metrics endpoint (before proxy router)
    @app.get("/metrics")
    async def metrics() -> str:
        """Prometheus metrics endpoint."""
        from prometheus_client import generate_latest
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
            return Response(
                content="# Metrics collection failed\n",
                media_type="text/plain; version=0.0.4; charset=utf-8",
            )
    
    # Register admin API router FIRST (before proxy router to ensure admin routes take precedence)
    # Admin endpoints are proxy-only and should NOT be forwarded to task servers
    from task_framework.api import proxy_admin
    from task_framework.dependencies import set_framework_instance
    from task_framework.framework import TaskFramework
    
    # Create a minimal framework instance for admin auth dependency injection
    # Admin API keys are passed directly to the dependency
    if admin_api_keys:
        # Create a temporary framework instance for dependency injection
        temp_framework = TaskFramework(
            api_keys=["dummy"],  # Not used for admin endpoints
            admin_api_keys=admin_api_keys,
        )
        set_framework_instance(temp_framework)
    
    app.include_router(proxy_admin.router)
    
    # Register discovery API router (public endpoints for server discovery)
    from task_framework.api import proxy_discovery
    
    app.include_router(proxy_discovery.router)
    
    # Register UI router (web interface for proxy management and task operations)
    from task_framework import ui
    
    app.include_router(ui.router)
    
    # Register proxy router LAST (catch-all routes come after all specific routes)
    # This router handles forwarding requests to enrolled task servers
    from task_framework.api import proxy
    
    app.include_router(proxy.router)
    
    # Startup event: Start health checker
    @app.on_event("startup")
    async def start_health_checker():
        """Start health checker on server startup."""
        health_checker.start()
        from task_framework.logging import logger
        logger.info("proxy.server.started", health_check_interval=health_check_interval)
    
    # Shutdown event: Stop health checker
    @app.on_event("shutdown")
    async def stop_health_checker():
        """Stop health checker on server shutdown."""
        health_checker.stop()
        from task_framework.logging import logger
        logger.info("proxy.server.stopped")
    
    return app
