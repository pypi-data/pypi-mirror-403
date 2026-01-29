"""Webhook service for managing webhook business logic."""

import secrets
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from task_framework.logging import logger
from task_framework.models.pagination import Pagination
from task_framework.models.webhook import (
    Webhook,
    WebhookCreateRequest,
    WebhookDelivery,
    WebhookDeliveryListResponse,
    WebhookListResponse,
    WebhookUpdateRequest,
)
from task_framework.models.webhook_scoping import WebhookScope
from task_framework.repositories.webhook_db import (
    WebhookDeliveryRepository,
    WebhookRepository,
)

if TYPE_CHECKING:
    pass


def generate_webhook_secret() -> str:
    """Generate a secure webhook secret.

    Returns:
        Base64-encoded secret string prefixed with 'whsec_'
    """
    # Generate 32 bytes of random data
    random_bytes = secrets.token_bytes(32)
    # Encode as base64url (safe for URLs)
    import base64

    secret_b64 = base64.urlsafe_b64encode(random_bytes).decode("ascii")
    # Prefix with 'whsec_' for identification
    return f"whsec_{secret_b64}"


class WebhookService:
    """Service layer for webhook management operations."""

    def __init__(
        self,
        webhook_repository: WebhookRepository,
        delivery_repository: WebhookDeliveryRepository,
    ) -> None:
        """Initialize WebhookService.

        Args:
            webhook_repository: WebhookRepository implementation
            delivery_repository: WebhookDeliveryRepository implementation
        """
        self.webhook_repository = webhook_repository
        self.delivery_repository = delivery_repository

    def validate_url(self, url: str) -> None:
        """Validate webhook URL format.

        Args:
            url: URL to validate

        Raises:
            ValueError: If URL is invalid
        """
        if not url or not url.strip():
            raise ValueError("Webhook URL must be non-empty")
        if not url.startswith(("http://", "https://")):
            raise ValueError("Webhook URL must start with http:// or https://")

    async def create_webhook(
        self,
        request: WebhookCreateRequest,
        created_by: Optional[str] = None,
        source: str = "manual",
    ) -> Webhook:
        """Create a new webhook.

        Args:
            request: Webhook creation request
            created_by: User/app identifier that created webhook
            source: Webhook source type: 'manual', 'thread', or 'schedule'

        Returns:
            Created Webhook instance with generated secret

        Raises:
            ValueError: If URL validation fails
        """
        # Validate URL
        self.validate_url(request.url)

        # Generate webhook ID
        from task_framework.utils.id_generator import generate_webhook_id
        webhook_id = generate_webhook_id()

        # Generate secret
        secret = generate_webhook_secret()

        # Create webhook
        now = datetime.now(timezone.utc)
        webhook = Webhook(
            id=webhook_id,
            url=request.url,
            secret=secret,
            enabled=request.enabled,
            events=request.events,
            data_filters=request.data_filters,
            scope=request.scope,
            timeout_seconds=request.timeout_seconds or 10,
            api_key=request.api_key,
            task_id=request.task_id,
            task_version=request.task_version,
            source=source,
            created_at=now,
            updated_at=now,
            created_by=created_by,
            metadata={},
        )

        # Store webhook
        await self.webhook_repository.create_webhook(webhook)

        logger.info(
            "webhook.created",
            webhook_id=webhook_id,
            url=request.url,
            enabled=request.enabled,
            source=source,
            created_by=created_by,
        )

        return webhook

    async def get_webhook(self, webhook_id: str) -> Optional[Webhook]:
        """Get a webhook by ID.

        Args:
            webhook_id: Webhook identifier

        Returns:
            Webhook instance if found, None otherwise
        """
        return await self.webhook_repository.get_webhook(webhook_id)

    async def list_webhooks(
        self,
        is_enabled: Optional[bool] = None,
        task_id: Optional[str] = None,
        task_version: Optional[str] = None,
        source: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        offset: Optional[int] = None,
    ) -> WebhookListResponse:
        """List webhooks with optional filtering.

        Args:
            is_enabled: Filter by enabled status
            task_id: Filter by task ID
            task_version: Filter by task version
            source: Filter by webhook source (manual, thread, schedule)
            limit: Maximum number of results (default: 50)
            cursor: Pagination cursor
            offset: Offset for pagination (alternative to cursor)

        Returns:
            WebhookListResponse with paginated results
        """
        filters: Dict[str, Any] = {}
        if is_enabled is not None:
            filters["is_enabled"] = is_enabled
        if task_id is not None:
            filters["task_id"] = task_id
        if task_version is not None:
            filters["task_version"] = task_version
        if source is not None:
            filters["source"] = source

        # Get all webhooks (before pagination)
        webhooks = await self.webhook_repository.list_webhooks(filters)

        # Apply cursor-based pagination
        limit = limit or 50
        
        if cursor:
            # Decode cursor (Base64 JSON with webhook_id and created_at)
            import base64
            import json as json_lib
            
            try:
                cursor_data = json_lib.loads(base64.b64decode(cursor).decode())
                cursor_webhook_id = cursor_data.get("webhook_id")
                cursor_created_at = cursor_data.get("created_at")
                
                # Filter webhooks after cursor
                if cursor_created_at:
                    from datetime import datetime
                    cursor_time = datetime.fromisoformat(cursor_created_at.replace("Z", "+00:00"))
                    webhooks = [w for w in webhooks if w.created_at < cursor_time]
            except (ValueError, KeyError, TypeError):
                # Invalid cursor, return empty
                webhooks = []
        
        # Offset-based pagination fallback
        elif offset is not None:
            webhooks = webhooks[offset:]
        
        # Apply limit
        has_more = len(webhooks) > limit
        webhooks = webhooks[:limit]
        
        # Generate next cursor if has_more
        next_cursor = None
        if has_more and webhooks:
            import base64
            import json as json_lib
            
            last_webhook = webhooks[-1]
            cursor_data = {
                "webhook_id": last_webhook.id,
                "created_at": last_webhook.created_at.isoformat() + "Z",
            }
            next_cursor = base64.b64encode(json_lib.dumps(cursor_data).encode()).decode()
        
        pagination = Pagination(
            cursor=next_cursor,
            has_more=has_more,
            total=None,
        )

        return WebhookListResponse(items=webhooks, pagination=pagination)

    async def update_webhook(
        self,
        webhook_id: str,
        request: WebhookUpdateRequest,
    ) -> Webhook:
        """Update an existing webhook.

        Args:
            webhook_id: Webhook identifier
            request: Webhook update request (partial)

        Returns:
            Updated Webhook instance

        Raises:
            ValueError: If webhook not found or validation fails
        """
        webhook = await self.webhook_repository.get_webhook(webhook_id)
        if not webhook:
            raise ValueError(f"Webhook {webhook_id} not found")

        # Validate URL if provided
        if request.url:
            self.validate_url(request.url)

        # Apply updates
        if request.url is not None:
            webhook.url = request.url
        if request.enabled is not None:
            webhook.enabled = request.enabled
        if request.events is not None:
            webhook.events = request.events
        if request.data_filters is not None:
            webhook.data_filters = request.data_filters
        if request.scope is not None:
            webhook.scope = request.scope
        if request.timeout_seconds is not None:
            webhook.timeout_seconds = request.timeout_seconds
        if request.api_key is not None:
            webhook.api_key = request.api_key
        if request.task_id is not None:
            webhook.task_id = request.task_id
        if request.task_version is not None:
            webhook.task_version = request.task_version

        # Update timestamp
        webhook.updated_at = datetime.now(timezone.utc)

        # Store updated webhook
        await self.webhook_repository.update_webhook(webhook)

        logger.info(
            "webhook.updated",
            webhook_id=webhook_id,
            enabled=webhook.enabled,
        )

        return webhook

    async def delete_webhook(self, webhook_id: str) -> None:
        """Delete a webhook.

        Args:
            webhook_id: Webhook identifier to delete

        Raises:
            ValueError: If webhook not found
        """
        webhook = await self.webhook_repository.get_webhook(webhook_id)
        if not webhook:
            raise ValueError(f"Webhook {webhook_id} not found")

        await self.webhook_repository.delete_webhook(webhook_id)

        logger.info("webhook.deleted", webhook_id=webhook_id)

    async def create_ad_hoc_webhook(
        self,
        url: str,
        thread_id: str,
        events: Optional[List[str]] = None,
        created_by: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> Webhook:
        """Create an ad-hoc webhook with thread-scoped scope.

        Args:
            url: Webhook delivery URL
            thread_id: Thread identifier for scoping
            events: Optional list of event types (default: all events)
            created_by: User/app identifier that created webhook
            api_key: Optional X-API-Key header for webhook delivery requests

        Returns:
            Created Webhook instance with thread-scoped scope

        Raises:
            ValueError: If URL validation fails
        """
        # Validate URL
        self.validate_url(url)

        # Create event filters if events specified
        event_filters = None
        if events:
            from task_framework.models.webhook import EventFilters

            event_filters = EventFilters(include=events)

        # Create thread-scoped scope
        scope = WebhookScope(thread_id=thread_id)

        # Create webhook request
        request = WebhookCreateRequest(
            url=url,
            events=event_filters,
            scope=scope,
            enabled=True,
            timeout_seconds=10,
            api_key=api_key,
        )

        # Create webhook with source='thread'
        return await self.create_webhook(request, created_by=created_by, source="thread")

    async def create_schedule_webhook(
        self,
        url: str,
        schedule_id: str,
        events: Optional[List[str]] = None,
        created_by: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> Webhook:
        """Create a webhook for a schedule with schedule-scoped scope.

        Args:
            url: Webhook delivery URL
            schedule_id: Schedule identifier for scoping
            events: Optional list of event types (default: all events)
            created_by: User/app identifier that created webhook
            api_key: Optional X-API-Key header for webhook delivery requests

        Returns:
            Created Webhook instance with schedule-scoped scope

        Raises:
            ValueError: If URL validation fails
        """
        # Validate URL
        self.validate_url(url)

        # Create event filters if events specified
        event_filters = None
        if events:
            from task_framework.models.webhook import EventFilters

            event_filters = EventFilters(include=events)

        # Create schedule-scoped scope
        scope = WebhookScope(schedule_id=schedule_id)

        # Create webhook request
        request = WebhookCreateRequest(
            url=url,
            events=event_filters,
            scope=scope,
            enabled=True,
            timeout_seconds=10,
            api_key=api_key,
        )

        # Create webhook with source='schedule'
        return await self.create_webhook(request, created_by=created_by, source="schedule")

    async def regenerate_secret(self, webhook_id: str) -> Webhook:
        """Regenerate webhook secret.

        Args:
            webhook_id: Webhook identifier

        Returns:
            Updated Webhook instance with new secret

        Raises:
            ValueError: If webhook not found
        """
        webhook = await self.webhook_repository.get_webhook(webhook_id)
        if not webhook:
            raise ValueError(f"Webhook {webhook_id} not found")

        # Generate new secret
        webhook.secret = generate_webhook_secret()
        webhook.updated_at = datetime.now(timezone.utc)

        # Store updated webhook
        await self.webhook_repository.update_webhook(webhook)

        logger.info("webhook.secret_regenerated", webhook_id=webhook_id)

        return webhook

    async def get_matching_webhooks(
        self,
        event_type: str,
        thread_id: Optional[str] = None,
        run_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Webhook]:
        """Get webhooks that match an event based on scope and event filters.

        Args:
            event_type: Event type (e.g., "thread.succeeded")
            thread_id: Thread identifier (if applicable)
            run_id: Run identifier (if applicable)
            metadata: Event metadata (for scope matching)

        Returns:
            List of matching Webhook instances
        """
        from task_framework.delivery.filter import should_deliver_webhook

        # Get all enabled webhooks
        all_webhooks = await self.webhook_repository.list_webhooks(filters={"is_enabled": True})

        matching_webhooks: List[Webhook] = []
        event_metadata = metadata or {}

        for webhook in all_webhooks:
            if should_deliver_webhook(webhook, event_type, event_metadata, thread_id):
                matching_webhooks.append(webhook)

        return matching_webhooks

    async def list_deliveries(
        self,
        webhook_id: str,
        status: Optional[str] = None,
        thread_id: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        offset: Optional[int] = None,
    ) -> WebhookDeliveryListResponse:
        """List delivery records for a webhook.

        Args:
            webhook_id: Webhook identifier
            status: Filter by delivery status ("success" | "failed")
            thread_id: Filter by thread ID
            limit: Maximum number of results (default: 50)
            cursor: Pagination cursor
            offset: Offset for pagination (alternative to cursor)

        Returns:
            WebhookDeliveryListResponse with paginated results
        """
        filters: Dict[str, Any] = {}
        if status:
            filters["status"] = status
        if thread_id:
            filters["thread_id"] = thread_id

        # Get all deliveries (before pagination)
        deliveries = await self.delivery_repository.list_deliveries(webhook_id, filters)

        # Apply cursor-based pagination
        limit = limit or 50
        
        if cursor:
            # Decode cursor (Base64 JSON with delivery_id and timestamp)
            import base64
            import json as json_lib
            
            try:
                cursor_data = json_lib.loads(base64.b64decode(cursor).decode())
                cursor_delivery_id = cursor_data.get("delivery_id")
                cursor_timestamp = cursor_data.get("timestamp")
                
                # Filter deliveries after cursor
                if cursor_timestamp:
                    from datetime import datetime
                    cursor_time = datetime.fromisoformat(cursor_timestamp.replace("Z", "+00:00"))
                    deliveries = [d for d in deliveries if d.timestamp < cursor_time]
            except (ValueError, KeyError, TypeError):
                # Invalid cursor, return empty
                deliveries = []
        
        # Offset-based pagination fallback
        elif offset is not None:
            deliveries = deliveries[offset:]
        
        # Apply limit
        has_more = len(deliveries) > limit
        deliveries = deliveries[:limit]
        
        # Generate next cursor if has_more
        next_cursor = None
        if has_more and deliveries:
            import base64
            import json as json_lib
            
            last_delivery = deliveries[-1]
            cursor_data = {
                "delivery_id": last_delivery.id,
                "timestamp": last_delivery.timestamp.isoformat() + "Z",
            }
            next_cursor = base64.b64encode(json_lib.dumps(cursor_data).encode()).decode()
        
        pagination = Pagination(
            cursor=next_cursor,
            has_more=has_more,
            total=None,
        )

        return WebhookDeliveryListResponse(items=deliveries, pagination=pagination)

    async def get_delivery(self, webhook_id: str, delivery_id: str) -> Optional[WebhookDelivery]:
        """Get a delivery record by ID.

        Args:
            webhook_id: Webhook identifier
            delivery_id: Delivery identifier

        Returns:
            WebhookDelivery instance if found, None otherwise
        """
        return await self.delivery_repository.get_delivery(webhook_id, delivery_id)

