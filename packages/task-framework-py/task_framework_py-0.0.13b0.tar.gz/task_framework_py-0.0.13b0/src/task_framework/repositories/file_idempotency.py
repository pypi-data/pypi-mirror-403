"""File-based IdempotencyStore implementation."""

import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import aiofiles
from aiofiles import os as aios

from task_framework.interfaces.idempotency import IdempotencyStore
from task_framework.models.thread import Thread

if TYPE_CHECKING:
    from task_framework.interfaces.database import Database


class FileIdempotencyStore(IdempotencyStore):
    """File-based IdempotencyStore implementation."""

    def __init__(self, base_path: str = "data", database: Optional["Database"] = None) -> None:
        """Initialize FileIdempotencyStore.
        
        Args:
            base_path: Base directory for storing data files
            database: Database instance for retrieving threads by ID
        """
        self.base_path = Path(base_path)
        self.idempotency_dir = self.base_path / "indexes" / "idempotency"
        self.database = database

    def _hash_key(self, user_id: str, app_id: str, idempotency_key: str) -> str:
        """Generate hash for idempotency key.
        
        Args:
            user_id: User identifier
            app_id: Application identifier
            idempotency_key: Idempotency key
            
        Returns:
            SHA-256 hash of {user_id}:{app_id}:{idempotency_key}
        """
        key_string = f"{user_id}:{app_id}:{idempotency_key}"
        return hashlib.sha256(key_string.encode()).hexdigest()

    async def _ensure_directories(self) -> None:
        """Ensure idempotency directory exists."""
        await aios.makedirs(self.idempotency_dir, exist_ok=True)

    async def get(self, idempotency_key: str, user_id: str, app_id: str) -> Optional[Thread]:
        """Get existing thread by idempotency key.
        
        Args:
            idempotency_key: The idempotency key provided by the client
            user_id: User identifier from AuthenticatedRequest
            app_id: Application identifier from AuthenticatedRequest
            
        Returns:
            Existing Thread if found, None otherwise
        """
        if not self.database:
            return None
        
        hash_key = self._hash_key(user_id, app_id, idempotency_key)
        file_path = self.idempotency_dir / f"{hash_key}.json"
        
        if not await aios.path.exists(file_path):
            return None
        
        try:
            async with aiofiles.open(file_path, "r") as f:
                content = await f.read()
                data = json.loads(content)
                thread_id = data.get("thread_id")
                
                if thread_id:
                    return await self.database.get_thread(thread_id)
        except (json.JSONDecodeError, ValueError, KeyError):
            return None
        
        return None

    async def set(self, idempotency_key: str, user_id: str, app_id: str, thread_id: str) -> None:
        """Store idempotency key mapping to thread_id.
        
        Args:
            idempotency_key: The idempotency key provided by the client
            user_id: User identifier from AuthenticatedRequest
            app_id: Application identifier from AuthenticatedRequest
            thread_id: The thread ID to associate with this idempotency key
        """
        await self._ensure_directories()
        
        hash_key = self._hash_key(user_id, app_id, idempotency_key)
        file_path = self.idempotency_dir / f"{hash_key}.json"
        
        from datetime import datetime, timezone
        
        data = {
            "thread_id": thread_id,
            "created_at": datetime.now(timezone.utc).isoformat() + "Z",
        }
        
        async with aiofiles.open(file_path, "w") as f:
            await f.write(json.dumps(data, indent=2))

