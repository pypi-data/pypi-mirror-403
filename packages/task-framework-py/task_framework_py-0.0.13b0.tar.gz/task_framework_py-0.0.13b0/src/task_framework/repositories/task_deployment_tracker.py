"""Task deployment tracker for idempotent deployment management."""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import aiofiles
from aiofiles import os as aios

from task_framework.interfaces.deployment_tracker_store import DeploymentTrackerStore
from task_framework.logging import logger
from task_framework.models.task_definition import DeploymentRecord


class TaskDeploymentTracker(DeploymentTrackerStore):
    """Tracks deployed task definitions to prevent redeployment on server restart.
    
    Implements DeploymentTrackerStore interface with file-based persistence.
    Persists deployment state to a JSON file and provides methods to check
    if a zip file has already been deployed.
    """
    
    def __init__(self, base_path: str = ".", persistence_file: Optional[str] = None) -> None:
        """Initialize TaskDeploymentTracker.
        
        Args:
            base_path: Base directory for the server
            persistence_file: Path to the persistence file (defaults to {base_path}/task_deployments.json)
        """
        self.base_path = Path(base_path)
        self.persistence_file = Path(persistence_file) if persistence_file else self.base_path / "task_deployments.json"
        
        # In-memory cache of deployments, keyed by zip_path
        self._deployments: Dict[str, DeploymentRecord] = {}
        # Also index by zip_hash for quick lookup
        self._hash_index: Dict[str, str] = {}  # hash -> zip_path
        
        self._loaded = False
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            SHA-256 hash prefixed with 'sha256:'
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return f"sha256:{sha256_hash.hexdigest()}"
    
    async def _calculate_file_hash_async(self, file_path: str) -> str:
        """Calculate SHA-256 hash of a file asynchronously.
        
        Args:
            file_path: Path to the file
            
        Returns:
            SHA-256 hash prefixed with 'sha256:'
        """
        sha256_hash = hashlib.sha256()
        async with aiofiles.open(file_path, "rb") as f:
            while True:
                byte_block = await f.read(4096)
                if not byte_block:
                    break
                sha256_hash.update(byte_block)
        return f"sha256:{sha256_hash.hexdigest()}"
    
    async def _ensure_directory(self) -> None:
        """Ensure the parent directory of the persistence file exists."""
        parent_dir = self.persistence_file.parent
        await aios.makedirs(parent_dir, exist_ok=True)
    
    async def load(self) -> None:
        """Load deployment state from persistence file.
        
        Loads all deployment records from the JSON file into memory.
        If the file doesn't exist, starts with an empty state.
        """
        if self._loaded:
            return
        
        if not await aios.path.exists(self.persistence_file):
            self._loaded = True
            logger.info(
                "task_deployment_tracker.no_persistence_file",
                persistence_file=str(self.persistence_file),
            )
            return
        
        try:
            async with aiofiles.open(self.persistence_file, "r") as f:
                content = await f.read()
                data = json.loads(content)
            
            # Load deployments
            self._deployments = {}
            self._hash_index = {}
            for record_data in data.get("deployments", []):
                # Parse datetime strings
                if "deployed_at" in record_data and record_data["deployed_at"]:
                    dt_str = record_data["deployed_at"]
                    # Only replace Z if at end (not if already has timezone)
                    # Handle double timezone suffixes (e.g. +00:00+00:00)
                    if dt_str.count("+00:00") > 1:
                        dt_str = dt_str.replace("+00:00", "", dt_str.count("+00:00") - 1)
                    
                    # Handle Z suffix
                    if dt_str.endswith("Z"):
                        dt_str = dt_str[:-1] + "+00:00"
                        
                    try:
                        record_data["deployed_at"] = datetime.fromisoformat(dt_str)
                    except ValueError:
                        # Fallback for corrupted dates
                        logger.warning(f"Invalid date format: {dt_str}, using current time")
                        record_data["deployed_at"] = datetime.now(timezone.utc)
                record = DeploymentRecord(**record_data)
                self._deployments[record.zip_path] = record
                self._hash_index[record.zip_hash] = record.zip_path
            
            self._loaded = True
            logger.info(
                "task_deployment_tracker.loaded",
                persistence_file=str(self.persistence_file),
                deployments_count=len(self._deployments),
            )
            
        except json.JSONDecodeError as e:
            logger.error(
                "task_deployment_tracker.load_failed",
                persistence_file=str(self.persistence_file),
                error=str(e),
            )
            # Don't raise - start with empty state
            self._deployments = {}
            self._hash_index = {}
            self._loaded = True
        except Exception as e:
            logger.error(
                "task_deployment_tracker.load_failed",
                persistence_file=str(self.persistence_file),
                error=str(e),
                exc_info=True,
            )
            self._deployments = {}
            self._hash_index = {}
            self._loaded = True
    
    async def save(self) -> None:
        """Save deployment state to persistence file.
        
        Writes all deployment records to the JSON file atomically.
        """
        await self._ensure_directory()
        
        # Prepare data for serialization
        deployments_data = []
        for record in self._deployments.values():
            record_dict = record.model_dump()
            # Convert datetime to ISO format string
            if record_dict.get("deployed_at"):
                record_dict["deployed_at"] = record_dict["deployed_at"].isoformat()
            deployments_data.append(record_dict)
        
        data = {
            "deployments": deployments_data,
        }
        
        # Write atomically using a temp file
        temp_file = self.persistence_file.with_suffix(".tmp")
        try:
            async with aiofiles.open(temp_file, "w") as f:
                await f.write(json.dumps(data, indent=2))
            
            # Atomic rename
            os.replace(temp_file, self.persistence_file)
            
            logger.debug(
                "task_deployment_tracker.saved",
                persistence_file=str(self.persistence_file),
                deployments_count=len(self._deployments),
            )
        except Exception as e:
            logger.error(
                "task_deployment_tracker.save_failed",
                persistence_file=str(self.persistence_file),
                error=str(e),
                exc_info=True,
            )
            # Clean up temp file if it exists
            if await aios.path.exists(temp_file):
                await aios.remove(temp_file)
            raise
    
    async def get_by_path(self, zip_path: str) -> Optional[DeploymentRecord]:
        """Get deployment record by zip file path.
        
        Args:
            zip_path: Full path to the zip file
            
        Returns:
            DeploymentRecord if found, None otherwise
        """
        await self.load()
        return self._deployments.get(zip_path)
    
    async def get_by_hash(self, zip_hash: str) -> Optional[DeploymentRecord]:
        """Get deployment record by zip file hash.
        
        Args:
            zip_hash: SHA-256 hash of the zip file
            
        Returns:
            DeploymentRecord if found, None otherwise
        """
        await self.load()
        zip_path = self._hash_index.get(zip_hash)
        if zip_path:
            return self._deployments.get(zip_path)
        return None
    
    async def is_deployed(self, zip_path: str) -> bool:
        """Check if a zip file has already been successfully deployed.
        
        Args:
            zip_path: Full path to the zip file
            
        Returns:
            True if the zip file has been deployed successfully
        """
        record = await self.get_by_path(zip_path)
        if record and record.is_deployed:
            return True
        
        # Also check by hash in case the file was moved/renamed
        if await aios.path.exists(zip_path):
            zip_hash = await self._calculate_file_hash_async(zip_path)
            record = await self.get_by_hash(zip_hash)
            if record and record.is_deployed:
                return True
        
        return False
    
    async def record_deployment(
        self,
        zip_path: str,
        task_id: str,
        version: str,
        status: str = "deployed",
        error: Optional[str] = None,
    ) -> DeploymentRecord:
        """Record a deployment attempt.
        
        Args:
            zip_path: Full path to the zip file
            task_id: Task identifier
            version: Task version
            status: Deployment status ('deployed', 'failed', 'pending')
            error: Error message if status is 'failed'
            
        Returns:
            The created DeploymentRecord
        """
        await self.load()
        
        # Calculate hash
        zip_hash = await self._calculate_file_hash_async(zip_path)
        
        record = DeploymentRecord(
            zip_path=zip_path,
            zip_hash=zip_hash,
            task_id=task_id,
            version=version,
            deployed_at=datetime.now(timezone.utc),
            status=status,
            error=error,
        )
        
        # Update in-memory state
        self._deployments[zip_path] = record
        self._hash_index[zip_hash] = zip_path
        
        # Persist to file
        await self.save()
        
        logger.info(
            "task_deployment_tracker.recorded",
            zip_path=zip_path,
            task_id=task_id,
            version=version,
            status=status,
        )
        
        return record
    
    async def mark_deployed(self, zip_path: str) -> Optional[DeploymentRecord]:
        """Mark a pending deployment as successfully deployed.
        
        Args:
            zip_path: Full path to the zip file
            
        Returns:
            Updated DeploymentRecord or None if not found
        """
        record = await self.get_by_path(zip_path)
        if not record:
            return None
        
        # Create updated record
        updated_record = DeploymentRecord(
            zip_path=record.zip_path,
            zip_hash=record.zip_hash,
            task_id=record.task_id,
            version=record.version,
            deployed_at=datetime.now(timezone.utc),
            status="deployed",
            error=None,
        )
        
        self._deployments[zip_path] = updated_record
        await self.save()
        
        return updated_record
    
    async def mark_failed(self, zip_path: str, error: str) -> Optional[DeploymentRecord]:
        """Mark a deployment as failed.
        
        Args:
            zip_path: Full path to the zip file
            error: Error message
            
        Returns:
            Updated DeploymentRecord or None if not found
        """
        record = await self.get_by_path(zip_path)
        if not record:
            return None
        
        # Create updated record
        updated_record = DeploymentRecord(
            zip_path=record.zip_path,
            zip_hash=record.zip_hash,
            task_id=record.task_id,
            version=record.version,
            deployed_at=datetime.now(timezone.utc),
            status="failed",
            error=error,
        )
        
        self._deployments[zip_path] = updated_record
        await self.save()
        
        return updated_record
    
    async def remove(self, zip_path: str) -> bool:
        """Remove a deployment record.
        
        Args:
            zip_path: Full path to the zip file
            
        Returns:
            True if removed, False if not found
        """
        await self.load()
        
        if zip_path not in self._deployments:
            return False
        
        record = self._deployments.pop(zip_path)
        if record.zip_hash in self._hash_index:
            del self._hash_index[record.zip_hash]
        
        await self.save()
        
        logger.info(
            "task_deployment_tracker.removed",
            zip_path=zip_path,
            task_id=record.task_id,
            version=record.version,
        )
        
        return True
    
    async def list_all(self) -> List[DeploymentRecord]:
        """List all deployment records.
        
        Returns:
            List of all DeploymentRecord objects
        """
        await self.load()
        return list(self._deployments.values())
    
    async def list_deployed(self) -> List[DeploymentRecord]:
        """List all successfully deployed records.
        
        Returns:
            List of DeploymentRecord objects with status 'deployed'
        """
        await self.load()
        return [r for r in self._deployments.values() if r.is_deployed]
    
    async def get_by_task(self, task_id: str, version: Optional[str] = None) -> List[DeploymentRecord]:
        """Get deployment records by task ID and optional version.
        
        Args:
            task_id: Task identifier
            version: Optional version filter
            
        Returns:
            List of matching DeploymentRecord objects
        """
        await self.load()
        records = [r for r in self._deployments.values() if r.task_id == task_id]
        if version:
            records = [r for r in records if r.version == version]
        return records
    
    async def get_deployment(self, zip_path: str) -> Optional[DeploymentRecord]:
        """Get deployment record for a zip file.
        
        This is an alias for get_by_path() to implement the DeploymentTrackerStore interface.
        
        Args:
            zip_path: Path to the zip file
            
        Returns:
            DeploymentRecord if found, None otherwise
        """
        return await self.get_by_path(zip_path)
    
    async def clear(self) -> None:
        """Clear all deployment records."""
        await self.load()
        self._deployments.clear()
        self._hash_index.clear()
        await self.save()
        logger.info("task_deployment_tracker.cleared")
