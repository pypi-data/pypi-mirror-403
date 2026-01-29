"""System settings model for configurable server behavior."""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class SystemSettings(BaseModel):
    """System-wide settings that control server behavior.
    
    Settings can be configured via:
    1. Environment variables (initial defaults)
    2. Admin API (runtime updates)
    3. UI Settings page (admin users)
    """
    
    # Thread concurrency settings
    max_concurrent_threads: int = Field(
        default=0,
        ge=0,
        description="Maximum threads running concurrently (0 = unlimited)"
    )
    
    # Metadata
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Last update timestamp (UTC)"
    )
    updated_by: Optional[str] = Field(
        default=None,
        description="User/admin who last updated settings"
    )
    
    @classmethod
    def default(cls) -> "SystemSettings":
        """Create settings with defaults from environment."""
        import os
        
        max_threads = int(os.getenv("MAX_CONCURRENT_THREADS", "0"))
        
        return cls(
            max_concurrent_threads=max_threads,
            updated_at=datetime.now(timezone.utc),
        )


class SettingsUpdateRequest(BaseModel):
    """Request model for updating system settings."""
    
    max_concurrent_threads: Optional[int] = Field(
        default=None,
        ge=0,
        description="Maximum threads running concurrently (0 = unlimited)"
    )


class SettingsResponse(BaseModel):
    """Response model for system settings."""
    
    max_concurrent_threads: int = Field(
        description="Maximum threads running concurrently (0 = unlimited)"
    )
    updated_at: Optional[datetime] = Field(
        description="Last update timestamp (UTC)"
    )
    updated_by: Optional[str] = Field(
        default=None,
        description="User/admin who last updated settings"
    )
    
    # Runtime stats
    current_running_threads: int = Field(
        default=0,
        description="Number of currently running threads"
    )
    current_queued_threads: int = Field(
        default=0,
        description="Number of threads waiting in queue"
    )
