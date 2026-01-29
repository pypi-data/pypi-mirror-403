"""Elasticsearch settings store for system settings persistence."""

import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from task_framework.logging import logger
from task_framework.models.settings import SystemSettings
from task_framework.repositories.elasticsearch.base import ElasticsearchRepository


# Settings mapping - simple key-value store
SETTINGS_MAPPINGS = {
    "properties": {
        "key": {"type": "keyword"},
        "value": {"type": "object", "enabled": False},  # Store as unindexed JSON
        "updated_at": {"type": "date"},
        "updated_by": {"type": "keyword"},
    }
}


class ElasticsearchSettingsStore:
    """ES-backed settings store for system configuration.
    
    Stores settings as key-value pairs in ES for persistence across restarts.
    Settings can be updated at runtime via Admin API.
    """
    
    SETTINGS_KEY = "system_settings"
    
    def __init__(
        self,
        es_client: "AsyncElasticsearch",
        index_prefix: Optional[str] = None,
    ):
        """Initialize settings store.
        
        Args:
            es_client: AsyncElasticsearch client
            index_prefix: Index name prefix
        """
        self.es = es_client
        self.prefix = index_prefix or os.getenv(
            "ELASTICSEARCH_INDEX_PREFIX", "task-framework"
        )
        self.index_name = f"{self.prefix}-settings"
        self._initialized = False
        self._cached_settings: Optional[SystemSettings] = None
    
    async def _ensure_index(self) -> None:
        """Ensure settings index exists."""
        if self._initialized:
            return
        
        try:
            exists = await self.es.indices.exists(index=self.index_name)
            if not exists:
                await self.es.indices.create(
                    index=self.index_name,
                    body={
                        "mappings": SETTINGS_MAPPINGS,
                        "settings": {
                            "number_of_shards": 1,
                            "number_of_replicas": 1,
                        }
                    }
                )
                logger.info(
                    "elasticsearch.settings_store.index_created",
                    index=self.index_name,
                )
        except Exception as e:
            if "resource_already_exists_exception" not in str(e):
                raise
        
        self._initialized = True
    
    async def get_settings(self) -> SystemSettings:
        """Get current system settings.
        
        Returns settings from ES if available, otherwise returns defaults
        from environment variables.
        
        Returns:
            SystemSettings instance
        """
        await self._ensure_index()
        
        try:
            result = await self.es.get(
                index=self.index_name,
                id=self.SETTINGS_KEY,
            )
            
            doc = result.get("_source", {})
            value = doc.get("value", {})
            
            settings = SystemSettings(
                max_concurrent_threads=value.get("max_concurrent_threads", 0),
                updated_at=doc.get("updated_at"),
                updated_by=doc.get("updated_by"),
            )
            
            self._cached_settings = settings
            return settings
            
        except Exception as e:
            if "not_found" in str(e).lower() or "404" in str(e):
                # No settings stored yet, return defaults
                return SystemSettings.default()
            raise
    
    async def update_settings(
        self,
        settings: SystemSettings,
        updated_by: Optional[str] = None,
    ) -> SystemSettings:
        """Update system settings.
        
        Args:
            settings: New settings values
            updated_by: User/admin making the update
            
        Returns:
            Updated SystemSettings instance
        """
        await self._ensure_index()
        
        now = datetime.now(timezone.utc)
        
        doc = {
            "key": self.SETTINGS_KEY,
            "value": {
                "max_concurrent_threads": settings.max_concurrent_threads,
            },
            "updated_at": now.isoformat(),
            "updated_by": updated_by,
        }
        
        await self.es.index(
            index=self.index_name,
            id=self.SETTINGS_KEY,
            body=doc,
            refresh=True,
        )
        
        settings.updated_at = now
        settings.updated_by = updated_by
        self._cached_settings = settings
        
        logger.info(
            "elasticsearch.settings_store.updated",
            max_concurrent_threads=settings.max_concurrent_threads,
            updated_by=updated_by,
        )
        
        return settings
    
    def get_cached_max_concurrent_threads(self) -> int:
        """Get cached max concurrent threads value.
        
        Uses cached value for performance in hot paths.
        Falls back to env var if not cached.
        
        Returns:
            Max concurrent threads (0 = unlimited)
        """
        if self._cached_settings:
            return self._cached_settings.max_concurrent_threads
        return int(os.getenv("MAX_CONCURRENT_THREADS", "0"))
    
    async def get_max_concurrent_threads_async(self) -> int:
        """Get max concurrent threads with fresh read from ES.
        
        Always reads from Elasticsearch to ensure up-to-date value
        across all workers.
        
        Returns:
            Max concurrent threads (0 = unlimited)
        """
        try:
            settings = await self.get_settings()
            return settings.max_concurrent_threads
        except Exception:
            return int(os.getenv("MAX_CONCURRENT_THREADS", "0"))
