"""Pagination model for list responses."""

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Pagination(BaseModel):
    """Pagination metadata for list responses."""

    cursor: Optional[str] = Field(None, description="Cursor for next page (Base64-encoded JSON with thread_id and created_at)")
    has_more: bool = Field(..., description="Whether more items are available")
    total: Optional[int] = Field(None, description="Total count if available")

    @field_validator("has_more")
    @classmethod
    def validate_has_more(cls, v: bool, info) -> bool:
        """Validate that has_more is true if cursor is not null."""
        if info.data.get("cursor") is not None and not v:
            raise ValueError("has_more must be true if cursor is not null")
        return v

