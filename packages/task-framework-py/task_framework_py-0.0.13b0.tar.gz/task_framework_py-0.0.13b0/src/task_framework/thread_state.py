"""Thread state enumeration."""

from enum import Enum


class ThreadState(str, Enum):
    """Thread execution state."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    STOPPED = "stopped"
    TIMEOUT = "timeout"
    EXPIRED = "expired"

