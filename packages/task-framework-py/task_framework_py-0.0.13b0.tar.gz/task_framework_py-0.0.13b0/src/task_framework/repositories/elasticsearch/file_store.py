"""Elasticsearch-backed file metadata storage.

Stores metadata for standalone file uploads in Elasticsearch, while file content
is stored in S3 or local filesystem.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from task_framework.logging import logger
from task_framework.repositories.elasticsearch.base import ElasticsearchRepository
from task_framework.repositories.elasticsearch.mappings import FILE_MAPPINGS


class ElasticsearchFileMetadataStore:
    """Elasticsearch-backed file metadata storage.
    
    Stores metadata for files uploaded via /files or /uploads endpoints.
    File content is stored separately in S3 or local filesystem.
    """
    
    def __init__(
        self,
        client: "AsyncElasticsearch",
        index_prefix: Optional[str] = None,
    ):
        """Initialize file metadata store.
        
        Args:
            client: AsyncElasticsearch client
            index_prefix: Index prefix (default from env)
        """
        self._repo = _FileMetadataRepo(client, index_prefix)
    
    async def save(
        self,
        file_ref: str,
        filename: Optional[str] = None,
        media_type: Optional[str] = None,
        size: Optional[int] = None,
        sha256: Optional[str] = None,
        created_by: Optional[str] = None,
        labels: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Save or update file metadata.
        
        Args:
            file_ref: Unique file reference (document ID)
            filename: Original filename
            media_type: MIME type
            size: File size in bytes
            sha256: SHA256 hash of file content
            created_by: User or app ID that created the file
            labels: Optional labels/tags
            
        Returns:
            Saved metadata document
        """
        await self._repo.ensure_index(FILE_MAPPINGS)
        
        now = datetime.now(timezone.utc)
        existing = await self._repo.get(file_ref)
        
        if existing:
            # Update existing - preserve created_at
            created_at = existing.get("created_at", now.isoformat().replace("+00:00", "Z"))
            action = "updated"
        else:
            created_at = now.isoformat().replace("+00:00", "Z")
            action = "created"
        
        doc = {
            "file_ref": file_ref,
            "filename": filename if filename else (existing.get("filename") if existing else None),
            "media_type": media_type if media_type else (existing.get("media_type") if existing else None),
            "size": size if size is not None else (existing.get("size") if existing else None),
            "sha256": sha256 if sha256 else (existing.get("sha256") if existing else None),
            "created_at": created_at,
            "updated_at": now.isoformat().replace("+00:00", "Z"),
            "created_by": created_by if created_by else (existing.get("created_by") if existing else None),
            "labels": labels if labels is not None else (existing.get("labels", {}) if existing else {}),
        }
        
        await self._repo.upsert(file_ref, doc)
        
        logger.info(
            f"elasticsearch.file.{action}",
            file_ref=file_ref,
            filename=filename,
            size=size,
        )
        
        return doc
    
    async def get(self, file_ref: str) -> Optional[Dict[str, Any]]:
        """Get file metadata by file_ref.
        
        Args:
            file_ref: File reference
            
        Returns:
            Metadata dict if found, None otherwise
        """
        await self._repo.ensure_index(FILE_MAPPINGS)
        return await self._repo.get(file_ref)
    
    async def exists(self, file_ref: str) -> bool:
        """Check if file metadata exists.
        
        Args:
            file_ref: File reference
            
        Returns:
            True if exists
        """
        await self._repo.ensure_index(FILE_MAPPINGS)
        doc = await self._repo.get(file_ref)
        return doc is not None
    
    async def delete(self, file_ref: str) -> bool:
        """Delete file metadata.
        
        Args:
            file_ref: File reference
            
        Returns:
            True if deleted, False if not found
        """
        await self._repo.ensure_index(FILE_MAPPINGS)
        
        existing = await self._repo.get(file_ref)
        if not existing:
            return False
        
        await self._repo.delete(file_ref)
        
        logger.info(
            "elasticsearch.file.deleted",
            file_ref=file_ref,
        )
        
        return True
    
    async def list_all(
        self,
        limit: int = 100,
        offset: int = 0,
        created_by: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List file metadata.
        
        Args:
            limit: Maximum number of results
            offset: Offset for pagination
            created_by: Filter by creator (optional)
            
        Returns:
            List of metadata dicts
        """
        await self._repo.ensure_index(FILE_MAPPINGS)
        return await self._repo.list_all(
            limit=limit,
            offset=offset,
            created_by=created_by,
        )
    
    async def count(self, created_by: Optional[str] = None) -> int:
        """Count file metadata records.
        
        Args:
            created_by: Filter by creator (optional)
            
        Returns:
            Count of records
        """
        await self._repo.ensure_index(FILE_MAPPINGS)
        return await self._repo.count(created_by=created_by)


class _FileMetadataRepo(ElasticsearchRepository):
    """Internal file metadata repository."""
    
    INDEX_SUFFIX = "files"
    
    async def get(self, file_ref: str) -> Optional[Dict[str, Any]]:
        """Get file metadata document by file_ref."""
        return await self._get_document(file_ref)
    
    async def upsert(self, file_ref: str, doc: Dict[str, Any]) -> None:
        """Create or update file metadata document."""
        await self._index_document(file_ref, doc, refresh=True)
    
    async def delete(self, file_ref: str) -> None:
        """Delete file metadata document."""
        await self._delete_document(file_ref, refresh=True)
    
    async def list_all(
        self,
        limit: int = 100,
        offset: int = 0,
        created_by: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List file metadata documents."""
        if created_by:
            query = {"term": {"created_by": created_by}}
        else:
            query = {"match_all": {}}
        
        # Use direct ES search with from/size for offset pagination
        body = {
            "query": query,
            "sort": [{"created_at": {"order": "desc"}}],
            "size": limit,
            "from": offset,
        }
        
        result = await self.es.search(index=self.index_name, body=body)
        return [hit["_source"] for hit in result.get("hits", {}).get("hits", [])]
    
    async def count(self, created_by: Optional[str] = None) -> int:
        """Count file metadata documents."""
        if created_by:
            query = {"term": {"created_by": created_by}}
        else:
            query = {"match_all": {}}
        
        result = await self._search(query=query, size=0)
        return result.get("hits", {}).get("total", {}).get("value", 0)
