"""Schedule and Run models for cron-based scheduling."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from task_framework.models.artifact import Artifact
from task_framework.models.pagination import Pagination
from task_framework.models.thread_create_request import AdHocWebhook


class ScheduleState(str, Enum):
    """Schedule state enumeration."""

    ACTIVE = "active"
    PAUSED = "paused"
    CANCELED = "canceled"


class RunState(str, Enum):
    """Run state enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    STOPPED = "stopped"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


class ConcurrencyPolicy(str, Enum):
    """Concurrency policy enumeration."""

    FORBID = "forbid"
    REPLACE = "replace"
    ALLOW = "allow"


class Schedule(BaseModel):
    """Schedule model representing a cron-based schedule configuration."""

    id: str = Field(..., description="Unique schedule identifier")
    cron: str = Field(..., description="Cron expression (5-field standard)")
    timezone: str = Field(..., description="IANA timezone identifier")
    state: ScheduleState = Field(..., description="Current schedule state")
    task_id: Optional[str] = Field(None, description="Associated task definition ID")
    task_version: Optional[str] = Field(None, description="Associated task version")
    inputs_template: List[Artifact] = Field(
        default_factory=list, description="Template artifacts for each run"
    )
    params: Dict[str, Any] = Field(
        default_factory=dict, description="Task-specific parameters"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Schedule metadata"
    )
    webhooks: Optional[List[AdHocWebhook]] = Field(
        default=None, description="Webhooks configured for scheduled threads"
    )
    concurrency_policy: ConcurrencyPolicy = Field(
        default=ConcurrencyPolicy.ALLOW, description="Concurrency handling policy"
    )
    max_attempts: int = Field(
        default=1, ge=1, description="Maximum retry attempts per run"
    )
    created_at: datetime = Field(..., description="Creation timestamp (UTC)")
    updated_at: datetime = Field(..., description="Last update timestamp (UTC)")

    model_config = {"use_enum_values": True}

    @field_validator("cron")
    @classmethod
    def validate_cron(cls, v: str) -> str:
        """Validate cron expression is valid 5-field format."""
        from apscheduler.triggers.cron import CronTrigger

        try:
            # Validate cron expression using APScheduler
            CronTrigger.from_crontab(v)
        except Exception as e:
            raise ValueError(f"Invalid cron expression: {v}") from e
        return v

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        """Validate timezone is valid IANA timezone identifier."""
        try:
            from zoneinfo import ZoneInfo

            ZoneInfo(v)
        except Exception as e:
            raise ValueError(f"Invalid timezone identifier: {v}") from e
        return v


class Run(BaseModel):
    """Run model representing a scheduled occurrence of a task execution."""

    schedule_id: str = Field(..., description="Associated schedule identifier")
    run_id: str = Field(..., description="Deterministic run identifier")
    scheduled_for_local: datetime = Field(
        ..., description="Scheduled time in schedule timezone"
    )
    scheduled_for_utc: datetime = Field(..., description="Scheduled time in UTC")
    state: RunState = Field(..., description="Current run state")
    attempt: int = Field(..., ge=1, description="Current attempt number (starts at 1)")
    max_attempts: int = Field(..., ge=1, description="Maximum retry attempts")
    threads: List[str] = Field(
        default_factory=list, description="Thread IDs belonging to this run"
    )
    metrics: Optional[Dict[str, Any]] = Field(
        None, description="Run execution metrics"
    )
    labels: Dict[str, Any] = Field(
        default_factory=dict, description="Run labels"
    )
    created_at: datetime = Field(..., description="Creation timestamp (UTC)")
    started_at: Optional[datetime] = Field(
        None, description="Execution start timestamp (UTC)"
    )
    finished_at: Optional[datetime] = Field(
        None, description="Completion timestamp (UTC)"
    )

    model_config = {"use_enum_values": True}

    @field_validator("run_id")
    @classmethod
    def validate_run_id_format(cls, v: str, info) -> str:
        """Validate run_id format matches specification."""
        schedule_id = info.data.get("schedule_id")
        if schedule_id and not v.startswith(f"{schedule_id}_run_"):
            raise ValueError(
                f"run_id must start with schedule_id prefix: {schedule_id}_run_"
            )
        # Validate ISO 8601 timestamp format
        import re

        pattern = r"^\w+_run_\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$"
        if not re.match(pattern, v):
            raise ValueError(
                "run_id must match format: {schedule_id}_run_{YYYY-MM-DDTHH:MM:SS.ffffffZ}"
            )
        return v

    @model_validator(mode="after")
    def validate_datetime_consistency(self) -> "Run":
        """Validate that scheduled_for_utc and scheduled_for_local represent the same instant."""
        # Convert scheduled_for_local to UTC for accurate comparison with scheduled_for_utc
        try:
            from datetime import timezone as _tz

            utc_local = self.scheduled_for_local.astimezone(_tz.utc).replace(tzinfo=None)
            utc_utc = self.scheduled_for_utc.astimezone(_tz.utc).replace(tzinfo=None)
        except Exception:
            # Fallback to naive comparison if timezone conversion fails
            utc_local = self.scheduled_for_local.replace(tzinfo=None)
            utc_utc = self.scheduled_for_utc.replace(tzinfo=None)

        # Allow small tolerance for floating point precision (1 second)
        if abs((utc_local - utc_utc).total_seconds()) > 1:
            raise ValueError("scheduled_for_utc and scheduled_for_local must represent the same instant")
        return self


