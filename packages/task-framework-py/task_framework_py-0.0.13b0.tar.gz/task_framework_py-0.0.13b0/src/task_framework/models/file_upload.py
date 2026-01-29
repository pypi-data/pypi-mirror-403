"""Pydantic models for file storage API endpoints."""

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field, field_validator


class CreateUploadRequest(BaseModel):
    """Request payload for creating upload URLs via POST /uploads endpoint."""

    filename: Optional[str] = Field(None, description="Original filename")
    media_type: str = Field(..., description="MIME type (e.g., 'application/pdf', 'image/png')")
    size: int = Field(..., description="File size in bytes", ge=0)
    expires_in: Optional[int] = Field(
        default=3600,
        description="Expiration time in seconds (default: 3600). Use 0 for permanent/no expiration.",
    )

    @field_validator("media_type")
    @classmethod
    def validate_media_type(cls, v: str) -> str:
        """Validate media_type format."""
        if not v or "/" not in v:
            raise ValueError("media_type must be a valid MIME type format (e.g., 'application/pdf')")
        return v


class UploadUrlResponse(BaseModel):
    """Response payload for upload URL creation."""

    file_ref: str = Field(..., description="Unique file reference identifier")
    upload_url: str = Field(..., description="Pre-signed URL for file upload")
    expires_at: Optional[datetime] = Field(
        None, description="Expiration timestamp (ISO 8601 UTC). Omitted if permanent."
    )
    method: str = Field(default="PUT", description="HTTP method (typically 'PUT')")
    headers: Dict[str, str] = Field(default_factory=dict, description="Required HTTP headers for upload")


class FileUploadResponse(BaseModel):
    """Response payload for direct file upload."""

    file_ref: str = Field(..., description="Unique file reference identifier")
    size: int = Field(..., description="File size in bytes")
    media_type: str = Field(..., description="File MIME type")
    sha256: Optional[str] = Field(None, description="SHA256 hash (may be omitted if computation is asynchronous)")
    created_at: datetime = Field(..., description="Creation timestamp (ISO 8601 UTC)")

