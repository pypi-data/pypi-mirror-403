"""IdempotencyStore interface for storing and retrieving idempotency keys."""

from abc import ABC, abstractmethod
from typing import Optional

from task_framework.models.thread import Thread


class IdempotencyStore(ABC):
    """Abstract base class for idempotency key storage."""

    @abstractmethod
    async def get(self, idempotency_key: str, user_id: str, app_id: str) -> Optional[Thread]:
        """Get existing thread by idempotency key (scoped per user/app combination).
        
        Args:
            idempotency_key: The idempotency key provided by the client
            user_id: User identifier from AuthenticatedRequest
            app_id: Application identifier from AuthenticatedRequest
            
        Returns:
            Existing Thread if found, None otherwise
        """
        pass

    @abstractmethod
    async def set(self, idempotency_key: str, user_id: str, app_id: str, thread_id: str) -> None:
        """Store idempotency key mapping to thread_id.
        
        Args:
            idempotency_key: The idempotency key provided by the client
            user_id: User identifier from AuthenticatedRequest
            app_id: Application identifier from AuthenticatedRequest
            thread_id: The thread ID to associate with this idempotency key
            
        Note:
            Key format: {user_id}:{app_id}:{idempotency_key}
            Storage key should be a hash of this combination for security
        """
        pass

