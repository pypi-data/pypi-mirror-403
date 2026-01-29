"""Artifact validation utility functions."""

from typing import Any, Dict, List, Optional

from task_framework.errors import ARTIFACT_INVALID_TYPE, ARTIFACT_VALIDATION_FAILED
from task_framework.models.artifact import Artifact


# Supported artifact types
SUPPORTED_ARTIFACT_TYPES = {
    "text",
    "rich_text",
    "url",
    "file",
    "binary",
    "json",
    "log",
    "metrics",
    "table",
    "bundle",
    "http_request",
    "http_response",
    "geo",
    "patch",
    "provenance",
}

# Text artifact types
TEXT_ARTIFACT_TYPES = {"text", "rich_text"}

# JSON-like artifact types
JSON_ARTIFACT_TYPES = {"json", "metrics", "provenance", "geo", "patch"}

# File-like artifact types
FILE_ARTIFACT_TYPES = {"file", "binary", "log", "table"}


class ArtifactValidationError(Exception):
    """Exception raised when artifact validation fails."""

    def __init__(self, message: str, errors: List[Dict[str, str]]):
        """Initialize validation error.

        Args:
            message: Error message
            errors: List of field-level errors with 'field' and 'message' keys
        """
        super().__init__(message)
        self.message = message
        self.errors = errors


def validate_artifact_type(kind: str) -> None:
    """Validate that artifact kind is supported.

    Args:
        kind: Artifact kind to validate

    Raises:
        ArtifactValidationError: If artifact kind is not supported
    """
    if kind not in SUPPORTED_ARTIFACT_TYPES:
        raise ArtifactValidationError(
            f"Invalid artifact type: {kind}",
            [
                {
                    "field": "kind",
                    "message": f"Artifact type '{kind}' is not supported. Supported types: {', '.join(sorted(SUPPORTED_ARTIFACT_TYPES))}",
                }
            ],
        )


def validate_artifact_fields(artifact: Artifact) -> None:
    """Validate artifact fields based on artifact kind.

    Args:
        artifact: Artifact instance to validate

    Raises:
        ArtifactValidationError: If artifact fields are invalid
    """
    errors: List[Dict[str, str]] = []
    kind = artifact.kind

    # Validate artifact type
    validate_artifact_type(kind)

    # Validate required fields per artifact type
    if kind in TEXT_ARTIFACT_TYPES:
        if not artifact.text and not artifact.file_ref:
            errors.append(
                {
                    "field": "text",
                    "message": f"text or file_ref required for {kind} artifacts",
                }
            )
    elif kind in JSON_ARTIFACT_TYPES:
        if artifact.value is None and not artifact.file_ref:
            errors.append(
                {
                    "field": "value",
                    "message": f"value or file_ref required for {kind} artifacts",
                }
            )
    elif kind in FILE_ARTIFACT_TYPES:
        if not artifact.file_ref:
            errors.append(
                {
                    "field": "file_ref",
                    "message": f"file_ref required for {kind} artifacts",
                }
            )
    elif kind == "http_response":
        # http_response can have value (with status) or file_ref
        if artifact.value is None or not isinstance(artifact.value, dict) or "status" not in artifact.value:
            if not artifact.file_ref:
                errors.append(
                    {
                        "field": "status",
                        "message": "status (in value) or file_ref required for http_response artifacts",
                    }
                )

    if errors:
        raise ArtifactValidationError(
            f"Artifact validation failed: {len(errors)} field(s) failed validation",
            errors,
        )


def validate_ref_format(ref: Optional[str]) -> None:
    """Validate ref format constraints.

    Args:
        ref: Ref value to validate

    Raises:
        ArtifactValidationError: If ref format is invalid
    """
    if ref is None:
        return

    errors: List[Dict[str, str]] = []

    if not isinstance(ref, str):
        errors.append({"field": "ref", "message": "ref must be a string"})
    elif not ref.strip():
        errors.append({"field": "ref", "message": "ref must be non-empty"})
    elif len(ref) > 255:
        errors.append({"field": "ref", "message": "ref must be 255 characters or less"})

    if errors:
        raise ArtifactValidationError(
            "Ref format validation failed",
            errors,
        )

