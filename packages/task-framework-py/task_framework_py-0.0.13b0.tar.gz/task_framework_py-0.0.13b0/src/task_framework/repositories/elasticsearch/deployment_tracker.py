"""Elasticsearch implementation of DeploymentTrackerStore interface."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from task_framework.interfaces.deployment_tracker_store import DeploymentTrackerStore
from task_framework.logging import logger
from task_framework.models.task_definition import DeploymentRecord
from task_framework.repositories.elasticsearch.base import ElasticsearchRepository
from task_framework.repositories.elasticsearch.mappings import DEPLOYMENT_MAPPINGS


class ElasticsearchDeploymentTracker(DeploymentTrackerStore):
    """Elasticsearch implementation of DeploymentTrackerStore."""
    
    def __init__(
        self,
        client: "AsyncElasticsearch",
        index_prefix: Optional[str] = None,
    ):
        """Initialize tracker.
        
        Args:
            client: AsyncElasticsearch client
            index_prefix: Index prefix (default from env)
        """
        self._repo = _DeploymentRepo(client, index_prefix)
    
    async def record_deployment(
        self,
        zip_path: str,
        task_id: str,
        version: str,
        status: str,
        error: Optional[str] = None,
    ) -> None:
        """Record a deployment attempt."""
        await self._repo.ensure_index(DEPLOYMENT_MAPPINGS)
        
        record = DeploymentRecord(
            zip_path=zip_path,
            task_id=task_id,
            version=version,
            status=status,
            error=error,
            deployed_at=datetime.now(timezone.utc),
        )
        
        await self._repo.upsert(record)
        
        logger.info(
            "elasticsearch.deployment.recorded",
            zip_path=zip_path,
            task_id=task_id,
            version=version,
            status=status,
        )
    
    async def list_deployed(self) -> List[DeploymentRecord]:
        """List all successfully deployed tasks."""
        await self._repo.ensure_index(DEPLOYMENT_MAPPINGS)
        return await self._repo.query({"status": "deployed"})
    
    async def is_deployed(self, zip_path: str) -> bool:
        """Check if a zip file has been successfully deployed."""
        await self._repo.ensure_index(DEPLOYMENT_MAPPINGS)
        record = await self._repo.get(zip_path)
        return record is not None and record.status == "deployed"
    
    async def get_deployment(self, zip_path: str) -> Optional[DeploymentRecord]:
        """Get deployment record for a zip file."""
        await self._repo.ensure_index(DEPLOYMENT_MAPPINGS)
        return await self._repo.get(zip_path)
    
    async def remove(self, zip_path: str) -> None:
        """Remove a deployment record."""
        await self._repo.ensure_index(DEPLOYMENT_MAPPINGS)
        await self._repo.delete(zip_path)
    
    async def list_all(self) -> List[DeploymentRecord]:
        """List all deployment records."""
        await self._repo.ensure_index(DEPLOYMENT_MAPPINGS)
        return await self._repo.query({})
    
    async def clear(self) -> None:
        """Clear all deployment records."""
        await self._repo.ensure_index(DEPLOYMENT_MAPPINGS)
        await self._repo.es.delete_by_query(
            index=self._repo.index_name,
            body={"query": {"match_all": {}}},
            refresh=True,
        )
        logger.info("elasticsearch.deployment.cleared")

    async def get_by_path(self, zip_path: str) -> Optional[DeploymentRecord]:
        """Get deployment record by zip path.
        
        This is an alias for get_deployment() to maintain interface compatibility.
        """
        return await self.get_deployment(zip_path)


class _DeploymentRepo(ElasticsearchRepository[DeploymentRecord]):
    """Internal deployment repository."""
    
    INDEX_SUFFIX = "deployments"
    
    def _make_doc_id(self, zip_path: str) -> str:
        """Create deterministic doc ID from zip path."""
        import hashlib
        return hashlib.sha256(zip_path.encode()).hexdigest()[:32]
    
    def _to_doc(self, record: DeploymentRecord) -> Dict[str, Any]:
        """Convert DeploymentRecord to ES document."""
        doc = {
            "zip_path": record.zip_path,
            "task_id": record.task_id,
            "version": record.version,
            "status": record.status,
            "deployed_at": self._datetime_to_iso(record.deployed_at),
        }
        
        if record.zip_hash:
            doc["zip_hash"] = record.zip_hash
        if record.error:
            doc["error"] = record.error
        
        return doc
    
    def _from_doc(self, doc: Dict[str, Any]) -> DeploymentRecord:
        """Convert ES document to DeploymentRecord."""
        return DeploymentRecord(
            zip_path=doc["zip_path"],
            zip_hash=doc.get("zip_hash"),
            task_id=doc["task_id"],
            version=doc["version"],
            status=doc["status"],
            deployed_at=self._iso_to_datetime(doc.get("deployed_at")),
            error=doc.get("error"),
        )
    
    async def upsert(self, record: DeploymentRecord) -> None:
        """Create or update deployment record."""
        doc_id = self._make_doc_id(record.zip_path)
        await self._index_document(doc_id, self._to_doc(record), refresh=True)
    
    async def get(self, zip_path: str) -> Optional[DeploymentRecord]:
        """Get deployment record by zip path."""
        doc_id = self._make_doc_id(zip_path)
        doc = await self._get_document(doc_id)
        return self._from_doc(doc) if doc else None
    
    async def delete(self, zip_path: str) -> None:
        """Delete deployment record."""
        doc_id = self._make_doc_id(zip_path)
        await self._delete_document(doc_id, refresh=True)
    
    async def query(self, filters: Dict[str, Any]) -> List[DeploymentRecord]:
        """Query deployment records."""
        must_clauses = []
        
        if filters.get("status"):
            must_clauses.append({"term": {"status": filters["status"]}})
        
        if filters.get("task_id"):
            must_clauses.append({"term": {"task_id": filters["task_id"]}})
        
        query = {"bool": {"must": must_clauses}} if must_clauses else {"match_all": {}}
        sort = [{"deployed_at": {"order": "desc"}}]
        
        result = await self._search(query=query, sort=sort, size=1000)
        
        return [
            self._from_doc(hit["_source"])
            for hit in result.get("hits", {}).get("hits", [])
        ]
