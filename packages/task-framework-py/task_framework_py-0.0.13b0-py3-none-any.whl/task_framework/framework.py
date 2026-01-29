"""TaskFramework class for managing configuration, server, and task execution."""

import os
from pathlib import Path
from typing import Any, List, Optional

from task_framework.delivery.event_publisher import EventPublisher
from task_framework.exceptions import ConfigurationError
from task_framework.execution import ExecutionEngine
from task_framework.interfaces import Database, FileStorage, Logger, Scheduler
from task_framework.logging import configure_logging
from task_framework.metrics import library_initializations_total
from task_framework.models.task_definition import TaskDefinition
from task_framework.utils.metrics_helpers import restore_thread_metrics_from_db

# Configure logging on module import
configure_logging()


class TaskFramework:
    """Main library class that manages configuration, server, and task execution.
    
    Multi-task mode with dynamic task loading from zip packages or source directories.
    """

    def __init__(
        self,
        api_keys: List[str],
        admin_api_keys: List[str],
        file_storage: Optional[FileStorage] = None,
        database: Optional[Database] = None,
        scheduler: Optional[Scheduler] = None,
        logger: Optional[Logger] = None,
        base_path: Optional[str] = None,
        task_definitions_dir: Optional[str] = None,
    ) -> None:
        """Initialize TaskFramework with API keys and optional dependencies.

        Args:
            api_keys: Required. List of regular API keys from environment variable
            admin_api_keys: Required. List of admin API keys from environment variable
            file_storage: Optional. File storage interface implementation (lazy-initialized)
            database: Optional. Database interface implementation (lazy-initialized)
            scheduler: Optional. Scheduler interface implementation (lazy-initialized)
            logger: Optional. Logger interface implementation (defaults to structlog if not provided)
            base_path: Optional. Base directory for server data (defaults to current directory)
            task_definitions_dir: Optional. Directory for task definition zip files.
                                  Defaults to {base_path}/task_definitions/ or TASK_DEFINITIONS_DIR env var.

        Raises:
            ConfigurationError: If api_keys or admin_api_keys are empty
        """
        if not api_keys:
            raise ConfigurationError("API keys are required")
        if not admin_api_keys:
            raise ConfigurationError("Admin API keys are required")

        self.api_keys = api_keys
        self.admin_api_keys = admin_api_keys
        self._file_storage = file_storage
        self._database = database
        self._scheduler = scheduler
        self._logger = logger
        self.server = None
        self._initialized = True
        self._execution_engine: Optional[ExecutionEngine] = None
        self._event_publisher: Optional[EventPublisher] = None
        self._delivery_engine: Optional[Any] = None
        
        # Multi-task mode support
        self._base_path = Path(base_path) if base_path else Path(".")
        
        # Determine task_definitions_dir from: argument > env var > default
        if task_definitions_dir:
            self._task_definitions_dir = Path(task_definitions_dir)
        elif os.environ.get("TASK_DEFINITIONS_DIR"):
            self._task_definitions_dir = Path(os.environ["TASK_DEFINITIONS_DIR"])
        else:
            self._task_definitions_dir = self._base_path / "task_definitions"
        
        # Multi-task components (lazy-initialized)
        self._task_registry: Optional[Any] = None
        self._task_storage: Optional[Any] = None
        self._deployment_tracker: Optional[Any] = None
        self._task_deployment_service: Optional[Any] = None
        self._registry_sync: Optional[Any] = None
        self._framework_path: Optional[str] = None  # For local development
        
        # Secrets and configuration services (lazy-initialized)
        self._credential_service: Optional[Any] = None
        self._configuration_service: Optional[Any] = None
        
        # Webhook repositories (lazy-initialized)
        self._webhook_repository: Optional[Any] = None
        self._webhook_delivery_repository: Optional[Any] = None
        
        # File metadata store (lazy-initialized, ES-only)
        self._file_metadata_store: Optional[Any] = None
        
        # Settings and concurrency (lazy-initialized)
        self._settings_store: Optional[Any] = None
        self._concurrency_manager: Optional[Any] = None
        
        # Storage factory (lazy-initialized based on STORAGE_TYPE env var)
        self._storage_factory: Optional[Any] = None

        # Metrics
        library_initializations_total.inc()

        # Logging
        from task_framework.logging import logger

        logger.info(
            "library.initialized",
            api_keys_count=len(api_keys),
            admin_api_keys_count=len(admin_api_keys),
            base_path=str(self._base_path),
            task_definitions_dir=str(self._task_definitions_dir),
        )

    @property
    def storage_factory(self) -> "StorageFactory":
        """Get storage factory instance (lazy initialization based on STORAGE_TYPE env)."""
        if self._storage_factory is None:
            from task_framework.storage_factory import StorageFactory
            self._storage_factory = StorageFactory.from_env()
        return self._storage_factory
    
    @property
    def file_storage(self) -> Optional[FileStorage]:
        """Get file storage instance (lazy initialization)."""
        if self._file_storage is None:
            self._file_storage = self.storage_factory.create_file_storage()
        return self._file_storage

    @property
    def database(self) -> Optional[Database]:
        """Get database instance (lazy initialization)."""
        if self._database is None:
            self._database = self.storage_factory.create_database()
        return self._database

    @property
    def webhook_repository(self) -> "WebhookRepository":
        """Get webhook repository instance (lazy initialization)."""
        if self._webhook_repository is None:
            self._webhook_repository = self.storage_factory.create_webhook_repository()
        return self._webhook_repository

    @property
    def webhook_delivery_repository(self) -> "WebhookDeliveryRepository":
        """Get webhook delivery repository instance (lazy initialization)."""
        if self._webhook_delivery_repository is None:
            self._webhook_delivery_repository = self.storage_factory.create_webhook_delivery_repository()
        return self._webhook_delivery_repository

    @property
    def file_metadata_store(self) -> Optional[Any]:
        """Get file metadata store instance (lazy initialization).
        
        Returns ElasticsearchFileMetadataStore when STORAGE_TYPE=elasticsearch,
        None for file-based storage (metadata stored in local JSON files).
        """
        if self._file_metadata_store is None:
            self._file_metadata_store = self.storage_factory.create_file_metadata_store()
        return self._file_metadata_store

    @property
    def settings_store(self) -> Optional[Any]:
        """Get settings store instance (lazy initialization).
        
        Returns ElasticsearchSettingsStore when STORAGE_TYPE=elasticsearch,
        None for file-based storage.
        """
        if self._settings_store is None:
            self._settings_store = self.storage_factory.create_settings_store()
        return self._settings_store

    @property
    def concurrency_manager(self) -> Optional[Any]:
        """Get concurrency manager instance (lazy initialization)."""
        if self._concurrency_manager is None:
            from task_framework.services.concurrency_manager import ConcurrencyManager
            self._concurrency_manager = ConcurrencyManager(
                database=self.database,
                settings_store=self.settings_store,
            )
        return self._concurrency_manager

    @property
    def scheduler(self) -> Optional[Scheduler]:
        """Get scheduler instance (lazy initialization)."""
        return self._scheduler

    @property
    def logger(self) -> Optional[Logger]:
        """Get logger instance (lazy initialization)."""
        return self._logger
    
    @property
    def base_path(self) -> Path:
        """Get base path for server data."""
        return self._base_path
    
    @property
    def task_definitions_dir(self) -> Path:
        """Get task definitions directory path."""
        return self._task_definitions_dir
    
    @property
    def task_registry(self) -> "TaskRegistry":
        """Get task registry instance (lazy initialization)."""
        if self._task_registry is None:
            from task_framework.services.task_registry import TaskRegistry
            # TaskRegistry uses file-based persistence for now
            # TODO: Migrate to ES-based storage in future iteration
            self._task_registry = TaskRegistry(data_dir=str(self._base_path))
        return self._task_registry
    
    @property
    def task_storage(self) -> "TaskStorage":
        """Get task storage instance (lazy initialization)."""
        if self._task_storage is None:
            # Use storage factory which may return S3TaskStorage or local TaskStorage
            self._task_storage = self.storage_factory.create_task_storage()
        return self._task_storage
    
    @property
    def deployment_tracker(self) -> "TaskDeploymentTracker":
        """Get deployment tracker instance (lazy initialization)."""
        if self._deployment_tracker is None:
            self._deployment_tracker = self.storage_factory.create_deployment_tracker_store()
        return self._deployment_tracker
    
    @property
    def task_deployment_service(self) -> "TaskDeploymentService":
        """Get task deployment service instance (lazy initialization)."""
        if self._task_deployment_service is None:
            from task_framework.services.task_deployment import TaskDeploymentService
            from task_framework.services.task_loader import TaskLoader
            
            task_loader = TaskLoader(self.task_storage, framework_path=self._framework_path)
            self._task_deployment_service = TaskDeploymentService(
                task_registry=self.task_registry,
                task_storage=self.task_storage,
                deployment_tracker=self.deployment_tracker,
                task_loader=task_loader,
                registry_sync=self.registry_sync,
            )
        return self._task_deployment_service
    
    @property
    def registry_sync(self) -> "RegistrySyncService":
        """Get registry sync service instance (lazy initialization)."""
        if self._registry_sync is None:
            from task_framework.services.registry_sync import RegistrySyncService
            
            sync_interval = float(os.environ.get("REGISTRY_SYNC_INTERVAL", "5"))
            self._registry_sync = RegistrySyncService(
                data_dir=str(self._base_path),
                sync_interval=sync_interval,
            )
            self._registry_sync.set_framework(self)
        return self._registry_sync
    
    @property
    def credential_service(self) -> "CredentialService":
        """Get credential service instance (lazy initialization via storage factory)."""
        if self._credential_service is None:
            self._credential_service = self.storage_factory.create_credential_store()
        return self._credential_service
    
    @property
    def configuration_service(self) -> "ConfigurationService":
        """Get configuration service instance (lazy initialization via storage factory)."""
        if self._configuration_service is None:
            self._configuration_service = self.storage_factory.create_config_store()
        return self._configuration_service
    
    def set_framework_path(self, path: str) -> None:
        """Set the framework path for local development.
        
        When set, deployed tasks will install task-framework from this path
        instead of from PyPI.
        
        Args:
            path: Path to the task-framework source directory
        """
        self._framework_path = path
    
    def get_task(self, task_id: Optional[str] = None, version: Optional[str] = None) -> Optional[TaskDefinition]:
        """Get a task definition by task_id and optional version.
        
        Args:
            task_id: Task identifier
            version: Optional version (defaults to latest)
            
        Returns:
            TaskDefinition if found, None otherwise
        """
        return self.task_registry.resolve_task(task_id, version)

    @property
    def execution_engine(self) -> ExecutionEngine:
        """Get execution engine instance."""
        if self._execution_engine is None:
            self._execution_engine = ExecutionEngine(self)
        return self._execution_engine

    @property
    def event_publisher(self) -> EventPublisher:
        """Get event publisher instance."""
        if self._event_publisher is None:
            self._event_publisher = EventPublisher()
            # Initialize webhook delivery when event publisher is first accessed
            self._ensure_webhook_delivery_initialized()
        return self._event_publisher

    def _ensure_webhook_delivery_initialized(self) -> None:
        """Ensure webhook delivery engine is initialized and event handler is set."""
        if self._delivery_engine is not None:
            return

        from task_framework.delivery.delivery_engine import DeliveryEngine
        from task_framework.services.webhook_service import WebhookService

        # Initialize webhook service and delivery engine using storage factory
        webhook_service = WebhookService(
            webhook_repository=self.webhook_repository,
            delivery_repository=self.webhook_delivery_repository,
        )

        delivery_engine = DeliveryEngine(
            webhook_service=webhook_service,
            delivery_repository=self.webhook_delivery_repository,
            database=self.database,
            file_storage=self.file_storage,
        )

        # Set event handler to process events
        async def event_handler(event: "WebhookEvent") -> None:
            """Handle webhook event by delivering to matching webhooks."""
            await delivery_engine.process_event(event)

        # Set handler - event publisher will auto-start when handler is set
        self.event_publisher.set_event_handler(event_handler)

        # Store delivery engine for cleanup
        self._delivery_engine = delivery_engine
    
    async def enable_multi_task_mode(self) -> None:
        """Enable multi-task mode and perform launch-time discovery.
        
        This method:
        1. Loads the deployment tracker
        2. Scans task_definitions_dir for zip files
        3. Deploys new tasks and reloads existing ones
        
        Should be called during server startup.
        """
        from task_framework.logging import logger
        
        logger.info(
            "framework.startup",
            task_definitions_dir=str(self._task_definitions_dir),
        )
        
        # Load deployment tracker state
        await self.deployment_tracker.load()
        
        # First, reload any previously deployed tasks
        loaded, failed = await self.task_deployment_service.reload_deployed_tasks()
        
        # Then, scan for new zip files and deploy them
        deployed, skipped, deploy_failed = await self.task_deployment_service.deploy_all_from_folder(
            str(self._task_definitions_dir)
        )
        
        logger.info(
            "framework.startup.complete",
            tasks_loaded=loaded,
            tasks_deployed=deployed,
            tasks_skipped=skipped,
            tasks_failed=failed + deploy_failed,
            total_registered=self.task_registry.count(),
        )
    
    async def deploy_task_from_zip(self, zip_path: str, force: bool = False) -> TaskDefinition:
        """Deploy a task from a zip file.
        
        Args:
            zip_path: Path to the task definition zip file
            force: If True, redeploy even if already deployed
            
        Returns:
            Deployed TaskDefinition
            
        Raises:
            TaskDeploymentError: If deployment fails
        """
        task_def, _ = await self.task_deployment_service.deploy_from_zip(zip_path, force=force)
        return task_def
    
    async def deploy_dev_task(self, task_dir: str) -> TaskDefinition:
        """Deploy a task from source directory (dev mode).
        
        This method loads a task directly from a source directory without
        packaging it as a zip file. Useful for rapid development iteration.
        
        Args:
            task_dir: Path to the task directory containing task.yaml and source code
            
        Returns:
            Deployed TaskDefinition
            
        Raises:
            TaskDeploymentError: If deployment fails
        """
        task_def = await self.task_deployment_service.deploy_from_source(task_dir)
        return task_def
    
    async def undeploy_task(self, task_id: str, version: Optional[str] = None) -> List[str]:
        """Undeploy a task.
        
        Args:
            task_id: Task identifier
            version: Optional version. If None, undeploys all versions.
            
        Returns:
            List of undeployed full_ids (task_id:version)
        """
        return await self.task_deployment_service.undeploy(task_id, version)
    
    def list_tasks(self) -> List[TaskDefinition]:
        """List all registered tasks.
        
        Returns:
            List of TaskDefinition objects
        """
        return self.task_registry.list_all()

