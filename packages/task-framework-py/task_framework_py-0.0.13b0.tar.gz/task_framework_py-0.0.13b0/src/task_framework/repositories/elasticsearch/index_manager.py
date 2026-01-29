"""Elasticsearch index management utilities.

Provides functions to create and manage ES indices at startup.
"""

import os
from typing import Optional

from task_framework.logging import logger


async def ensure_all_indices(
    client: "AsyncElasticsearch",
    index_prefix: Optional[str] = None,
    force_create: bool = False,
) -> int:
    """Create all Elasticsearch indices with their mappings.
    
    This function creates all required indices if they don't already exist.
    Useful for initializing a fresh ES cluster or ensuring indices are ready
    before the application starts processing requests.
    
    Args:
        client: AsyncElasticsearch client instance
        index_prefix: Index name prefix (default from env: ELASTICSEARCH_INDEX_PREFIX)
        force_create: If True, attempt to create indices even if they might exist
        
    Returns:
        Number of indices created
        
    Environment Variables:
        ELASTICSEARCH_INDEX_PREFIX: Prefix for index names (default: "task-framework")
        
    Example:
        >>> from task_framework.repositories.elasticsearch import ensure_all_indices
        >>> from task_framework.repositories.elasticsearch.client import create_es_client
        >>> 
        >>> client = create_es_client()
        >>> created = await ensure_all_indices(client)
        >>> print(f"Created {created} indices")
    """
    from task_framework.repositories.elasticsearch.mappings import (
        ALL_MAPPINGS,
        INDEX_SUFFIXES,
    )
    
    prefix = index_prefix or os.getenv("ELASTICSEARCH_INDEX_PREFIX", "task-framework")
    
    created_count = 0
    
    for suffix, mapping in ALL_MAPPINGS.items():
        index_name = f"{prefix}-{suffix}"
        
        try:
            # Check if index exists
            exists = await client.indices.exists(index=index_name)
            
            if not exists:
                # Create index with mappings
                body = {
                    "mappings": mapping,
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 1,
                    }
                }
                
                await client.indices.create(index=index_name, body=body)
                created_count += 1
                
                logger.info(
                    "elasticsearch.index.created",
                    index=index_name,
                )
            else:
                logger.debug(
                    "elasticsearch.index.exists",
                    index=index_name,
                )
                
        except Exception as e:
            # Index might have been created by another worker (race condition)
            if "resource_already_exists_exception" in str(e):
                logger.debug(
                    "elasticsearch.index.already_created",
                    index=index_name,
                )
            else:
                logger.error(
                    "elasticsearch.index.create_failed",
                    index=index_name,
                    error=str(e),
                )
                # Don't raise - continue creating other indices
    
    logger.info(
        "elasticsearch.indices.initialized",
        total_indices=len(ALL_MAPPINGS),
        created=created_count,
        prefix=prefix,
    )
    
    return created_count


async def ensure_indices_on_startup() -> int:
    """Create all ES indices on server startup if enabled.
    
    Checks the ELASTICSEARCH_CREATE_INDICES_ON_STARTUP environment variable.
    If set to 'true', '1', or 'yes', creates all indices with their mappings.
    
    This is useful for:
    - Fresh deployments where indices don't exist yet
    - Ensuring consistent index mappings across environments
    - Reducing first-request latency by pre-creating indices
    
    Environment Variables:
        ELASTICSEARCH_CREATE_INDICES_ON_STARTUP: Enable index creation
            Values: 'true', '1', 'yes' (case-insensitive) to enable
            Default: disabled
        STORAGE_TYPE: Must be 'elasticsearch' for this to work
        ELASTICSEARCH_URL or ELASTICSEARCH_CLOUD_ID: ES connection settings
        
    Returns:
        Number of indices created, or 0 if disabled/not applicable
        
    Example in server startup:
        >>> from task_framework.repositories.elasticsearch import ensure_indices_on_startup
        >>> 
        >>> @app.on_event("startup")
        >>> async def startup():
        >>>     await ensure_indices_on_startup()
    """
    # Check if enabled
    enabled = os.getenv("ELASTICSEARCH_CREATE_INDICES_ON_STARTUP", "").lower()
    if enabled not in ("true", "1", "yes"):
        logger.debug(
            "elasticsearch.indices.startup_creation_disabled",
            message="Set ELASTICSEARCH_CREATE_INDICES_ON_STARTUP=true to enable",
        )
        return 0
    
    # Check storage type
    storage_type = os.getenv("STORAGE_TYPE", "file")
    if storage_type != "elasticsearch":
        logger.debug(
            "elasticsearch.indices.startup_creation_skipped",
            reason="STORAGE_TYPE is not elasticsearch",
            storage_type=storage_type,
        )
        return 0
    
    # Create ES client
    try:
        from task_framework.repositories.elasticsearch.client import ElasticsearchClientFactory
        
        client = ElasticsearchClientFactory.from_env()
        created = await ensure_all_indices(client)
        
        return created
        
    except Exception as e:
        logger.error(
            "elasticsearch.indices.startup_creation_failed",
            error=str(e),
        )
        return 0
