"""Registry synchronization service for multi-worker mode.

Provides file-based synchronization to keep TaskRegistry consistent
across multiple uvicorn worker processes.
"""

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import aiofiles
from aiofiles import os as aios

from task_framework.logging import logger

if TYPE_CHECKING:
    from task_framework.framework import TaskFramework


class RegistrySyncService:
    """Service for synchronizing TaskRegistry across multiple workers.
    
    Uses a file-based sync marker to detect when the registry has been
    modified by another worker and triggers a reload.
    
    The sync file contains:
    - version: Incremented on each deploy/undeploy
    - updated_at: Timestamp of last modification
    """
    
    def __init__(
        self,
        data_dir: str,
        sync_interval: float = 5.0,
    ) -> None:
        """Initialize RegistrySyncService.
        
        Args:
            data_dir: Base data directory
            sync_interval: Seconds between sync checks (default: 5.0)
        """
        self.data_dir = Path(data_dir)
        self.sync_file = self.data_dir / "registry_sync.json"
        self.sync_interval = sync_interval
        
        # Local cache of last known version
        self._local_version: int = 0
        self._sync_task: Optional[asyncio.Task] = None
        self._framework: Optional["TaskFramework"] = None
        self._running = False
    
    def set_framework(self, framework: "TaskFramework") -> None:
        """Set the framework reference for triggering reloads.
        
        Args:
            framework: TaskFramework instance
        """
        self._framework = framework
    
    async def get_version(self) -> int:
        """Read current sync version from file.
        
        Returns:
            Current version number, or 0 if file doesn't exist
        """
        try:
            if not self.sync_file.exists():
                return 0
            
            async with aiofiles.open(self.sync_file, "r") as f:
                content = await f.read()
                data = json.loads(content)
                return data.get("version", 0)
        except Exception as e:
            logger.warning(
                "registry_sync.read_failed",
                error=str(e),
            )
            return 0
    
    async def increment_version(self) -> int:
        """Increment sync version and write to file.
        
        Called after successful deploy/undeploy operations.
        
        Returns:
            New version number
        """
        try:
            # Ensure directory exists
            await aios.makedirs(self.data_dir, exist_ok=True)
            
            # Read current version
            current_version = await self.get_version()
            new_version = current_version + 1
            
            # Write new version
            data = {
                "version": new_version,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            
            # Write atomically
            temp_file = self.sync_file.with_suffix(".tmp")
            async with aiofiles.open(temp_file, "w") as f:
                await f.write(json.dumps(data, indent=2))
            
            # Atomic rename
            await aios.rename(str(temp_file), str(self.sync_file))
            
            # Update local cache
            self._local_version = new_version
            
            logger.info(
                "registry_sync.version_incremented",
                old_version=current_version,
                new_version=new_version,
            )
            
            return new_version
            
        except Exception as e:
            logger.error(
                "registry_sync.write_failed",
                error=str(e),
                exc_info=True,
            )
            raise
    
    async def check_and_reload(self) -> bool:
        """Check if registry needs reload and trigger if needed.
        
        Returns:
            True if reload was triggered, False otherwise
        """
        try:
            file_version = await self.get_version()
            
            if file_version > self._local_version:
                logger.info(
                    "registry_sync.reload_triggered",
                    local_version=self._local_version,
                    file_version=file_version,
                )
                
                # Update local version first to prevent repeated reloads
                self._local_version = file_version
                
                # Trigger reload
                if self._framework and self._framework._task_deployment_service:
                    await self._framework._task_deployment_service.reload_deployed_tasks()
                    return True
                else:
                    logger.warning("registry_sync.no_framework")
                    
            return False
            
        except Exception as e:
            logger.error(
                "registry_sync.check_failed",
                error=str(e),
            )
            return False
    
    async def _sync_loop(self) -> None:
        """Background loop that periodically checks for registry updates."""
        logger.info(
            "registry_sync.started",
            interval=self.sync_interval,
        )
        
        while self._running:
            try:
                await asyncio.sleep(self.sync_interval)
                
                if self._running:  # Check again after sleep
                    await self.check_and_reload()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    "registry_sync.loop_error",
                    error=str(e),
                )
        
        logger.info("registry_sync.stopped")
    
    async def start(self) -> None:
        """Start the background sync task."""
        if self._running:
            return
        
        # Initialize local version from file
        self._local_version = await self.get_version()
        
        self._running = True
        self._sync_task = asyncio.create_task(self._sync_loop())
        
        logger.info(
            "registry_sync.task_started",
            initial_version=self._local_version,
        )
    
    async def stop(self) -> None:
        """Stop the background sync task."""
        if not self._running:
            return
        
        self._running = False
        
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
            self._sync_task = None
        
        logger.info("registry_sync.task_stopped")
    
    async def initialize_version(self) -> None:
        """Initialize local version from file without starting sync loop.
        
        Used during startup to set the initial version before the sync
        loop starts, ensuring we don't immediately trigger a reload.
        """
        self._local_version = await self.get_version()
        logger.info(
            "registry_sync.initialized",
            version=self._local_version,
        )
