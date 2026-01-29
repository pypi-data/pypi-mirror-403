"""Webhook models for webhook system."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from task_framework.models.pagination import Pagination
from task_framework.models.webhook_scoping import WebhookScope


class ArtifactSelector(BaseModel):
    """Pattern-based artifact selection filter."""

    ref: str = Field(..., description="Artifact reference pattern (e.g., 'result:*', 'input:data.json')")

    @field_validator("ref")
    @classmethod
    def validate_ref_pattern(cls, v: str) -> str:
        """Validate ref pattern is non-empty."""
        if not v or not v.strip():
            raise ValueError("ref pattern must be non-empty")
        return v.strip()


class EventFilters(BaseModel):
    """Event filtering configuration for webhooks."""

    include: Optional[List[str]] = Field(None, description="Event types to include")
    exclude: Optional[List[str]] = Field(None, description="Event types to exclude")

    @model_validator(mode="after")
    def validate_mutually_exclusive(self) -> "EventFilters":
        """Validate include and exclude are mutually exclusive."""
        if self.include and self.exclude:
            raise ValueError("Cannot specify both include and exclude event filters")
        return self

    @field_validator("include", "exclude")
    @classmethod
    def validate_event_types(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate event types are non-empty strings."""
        if v is None:
            return v
        if not isinstance(v, list):
            raise ValueError("Event filters must be lists")
        if not v:
            raise ValueError("Event filter lists cannot be empty")
        for event_type in v:
            if not isinstance(event_type, str) or not event_type.strip():
                raise ValueError("Event types must be non-empty strings")
        return v


class DataFilters(BaseModel):
    """Data filtering configuration for webhook payloads."""

    detail: Optional[str] = Field(
        default="inline_small",
        description="Detail level: 'none' | 'inline_small' | 'inline_all'",
    )
    artifact_selectors: Optional[List[ArtifactSelector]] = Field(
        None, description="Artifact selection filters"
    )
    include_download_urls: bool = Field(default=False, description="Include download URLs for file artifacts")
    include_logs: bool = Field(default=False, description="Include execution logs")
    include_metrics: bool = Field(default=False, description="Include execution metrics")

    @field_validator("detail")
    @classmethod
    def validate_detail_level(cls, v: Optional[str]) -> Optional[str]:
        """Validate detail level is one of allowed values."""
        if v is None:
            return "inline_small"
        allowed = {"none", "inline_small", "inline_all"}
        if v not in allowed:
            raise ValueError(f"detail must be one of: {', '.join(allowed)}")
        return v


