"""Webhook repository interfaces and implementations."""

import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
from aiofiles import os as aios

from task_framework.interfaces.database import Database
from task_framework.models.webhook import Webhook, WebhookDelivery


class WebhookRepository(ABC):
    """Abstract base class for webhook storage."""

    @abstractmethod
    async def create_webhook(self, webhook: Webhook) -> None:
        """Create a new webhook.

        Args:
            webhook: Webhook instance to store
        """
        pass

    @abstractmethod
    async def get_webhook(self, webhook_id: str) -> Optional[Webhook]:
        """Get a webhook by ID.

        Args:
            webhook_id: Webhook identifier

        Returns:
            Webhook instance if found, None otherwise
        """
        pass

    @abstractmethod
    async def update_webhook(self, webhook: Webhook) -> None:
        """Update an existing webhook.

        Args:
            webhook: Webhook instance with updated data
        """
        pass

    @abstractmethod
    async def delete_webhook(self, webhook_id: str) -> None:
        """Delete a webhook.

        Args:
            webhook_id: Webhook identifier to delete
        """
        pass

    @abstractmethod
    async def list_webhooks(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[Webhook]:
        """List webhooks with optional filtering.

        Args:
            filters: Optional filter dictionary containing:
                - is_enabled: Optional[bool] - Filter by enabled status
                - limit: Optional[int] - Maximum number of results
                - cursor: Optional[str] - Pagination cursor

        Returns:
            List of Webhook instances matching filters
        """
        pass


class WebhookDeliveryRepository(ABC):
    """Abstract base class for webhook delivery audit log storage."""

    @abstractmethod
    async def create_delivery(self, delivery: WebhookDelivery) -> None:
        """Create a new delivery record.

        Args:
            delivery: WebhookDelivery instance to store
        """
        pass

    @abstractmethod
    async def get_delivery(self, webhook_id: str, delivery_id: str) -> Optional[WebhookDelivery]:
        """Get a delivery record by ID.

        Args:
            webhook_id: Webhook identifier
            delivery_id: Delivery identifier

        Returns:
            WebhookDelivery instance if found, None otherwise
        """
        pass

    @abstractmethod
    async def list_deliveries(
        self, webhook_id: str, filters: Optional[Dict[str, Any]] = None
    ) -> List[WebhookDelivery]:
        """List delivery records for a webhook.

        Args:
            webhook_id: Webhook identifier
            filters: Optional filter dictionary containing:
                - status: Optional[str] - Filter by delivery status ("success" | "failed")
                - thread_id: Optional[str] - Filter by thread ID
                - limit: Optional[int] - Maximum number of results
                - cursor: Optional[str] - Pagination cursor

        Returns:
            List of WebhookDelivery instances matching filters
        """
        pass


class FileWebhookRepository(WebhookRepository):
    """File-based webhook repository implementation."""

    def __init__(self, base_path: str = "data") -> None:
        """Initialize FileWebhookRepository.

        Args:
            base_path: Base directory for storing data files
        """
        self.base_path = Path(base_path)
        self.webhooks_dir = self.base_path / "webhooks"

    async def _ensure_directories(self) -> None:
        """Ensure webhooks directory exists."""
        await aios.makedirs(self.webhooks_dir, exist_ok=True)

    async def create_webhook(self, webhook: Webhook) -> None:
        """Create a new webhook.

        Args:
            webhook: Webhook instance to store
        """
        await self._ensure_directories()
        file_path = self.webhooks_dir / f"{webhook.id}.json"

        async with aiofiles.open(file_path, "w") as f:
            await f.write(webhook.model_dump_json(exclude_none=False))

    async def get_webhook(self, webhook_id: str) -> Optional[Webhook]:
        """Get a webhook by ID.

        Args:
            webhook_id: Webhook identifier

        Returns:
            Webhook instance if found, None otherwise
        """
        file_path = self.webhooks_dir / f"{webhook_id}.json"

        if not await aios.path.exists(file_path):
            return None

        async with aiofiles.open(file_path, "r") as f:
            content = await f.read()
            data = json.loads(content)
            return Webhook.model_validate(data)

    async def update_webhook(self, webhook: Webhook) -> None:
        """Update an existing webhook.

        Args:
            webhook: Webhook instance with updated data
        """
        await self._ensure_directories()
        file_path = self.webhooks_dir / f"{webhook.id}.json"

        async with aiofiles.open(file_path, "w") as f:
            await f.write(webhook.model_dump_json(exclude_none=False))

    async def delete_webhook(self, webhook_id: str) -> None:
        """Delete a webhook.

        Args:
            webhook_id: Webhook identifier to delete
        """
        file_path = self.webhooks_dir / f"{webhook_id}.json"

        if await aios.path.exists(file_path):
            await aios.remove(file_path)

    async def list_webhooks(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[Webhook]:
        """List webhooks with optional filtering.

        Args:
            filters: Optional filter dictionary containing:
                - is_enabled: Optional[bool] - Filter by enabled status
                Note: limit and cursor are handled in service layer, not here

        Returns:
            List of Webhook instances matching filters (sorted by created_at descending)
        """
        await self._ensure_directories()

        webhooks: List[Webhook] = []

        # Read all webhook files
        if await aios.path.exists(self.webhooks_dir):
            async for file_path in self._list_webhook_files():
                webhook = await self.get_webhook(file_path.stem)
                if webhook:
                    webhooks.append(webhook)

        # Apply filters
        if filters:
            if "is_enabled" in filters and filters["is_enabled"] is not None:
                webhooks = [w for w in webhooks if w.enabled == filters["is_enabled"]]
            if "task_id" in filters and filters["task_id"] is not None:
                webhooks = [w for w in webhooks if w.task_id == filters["task_id"]]
            if "task_version" in filters and filters["task_version"] is not None:
                webhooks = [w for w in webhooks if w.task_version == filters["task_version"]]

        # Sort by created_at descending
        webhooks.sort(key=lambda w: w.created_at, reverse=True)

        return webhooks

    async def _list_webhook_files(self):
        """List webhook JSON files."""
        import os

        if await aios.path.exists(self.webhooks_dir):
            entries = await aios.listdir(self.webhooks_dir)
            for entry in entries:
                file_path = self.webhooks_dir / entry
                if entry.endswith(".json") and await aios.path.isfile(file_path):
                    yield file_path


class FileWebhookDeliveryRepository(WebhookDeliveryRepository):
    """File-based webhook delivery repository implementation."""

    def __init__(self, base_path: str = "data") -> None:
        """Initialize FileWebhookDeliveryRepository.

        Args:
            base_path: Base directory for storing data files
        """
        self.base_path = Path(base_path)
        self.deliveries_base_dir = self.base_path / "webhooks"

    async def _ensure_directories(self, webhook_id: str) -> None:
        """Ensure deliveries directory exists for a webhook.

        Args:
            webhook_id: Webhook identifier
        """
        deliveries_dir = self.deliveries_base_dir / webhook_id / "deliveries"
        await aios.makedirs(deliveries_dir, exist_ok=True)

    async def create_delivery(self, delivery: WebhookDelivery) -> None:
        """Create a new delivery record.

        Args:
            delivery: WebhookDelivery instance to store
        """
        await self._ensure_directories(delivery.webhook_id)
        file_path = (
            self.deliveries_base_dir / delivery.webhook_id / "deliveries" / f"{delivery.id}.json"
        )

        async with aiofiles.open(file_path, "w") as f:
            await f.write(delivery.model_dump_json(exclude_none=False))

    async def get_delivery(self, webhook_id: str, delivery_id: str) -> Optional[WebhookDelivery]:
        """Get a delivery record by ID.

        Args:
            webhook_id: Webhook identifier
            delivery_id: Delivery identifier

        Returns:
            WebhookDelivery instance if found, None otherwise
        """
        file_path = self.deliveries_base_dir / webhook_id / "deliveries" / f"{delivery_id}.json"

        if not await aios.path.exists(file_path):
            return None

        async with aiofiles.open(file_path, "r") as f:
            content = await f.read()
            data = json.loads(content)
            return WebhookDelivery.model_validate(data)

    async def list_deliveries(
        self, webhook_id: str, filters: Optional[Dict[str, Any]] = None
    ) -> List[WebhookDelivery]:
        """List delivery records for a webhook.

        Args:
            webhook_id: Webhook identifier
            filters: Optional filter dictionary containing:
                - status: Optional[str] - Filter by delivery status ("success" | "failed")
                - thread_id: Optional[str] - Filter by thread ID
                Note: limit and cursor are handled in service layer, not here

        Returns:
            List of WebhookDelivery instances matching filters (sorted by timestamp descending)
        """
        deliveries_dir = self.deliveries_base_dir / webhook_id / "deliveries"

        deliveries: List[WebhookDelivery] = []

        if await aios.path.exists(deliveries_dir):
            async for file_path in self._list_delivery_files(webhook_id):
                delivery = await self.get_delivery(webhook_id, file_path.stem)
                if delivery:
                    deliveries.append(delivery)

        # Apply filters
        if filters:
            if "status" in filters and filters["status"]:
                deliveries = [d for d in deliveries if d.status == filters["status"]]
            if "thread_id" in filters and filters["thread_id"]:
                deliveries = [d for d in deliveries if d.thread_id == filters["thread_id"]]

        # Sort by timestamp descending
        deliveries.sort(key=lambda d: d.timestamp, reverse=True)

        return deliveries

    async def _list_delivery_files(self, webhook_id: str):
        """List delivery JSON files for a webhook."""
        deliveries_dir = self.deliveries_base_dir / webhook_id / "deliveries"

        if await aios.path.exists(deliveries_dir):
            entries = await aios.listdir(deliveries_dir)
            for entry in entries:
                file_path = deliveries_dir / entry
                if entry.endswith(".json") and await aios.path.isfile(file_path):
                    yield file_path


