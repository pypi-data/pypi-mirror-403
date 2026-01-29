"""ThreadRetryRequest model for POST /threads/{thread_id}:retry endpoint."""

from typing import Optional

from pydantic import BaseModel, Field


class ThreadRetryRequest(BaseModel):
    """Request payload for retrying threads via POST /threads/{thread_id}:retry endpoint."""

    preserve_run_id: Optional[bool] = Field(default=False, description="Whether to preserve the run_id from original thread (default: false)")

