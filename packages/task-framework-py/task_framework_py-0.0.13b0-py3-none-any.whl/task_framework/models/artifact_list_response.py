"""Artifact list response model."""

from typing import List

from pydantic import BaseModel, Field

from task_framework.models.artifact import Artifact
from task_framework.models.pagination import Pagination


class ArtifactListResponse(BaseModel):
    """Response model for artifact list endpoints."""

    items: List[Artifact] = Field(..., description="List of artifacts")
    pagination: Pagination = Field(..., description="Pagination metadata")

