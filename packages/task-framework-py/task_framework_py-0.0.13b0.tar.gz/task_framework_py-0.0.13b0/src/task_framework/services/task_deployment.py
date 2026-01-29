"""Task deployment service for deploying task definitions from zip files."""

import json
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Tuple

from task_framework.logging import logger
from task_framework.models.task_definition import TaskDefinition, TaskMetadata
from task_framework.repositories.task_deployment_tracker import TaskDeploymentTracker
from task_framework.repositories.task_storage import TaskStorage
from task_framework.services.task_loader import TaskLoader, TaskLoaderError
from task_framework.services.task_registry import TaskRegistry
from task_framework.utils.task_packaging import TaskPackageValidator, calculate_zip_hash_async

if TYPE_CHECKING:
    from task_framework.services.registry_sync import RegistrySyncService


class TaskDeploymentError(Exception):
    """Exception raised for task deployment errors."""
    pass


class TaskDeploymentService:
    """Service for deploying task definitions from zip files.
    
    Handles the full deployment lifecycle:
    1. Idempotency check via deployment tracker
    2. Zip validation
    3. Extraction and venv creation
    4. Dependency installation
    5. Task function loading
    6. Registration in TaskRegistry
    7. Deployment state tracking
    """
    
    def __init__(
        self,
        task_registry: TaskRegistry,
        task_storage: TaskStorage,
        deployment_tracker: TaskDeploymentTracker,
        task_loader: Optional[TaskLoader] = None,
        registry_sync: Optional["RegistrySyncService"] = None,
    ) -> None:
        """Initialize TaskDeploymentService.
        
        Args:
            task_registry: TaskRegistry for registering loaded tasks
            task_storage: TaskStorage for managing task directories
            deployment_tracker: TaskDeploymentTracker for idempotency
            task_loader: Optional TaskLoader (created if not provided)
            registry_sync: Optional RegistrySyncService for multi-worker sync
        """
        self.task_registry = task_registry
        self.task_storage = task_storage
        self.deployment_tracker = deployment_tracker
        self.task_loader = task_loader or TaskLoader(task_storage)
        self.registry_sync = registry_sync
    
    async def deploy_from_zip(
        self,
        zip_path: str,
        force: bool = False,
    ) -> Tuple[TaskDefinition, bool]:
        """Deploy a task from a zip file.
        
        Args:
            zip_path: Path to the task definition zip file
            force: If True, redeploy even if already deployed
            
        Returns:
            Tuple of (TaskDefinition, was_newly_deployed)
            
        Raises:
            TaskDeploymentError: If deployment fails
        """
        zip_path = Path(zip_path)
        zip_path_str = str(zip_path.absolute())
        
        logger.info(
            "task_deployment.starting",
            zip_path=zip_path_str,
            force=force,
        )
        
        # Check idempotency - is this zip already deployed?
        if not force:
            is_deployed = await self._check_already_deployed(zip_path_str)
            if is_deployed:
                # Already deployed, try to get the task from registry
                task_def = await self._get_deployed_task(zip_path_str)
                if task_def:
                    logger.info(
                        "task_deployment.skipped_already_deployed",
                        zip_path=zip_path_str,
                        task_id=task_def.task_id,
                        version=task_def.version,
                    )
                    return task_def, False
                else:
                    # Task is marked deployed but not in registry - redeploy
                    logger.info(
                        "task_deployment.redeploying_missing_task",
                        zip_path=zip_path_str,
                    )
        
        # Validate the zip package first
        validator = TaskPackageValidator(zip_path_str)
        is_valid, error = validator.validate()
        if not is_valid:
            await self._record_failed_deployment(zip_path_str, error or "Validation failed")
            raise TaskDeploymentError(f"Invalid task package: {error}")
        
        # Get metadata for recording
        try:
            metadata = validator.get_metadata()
            task_id = metadata.name
            version = metadata.version
        except Exception as e:
            await self._record_failed_deployment(zip_path_str, str(e))
            raise TaskDeploymentError(f"Failed to read metadata: {e}")
        
        # Check if task is already registered
        if self.task_registry.is_registered(task_id, version):
            if not force:
                # Already registered - return existing
                existing = self.task_registry.get(task_id, version)
                if existing:
                    logger.info(
                        "task_deployment.skipped_already_registered",
                        zip_path=zip_path_str,
                        task_id=task_id,
                        version=version,
                    )
                    # Update deployment tracker
                    await self.deployment_tracker.record_deployment(
                        zip_path=zip_path_str,
                        task_id=task_id,
                        version=version,
                        status="deployed",
                    )
                    return existing, False
            else:
                # Force redeploy - unregister first
                self.task_registry.unregister(task_id, version)
        
        # Record pending deployment
        await self.deployment_tracker.record_deployment(
            zip_path=zip_path_str,
            task_id=task_id,
            version=version,
            status="pending",
        )
        
        try:
            # Load task (extract, create venv, install deps, load function)
            task_def = await self.task_loader.load_from_zip(zip_path_str)
            
            # Register task and save to file
            await self.task_registry.register_and_save(task_def)
            
            # Record successful deployment
            await self.deployment_tracker.record_deployment(
                zip_path=zip_path_str,
                task_id=task_id,
                version=version,
                status="deployed",
            )
            
            # Save metadata for future loads
            await self._save_task_metadata(task_def, metadata)
            
            logger.info(
                "task_deployment.completed",
                zip_path=zip_path_str,
                task_id=task_id,
                version=version,
            )
            return task_def, True
            
        except TaskLoaderError as e:
            error_msg = str(e)
            await self.deployment_tracker.record_deployment(
                zip_path=zip_path_str,
                task_id=task_id,
                version=version,
                status="failed",
                error=error_msg,
            )
            raise TaskDeploymentError(f"Failed to load task: {error_msg}")
        except Exception as e:
            error_msg = str(e)
            await self.deployment_tracker.record_deployment(
                zip_path=zip_path_str,
                task_id=task_id,
                version=version,
                status="failed",
                error=error_msg,
            )
            raise TaskDeploymentError(f"Deployment failed: {error_msg}")
    
    async def deploy_from_source(self, task_dir: str) -> TaskDefinition:
        """Deploy a task directly from source directory (dev mode).
        
        This method loads a task directly from a source directory without
        packaging it as a zip file. Useful for rapid development iteration.
        
        Unlike deploy_from_zip, this:
        - Does not create isolated venv (uses current Python env)
        - Does not track in deployment tracker
        - Does not require packaging
        
        Args:
            task_dir: Path to the task directory containing task.yaml and source code
            
        Returns:
            Deployed TaskDefinition
            
        Raises:
            TaskDeploymentError: If deployment fails
        """
        import yaml
        
        task_path = Path(task_dir).absolute()
        
        logger.info(
            "task_deployment.dev_mode.starting",
            task_dir=str(task_path),
        )
        
        # Check task.yaml exists
        task_yaml = task_path / "task.yaml"
        if not task_yaml.exists():
            raise TaskDeploymentError(f"task.yaml not found in {task_path}")
        
        # Load task.yaml
        try:
            with open(task_yaml, "r") as f:
                config = yaml.safe_load(f)
        except Exception as e:
            raise TaskDeploymentError(f"Failed to parse task.yaml: {e}")
        
        # Extract required fields
        task_id = config.get("task_id") or config.get("name")
        version = config.get("version", "dev")
        name = config.get("name", task_id)
        description = config.get("description", "")
        entry_point = config.get("entry_point")
        
        if not task_id:
            raise TaskDeploymentError("task.yaml must have task_id or name field")
        if not entry_point:
            raise TaskDeploymentError("task.yaml must have entry_point field")
        
        # Check if already registered
        if self.task_registry.is_registered(task_id, version):
            # Unregister to allow reload
            self.task_registry.unregister(task_id, version)
        
        # Add src/ to Python path if exists
        import sys
        src_path = task_path / "src"
        if src_path.exists():
            src_path_str = str(src_path)
            if src_path_str not in sys.path:
                sys.path.insert(0, src_path_str)
        else:
            # Add task_dir itself
            task_path_str = str(task_path)
            if task_path_str not in sys.path:
                sys.path.insert(0, task_path_str)
        
        # Load task function
        try:
            module_path, function_name = entry_point.rsplit(":", 1)
            import importlib
            module = importlib.import_module(module_path)
            task_function = getattr(module, function_name)
        except Exception as e:
            raise TaskDeploymentError(f"Failed to load task function from {entry_point}: {e}")
        
        # Build schemas if provided
        input_schemas = config.get("input_schemas", [])
        output_schemas = config.get("output_schemas", [])
        requirements = config.get("requirements", [])
        
        # Create TaskMetadata and use from_metadata factory
        from task_framework.models.task_definition import TaskMetadata
        
        metadata = TaskMetadata(
            name=task_id,
            version=version,
            description=description,
            entry_point=entry_point,
            input_schemas=input_schemas,
            output_schemas=output_schemas,
            requirements=requirements,
        )
        
        task_def = TaskDefinition.from_metadata(metadata, task_path)
        task_def.set_task_function(task_function)
        
        # Register task
        await self.task_registry.register_and_save(task_def)
        
        logger.info(
            "task_deployment.dev_mode.completed",
            task_id=task_id,
            version=version,
            task_dir=str(task_path),
        )
        
        return task_def
    
    async def deploy_all_from_folder(
        self,
        folder_path: Optional[str] = None,
    ) -> Tuple[int, int, int]:
        """Deploy all zip files from a folder.
        
        Used for launch-time auto-discovery.
        
        Args:
            folder_path: Path to folder containing zip files.
                        Defaults to task_storage.task_definitions_dir.
            
        Returns:
            Tuple of (deployed_count, skipped_count, failed_count)
        """
        if folder_path:
            zip_files = list(Path(folder_path).glob("*.zip"))
        else:
            zip_files = await self.task_storage.list_zip_files()
        
        if not zip_files:
            logger.info("task_deployment.no_zip_files_found")
            return 0, 0, 0
        
        deployed = 0
        skipped = 0
        failed = 0
        
        for zip_file in zip_files:
            try:
                _, was_new = await self.deploy_from_zip(str(zip_file))
                if was_new:
                    deployed += 1
                else:
                    skipped += 1
            except TaskDeploymentError as e:
                logger.error(
                    "task_deployment.zip_failed",
                    zip_path=str(zip_file),
                    error=str(e),
                )
                failed += 1
            except Exception as e:
                logger.error(
                    "task_deployment.zip_failed",
                    zip_path=str(zip_file),
                    error=str(e),
                    exc_info=True,
                )
                failed += 1
        
        logger.info(
            "task_deployment.folder_completed",
            deployed=deployed,
            skipped=skipped,
            failed=failed,
            total=len(zip_files),
        )
        
        return deployed, skipped, failed
    
    async def reload_deployed_tasks(self) -> Tuple[int, int]:
        """Reload all previously deployed tasks.
        
        Used for server restart to reload tasks from deployment tracker.
        
        Returns:
            Tuple of (loaded_count, failed_count)
        """
        records = await self.deployment_tracker.list_deployed()
        
        if not records:
            logger.info("task_deployment.no_deployed_tasks")
            return 0, 0
        
        loaded = 0
        failed = 0
        
        for record in records:
            try:
                # Check if task is already registered
                if self.task_registry.is_registered(record.task_id, record.version):
                    logger.debug(
                        "task_deployment.already_registered",
                        task_id=record.task_id,
                        version=record.version,
                    )
                    loaded += 1
                    continue
                
                # Try to load from stored metadata
                metadata = await self._load_task_metadata(record.task_id, record.version)
                if metadata:
                    task_def = await self.task_loader.load_existing(
                        record.task_id,
                        record.version,
                        metadata,
                        deployed_at=record.deployed_at,
                    )
                    await self.task_registry.register_and_save(task_def)
                    loaded += 1
                else:
                    # No metadata, try to redeploy from zip
                    if Path(record.zip_path).exists():
                        await self.deploy_from_zip(record.zip_path, force=True)
                        loaded += 1
                    else:
                        logger.warning(
                            "task_deployment.zip_missing",
                            zip_path=record.zip_path,
                            task_id=record.task_id,
                            version=record.version,
                        )
                        failed += 1
                        
            except Exception as e:
                logger.error(
                    "task_deployment.reload_failed",
                    task_id=record.task_id,
                    version=record.version,
                    error=str(e),
                )
                failed += 1
        
        logger.info(
            "task_deployment.reload_completed",
            loaded=loaded,
            failed=failed,
            total=len(records),
        )
        
        return loaded, failed
    
    async def undeploy(self, task_id: str, version: Optional[str] = None) -> List[str]:
        """Undeploy a task.
        
        Args:
            task_id: Task identifier
            version: Optional version. If None, undeploys all versions.
            
        Returns:
            List of undeployed full_ids
        """
        undeployed = []
        
        # Unregister from registry and save to file
        task_defs = await self.task_registry.unregister_and_save(task_id, version)
        
        for task_def in task_defs:
            # Unload task
            await self.task_loader.unload_task(task_def)
            
            # Delete storage
            await self.task_storage.delete_task(task_def.task_id, task_def.version)
            
            # Remove from deployment tracker and delete zip file
            if task_def.zip_path:
                await self.deployment_tracker.remove(task_def.zip_path)
                
                # Delete the zip file to prevent re-deployment on restart
                zip_file = Path(task_def.zip_path)
                if zip_file.exists():
                    try:
                        zip_file.unlink()
                        logger.info(
                            "task_deployment.zip_deleted",
                            zip_path=str(zip_file),
                        )
                    except Exception as e:
                        logger.warning(
                            "task_deployment.zip_delete_failed",
                            zip_path=str(zip_file),
                            error=str(e),
                        )
            
            undeployed.append(task_def.full_id)
            
            logger.info(
                "task_deployment.undeployed",
                task_id=task_def.task_id,
                version=task_def.version,
            )
        
        return undeployed
    
    async def _check_already_deployed(self, zip_path: str) -> bool:
        """Check if a zip file has already been deployed.
        
        Args:
            zip_path: Path to the zip file
            
        Returns:
            True if already deployed successfully
        """
        return await self.deployment_tracker.is_deployed(zip_path)
    
    async def _get_deployed_task(self, zip_path: str) -> Optional[TaskDefinition]:
        """Get a deployed task from the registry.
        
        Args:
            zip_path: Path to the zip file
            
        Returns:
            TaskDefinition if found in registry, None otherwise
        """
        record = await self.deployment_tracker.get_by_path(zip_path)
        if not record or not record.is_deployed:
            return None
        
        return self.task_registry.get(record.task_id, record.version)
    
    async def _record_failed_deployment(self, zip_path: str, error: str) -> None:
        """Record a failed deployment attempt.
        
        Args:
            zip_path: Path to the zip file
            error: Error message
        """
        # Try to extract task_id and version from the zip
        try:
            validator = TaskPackageValidator(zip_path)
            metadata = validator.get_metadata()
            task_id = metadata.name
            version = metadata.version
        except Exception:
            # Can't extract metadata, use placeholder
            task_id = "unknown"
            version = "unknown"
        
        await self.deployment_tracker.record_deployment(
            zip_path=zip_path,
            task_id=task_id,
            version=version,
            status="failed",
            error=error,
        )
    
    async def _save_task_metadata(self, task_def: TaskDefinition, metadata: TaskMetadata) -> None:
        """Save task metadata to the task directory.
        
        Args:
            task_def: TaskDefinition
            metadata: TaskMetadata to save
        """
        metadata_path = Path(task_def.base_path) / "metadata.json"
        
        metadata_dict = metadata.model_dump()
        
        import aiofiles
        async with aiofiles.open(metadata_path, "w") as f:
            await f.write(json.dumps(metadata_dict, indent=2))
    
    async def _load_task_metadata(self, task_id: str, version: str) -> Optional[TaskMetadata]:
        """Load task metadata from the task directory.
        
        Args:
            task_id: Task identifier
            version: Task version
            
        Returns:
            TaskMetadata if found, None otherwise
        """
        base_path = self.task_storage.get_task_base_path(task_id, version)
        metadata_path = base_path / "metadata.json"
        
        if not metadata_path.exists():
            return None
        
        try:
            import aiofiles
            async with aiofiles.open(metadata_path, "r") as f:
                content = await f.read()
                metadata_dict = json.loads(content)
                return TaskMetadata(**metadata_dict)
        except Exception as e:
            logger.warning(
                "task_deployment.metadata_load_failed",
                task_id=task_id,
                version=version,
                error=str(e),
            )
            return None

