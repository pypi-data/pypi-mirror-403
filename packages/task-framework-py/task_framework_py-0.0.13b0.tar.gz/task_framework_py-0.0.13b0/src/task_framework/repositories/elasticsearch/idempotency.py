"""Elasticsearch implementation of IdempotencyStore interface."""

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from task_framework.interfaces.idempotency import IdempotencyStore
from task_framework.logging import logger
from task_framework.models.thread import Thread
from task_framework.repositories.elasticsearch.base import ElasticsearchRepository
from task_framework.repositories.elasticsearch.mappings import IDEMPOTENCY_MAPPINGS


class ElasticsearchIdempotencyStore(IdempotencyStore):
    """Elasticsearch implementation of IdempotencyStore."""
    
    def __init__(
        self,
        client: "AsyncElasticsearch",
        index_prefix: Optional[str] = None,
        database: Optional["Database"] = None,
    ):
        """Initialize store.
        
        Args:
            client: AsyncElasticsearch client
            index_prefix: Index prefix (default from env)
            database: Database instance for retrieving threads by ID
        """
        self._repo = _IdempotencyRepo(client, index_prefix)
        self.database = database
    
    def _hash_key(self, user_id: str, app_id: str, idempotency_key: str) -> str:
        """Generate hash for idempotency key."""
        key_string = f"{user_id}:{app_id}:{idempotency_key}"
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    async def get(
        self, idempotency_key: str, user_id: str, app_id: str
    ) -> Optional[Thread]:
        """Get existing thread by idempotency key."""
        if not self.database:
            return None
        
        await self._repo.ensure_index(IDEMPOTENCY_MAPPINGS)
        
        hash_key = self._hash_key(user_id, app_id, idempotency_key)
        doc = await self._repo.get(hash_key)
        
        if doc and doc.get("thread_id"):
            return await self.database.get_thread(doc["thread_id"])
        
        return None
    
    async def set(
        self, idempotency_key: str, user_id: str, app_id: str, thread_id: str
    ) -> None:
        """Store idempotency key mapping to thread_id."""
        await self._repo.ensure_index(IDEMPOTENCY_MAPPINGS)
        
        hash_key = self._hash_key(user_id, app_id, idempotency_key)
        
        await self._repo.upsert(hash_key, thread_id)
        
        logger.debug(
            "elasticsearch.idempotency.set",
            hash_key=hash_key[:16] + "...",
            thread_id=thread_id,
        )


class _IdempotencyRepo(ElasticsearchRepository):
    """Internal idempotency repository."""
    
    INDEX_SUFFIX = "idempotency"
    
    async def get(self, hash_key: str) -> Optional[Dict[str, Any]]:
        """Get idempotency record by hash key."""
        return await self._get_document(hash_key)
    
    async def upsert(self, hash_key: str, thread_id: str) -> None:
        """Create or update idempotency record."""
        doc = {
            "hash_key": hash_key,
            "thread_id": thread_id,
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        await self._index_document(hash_key, doc, refresh=True)
