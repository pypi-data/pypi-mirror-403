"""Logger interface abstract base class."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class Logger(ABC):
    """Abstract base class for logger interface."""

    @abstractmethod
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log a debug message."""
        pass

    @abstractmethod
    def info(self, message: str, **kwargs: Any) -> None:
        """Log an info message."""
        pass

    @abstractmethod
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message."""
        pass

    @abstractmethod
    def error(self, message: str, **kwargs: Any) -> None:
        """Log an error message."""
        pass

    @abstractmethod
    def bind(self, **kwargs: Any) -> "Logger":
        """Bind contextual data to logger."""
        pass

