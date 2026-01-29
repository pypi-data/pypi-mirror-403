"""ThreadCreateRequest model for POST /threads endpoint."""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from task_framework.models.artifact import Artifact


class AdHocWebhook(BaseModel):
    """Ad-hoc webhook configuration for a thread."""

    callback_url: str = Field(..., description="Webhook callback URL (URI format)")
    events: List[str] = Field(
        default=["thread.succeeded", "thread.failed"],
        description="List of events to trigger webhook",
    )
    api_key: Optional[str] = Field(
        None,
        description="Optional X-API-Key header to include in webhook delivery requests",
    )


class ThreadCreateRequest(BaseModel):
    """Request payload for creating threads via POST /threads endpoint."""

    mode: Literal["sync", "async"] = Field(..., description="Execution mode: sync (wait) or async (return immediately)")
    name: Optional[str] = Field(None, description="Optional thread name for display and grouping")
    inputs: List[Artifact] = Field(..., description="Input artifacts (required, non-empty)")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Task-specific parameters")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Thread metadata (common fields: user_id, app_id)")
    webhooks: Optional[List[AdHocWebhook]] = Field(None, description="List of ad-hoc webhook configurations for this thread")
    webhook: Optional[AdHocWebhook] = Field(None, description="[Deprecated] Single ad-hoc webhook configuration. Use 'webhooks' array instead.")
    idempotency_key: Optional[str] = Field(None, description="Idempotency key for preventing duplicate creation")
    timeout_seconds: Optional[int] = Field(None, description="Execution timeout in seconds (minimum: 1)")

    @field_validator("inputs")
    @classmethod
    def validate_inputs_not_empty(cls, v: List[Artifact]) -> List[Artifact]:
        """Validate that inputs is not empty."""
        if not v:
            raise ValueError("inputs must be a non-empty array")
        return v

    @field_validator("timeout_seconds")
    @classmethod
    def validate_timeout(cls, v: Optional[int]) -> Optional[int]:
        """Validate timeout_seconds is >= 1 if provided."""
        if v is not None and v < 1:
            raise ValueError("timeout_seconds must be >= 1")
        return v

    @model_validator(mode="after")
    def normalize_webhooks(self) -> "ThreadCreateRequest":
        """Normalize webhook (deprecated) to webhooks array for backward compatibility."""
        if self.webhook and not self.webhooks:
            # Convert single webhook to list
            self.webhooks = [self.webhook]
        elif self.webhook and self.webhooks:
            # Both provided - merge them (webhooks takes precedence, but include webhook too)
            if self.webhook not in self.webhooks:
                self.webhooks.append(self.webhook)
        return self

