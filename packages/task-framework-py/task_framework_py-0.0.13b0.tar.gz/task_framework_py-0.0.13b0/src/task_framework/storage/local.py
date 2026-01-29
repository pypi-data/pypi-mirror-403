"""Local filesystem storage backend implementation."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import quote

import aiofiles
from aiofiles import os as aios

from task_framework.interfaces.storage import FileStorage


class LocalFileStorage(FileStorage):
    """Local filesystem storage backend implementation.
    
    Stores files on the local filesystem with metadata stored in separate JSON files.
    Supports file:// URLs for local access and HTTP URLs when base_url is configured.
    """
    
    def __init__(self, base_path: str = "storage", base_url: Optional[str] = None):
        """Initialize LocalFileStorage with base path.
        
        Args:
            base_path: Base directory for storing files (default: "storage")
            base_url: Base URL for generating HTTP URLs (optional, defaults to file:// URLs)
        """
        self.base_path = Path(base_path)
        self.base_url = base_url
        self.files_dir = self.base_path / "files"
        self.metadata_dir = self.base_path / "metadata"
    
    async def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        await aios.makedirs(self.files_dir, exist_ok=True)
        await aios.makedirs(self.metadata_dir, exist_ok=True)
    
    def _get_file_path(self, file_ref: str) -> Path:
        """Get file path for file_ref.
        
        Args:
            file_ref: File reference identifier
            
        Returns:
            Path object for file
        """
        return self.files_dir / file_ref
    
    def _get_metadata_path(self, file_ref: str) -> Path:
        """Get metadata file path for file_ref.
        
        Args:
            file_ref: File reference identifier
            
        Returns:
            Path object for metadata file
        """
        return self.metadata_dir / f"{file_ref}.json"
    
    async def upload(self, file_ref: str, data: bytes, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Upload a file to storage.
        
        Args:
            file_ref: Unique file reference identifier
            data: File content bytes
            metadata: File metadata dictionary
            
        Raises:
            OSError: If file write fails
        """
        await self._ensure_directories()
        
        file_path = self._get_file_path(file_ref)
        
        # Write file content
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(data)
        
        # Store metadata
        if metadata:
            metadata_path = self._get_metadata_path(file_ref)
            metadata_data = {
                **metadata,
                "created_at": datetime.now(timezone.utc).isoformat() + "Z",
            }
            async with aiofiles.open(metadata_path, "w") as f:
                await f.write(json.dumps(metadata_data, indent=2))
    
    async def download(self, file_ref: str) -> bytes:
        """Download a file from storage.
        
        Args:
            file_ref: File reference identifier
            
        Returns:
            File content bytes
            
        Raises:
            FileNotFoundError: If file doesn't exist
            OSError: If file read fails
        """
        file_path = self._get_file_path(file_ref)
        
        if not await aios.path.exists(file_path):
            raise FileNotFoundError(f"File {file_ref} not found")
        
        async with aiofiles.open(file_path, "rb") as f:
            return await f.read()
    
    async def delete(self, file_ref: str) -> None:
        """Delete a file from storage.
        
        Args:
            file_ref: File reference identifier
            
        Raises:
            FileNotFoundError: If file doesn't exist
            OSError: If file deletion fails
        """
        file_path = self._get_file_path(file_ref)
        metadata_path = self._get_metadata_path(file_ref)
        
        # Delete file
        if await aios.path.exists(file_path):
            await aios.remove(file_path)
        
        # Delete metadata
        if await aios.path.exists(metadata_path):
            await aios.remove(metadata_path)
    
    async def exists(self, file_ref: str) -> bool:
        """Check if a file exists in storage.
        
        Args:
            file_ref: File reference identifier
            
        Returns:
            True if file exists, False otherwise
        """
        file_path = self._get_file_path(file_ref)
        return await aios.path.exists(file_path)
    
    async def get_signed_url(self, file_ref: str, expires_in: int) -> str:
        """Get a pre-signed download URL for a file.
        
        For local filesystem storage:
        - If base_url is configured: Returns HTTP URL
        - Otherwise: Returns file:// URL
        
        Args:
            file_ref: File reference identifier
            expires_in: Expiration time in seconds (0 for permanent/no expiration)
            
        Returns:
            Pre-signed URL string
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not await self.exists(file_ref):
            raise FileNotFoundError(f"File {file_ref} not found")
        
        if self.base_url:
            # Generate HTTP URL
            encoded_file_ref = quote(file_ref, safe="")
            url = f"{self.base_url.rstrip('/')}/files/{encoded_file_ref}"
            if expires_in > 0:
                url += f"?expires_in={expires_in}"
            return url
        else:
            # Generate file:// URL
            file_path = self._get_file_path(file_ref)
            return f"file://{file_path.absolute()}"
    
    async def get_upload_url(self, file_ref: str, expires_in: int) -> str:
        """Get a pre-signed upload URL for a file.
        
        For local filesystem storage:
        - If base_url is configured: Returns HTTP PUT URL
        - Otherwise: Returns file:// URL
        
        Args:
            file_ref: Unique file reference identifier
            expires_in: Expiration time in seconds (0 for permanent/no expiration)
            
        Returns:
            Pre-signed upload URL string
        """
        if self.base_url:
            # Generate HTTP PUT URL
            encoded_file_ref = quote(file_ref, safe="")
            url = f"{self.base_url.rstrip('/')}/files/{encoded_file_ref}"
            if expires_in > 0:
                url += f"?expires_in={expires_in}"
            return url
        else:
            # Generate file:// URL for direct file access
            await self._ensure_directories()
            file_path = self._get_file_path(file_ref)
            return f"file://{file_path.absolute()}"
    
    async def get_metadata(self, file_ref: str) -> Dict[str, Any]:
        """Get file metadata.
        
        Args:
            file_ref: File reference identifier
            
        Returns:
            Dictionary containing file metadata:
            - filename: Optional[str] - Original filename
            - media_type: str - MIME type
            - size: int - File size in bytes
            - sha256: Optional[str] - SHA256 hash (if available)
            - created_at: Optional[str] - Creation timestamp (ISO 8601 UTC)
            - labels: Optional[Dict[str, str]] - Key-value labels
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not await self.exists(file_ref):
            raise FileNotFoundError(f"File {file_ref} not found")
        
        # Try to load metadata from metadata file
        metadata_path = self._get_metadata_path(file_ref)
        if await aios.path.exists(metadata_path):
            async with aiofiles.open(metadata_path, "r") as f:
                metadata_json = await f.read()
                metadata = json.loads(metadata_json)
        else:
            # Fallback: generate metadata from file
            file_path = self._get_file_path(file_ref)
            stat = await aios.stat(file_path)
            metadata = {
                "size": stat.st_size,
                "media_type": "application/octet-stream",
                "created_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat() + "Z",
            }
        
        return metadata

