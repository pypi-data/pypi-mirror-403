"""Artifact download response model."""

from typing import Optional

from pydantic import BaseModel, Field


class ArtifactDownloadResponse(BaseModel):
    """Response model for artifact download URL endpoint."""

    download_url: str = Field(..., description="Pre-signed download URL")
    expires_at: str = Field(..., description="ISO 8601 timestamp when URL expires")
    expires_in: int = Field(..., description="Expiration time in seconds")

