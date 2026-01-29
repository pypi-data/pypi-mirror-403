"""ThreadListResponse model for GET /threads endpoint."""

from typing import List

from pydantic import BaseModel, Field

from task_framework.models.pagination import Pagination
from task_framework.models.thread import Thread


class ThreadListResponse(BaseModel):
    """Paginated response for GET /threads endpoint."""

    items: List[Thread] = Field(..., description="Array of Thread objects matching the query")
    pagination: Pagination = Field(..., description="Pagination metadata")

    @property
    def count(self) -> int:
        """Get the number of items in the response."""
        return len(self.items)

