"""Artifact query filters model."""

from typing import Optional

from pydantic import BaseModel, Field


class ArtifactQueryFilters(BaseModel):
    """Query filters for artifact list endpoints."""

    ref: Optional[str] = Field(None, description="Ref filter (supports prefix wildcards with *)")
    kind: Optional[str] = Field(None, description="Artifact kind filter")
    media_type: Optional[str] = Field(None, description="Media type filter")
    direction: Optional[str] = Field(None, description="Direction filter: 'input', 'output', or 'both'")
    include_archived: bool = Field(default=False, description="Include archived artifacts (default: false)")
    limit: Optional[int] = Field(None, description="Maximum number of results")
    cursor: Optional[str] = Field(None, description="Pagination cursor")

