"""Abstract base class interfaces for pluggable components."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class FileStorage(ABC):
    """Abstract base class for file storage interface."""

    @abstractmethod
    async def upload(self, file_ref: str, data: bytes, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Upload a file to storage."""
        pass

    @abstractmethod
    async def download(self, file_ref: str) -> bytes:
        """Download a file from storage."""
        pass

    @abstractmethod
    async def delete(self, file_ref: str) -> None:
        """Delete a file from storage."""
        pass

    @abstractmethod
    async def exists(self, file_ref: str) -> bool:
        """Check if a file exists in storage."""
        pass

    @abstractmethod
    async def get_signed_url(self, file_ref: str, expires_in: int) -> str:
        """Get a signed URL for a file."""
        pass

    @abstractmethod
    async def get_upload_url(self, file_ref: str, expires_in: int) -> str:
        """Get a pre-signed upload URL for a file.
        
        Args:
            file_ref: Unique file reference identifier
            expires_in: Expiration time in seconds (0 for permanent/no expiration)
            
        Returns:
            Pre-signed upload URL
            
        Raises:
            Storage backend specific exceptions on failure
        """
        pass

    @abstractmethod
    async def get_metadata(self, file_ref: str) -> Dict[str, Any]:
        """Get file metadata.
        
        Args:
            file_ref: Unique file reference identifier
            
        Returns:
            Dictionary containing file metadata:
            - filename: Optional[str] - Original filename
            - media_type: str - MIME type
            - size: int - File size in bytes
            - sha256: Optional[str] - SHA256 hash (if available)
            - created_at: Optional[str] - Creation timestamp (ISO 8601 UTC)
            - labels: Optional[Dict[str, str]] - Key-value labels
            
        Raises:
            Storage backend specific exceptions if file doesn't exist
        """
        pass

