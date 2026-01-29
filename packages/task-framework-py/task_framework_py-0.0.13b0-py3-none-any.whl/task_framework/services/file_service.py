"""File service for file operations including SHA256 computation and URL generation."""

import asyncio
import hashlib
import mimetypes
import re
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, Optional, Tuple

from task_framework.interfaces.storage import FileStorage

# Threshold for using async streaming SHA256 computation (1MB)
LARGE_FILE_THRESHOLD = 1024 * 1024  # 1MB

# File reference format pattern: file_ prefix + 12+ alphanumeric characters
FILE_REF_PATTERN = re.compile(r"^file_[a-zA-Z0-9]{12,}$")
FILE_REF_MIN_LENGTH = 17  # "file_" (5) + 12 chars = 17
FILE_REF_MAX_LENGTH = 128


def validate_file_ref(file_ref: str) -> None:
    """Validate file_ref format and constraints.
    
    Validates that file_ref matches the required pattern:
    - Must start with "file_" prefix
    - Followed by 12+ alphanumeric characters
    - Total length between 17 and 128 characters
    
    Args:
        file_ref: File reference identifier to validate
        
    Raises:
        ValueError: If file_ref format is invalid
    """
    if not file_ref or not isinstance(file_ref, str):
        raise ValueError("file_ref must be a non-empty string")
    
    if len(file_ref) < FILE_REF_MIN_LENGTH:
        raise ValueError(f"file_ref must be at least {FILE_REF_MIN_LENGTH} characters long")
    
    if len(file_ref) > FILE_REF_MAX_LENGTH:
        raise ValueError(f"file_ref must be at most {FILE_REF_MAX_LENGTH} characters long")
    
    if not FILE_REF_PATTERN.match(file_ref):
        raise ValueError(
            f"file_ref must match pattern '^file_[a-zA-Z0-9]{{12,}}$' "
            f"(e.g., 'file_abc123def456')"
        )


def generate_file_ref() -> str:
    """Generate a unique file reference identifier.
    
    Returns:
        Unique file reference string (e.g., "file_a1b2c3d4...")
    """
    # Generate UUID and format as file_ref (full 32 hex chars)
    file_id = str(uuid.uuid4()).replace("-", "")
    return f"file_{file_id}"


def normalize_expiration_time(
    expires_in: Optional[int],
    default_seconds: int,
) -> Tuple[int, Optional[datetime]]:
    """Normalize expiration time and compute expiration timestamp.
    
    Handles expiration time normalization:
    - If expires_in is None, uses default_seconds
    - If expires_in is 0, indicates permanent/no expiration (returns None for expires_at)
    - Otherwise, uses expires_in value and computes expires_at
    
    Args:
        expires_in: Expiration time in seconds (None, 0 for permanent, or positive integer)
        default_seconds: Default expiration time in seconds if expires_in is None
        
    Returns:
        Tuple of (normalized_expires_in, expires_at):
        - normalized_expires_in: Expiration time in seconds (0 for permanent)
        - expires_at: Expiration datetime (None if permanent, otherwise computed datetime)
    """
    # Use default if not provided
    normalized_expires_in = expires_in if expires_in is not None else default_seconds
    
    # Compute expires_at (None for permanent, otherwise compute from current time)
    expires_at = None
    if normalized_expires_in > 0:
        expires_at = datetime.now(UTC) + timedelta(seconds=normalized_expires_in)
    
    return (normalized_expires_in, expires_at)


def compute_sha256(data: bytes) -> str:
    """Compute SHA256 hash of data synchronously (for small files).
    
    Args:
        data: File content bytes
        
    Returns:
        SHA256 hash as hexadecimal string (64 characters)
    """
    return hashlib.sha256(data).hexdigest()


async def compute_sha256_async(data: bytes, chunk_size: int = 8192) -> str:
    """Compute SHA256 hash of data asynchronously using chunked processing (for large files).
    
    Processes data in chunks to avoid blocking the event loop for large files.
    Uses asyncio.to_thread for CPU-bound hashing operations.
    
    Args:
        data: File content bytes
        chunk_size: Chunk size for processing (default: 8KB)
        
    Returns:
        SHA256 hash as hexadecimal string (64 characters)
    """
    sha256 = hashlib.sha256()
    
    # Process in chunks to avoid blocking event loop
    for i in range(0, len(data), chunk_size):
        chunk = data[i : i + chunk_size]
        # Run hash update in thread pool to avoid blocking event loop
        await asyncio.to_thread(sha256.update, chunk)
    
    return sha256.hexdigest()


async def compute_sha256_optimized(data: bytes) -> str:
    """Compute SHA256 hash with automatic optimization based on file size.
    
    - Small files (< 1MB): Synchronous computation for performance
    - Large files (>= 1MB): Async chunked computation to avoid blocking event loop
    
    Args:
        data: File content bytes
        
    Returns:
        SHA256 hash as hexadecimal string (64 characters)
    """
    if len(data) < LARGE_FILE_THRESHOLD:
        # Small files: use synchronous computation (faster for small data)
        return compute_sha256(data)
    else:
        # Large files: use async chunked computation (non-blocking)
        return await compute_sha256_async(data)


