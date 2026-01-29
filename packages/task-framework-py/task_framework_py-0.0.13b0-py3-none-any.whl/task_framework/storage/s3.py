"""S3-compatible file storage backend.

Supports both AWS S3 and S3-compatible services like MinIO.
"""

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from task_framework.interfaces.storage import FileStorage
from task_framework.logging import logger


class S3FileStorage(FileStorage):
    """S3-compatible file storage implementation.
    
    Supports:
    - AWS S3 (using region)
    - MinIO and other S3-compatible services (using endpoint_url)
    
    Files are stored with their metadata in a companion JSON object.
    
    Example:
        # AWS S3
        storage = S3FileStorage(
            bucket="my-bucket",
            region="us-east-1",
        )
        
        # MinIO
        storage = S3FileStorage(
            bucket="my-bucket",
            endpoint_url="http://localhost:9000",
            access_key_id="minioadmin",
            secret_access_key="minioadmin",
        )
        
        # From environment
        storage = S3FileStorage.from_env()
    """
    
    def __init__(
        self,
        bucket: str,
        region: str = "us-east-1",
        endpoint_url: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        path_prefix: str = "",
        presigned_url_expiration: int = 3600,
    ):
        """Initialize S3 file storage.
        
        Args:
            bucket: S3 bucket name
            region: AWS region (for AWS S3)
            endpoint_url: S3 endpoint URL (for MinIO/S3-compatible)
            access_key_id: AWS access key ID (optional, can use IAM role)
            secret_access_key: AWS secret access key
            path_prefix: Prefix for all object keys
            presigned_url_expiration: Default presigned URL expiration in seconds
        """
        self.bucket = bucket
        self.region = region
        self.endpoint_url = endpoint_url
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.path_prefix = path_prefix.strip("/")
        self.presigned_url_expiration = presigned_url_expiration
        
        # Lazy-loaded session
        self._session = None
        
        logger.info(
            "s3.storage.initialized",
            bucket=bucket,
            region=region,
            endpoint_url=endpoint_url,
            path_prefix=path_prefix,
        )
    
    @classmethod
    def from_env(cls) -> "S3FileStorage":
        """Create S3 storage from environment variables.
        
        Environment variables:
            S3_BUCKET: Bucket name (required)
            S3_REGION: AWS region (default: us-east-1)
            S3_ENDPOINT_URL: Endpoint URL for MinIO/S3-compatible
            AWS_ACCESS_KEY_ID: Access key ID
            AWS_SECRET_ACCESS_KEY: Secret access key
            S3_PATH_PREFIX: Object key prefix
            S3_PRESIGNED_URL_EXPIRATION: Presigned URL TTL in seconds
            
        Returns:
            Configured S3FileStorage
            
        Raises:
            ValueError: If S3_BUCKET is not set
        """
        bucket = os.getenv("S3_BUCKET")
        if not bucket:
            raise ValueError("S3_BUCKET environment variable is required")
        
        return cls(
            bucket=bucket,
            region=os.getenv("S3_REGION", "us-east-1"),
            endpoint_url=os.getenv("S3_ENDPOINT_URL"),
            access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            path_prefix=os.getenv("S3_PATH_PREFIX", ""),
            presigned_url_expiration=int(os.getenv("S3_PRESIGNED_URL_EXPIRATION", "3600")),
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
    
    def _get_file_key(self, file_ref: str) -> str:
        """Get S3 key for file content."""
        if self.path_prefix:
            return f"{self.path_prefix}/files/{file_ref}"
        return f"files/{file_ref}"
    
    def _get_metadata_key(self, file_ref: str) -> str:
        """Get S3 key for file metadata."""
        if self.path_prefix:
            return f"{self.path_prefix}/metadata/{file_ref}.json"
        return f"metadata/{file_ref}.json"
    
    async def upload(
        self,
        file_ref: str,
        data: bytes,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Upload a file to S3.
        
        Args:
            file_ref: Unique file reference identifier
            data: File content bytes
            metadata: Optional file metadata
        """
        session = self._get_session()
        
        async with session.create_client("s3", **self._get_client_config()) as client:
            # Determine content type
            content_type = "application/octet-stream"
            if metadata and metadata.get("media_type"):
                content_type = metadata["media_type"]
            
            # Upload file content
            await client.put_object(
                Bucket=self.bucket,
                Key=self._get_file_key(file_ref),
                Body=data,
                ContentType=content_type,
            )
            
            # Store metadata as companion object
            meta_doc = metadata.copy() if metadata else {}
            meta_doc["size"] = len(data)
            meta_doc["created_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            
            await client.put_object(
                Bucket=self.bucket,
                Key=self._get_metadata_key(file_ref),
                Body=json.dumps(meta_doc).encode(),
                ContentType="application/json",
            )
            
            logger.debug(
                "s3.upload.complete",
                file_ref=file_ref,
                size=len(data),
            )
    
    async def download(self, file_ref: str) -> bytes:
        """Download a file from S3.
        
        Args:
            file_ref: Unique file reference identifier
            
        Returns:
            File content bytes
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        session = self._get_session()
        
        async with session.create_client("s3", **self._get_client_config()) as client:
            try:
                response = await client.get_object(
                    Bucket=self.bucket,
                    Key=self._get_file_key(file_ref),
                )
                async with response["Body"] as stream:
                    data = await stream.read()
                
                logger.debug(
                    "s3.download.complete",
                    file_ref=file_ref,
                    size=len(data),
                )
                return data
                
            except client.exceptions.NoSuchKey:
                raise FileNotFoundError(f"File not found: {file_ref}")
            except Exception as e:
                if "NoSuchKey" in str(e) or "404" in str(e):
                    raise FileNotFoundError(f"File not found: {file_ref}")
                raise
    
    async def delete(self, file_ref: str) -> None:
        """Delete a file and its metadata from S3.
        
        Args:
            file_ref: Unique file reference identifier
        """
        session = self._get_session()
        
        async with session.create_client("s3", **self._get_client_config()) as client:
            # Delete file content
            await client.delete_object(
                Bucket=self.bucket,
                Key=self._get_file_key(file_ref),
            )
            
            # Delete metadata
            try:
                await client.delete_object(
                    Bucket=self.bucket,
                    Key=self._get_metadata_key(file_ref),
                )
            except Exception:
                pass  # Metadata may not exist
            
            logger.debug(
                "s3.delete.complete",
                file_ref=file_ref,
            )
    
    async def exists(self, file_ref: str) -> bool:
        """Check if a file exists in S3.
        
        Args:
            file_ref: Unique file reference identifier
            
        Returns:
            True if file exists
        """
        session = self._get_session()
        
        async with session.create_client("s3", **self._get_client_config()) as client:
            try:
                await client.head_object(
                    Bucket=self.bucket,
                    Key=self._get_file_key(file_ref),
                )
                return True
            except Exception:
                return False
    
    async def get_signed_url(self, file_ref: str, expires_in: int) -> str:
        """Generate a pre-signed download URL.
        
        Args:
            file_ref: Unique file reference identifier
            expires_in: URL expiration time in seconds (0 for default)
            
        Returns:
            Pre-signed download URL
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        # Verify file exists first
        if not await self.exists(file_ref):
            raise FileNotFoundError(f"File not found: {file_ref}")
        
        expiration = expires_in if expires_in > 0 else self.presigned_url_expiration
        
        session = self._get_session()
        
        async with session.create_client("s3", **self._get_client_config()) as client:
            url = await client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self.bucket,
                    "Key": self._get_file_key(file_ref),
                },
                ExpiresIn=expiration,
            )
            
            logger.debug(
                "s3.signed_url.download",
                file_ref=file_ref,
                expires_in=expiration,
            )
            return url
    
    async def get_upload_url(self, file_ref: str, expires_in: int) -> str:
        """Generate a pre-signed upload URL.
        
        Args:
            file_ref: Unique file reference identifier
            expires_in: URL expiration time in seconds (0 for default)
            
        Returns:
            Pre-signed upload URL
        """
        expiration = expires_in if expires_in > 0 else self.presigned_url_expiration
        
        session = self._get_session()
        
        async with session.create_client("s3", **self._get_client_config()) as client:
            url = await client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": self.bucket,
                    "Key": self._get_file_key(file_ref),
                },
                ExpiresIn=expiration,
            )
            
            logger.debug(
                "s3.signed_url.upload",
                file_ref=file_ref,
                expires_in=expiration,
            )
            return url
    
    async def get_metadata(self, file_ref: str) -> Dict[str, Any]:
        """Get file metadata.
        
        Args:
            file_ref: Unique file reference identifier
            
        Returns:
            File metadata dictionary
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        session = self._get_session()
        
        async with session.create_client("s3", **self._get_client_config()) as client:
            # Try to get metadata from companion object
            try:
                response = await client.get_object(
                    Bucket=self.bucket,
                    Key=self._get_metadata_key(file_ref),
                )
                async with response["Body"] as stream:
                    return json.loads(await stream.read())
                    
            except Exception:
                # Fall back to head_object for basic metadata
                try:
                    head = await client.head_object(
                        Bucket=self.bucket,
                        Key=self._get_file_key(file_ref),
                    )
                    return {
                        "size": head["ContentLength"],
                        "media_type": head.get("ContentType", "application/octet-stream"),
                        "created_at": head["LastModified"].isoformat() if head.get("LastModified") else None,
                    }
                except Exception as e:
                    if "NoSuchKey" in str(e) or "404" in str(e):
                        raise FileNotFoundError(f"File not found: {file_ref}")
                    raise
