"""Webhook scoping models for event filtering."""

from typing import Optional

from pydantic import BaseModel, field_validator, model_validator


class WebhookScope(BaseModel):
    """Webhook scope configuration for event filtering."""

    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    app_id: Optional[str] = None
    schedule_id: Optional[str] = None
    thread_id: Optional[str] = None

    @field_validator("*")
    @classmethod
    def validate_scope_fields(cls, v: Optional[str]) -> Optional[str]:
        """Validate scope fields are strings if provided."""
        if v is not None and not isinstance(v, str):
            raise ValueError("Scope fields must be strings")
        return v

    @model_validator(mode="after")
    def validate_at_least_one_scope(self) -> "WebhookScope":
        """Validate at least one scope field is specified."""
        if not any(
            [
                self.tenant_id,
                self.user_id,
                self.app_id,
                self.schedule_id,
                self.thread_id,
            ]
        ):
            raise ValueError("At least one scope field must be specified")
        return self