def infer_media_type(content_type: Optional[str] = None, filename: Optional[str] = None) -> str:
    """Infer media type from Content-Type header or filename extension.
    
    Priority order:
    1. Content-Type header (if provided and valid)
    2. Filename extension (using mimetypes library)
    3. Fallback to application/octet-stream
    
    Args:
        content_type: Content-Type header value
        filename: Filename with extension
        
    Returns:
        MIME type string
    """
    # Try Content-Type header first
    if content_type and "/" in content_type:
        # Extract base MIME type (remove parameters like charset)
        base_type = content_type.split(";")[0].strip()
        if base_type and "/" in base_type:
            return base_type
    
    # Try filename extension
    if filename:
        guessed_type, _ = mimetypes.guess_type(filename)
        if guessed_type:
            return guessed_type
    
    # Fallback to application/octet-stream
    return "application/octet-stream"


class FileService:
    """Service for file operations."""
    
    def __init__(self, storage: FileStorage):
        """Initialize FileService with storage backend.
        
        Args:
            storage: FileStorage interface implementation
        """
        self.storage = storage

    async def generate_upload_url(self, file_ref: str, expires_in: int) -> str:
        """Generate a pre-signed upload URL for a file.
        
        Args:
            file_ref: Unique file reference identifier
            expires_in: Expiration time in seconds (0 for permanent/no expiration)
            
        Returns:
            Pre-signed upload URL
            
        Raises:
            ValueError: If file_ref format is invalid
            Storage backend specific exceptions on failure
        """
        validate_file_ref(file_ref)
        return await self.storage.get_upload_url(file_ref=file_ref, expires_in=expires_in)

    async def upload_file_direct(
        self,
        file_ref: str,
        data: bytes,
        filename: Optional[str] = None,
        media_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Upload a file directly to storage.
        
        **Concurrent Upload Handling**: If multiple uploads occur to the same file_ref,
        the last write wins - the latest upload succeeds and overwrites earlier uploads.
        Storage backend implementations handle this automatically.
        
        **Partial Upload Cleanup**: If uploads are interrupted or fail (e.g., network errors,
        storage backend unavailability), the storage backend automatically cleans up partial
        or failed uploads. Clients should retry uploads using the same or new pre-signed URL
        if needed. The framework does not perform automatic retries - retry logic is handled
        by client applications.
        
        Args:
            file_ref: Unique file reference identifier
            data: File content bytes
            filename: Original filename (optional)
            media_type: MIME type (optional, will be inferred if not provided)
            
        Returns:
            Dictionary with file metadata including sha256
            
        Raises:
            ValueError: If file_ref format is invalid
            Storage backend specific exceptions on failure
        """
        validate_file_ref(file_ref)
        # Infer media type if not provided
        if not media_type:
            media_type = infer_media_type(filename=filename)
        
        # Compute SHA256 hash (optimized: sync for small files, async for large files)
        sha256 = await compute_sha256_optimized(data)
        
        # Prepare metadata
        metadata = {
            "filename": filename,
            "media_type": media_type,
            "size": len(data),
            "sha256": sha256,
        }
        
        # Upload to storage backend
        await self.storage.upload(file_ref=file_ref, data=data, metadata=metadata)
        
        return metadata
    
    async def generate_download_url(self, file_ref: str, expires_in: int) -> str:
        """Generate a pre-signed download URL for a file.
        
        Args:
            file_ref: Unique file reference identifier
            expires_in: Expiration time in seconds (0 for permanent/no expiration)
            
        Returns:
            Pre-signed download URL
            
        Raises:
            ValueError: If file_ref format is invalid
            Storage backend specific exceptions on failure
        """
        validate_file_ref(file_ref)
        return await self.storage.get_signed_url(file_ref=file_ref, expires_in=expires_in)

    async def check_file_exists(self, file_ref: str) -> bool:
        """Check if a file exists in storage.
        
        Args:
            file_ref: Unique file reference identifier
            
        Returns:
            True if file exists, False otherwise
            
        Raises:
            ValueError: If file_ref format is invalid
            Storage backend specific exceptions on failure
        """
        validate_file_ref(file_ref)
        return await self.storage.exists(file_ref=file_ref)

    async def get_file_metadata(self, file_ref: str) -> Dict[str, Any]:
        """Get file metadata from storage.
        
        Args:
            file_ref: Unique file reference identifier
            
        Returns:
            Dictionary containing file metadata
            
        Raises:
            ValueError: If file_ref format is invalid
            Storage backend specific exceptions if file doesn't exist
        """
        validate_file_ref(file_ref)
        return await self.storage.get_metadata(file_ref=file_ref)

