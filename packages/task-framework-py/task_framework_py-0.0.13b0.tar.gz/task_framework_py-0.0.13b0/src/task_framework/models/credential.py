"""Credential and TaskConfiguration models for secrets management."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Requirement(BaseModel):
    """Configuration requirement declared in task.yaml."""
    
    name: str = Field(..., description="Configuration key name")
    required: bool = Field(default=True, description="Whether this key is required")
    default: Optional[str] = Field(None, description="Default value if not configured")
    description: str = Field(default="", description="Human-readable description")


class Credential(BaseModel):
    """A server-level credential/secret stored in the credentials store."""
    
    name: str = Field(..., description="Unique credential identifier")
    value: str = Field(..., description="The credential value (encrypted at rest)")
    description: str = Field(default="", description="Human-readable description")
    tags: List[str] = Field(default_factory=list, description="Tags for organization")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = Field(None, description="Optional expiration time")
    
    def is_expired(self) -> bool:
        """Check if the credential has expired.
        
        Returns:
            True if expired
        """
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at


class CredentialInfo(BaseModel):
    """Credential information without the sensitive value (for API responses)."""
    
    name: str
    description: str = ""
    tags: List[str] = []
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    has_value: bool = True
    value_preview: Optional[str] = None
    
    @classmethod
    def from_credential(cls, credential: Credential) -> "CredentialInfo":
        """Create CredentialInfo from a Credential.
        
        Args:
            credential: The source credential
            
        Returns:
            CredentialInfo without the sensitive value
        """
        # Generate preview (last 4 chars)
        value = credential.value
        if not value:
            preview = ""
        elif len(value) <= 4:
            preview = "••••"
        else:
            preview = "••••" + value[-4:]

        return cls(
            name=credential.name,
            description=credential.description,
            tags=credential.tags,
            created_at=credential.created_at,
            updated_at=credential.updated_at,
            expires_at=credential.expires_at,
            has_value=bool(credential.value),
            value_preview=preview,
        )


class TaskConfiguration(BaseModel):
    """Configuration for a specific task version.
    
    Stores configuration values - either direct values or vault references.
    All values are encrypted at rest.
    """
    
    task_id: str = Field(..., description="Task identifier")
    version: str = Field(..., description="Task version")
    
    # Configuration values: key -> {"value": "...", "is_vault_ref": false} or {"vault_key": "...", "is_vault_ref": true}
    config_values: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Configuration values - direct values or vault references"
    )
    
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ResolvedConfiguration(BaseModel):
    """Fully resolved configuration for task execution.
    
    Contains the actual values (env vars and secrets) ready for injection.
    """
    
    env_vars: Dict[str, str] = Field(
        default_factory=dict,
        description="Resolved environment variables"
    )
    secrets: Dict[str, str] = Field(
        default_factory=dict,
        description="Resolved secret values"
    )


class ConfigurationStatus(BaseModel):
    """Status of task configuration - what's configured and what's missing."""
    
    task_id: str
    version: str
    
    # Requirements from task.yaml with status
    requirements: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of requirement status objects"
    )
    
    # Current configuration values (for editing)
    config_values: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Current configuration values"
    )
    
    # Overall validation
    ready: bool = Field(default=False, description="Whether all required config is set")
    missing_required: List[str] = Field(
        default_factory=list,
        description="List of missing required configuration names"
    )
