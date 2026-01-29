"""Health checker service for monitoring enrolled task servers."""

import asyncio
from datetime import datetime, timezone
from typing import Dict, Optional

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from task_framework.logging import logger
from task_framework.metrics_proxy import proxy_server_health_checks_total
from task_framework.proxy_registry import ServerEntry, ServiceRegistry, TaskTypeGroup


class HealthChecker:
    """Health checker that periodically polls enrolled servers."""

    def __init__(
        self,
        registry: ServiceRegistry,
        default_interval_seconds: int = 10,
        timeout_seconds: int = 5,
    ) -> None:
        """Initialize health checker.

        Args:
            registry: ServiceRegistry instance
            default_interval_seconds: Default polling interval in seconds
            timeout_seconds: HTTP request timeout for health checks
        """
        self.registry = registry
        self.default_interval_seconds = default_interval_seconds
        self.timeout_seconds = timeout_seconds
        self.scheduler: Optional[AsyncIOScheduler] = None
        self._failure_counts: Dict[str, int] = {}  # server_id -> consecutive failures
        self._success_counts: Dict[str, int] = {}  # server_id -> consecutive successes

    def start(self) -> None:
        """Start the health checker scheduler."""
        if self.scheduler is None:
            self.scheduler = AsyncIOScheduler()
            self.scheduler.start()
            # Schedule periodic health checks
            self.scheduler.add_job(
                self._check_all_servers,
                IntervalTrigger(seconds=self.default_interval_seconds),
                id="health_check_all",
                replace_existing=True,
            )
            logger.info("health.checker.started", interval_seconds=self.default_interval_seconds)

    def stop(self) -> None:
        """Stop the health checker scheduler."""
        if self.scheduler is not None:
            self.scheduler.shutdown()
            self.scheduler = None
            logger.info("health.checker.stopped")

    async def _check_all_servers(self) -> None:
        """Check health of all enrolled servers."""
        servers = self.registry.list_servers()
        for server in servers:
            await self._check_server_health(server)

    async def _check_server_health(self, server: ServerEntry) -> None:
        """Check health of a single server.

        Args:
            server: ServerEntry to check
        """
        health_url = f"{server.base_url.rstrip('/')}{server.health_path}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(health_url)
                
            if response.status_code == 200:
                proxy_server_health_checks_total.labels(server_id=server.id, status="success").inc()
                await self._handle_health_success(server)
            else:
                proxy_server_health_checks_total.labels(server_id=server.id, status="failure").inc()
                await self._handle_health_failure(server, f"HTTP {response.status_code}")
                
        except httpx.TimeoutException:
            proxy_server_health_checks_total.labels(server_id=server.id, status="timeout").inc()
            await self._handle_health_failure(server, "timeout")
        except httpx.ConnectError:
            proxy_server_health_checks_total.labels(server_id=server.id, status="connection_error").inc()
            await self._handle_health_failure(server, "connection_error")
        except Exception as e:
            proxy_server_health_checks_total.labels(server_id=server.id, status="error").inc()
            await self._handle_health_failure(server, str(e))

    async def _handle_health_success(self, server: ServerEntry) -> None:
        """Handle successful health check.

        Args:
            server: ServerEntry that passed health check
        """
        # Reset failure count
        self._failure_counts.pop(server.id, None)
        
        # Get task type groups for this server to check recovery threshold
        recovery_threshold = 1  # default
        for task_type in server.task_types:
            group = self.registry.get_task_type_group(task_type)
            if group and "recovery_threshold" in group.health_policy:
                recovery_threshold = max(recovery_threshold, group.health_policy["recovery_threshold"])
        
        # Increment success count
        success_count = self._success_counts.get(server.id, 0) + 1
        self._success_counts[server.id] = success_count
        
        # Update status if recovering or if previously unknown and we have enough successes
        if server.status in ("unhealthy", "unknown") and success_count >= recovery_threshold:
            updates = {
                "status": "healthy",
                "last_checked_at": datetime.now(timezone.utc),
            }
            self.registry.update_server(server.id, updates)
            logger.info(
                "health.check.recovered",
                server_id=server.id,
                success_count=success_count,
            )
        elif server.status == "healthy":
            # Update last_checked_at
            updates = {"last_checked_at": datetime.now(timezone.utc)}
            self.registry.update_server(server.id, updates)
        else:
            # Update last_checked_at even if status unchanged
            updates = {"last_checked_at": datetime.now(timezone.utc)}
            self.registry.update_server(server.id, updates)

    async def _handle_health_failure(self, server: ServerEntry, error: str) -> None:
        """Handle failed health check.

        Args:
            server: ServerEntry that failed health check
            error: Error message
        """
        # Reset success count
        self._success_counts.pop(server.id, None)
        
        # Get task type groups for this server to check failure threshold
        failure_threshold = 1  # default
        for task_type in server.task_types:
            group = self.registry.get_task_type_group(task_type)
            if group and "failure_threshold" in group.health_policy:
                failure_threshold = max(failure_threshold, group.health_policy["failure_threshold"])
        
        # Increment failure count
        failure_count = self._failure_counts.get(server.id, 0) + 1
        self._failure_counts[server.id] = failure_count
        
        # Update status if threshold exceeded
        if server.status != "unhealthy" and failure_count >= failure_threshold:
            updates = {
                "status": "unhealthy",
                "last_checked_at": datetime.now(timezone.utc),
            }
            self.registry.update_server(server.id, updates)
            logger.warning(
                "health.check.failed",
                server_id=server.id,
                error=error,
                failure_count=failure_count,
            )
        else:
            # Update last_checked_at even if status unchanged
            updates = {"last_checked_at": datetime.now(timezone.utc)}
            self.registry.update_server(server.id, updates)

    async def check_server_now(self, server_id: str) -> bool:
        """Manually trigger health check for a specific server.

        Args:
            server_id: Server identifier

        Returns:
            True if healthy, False otherwise
        """
        server = self.registry.get_server(server_id)
        if not server:
            return False
        
        await self._check_server_health(server)
        updated_server = self.registry.get_server(server_id)
        return updated_server.status == "healthy" if updated_server else False