class Webhook(BaseModel):
    """Webhook subscription configuration."""

    id: str = Field(..., description="Unique webhook identifier")
    url: str = Field(..., description="Webhook delivery URL")
    secret: str = Field(..., description="HMAC secret for signature generation")
    enabled: bool = Field(default=True, description="Whether webhook is active")
    events: Optional[EventFilters] = Field(None, description="Event filtering configuration")
    data_filters: Optional[DataFilters] = Field(None, description="Data filtering configuration")
    scope: Optional[WebhookScope] = Field(None, description="Webhook scoping configuration")
    timeout_seconds: int = Field(default=10, description="Delivery timeout in seconds")
    api_key: Optional[str] = Field(None, description="Optional X-API-Key header for webhook delivery requests")
    task_id: Optional[str] = Field(None, description="Task identifier for task-specific webhooks")
    task_version: Optional[str] = Field(None, description="Task version for task-specific webhooks")
    source: Optional[str] = Field(
        default="manual",
        description="Webhook source: 'manual' (API created), 'thread' (ad-hoc per thread), 'schedule' (schedule webhook)"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = Field(None, description="User/app identifier that created webhook")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        if not v or not v.strip():
            raise ValueError("url must be non-empty")
        # Basic URL validation - allow HTTP/HTTPS
        if not v.startswith(("http://", "https://")):
            raise ValueError("url must start with http:// or https://")
        return v.strip()

    @field_validator("timeout_seconds")
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        """Validate timeout is within valid range."""
        if v < 1 or v > 60:
            raise ValueError("timeout_seconds must be between 1 and 60")
        return v

    @field_validator("secret")
    @classmethod
    def validate_secret(cls, v: str) -> str:
        """Validate secret is non-empty."""
        if not v or not v.strip():
            raise ValueError("secret must be non-empty")
        return v


class WebhookCreateRequest(BaseModel):
    """Request payload for creating webhooks."""

    url: str = Field(..., description="Webhook delivery URL")
    events: Optional[EventFilters] = Field(None, description="Event filtering")
    data_filters: Optional[DataFilters] = Field(None, description="Data filtering")
    scope: Optional[WebhookScope] = Field(None, description="Webhook scoping")
    timeout_seconds: Optional[int] = Field(default=10, description="Delivery timeout in seconds")
    enabled: bool = Field(default=True, description="Whether webhook is enabled")
    api_key: Optional[str] = Field(None, description="Optional X-API-Key header for webhook delivery requests")
    task_id: Optional[str] = Field(None, description="Task identifier for task-specific webhooks")
    task_version: Optional[str] = Field(None, description="Task version for task-specific webhooks")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        if not v or not v.strip():
            raise ValueError("url must be non-empty")
        if not v.startswith(("http://", "https://")):
            raise ValueError("url must start with http:// or https://")
        return v.strip()

    @field_validator("timeout_seconds")
    @classmethod
    def validate_timeout(cls, v: Optional[int]) -> Optional[int]:
        """Validate timeout is within valid range."""
        if v is not None and (v < 1 or v > 60):
            raise ValueError("timeout_seconds must be between 1 and 60")
        return v


class WebhookUpdateRequest(BaseModel):
    """Request payload for updating webhooks (partial update)."""

    url: Optional[str] = Field(None, description="Webhook delivery URL")
    events: Optional[EventFilters] = Field(None, description="Event filtering")
    data_filters: Optional[DataFilters] = Field(None, description="Data filtering")
    scope: Optional[WebhookScope] = Field(None, description="Webhook scoping")
    timeout_seconds: Optional[int] = Field(None, description="Delivery timeout in seconds")
    api_key: Optional[str] = Field(None, description="Optional X-API-Key header for webhook delivery requests")
    enabled: Optional[bool] = Field(None, description="Whether webhook is enabled")
    task_id: Optional[str] = Field(None, description="Task identifier for task-specific webhooks")
    task_version: Optional[str] = Field(None, description="Task version for task-specific webhooks")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate URL format if provided."""
        if v is None:
            return v
        if not v.strip():
            raise ValueError("url must be non-empty")
        if not v.startswith(("http://", "https://")):
            raise ValueError("url must start with http:// or https://")
        return v.strip()

    @field_validator("timeout_seconds")
    @classmethod
    def validate_timeout(cls, v: Optional[int]) -> Optional[int]:
        """Validate timeout is within valid range if provided."""
        if v is not None and (v < 1 or v > 60):
            raise ValueError("timeout_seconds must be between 1 and 60")
        return v


class WebhookListResponse(BaseModel):
    """Paginated response for webhook list."""

    items: List[Webhook] = Field(..., description="Array of webhook objects")
    pagination: Pagination = Field(..., description="Pagination metadata")


class WebhookDelivery(BaseModel):
    """Webhook delivery audit log record."""

    id: str = Field(..., description="Unique delivery identifier")
    webhook_id: str = Field(..., description="Associated webhook ID")
    event_type: str = Field(..., description="Event type that triggered delivery")
    event_payload: Dict[str, Any] = Field(..., description="Event payload data (JSON)")
    thread_id: Optional[str] = Field(None, description="Associated thread ID")
    run_id: Optional[str] = Field(None, description="Associated run ID")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = Field(..., description="Delivery status: 'success' | 'failed'")
    status_code: Optional[int] = Field(None, description="HTTP status code from subscriber")
    response_time_ms: Optional[int] = Field(None, description="Response time in milliseconds")
    error: Optional[str] = Field(None, description="Error message (if failed)")
    delivery_url: str = Field(..., description="URL that was called")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status is one of allowed values."""
        allowed = {"success", "failed"}
        if v not in allowed:
            raise ValueError(f"status must be one of: {', '.join(allowed)}")
        return v

    @field_validator("status_code")
    @classmethod
    def validate_status_code(cls, v: Optional[int]) -> Optional[int]:
        """Validate status code is valid HTTP status if provided."""
        if v is not None and (v < 100 or v > 599):
            raise ValueError("status_code must be a valid HTTP status code (100-599)")
        return v

    @field_validator("response_time_ms")
    @classmethod
    def validate_response_time(cls, v: Optional[int]) -> Optional[int]:
        """Validate response time is non-negative if provided."""
        if v is not None and v < 0:
            raise ValueError("response_time_ms must be >= 0")
        return v


class WebhookDeliveryListResponse(BaseModel):
    """Paginated response for webhook delivery list."""

    items: List[WebhookDelivery] = Field(..., description="Array of delivery records")
    pagination: Pagination = Field(..., description="Pagination metadata")

