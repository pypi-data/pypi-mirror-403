"""Structured logging infrastructure using structlog."""

import os
import sys
from datetime import datetime, timezone

import structlog


def _get_log_level() -> str:
    """Get log level from environment variable LOG_LEVEL.
    
    Returns:
        Log level string (DEBUG, INFO, WARN, ERROR). Defaults to INFO.
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    valid_levels = {"DEBUG", "INFO", "WARN", "ERROR"}
    if log_level not in valid_levels:
        return "INFO"
    return log_level


def _iso8601_timestamp_processor(logger, method_name, event_dict):
    """Add ISO 8601 timestamp with millisecond precision (UTC) to log entry."""
    # Generate timestamp with millisecond precision
    now = datetime.now(timezone.utc)
    timestamp_str = now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    event_dict["timestamp"] = timestamp_str
    return event_dict


def _add_error_fields(logger, method_name, event_dict):
    """Add error, error_code, and stack_trace fields for ERROR level logs."""
    if method_name == "error":
        # Check if exc_info was already processed by format_exc_info
        if "exception" in event_dict:
            # Extract exception details
            exc_str = event_dict.get("exception", "")
            if exc_str:
                event_dict["error"] = exc_str.split("\n")[0] if "\n" in exc_str else exc_str
                # Try to extract error code from exception type
                if "Traceback" in exc_str:
                    lines = exc_str.split("\n")
                    for line in lines:
                        if ":" in line and ("Error" in line or "Exception" in line):
                            parts = line.split(":")
                            if len(parts) > 0:
                                event_dict["error_code"] = parts[0].strip()
                                break
                event_dict["stack_trace"] = exc_str
        # Also check if error was passed directly
        elif "error" not in event_dict:
            # If exc_info=True was passed, format_exc_info will have added exception
            # Otherwise, check if an exception object was passed
            pass
    return event_dict


logger = structlog.get_logger()


def get_logger_with_request_id(request_id: str):
    """Get a logger bound with request_id context.
    
    Args:
        request_id: Request identifier to bind to logger
        
    Returns:
        Logger instance bound with request_id
    """
    return logger.bind(request_id=request_id)


def configure_logging() -> None:
    """Configure structlog for structured logging.
    
    Configures logging to:
    - Output NDJSON format (one JSON object per line) to stdout
    - Use ISO 8601 timestamps with millisecond precision (UTC)
    - Support LOG_LEVEL environment variable for log level filtering
    - Include error, error_code, and stack_trace fields for ERROR logs
    - Support standard context fields (thread_id, user_id, app_id, etc.)
    """
    log_level = _get_log_level()
    
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            _iso8601_timestamp_processor,  # Custom timestamp with millisecond precision
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,  # Process exceptions first
            _add_error_fields,  # Add error fields for ERROR logs (after format_exc_info)
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),  # NDJSON format (one JSON object per line)
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging to output to stdout
    import logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level),
    )

