"""Webhook delivery engine for async HTTP delivery."""

import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx

from task_framework.delivery.event_publisher import WebhookEvent
from task_framework.delivery.payload_builder import build_webhook_payload
from task_framework.delivery.signature import generate_signature_header
from task_framework.logging import logger
from task_framework.metrics import webhook_delivery_duration_seconds, webhook_deliveries_total
from task_framework.models.webhook import Webhook, WebhookDelivery
from task_framework.repositories.webhook_db import WebhookDeliveryRepository, WebhookRepository
from task_framework.services.webhook_service import WebhookService


class DeliveryEngine:
    """Async webhook delivery engine."""

    def __init__(
        self,
        webhook_service: WebhookService,
        delivery_repository: WebhookDeliveryRepository,
        database: Optional[Any] = None,
        file_storage: Optional[Any] = None,
        timeout_seconds: int = 10,
    ) -> None:
        """Initialize delivery engine.

        Args:
            webhook_service: WebhookService for finding matching webhooks
            delivery_repository: WebhookDeliveryRepository for storing delivery records
            database: Database instance for loading artifacts (optional)
            file_storage: File storage instance for download URLs (optional)
            timeout_seconds: Default timeout for HTTP requests (default: 10)
        """
        self.webhook_service = webhook_service
        self.delivery_repository = delivery_repository
        self.database = database
        self.file_storage = file_storage
        self.timeout_seconds = timeout_seconds
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with connection pooling.

        Returns:
            httpx.AsyncClient instance
        """
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout_seconds, connect=5.0),
                limits=httpx.Limits(max_connections=100),
            )
        return self._http_client

    async def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def process_event(self, event: WebhookEvent) -> None:
        """Process a webhook event and deliver to matching webhooks.

        Args:
            event: WebhookEvent instance to process
        """
        # Get matching webhooks (from webhook repository)
        # This now includes schedule webhooks since they're stored as real webhook records
        # with scope.schedule_id and source='schedule'
        matching_webhooks = await self.webhook_service.get_matching_webhooks(
            event_type=event.event_type,
            thread_id=event.thread_id,
            run_id=event.run_id,
            metadata=event.metadata,
        )

        if not matching_webhooks:
            logger.debug(
                "webhook.no_matching_webhooks",
                event_type=event.event_type,
                thread_id=event.thread_id,
            )
            return

        # Deduplicate webhooks by URL to avoid sending duplicate HTTP requests
        # If multiple webhooks point to the same URL, only deliver once (use first webhook)
        seen_urls: Dict[str, Webhook] = {}
        for webhook in matching_webhooks:
            if webhook.url not in seen_urls:
                seen_urls[webhook.url] = webhook
            else:
                logger.debug(
                    "webhook.deduplicated",
                    webhook_id=webhook.id,
                    url=webhook.url,
                    event_type=event.event_type,
                    thread_id=event.thread_id,
                )

        # Deliver to each unique webhook URL
        for webhook in seen_urls.values():
            await self._deliver_to_webhook(webhook, event)

    async def _deliver_to_webhook(self, webhook: Webhook, event: WebhookEvent) -> None:
        """Deliver event to a specific webhook.

        Args:
            webhook: Webhook instance to deliver to
            event: WebhookEvent instance to deliver
        """
        from task_framework.utils.id_generator import generate_delivery_id
        delivery_id = generate_delivery_id()
        start_time = time.time()

        # Build payload with data filtering
        payload = await self._build_payload(webhook, event)

        # Create delivery record
        delivery = WebhookDelivery(
            id=delivery_id,
            webhook_id=webhook.id,
            event_type=event.event_type,
            event_payload=payload,
            thread_id=event.thread_id,
            run_id=event.run_id,
            timestamp=datetime.now(timezone.utc),
            status="failed",  # Will be updated on success
            delivery_url=webhook.url,
        )

        logger.info(
            "webhook.delivery.started",
            webhook_id=webhook.id,
            delivery_id=delivery_id,
            event_type=event.event_type,
            thread_id=event.thread_id,
        )

        try:
            # Get HTTP client
            client = await self._get_http_client()

            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "X-Task-Event-Type": event.event_type,
                "X-Task-Webhook-ID": webhook.id,
            }

            # Generate HMAC signature
            body_bytes = json.dumps(payload, sort_keys=True).encode('utf-8')
            _, signature_header = generate_signature_header(webhook.secret, body_bytes)
            headers["X-Task-Signature"] = signature_header

            # Add API key if configured
            if webhook.api_key:
                headers["X-API-Key"] = webhook.api_key

            # Make HTTP POST request
            timeout = httpx.Timeout(webhook.timeout_seconds or self.timeout_seconds, connect=5.0)
            response = await client.post(
                webhook.url,
                json=payload,
                headers=headers,
                timeout=timeout,
            )

            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)

            # Update delivery record
            delivery.status = "success"
            delivery.status_code = response.status_code
            delivery.response_time_ms = response_time_ms

            # Handle 410 Gone - disable webhook automatically
            if response.status_code == 410:
                logger.warning(
                    "webhook.disabled_410_gone",
                    webhook_id=webhook.id,
                    delivery_id=delivery_id,
                )
                webhook.enabled = False
                webhook.updated_at = datetime.now(timezone.utc)
                # Update webhook via storage-factory-based repository
                from task_framework.storage_factory import StorageFactory
                storage_factory = StorageFactory.from_env()
                webhook_repo = storage_factory.create_webhook_repository()
                await webhook_repo.update_webhook(webhook)

            # Update metrics
            webhook_deliveries_total.labels(webhook_id=webhook.id, status="success").inc()
            webhook_delivery_duration_seconds.observe((time.time() - start_time))

            logger.info(
                "webhook.delivery.completed",
                webhook_id=webhook.id,
                delivery_id=delivery_id,
                status="success",
                status_code=response.status_code,
                response_time_ms=response_time_ms,
            )

        except httpx.TimeoutException:
            # Handle timeout
            response_time_ms = int((time.time() - start_time) * 1000)
            delivery.status = "failed"
            delivery.error = "Request timeout"
            delivery.response_time_ms = response_time_ms

            webhook_deliveries_total.labels(webhook_id=webhook.id, status="failed").inc()
            webhook_delivery_duration_seconds.observe((time.time() - start_time))

            logger.error(
                "webhook.delivery.failed",
                webhook_id=webhook.id,
                delivery_id=delivery_id,
                error="Request timeout",
                status_code=None,
            )

        except httpx.RequestError as e:
            # Handle connection errors
            response_time_ms = int((time.time() - start_time) * 1000)
            delivery.status = "failed"
            delivery.error = str(e)
            delivery.response_time_ms = response_time_ms

            webhook_deliveries_total.labels(webhook_id=webhook.id, status="failed").inc()
            webhook_delivery_duration_seconds.observe((time.time() - start_time))

            logger.error(
                "webhook.delivery.failed",
                webhook_id=webhook.id,
                delivery_id=delivery_id,
                error=str(e),
                status_code=None,
            )

        except Exception as e:
            # Handle other errors
            response_time_ms = int((time.time() - start_time) * 1000)
            delivery.status = "failed"
            delivery.error = str(e)
            delivery.response_time_ms = response_time_ms

            webhook_deliveries_total.labels(webhook_id=webhook.id, status="failed").inc()
            webhook_delivery_duration_seconds.observe((time.time() - start_time))

            logger.error(
                "webhook.delivery.failed",
                webhook_id=webhook.id,
                delivery_id=delivery_id,
                error=str(e),
                error_type=type(e).__name__,
                status_code=None,
            )

        finally:
            # Store delivery record
            await self.delivery_repository.create_delivery(delivery)

    async def _build_payload(self, webhook: Webhook, event: WebhookEvent) -> Dict[str, Any]:
        """Build webhook payload from event with data filtering applied.

        Args:
            webhook: Webhook instance (contains data_filters)
            event: WebhookEvent instance

        Returns:
            Filtered payload dictionary
        """
        # Load artifacts if thread_id is available and database is available
        artifacts: Optional[List[Any]] = None
        if event.thread_id and self.database:
            try:
                artifacts = await self.database.get_thread_artifacts(event.thread_id)
            except Exception as e:
                logger.warning(
                    "webhook.payload.artifacts_load_failed",
                    thread_id=event.thread_id,
                    error=str(e),
                )

        # Build payload with data filtering
        payload = build_webhook_payload(
            event_type=event.event_type,
            timestamp=event.timestamp.isoformat() + "Z",
            thread_id=event.thread_id,
            run_id=event.run_id,
            thread=event.thread,
            metadata=event.metadata,
            artifacts=artifacts,
            data_filters=webhook.data_filters,
            file_storage=self.file_storage,
        )

        return payload

