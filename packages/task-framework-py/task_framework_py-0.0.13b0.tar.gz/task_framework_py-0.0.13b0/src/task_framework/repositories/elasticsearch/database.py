"""Elasticsearch implementation of Database interface.

Provides storage for threads, artifacts, schedules, and runs.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from task_framework.interfaces.database import Database
from task_framework.logging import logger
from task_framework.models.artifact import Artifact
from task_framework.models.schedule import Run, Schedule
from task_framework.models.thread import Thread
from task_framework.repositories.elasticsearch.base import ElasticsearchRepository
from task_framework.repositories.elasticsearch.mappings import (
    ARTIFACT_MAPPINGS,
    RUN_MAPPINGS,
    SCHEDULE_MAPPINGS,
    THREAD_MAPPINGS,
)


class ElasticsearchDatabase(Database):
    """Elasticsearch implementation of Database interface.
    
    Stores threads, artifacts, schedules, and runs in Elasticsearch indices.
    Uses optimistic concurrency control for updates.
    """
    
    def __init__(
        self,
        client: "AsyncElasticsearch",
        index_prefix: Optional[str] = None,
    ):
        """Initialize Elasticsearch database.
        
        Args:
            client: AsyncElasticsearch client
            index_prefix: Index name prefix (default from env)
        """
        self._client = client
        self._index_prefix = index_prefix
        
        # Create helper repositories for each entity type
        self._threads = _ThreadRepository(client, index_prefix)
        self._artifacts = _ArtifactRepository(client, index_prefix)
        self._schedules = _ScheduleRepository(client, index_prefix)
        self._runs = _RunRepository(client, index_prefix)
        
        self._initialized = False
    
    async def _ensure_indices(self) -> None:
        """Ensure all indices exist."""
        if self._initialized:
            return
        
        await self._threads.ensure_index(THREAD_MAPPINGS)
        await self._artifacts.ensure_index(ARTIFACT_MAPPINGS)
        await self._schedules.ensure_index(SCHEDULE_MAPPINGS)
        await self._runs.ensure_index(RUN_MAPPINGS)
        
        self._initialized = True
        logger.info("elasticsearch.database.initialized")
    
    # Thread methods
    
    async def create_thread(self, thread: Thread) -> None:
        """Create a new thread."""
        await self._ensure_indices()
        await self._threads.create(thread)
    
    async def get_thread(self, thread_id: str) -> Optional[Thread]:
        """Get a thread by ID."""
        await self._ensure_indices()
        return await self._threads.get(thread_id)
    
    async def update_thread(self, thread: Thread) -> None:
        """Update an existing thread."""
        await self._ensure_indices()
        await self._threads.update(thread)
    
    async def delete_thread(self, thread_id: str) -> None:
        """Delete a thread."""
        await self._ensure_indices()
        await self._threads.delete(thread_id)
    
    async def query_threads(self, filters: Dict[str, Any]) -> List[Thread]:
        """Query threads with filters."""
        await self._ensure_indices()
        return await self._threads.query(filters)
    
    # Artifact methods
    
    async def create_artifact(self, artifact: Artifact) -> None:
        """Create a new artifact."""
        await self._ensure_indices()
        await self._artifacts.create(artifact)
    
    async def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        """Get an artifact by ID."""
        await self._ensure_indices()
        return await self._artifacts.get(artifact_id)
    
    async def get_thread_artifacts(self, thread_id: str) -> List[Artifact]:
        """Get all artifacts for a thread."""
        await self._ensure_indices()
        return await self._artifacts.get_by_thread(thread_id)
    
    async def delete_artifact(self, artifact_id: str) -> None:
        """Delete an artifact."""
        await self._ensure_indices()
        await self._artifacts.delete(artifact_id)
    
    async def query_artifacts(self, filters: Dict[str, Any]) -> List[Artifact]:
        """Query artifacts with filters."""
        await self._ensure_indices()
        return await self._artifacts.query(filters)
    
    # Schedule methods
    
    async def create_schedule(self, schedule: Schedule) -> None:
        """Create a new schedule."""
        await self._ensure_indices()
        await self._schedules.create(schedule)
    
    async def get_schedule(self, schedule_id: str) -> Optional[Schedule]:
        """Get a schedule by ID."""
        await self._ensure_indices()
        return await self._schedules.get(schedule_id)
    
    async def update_schedule(self, schedule: Schedule) -> None:
        """Update an existing schedule."""
        await self._ensure_indices()
        await self._schedules.update(schedule)
    
    async def delete_schedule(self, schedule_id: str) -> None:
        """Delete a schedule."""
        await self._ensure_indices()
        await self._schedules.delete(schedule_id)
    
    async def query_schedules(self, filters: Dict[str, Any]) -> List[Schedule]:
        """Query schedules with filters."""
        await self._ensure_indices()
        return await self._schedules.query(filters)
    
    # Run methods
    
    async def create_run(self, run: Run) -> None:
        """Create a new run."""
        await self._ensure_indices()
        await self._runs.create(run)
    
    async def get_run(self, schedule_id: str, run_id: str) -> Optional[Run]:
        """Get a run by schedule_id and run_id."""
        await self._ensure_indices()
        return await self._runs.get(schedule_id, run_id)
    
    async def update_run(self, run: Run) -> None:
        """Update an existing run."""
        await self._ensure_indices()
        await self._runs.update(run)
    
    async def delete_run(self, schedule_id: str, run_id: str) -> None:
        """Delete a run."""
        await self._ensure_indices()
        await self._runs.delete(schedule_id, run_id)
    
    async def query_runs(
        self, schedule_id: str, filters: Dict[str, Any]
    ) -> List[Run]:
        """Query runs for a schedule."""
        await self._ensure_indices()
        return await self._runs.query(schedule_id, filters)
    
    async def get_running_run_by_schedule(self, schedule_id: str) -> Optional[Run]:
        """Get the currently running run for a schedule."""
        await self._ensure_indices()
        runs = await self._runs.query(schedule_id, {"state": "running", "limit": 1})
        return runs[0] if runs else None
    
    async def claim_run(self, schedule_id: str, run_id: str) -> bool:
        """Atomically claim a run for execution (pending → running).
        
        Only one worker will succeed; others will fail and return False.
        
        Args:
            schedule_id: Schedule ID
            run_id: Run ID
            
        Returns:
            True if claim succeeded (this worker should execute),
            False if run was already claimed by another worker
        """
        await self._ensure_indices()
        return await self._runs.claim_run(schedule_id, run_id)


class _ThreadRepository(ElasticsearchRepository[Thread]):
    """Internal repository for Thread entities."""
    
    INDEX_SUFFIX = "threads"
    
    def _to_doc(self, thread: Thread) -> Dict[str, Any]:
        """Convert Thread to ES document."""
        doc = thread.model_dump(mode="json", exclude_none=True)
        # Ensure datetime fields are ISO format
        for field in ["created_at", "started_at", "finished_at"]:
            if field in doc and doc[field]:
                if isinstance(doc[field], datetime):
                    doc[field] = self._datetime_to_iso(doc[field])
        return doc
    
    def _from_doc(self, doc: Dict[str, Any]) -> Thread:
        """Convert ES document to Thread."""
        return Thread.model_validate(doc)
    
    async def create(self, thread: Thread) -> None:
        """Create a thread document."""
        await self._index_document(thread.id, self._to_doc(thread), refresh=True)
        logger.debug("elasticsearch.thread.created", thread_id=thread.id)
    
    async def get(self, thread_id: str) -> Optional[Thread]:
        """Get a thread by ID."""
        doc = await self._get_document(thread_id)
        return self._from_doc(doc) if doc else None
    
    async def update(self, thread: Thread) -> None:
        """Update a thread."""
        await self._index_document(thread.id, self._to_doc(thread), refresh=True)
        logger.debug("elasticsearch.thread.updated", thread_id=thread.id)
    
    async def delete(self, thread_id: str) -> None:
        """Delete a thread."""
        await self._delete_document(thread_id, refresh=True)
        logger.debug("elasticsearch.thread.deleted", thread_id=thread_id)
    
    async def query(self, filters: Dict[str, Any]) -> List[Thread]:
        """Query threads with filters."""
        must_clauses = []
        
        # State filter
        if filters.get("state"):
            must_clauses.append({"term": {"state": filters["state"]}})
        
        # User ID filter (in metadata)
        if filters.get("user_id"):
            must_clauses.append({"term": {"metadata.user_id": filters["user_id"]}})
        
        # App ID filter (in metadata)
        if filters.get("app_id"):
            must_clauses.append({"term": {"metadata.app_id": filters["app_id"]}})
        
        # Task ID filter
        if filters.get("task_id"):
            must_clauses.append({"term": {"metadata.task_id": filters["task_id"]}})
        
        # Task version filter
        if filters.get("task_version"):
            must_clauses.append({"term": {"metadata.task_version": filters["task_version"]}})
        
        # Schedule ID filter
        if filters.get("schedule_id"):
            must_clauses.append({"term": {"schedule_id": filters["schedule_id"]}})
        
        # Name filter (supports wildcards)
        if filters.get("name"):
            name = filters["name"]
            if name.endswith("*"):
                must_clauses.append({"prefix": {"name": name[:-1]}})
            else:
                must_clauses.append({"term": {"name": name}})
        
        # Build query
        query = {"bool": {"must": must_clauses}} if must_clauses else {"match_all": {}}
        
        # Sort by created_at descending
        sort = [{"created_at": {"order": "desc"}}, {"id": {"order": "asc"}}]
        
        # Pagination
        size = filters.get("limit", 100)
        
        result = await self._search(query=query, sort=sort, size=size)
        
        threads = []
        for hit in result.get("hits", {}).get("hits", []):
            threads.append(self._from_doc(hit["_source"]))
        
        return threads


class _ArtifactRepository(ElasticsearchRepository[Artifact]):
    """Internal repository for Artifact entities."""
    
    INDEX_SUFFIX = "artifacts"
    
    def _to_doc(self, artifact: Artifact) -> Dict[str, Any]:
        """Convert Artifact to ES document."""
        doc = artifact.model_dump(mode="json", exclude_none=True)
        for field in ["created_at", "archived_at"]:
            if field in doc and doc[field]:
                if isinstance(doc[field], datetime):
                    doc[field] = self._datetime_to_iso(doc[field])
        return doc
    
    def _from_doc(self, doc: Dict[str, Any]) -> Artifact:
        """Convert ES document to Artifact."""
        return Artifact.model_validate(doc)
    
    async def create(self, artifact: Artifact) -> None:
        """Create an artifact document."""
        await self._index_document(artifact.id, self._to_doc(artifact), refresh=True)
        logger.debug("elasticsearch.artifact.created", artifact_id=artifact.id)
    
    async def get(self, artifact_id: str) -> Optional[Artifact]:
        """Get an artifact by ID."""
        doc = await self._get_document(artifact_id)
        return self._from_doc(doc) if doc else None
    
    async def get_by_thread(self, thread_id: str) -> List[Artifact]:
        """Get all artifacts for a thread."""
        query = {"term": {"thread_id": thread_id}}
        sort = [{"created_at": {"order": "desc"}}]
        
        result = await self._search(query=query, sort=sort, size=1000)
        
        return [
            self._from_doc(hit["_source"])
            for hit in result.get("hits", {}).get("hits", [])
        ]
    
    async def delete(self, artifact_id: str) -> None:
        """Delete an artifact."""
        await self._delete_document(artifact_id, refresh=True)
        logger.debug("elasticsearch.artifact.deleted", artifact_id=artifact_id)
    
    async def query(self, filters: Dict[str, Any]) -> List[Artifact]:
        """Query artifacts with filters."""
        must_clauses = []
        must_not_clauses = []
        
        # Thread ID filter
        if filters.get("thread_id"):
            must_clauses.append({"term": {"thread_id": filters["thread_id"]}})
        
        # Kind filter
        if filters.get("kind"):
            must_clauses.append({"term": {"kind": filters["kind"]}})
        
        # Media type filter
        if filters.get("media_type"):
            must_clauses.append({"term": {"media_type": filters["media_type"]}})
        
        # Ref filter (supports wildcards)
        if filters.get("ref"):
            ref = filters["ref"]
            if ref.endswith("*"):
                must_clauses.append({"prefix": {"ref": ref[:-1]}})
            else:
                must_clauses.append({"term": {"ref": ref}})
        
        # Include archived filter (default: exclude archived)
        if not filters.get("include_archived", False):
            must_not_clauses.append({"term": {"archived": True}})
        
        # Build query
        bool_query = {}
        if must_clauses:
            bool_query["must"] = must_clauses
        if must_not_clauses:
            bool_query["must_not"] = must_not_clauses
        
        query = {"bool": bool_query} if bool_query else {"match_all": {}}
        
        sort = [{"created_at": {"order": "desc"}}]
        size = filters.get("limit", 100)
        
        result = await self._search(query=query, sort=sort, size=size)
        
        return [
            self._from_doc(hit["_source"])
            for hit in result.get("hits", {}).get("hits", [])
        ]


class _ScheduleRepository(ElasticsearchRepository[Schedule]):
    """Internal repository for Schedule entities."""
    
    INDEX_SUFFIX = "schedules"
    
    def _to_doc(self, schedule: Schedule) -> Dict[str, Any]:
        """Convert Schedule to ES document."""
        doc = schedule.model_dump(mode="json", exclude_none=True)
        for field in ["created_at", "updated_at", "last_run_at", "next_run_at"]:
            if field in doc and doc[field]:
                if isinstance(doc[field], datetime):
                    doc[field] = self._datetime_to_iso(doc[field])
        return doc
    
    def _from_doc(self, doc: Dict[str, Any]) -> Schedule:
        """Convert ES document to Schedule."""
        return Schedule.model_validate(doc)
    
    async def create(self, schedule: Schedule) -> None:
        """Create a schedule document."""
        await self._index_document(schedule.id, self._to_doc(schedule), refresh=True)
        logger.debug("elasticsearch.schedule.created", schedule_id=schedule.id)
    
    async def get(self, schedule_id: str) -> Optional[Schedule]:
        """Get a schedule by ID."""
        doc = await self._get_document(schedule_id)
        return self._from_doc(doc) if doc else None
    
    async def update(self, schedule: Schedule) -> None:
        """Update a schedule."""
        await self._index_document(schedule.id, self._to_doc(schedule), refresh=True)
        logger.debug("elasticsearch.schedule.updated", schedule_id=schedule.id)
    
    async def delete(self, schedule_id: str) -> None:
        """Delete a schedule."""
        await self._delete_document(schedule_id, refresh=True)
        logger.debug("elasticsearch.schedule.deleted", schedule_id=schedule_id)
    
    async def query(self, filters: Dict[str, Any]) -> List[Schedule]:
        """Query schedules with filters."""
        must_clauses = []
        
        if filters.get("state"):
            must_clauses.append({"term": {"state": filters["state"]}})
        
        if filters.get("task_id"):
            must_clauses.append({"term": {"task_id": filters["task_id"]}})
        
        if filters.get("task_version"):
            must_clauses.append({"term": {"task_version": filters["task_version"]}})
        
        query = {"bool": {"must": must_clauses}} if must_clauses else {"match_all": {}}
        sort = [{"created_at": {"order": "desc"}}]
        size = filters.get("limit", 100)
        
        result = await self._search(query=query, sort=sort, size=size)
        
        return [
            self._from_doc(hit["_source"])
            for hit in result.get("hits", {}).get("hits", [])
        ]


class _RunRepository(ElasticsearchRepository[Run]):
    """Internal repository for Run entities."""
    
    INDEX_SUFFIX = "runs"
    
    def _to_doc(self, run: Run) -> Dict[str, Any]:
        """Convert Run to ES document."""
        doc = run.model_dump(mode="json", exclude_none=True)
        for field in ["scheduled_for_utc", "started_at", "finished_at"]:
            if field in doc and doc[field]:
                if isinstance(doc[field], datetime):
                    doc[field] = self._datetime_to_iso(doc[field])
        return doc
    
    def _from_doc(self, doc: Dict[str, Any]) -> Run:
        """Convert ES document to Run."""
        return Run.model_validate(doc)
    
    def _get_doc_id(self, schedule_id: str, run_id: str) -> str:
        """Generate composite document ID."""
        return f"{schedule_id}:{run_id}"
    
    async def create(self, run: Run) -> None:
        """Create a run document."""
        doc_id = self._get_doc_id(run.schedule_id, run.run_id)
        await self._index_document(doc_id, self._to_doc(run), refresh=True)
        logger.debug("elasticsearch.run.created", schedule_id=run.schedule_id, run_id=run.run_id)
    
    async def get(self, schedule_id: str, run_id: str) -> Optional[Run]:
        """Get a run by schedule_id and run_id."""
        doc_id = self._get_doc_id(schedule_id, run_id)
        doc = await self._get_document(doc_id)
        return self._from_doc(doc) if doc else None
    
    async def update(self, run: Run) -> None:
        """Update a run."""
        doc_id = self._get_doc_id(run.schedule_id, run.run_id)
        await self._index_document(doc_id, self._to_doc(run), refresh=True)
        logger.debug("elasticsearch.run.updated", schedule_id=run.schedule_id, run_id=run.run_id)
    
    async def delete(self, schedule_id: str, run_id: str) -> None:
        """Delete a run."""
        doc_id = self._get_doc_id(schedule_id, run_id)
        await self._delete_document(doc_id, refresh=True)
        logger.debug("elasticsearch.run.deleted", schedule_id=schedule_id, run_id=run_id)
    
    async def query(self, schedule_id: str, filters: Dict[str, Any]) -> List[Run]:
        """Query runs for a schedule."""
        must_clauses = [{"term": {"schedule_id": schedule_id}}]
        
        if filters.get("state"):
            must_clauses.append({"term": {"state": filters["state"]}})
        
        if filters.get("scheduled_after"):
            must_clauses.append({
                "range": {
                    "scheduled_for_utc": {"gte": self._datetime_to_iso(filters["scheduled_after"])}
                }
            })
        
        if filters.get("scheduled_before"):
            must_clauses.append({
                "range": {
                    "scheduled_for_utc": {"lte": self._datetime_to_iso(filters["scheduled_before"])}
                }
            })
        
        query = {"bool": {"must": must_clauses}}
        sort = [{"scheduled_for_utc": {"order": "desc"}}]
        size = filters.get("limit", 100)
        
        result = await self._search(query=query, sort=sort, size=size)
        
        return [
            self._from_doc(hit["_source"])
            for hit in result.get("hits", {}).get("hits", [])
        ]
    
    async def claim_run(self, schedule_id: str, run_id: str) -> bool:
        """Atomically claim a run for execution (pending → running).
        
        Uses ES scripted update to only transition if state is still 'pending'.
        Only one worker will succeed; others will fail and return False.
        
        Args:
            schedule_id: Schedule ID
            run_id: Run ID
            
        Returns:
            True if claim succeeded (this worker should execute),
            False if run was already claimed by another worker
        """
        doc_id = self._get_doc_id(schedule_id, run_id)
        now = datetime.now(timezone.utc)
        
        # Use painless script to atomically update only if state is pending
        script = {
            "source": """
                if (ctx._source.state == 'pending') {
                    ctx._source.state = 'running';
                    ctx._source.started_at = params.started_at;
                } else {
                    ctx.op = 'noop';
                }
            """,
            "lang": "painless",
            "params": {
                "started_at": self._datetime_to_iso(now),
            }
        }
        
        try:
            result = await self.es.update(
                index=self.index_name,
                id=doc_id,
                script=script,
                refresh=True,
            )
            
            # 'noop' means the script didn't update (state wasn't pending)
            if result.get("result") == "noop":
                logger.debug(
                    "elasticsearch.run.claim_failed",
                    schedule_id=schedule_id,
                    run_id=run_id,
                    reason="already_claimed",
                )
                return False
            
            logger.info(
                "elasticsearch.run.claimed",
                schedule_id=schedule_id,
                run_id=run_id,
            )
            return True
            
        except Exception as e:
            logger.error(
                "elasticsearch.run.claim_error",
                schedule_id=schedule_id,
                run_id=run_id,
                error=str(e),
            )
            return False
