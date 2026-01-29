"""ThreadError model class with Pydantic validation."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ThreadError(BaseModel):
    """Error details associated with a failed thread."""

    code: Optional[str] = Field(None, description="Error code (if available)")
    message: str = Field(..., description="Error message")
    exception_type: str = Field(..., description="Python exception type name")
    stack_trace: str = Field(..., description="Formatted stack trace")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error context")