class ScheduleCreateRequest(BaseModel):
    """Request model for creating a schedule."""

    cron: str = Field(..., description="Cron expression (5-field standard)")
    timezone: str = Field(..., description="IANA timezone identifier")
    task_id: Optional[str] = Field(None, description="Associated task definition ID")
    task_version: Optional[str] = Field(None, description="Associated task version")
    state: ScheduleState = Field(
        default=ScheduleState.ACTIVE, description="Initial schedule state"
    )
    inputs_template: List[Artifact] = Field(
        default_factory=list, description="Template artifacts for each run"
    )
    params: Dict[str, Any] = Field(
        default_factory=dict, description="Task-specific parameters"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Schedule metadata"
    )
    webhooks: Optional[List[AdHocWebhook]] = Field(
        default=None, description="Webhooks configured for scheduled threads"
    )
    concurrency_policy: ConcurrencyPolicy = Field(
        default=ConcurrencyPolicy.ALLOW, description="Concurrency handling policy"
    )
    max_attempts: int = Field(
        default=1, ge=1, description="Maximum retry attempts per run"
    )


class ScheduleUpdateRequest(BaseModel):
    """Request model for updating a schedule."""

    cron: Optional[str] = Field(None, description="Cron expression (5-field standard)")
    timezone: Optional[str] = Field(None, description="IANA timezone identifier")
    task_id: Optional[str] = Field(None, description="Associated task definition ID")
    task_version: Optional[str] = Field(None, description="Associated task version")
    state: Optional[ScheduleState] = Field(None, description="Schedule state")
    inputs_template: Optional[List[Artifact]] = Field(
        None, description="Template artifacts for each run"
    )
    params: Optional[Dict[str, Any]] = Field(
        None, description="Task-specific parameters"
    )
    metadata: Optional[Dict[str, Any]] = Field(None, description="Schedule metadata")
    webhooks: Optional[List[AdHocWebhook]] = Field(
        None, description="Webhooks configured for scheduled threads"
    )
    concurrency_policy: Optional[ConcurrencyPolicy] = Field(
        None, description="Concurrency handling policy"
    )
    max_attempts: Optional[int] = Field(
        None, ge=1, description="Maximum retry attempts per run"
    )


class ScheduleListResponse(BaseModel):
    """Paginated response for schedule list."""

    items: List[Schedule] = Field(..., description="Array of schedule objects")
    pagination: Pagination = Field(..., description="Pagination metadata")


class RunListResponse(BaseModel):
    """Paginated response for run list."""

    items: List[Run] = Field(..., description="Array of run objects")
    pagination: Pagination = Field(..., description="Pagination metadata")

