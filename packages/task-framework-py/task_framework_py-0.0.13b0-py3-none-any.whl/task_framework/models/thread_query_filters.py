"""ThreadQueryFilters model for GET /threads query parameters."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from task_framework.thread_state import ThreadState


class ThreadQueryFilters(BaseModel):
    """Query parameters for filtering threads in GET /threads endpoint."""

    state: Optional[ThreadState] = Field(None, description="Filter by thread state")
    name: Optional[str] = Field(None, description="Filter by thread name (exact match or prefix with * suffix)")
    user_id: Optional[str] = Field(None, description="Filter by user_id metadata")
    app_id: Optional[str] = Field(None, description="Filter by app_id metadata")
    schedule_id: Optional[str] = Field(None, description="Filter by schedule_id")
    run_id: Optional[str] = Field(None, description="Filter by run_id")
    task_id: Optional[str] = Field(None, description="Filter by task_id metadata")
    task_version: Optional[str] = Field(None, description="Filter by task_version metadata")
    created_after: Optional[datetime] = Field(None, description="Filter threads created after this time (ISO 8601 UTC format)")
    created_before: Optional[datetime] = Field(None, description="Filter threads created before this time (ISO 8601 UTC format)")
    started_after: Optional[datetime] = Field(None, description="Filter threads started after this time (ISO 8601 UTC format)")
    finished_before: Optional[datetime] = Field(None, description="Filter threads finished before this time (ISO 8601 UTC format)")
    limit: Optional[int] = Field(default=50, description="Maximum number of results (default: 50, maximum: 1000)")
    cursor: Optional[str] = Field(None, description="Cursor for pagination (Base64-encoded JSON)")
    offset: Optional[int] = Field(None, description="Offset for pagination fallback (must be >= 0)")

    @field_validator("limit")
    @classmethod
    def validate_limit(cls, v: Optional[int]) -> int:
        """Validate limit is between 1 and 1000."""
        if v is None:
            return 50
        if v < 1 or v > 1000:
            raise ValueError("limit must be between 1 and 1000")
        return v

    @field_validator("offset")
    @classmethod
    def validate_offset(cls, v: Optional[int]) -> Optional[int]:
        """Validate offset is >= 0 if provided."""
        if v is not None and v < 0:
            raise ValueError("offset must be >= 0")
        return v

    @field_validator("created_after", "created_before", "started_after", "finished_before")
    @classmethod
    def validate_time_ranges(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """Validate time range filters are valid (after < before if both provided)."""
        field_name = info.field_name
        if field_name == "created_after" and v is not None:
            created_before = info.data.get("created_before")
            if created_before is not None and v >= created_before:
                raise ValueError("created_after must be before created_before")
        elif field_name == "created_before" and v is not None:
            created_after = info.data.get("created_after")
            if created_after is not None and v <= created_after:
                raise ValueError("created_before must be after created_after")
        elif field_name == "started_after" and v is not None:
            finished_before = info.data.get("finished_before")
            if finished_before is not None and v >= finished_before:
                raise ValueError("started_after must be before finished_before")
        elif field_name == "finished_before" and v is not None:
            started_after = info.data.get("started_after")
            if started_after is not None and v <= started_after:
                raise ValueError("finished_before must be after started_after")
        return v

    model_config = {"use_enum_values": True}

