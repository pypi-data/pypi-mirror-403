"""Elasticsearch-based distributed locking.

Provides distributed locks using Elasticsearch documents with:
- TTL-based auto-expiration
- Heartbeat mechanism for long operations
- Automatic expired lock recovery
- Context manager support
"""

import asyncio
import os
import socket
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from task_framework.logging import logger


class LockAcquisitionError(Exception):
    """Raised when a distributed lock cannot be acquired."""
    pass


class ElasticsearchDistributedLock:
    """Distributed lock using Elasticsearch documents.
    
    Uses ES document creation with conflict detection to implement
    distributed locking across multiple workers.
    
    Features:
    - TTL-based expiration (locks auto-release if holder crashes)
    - Heartbeat to extend locks for long operations
    - Expired lock detection and takeover
    - Async context manager support
    
    Example:
        lock_manager = ElasticsearchDistributedLock(client)
        
        # Manual acquire/release
        if await lock_manager.acquire("my-lock"):
            try:
                # Do work
                pass
            finally:
                await lock_manager.release("my-lock")
        
        # Context manager
        async with lock_manager.lock("my-lock"):
            # Do work with lock held
            pass
    """
    
    LOCK_INDEX_SUFFIX = "locks"
    
    # Lock document mappings
    MAPPINGS = {
        "properties": {
            "owner": {"type": "keyword"},
            "acquired_at": {"type": "date"},
            "expires_at": {"type": "date"},
            "heartbeat_at": {"type": "date"},
            "context": {"type": "object", "enabled": False},
        }
    }
    
    def __init__(
        self,
        client: "AsyncElasticsearch",
        index_prefix: Optional[str] = None,
        default_ttl_seconds: int = 300,
        heartbeat_interval_seconds: int = 30,
    ):
        """Initialize lock manager.
        
        Args:
            client: AsyncElasticsearch client
            index_prefix: Index prefix (default from ELASTICSEARCH_INDEX_PREFIX env)
            default_ttl_seconds: Default lock TTL in seconds
            heartbeat_interval_seconds: Interval for lock heartbeat
        """
        self.es = client
        self._index_prefix = index_prefix or os.getenv("ELASTICSEARCH_INDEX_PREFIX", "task-framework")
        self.default_ttl = default_ttl_seconds
        self.heartbeat_interval = heartbeat_interval_seconds
        
        # Generate unique worker ID
        self.worker_id = f"{socket.gethostname()}-{os.getpid()}"
        
        # Track active heartbeat tasks
        self._heartbeat_tasks: Dict[str, asyncio.Task] = {}
        self._index_initialized = False
    
    @property
    def _lock_index(self) -> str:
        """Get full lock index name."""
        return f"{self._index_prefix}-{self.LOCK_INDEX_SUFFIX}"
    
    async def ensure_index(self) -> None:
        """Create locks index if it doesn't exist."""
        if self._index_initialized:
            return
            
        try:
            exists = await self.es.indices.exists(index=self._lock_index)
            if not exists:
                await self.es.indices.create(
                    index=self._lock_index,
                    body={
                        "mappings": self.MAPPINGS,
                        "settings": {
                            "number_of_shards": 1,
                            "number_of_replicas": 1,
                        }
                    }
                )
                logger.info("elasticsearch.locks.index_created", index=self._lock_index)
            
            self._index_initialized = True
        except Exception as e:
            if "resource_already_exists_exception" in str(e):
                self._index_initialized = True
            else:
                raise
    
    async def acquire(
        self,
        lock_id: str,
        ttl_seconds: Optional[int] = None,
        wait: bool = False,
        wait_timeout: float = 30.0,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Acquire a distributed lock.
        
        Args:
            lock_id: Unique identifier for the lock
            ttl_seconds: Lock TTL (auto-expires if holder crashes)
            wait: If True, wait for lock to become available
            wait_timeout: Maximum time to wait for lock (seconds)
            context: Optional metadata to store with lock
            
        Returns:
            True if lock acquired, False otherwise
        """
        try:
            from elasticsearch import ConflictError, NotFoundError
        except ImportError:
            raise ImportError("elasticsearch package required")
        
        await self.ensure_index()
        
        ttl = ttl_seconds or self.default_ttl
        now = datetime.now(timezone.utc)
        expires = now + timedelta(seconds=ttl)
        
        lock_doc = {
            "owner": self.worker_id,
            "acquired_at": now.isoformat().replace("+00:00", "Z"),
            "expires_at": expires.isoformat().replace("+00:00", "Z"),
            "heartbeat_at": now.isoformat().replace("+00:00", "Z"),
            "context": context or {},
        }
        
        start_time = asyncio.get_event_loop().time()
        
        while True:
            try:
                # Try to create lock (fails if exists)
                await self.es.create(
                    index=self._lock_index,
                    id=lock_id,
                    document=lock_doc,
                )
                
                logger.debug(
                    "elasticsearch.lock.acquired",
                    lock_id=lock_id,
                    owner=self.worker_id,
                    ttl=ttl,
                )
                
                # Start heartbeat for this lock
                self._start_heartbeat(lock_id, ttl)
                return True
                
            except ConflictError:
                # Lock exists - check if expired
                try:
                    existing = await self.es.get(index=self._lock_index, id=lock_id)
                    expires_at_str = existing["_source"]["expires_at"]
                    expires_at = datetime.fromisoformat(
                        expires_at_str.replace("Z", "+00:00")
                    )
                    
                    if expires_at < now:
                        # Lock expired - try to steal it
                        stolen = await self._steal_lock(
                            lock_id,
                            existing["_seq_no"],
                            existing["_primary_term"],
                            lock_doc,
                        )
                        if stolen:
                            self._start_heartbeat(lock_id, ttl)
                            return True
                    
                    if not wait:
                        logger.debug(
                            "elasticsearch.lock.busy",
                            lock_id=lock_id,
                            owner=existing["_source"]["owner"],
                        )
                        return False
                    
                    # Wait and retry
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed >= wait_timeout:
                        logger.debug(
                            "elasticsearch.lock.timeout",
                            lock_id=lock_id,
                            waited=elapsed,
                        )
                        return False
                    
                    await asyncio.sleep(0.5)  # Backoff
                    now = datetime.now(timezone.utc)  # Refresh now
                    
                except NotFoundError:
                    # Lock was released, retry immediately
                    continue
    
    async def release(self, lock_id: str) -> bool:
        """Release a lock (only if we own it).
        
        Args:
            lock_id: Lock identifier
            
        Returns:
            True if released, False if not owned or not found
        """
        try:
            from elasticsearch import ConflictError, NotFoundError
        except ImportError:
            raise ImportError("elasticsearch package required")
        
        # Stop heartbeat first
        self._stop_heartbeat(lock_id)
        
        try:
            existing = await self.es.get(index=self._lock_index, id=lock_id)
            
            if existing["_source"]["owner"] != self.worker_id:
                logger.warning(
                    "elasticsearch.lock.release_denied",
                    lock_id=lock_id,
                    owner=existing["_source"]["owner"],
                    requester=self.worker_id,
                )
                return False
            
            await self.es.delete(
                index=self._lock_index,
                id=lock_id,
                if_seq_no=existing["_seq_no"],
                if_primary_term=existing["_primary_term"],
            )
            
            logger.debug(
                "elasticsearch.lock.released",
                lock_id=lock_id,
            )
            return True
            
        except (NotFoundError, ConflictError):
            return False
    
    async def is_locked(self, lock_id: str) -> bool:
        """Check if a lock is currently held (not expired).
        
        Args:
            lock_id: Lock identifier
            
        Returns:
            True if lock is held and not expired
        """
        try:
            from elasticsearch import NotFoundError
        except ImportError:
            raise ImportError("elasticsearch package required")
        
        try:
            existing = await self.es.get(index=self._lock_index, id=lock_id)
            expires_at = datetime.fromisoformat(
                existing["_source"]["expires_at"].replace("Z", "+00:00")
            )
            return expires_at > datetime.now(timezone.utc)
        except NotFoundError:
            return False
    
    async def get_lock_info(self, lock_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a lock.
        
        Args:
            lock_id: Lock identifier
            
        Returns:
            Lock info dict or None if not found
        """
        try:
            from elasticsearch import NotFoundError
        except ImportError:
            raise ImportError("elasticsearch package required")
        
        try:
            result = await self.es.get(index=self._lock_index, id=lock_id)
            return result["_source"]
        except NotFoundError:
            return None
    
    async def _steal_lock(
        self,
        lock_id: str,
        seq_no: int,
        primary_term: int,
        new_doc: Dict[str, Any],
    ) -> bool:
        """Attempt to take over an expired lock.
        
        Args:
            lock_id: Lock identifier
            seq_no: Current document sequence number
            primary_term: Current primary term
            new_doc: New lock document
            
        Returns:
            True if lock was stolen successfully
        """
        try:
            from elasticsearch import ConflictError
        except ImportError:
            raise ImportError("elasticsearch package required")
        
        try:
            await self.es.index(
                index=self._lock_index,
                id=lock_id,
                document=new_doc,
                if_seq_no=seq_no,
                if_primary_term=primary_term,
            )
            
            logger.info(
                "elasticsearch.lock.stolen",
                lock_id=lock_id,
                new_owner=self.worker_id,
            )
            return True
        except ConflictError:
            return False
    
    def _start_heartbeat(self, lock_id: str, ttl: int) -> None:
        """Start background heartbeat task for lock.
        
        Args:
            lock_id: Lock identifier
            ttl: Lock TTL for renewal
        """
        async def heartbeat_loop():
            while True:
                await asyncio.sleep(self.heartbeat_interval)
                try:
                    new_expires = datetime.now(timezone.utc) + timedelta(seconds=ttl)
                    await self.es.update(
                        index=self._lock_index,
                        id=lock_id,
                        doc={
                            "heartbeat_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                            "expires_at": new_expires.isoformat().replace("+00:00", "Z"),
                        },
                    )
                    logger.debug(
                        "elasticsearch.lock.heartbeat",
                        lock_id=lock_id,
                    )
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.warning(
                        "elasticsearch.lock.heartbeat_failed",
                        lock_id=lock_id,
                        error=str(e),
                    )
                    break
        
        task = asyncio.create_task(heartbeat_loop())
        self._heartbeat_tasks[lock_id] = task
    
    def _stop_heartbeat(self, lock_id: str) -> None:
        """Stop heartbeat task for lock.
        
        Args:
            lock_id: Lock identifier
        """
        task = self._heartbeat_tasks.pop(lock_id, None)
        if task:
            task.cancel()
    
    @asynccontextmanager
    async def lock(
        self,
        lock_id: str,
        ttl_seconds: Optional[int] = None,
        wait: bool = True,
        wait_timeout: float = 30.0,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Context manager for lock acquisition and automatic release.
        
        Args:
            lock_id: Unique identifier for the lock
            ttl_seconds: Lock TTL
            wait: If True, wait for lock to become available
            wait_timeout: Maximum time to wait (seconds)
            context: Optional metadata
            
        Raises:
            LockAcquisitionError: If lock cannot be acquired
            
        Yields:
            None when lock is held
        """
        acquired = await self.acquire(
            lock_id,
            ttl_seconds=ttl_seconds,
            wait=wait,
            wait_timeout=wait_timeout,
            context=context,
        )
        
        if not acquired:
            raise LockAcquisitionError(f"Failed to acquire lock: {lock_id}")
        
        try:
            yield
        finally:
            await self.release(lock_id)
    
    async def cleanup_expired(self) -> int:
        """Clean up expired locks.
        
        Returns:
            Number of expired locks deleted
        """
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        result = await self.es.delete_by_query(
            index=self._lock_index,
            body={
                "query": {
                    "range": {
                        "expires_at": {"lt": now}
                    }
                }
            },
        )
        
        deleted = result.get("deleted", 0)
        if deleted > 0:
            logger.info(
                "elasticsearch.locks.cleanup",
                deleted=deleted,
            )
        
        return deleted
