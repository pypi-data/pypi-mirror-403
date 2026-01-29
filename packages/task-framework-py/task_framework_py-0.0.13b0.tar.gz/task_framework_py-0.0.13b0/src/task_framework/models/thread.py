"""Thread model class with Pydantic validation."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, computed_field, ConfigDict, Field

from task_framework.models.artifact import Artifact
from task_framework.models.thread_error import ThreadError
from task_framework.thread_state import ThreadState


class Thread(BaseModel):
    """Thread execution unit representing a single attempt to run the task function."""

    id: str = Field(..., description="Unique thread identifier")
    name: Optional[str] = Field(None, description="Optional thread name for display and grouping")
    state: ThreadState = Field(..., description="Current execution state")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Thread metadata")
    params: Dict[str, Any] = Field(default_factory=dict, description="Task-specific parameters")
    error: Optional[ThreadError] = Field(None, description="Error details if state is failed")
    inputs: List[Artifact] = Field(default_factory=list, description="Input artifacts provided at thread creation")
    outputs: List[Artifact] = Field(default_factory=list, description="Output artifacts published during execution")
    created_at: datetime = Field(..., description="Thread creation timestamp (UTC)")
    started_at: Optional[datetime] = Field(None, description="Execution start timestamp (UTC)")
    finished_at: Optional[datetime] = Field(None, description="Execution completion timestamp (UTC)")
    schedule_id: Optional[str] = Field(None, description="Associated schedule ID (if scheduled)")
    run_id: Optional[str] = Field(None, description="Associated run ID (if scheduled)")
    attempt: Optional[int] = Field(None, description="Attempt number (if retry)")

    model_config = ConfigDict(use_enum_values=True)

    @computed_field
    @property
    def artifacts(self) -> List[Artifact]:
        """All artifacts (inputs and outputs combined) for backward compatibility.
        
        Returns:
            Combined list of input and output artifacts
        """
        return self.inputs + self.outputs

