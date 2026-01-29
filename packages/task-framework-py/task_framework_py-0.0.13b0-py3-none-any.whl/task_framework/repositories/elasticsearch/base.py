"""Base class for Elasticsearch repositories.

Provides common operations for ES-backed repositories including:
- Index management
- Optimistic concurrency control (OCC)
- Common query patterns
"""

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypeVar, Generic

from task_framework.logging import logger

# Type variable for model classes
T = TypeVar("T")


class ElasticsearchRepository(Generic[T]):
    """Base repository with common Elasticsearch operations.
    
    Provides:
    - Index name generation with configurable prefix
    - Index creation with mappings
    - Document CRUD with optimistic concurrency control
    - Pagination support with search_after
    
    Example:
        class MyRepository(ElasticsearchRepository[MyModel]):
            INDEX_SUFFIX = "my-index"
            
            async def create(self, item: MyModel) -> None:
                await self._index_document(item.id, item.model_dump())
    """
    
    INDEX_SUFFIX: str = ""  # Override in subclass
    
    def __init__(
        self,
        client: "AsyncElasticsearch",
        index_prefix: Optional[str] = None,
    ):
        """Initialize repository.
        
        Args:
            client: AsyncElasticsearch client instance
            index_prefix: Index name prefix (default from env: ELASTICSEARCH_INDEX_PREFIX)
        """
        self.es = client
        self._index_prefix = index_prefix or os.getenv("ELASTICSEARCH_INDEX_PREFIX", "task-framework")
        self._index_initialized = False
    
    @property
    def index_name(self) -> str:
        """Get full index name with prefix."""
        if not self.INDEX_SUFFIX:
            raise ValueError("INDEX_SUFFIX must be set in subclass")
        return f"{self._index_prefix}-{self.INDEX_SUFFIX}"
    
    def _make_index_name(self, suffix: str) -> str:
        """Generate index name for a specific suffix."""
        return f"{self._index_prefix}-{suffix}"
    
    async def ensure_index(self, mappings: Optional[Dict[str, Any]] = None) -> None:
        """Create index if it doesn't exist.
        
        Args:
            mappings: Optional ES mappings definition
        """
        if self._index_initialized:
            return
            
        try:
            exists = await self.es.indices.exists(index=self.index_name)
            if not exists:
                body = {}
                if mappings:
                    body["mappings"] = mappings
                body["settings"] = {
                    "number_of_shards": 1,
                    "number_of_replicas": 1,
                }
                
                await self.es.indices.create(index=self.index_name, body=body)
                logger.info(
                    "elasticsearch.index.created",
                    index=self.index_name,
                )
            
            self._index_initialized = True
        except Exception as e:
            # Index might have been created by another worker
            if "resource_already_exists_exception" in str(e):
                self._index_initialized = True
            else:
                logger.error(
                    "elasticsearch.index.create_failed",
                    index=self.index_name,
                    error=str(e),
                )
                raise
    
    async def _index_document(
        self,
        doc_id: str,
        document: Dict[str, Any],
        refresh: bool = False,
    ) -> None:
        """Index a document (create or replace).
        
        Args:
            doc_id: Document ID
            document: Document body
            refresh: Whether to refresh index immediately
        """
        await self.es.index(
            index=self.index_name,
            id=doc_id,
            document=document,
            refresh=refresh,
        )
    
    async def _create_document(
        self,
        doc_id: str,
        document: Dict[str, Any],
        refresh: bool = False,
    ) -> bool:
        """Create a new document (fails if exists).
        
        Args:
            doc_id: Document ID
            document: Document body
            refresh: Whether to refresh index immediately
            
        Returns:
            True if created, False if already exists
        """
        try:
            from elasticsearch import ConflictError
        except ImportError:
            raise ImportError("elasticsearch package required")
            
        try:
            await self.es.create(
                index=self.index_name,
                id=doc_id,
                document=document,
                refresh=refresh,
            )
            return True
        except ConflictError:
            return False
    
    async def _get_document(
        self,
        doc_id: str,
        include_version: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Get a document by ID.
        
        Args:
            doc_id: Document ID
            include_version: Include _seq_no and _primary_term for OCC
            
        Returns:
            Document source, or None if not found
        """
        try:
            from elasticsearch import NotFoundError
        except ImportError:
            raise ImportError("elasticsearch package required")
            
        try:
            result = await self.es.get(index=self.index_name, id=doc_id)
            
            if include_version:
                return {
                    "_source": result["_source"],
                    "_seq_no": result["_seq_no"],
                    "_primary_term": result["_primary_term"],
                }
            return result["_source"]
        except NotFoundError:
            return None
    
    async def _update_document(
        self,
        doc_id: str,
        doc: Dict[str, Any],
        seq_no: Optional[int] = None,
        primary_term: Optional[int] = None,
        refresh: bool = False,
    ) -> bool:
        """Update a document with optional OCC.
        
        Args:
            doc_id: Document ID
            doc: Fields to update
            seq_no: Sequence number for OCC (optional)
            primary_term: Primary term for OCC (optional)
            refresh: Whether to refresh index immediately
            
        Returns:
            True if updated, False if conflict
        """
        try:
            from elasticsearch import ConflictError
        except ImportError:
            raise ImportError("elasticsearch package required")
            
        try:
            kwargs = {
                "index": self.index_name,
                "id": doc_id,
                "doc": doc,
                "refresh": refresh,
            }
            
            if seq_no is not None and primary_term is not None:
                kwargs["if_seq_no"] = seq_no
                kwargs["if_primary_term"] = primary_term
            
            await self.es.update(**kwargs)
            return True
        except ConflictError:
            logger.debug(
                "elasticsearch.update.conflict",
                index=self.index_name,
                doc_id=doc_id,
            )
            return False
    
    async def _delete_document(
        self,
        doc_id: str,
        seq_no: Optional[int] = None,
        primary_term: Optional[int] = None,
        refresh: bool = False,
    ) -> bool:
        """Delete a document.
        
        Args:
            doc_id: Document ID
            seq_no: Sequence number for OCC (optional)
            primary_term: Primary term for OCC (optional)
            refresh: Whether to refresh index immediately
            
        Returns:
            True if deleted, False if not found or conflict
        """
        try:
            from elasticsearch import ConflictError, NotFoundError
        except ImportError:
            raise ImportError("elasticsearch package required")
            
        try:
            kwargs = {
                "index": self.index_name,
                "id": doc_id,
                "refresh": refresh,
            }
            
            if seq_no is not None and primary_term is not None:
                kwargs["if_seq_no"] = seq_no
                kwargs["if_primary_term"] = primary_term
            
            await self.es.delete(**kwargs)
            return True
        except (NotFoundError, ConflictError):
            return False
    
    async def _search(
        self,
        query: Optional[Dict[str, Any]] = None,
        sort: Optional[List[Dict[str, Any]]] = None,
        size: int = 100,
        search_after: Optional[List[Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a search query.
        
        Args:
            query: ES query DSL
            sort: Sort specification
            size: Maximum results to return
            search_after: Pagination cursor
            
        Returns:
            Search response with hits
        """
        body = {"size": size}
        
        if query:
            body["query"] = query
        else:
            body["query"] = {"match_all": {}}
        
        if sort:
            body["sort"] = sort
        
        if search_after:
            body["search_after"] = search_after
        
        result = await self.es.search(index=self.index_name, body=body)
        return result
    
    async def _count(self, query: Optional[Dict[str, Any]] = None) -> int:
        """Count documents matching query.
        
        Args:
            query: ES query DSL (optional)
            
        Returns:
            Document count
        """
        body = {}
        if query:
            body["query"] = query
        
        result = await self.es.count(index=self.index_name, body=body if body else None)
        return result["count"]
    
    async def _exists(self, doc_id: str) -> bool:
        """Check if document exists.
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if exists
        """
        return await self.es.exists(index=self.index_name, id=doc_id)
    
    async def _refresh(self) -> None:
        """Force refresh the index."""
        await self.es.indices.refresh(index=self.index_name)
    
    @staticmethod
    def _datetime_to_iso(dt: Optional[datetime]) -> Optional[str]:
        """Convert datetime to ISO format string."""
        if dt is None:
            return None
        return dt.isoformat().replace("+00:00", "Z")
    
    @staticmethod
    def _iso_to_datetime(iso_str: Optional[str]) -> Optional[datetime]:
        """Convert ISO format string to datetime."""
        if iso_str is None:
            return None
        # Handle various ISO formats
        iso_str = iso_str.replace("Z", "+00:00")
        return datetime.fromisoformat(iso_str)
