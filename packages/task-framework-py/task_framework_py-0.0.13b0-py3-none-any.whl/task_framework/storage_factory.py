"""Storage Factory for creating storage instances based on configuration.

Provides a unified way to create storage instances, enabling easy switching
between different backends (file-based, Elasticsearch, S3) via configuration.
"""

import os
from typing import Any, Optional

from task_framework.interfaces.database import Database
from task_framework.interfaces.deployment_tracker_store import DeploymentTrackerStore
from task_framework.interfaces.idempotency import IdempotencyStore
from task_framework.interfaces.storage import FileStorage
from task_framework.interfaces.task_registry_store import TaskRegistryStore
from task_framework.logging import logger
from task_framework.repositories.webhook_db import WebhookRepository


class StorageFactory:
    """Factory for creating storage instances based on configuration.
    
    Supports separate configuration for records and files:
    - storage_type: Backend for records (threads, artifacts, schedules, etc.)
    - file_storage_type: Backend for physical files
    
    Attributes:
        storage_type: Type of storage backend ('file' or 'elasticsearch')
        file_storage_type: Type of file storage ('local' or 's3')
        config: Configuration dictionary for the storage backend
        
    Example:
        # Local storage (default)
        factory = StorageFactory(storage_type="file", base_path="./data")
        
        # Elasticsearch + S3
        factory = StorageFactory.from_env()  # Uses env vars
        
        # Get instances
        database = factory.create_database()
        file_storage = factory.create_file_storage()
    """
    
    # Supported storage types for records
    STORAGE_TYPE_FILE = "file"
    STORAGE_TYPE_ELASTICSEARCH = "elasticsearch"
    
    # Supported file storage types
    FILE_STORAGE_TYPE_LOCAL = "local"
    FILE_STORAGE_TYPE_S3 = "s3"
    
    def __init__(
        self,
        storage_type: str = "file",
        file_storage_type: str = "local",
        **config: Any,
    ) -> None:
        """Initialize StorageFactory.
        
        Args:
            storage_type: Type of record storage backend ('file' or 'elasticsearch')
            file_storage_type: Type of file storage ('local' or 's3')
            **config: Configuration options for the storage backend
                For 'file':
                    - base_path: str - Base directory for file storage
                For 'elasticsearch':
                    - hosts: List[str] - Elasticsearch hosts
                    - cloud_id: str - Elastic Cloud ID
                    - index_prefix: str - Prefix for index names
                    - api_key: str - API key for authentication
                    - username: str - Username for basic auth
                    - password: str - Password for basic auth
                For 's3':
                    - s3_bucket: str - S3 bucket name
                    - s3_region: str - AWS region
                    - s3_endpoint_url: str - Endpoint URL for MinIO
                    - s3_path_prefix: str - Path prefix for objects
        """
        self.storage_type = storage_type
        self.file_storage_type = file_storage_type
        self.config = config
        
        # Lazy-initialized ES client
        self._es_client = None
        self._lock_manager = None
    
    def _get_es_client(self) -> "AsyncElasticsearch":
        """Get or create the Elasticsearch client (singleton)."""
        if self._es_client is None:
            from task_framework.repositories.elasticsearch.client import ElasticsearchClientFactory
            self._es_client = ElasticsearchClientFactory.from_env()
            logger.info("storage_factory.elasticsearch_client_created")
        return self._es_client
    
    def _get_index_prefix(self) -> str:
        """Get Elasticsearch index prefix."""
        return self.config.get(
            "index_prefix",
            os.getenv("ELASTICSEARCH_INDEX_PREFIX", "task-framework")
        )
    
    @property
    def lock_manager(self) -> Optional["ElasticsearchDistributedLock"]:
        """Get the distributed lock manager (ES storage only)."""
        if self.storage_type != self.STORAGE_TYPE_ELASTICSEARCH:
            return None
        
        if self._lock_manager is None:
            from task_framework.repositories.elasticsearch.locks import ElasticsearchDistributedLock
            self._lock_manager = ElasticsearchDistributedLock(
                client=self._get_es_client(),
                index_prefix=self._get_index_prefix(),
            )
            logger.info("storage_factory.lock_manager_created")
        return self._lock_manager
    
    def create_database(self) -> Database:
        """Create a Database instance.
        
        Returns:
            Database implementation based on storage_type
            
        Raises:
            ValueError: If storage_type is not supported
        """
        logger.info(
            "storage_factory.create_database",
            storage_type=self.storage_type,
        )
        
        if self.storage_type == self.STORAGE_TYPE_FILE:
            from task_framework.repositories.file_db import FileDatabase
            logger.info("storage_factory.creating_file_database")
            return FileDatabase(base_path=self.config.get("base_path", "data"))
        
        elif self.storage_type == self.STORAGE_TYPE_ELASTICSEARCH:
            from task_framework.repositories.elasticsearch.database import ElasticsearchDatabase
            logger.info("storage_factory.creating_elasticsearch_database")
            return ElasticsearchDatabase(
                client=self._get_es_client(),
                index_prefix=self._get_index_prefix(),
            )
        
        raise ValueError(f"Unsupported storage type: {self.storage_type}")
    
    def create_task_registry_store(self) -> TaskRegistryStore:
        """Create a TaskRegistryStore instance.
        
        Returns:
            TaskRegistryStore implementation based on storage_type
            
        Raises:
            ValueError: If storage_type is not supported
        """
        if self.storage_type == self.STORAGE_TYPE_FILE:
            from task_framework.repositories.file_task_registry_store import (
                FileTaskRegistryStore,
            )
            return FileTaskRegistryStore(
                data_dir=self.config.get("base_path", "data")
            )
        
        elif self.storage_type == self.STORAGE_TYPE_ELASTICSEARCH:
            from task_framework.repositories.elasticsearch.task_registry_store import (
                ElasticsearchTaskRegistryStore,
            )
            return ElasticsearchTaskRegistryStore(
                client=self._get_es_client(),
                index_prefix=self._get_index_prefix(),
            )
        
        raise ValueError(f"Unsupported storage type: {self.storage_type}")
    
    def create_deployment_tracker_store(self) -> DeploymentTrackerStore:
        """Create a DeploymentTrackerStore instance.
        
        Returns:
            DeploymentTrackerStore implementation based on storage_type
            
        Raises:
            ValueError: If storage_type is not supported
        """
        if self.storage_type == self.STORAGE_TYPE_FILE:
            from task_framework.repositories.task_deployment_tracker import (
                TaskDeploymentTracker,
            )
            return TaskDeploymentTracker(
                base_path=self.config.get("base_path", "data")
            )
        
        elif self.storage_type == self.STORAGE_TYPE_ELASTICSEARCH:
            from task_framework.repositories.elasticsearch.deployment_tracker import (
                ElasticsearchDeploymentTracker,
            )
            return ElasticsearchDeploymentTracker(
                client=self._get_es_client(),
                index_prefix=self._get_index_prefix(),
            )
        
        raise ValueError(f"Unsupported storage type: {self.storage_type}")
    
    def create_file_storage(self) -> FileStorage:
        """Create a FileStorage instance.
        
        Returns:
            FileStorage implementation based on file_storage_type
            
        Raises:
            ValueError: If file_storage_type is not supported
        """
        if self.file_storage_type == self.FILE_STORAGE_TYPE_LOCAL:
            from task_framework.storage.local import LocalFileStorage
            return LocalFileStorage(
                base_path=self.config.get("storage_path", 
                    os.path.join(self.config.get("base_path", "data"), "storage"))
            )
        
        elif self.file_storage_type == self.FILE_STORAGE_TYPE_S3:
            from task_framework.storage.s3 import S3FileStorage
            return S3FileStorage.from_env()
        
        raise ValueError(f"Unsupported file storage type: {self.file_storage_type}")
    
    def create_idempotency_store(self, database: Optional[Database] = None) -> IdempotencyStore:
        """Create an IdempotencyStore instance.
        
        Args:
            database: Optional Database instance for thread lookup
        
        Returns:
            IdempotencyStore implementation based on storage_type
            
        Raises:
            ValueError: If storage_type is not supported
        """
        if self.storage_type == self.STORAGE_TYPE_FILE:
            from task_framework.repositories.file_idempotency import (
                FileIdempotencyStore,
            )
            return FileIdempotencyStore(
                base_path=self.config.get("base_path", "data"),
                database=database,
            )
        
        elif self.storage_type == self.STORAGE_TYPE_ELASTICSEARCH:
            from task_framework.repositories.elasticsearch.idempotency import (
                ElasticsearchIdempotencyStore,
            )
            return ElasticsearchIdempotencyStore(
                client=self._get_es_client(),
                index_prefix=self._get_index_prefix(),
                database=database,
            )
        
        raise ValueError(f"Unsupported storage type: {self.storage_type}")
    
    def create_webhook_repository(self) -> WebhookRepository:
        """Create a WebhookRepository instance.
        
        Returns:
            WebhookRepository implementation based on storage_type
            
        Raises:
            ValueError: If storage_type is not supported
        """
        if self.storage_type == self.STORAGE_TYPE_FILE:
            from task_framework.repositories.webhook_db import (
                FileWebhookRepository,
            )
            return FileWebhookRepository(
                base_path=self.config.get("base_path", "data")
            )
        
        elif self.storage_type == self.STORAGE_TYPE_ELASTICSEARCH:
            from task_framework.repositories.elasticsearch.webhook_db import (
                ElasticsearchWebhookRepository,
            )
            return ElasticsearchWebhookRepository(
                client=self._get_es_client(),
                index_prefix=self._get_index_prefix(),
            )
        
        raise ValueError(f"Unsupported storage type: {self.storage_type}")
    
    def create_webhook_delivery_repository(self) -> "WebhookDeliveryRepository":
        """Create a WebhookDeliveryRepository instance.
        
        Returns:
            WebhookDeliveryRepository implementation based on storage_type
        """
        if self.storage_type == self.STORAGE_TYPE_FILE:
            from task_framework.repositories.webhook_db import (
                FileWebhookDeliveryRepository,
            )
            return FileWebhookDeliveryRepository(
                base_path=self.config.get("base_path", "data")
            )
        
        elif self.storage_type == self.STORAGE_TYPE_ELASTICSEARCH:
            from task_framework.repositories.elasticsearch.webhook_db import (
                ElasticsearchWebhookDeliveryRepository,
            )
            return ElasticsearchWebhookDeliveryRepository(
                client=self._get_es_client(),
                index_prefix=self._get_index_prefix(),
            )
        
        raise ValueError(f"Unsupported storage type: {self.storage_type}")
    
    def create_task_storage(self) -> "TaskStorage":
        """Create a TaskStorage instance for zip packages.
        
        If S3 is configured, creates a dual-storage instance (S3 + local cache).
        Otherwise, creates a local-only storage.
        
        Returns:
            TaskStorage or S3TaskStorage instance
        """
        from task_framework.repositories.task_storage import TaskStorage
        
        base_path = self.config.get("base_path", ".")
        
        if self.file_storage_type == self.FILE_STORAGE_TYPE_S3:
            from task_framework.repositories.s3.task_storage import S3TaskStorage
            
            # Create S3 task storage (inherits from TaskStorage)
            return S3TaskStorage.from_env(base_path=base_path)
        
        return TaskStorage(base_path=base_path)
    
    def create_credential_store(self) -> "CredentialService":
        """Create a credential store instance.
        
        Returns:
            CredentialService or ElasticsearchCredentialStore based on storage_type
        """
        base_path = self.config.get("base_path", "data")
        
        if self.storage_type == self.STORAGE_TYPE_FILE:
            from task_framework.services.credential_service import CredentialService
            return CredentialService(base_path=base_path)
        
        elif self.storage_type == self.STORAGE_TYPE_ELASTICSEARCH:
            from task_framework.repositories.elasticsearch.credential_store import (
                ElasticsearchCredentialStore,
            )
            from task_framework.services.encryption_service import EncryptionService
            
            # Create encryption service with key from environment
            key_file = f"{base_path}/credentials/credentials.key"
            encryption_service = EncryptionService(key_file_path=key_file)
            
            return ElasticsearchCredentialStore(
                client=self._get_es_client(),
                encryption_service=encryption_service,
                index_prefix=self._get_index_prefix(),
            )
        
        raise ValueError(f"Unsupported storage type: {self.storage_type}")
    
    def create_config_store(self) -> "ConfigurationService":
        """Create a configuration store instance.
        
        Returns:
            ConfigurationService or ElasticsearchConfigStore based on storage_type
        """
        base_path = self.config.get("base_path", "data")
        
        if self.storage_type == self.STORAGE_TYPE_FILE:
            from task_framework.services.configuration_service import ConfigurationService
            # File-based ConfigurationService needs credential_service for value resolution
            return ConfigurationService(
                base_path=base_path,
                credential_service=self.create_credential_store(),
            )
        
        elif self.storage_type == self.STORAGE_TYPE_ELASTICSEARCH:
            from task_framework.repositories.elasticsearch.config_store import (
                ElasticsearchConfigurationService,
            )
            from task_framework.services.encryption_service import EncryptionService
            
            # Create encryption service with key from environment
            key_file = f"{base_path}/config/config.key"
            encryption_service = EncryptionService(key_file_path=key_file)
            
            # ES config service needs credential_store for vault resolution
            return ElasticsearchConfigurationService(
                client=self._get_es_client(),
                credential_store=self.create_credential_store(),
                encryption_service=encryption_service,
                index_prefix=self._get_index_prefix(),
            )
        
        raise ValueError(f"Unsupported storage type: {self.storage_type}")
    
    def create_file_metadata_store(self) -> Optional["ElasticsearchFileMetadataStore"]:
        """Create a file metadata store instance.
        
        Only creates ES-backed store when STORAGE_TYPE=elasticsearch.
        Returns None for file-based storage (metadata stored in local JSON files).
        
        Returns:
            ElasticsearchFileMetadataStore if using ES, None otherwise
        """
        if self.storage_type == self.STORAGE_TYPE_FILE:
            # File-based storage handles metadata in local JSON files
            return None
        
        elif self.storage_type == self.STORAGE_TYPE_ELASTICSEARCH:
            from task_framework.repositories.elasticsearch.file_store import (
                ElasticsearchFileMetadataStore,
            )
            
            return ElasticsearchFileMetadataStore(
                client=self._get_es_client(),
                index_prefix=self._get_index_prefix(),
            )
        
        raise ValueError(f"Unsupported storage type: {self.storage_type}")
    
    def create_settings_store(self) -> Optional["ElasticsearchSettingsStore"]:
        """Create a system settings store instance.
        
        Only creates ES-backed store when STORAGE_TYPE=elasticsearch.
        Returns None for file-based storage.
        
        Returns:
            ElasticsearchSettingsStore if using ES, None otherwise
        """
        if self.storage_type == self.STORAGE_TYPE_FILE:
            # File-based storage doesn't support runtime settings
            return None
        
        elif self.storage_type == self.STORAGE_TYPE_ELASTICSEARCH:
            from task_framework.repositories.elasticsearch.settings_store import (
                ElasticsearchSettingsStore,
            )
            
            return ElasticsearchSettingsStore(
                es_client=self._get_es_client(),
                index_prefix=self._get_index_prefix(),
            )
        
        raise ValueError(f"Unsupported storage type: {self.storage_type}")
    
    @classmethod
    def from_env(cls) -> "StorageFactory":
        """Create a StorageFactory from environment variables.
        
        Environment variables:
            STORAGE_TYPE: 'file' (default) or 'elasticsearch'
            FILE_STORAGE_TYPE: 'local' (default) or 's3'
            DATA_DIR: Base path for file storage (default: 'data')
            TASK_DEFINITIONS_DIR: Directory for task zips (default: 'task_definitions')
            
            For Elasticsearch (when STORAGE_TYPE=elasticsearch):
                ELASTICSEARCH_HOSTS: Comma-separated ES hosts
                ELASTICSEARCH_CLOUD_ID: Elastic Cloud ID
                ELASTICSEARCH_API_KEY: API key
                ELASTICSEARCH_USERNAME: Username
                ELASTICSEARCH_PASSWORD: Password
                ELASTICSEARCH_INDEX_PREFIX: Index prefix (default: 'task-framework')
            
            For S3 (when FILE_STORAGE_TYPE=s3):
                S3_BUCKET: Bucket name (required)
                S3_REGION: AWS region (default: us-east-1)
                S3_ENDPOINT_URL: Endpoint URL for MinIO
                AWS_ACCESS_KEY_ID: Access key
                AWS_SECRET_ACCESS_KEY: Secret key
                S3_PATH_PREFIX: Path prefix
            
        Returns:
            Configured StorageFactory instance
        """
        storage_type = os.environ.get("STORAGE_TYPE", cls.STORAGE_TYPE_FILE)
        file_storage_type = os.environ.get("FILE_STORAGE_TYPE", cls.FILE_STORAGE_TYPE_LOCAL)
        
        config = {
            "base_path": os.environ.get("DATA_DIR", "data"),
            "task_definitions_dir": os.environ.get("TASK_DEFINITIONS_DIR", "task_definitions"),
        }
        
        # Add ES config from env
        if storage_type == cls.STORAGE_TYPE_ELASTICSEARCH:
            config["index_prefix"] = os.environ.get("ELASTICSEARCH_INDEX_PREFIX", "task-framework")
        
        logger.info(
            "storage_factory.from_env",
            storage_type=storage_type,
            file_storage_type=file_storage_type,
        )
        
        return cls(
            storage_type=storage_type,
            file_storage_type=file_storage_type,
            **config,
        )
