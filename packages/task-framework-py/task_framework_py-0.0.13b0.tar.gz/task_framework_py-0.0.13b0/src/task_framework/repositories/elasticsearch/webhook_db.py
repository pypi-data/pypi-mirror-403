"""Elasticsearch implementation of WebhookRepository and WebhookDeliveryRepository."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from task_framework.logging import logger
from task_framework.models.webhook import Webhook, WebhookDelivery
from task_framework.repositories.elasticsearch.base import ElasticsearchRepository
from task_framework.repositories.elasticsearch.mappings import (
    DELIVERY_MAPPINGS,
    WEBHOOK_MAPPINGS,
)
from task_framework.repositories.webhook_db import (
    WebhookDeliveryRepository,
    WebhookRepository,
)


class ElasticsearchWebhookRepository(WebhookRepository):
    """Elasticsearch implementation of WebhookRepository."""
    
    def __init__(
        self,
        client: "AsyncElasticsearch",
        index_prefix: Optional[str] = None,
    ):
        """Initialize repository.
        
        Args:
            client: AsyncElasticsearch client
            index_prefix: Index prefix (default from env)
        """
        self._repo = _WebhookRepo(client, index_prefix)
    
    async def create_webhook(self, webhook: Webhook) -> None:
        """Create a new webhook."""
        await self._repo.ensure_index(WEBHOOK_MAPPINGS)
        await self._repo.create(webhook)
    
    async def get_webhook(self, webhook_id: str) -> Optional[Webhook]:
        """Get a webhook by ID."""
        await self._repo.ensure_index(WEBHOOK_MAPPINGS)
        return await self._repo.get(webhook_id)
    
    async def update_webhook(self, webhook: Webhook) -> None:
        """Update an existing webhook."""
        await self._repo.ensure_index(WEBHOOK_MAPPINGS)
        await self._repo.update(webhook)
    
    async def delete_webhook(self, webhook_id: str) -> None:
        """Delete a webhook."""
        await self._repo.ensure_index(WEBHOOK_MAPPINGS)
        await self._repo.delete(webhook_id)
    
    async def list_webhooks(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[Webhook]:
        """List webhooks with optional filtering."""
        await self._repo.ensure_index(WEBHOOK_MAPPINGS)
        return await self._repo.query(filters or {})


class ElasticsearchWebhookDeliveryRepository(WebhookDeliveryRepository):
    """Elasticsearch implementation of WebhookDeliveryRepository."""
    
    def __init__(
        self,
        client: "AsyncElasticsearch",
        index_prefix: Optional[str] = None,
    ):
        """Initialize repository.
        
        Args:
            client: AsyncElasticsearch client
            index_prefix: Index prefix (default from env)
        """
        self._repo = _DeliveryRepo(client, index_prefix)
    
    async def create_delivery(self, delivery: WebhookDelivery) -> None:
        """Create a new delivery record."""
        await self._repo.ensure_index(DELIVERY_MAPPINGS)
        await self._repo.create(delivery)
    
    async def get_delivery(
        self, webhook_id: str, delivery_id: str
    ) -> Optional[WebhookDelivery]:
        """Get a delivery record by ID."""
        await self._repo.ensure_index(DELIVERY_MAPPINGS)
        return await self._repo.get(delivery_id)
    
    async def list_deliveries(
        self, webhook_id: str, filters: Optional[Dict[str, Any]] = None
    ) -> List[WebhookDelivery]:
        """List delivery records for a webhook."""
        await self._repo.ensure_index(DELIVERY_MAPPINGS)
        query_filters = {"webhook_id": webhook_id}
        if filters:
            query_filters.update(filters)
        return await self._repo.query(query_filters)


class _WebhookRepo(ElasticsearchRepository[Webhook]):
    """Internal webhook repository."""
    
    INDEX_SUFFIX = "webhooks"
    
    def _to_doc(self, webhook: Webhook) -> Dict[str, Any]:
        """Convert Webhook to ES document."""
        doc = webhook.model_dump(mode="json", exclude_none=True)
        for field in ["created_at", "updated_at"]:
            if field in doc and doc[field]:
                if isinstance(doc[field], datetime):
                    doc[field] = self._datetime_to_iso(doc[field])
        return doc
    
    def _from_doc(self, doc: Dict[str, Any]) -> Webhook:
        """Convert ES document to Webhook."""
        return Webhook.model_validate(doc)
    
    async def create(self, webhook: Webhook) -> None:
        """Create webhook document."""
        await self._index_document(webhook.id, self._to_doc(webhook), refresh=True)
        logger.debug("elasticsearch.webhook.created", webhook_id=webhook.id)
    
    async def get(self, webhook_id: str) -> Optional[Webhook]:
        """Get webhook by ID."""
        doc = await self._get_document(webhook_id)
        return self._from_doc(doc) if doc else None
    
    async def update(self, webhook: Webhook) -> None:
        """Update webhook."""
        await self._index_document(webhook.id, self._to_doc(webhook), refresh=True)
    
    async def delete(self, webhook_id: str) -> None:
        """Delete webhook."""
        await self._delete_document(webhook_id, refresh=True)
    
    async def query(self, filters: Dict[str, Any]) -> List[Webhook]:
        """Query webhooks."""
        must_clauses = []
        
        if filters.get("is_enabled") is not None:
            must_clauses.append({"term": {"enabled": filters["is_enabled"]}})
        
        if filters.get("task_id"):
            must_clauses.append({"term": {"task_id": filters["task_id"]}})
        
        if filters.get("task_version"):
            must_clauses.append({"term": {"task_version": filters["task_version"]}})
        
        if filters.get("source"):
            must_clauses.append({"term": {"source": filters["source"]}})
        
        query = {"bool": {"must": must_clauses}} if must_clauses else {"match_all": {}}
        sort = [{"created_at": {"order": "desc"}}]
        size = filters.get("limit", 100)
        
        result = await self._search(query=query, sort=sort, size=size)
        
        return [
            self._from_doc(hit["_source"])
            for hit in result.get("hits", {}).get("hits", [])
        ]


class _DeliveryRepo(ElasticsearchRepository[WebhookDelivery]):
    """Internal delivery repository."""
    
    INDEX_SUFFIX = "deliveries"
    
    def _to_doc(self, delivery: WebhookDelivery) -> Dict[str, Any]:
        """Convert WebhookDelivery to ES document."""
        doc = delivery.model_dump(mode="json", exclude_none=True)
        if "timestamp" in doc and doc["timestamp"]:
            if isinstance(doc["timestamp"], datetime):
                doc["timestamp"] = self._datetime_to_iso(doc["timestamp"])
        return doc
    
    def _from_doc(self, doc: Dict[str, Any]) -> WebhookDelivery:
        """Convert ES document to WebhookDelivery."""
        return WebhookDelivery.model_validate(doc)
    
    async def create(self, delivery: WebhookDelivery) -> None:
        """Create delivery document."""
        await self._index_document(delivery.id, self._to_doc(delivery), refresh=True)
        logger.debug("elasticsearch.delivery.created", delivery_id=delivery.id)
    
    async def get(self, delivery_id: str) -> Optional[WebhookDelivery]:
        """Get delivery by ID."""
        doc = await self._get_document(delivery_id)
        return self._from_doc(doc) if doc else None
    
    async def query(self, filters: Dict[str, Any]) -> List[WebhookDelivery]:
        """Query deliveries."""
        must_clauses = []
        
        if filters.get("webhook_id"):
            must_clauses.append({"term": {"webhook_id": filters["webhook_id"]}})
        
        if filters.get("status"):
            must_clauses.append({"term": {"status": filters["status"]}})
        
        if filters.get("thread_id"):
            must_clauses.append({"term": {"thread_id": filters["thread_id"]}})
        
        query = {"bool": {"must": must_clauses}} if must_clauses else {"match_all": {}}
        sort = [{"timestamp": {"order": "desc"}}]
        size = filters.get("limit", 100)
        
        result = await self._search(query=query, sort=sort, size=size)
        
        return [
            self._from_doc(hit["_source"])
            for hit in result.get("hits", {}).get("hits", [])
        ]
