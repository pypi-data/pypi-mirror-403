"""ThreadService for managing thread business logic."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, Optional

from task_framework.errors import IDEMPOTENCY_CONFLICT
from task_framework.logging import logger
from task_framework.models.artifact import Artifact
from task_framework.models.pagination import Pagination
from task_framework.models.thread import Thread
from task_framework.models.thread_create_request import ThreadCreateRequest
from task_framework.models.thread_list_response import ThreadListResponse
from task_framework.models.thread_query_filters import ThreadQueryFilters
from task_framework.models.thread_retry_request import ThreadRetryRequest
from task_framework.services.artifact_service import ArtifactService
from task_framework.thread_state import ThreadState
from task_framework.utils.artifact_validation import ArtifactValidationError
from task_framework.utils.metrics_helpers import update_thread_state_gauge

if TYPE_CHECKING:
    from task_framework.execution import ExecutionEngine
    from task_framework.interfaces.database import Database
    from task_framework.interfaces.idempotency import IdempotencyStore


class ThreadService:
    """Service layer for thread management operations."""

    def __init__(
        self,
        database: "Database",
        idempotency_store: "IdempotencyStore",
        execution_engine: "ExecutionEngine",
        concurrency_manager: Optional[Any] = None,
    ) -> None:
        """Initialize ThreadService.
        
        Args:
            database: Database implementation for thread persistence
            idempotency_store: IdempotencyStore implementation for idempotency key tracking
            execution_engine: ExecutionEngine for thread execution
            concurrency_manager: Optional ConcurrencyManager for thread limit enforcement
        """
        self.database = database
        self.idempotency_store = idempotency_store
        self.execution_engine = execution_engine
        self.concurrency_manager = concurrency_manager

    async def create_thread(
        self,
        request: ThreadCreateRequest,
        user_id: Optional[str],
        app_id: Optional[str],
        is_admin: bool,
        task_function: Any,
        task_definition: Optional[Any] = None,
        requested_version: Optional[str] = None,
    ) -> Thread:
        """Create a new thread and optionally execute it.
        
        Args:
            request: Thread creation request
            user_id: User identifier from AuthenticatedRequest
            app_id: Application identifier from AuthenticatedRequest
            task_function: Task function to execute
            task_definition: Optional TaskDefinition (for multi-task mode, to provide output schemas)
            requested_version: Optional version that was explicitly requested (vs resolved latest)
            
        Returns:
            Created Thread instance
            
        Raises:
            ValueError: If idempotency key conflict occurs
        """
        # Check idempotency if key provided
        if request.idempotency_key and user_id and app_id:
            existing_thread = await self.idempotency_store.get(
                request.idempotency_key, user_id, app_id
            )
            if existing_thread:
                # Return existing thread (idempotency)
                return existing_thread
        
        # Generate thread ID
        from task_framework.utils.id_generator import generate_thread_id, generate_artifact_id
        thread_id = generate_thread_id()
        
        # Merge metadata with user_id/app_id from AuthenticatedRequest
        metadata = request.metadata.copy() if request.metadata else {}
        if user_id:
            metadata["user_id"] = user_id
        if app_id:
            metadata["app_id"] = app_id
        
        # Store task_id and task_version in metadata if task_definition is provided (multi-task mode)
        if task_definition:
            metadata["task_id"] = task_definition.task_id
            # Use requested_version if explicitly provided, otherwise use task_definition.version (latest)
            # This ensures we store the version the user actually requested, not just the resolved one
            metadata["task_version"] = requested_version if requested_version else task_definition.version
        
        # Create thread using ExecutionEngine
        thread = self.execution_engine.create_thread(
            thread_id=thread_id,
            name=request.name,
            metadata=metadata,
            params=request.params or {},
        )
        
        # Set inputs from request
        thread.inputs = request.inputs.copy()
        
        # Create ArtifactService for validation
        artifact_service = ArtifactService(self.database)
        
        # Note: is_admin parameter is passed from API layer (auth.key_type == "admin")
        
        # Process input artifacts: handle references vs new artifacts
        processed_inputs = []
        
        for artifact in thread.inputs:
            # Check if this might be an artifact reference (has ID)
            # If artifact has an ID, check if it exists in the database
            if artifact.id and artifact.id != "":
                existing_artifact = await artifact_service.get_artifact(artifact.id)
                if existing_artifact:
                    # This is a reference to an existing artifact
                    # Validate that the artifact is accessible
                    try:
                        referenced_artifact = await artifact_service.validate_artifact_reference(
                            artifact.id,
                            user_id=user_id,
                            app_id=app_id,
                            is_admin=is_admin,
                        )
                        # Use the referenced artifact (don't create new)
                        # Artifact keeps its original thread_id, but is linked to this thread via inputs
                        processed_inputs.append(referenced_artifact)
                        continue  # Skip to next artifact
                    except ValueError as e:
                        # Re-raise with clearer context
                        from task_framework.errors import ARTIFACT_NOT_FOUND
                        raise ValueError(f"Invalid artifact reference: {e}") from e
            
            # This is a new artifact to be created
            artifact.thread_id = thread_id
            artifact.direction = "input"  # Mark as input artifact
            if not artifact.id or artifact.id == "":
                artifact.id = generate_artifact_id()
            if not artifact.created_at:
                artifact.created_at = datetime.now(timezone.utc)
            
            # Validate new artifact schema
            try:
                artifact_service.validate_artifact_schema(artifact)
            except ArtifactValidationError as e:
                # Re-raise with context
                raise ValueError(f"Invalid input artifact: {e.message}") from e
            
            processed_inputs.append(artifact)
        
        # Update thread with processed inputs
        thread.inputs = processed_inputs
        
        # Store thread in database
        await self.database.create_thread(thread)
        
        # Create all ad-hoc webhooks BEFORE publishing events or executing tasks
        # This ensures webhooks exist and can receive all thread lifecycle events
        if request.webhooks:
            try:
                from task_framework.services.webhook_service import WebhookService
                from task_framework.storage_factory import StorageFactory

                # Use storage factory to get appropriate webhook repositories
                storage_factory = StorageFactory.from_env()
                webhook_repository = storage_factory.create_webhook_repository()
                delivery_repository = storage_factory.create_webhook_delivery_repository()
                webhook_service = WebhookService(
                    webhook_repository=webhook_repository,
                    delivery_repository=delivery_repository,
                )

                created_by = user_id or app_id
                for webhook_config in request.webhooks:
                    try:
                        ad_hoc_webhook = await webhook_service.create_ad_hoc_webhook(
                            url=webhook_config.callback_url,
                            thread_id=thread.id,
                            events=webhook_config.events,
                            created_by=created_by,
                            api_key=webhook_config.api_key,
                        )
                        
                        logger.info(
                            "webhook.ad_hoc.created",
                            webhook_id=ad_hoc_webhook.id,
                            thread_id=thread.id,
                            url=webhook_config.callback_url,
                        )
                    except Exception as e:
                        # Log error but don't fail thread creation if individual webhook setup fails
                        logger.error(
                            "webhook.ad_hoc.creation.failed",
                            thread_id=thread.id,
                            url=webhook_config.callback_url,
                            error=str(e),
                            exc_info=True,
                        )
                        # Continue creating other webhooks
            except Exception as e:
                # Log error but don't fail thread creation if webhook service setup fails
                logger.error(
                    "webhook.service.setup.failed",
                    thread_id=thread.id,
                    error=str(e),
                    exc_info=True,
                )
                # Continue without failing thread creation
        
        # Publish thread.created event (webhooks are now created and can receive it)
        if self.execution_engine.framework.event_publisher:
            await self.execution_engine.framework.event_publisher.publish(
                event_type="thread.created",
                thread_id=thread.id,
                thread=thread,
                metadata=thread.metadata,
            )
        
        # Store new artifacts (references are already stored, so skip them)
        for artifact in thread.inputs:
            # Only create if this artifact doesn't already exist (check by ID)
            existing = await artifact_service.get_artifact(artifact.id)
            if not existing:
                # This is a new artifact, create it
                await artifact_service.create_artifact(artifact)
            # If existing, it's a reference - already linked to thread via inputs list
            # Artifact persists independently (FR-010: artifacts persist when threads fail/stop)
        
        # Store idempotency key if provided
        if request.idempotency_key and user_id and app_id:
            await self.idempotency_store.set(
                request.idempotency_key, user_id, app_id, thread_id
            )
        
        # Execute thread based on mode
        if request.mode == "sync":
            # Execute synchronously (wait for completion)
            # Create execution engine with timeout if specified
            if request.timeout_seconds:
                from task_framework.execution import ExecutionEngine
                timeout_engine = ExecutionEngine(
                    framework=self.execution_engine.framework,
                    timeout_seconds=request.timeout_seconds
                )
                thread = await timeout_engine.execute_task(thread, task_function, task_definition)
            else:
                thread = await self.execution_engine.execute_task(thread, task_function, task_definition)
            
            # Update thread in database after execution
            await self.database.update_thread(thread)
            # Load all artifacts and split into inputs/outputs based on thread start time
            all_artifacts = await self.database.get_thread_artifacts(thread_id)
            thread_start_time = thread.started_at or thread.created_at
            thread.inputs = [a for a in all_artifacts if a.created_at < thread_start_time]
            thread.outputs = [a for a in all_artifacts if a.created_at >= thread_start_time]
            await self.database.update_thread(thread)
        else:
            # Async mode: schedule execution in background and return queued thread
            import asyncio

            async def _background_runner(thread_obj: Thread) -> None:
                try:
                    # Wait for concurrency slot if manager is configured
                    if self.concurrency_manager:
                        # Efficiently wait for a slot using semaphore (no polling)
                        # Initially set state to queued while waiting
                        thread_obj.state = ThreadState.QUEUED
                        await self.database.update_thread(thread_obj)
                        update_thread_state_gauge(None, "queued")
                        
                        # This blocks efficiently until a slot is available
                        await self.concurrency_manager.wait_for_slot(thread_obj.id)
                        
                        # Got a slot - update state to running
                        thread_obj.state = ThreadState.RUNNING
                        await self.database.update_thread(thread_obj)
                        update_thread_state_gauge("queued", "running")
                    
                    # Execute the task (respecting timeout if set on engine)
                    if request.timeout_seconds:
                        from task_framework.execution import ExecutionEngine

                        timeout_engine = ExecutionEngine(
                            framework=self.execution_engine.framework,
                            timeout_seconds=request.timeout_seconds,
                        )
                        finished_thread = await timeout_engine.execute_task(thread_obj, task_function, task_definition)
                    else:
                        finished_thread = await self.execution_engine.execute_task(thread_obj, task_function, task_definition)

                    # Update DB and split artifacts
                    await self.database.update_thread(finished_thread)
                    all_artifacts = await self.database.get_thread_artifacts(thread_obj.id)
                    thread_start_time = finished_thread.started_at or finished_thread.created_at
                    finished_thread.inputs = [a for a in all_artifacts if a.created_at < thread_start_time]
                    finished_thread.outputs = [a for a in all_artifacts if a.created_at >= thread_start_time]
                    await self.database.update_thread(finished_thread)
                except Exception as e:
                    # Log error and mark thread as failed
                    logger.error("thread.background_execution_failed", thread_id=thread_obj.id, error=str(e), exc_info=True)
                    try:
                        thread_obj.state = ThreadState.FAILED
                        thread_obj.finished_at = datetime.now(timezone.utc)
                        await self.database.update_thread(thread_obj)
                    except Exception:
                        logger.error("thread.background_failure_update_failed", thread_id=thread_obj.id, error=str(e), exc_info=True)
                finally:
                    # Release concurrency slot
                    if self.concurrency_manager:
                        await self.concurrency_manager.release_slot(thread_obj.id)

            # Start the background runner but don't await it
            try:
                asyncio.create_task(_background_runner(thread))
            except RuntimeError:
                # No running loop in this context (unlikely in FastAPI), log and skip
                logger.warning("background_task_creation_failed", thread_id=thread.id)
        
        return thread

    async def list_threads(
        self,
        filters: ThreadQueryFilters,
        user_id: Optional[str],
        app_id: Optional[str],
        is_admin: bool,
    ) -> ThreadListResponse:
        """List threads with filtering and pagination.
        
        Args:
            filters: Query filters
            user_id: User identifier from AuthenticatedRequest
            app_id: Application identifier from AuthenticatedRequest
            is_admin: Whether request is from admin API key
            
        Returns:
            ThreadListResponse with paginated results
        """
        # Build filter dict for database query
        filter_dict: Dict[str, Any] = {}
        
        if filters.state:
            filter_dict["state"] = filters.state
        if filters.name:
            filter_dict["name"] = filters.name
        if filters.user_id:
            filter_dict["user_id"] = filters.user_id
        if filters.app_id:
            filter_dict["app_id"] = filters.app_id
        if filters.schedule_id:
            filter_dict["schedule_id"] = filters.schedule_id
        if filters.run_id:
            filter_dict["run_id"] = filters.run_id
        if filters.task_id:
            filter_dict["task_id"] = filters.task_id
        if filters.task_version:
            filter_dict["task_version"] = filters.task_version
        if filters.created_after:
            filter_dict["created_after"] = filters.created_after
        if filters.created_before:
            filter_dict["created_before"] = filters.created_before
        if filters.started_after:
            filter_dict["started_after"] = filters.started_after
        if filters.finished_before:
            filter_dict["finished_before"] = filters.finished_before
        
        # Apply access control filtering (unless admin)
        if not is_admin:
            if user_id:
                filter_dict["user_id"] = user_id
            if app_id:
                filter_dict["app_id"] = app_id
        
        # Pass limit to database for early stopping optimization
        # The database can use this to stop scanning files early
        limit_for_db = filters.limit or 50
        filter_dict_with_limit = filter_dict.copy()
        filter_dict_with_limit["limit"] = limit_for_db * 3  # Get 3x limit to account for filtering
        
        # Query threads
        threads = await self.database.query_threads(filter_dict_with_limit)
        
        # Apply pagination
        limit = filters.limit or 50
        cursor = filters.cursor
        
        # Cursor-based pagination
        if cursor:
            # Decode cursor (Base64 JSON with thread_id and created_at)
            import base64
            import json as json_lib
            
            try:
                cursor_data = json_lib.loads(base64.b64decode(cursor).decode())
                cursor_thread_id = cursor_data.get("thread_id")
                cursor_created_at = cursor_data.get("created_at")
                
                # Filter threads after cursor
                if cursor_created_at:
                    from datetime import datetime
                    cursor_time = datetime.fromisoformat(cursor_created_at.replace("Z", "+00:00"))
                    threads = [t for t in threads if t.created_at < cursor_time]
            except (ValueError, KeyError, TypeError):
                # Invalid cursor, return empty
                threads = []
        
        # Offset-based pagination fallback
        elif filters.offset is not None:
            threads = threads[filters.offset:]
        
        # Apply limit
        has_more = len(threads) > limit
        threads = threads[:limit]
        
        # Generate next cursor if has_more
        next_cursor = None
        if has_more and threads:
            import base64
            import json as json_lib
            
            last_thread = threads[-1]
            cursor_data = {
                "thread_id": last_thread.id,
                "created_at": last_thread.created_at.isoformat() + "Z",
            }
            next_cursor = base64.b64encode(json_lib.dumps(cursor_data).encode()).decode()
        
        pagination = Pagination(
            cursor=next_cursor,
            has_more=has_more,
            total=None,  # Total not available for file-based implementation
        )
        
        return ThreadListResponse(items=threads, pagination=pagination)

    async def get_thread(
        self,
        thread_id: str,
        user_id: Optional[str],
        app_id: Optional[str],
        is_admin: bool,
    ) -> Optional[Thread]:
        """Get thread by ID with access control.
        
        Args:
            thread_id: Thread identifier
            user_id: User identifier from AuthenticatedRequest
            app_id: Application identifier from AuthenticatedRequest
            is_admin: Whether request is from admin API key
            
        Returns:
            Thread instance if found and accessible, None otherwise
        """
        thread = await self.database.get_thread(thread_id)
        
        if not thread:
            return None
        
        # Apply access control filtering (unless admin)
        if not is_admin:
            if user_id and thread.metadata.get("user_id") != user_id:
                return None
            if app_id and thread.metadata.get("app_id") != app_id:
                return None
        
        # Load artifacts and separate into inputs/outputs
        all_artifacts = await self.database.get_thread_artifacts(thread_id)
        
        # Inputs are artifacts created before thread started_at (or created_at if not started)
        # Outputs are artifacts created during/after execution
        thread_start_time = thread.started_at or thread.created_at
        
        thread.inputs = [a for a in all_artifacts if a.created_at < thread_start_time]
        thread.outputs = [a for a in all_artifacts if a.created_at >= thread_start_time]
        
        return thread

    async def stop_thread(
        self,
        thread_id: str,
        user_id: Optional[str],
        app_id: Optional[str],
        is_admin: bool,
    ) -> Thread:
        """Stop a running thread.
        
        Args:
            thread_id: Thread identifier
            user_id: User identifier from AuthenticatedRequest
            app_id: Application identifier from AuthenticatedRequest
            is_admin: Whether request is from admin API key
            
        Returns:
            Updated Thread instance
            
        Raises:
            ValueError: If thread not found or invalid state
        """
        thread = await self.database.get_thread(thread_id)
        
        if not thread:
            raise ValueError(f"Thread {thread_id} not found")
        
        # Apply access control filtering (unless admin)
        if not is_admin:
            if user_id and thread.metadata.get("user_id") != user_id:
                raise ValueError(f"Thread {thread_id} not found")
            if app_id and thread.metadata.get("app_id") != app_id:
                raise ValueError(f"Thread {thread_id} not found")
        
        # Check if thread is in a stoppable state
        if thread.state not in [ThreadState.QUEUED, ThreadState.RUNNING]:
            state_str = thread.state.value if hasattr(thread.state, 'value') else str(thread.state)
            raise ValueError(f"Thread {thread_id} is in state {state_str}, cannot stop")
        
        # Mark thread as cancelled and update state
        previous_state = thread.state
        thread.state = ThreadState.STOPPED
        thread.finished_at = datetime.now(timezone.utc)
        
        # Set cancelled flag (for context.is_cancelled())
        if hasattr(thread, "_cancelled"):
            thread._cancelled = True
        
        # Update thread in database
        await self.database.update_thread(thread)
        
        # Update gauge for state transition (decrement previous state, increment stopped)
        update_thread_state_gauge(previous_state, thread.state)
        
        # Propagate cancellation to active TaskContext if thread is currently executing
        if self.execution_engine:
            cancelled = self.execution_engine.cancel_context(thread_id)
            if cancelled:
                logger.info(
                    "thread.stop.context_cancelled",
                    thread_id=thread_id,
                    message="Cancellation propagated to active TaskContext",
                )
        
        # Publish thread.stopped event
        if self.execution_engine.framework.event_publisher:
            await self.execution_engine.framework.event_publisher.publish(
                event_type="thread.stopped",
                thread_id=thread.id,
                thread=thread,
                metadata=thread.metadata,
            )
        
        return thread

    async def retry_thread(
        self,
        thread_id: str,
        request: ThreadRetryRequest,
        user_id: Optional[str],
        app_id: Optional[str],
        is_admin: bool,
        task_function: Any,
        task_definition: Optional[Any] = None,
    ) -> Thread:
        """Retry a failed thread.
        
        Args:
            thread_id: Original thread identifier
            request: Retry request options
            user_id: User identifier from AuthenticatedRequest
            app_id: Application identifier from AuthenticatedRequest
            is_admin: Whether request is from admin API key
            task_function: Task function to execute
            task_definition: Optional TaskDefinition (for multi-task mode, to provide output schemas)
            
        Returns:
            New Thread instance (new attempt)
            
        Raises:
            ValueError: If thread not found or invalid state
        """
        original_thread = await self.database.get_thread(thread_id)
        
        if not original_thread:
            raise ValueError(f"Thread {thread_id} not found")
        
        # Apply access control filtering (unless admin)
        if not is_admin:
            if user_id and original_thread.metadata.get("user_id") != user_id:
                raise ValueError(f"Thread {thread_id} not found")
            if app_id and original_thread.metadata.get("app_id") != app_id:
                raise ValueError(f"Thread {thread_id} not found")
        
        # Check if thread is in a retryable state
        retryable_states = [ThreadState.FAILED, ThreadState.STOPPED, ThreadState.TIMEOUT, ThreadState.EXPIRED]
        if original_thread.state not in retryable_states:
            state_str = original_thread.state.value if hasattr(original_thread.state, 'value') else str(original_thread.state)
            raise ValueError(f"Thread {thread_id} is in state {state_str}, cannot retry")
        
        # Generate new thread ID
        from task_framework.utils.id_generator import generate_thread_id, generate_artifact_id
        new_thread_id = generate_thread_id()
        
        # Create new thread with same metadata and params
        new_thread = self.execution_engine.create_thread(
            thread_id=new_thread_id,
            metadata=original_thread.metadata.copy(),
            params=original_thread.params.copy(),
        )
        
        # Copy inputs from original thread
        new_thread.inputs = []
        for original_input in original_thread.inputs:
            new_input = Artifact(
                id=generate_artifact_id(),
                thread_id=new_thread_id,
                kind=original_input.kind,
                media_type=original_input.media_type,
                ref=original_input.ref,
                explain=original_input.explain,
                size=original_input.size,
                sha256=original_input.sha256,
                file_ref=original_input.file_ref,
                url=original_input.url,
                value=original_input.value,
                text=original_input.text,
                labels=original_input.labels.copy() if original_input.labels else {},
                created_at=datetime.now(timezone.utc),
                direction="input",  # Mark as input artifact
            )
            new_thread.inputs.append(new_input)
        
        # Preserve run_id if requested
        if request.preserve_run_id and original_thread.run_id:
            new_thread.run_id = original_thread.run_id
        
        # Set attempt number (increment from original)
        original_attempt = original_thread.attempt or 0
        new_thread.attempt = original_attempt + 1
        
        # Store new thread in database
        await self.database.create_thread(new_thread)
        
        # Store input artifacts
        for artifact in new_thread.inputs:
            await self.database.create_artifact(artifact)
        
        # Execute new thread synchronously (retry is always sync)
        new_thread = await self.execution_engine.execute_task(new_thread, task_function, task_definition)
        
        # Update thread in database after execution
        await self.database.update_thread(new_thread)
        
        # Load output artifacts
        outputs = await self.database.get_thread_artifacts(new_thread_id)
        new_thread.outputs = outputs
        await self.database.update_thread(new_thread)
        
        return new_thread

