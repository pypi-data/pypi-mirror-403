"""Artifact service for managing artifact business logic."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from task_framework.logging import logger
from task_framework.metrics import artifacts_archived_total, artifacts_created_total, artifacts_deleted_total
from task_framework.models.artifact import Artifact
from task_framework.utils.artifact_validation import (
    ArtifactValidationError,
    validate_artifact_fields,
    validate_ref_format,
)
from task_framework.utils.ref_filtering import matches_ref_pattern
from task_framework.utils.sha256 import compute_sha256_streaming

if TYPE_CHECKING:
    from task_framework.interfaces.database import Database
    from task_framework.interfaces.storage import FileStorage


class ArtifactService:
    """Service layer for artifact management operations."""

    def __init__(self, database: "Database", file_storage: Optional["FileStorage"] = None) -> None:
        """Initialize ArtifactService.
        
        Args:
            database: Database implementation for artifact persistence
            file_storage: Optional file storage implementation for file operations
        """
        self.database = database
        self.file_storage = file_storage

    def validate_artifact(self, artifact: Artifact) -> None:
        """Validate artifact schema and fields.
        
        Args:
            artifact: Artifact instance to validate
            
        Raises:
            ArtifactValidationError: If artifact validation fails
        """
        try:
            validate_artifact_fields(artifact)
        except ArtifactValidationError as e:
            # Log validation failure
            logger.error(
                "artifact.validation.failed",
                thread_id=artifact.thread_id,
                error=str(e),
                artifact_kind=artifact.kind,
                validation_errors=e.errors,
            )
            raise

    def validate_artifact_schema(self, artifact: Artifact) -> None:
        """Validate artifact schema with field-level error details.
        
        Args:
            artifact: Artifact instance to validate
            
        Raises:
            ArtifactValidationError: If artifact validation fails, with field-level details
        """
        try:
            validate_artifact_fields(artifact)
        except ArtifactValidationError as e:
            # Log validation failure
            logger.error(
                "artifact.validation.failed",
                thread_id=artifact.thread_id,
                error=str(e),
                artifact_kind=artifact.kind,
                validation_errors=e.errors,
            )
            # Re-raise with field-level details
            raise ArtifactValidationError(e.message, e.errors)

    def check_ref_uniqueness(self, ref: Optional[str], thread_id: Optional[str], exclude_artifact_id: Optional[str] = None) -> bool:
        """Check if ref is unique within a thread.
        
        Args:
            ref: Ref value to check
            thread_id: Thread identifier
            exclude_artifact_id: Artifact ID to exclude from check (for updates)
            
        Returns:
            True if ref is unique or None, False if duplicate exists
        """
        if not ref or not thread_id:
            return True
        
        # Get all artifacts for the thread
        # Note: This is a synchronous check; async implementation will be in database layer
        # For now, return True and let database layer enforce uniqueness
        return True

    async def create_artifact(self, artifact: Artifact) -> Artifact:
        """Create a new artifact.
        
        Args:
            artifact: Artifact instance to create
            
        Returns:
            Created Artifact instance
            
        Raises:
            ArtifactValidationError: If artifact validation fails
        """
        # Validate artifact schema
        self.validate_artifact_schema(artifact)
        
        # Validate ref format
        validate_ref_format(artifact.ref)
        
        # Set defaults
        if not artifact.created_at:
            artifact.created_at = datetime.now(timezone.utc)
        if artifact.archived is None:
            artifact.archived = False
        
        # Compute SHA256 and size for file artifacts
        if artifact.file_ref and artifact.kind in {"file", "binary", "log", "table"}:
            if not artifact.sha256 and self.file_storage:
                # Compute SHA256 synchronously with streaming for large files
                try:
                    # Download file data to compute SHA256
                    # Note: This assumes file_storage has a way to get file path or stream
                    # For now, we'll compute SHA256 if file_storage provides download capability
                    file_data = await self.file_storage.download(artifact.file_ref)
                    from task_framework.utils.sha256 import compute_sha256
                    artifact.sha256 = await compute_sha256(file_data)
                    
                    # Set size if not provided
                    if not artifact.size:
                        artifact.size = len(file_data)
                except Exception as e:
                    # Log warning but don't fail artifact creation
                    logger.warning(
                        "artifact.sha256_computation_failed",
                        artifact_id=artifact.id,
                        file_ref=artifact.file_ref,
                        error=str(e),
                    )
        
        # Check ref uniqueness within thread
        # Note: This will be implemented in database layer for atomicity
        if artifact.ref and artifact.thread_id:
            existing_artifacts = await self.database.get_thread_artifacts(artifact.thread_id)
            for existing in existing_artifacts:
                if existing.id != artifact.id and existing.ref == artifact.ref:
                    raise ArtifactValidationError(
                        f"Duplicate ref '{artifact.ref}' within thread '{artifact.thread_id}'",
                        [{"field": "ref", "message": f"ref '{artifact.ref}' already exists in thread"}],
                    )
        
        # Store artifact
        await self.database.create_artifact(artifact)
        
        # Increment metrics
        artifacts_created_total.labels(kind=artifact.kind).inc()
        
        # Log artifact creation
        logger.info(
            "artifact.created",
            artifact_id=artifact.id,
            kind=artifact.kind,
            thread_id=artifact.thread_id,
            ref=artifact.ref,
            sha256=artifact.sha256,
            size=artifact.size,
        )
        
        return artifact

    async def list_thread_artifacts(
        self,
        thread_id: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Artifact]:
        """List artifacts for a thread with filtering.
        
        Args:
            thread_id: Thread identifier
            filters: Optional filter dictionary containing:
                - ref: Optional[str] - Ref filter (supports prefix wildcards)
                - kind: Optional[str] - Artifact kind filter
                - media_type: Optional[str] - Media type filter
                - direction: Optional[str] - 'input', 'output', or 'both'
                - include_archived: Optional[bool] - Include archived artifacts
                - limit: Optional[int] - Maximum number of results
                - cursor: Optional[str] - Pagination cursor
                
        Returns:
            List of Artifact instances matching filters
        """
        if filters is None:
            filters = {}
        
        # Get all artifacts for thread
        all_artifacts = await self.database.get_thread_artifacts(thread_id)
        
        # Filter by archived status
        include_archived = filters.get("include_archived", False)
        if not include_archived:
            all_artifacts = [a for a in all_artifacts if not a.archived]
        
        # Filter by direction (requires thread metadata to determine input/output)
        if "direction" in filters and filters["direction"] is not None:
            direction = filters["direction"]
            if direction != "both":
                # Get thread to determine input/output based on started_at
                thread = await self.database.get_thread(thread_id)
                if thread:
                    thread_start_time = thread.started_at or thread.created_at
                    if direction == "input":
                        all_artifacts = [a for a in all_artifacts if a.created_at and a.created_at < thread_start_time]
                    elif direction == "output":
                        all_artifacts = [a for a in all_artifacts if a.created_at and a.created_at >= thread_start_time]
        
        # Filter by kind
        if "kind" in filters and filters["kind"] is not None:
            all_artifacts = [a for a in all_artifacts if a.kind == filters["kind"]]
        
        # Filter by media_type
        if "media_type" in filters and filters["media_type"] is not None:
            all_artifacts = [a for a in all_artifacts if a.media_type == filters["media_type"]]
        
        # Filter by ref (supports prefix wildcards)
        if "ref" in filters and filters["ref"] is not None:
            ref_pattern = filters["ref"]
            all_artifacts = [a for a in all_artifacts if matches_ref_pattern(a.ref, ref_pattern)]
        
        # Apply limit
        limit = filters.get("limit")
        if limit is not None:
            all_artifacts = all_artifacts[:limit]
        
        return all_artifacts

    async def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        """Get an artifact by ID.
        
        Args:
            artifact_id: Artifact identifier
            
        Returns:
            Artifact instance if found, None otherwise
        """
        return await self.database.get_artifact(artifact_id)

    async def delete_artifact(self, artifact_id: str) -> None:
        """Delete an artifact and its associated file.
        
        Args:
            artifact_id: Artifact identifier
            
        Raises:
            ValueError: If artifact not found
        """
        # Get artifact to check for file_ref
        artifact = await self.database.get_artifact(artifact_id)
        
        if not artifact:
            raise ValueError(f"Artifact {artifact_id} not found")
        
        # Delete associated file if file_ref exists
        file_deleted = False
        file_deletion_error = None
        
        if artifact.file_ref and self.file_storage:
            try:
                await self.file_storage.delete(artifact.file_ref)
                file_deleted = True
            except Exception as e:
                file_deletion_error = str(e)
                # Artifact deletion still succeeds even if file deletion fails
                logger.warning(
                    "artifact.file_deletion_failed",
                    artifact_id=artifact_id,
                    file_ref=artifact.file_ref,
                    error=str(e),
                )
        
        # Delete artifact from database
        await self.database.delete_artifact(artifact_id)
        
        # Increment metrics
        artifacts_deleted_total.inc()
        
        # Log artifact deletion
        logger.info(
            "artifact.deleted",
            artifact_id=artifact_id,
            file_deleted=file_deleted,
            file_deletion_error=file_deletion_error,
        )

    async def archive_artifact(self, artifact_id: str) -> Artifact:
        """Archive an artifact (soft delete).
        
        Args:
            artifact_id: Artifact identifier
            
        Returns:
            Archived Artifact instance
            
        Raises:
            ValueError: If artifact not found
        """
        # Get artifact
        artifact = await self.database.get_artifact(artifact_id)
        
        if not artifact:
            raise ValueError(f"Artifact {artifact_id} not found")
        
        # Check artifact state for optimistic concurrency
        # Note: Simplified - full implementation would check last modified timestamp
        
        # Set archived fields
        artifact.archived = True
        artifact.archived_at = datetime.now(timezone.utc)
        
        # Update artifact in database
        await self.database.create_artifact(artifact)  # Update by overwriting
        
        # Increment metrics
        artifacts_archived_total.inc()
        
        # Log artifact archiving
        logger.info(
            "artifact.archived",
            artifact_id=artifact_id,
        )
        
        return artifact

    async def get_download_url(self, artifact_id: str, expires_in: int = 900) -> Dict[str, Any]:
        """Get pre-signed download URL for artifact file.
        
        Args:
            artifact_id: Artifact identifier
            expires_in: URL expiration time in seconds (default: 900)
            
        Returns:
            Dictionary with download_url and expires_at
            
        Raises:
            ValueError: If artifact not found or doesn't have file_ref
        """
        artifact = await self.database.get_artifact(artifact_id)
        
        if not artifact:
            raise ValueError(f"Artifact {artifact_id} not found")
        
        if not artifact.file_ref:
            raise ValueError(f"Artifact {artifact_id} does not have a file reference")
        
        # Get signed URL from FileStorage interface
        from datetime import timedelta
        
        if self.file_storage:
            try:
                download_url = await self.file_storage.get_signed_url(artifact.file_ref, expires_in)
                expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                
                return {
                    "download_url": download_url,
                    "expires_at": expires_at.isoformat() + "Z",
                    "expires_in": expires_in,
                }
            except Exception as e:
                logger.error(
                    "artifact.download_url_generation_failed",
                    artifact_id=artifact_id,
                    file_ref=artifact.file_ref,
                    error=str(e),
                )
                raise ValueError(f"Failed to generate download URL: {str(e)}") from e
        else:
            # Fallback placeholder if FileStorage not available
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            
            return {
                "download_url": f"placeholder://file/{artifact.file_ref}",  # Placeholder
                "expires_at": expires_at.isoformat() + "Z",
                "expires_in": expires_in,
            }

    async def query_artifacts(self, filters: Dict[str, Any]) -> List[Artifact]:
        """Query artifacts across threads with filters.
        
        Args:
            filters: Filter dictionary containing:
                - ref: Optional[str] - Ref filter (supports prefix wildcards)
                - kind: Optional[str] - Artifact kind filter
                - media_type: Optional[str] - Media type filter
                - thread_id: Optional[str] - Filter by thread ID
                - app_id: Optional[str] - Filter by app_id (from thread metadata)
                - include_archived: Optional[bool] - Include archived artifacts
                - limit: Optional[int] - Maximum number of results
                - cursor: Optional[str] - Pagination cursor
                
        Returns:
            List of Artifact instances matching filters
        """
        return await self.database.query_artifacts(filters)

    async def validate_artifact_reference(
        self,
        artifact_id: str,
        user_id: Optional[str] = None,
        app_id: Optional[str] = None,
        is_admin: bool = False,
    ) -> Artifact:
        """Validate that an artifact reference exists and is accessible.
        
        Args:
            artifact_id: Artifact ID to validate
            user_id: User identifier for access control (optional)
            app_id: Application identifier for access control (optional)
            is_admin: Whether request is from admin API key
            
        Returns:
            Artifact instance if found and accessible
            
        Raises:
            ValueError: If artifact not found or not accessible
        """
        artifact = await self.get_artifact(artifact_id)
        
        if not artifact:
            raise ValueError(f"Artifact {artifact_id} not found")
        
        # Apply access control filtering (unless admin)
        if not is_admin and artifact.thread_id:
            # Get thread to check access control
            thread = await self.database.get_thread(artifact.thread_id)
            if thread:
                thread_user_id = thread.metadata.get("user_id")
                thread_app_id = thread.metadata.get("app_id")
                
                if user_id and thread_user_id != user_id:
                    raise ValueError(f"Artifact {artifact_id} not accessible")
                if app_id and thread_app_id != app_id:
                    raise ValueError(f"Artifact {artifact_id} not accessible")
        
        return artifact

    def is_artifact_reference(self, artifact: Artifact) -> bool:
        """Check if an artifact is a reference (has ID but minimal other data).
        
        Args:
            artifact: Artifact instance to check
            
        Returns:
            True if artifact appears to be a reference (ID provided but minimal data)
        """
        # If artifact has an ID and is missing most required fields for its kind,
        # it's likely a reference
        if not artifact.id or artifact.id == "":
            return False
        
        # Check if artifact has minimal data (just ID and kind, maybe ref)
        # If it has substantial content (text, value, file_ref, url), it's not a reference
        has_content = (
            artifact.text is not None and artifact.text != "" or
            artifact.value is not None or
            artifact.file_ref is not None or
            artifact.url is not None
        )
        
        # If it has content, it's not a reference
        return not has_content

