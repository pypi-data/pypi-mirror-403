"""Elasticsearch client factory with local and Elastic Cloud support.

Provides unified client creation for both self-hosted Elasticsearch
and Elastic Cloud deployments with configurable connection pooling.
"""

import os
from typing import List, Optional, Tuple, Union

from task_framework.logging import logger


class ElasticsearchClientFactory:
    """Factory for creating Elasticsearch clients with configurable options.
    
    Supports two connection modes:
    1. Self-hosted/Local: Connect via hosts list
    2. Elastic Cloud: Connect via cloud_id
    
    Authentication options:
    - API Key (recommended for Elastic Cloud)
    - Basic auth (username/password)
    
    Example:
        # Local Elasticsearch
        client = ElasticsearchClientFactory.create_client(
            hosts=["http://localhost:9200"],
        )
        
        # Elastic Cloud
        client = ElasticsearchClientFactory.create_client(
            cloud_id="my-deployment:base64string...",
            api_key="my-api-key",
        )
        
        # From environment variables
        client = ElasticsearchClientFactory.from_env()
    """
    
    @classmethod
    def create_client(
        cls,
        # Connection options (use one)
        hosts: Optional[List[str]] = None,
        cloud_id: Optional[str] = None,
        
        # Authentication (use one)
        api_key: Optional[Union[str, Tuple[str, str]]] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        
        # Connection pool settings
        max_connections: int = 10,
        connections_per_node: int = 10,
        
        # TLS settings
        verify_certs: bool = True,
        ca_certs: Optional[str] = None,
        
        # Timeout settings
        request_timeout: int = 30,
        retry_on_timeout: bool = True,
        max_retries: int = 3,
    ) -> "AsyncElasticsearch":
        """Create an async Elasticsearch client.
        
        Args:
            hosts: List of Elasticsearch host URLs (for self-hosted)
            cloud_id: Elastic Cloud deployment ID
            api_key: API key for authentication (string or (id, key) tuple)
            username: Username for basic auth
            password: Password for basic auth
            max_connections: Maximum total connections in pool
            connections_per_node: Maximum connections per ES node
            verify_certs: Whether to verify TLS certificates
            ca_certs: Path to CA certificate file
            request_timeout: Request timeout in seconds
            retry_on_timeout: Whether to retry on timeout
            max_retries: Maximum number of retries
            
        Returns:
            Configured AsyncElasticsearch client
            
        Raises:
            ValueError: If neither hosts nor cloud_id is provided
            ImportError: If elasticsearch package is not installed
        """
        try:
            from elasticsearch import AsyncElasticsearch
        except ImportError:
            raise ImportError(
                "elasticsearch package is required for Elasticsearch storage. "
                "Install with: pip install 'task-framework[elasticsearch]'"
            )
        
        # Build client kwargs
        kwargs = {
            "request_timeout": request_timeout,
            "retry_on_timeout": retry_on_timeout,
            "max_retries": max_retries,
            "verify_certs": verify_certs,
        }
        
        # Connection mode
        if cloud_id:
            kwargs["cloud_id"] = cloud_id
            logger.info(
                "elasticsearch.client.cloud_mode",
                cloud_id=cloud_id[:20] + "..." if len(cloud_id) > 20 else cloud_id,
            )
        elif hosts:
            # Filter out empty hosts
            valid_hosts = [h.strip() for h in hosts if h and h.strip()]
            if not valid_hosts:
                raise ValueError("At least one valid host URL is required")
            kwargs["hosts"] = valid_hosts
            logger.info(
                "elasticsearch.client.hosts_mode",
                hosts=valid_hosts,
            )
        else:
            raise ValueError(
                "Either 'hosts' or 'cloud_id' must be provided for Elasticsearch connection"
            )
        
        # Authentication
        if api_key:
            kwargs["api_key"] = api_key
            logger.debug("elasticsearch.client.auth", method="api_key")
        elif username and password:
            kwargs["basic_auth"] = (username, password)
            logger.debug("elasticsearch.client.auth", method="basic_auth", user=username)
        else:
            logger.warning(
                "elasticsearch.client.no_auth",
                message="No authentication configured - ensure ES allows unauthenticated access",
            )
        
        # TLS/CA settings
        if ca_certs:
            kwargs["ca_certs"] = ca_certs
            logger.debug("elasticsearch.client.ca_certs", path=ca_certs)
        
        # Create client
        client = AsyncElasticsearch(**kwargs)
        
        logger.info(
            "elasticsearch.client.created",
            max_connections=max_connections,
            connections_per_node=connections_per_node,
            request_timeout=request_timeout,
            verify_certs=verify_certs,
        )
        
        return client
    
    @classmethod
    def from_env(cls) -> "AsyncElasticsearch":
        """Create client from environment variables.
        
        Environment variables:
            ELASTICSEARCH_HOSTS: Comma-separated list of ES hosts (or use CLOUD_ID)
            ELASTICSEARCH_CLOUD_ID: Elastic Cloud deployment ID (or use HOSTS)
            ELASTICSEARCH_API_KEY: API key for authentication
            ELASTICSEARCH_USERNAME: Username for basic auth
            ELASTICSEARCH_PASSWORD: Password for basic auth
            ELASTICSEARCH_MAX_CONNECTIONS: Max total connections (default: 10)
            ELASTICSEARCH_CONNECTIONS_PER_NODE: Connections per node (default: 10)
            ELASTICSEARCH_TIMEOUT: Request timeout in seconds (default: 30)
            ELASTICSEARCH_VERIFY_CERTS: Verify TLS certs (default: true)
            ELASTICSEARCH_CA_CERTS: Path to CA certificate file
            
        Returns:
            Configured AsyncElasticsearch client
            
        Raises:
            ValueError: If required environment variables are missing
        """
        # Parse hosts
        hosts_str = os.getenv("ELASTICSEARCH_HOSTS", "")
        hosts = [h.strip() for h in hosts_str.split(",") if h.strip()] if hosts_str else None
        
        # Cloud ID
        cloud_id = os.getenv("ELASTICSEARCH_CLOUD_ID")
        
        # Validate connection config
        if not hosts and not cloud_id:
            raise ValueError(
                "Either ELASTICSEARCH_HOSTS or ELASTICSEARCH_CLOUD_ID environment variable is required"
            )
        
        # Parse boolean for verify_certs
        verify_certs_str = os.getenv("ELASTICSEARCH_VERIFY_CERTS", "true").lower()
        verify_certs = verify_certs_str in ("true", "1", "yes")
        
        return cls.create_client(
            hosts=hosts,
            cloud_id=cloud_id,
            api_key=os.getenv("ELASTICSEARCH_API_KEY"),
            username=os.getenv("ELASTICSEARCH_USERNAME"),
            password=os.getenv("ELASTICSEARCH_PASSWORD"),
            max_connections=int(os.getenv("ELASTICSEARCH_MAX_CONNECTIONS", "10")),
            connections_per_node=int(os.getenv("ELASTICSEARCH_CONNECTIONS_PER_NODE", "10")),
            request_timeout=int(os.getenv("ELASTICSEARCH_TIMEOUT", "30")),
            verify_certs=verify_certs,
            ca_certs=os.getenv("ELASTICSEARCH_CA_CERTS"),
        )
    
    @classmethod
    def get_index_prefix(cls) -> str:
        """Get the index prefix from environment.
        
        Returns:
            Index prefix (default: 'task-framework')
        """
        return os.getenv("ELASTICSEARCH_INDEX_PREFIX", "task-framework")
