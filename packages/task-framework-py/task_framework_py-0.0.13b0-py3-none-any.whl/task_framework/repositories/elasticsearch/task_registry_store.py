"""Elasticsearch implementation of TaskRegistryStore interface."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from task_framework.interfaces.task_registry_store import TaskRegistryStore
from task_framework.logging import logger
from task_framework.models.task_definition import TaskDefinition
from task_framework.repositories.elasticsearch.base import ElasticsearchRepository
from task_framework.repositories.elasticsearch.mappings import TASK_DEFINITION_MAPPINGS


class ElasticsearchTaskRegistryStore(TaskRegistryStore):
    """Elasticsearch implementation of TaskRegistryStore."""
    
    def __init__(
        self,
        client: "AsyncElasticsearch",
        index_prefix: Optional[str] = None,
    ):
        """Initialize store.
        
        Args:
            client: AsyncElasticsearch client
            index_prefix: Index prefix (default from env)
        """
        self._repo = _TaskDefRepo(client, index_prefix)
    
    async def load(self) -> List[TaskDefinition]:
        """Load all task definitions from storage."""
        return await self.list_all()
    
    async def save_all(self, tasks: List[TaskDefinition]) -> None:
        """Save all task definitions (full replacement)."""
        # Note: For ES, we don't do a full replacement, just update each task
        # This is safer for concurrent operations
        for task in tasks:
            await self.register(task)
    
    async def register(self, task_def: TaskDefinition) -> None:
        """Register a single task definition."""
        await self._repo.ensure_index(TASK_DEFINITION_MAPPINGS)
        
        # Check if already exists
        existing = await self.get(task_def.task_id, task_def.version)
        if existing:
            raise ValueError(
                f"Task {task_def.task_id}:{task_def.version} is already registered"
            )
        
        await self._repo.create(task_def)
        
        # Update is_latest flags for this task_id
        await self._update_latest_flag(task_def.task_id)
        
        logger.info(
            "elasticsearch.task_registry.registered",
            task_id=task_def.task_id,
            version=task_def.version,
        )
    
    async def unregister(
        self, task_id: str, version: Optional[str] = None
    ) -> List[TaskDefinition]:
        """Unregister task definition(s)."""
        await self._repo.ensure_index(TASK_DEFINITION_MAPPINGS)
        
        unregistered = []
        
        if version:
            # Unregister specific version
            task = await self.get(task_id, version)
            if task:
                await self._repo.delete(f"{task_id}:{version}")
                unregistered.append(task)
        else:
            # Unregister all versions
            tasks = await self._repo.query({"task_id": task_id})
            for task in tasks:
                await self._repo.delete(f"{task.task_id}:{task.version}")
                unregistered.append(task)
        
        # Update is_latest flags
        if unregistered:
            await self._update_latest_flag(task_id)
        
        return unregistered
    
    async def get(
        self, task_id: str, version: Optional[str] = None
    ) -> Optional[TaskDefinition]:
        """Get a task definition."""
        await self._repo.ensure_index(TASK_DEFINITION_MAPPINGS)
        
        if version:
            return await self._repo.get(f"{task_id}:{version}")
        else:
            # Get latest version
            tasks = await self._repo.query({"task_id": task_id, "is_latest": True})
            return tasks[0] if tasks else None
    
    async def get_by_full_id(self, full_id: str) -> Optional[TaskDefinition]:
        """Get a task definition by full ID."""
        await self._repo.ensure_index(TASK_DEFINITION_MAPPINGS)
        return await self._repo.get(full_id)
    
    async def list_all(self) -> List[TaskDefinition]:
        """List all registered task definitions."""
        await self._repo.ensure_index(TASK_DEFINITION_MAPPINGS)
        return await self._repo.query({})
    
    async def list_task_ids(self) -> List[str]:
        """List all unique task IDs."""
        tasks = await self.list_all()
        return list(set(t.task_id for t in tasks))
    
    async def list_versions(self, task_id: str) -> List[str]:
        """List all versions for a task."""
        await self._repo.ensure_index(TASK_DEFINITION_MAPPINGS)
        tasks = await self._repo.query({"task_id": task_id})
        
        # Sort by version (semantic versioning)
        from packaging import version as pkg_version
        versions = [t.version for t in tasks]
        try:
            versions.sort(key=lambda v: pkg_version.parse(v), reverse=True)
        except Exception:
            versions.sort(reverse=True)
        
        return versions
    
    async def is_registered(
        self, task_id: str, version: Optional[str] = None
    ) -> bool:
        """Check if a task is registered."""
        task = await self.get(task_id, version)
        return task is not None
    
    async def count(self) -> int:
        """Get total number of registered task definitions."""
        await self._repo.ensure_index(TASK_DEFINITION_MAPPINGS)
        return await self._repo._count()
    
    async def clear(self) -> None:
        """Clear all registered tasks."""
        await self._repo.ensure_index(TASK_DEFINITION_MAPPINGS)
        # Delete all documents
        await self._repo.es.delete_by_query(
            index=self._repo.index_name,
            body={"query": {"match_all": {}}},
            refresh=True,
        )
        logger.info("elasticsearch.task_registry.cleared")
    
    async def _update_latest_flag(self, task_id: str) -> None:
        """Update is_latest flag for all versions of a task."""
        versions = await self.list_versions(task_id)
        
        if not versions:
            return
        
        latest_version = versions[0]  # Already sorted newest first
        
        # Update all versions for this task_id
        tasks = await self._repo.query({"task_id": task_id})
        for task in tasks:
            is_latest = task.version == latest_version
            if task.is_latest != is_latest:
                task.is_latest = is_latest
                await self._repo.update(task)


class _TaskDefRepo(ElasticsearchRepository[TaskDefinition]):
    """Internal task definition repository."""
    
    INDEX_SUFFIX = "tasks"
    
    def _to_doc(self, task: TaskDefinition) -> Dict[str, Any]:
        """Convert TaskDefinition to ES document."""
        doc = {
            "task_id": task.task_id,
            "version": task.version,
            "full_id": f"{task.task_id}:{task.version}",
            "name": task.name,
            "description": task.description or "",
            "registered_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "is_latest": getattr(task, "is_latest", False),
        }
        
        # Optional fields
        if task.input_schema:
            doc["input_schema"] = task.input_schema
        if task.output_schema:
            doc["output_schema"] = task.output_schema
        if task.config_schema:
            doc["config_schema"] = task.config_schema
        if task.credentials:
            doc["credentials"] = task.credentials
        if task.code_path:
            doc["code_path"] = str(task.code_path)
        if task.venv_path:
            doc["venv_path"] = str(task.venv_path)
        if task.sdk_version:
            doc["sdk_version"] = task.sdk_version
        
        return doc
    
    def _from_doc(self, doc: Dict[str, Any]) -> TaskDefinition:
        """Convert ES document to TaskDefinition."""
        return TaskDefinition(
            task_id=doc["task_id"],
            version=doc["version"],
            name=doc.get("name", doc["task_id"]),
            description=doc.get("description"),
            input_schema=doc.get("input_schema"),
            output_schema=doc.get("output_schema"),
            config_schema=doc.get("config_schema"),
            credentials=doc.get("credentials"),
            code_path=doc.get("code_path"),
            venv_path=doc.get("venv_path"),
            sdk_version=doc.get("sdk_version"),
            is_latest=doc.get("is_latest", False),
        )
    
    async def create(self, task: TaskDefinition) -> None:
        """Create task document."""
        doc_id = f"{task.task_id}:{task.version}"
        await self._index_document(doc_id, self._to_doc(task), refresh=True)
    
    async def get(self, doc_id: str) -> Optional[TaskDefinition]:
        """Get task by full_id."""
        doc = await self._get_document(doc_id)
        return self._from_doc(doc) if doc else None
    
    async def update(self, task: TaskDefinition) -> None:
        """Update task."""
        doc_id = f"{task.task_id}:{task.version}"
        await self._index_document(doc_id, self._to_doc(task), refresh=True)
    
    async def delete(self, doc_id: str) -> None:
        """Delete task."""
        await self._delete_document(doc_id, refresh=True)
    
    async def query(self, filters: Dict[str, Any]) -> List[TaskDefinition]:
        """Query tasks."""
        must_clauses = []
        
        if filters.get("task_id"):
            must_clauses.append({"term": {"task_id": filters["task_id"]}})
        
        if filters.get("is_latest") is not None:
            must_clauses.append({"term": {"is_latest": filters["is_latest"]}})
        
        query = {"bool": {"must": must_clauses}} if must_clauses else {"match_all": {}}
        sort = [{"registered_at": {"order": "desc"}}]
        
        result = await self._search(query=query, sort=sort, size=1000)
        
        return [
            self._from_doc(hit["_source"])
            for hit in result.get("hits", {}).get("hits", [])
        ]
