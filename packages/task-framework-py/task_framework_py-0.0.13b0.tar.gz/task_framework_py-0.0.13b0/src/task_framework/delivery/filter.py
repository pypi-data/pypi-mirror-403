"""Event and data filtering logic for webhook delivery."""

from typing import Any, Dict, List, Optional

from task_framework.models.webhook import Webhook
from task_framework.models.webhook_scoping import WebhookScope


def matches_scope(webhook_scope: Optional[WebhookScope], event_metadata: Dict[str, Any], thread_id: Optional[str] = None) -> bool:
    """Check if event matches webhook scope.

    Args:
        webhook_scope: Webhook scope configuration (None matches all)
        event_metadata: Event metadata (containing user_id, app_id, tenant_id, etc.)
        thread_id: Thread identifier (for thread-scoped matching)

    Returns:
        True if event matches scope, False otherwise
    """
    # If no scope specified, match all events
    if not webhook_scope:
        return True

    # Thread-scoped webhooks only match events for that specific thread
    if webhook_scope.thread_id:
        return thread_id == webhook_scope.thread_id

    # Check other scope fields (AND logic - all specified fields must match)
    if webhook_scope.tenant_id and event_metadata.get("tenant_id") != webhook_scope.tenant_id:
        return False
    if webhook_scope.user_id and event_metadata.get("user_id") != webhook_scope.user_id:
        return False
    if webhook_scope.app_id and event_metadata.get("app_id") != webhook_scope.app_id:
        return False
    if webhook_scope.schedule_id and event_metadata.get("schedule_id") != webhook_scope.schedule_id:
        return False

    return True


def matches_event_type(webhook: Webhook, event_type: str) -> bool:
    """Check if event type matches webhook event filters.

    Args:
        webhook: Webhook instance with event filters
        event_type: Event type to check (e.g., "thread.succeeded")

    Returns:
        True if event type matches filters, False otherwise
    """
    # If no event filters, match all events
    if not webhook.events:
        return True

    # Check include filter
    if webhook.events.include:
        return event_type in webhook.events.include

    # Check exclude filter
    if webhook.events.exclude:
        return event_type not in webhook.events.exclude

    # No filters specified, match all
    return True


def should_deliver_webhook(
    webhook: Webhook,
    event_type: str,
    event_metadata: Dict[str, Any],
    thread_id: Optional[str] = None,
) -> bool:
    """Check if webhook should receive event based on scope and event filters.

    Args:
        webhook: Webhook instance to check
        event_type: Event type (e.g., "thread.succeeded")
        event_metadata: Event metadata (for scope matching)
        thread_id: Thread identifier (for thread-scoped matching)

    Returns:
        True if webhook should receive event, False otherwise
    """
    # Skip disabled webhooks
    if not webhook.enabled:
        return False

    # Check task_id filter (if webhook has task_id set, event must match)
    if webhook.task_id:
        event_task_id = event_metadata.get("task_id")
        if event_task_id != webhook.task_id:
            return False

    # Check task_version filter (if webhook has task_version set, event must match)
    if webhook.task_version:
        event_task_version = event_metadata.get("task_version")
        if event_task_version != webhook.task_version:
            return False

    # Check scope matching (more restrictive)
    if not matches_scope(webhook.scope, event_metadata, thread_id):
        return False

    # Check event type matching
    if not matches_event_type(webhook, event_type):
        return False

    return True

