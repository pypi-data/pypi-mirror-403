"""SHA256 computation utility functions."""

import hashlib
from pathlib import Path
from typing import Optional

import aiofiles


async def compute_sha256(data: bytes) -> str:
    """Compute SHA256 hash of data.
    
    Args:
        data: Bytes to hash
        
    Returns:
        SHA256 hex digest
    """
    return hashlib.sha256(data).hexdigest()


async def compute_sha256_streaming(file_path: str) -> str:
    """Compute SHA256 hash of file using streaming (for large files).
    
    Args:
        file_path: Path to file to hash
        
    Returns:
        SHA256 hex digest
    """
    sha256 = hashlib.sha256()
    
    async with aiofiles.open(file_path, "rb") as f:
        while chunk := await f.read(8192):  # Read in 8KB chunks
            sha256.update(chunk)
    
    return sha256.hexdigest()


async def compute_sha256_from_file_ref(file_ref: str, storage) -> Optional[str]:
    """Compute SHA256 hash from file reference using storage interface.
    
    Args:
        file_ref: File reference identifier
        storage: FileStorage interface implementation
        
    Returns:
        SHA256 hex digest, or None if file not found
    """
    try:
        # Get file content from storage
        file_data = await storage.download(file_ref)
        return await compute_sha256(file_data)
    except Exception:
        return None

