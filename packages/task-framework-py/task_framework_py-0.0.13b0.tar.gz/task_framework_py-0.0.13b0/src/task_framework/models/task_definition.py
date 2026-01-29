"""TaskDefinition model for multi-task server architecture."""

from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field, computed_field


class TaskMetadata(BaseModel):
    """Metadata from task_metadata.json in the task definition package."""
    
    name: str = Field(..., description="Task name identifier")
    version: str = Field(..., description="Task version (semver format)")
    description: str = Field(default="", description="Human-readable description of what the task does")
    entry_point: str = Field(..., description="Entry point in format 'module:function_name'")
    input_schemas: List[Dict[str, Any]] = Field(default_factory=list, description="Input artifact schemas")
    output_schemas: List[Dict[str, Any]] = Field(default_factory=list, description="Output artifact schemas")
    
    # SDK version used when packaging this task
    sdk_version: Optional[str] = Field(default=None, description="task-framework-py SDK version used to package this task")
    
    # Configuration requirements (unified - no env/secret distinction)
    requirements: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="Configuration requirements (keys needed by the task)"
    )


class TaskDefinition(BaseModel):
    """A registered task definition with execution environment.
    
    Represents a deployed task with its own:
    - Code directory
    - Virtual environment
    
    Note: Database and file storage are now managed at the framework level,
    not per-task. Tasks share the same storage.
    """
    
    task_id: str = Field(..., description="Unique task identifier")
    version: str = Field(..., description="Task version (semver format)")
    
    # Metadata from task_metadata.json
    name: str = Field(..., description="Task display name")
    description: str = Field(default="", description="Task description")
    entry_point: str = Field(..., description="Entry point in format 'module:function_name'")
    
    # Schema definitions
    input_schemas: List[Dict[str, Any]] = Field(default_factory=list, description="Input artifact schemas")
    output_schemas: List[Dict[str, Any]] = Field(default_factory=list, description="Output artifact schemas")
    
    # Configuration requirements (unified)
    requirements: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="Configuration requirements declared in task.yaml"
    )
    
    # SDK version used when packaging this task
    sdk_version: Optional[str] = Field(default=None, description="task-framework-py SDK version used to package this task")
    
    # Isolated paths
    base_path: str = Field(..., description="Base path for this task version: {server_base}/tasks/{task_id}/{version}/")
    code_path: str = Field(..., description="Path to extracted task code: {base_path}/code/")
    venv_path: str = Field(..., description="Path to virtual environment: {base_path}/venv/")
    data_path: str = Field(..., description="Path to isolated database: {base_path}/data/")
    storage_path: str = Field(..., description="Path to isolated file storage: {base_path}/storage/")
    
    # Deployment info
    zip_path: Optional[str] = Field(None, description="Original zip file path")
    zip_hash: Optional[str] = Field(None, description="SHA-256 hash of the zip file")
    deployed_at: Optional[datetime] = Field(None, description="Deployment timestamp")
    
    # Runtime reference (not persisted)
    _task_function: Optional[Callable] = None
    
    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True
    
    @computed_field
    @property
    def full_id(self) -> str:
        """Full task identifier including version.
        
        Returns:
            String in format '{task_id}:{version}'
        """
        return f"{self.task_id}:{self.version}"
    
    def set_task_function(self, func: Callable) -> None:
        """Set the task function reference.
        
        Args:
            func: The task function callable
        """
        object.__setattr__(self, "_task_function", func)
    
    def get_task_function(self) -> Optional[Callable]:
        """Get the task function reference.
        
        Returns:
            The task function callable or None if not set
        """
        return self._task_function
    
    # Note: Database and file storage methods removed.
    # All storage is now managed at the framework level.
    
    @classmethod
    def from_metadata(
        cls,
        metadata: TaskMetadata,
        base_path: Path,
        zip_path: Optional[str] = None,
        zip_hash: Optional[str] = None,
        deployed_at: Optional[datetime] = None,
    ) -> "TaskDefinition":
        """Create TaskDefinition from TaskMetadata and base path.
        
        Args:
            metadata: TaskMetadata parsed from task_metadata.json
            base_path: Base path for this task version
            zip_path: Original zip file path
            zip_hash: SHA-256 hash of the zip file
            deployed_at: Optional deployment timestamp (defaults to now if not provided)
            
        Returns:
            TaskDefinition instance with computed paths
        """
        base_path = Path(base_path)
        return cls(
            task_id=metadata.name,
            version=metadata.version,
            name=metadata.name,
            description=metadata.description,
            entry_point=metadata.entry_point,
            input_schemas=metadata.input_schemas,
            output_schemas=metadata.output_schemas,
            requirements=metadata.requirements,
            sdk_version=metadata.sdk_version,
            base_path=str(base_path),
            code_path=str(base_path / "code"),
            venv_path=str(base_path / "venv"),
            data_path=str(base_path / "data"),
            storage_path=str(base_path / "storage"),
            zip_path=zip_path,
            zip_hash=zip_hash,
            deployed_at=deployed_at if deployed_at else datetime.now(),
        )


class DeploymentRecord(BaseModel):
    """Record of a deployed task definition for idempotency tracking."""
    
    zip_path: str = Field(..., description="Full path to the zip file")
    zip_hash: Optional[str] = Field(None, description="SHA-256 hash of the zip file")
    task_id: str = Field(..., description="Deployed task identifier")
    version: str = Field(..., description="Deployed task version")
    deployed_at: datetime = Field(..., description="Deployment timestamp")
    status: str = Field(..., description="Deployment status: 'deployed', 'failed', 'pending'")
    error: Optional[str] = Field(None, description="Error message if status is 'failed'")
    
    @property
    def is_deployed(self) -> bool:
        """Check if deployment was successful.
        
        Returns:
            True if status is 'deployed'
        """
        return self.status == "deployed"
    
    @property
    def is_failed(self) -> bool:
        """Check if deployment failed.
        
        Returns:
            True if status is 'failed'
        """
        return self.status == "failed"

