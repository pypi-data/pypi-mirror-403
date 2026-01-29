"""File-based Database implementation using JSON files."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
from aiofiles import os as aios

from task_framework.interfaces.database import Database
from task_framework.models.artifact import Artifact
from task_framework.models.schedule import Run, Schedule
from task_framework.models.thread import Thread


class FileDatabase(Database):
    """File-based Database implementation storing threads and artifacts as JSON files."""

    def __init__(self, base_path: str = "data") -> None:
        """Initialize FileDatabase with base path.
        
        Args:
            base_path: Base directory for storing data files
        """
        self.base_path = Path(base_path)
        self.threads_dir = self.base_path / "threads"
        self.artifacts_dir = self.base_path / "artifacts"
        self.schedules_dir = self.base_path / "schedules"
        self.runs_dir = self.base_path / "runs"
        self.indexes_dir = self.base_path / "indexes" / "threads"
        self.app_id_index_dir = self.indexes_dir / "app_id"
        self.user_id_index_dir = self.indexes_dir / "user_id"

    async def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        await aios.makedirs(self.threads_dir, exist_ok=True)
        await aios.makedirs(self.artifacts_dir, exist_ok=True)
        await aios.makedirs(self.schedules_dir, exist_ok=True)
        await aios.makedirs(self.runs_dir, exist_ok=True)
        await aios.makedirs(self.app_id_index_dir, exist_ok=True)
        await aios.makedirs(self.user_id_index_dir, exist_ok=True)

    async def create_thread(self, thread: Thread) -> None:
        """Create a new thread, storing as JSON file.
        
        Args:
            thread: Thread instance to store
        """
        await self._ensure_directories()
        file_path = self.threads_dir / f"{thread.id}.json"
        
        async with aiofiles.open(file_path, "w") as f:
            await f.write(thread.model_dump_json(exclude_none=False))
        
        # Update indexes for app_id and user_id
        await self._update_thread_indexes(thread, is_delete=False)

    async def get_thread(self, thread_id: str) -> Optional[Thread]:
        """Get a thread by ID.
        
        Args:
            thread_id: Thread identifier
            
        Returns:
            Thread instance if found, None otherwise
        """
        file_path = self.threads_dir / f"{thread_id}.json"
        
        if not await aios.path.exists(file_path):
            return None
        
        async with aiofiles.open(file_path, "r") as f:
            content = await f.read()
            data = json.loads(content)
            return Thread.model_validate(data)

    async def update_thread(self, thread: Thread) -> None:
        """Update an existing thread.
        
        Args:
            thread: Thread instance with updated data
        """
        # Get old thread to check if app_id/user_id changed
        old_thread = await self.get_thread(thread.id)
        
        await self._ensure_directories()
        file_path = self.threads_dir / f"{thread.id}.json"
        
        async with aiofiles.open(file_path, "w") as f:
            await f.write(thread.model_dump_json(exclude_none=False))
        
        # Update indexes - remove from old indexes if app_id/user_id changed
        if old_thread:
            old_app_id = old_thread.metadata.get("app_id") if old_thread.metadata else None
            old_user_id = old_thread.metadata.get("user_id") if old_thread.metadata else None
            new_app_id = thread.metadata.get("app_id") if thread.metadata else None
            new_user_id = thread.metadata.get("user_id") if thread.metadata else None
            
            # Remove from old indexes if changed
            if old_app_id != new_app_id and old_app_id:
                await self._remove_from_index(self.app_id_index_dir, old_app_id, thread.id)
            if old_user_id != new_user_id and old_user_id:
                await self._remove_from_index(self.user_id_index_dir, old_user_id, thread.id)
        
        # Add to new indexes
        await self._update_thread_indexes(thread, is_delete=False)

    async def delete_thread(self, thread_id: str) -> None:
        """Delete a thread.
        
        Args:
            thread_id: Thread identifier to delete
        """
        # Get thread before deletion to update indexes
        thread = await self.get_thread(thread_id)
        
        file_path = self.threads_dir / f"{thread_id}.json"
        
        if await aios.path.exists(file_path):
            await aios.remove(file_path)
        
        # Remove from indexes
        if thread:
            await self._update_thread_indexes(thread, is_delete=True)

    async def query_threads(self, filters: Dict[str, Any]) -> List[Thread]:
        """Query threads with filters.
        
        Optimized implementation:
        - Uses indexes for app_id and user_id when provided (priority optimization)
        - Sorts files by modification time (newest first) to prioritize recent threads
        - Uses date filters to limit file scanning when possible
        - Stops early when limit is reached (if provided)
        - Performs partial JSON parsing for faster filtering
        
        Args:
            filters: Dictionary of filter criteria (state, user_id, app_id, etc.)
                    May include 'limit' for early stopping optimization
            
        Returns:
            List of Thread instances matching filters, sorted by created_at descending
        """
        if not await aios.path.exists(self.threads_dir):
            return []
        
        threads: List[Thread] = []
        limit = filters.get("limit")  # For early stopping optimization
        
        # PRIORITY OPTIMIZATION: Use indexes for app_id and user_id if provided
        app_id = filters.get("app_id")
        user_id = filters.get("user_id")
        candidate_thread_ids: Optional[set] = None
        use_index = False
        
        if app_id or user_id:
            # Get thread IDs from indexes
            app_thread_ids = set()
            user_thread_ids = set()
            app_index_exists = False
            user_index_exists = False
            
            if app_id:
                app_thread_ids, app_index_exists = await self._get_indexed_thread_ids_with_status(
                    self.app_id_index_dir, app_id
                )
            
            if user_id:
                user_thread_ids, user_index_exists = await self._get_indexed_thread_ids_with_status(
                    self.user_id_index_dir, user_id
                )
            
            # Combine filters: if both provided, use intersection; otherwise use the one provided
            if app_id and user_id:
                candidate_thread_ids = app_thread_ids & user_thread_ids
                use_index = app_index_exists and user_index_exists
            elif app_id:
                candidate_thread_ids = app_thread_ids
                use_index = app_index_exists
            elif user_id:
                candidate_thread_ids = user_thread_ids
                use_index = user_index_exists
            
            # If index exists but is empty, it means no threads match (can return early)
            # If index doesn't exist, we need to do a full scan and build the index
            if use_index and not candidate_thread_ids:
                return []
        
        # Get thread files - either all files or only indexed ones
        file_paths_with_mtime = []
        # Track if we need to rebuild indexes (index doesn't exist for requested app_id/user_id)
        need_index_rebuild = (app_id or user_id) and not use_index
        
        try:
            if candidate_thread_ids and use_index:
                # Only process files for indexed thread IDs (index exists and has data)
                for thread_id in candidate_thread_ids:
                    file_path = self.threads_dir / f"{thread_id}.json"
                    if await aios.path.exists(file_path) and file_path.suffix == ".json":
                        try:
                            stat = await aios.stat(file_path)
                            file_paths_with_mtime.append((file_path, stat.st_mtime))
                        except OSError:
                            continue
            else:
                # Scan all files (no app_id/user_id filter OR index doesn't exist - need to rebuild)
                entries = await aios.listdir(self.threads_dir)
                for entry in entries:
                    file_path = self.threads_dir / entry
                    if file_path.suffix == ".json":
                        try:
                            stat = await aios.stat(file_path)
                            file_paths_with_mtime.append((file_path, stat.st_mtime))
                        except OSError:
                            continue
        except FileNotFoundError:
            return []
        
        # Sort by modification time descending (newest first)
        # This allows us to process recent threads first and stop early
        file_paths_with_mtime.sort(key=lambda x: x[1], reverse=True)
        
        # If we have created_after filter, we can skip files older than that
        # (approximation using mtime - not perfect but helps)
        created_after = filters.get("created_after")
        if created_after:
            # Convert datetime to timestamp for comparison
            if hasattr(created_after, 'timestamp'):
                min_mtime = created_after.timestamp()
            else:
                from datetime import datetime
                if isinstance(created_after, datetime):
                    min_mtime = created_after.timestamp()
                else:
                    min_mtime = None
            
            if min_mtime:
                # Filter out files that are definitely too old
                file_paths_with_mtime = [
                    (fp, mtime) for fp, mtime in file_paths_with_mtime
                    if mtime >= min_mtime
                ]
        
        # Scan files in order (newest first)
        for file_path, _ in file_paths_with_mtime:
            # Early stopping: if we have a limit and enough results, stop
            if limit and len(threads) >= limit * 2:  # Get 2x limit to account for filtering
                break
            
            try:
                async with aiofiles.open(file_path, "r") as f:
                    content = await f.read()
                    
                    # Try partial parsing for faster filtering
                    # Parse JSON but don't validate full Thread object yet
                    data = json.loads(content)
                    
                    # Quick pre-filtering on raw JSON data before full validation
                    if self._quick_filter_json(data, filters):
                        # Only validate full Thread object if it passes quick filter
                        thread = Thread.model_validate(data)
                        
                        # Apply full filters
                        if self._matches_filters(thread, filters):
                            threads.append(thread)
                            
                            # If we're rebuilding indexes, update them as we go
                            if need_index_rebuild:
                                await self._update_thread_indexes(thread, is_delete=False)
            except (json.JSONDecodeError, ValueError, KeyError):
                # Skip invalid files
                continue
        
        # Sort by created_at descending (newest first)
        threads.sort(key=lambda t: t.created_at, reverse=True)
        
        return threads
    
    def _quick_filter_json(self, data: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Quick filter on raw JSON data before full Thread validation.
        
        This allows us to skip expensive Thread.model_validate() for threads
        that definitely don't match filters.
        
        Args:
            data: Raw JSON data from file
            filters: Filter criteria
            
        Returns:
            True if thread might match filters (needs full validation), False otherwise
        """
        # Quick filter by state (if present in JSON)
        if "state" in filters and filters["state"] is not None:
            if data.get("state") != filters["state"]:
                return False
        
        # Quick filter by name (supports prefix matching with * suffix)
        if "name" in filters and filters["name"] is not None:
            name_filter = filters["name"]
            thread_name = data.get("name")
            if name_filter.endswith("*"):
                # Prefix match
                if not thread_name or not thread_name.startswith(name_filter[:-1]):
                    return False
            else:
                # Exact match
                if thread_name != name_filter:
                    return False
        
        # Quick filter by user_id (if present in metadata)
        if "user_id" in filters and filters["user_id"] is not None:
            metadata = data.get("metadata", {})
            if isinstance(metadata, dict) and metadata.get("user_id") != filters["user_id"]:
                return False
        
        # Quick filter by app_id (if present in metadata)
        if "app_id" in filters and filters["app_id"] is not None:
            metadata = data.get("metadata", {})
            if isinstance(metadata, dict) and metadata.get("app_id") != filters["app_id"]:
                return False
        
        # Quick filter by schedule_id
        if "schedule_id" in filters and filters["schedule_id"] is not None:
            if data.get("schedule_id") != filters["schedule_id"]:
                return False
        
        # Quick filter by run_id
        if "run_id" in filters and filters["run_id"] is not None:
            if data.get("run_id") != filters["run_id"]:
                return False
        
        # Quick filter by task_id (if present in metadata)
        if "task_id" in filters and filters["task_id"] is not None:
            metadata = data.get("metadata", {})
            if isinstance(metadata, dict) and metadata.get("task_id") != filters["task_id"]:
                return False
        
        # Quick filter by task_version (if present in metadata)
        if "task_version" in filters and filters["task_version"] is not None:
            metadata = data.get("metadata", {})
            if isinstance(metadata, dict) and metadata.get("task_version") != filters["task_version"]:
                return False
        
        # Quick filter by created_after (parse created_at from JSON)
        if "created_after" in filters and filters["created_after"] is not None:
            created_at_str = data.get("created_at")
            if created_at_str:
                try:
                    thread_created = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                    if thread_created < filters["created_after"]:
                        return False
                except (ValueError, TypeError):
                    pass  # If we can't parse, let full validation handle it
        
        # Quick filter by created_before
        if "created_before" in filters and filters["created_before"] is not None:
            created_at_str = data.get("created_at")
            if created_at_str:
                try:
                    thread_created = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                    if thread_created > filters["created_before"]:
                        return False
                except (ValueError, TypeError):
                    pass
        
        # For started_after and finished_before, we need full validation
        # (these fields might be None and need proper handling)
        # So we return True to let full validation handle them
        
        return True

    async def _update_thread_indexes(self, thread: Thread, is_delete: bool = False) -> None:
        """Update indexes for app_id and user_id when thread is created/updated/deleted.
        
        Args:
            thread: Thread instance
            is_delete: If True, remove from indexes; if False, add/update indexes
        """
        app_id = thread.metadata.get("app_id") if thread.metadata else None
        user_id = thread.metadata.get("user_id") if thread.metadata else None
        
        if app_id:
            if is_delete:
                await self._remove_from_index(self.app_id_index_dir, app_id, thread.id)
            else:
                await self._add_to_index(self.app_id_index_dir, app_id, thread.id)
        
        if user_id:
            if is_delete:
                await self._remove_from_index(self.user_id_index_dir, user_id, thread.id)
            else:
                await self._add_to_index(self.user_id_index_dir, user_id, thread.id)
    
    async def _add_to_index(self, index_dir: Path, key: str, thread_id: str) -> None:
        """Add a thread_id to an index file.
        
        Args:
            index_dir: Directory for the index (app_id_index_dir or user_id_index_dir)
            key: Index key (app_id or user_id value)
            thread_id: Thread ID to add
        """
        await self._ensure_directories()
        # Sanitize key for filename (replace special chars with hash)
        safe_key = hashlib.md5(key.encode()).hexdigest() if any(c in key for c in '/\\:<>"|?*') else key
        index_file = index_dir / f"{safe_key}.json"
        
        # Read existing index
        thread_ids = set()
        if await aios.path.exists(index_file):
            try:
                async with aiofiles.open(index_file, "r") as f:
                    content = await f.read()
                    data = json.loads(content)
                    thread_ids = set(data.get("thread_ids", []))
            except (json.JSONDecodeError, ValueError, KeyError):
                # If index is corrupted, start fresh
                thread_ids = set()
        
        # Add thread_id
        thread_ids.add(thread_id)
        
        # Write back
        async with aiofiles.open(index_file, "w") as f:
            await f.write(json.dumps({"thread_ids": sorted(thread_ids)}, indent=2))
    
    async def _remove_from_index(self, index_dir: Path, key: str, thread_id: str) -> None:
        """Remove a thread_id from an index file.
        
        Args:
            index_dir: Directory for the index (app_id_index_dir or user_id_index_dir)
            key: Index key (app_id or user_id value)
            thread_id: Thread ID to remove
        """
        # Sanitize key for filename
        safe_key = hashlib.md5(key.encode()).hexdigest() if any(c in key for c in '/\\:<>"|?*') else key
        index_file = index_dir / f"{safe_key}.json"
        
        if not await aios.path.exists(index_file):
            return
        
        try:
            # Read existing index
            async with aiofiles.open(index_file, "r") as f:
                content = await f.read()
                data = json.loads(content)
                thread_ids = set(data.get("thread_ids", []))
            
            # Remove thread_id
            thread_ids.discard(thread_id)
            
            # Write back (or delete if empty)
            if thread_ids:
                async with aiofiles.open(index_file, "w") as f:
                    await f.write(json.dumps({"thread_ids": sorted(thread_ids)}, indent=2))
            else:
                # Delete empty index file
                await aios.remove(index_file)
        except (json.JSONDecodeError, ValueError, KeyError, OSError):
            # If index is corrupted or can't be updated, skip
            pass
    
    async def _get_indexed_thread_ids(self, index_dir: Path, key: str) -> set:
        """Get thread IDs from an index file.
        
        Args:
            index_dir: Directory for the index (app_id_index_dir or user_id_index_dir)
            key: Index key (app_id or user_id value)
            
        Returns:
            Set of thread IDs
        """
        thread_ids, _ = await self._get_indexed_thread_ids_with_status(index_dir, key)
        return thread_ids
    
    async def _get_indexed_thread_ids_with_status(self, index_dir: Path, key: str) -> tuple[set, bool]:
        """Get thread IDs from an index file and indicate if index exists.
        
        Args:
            index_dir: Directory for the index (app_id_index_dir or user_id_index_dir)
            key: Index key (app_id or user_id value)
            
        Returns:
            Tuple of (set of thread IDs, bool indicating if index file exists)
        """
        # Sanitize key for filename
        safe_key = hashlib.md5(key.encode()).hexdigest() if any(c in key for c in '/\\:<>"|?*') else key
        index_file = index_dir / f"{safe_key}.json"
        
        if not await aios.path.exists(index_file):
            return set(), False
        
        try:
            async with aiofiles.open(index_file, "r") as f:
                content = await f.read()
                data = json.loads(content)
                thread_ids = set(data.get("thread_ids", []))
                return thread_ids, True
        except (json.JSONDecodeError, ValueError, KeyError):
            # If index is corrupted, return empty set and indicate index exists but is corrupted
            # This will trigger a rebuild
            return set(), False

    async def _scan_directory(self, directory: Path):
        """Async generator to scan directory files."""
        try:
            entries = await aios.listdir(directory)
            for entry in entries:
                yield directory / entry
        except FileNotFoundError:
            return

    def _matches_filters(self, thread: Thread, filters: Dict[str, Any]) -> bool:
        """Check if thread matches all provided filters.
        
        Args:
            thread: Thread to check
            filters: Filter criteria
            
        Returns:
            True if thread matches all filters, False otherwise
        """
        # Filter by state
        if "state" in filters and filters["state"] is not None:
            if thread.state != filters["state"]:
                return False
        
        # Filter by name (supports prefix matching with * suffix)
        if "name" in filters and filters["name"] is not None:
            name_filter = filters["name"]
            if name_filter.endswith("*"):
                # Prefix match
                if not thread.name or not thread.name.startswith(name_filter[:-1]):
                    return False
            else:
                # Exact match
                if thread.name != name_filter:
                    return False
        
        # Filter by metadata fields
        if "user_id" in filters and filters["user_id"] is not None:
            if thread.metadata.get("user_id") != filters["user_id"]:
                return False
        
        if "app_id" in filters and filters["app_id"] is not None:
            if thread.metadata.get("app_id") != filters["app_id"]:
                return False
        
        # Filter by schedule_id
        if "schedule_id" in filters and filters["schedule_id"] is not None:
            if thread.schedule_id != filters["schedule_id"]:
                return False
        
        # Filter by run_id
        if "run_id" in filters and filters["run_id"] is not None:
            if thread.run_id != filters["run_id"]:
                return False
        
        # Filter by task_id (from metadata)
        if "task_id" in filters and filters["task_id"] is not None:
            if thread.metadata.get("task_id") != filters["task_id"]:
                return False
        
        # Filter by task_version (from metadata)
        if "task_version" in filters and filters["task_version"] is not None:
            if thread.metadata.get("task_version") != filters["task_version"]:
                return False
        
        # Filter by created_after
        if "created_after" in filters and filters["created_after"] is not None:
            if thread.created_at < filters["created_after"]:
                return False
        
        # Filter by created_before
        if "created_before" in filters and filters["created_before"] is not None:
            if thread.created_at > filters["created_before"]:
                return False
        
        # Filter by started_after
        if "started_after" in filters and filters["started_after"] is not None:
            if thread.started_at is None or thread.started_at < filters["started_after"]:
                return False
        
        # Filter by finished_before
        if "finished_before" in filters and filters["finished_before"] is not None:
            if thread.finished_at is None or thread.finished_at > filters["finished_before"]:
                return False
        
        return True

    async def create_artifact(self, artifact: Artifact) -> None:
        """Create a new artifact, storing as JSON file.
        
        Args:
            artifact: Artifact instance to store
        """
        await self._ensure_directories()
        file_path = self.artifacts_dir / f"{artifact.id}.json"
        
        async with aiofiles.open(file_path, "w") as f:
            await f.write(artifact.model_dump_json(exclude_none=False))

    async def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        """Get an artifact by ID.
        
        Args:
            artifact_id: Artifact identifier
            
        Returns:
            Artifact instance if found, None otherwise
        """
        file_path = self.artifacts_dir / f"{artifact_id}.json"
        
        if not await aios.path.exists(file_path):
            return None
        
        async with aiofiles.open(file_path, "r") as f:
            content = await f.read()
            data = json.loads(content)
            return Artifact.model_validate(data)

    async def get_thread_artifacts(self, thread_id: str) -> List[Artifact]:
        """Get all artifacts for a thread.
        
        Args:
            thread_id: Thread identifier
            
        Returns:
            List of Artifact instances for the thread
        """
        if not await aios.path.exists(self.artifacts_dir):
            return []
        
        artifacts: List[Artifact] = []
        
        # Scan all artifact files
        async for file_path in self._scan_directory(self.artifacts_dir):
            if file_path.suffix == ".json":
                try:
                    async with aiofiles.open(file_path, "r") as f:
                        content = await f.read()
                        data = json.loads(content)
                        artifact = Artifact.model_validate(data)
                        
                        # Filter by thread_id
                        if artifact.thread_id == thread_id:
                            artifacts.append(artifact)
                except (json.JSONDecodeError, ValueError):
                    # Skip invalid files
                    continue
        
        # Sort by created_at
        artifacts.sort(key=lambda a: a.created_at)
        
        return artifacts

    async def delete_artifact(self, artifact_id: str) -> None:
        """Delete an artifact.
        
        Args:
            artifact_id: Artifact identifier to delete
        """
        file_path = self.artifacts_dir / f"{artifact_id}.json"
        
        if await aios.path.exists(file_path):
            await aios.remove(file_path)

    async def query_artifacts(self, filters: Dict[str, Any]) -> List[Artifact]:
        """Query artifacts across threads with filters.
        
        Args:
            filters: Filter dictionary containing:
                - ref: Optional[str] - Ref filter (supports prefix wildcards with *)
                - kind: Optional[str] - Artifact kind filter
                - media_type: Optional[str] - Media type filter
                - thread_id: Optional[str] - Filter by thread ID
                - app_id: Optional[str] - Filter by app_id (from thread metadata)
                - include_archived: Optional[bool] - Include archived artifacts (default: False)
                - limit: Optional[int] - Maximum number of results
                - cursor: Optional[str] - Pagination cursor
                
        Returns:
            List of Artifact instances matching filters
        """
        if not await aios.path.exists(self.artifacts_dir):
            return []
        
        artifacts: List[Artifact] = []
        include_archived = filters.get("include_archived", False)
        
        # Scan all artifact files
        async for file_path in self._scan_directory(self.artifacts_dir):
            if file_path.suffix == ".json":
                try:
                    async with aiofiles.open(file_path, "r") as f:
                        content = await f.read()
                        data = json.loads(content)
                        artifact = Artifact.model_validate(data)
                        
                        # Filter by archived status (unless include_archived=True)
                        if not include_archived and artifact.archived:
                            continue
                        
                        # Filter by thread_id
                        if "thread_id" in filters and filters["thread_id"] is not None:
                            if artifact.thread_id != filters["thread_id"]:
                                continue
                        
                        # Filter by app_id (requires loading thread metadata)
                        if "app_id" in filters and filters["app_id"] is not None:
                            if artifact.thread_id:
                                thread = await self.get_thread(artifact.thread_id)
                                if thread and thread.metadata.get("app_id") != filters["app_id"]:
                                    continue
                        
                        # Filter by task_id (requires loading thread metadata)
                        if "task_id" in filters and filters["task_id"] is not None:
                            if artifact.thread_id:
                                thread = await self.get_thread(artifact.thread_id)
                                if thread and thread.metadata.get("task_id") != filters["task_id"]:
                                    continue
                        
                        # Filter by task_version (requires loading thread metadata)
                        if "task_version" in filters and filters["task_version"] is not None:
                            if artifact.thread_id:
                                thread = await self.get_thread(artifact.thread_id)
                                if thread and thread.metadata.get("task_version") != filters["task_version"]:
                                    continue
                        
                        # Filter by kind
                        if "kind" in filters and filters["kind"] is not None:
                            if artifact.kind != filters["kind"]:
                                continue
                        
                        # Filter by media_type
                        if "media_type" in filters and filters["media_type"] is not None:
                            if artifact.media_type != filters["media_type"]:
                                continue
                        
                        # Filter by ref (supports prefix wildcards)
                        if "ref" in filters and filters["ref"] is not None:
                            ref_pattern = filters["ref"]
                            if ref_pattern.endswith("*"):
                                prefix = ref_pattern[:-1]
                                if not artifact.ref or not artifact.ref.startswith(prefix):
                                    continue
                            else:
                                if artifact.ref != ref_pattern:
                                    continue
                        
                        # Filter by direction
                        if "direction" in filters and filters["direction"] is not None:
                            direction_filter = filters["direction"]
                            if direction_filter != "both":
                                if artifact.direction != direction_filter:
                                    continue
                        
                        artifacts.append(artifact)
                except (json.JSONDecodeError, ValueError):
                    # Skip invalid files
                    continue
        
        # Sort by created_at descending (newest first)
        artifacts.sort(key=lambda a: a.created_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        
        # Note: Pagination (limit/offset) is handled at the API layer
        # to maintain consistency with cursor-based pagination
        
        return artifacts

    # Schedule methods

    async def create_schedule(self, schedule: Schedule) -> None:
        """Create a new schedule, storing as JSON file.
        
        Args:
            schedule: Schedule instance to store
        """
        await self._ensure_directories()
        file_path = self.schedules_dir / f"{schedule.id}.json"
        
        async with aiofiles.open(file_path, "w") as f:
            await f.write(schedule.model_dump_json(exclude_none=False))

    async def get_schedule(self, schedule_id: str) -> Optional[Schedule]:
        """Get a schedule by ID.
        
        Args:
            schedule_id: Schedule identifier
            
        Returns:
            Schedule instance if found, None otherwise
        """
        file_path = self.schedules_dir / f"{schedule_id}.json"
        
        if not await aios.path.exists(file_path):
            return None
        
        async with aiofiles.open(file_path, "r") as f:
            content = await f.read()
            data = json.loads(content)
            return Schedule.model_validate(data)

    async def update_schedule(self, schedule: Schedule) -> None:
        """Update an existing schedule.
        
        Args:
            schedule: Schedule instance with updated data
        """
        await self._ensure_directories()
        file_path = self.schedules_dir / f"{schedule.id}.json"
        
        async with aiofiles.open(file_path, "w") as f:
            await f.write(schedule.model_dump_json(exclude_none=False))

    async def delete_schedule(self, schedule_id: str) -> None:
        """Delete a schedule.
        
        Args:
            schedule_id: Schedule identifier to delete
        """
        file_path = self.schedules_dir / f"{schedule_id}.json"
        
        if await aios.path.exists(file_path):
            await aios.remove(file_path)

    async def query_schedules(self, filters: Dict[str, Any]) -> List[Schedule]:
        """Query schedules with filters.
        
        Args:
            filters: Filter dictionary containing:
                - state: Optional[str] - Filter by schedule state
                - limit: Optional[int] - Maximum number of results
                - cursor: Optional[str] - Pagination cursor
                
        Returns:
            List of Schedule instances matching filters
        """
        if not await aios.path.exists(self.schedules_dir):
            return []
        
        schedules: List[Schedule] = []
        
        # Scan all schedule files
        async for file_path in self._scan_directory(self.schedules_dir):
            if file_path.suffix == ".json":
                try:
                    async with aiofiles.open(file_path, "r") as f:
                        content = await f.read()
                        data = json.loads(content)
                        schedule = Schedule.model_validate(data)
                        
                        # Apply filters
                        if "state" in filters and filters["state"] is not None:
                            if schedule.state != filters["state"]:
                                continue
                        if "task_id" in filters and filters["task_id"] is not None:
                            if schedule.task_id != filters["task_id"]:
                                continue
                        if "task_version" in filters and filters["task_version"] is not None:
                            if schedule.task_version != filters["task_version"]:
                                continue
                        
                        schedules.append(schedule)
                except (json.JSONDecodeError, ValueError):
                    # Skip invalid files
                    continue
        
        # Sort by created_at descending (newest first)
        schedules.sort(key=lambda s: s.created_at, reverse=True)
        
        # Apply pagination
        limit = filters.get("limit")
        if limit is not None:
            schedules = schedules[:limit]
        
        return schedules

    # Run methods

    async def create_run(self, run: Run) -> None:
        """Create a new run, storing as JSON file.
        
        Args:
            run: Run instance to store
        """
        await self._ensure_directories()
        # Store runs in subdirectory by schedule_id
        schedule_runs_dir = self.runs_dir / run.schedule_id
        await aios.makedirs(schedule_runs_dir, exist_ok=True)
        file_path = schedule_runs_dir / f"{run.run_id}.json"
        
        async with aiofiles.open(file_path, "w") as f:
            await f.write(run.model_dump_json(exclude_none=False))

    async def get_run(self, schedule_id: str, run_id: str) -> Optional[Run]:
        """Get a run by schedule_id and run_id.
        
        Args:
            schedule_id: Schedule identifier
            run_id: Run identifier
            
        Returns:
            Run instance if found, None otherwise
        """
        schedule_runs_dir = self.runs_dir / schedule_id
        file_path = schedule_runs_dir / f"{run_id}.json"
        
        if not await aios.path.exists(file_path):
            return None
        
        async with aiofiles.open(file_path, "r") as f:
            content = await f.read()
            data = json.loads(content)
            return Run.model_validate(data)

    async def update_run(self, run: Run) -> None:
        """Update an existing run.
        
        Args:
            run: Run instance with updated data
        """
        await self._ensure_directories()
        schedule_runs_dir = self.runs_dir / run.schedule_id
        await aios.makedirs(schedule_runs_dir, exist_ok=True)
        file_path = schedule_runs_dir / f"{run.run_id}.json"
        
        async with aiofiles.open(file_path, "w") as f:
            await f.write(run.model_dump_json(exclude_none=False))

    async def delete_run(self, schedule_id: str, run_id: str) -> None:
        """Delete a run.
        
        Args:
            schedule_id: Schedule identifier
            run_id: Run identifier to delete
        """
        schedule_runs_dir = self.runs_dir / schedule_id
        file_path = schedule_runs_dir / f"{run_id}.json"
        
        if await aios.path.exists(file_path):
            await aios.remove(file_path)

    async def query_runs(
        self, schedule_id: str, filters: Dict[str, Any]
    ) -> List[Run]:
        """Query runs for a schedule with filters.
        
        Args:
            schedule_id: Schedule identifier
            filters: Filter dictionary containing:
                - state: Optional[str] - Filter by run state
                - scheduled_after: Optional[datetime] - Filter runs scheduled after this time (UTC)
                - scheduled_before: Optional[datetime] - Filter runs scheduled before this time (UTC)
                - limit: Optional[int] - Maximum number of results
                - cursor: Optional[str] - Pagination cursor
                
        Returns:
            List of Run instances matching filters
        """
        schedule_runs_dir = self.runs_dir / schedule_id
        
        if not await aios.path.exists(schedule_runs_dir):
            return []
        
        runs: List[Run] = []
        
        # Scan all run files for this schedule
        async for file_path in self._scan_directory(schedule_runs_dir):
            if file_path.suffix == ".json":
                try:
                    async with aiofiles.open(file_path, "r") as f:
                        content = await f.read()
                        data = json.loads(content)
                        run = Run.model_validate(data)
                        
                        # Apply filters
                        if "state" in filters and filters["state"] is not None:
                            if run.state != filters["state"]:
                                continue
                        
                        if "scheduled_after" in filters and filters["scheduled_after"] is not None:
                            if run.scheduled_for_utc < filters["scheduled_after"]:
                                continue
                        
                        if "scheduled_before" in filters and filters["scheduled_before"] is not None:
                            if run.scheduled_for_utc > filters["scheduled_before"]:
                                continue
                        
                        runs.append(run)
                except (json.JSONDecodeError, ValueError):
                    # Skip invalid files
                    continue
        
        # Sort by scheduled_for_utc descending (newest first)
        runs.sort(key=lambda r: r.scheduled_for_utc, reverse=True)
        
        # Apply pagination
        limit = filters.get("limit")
        if limit is not None:
            runs = runs[:limit]
        
        return runs

    async def get_running_run_by_schedule(self, schedule_id: str) -> Optional[Run]:
        """Get the currently running run for a schedule (if any).
        
        Args:
            schedule_id: Schedule identifier
            
        Returns:
            Run instance if found, None otherwise
        """
        runs = await self.query_runs(schedule_id, {"state": "running"})
        if runs:
            return runs[0]  # Return first running run found
        return None

