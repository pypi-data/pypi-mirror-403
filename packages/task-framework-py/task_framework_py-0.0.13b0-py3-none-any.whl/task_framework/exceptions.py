"""Base exception classes for Task Framework."""


class TaskFrameworkError(Exception):
    """Base exception for Task Framework errors."""

    pass


class ConfigurationError(TaskFrameworkError):
    """Raised when configuration is invalid."""

    pass


class TaskFunctionError(TaskFrameworkError):
    """Raised when task function registration fails."""

    pass

