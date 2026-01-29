"""S3-based task storage for zip packages.

Provides dual storage pattern: S3 as source of truth + local cache for execution.
Inherits from TaskStorage for full compatibility with local directory operations.
"""

import os
from pathlib import Path
from typing import List, Optional

from task_framework.logging import logger
from task_framework.repositories.task_storage import TaskStorage


class S3TaskStorage(TaskStorage):
    """S3 storage for task definition zip packages.
    
    Inherits from TaskStorage to provide full interface compatibility.
    Overrides zip-related methods to use S3 as source of truth.
    
    Implements write-through pattern:
    - Upload: Write to S3 first (source of truth), then cache locally
    - Download: Try local first, fall back to S3 and cache
    
    Example:
        storage = S3TaskStorage.from_env(base_path="./data")
        
        # Upload zip (goes to both S3 and local)
        await storage.save_zip_file("my-task-1.0.0.zip", content)
        
        # Local task directories work exactly like TaskStorage
        paths = await storage.create_task_directories("my-task", "1.0.0")
    """
    
    def __init__(
        self,
        bucket: str,
        base_path: str = ".",
        region: str = "us-east-1",
        endpoint_url: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        path_prefix: str = "",
    ):
        """Initialize S3 task storage.
        
        Args:
            bucket: S3 bucket name
            base_path: Base path for local task directories
            region: AWS region
            endpoint_url: S3 endpoint URL (for MinIO)
            access_key_id: AWS access key ID
            secret_access_key: AWS secret access key
            path_prefix: Prefix for S3 keys
        """
        # Initialize parent TaskStorage for local directory operations
        super().__init__(base_path=base_path)
        
        # S3 configuration
        self.bucket = bucket
        self.region = region
        self.endpoint_url = endpoint_url
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.path_prefix = path_prefix.strip("/")
        
        self._session = None
    
    @classmethod
    def from_env(cls, base_path: str = ".") -> "S3TaskStorage":
        """Create from environment variables.
        
        Args:
            base_path: Base path for local task directories
            
        Returns:
            Configured S3TaskStorage
        """
        bucket = os.getenv("S3_BUCKET")
        if not bucket:
            raise ValueError("S3_BUCKET environment variable is required")
        
        return cls(
            bucket=bucket,
            base_path=base_path,
            region=os.getenv("S3_REGION", "us-east-1"),
            endpoint_url=os.getenv("S3_ENDPOINT_URL"),
            access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            path_prefix=os.getenv("S3_PATH_PREFIX", ""),
        )
    
    def _get_session(self):
        """Get or create aiobotocore session."""
        if self._session is None:
            try:
                from aiobotocore.session import get_session
            except ImportError:
                raise ImportError(
                    "aiobotocore package is required for S3 storage. "
                    "Install with: pip install 'task-framework[s3]'"
                )
            self._session = get_session()
        return self._session
    
    def _get_client_config(self) -> dict:
        """Get boto client configuration."""
        config = {
            "region_name": self.region,
        }
        if self.endpoint_url:
            config["endpoint_url"] = self.endpoint_url
        if self.access_key_id and self.secret_access_key:
            config["aws_access_key_id"] = self.access_key_id
            config["aws_secret_access_key"] = self.secret_access_key
        return config
    
    def _get_s3_key(self, filename: str) -> str:
        """Get S3 key for zip file."""
        if self.path_prefix:
            return f"{self.path_prefix}/task-definitions/{filename}"
        return f"task-definitions/{filename}"
    
    # =========================================================================
    # Override zip-related methods to use S3
    # =========================================================================
    
    async def save_zip_file(self, filename: str, content: bytes) -> Path:
        """Save a zip file to S3 and local cache.
        
        Write-through pattern: S3 first (source of truth), then local.
        
        Args:
            filename: Name for the zip file
            content: Zip file content
            
        Returns:
            Path to the saved zip file
        """
        import aiofiles
        
        # Ensure filename ends with .zip
        if not filename.endswith(".zip"):
            filename = f"{filename}.zip"
        
        session = self._get_session()
        
        # Upload to S3 first (source of truth)
        async with session.create_client("s3", **self._get_client_config()) as client:
            await client.put_object(
                Bucket=self.bucket,
                Key=self._get_s3_key(filename),
                Body=content,
                ContentType="application/zip",
            )
            
            logger.info(
                "s3.task_storage.uploaded",
                filename=filename,
                size=len(content),
            )
        
        # Also save locally for fast access
        return await super().save_zip_file(filename, content)
    
    async def list_zip_files(self) -> List[Path]:
        """List all zip files (from S3 + local cache).
        
        Returns:
            List of Path objects to zip files
        """
        # Get local files first
        local_files = await super().list_zip_files()
        local_names = {f.name for f in local_files}
        
        # Also check S3 for any missing files
        session = self._get_session()
        prefix = self._get_s3_key("")
        
        async with session.create_client("s3", **self._get_client_config()) as client:
            try:
                paginator = client.get_paginator("list_objects_v2")
                
                async for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
                    for obj in page.get("Contents", []):
                        key = obj["Key"]
                        if key.endswith(".zip"):
                            filename = key.split("/")[-1]
                            if filename not in local_names:
                                # File exists in S3 but not locally
                                local_files.append(self.task_definitions_dir / filename)
                
            except Exception as e:
                logger.error(
                    "s3.task_storage.list_failed",
                    error=str(e),
                )
        
        return local_files
    
    async def delete_zip_file(self, zip_path: Path) -> bool:
        """Delete a zip file from S3 and local cache.
        
        Args:
            zip_path: Path to the zip file
            
        Returns:
            True if deleted successfully
        """
        filename = zip_path.name
        deleted = False
        
        # Delete from S3
        session = self._get_session()
        
        async with session.create_client("s3", **self._get_client_config()) as client:
            try:
                await client.delete_object(
                    Bucket=self.bucket,
                    Key=self._get_s3_key(filename),
                )
                deleted = True
                logger.debug(
                    "s3.task_storage.deleted_from_s3",
                    filename=filename,
                )
            except Exception:
                pass
        
        # Delete from local
        local_deleted = await super().delete_zip_file(zip_path)
        
        return deleted or local_deleted
    
    async def sync_from_s3(self) -> int:
        """Download all zips from S3 to local cache.
        
        Returns:
            Number of files synced
        """
        import aiofiles
        import aiofiles.os as aios
        
        session = self._get_session()
        prefix = self._get_s3_key("")
        synced = 0
        
        async with session.create_client("s3", **self._get_client_config()) as client:
            try:
                paginator = client.get_paginator("list_objects_v2")
                
                async for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
                    for obj in page.get("Contents", []):
                        key = obj["Key"]
                        if key.endswith(".zip"):
                            filename = key.split("/")[-1]
                            local_path = self.task_definitions_dir / filename
                            
                            if not await aios.path.exists(local_path):
                                # Download from S3
                                response = await client.get_object(
                                    Bucket=self.bucket,
                                    Key=key,
                                )
                                async with response["Body"] as stream:
                                    content = await stream.read()
                                
                                await self._ensure_base_directories()
                                async with aiofiles.open(local_path, "wb") as f:
                                    await f.write(content)
                                
                                synced += 1
                
            except Exception as e:
                logger.error(
                    "s3.task_storage.sync_failed",
                    error=str(e),
                )
        
        logger.info(
            "s3.task_storage.sync_complete",
            synced=synced,
        )
        
        return synced
