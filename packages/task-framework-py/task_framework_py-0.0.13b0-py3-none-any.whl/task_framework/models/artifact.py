"""Artifact model class with Pydantic validation."""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class Artifact(BaseModel):
    """Input or output payload unit (text, file, JSON, etc.)."""

    id: Optional[str] = Field(None, description="Unique artifact identifier (auto-generated if not provided)")
    thread_id: Optional[str] = Field(None, description="Associated thread identifier (auto-generated if not provided)")
    kind: str = Field(
        ...,
        description="Artifact type (text, rich_text, url, file, binary, json, log, metrics, table, bundle, http_request, http_response, geo, patch, provenance)",
    )
    media_type: Optional[str] = Field(None, description="MIME type (if applicable)")
    ref: Optional[str] = Field(None, description="Stable reference name (unique within thread)")
    explain: Optional[str] = Field(None, description="Human-readable description")
    size: Optional[int] = Field(None, description="Size in bytes (for files)")
    sha256: Optional[str] = Field(None, description="SHA-256 hash (for files)")
    file_ref: Optional[str] = Field(None, description="File reference (for file artifacts)")
    url: Optional[str] = Field(None, description="URL (for url artifacts)")
    value: Optional[Any] = Field(None, description="Inline value (for text/json artifacts)")
    text: Optional[str] = Field(None, description="Inline text content (for text/rich_text artifacts)")
    labels: Dict[str, Any] = Field(default_factory=dict, description="Freeform tags/metadata")
    created_at: Optional[datetime] = Field(None, description="Artifact creation timestamp (UTC, auto-generated if not provided)")
    archived: bool = Field(default=False, description="Whether artifact is archived (default: False)")
    archived_at: Optional[datetime] = Field(None, description="Timestamp when artifact was archived (UTC, None if not archived)")
    # Task association fields (populated from thread metadata for UI display)
    task_id: Optional[str] = Field(None, description="Task definition ID (from thread metadata)")
    task_version: Optional[str] = Field(None, description="Task version (from thread metadata)")
    # Direction field (input or output)
    direction: Optional[str] = Field(None, description="Artifact direction: 'input' or 'output'")
    
    @field_validator('ref')
    @classmethod
    def validate_ref_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate ref format: non-empty string, max 255 characters."""
        if v is None:
            return v
        if not isinstance(v, str):
            raise ValueError("ref must be a string")
        if not v.strip():
            raise ValueError("ref must be non-empty")
        if len(v) > 255:
            raise ValueError("ref must be 255 characters or less")
        return v
    
    @model_validator(mode='after')
    def validate_artifact_fields(self):
        """Validate required fields per artifact kind."""
        from task_framework.utils.artifact_validation import (
            JSON_ARTIFACT_TYPES,
            FILE_ARTIFACT_TYPES,
            TEXT_ARTIFACT_TYPES,
        )
        
        kind = self.kind
        
        # Validate text artifacts
        if kind in TEXT_ARTIFACT_TYPES:
            if not self.text and not self.file_ref:
                raise ValueError(f"text or file_ref required for {kind} artifacts")
        
        # Validate JSON-like artifacts
        elif kind in JSON_ARTIFACT_TYPES:
            if self.value is None and not self.file_ref:
                raise ValueError(f"value or file_ref required for {kind} artifacts")
        
        # Validate file-like artifacts
        elif kind in FILE_ARTIFACT_TYPES:
            if not self.file_ref:
                raise ValueError(f"file_ref required for {kind} artifacts")
        
        # Validate URL artifacts
        elif kind == "url":
            if not self.url:
                raise ValueError("url required for url artifacts")
        
        # Validate bundle artifacts
        elif kind == "bundle":
            if not self.value or not isinstance(self.value, list):
                raise ValueError("items (list) required for bundle artifacts")
        
        # Validate http_request artifacts
        elif kind == "http_request":
            if not self.url:
                raise ValueError("url required for http_request artifacts")
        
        # Validate http_response artifacts
        elif kind == "http_response":
            if self.value is None or not isinstance(self.value, dict) or "status" not in self.value:
                raise ValueError("status required for http_response artifacts")
        
        return self
    
    @model_validator(mode='after')
    def ensure_id(self):
        """Ensure id is set if not provided."""
        if not self.id:
            from task_framework.utils.id_generator import generate_artifact_id
            self.id = generate_artifact_id()
        return self

