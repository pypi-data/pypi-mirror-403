"""TaskContext class providing framework functionality to task functions."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict

from task_framework.models.artifact import Artifact

if TYPE_CHECKING:
    from task_framework.framework import TaskFramework


class TaskContext(BaseModel):
    """Context object provided to task functions for accessing framework functionality."""

    thread_id: str
    metadata: Dict[str, Any]
    params: Dict[str, Any]
    _cancelled: bool = False
    _framework: Optional["TaskFramework"] = None
    _task_definition: Optional[Any] = None  # TaskDefinition in multi-task mode
    _completed: bool = False
    
    # Configuration (injected at execution time)
    _env_vars: Dict[str, str] = {}
    _secrets: Dict[str, str] = {}

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(
        self,
        thread_id: str,
        metadata: Dict[str, Any],
        params: Dict[str, Any] = None,
        framework: Optional["TaskFramework"] = None,
        task_definition: Optional[Any] = None,
        env_vars: Optional[Dict[str, str]] = None,
        secrets: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize TaskContext.

        Args:
            thread_id: Current thread identifier
            metadata: Thread metadata (user_id, app_id, custom fields)
            params: Task-specific parameters
            framework: Reference to framework instance
            task_definition: Optional TaskDefinition (for multi-task mode)
            env_vars: Environment variables for this task execution
            secrets: Secrets for this task execution
            **kwargs: Additional keyword arguments
        """
        super().__init__(
            thread_id=thread_id,
            metadata=metadata or {},
            params=params or {},
            _cancelled=False,
            _framework=framework,
            _task_definition=task_definition,
            _completed=False,
            _env_vars=env_vars or {},
            _secrets=secrets or {},
            **kwargs,
        )
        # Explicitly set private attributes since Pydantic may not handle them correctly
        if framework is not None:
            object.__setattr__(self, "_framework", framework)
        if task_definition is not None:
            object.__setattr__(self, "_task_definition", task_definition)
        if env_vars is not None:
            object.__setattr__(self, "_env_vars", env_vars)
        if secrets is not None:
            object.__setattr__(self, "_secrets", secrets)

    def get_thread_id(self) -> str:
        """Get current thread identifier.

        Returns:
            Thread identifier
        """
        return self.thread_id

    def get_metadata(self) -> Dict[str, Any]:
        """Get thread metadata.

        Returns:
            Thread metadata dictionary
        """
        return self.metadata

    def get_params(self) -> Dict[str, Any]:
        """Get task-specific parameters.

        Returns:
            Task parameters dictionary
        """
        return self.params

    def is_cancelled(self) -> bool:
        """Check if thread has been cancelled.

        Returns:
            True if thread has been cancelled, False otherwise
        """
        return self._cancelled
    
    def get(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get a configuration value (unified method for env vars and secrets).
        
        Checks both env_vars and secrets. Secrets take precedence.
        
        Args:
            name: Configuration key name
            default: Default value if not found
            
        Returns:
            Configuration value or default
        """
        # Check secrets first (higher priority)
        if name in self._secrets:
            return self._secrets[name]
        # Then env vars
        if name in self._env_vars:
            return self._env_vars[name]
        return default
    
    def get_env(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get an environment variable value.
        
        DEPRECATED: Use get() instead for unified access.
        
        Args:
            name: Environment variable name
            default: Default value if not set
            
        Returns:
            Environment variable value or default
        """
        return self._env_vars.get(name, default)
    
    def get_secret(self, name: str, default: Optional[str] = None) -> str:
        """Get a secret value.
        
        DEPRECATED: Use get() instead for unified access.
        
        Args:
            name: Secret name (as declared in task.yaml requirements)
            default: Default value if not set. If None, raises KeyError for missing secret.
            
        Returns:
            Secret value or default
            
        Raises:
            KeyError: If secret is not found and no default is provided
        """
        if name not in self._secrets:
            if default is not None:
                return default
            raise KeyError(
                f"Secret '{name}' not found. Ensure it is declared in task.yaml "
                f"requirements and configured via Admin API."
            )
        return self._secrets[name]
    
    def has(self, name: str) -> bool:
        """Check if a configuration value is available.
        
        Args:
            name: Configuration key name
            
        Returns:
            True if value is available (in either env_vars or secrets)
        """
        return name in self._secrets or name in self._env_vars
    
    def has_secret(self, name: str) -> bool:
        """Check if a secret is available.
        
        DEPRECATED: Use has() instead for unified access.
        
        Args:
            name: Secret name
            
        Returns:
            True if secret is available
        """
        return name in self._secrets
    
    def get_all_env(self) -> Dict[str, str]:
        """Get all environment variables.
        
        Returns:
            Copy of all environment variables
        """
        return dict(self._env_vars)

    async def get_input_artifacts(self) -> List[Artifact]:
        """Get input artifacts for current thread.

        Returns:
            List of input artifacts
        """
        if not self._framework or not self._framework.database:
            return []
        
        # Get all artifacts for thread from framework database
        artifacts = await self._framework.database.get_thread_artifacts(self.thread_id)
        
        # Return only input artifacts (created before thread started)
        # Note: This logic is handled in ThreadService.get_thread() for API responses
        # For task context, we return all artifacts associated with the thread
        return artifacts

    async def publish_output_artifacts(self, artifacts: List[Artifact]) -> None:
        """Publish output artifacts for current thread.

        Args:
            artifacts: List of artifacts to publish
            
        Raises:
            ArtifactValidationError: If output schema validation fails
        """
        if not self._framework:
            raise RuntimeError("Framework not available")
        
        from task_framework.services.artifact_service import ArtifactService
        from task_framework.utils.artifact_validation import ArtifactValidationError
        from task_framework.models.artifact_schema import validate_artifact_against_schemas
        from task_framework.logging import logger
        
        # Use framework database and file storage (all storage is at framework level)
        database = self._framework.database
        file_storage = self._framework.file_storage
        
        if not database:
            raise RuntimeError("Database not available")
        
        artifact_service = ArtifactService(
            database=database,
            file_storage=file_storage,
        )
        
        # Get output schemas if defined
        # In multi-task mode, use TaskDefinition's output_schemas
        # In single-task mode, use framework's output_schemas
        output_schemas = None
        if self._task_definition and hasattr(self._task_definition, "output_schemas"):
            # Multi-task mode: use TaskDefinition's output_schemas
            output_schemas_raw = self._task_definition.output_schemas or []
            if output_schemas_raw:
                from task_framework.models.artifact_schema import ArtifactSchema
                output_schemas = [
                    ArtifactSchema.model_validate(s) if isinstance(s, dict) else s
                    for s in output_schemas_raw
                ]
        
        if not output_schemas:
            # Fallback to framework output_schemas (single-task mode or no task definition)
            output_schemas = getattr(self._framework, "output_schemas", None)
            if not output_schemas:
                # Fallback to singular for backward compatibility
                output_schema_singular = getattr(self._framework, "output_schema", None)
                output_schemas = [output_schema_singular] if output_schema_singular is not None else []
        
        # Set thread_id and created_at for all artifacts
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        
        for artifact in artifacts:
            artifact.thread_id = self.thread_id
            artifact.direction = "output"  # Mark as output artifact
            if not artifact.created_at:
                artifact.created_at = now
            
            try:
                # Validate against output schemas if defined
                if output_schemas:
                    # Convert artifact to dict for schema validation
                    art_dict = artifact.model_dump() if hasattr(artifact, "model_dump") else dict(artifact)
                    
                    # For JSON artifacts with json_schema, validation happens on artifact.value
                    # For other cases, validate at artifact level
                    try:
                        validate_artifact_against_schemas(art_dict, output_schemas)
                    except ValueError as schema_error:
                        # Convert ValueError to ArtifactValidationError
                        raise ArtifactValidationError(
                            f"Output artifact validation failed: {str(schema_error)}",
                            [{"field": "artifact", "message": str(schema_error)}],
                        )
                
                # Validate and create artifact (this does basic artifact structure validation)
                await artifact_service.create_artifact(artifact)
                
                # Log artifact creation
                logger.info(
                    "artifact.created",
                    artifact_id=artifact.id,
                    kind=artifact.kind,
                    thread_id=self.thread_id,
                    ref=artifact.ref,
                )
            except ArtifactValidationError as e:
                # Log validation failure
                logger.error(
                    "artifact.validation.failed",
                    thread_id=self.thread_id,
                    error=str(e),
                    artifact_kind=artifact.kind,
                    validation_errors=e.errors,
                )
                raise

    async def signal_problem(self, error: Exception | str, details: Optional[Dict[str, Any]] = None) -> None:
        """Signal a problem or error during task execution.

        Args:
            error: Exception or error message string
            details: Optional additional error context
        """
        # TODO: Implement error signaling
        pass

