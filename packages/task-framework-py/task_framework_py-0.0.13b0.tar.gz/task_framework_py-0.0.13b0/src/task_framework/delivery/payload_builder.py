"""Webhook payload builder with data filtering support."""

from typing import Any, Dict, List, Optional

from task_framework.models.artifact import Artifact
from task_framework.models.webhook import DataFilters, Webhook
from task_framework.utils.ref_filtering import matches_ref_pattern


def build_webhook_payload(
    event_type: str,
    timestamp: str,
    thread_id: Optional[str],
    run_id: Optional[str],
    thread: Optional[Any],
    metadata: Optional[Dict[str, Any]],
    artifacts: Optional[List[Artifact]],
    data_filters: Optional[DataFilters],
    file_storage: Optional[Any] = None,
) -> Dict[str, Any]:
    """Build webhook payload with data filtering applied.

    Args:
        event_type: Event type (e.g., "thread.succeeded")
        timestamp: Event timestamp (ISO format)
        thread_id: Thread identifier (if applicable)
        run_id: Run identifier (if applicable)
        thread: Thread instance (if available)
        metadata: Event metadata
        artifacts: List of artifacts for the thread
        data_filters: Data filtering configuration
        file_storage: File storage instance (for download URLs)

    Returns:
        Filtered payload dictionary
    """
    payload: Dict[str, Any] = {
        "event_type": event_type,
        "timestamp": timestamp,
    }

    if thread_id:
        payload["thread_id"] = thread_id

    if run_id:
        payload["run_id"] = run_id

    # Apply detail level filtering
    # Detail defaults to "inline_small" per DataFilters model
    detail_level = (data_filters.detail if data_filters else None) or "inline_small"

    if detail_level == "none":
        # No thread data or artifacts
        if metadata:
            payload["metadata"] = metadata
        return payload

    # Include thread data
    if thread:
        thread_dict = _serialize_thread(thread)
        payload["thread"] = thread_dict

    # Include metadata
    if metadata:
        payload["metadata"] = metadata

    # Apply artifact filtering
    if artifacts:
        filtered_artifacts = _filter_artifacts(artifacts, data_filters)
        artifact_dicts = _serialize_artifacts(
            filtered_artifacts,
            detail_level,
            data_filters,
            file_storage,
        )
        if artifact_dicts:
            payload["artifacts"] = artifact_dicts

    # Include logs if requested
    if data_filters and data_filters.include_logs:
        # TODO: Extract logs from thread/execution context (if available)
        # For now, logs are not implemented in the thread model
        pass

    # Include metrics if requested
    if data_filters and data_filters.include_metrics:
        # TODO: Extract metrics from thread/execution context (if available)
        # For now, metrics are not implemented in the thread model
        pass

    return payload


def _filter_artifacts(artifacts: List[Artifact], data_filters: Optional[DataFilters]) -> List[Artifact]:
    """Filter artifacts based on artifact selectors.

    Args:
        artifacts: List of artifacts to filter
        data_filters: Data filtering configuration

    Returns:
        Filtered list of artifacts
    """
    if not data_filters or not data_filters.artifact_selectors:
        return artifacts

    filtered: List[Artifact] = []
    selectors = data_filters.artifact_selectors

    for artifact in artifacts:
        # Check if artifact matches any selector
        for selector in selectors:
            if matches_ref_pattern(artifact.ref, selector.ref):
                filtered.append(artifact)
                break

    return filtered


def _serialize_artifacts(
    artifacts: List[Artifact],
    detail_level: str,
    data_filters: Optional[DataFilters],
    file_storage: Optional[Any],
) -> List[Dict[str, Any]]:
    """Serialize artifacts based on detail level and filters.

    Args:
        artifacts: List of artifacts to serialize
        detail_level: Detail level ("none", "inline_small", "inline_all")
        data_filters: Data filtering configuration
        file_storage: File storage instance (for download URLs)

    Returns:
        List of serialized artifact dictionaries
    """
    if detail_level == "none":
        return []

    artifact_dicts: List[Dict[str, Any]] = []
    include_download_urls = data_filters.include_download_urls if data_filters else False

    for artifact in artifacts:
        artifact_dict: Dict[str, Any] = {
            "id": artifact.id,
            "kind": artifact.kind,
            "ref": artifact.ref,
        }

        if artifact.media_type:
            artifact_dict["media_type"] = artifact.media_type

        if artifact.explain:
            artifact_dict["explain"] = artifact.explain

        if artifact.size is not None:
            artifact_dict["size"] = artifact.size

        if artifact.sha256:
            artifact_dict["sha256"] = artifact.sha256

        # Apply detail level filtering
        if detail_level == "inline_small":
            # Include small artifacts (< 1MB) inline, reference large ones
            if artifact.size is not None and artifact.size < 1024 * 1024:  # 1MB
                # Include inline value
                if artifact.text is not None:
                    artifact_dict["text"] = artifact.text
                elif artifact.value is not None:
                    artifact_dict["value"] = artifact.value
            else:
                # Large artifact - only include reference
                if artifact.file_ref:
                    artifact_dict["file_ref"] = artifact.file_ref
                if artifact.url:
                    artifact_dict["url"] = artifact.url

        elif detail_level == "inline_all":
            # Include all artifacts inline
            if artifact.text is not None:
                artifact_dict["text"] = artifact.text
            if artifact.value is not None:
                artifact_dict["value"] = artifact.value
            if artifact.file_ref:
                artifact_dict["file_ref"] = artifact.file_ref
            if artifact.url:
                artifact_dict["url"] = artifact.url

        # Include download URLs if requested and available
        if include_download_urls and artifact.file_ref and file_storage:
            try:
                # Generate download URL (if file storage supports it)
                # TODO: Implement download URL generation from file storage
                # For now, skip download URL generation
                pass
            except Exception:
                # Skip if URL generation fails
                pass

        artifact_dicts.append(artifact_dict)

    return artifact_dicts


def _serialize_thread(thread: Any) -> Dict[str, Any]:
    """Serialize thread object to dictionary.

    Args:
        thread: Thread instance

    Returns:
        Thread dictionary
    """
    thread_dict: Dict[str, Any] = {
        "id": thread.id,
        "state": str(thread.state),
    }

    if thread.created_at:
        thread_dict["created_at"] = thread.created_at.isoformat() + "Z"

    if thread.started_at:
        thread_dict["started_at"] = thread.started_at.isoformat() + "Z"

    if thread.finished_at:
        thread_dict["finished_at"] = thread.finished_at.isoformat() + "Z"

    if thread.error:
        thread_dict["error"] = {
            "message": thread.error.message,
            "exception_type": thread.error.exception_type,
        }

    if thread.metadata:
        thread_dict["metadata"] = thread.metadata

    if thread.params:
        thread_dict["params"] = thread.params

    if thread.schedule_id:
        thread_dict["schedule_id"] = thread.schedule_id

    if thread.run_id:
        thread_dict["run_id"] = thread.run_id

    if thread.attempt is not None:
        thread_dict["attempt"] = thread.attempt

    return thread_dict

