"""Elasticsearch repositories package."""

from task_framework.repositories.elasticsearch.client import ElasticsearchClientFactory
from task_framework.repositories.elasticsearch.base import ElasticsearchRepository
from task_framework.repositories.elasticsearch.locks import (
    ElasticsearchDistributedLock,
    LockAcquisitionError,
)
from task_framework.repositories.elasticsearch.database import ElasticsearchDatabase
from task_framework.repositories.elasticsearch.webhook_db import (
    ElasticsearchWebhookRepository,
    ElasticsearchWebhookDeliveryRepository,
)
from task_framework.repositories.elasticsearch.task_registry_store import ElasticsearchTaskRegistryStore
from task_framework.repositories.elasticsearch.deployment_tracker import ElasticsearchDeploymentTracker
from task_framework.repositories.elasticsearch.idempotency import ElasticsearchIdempotencyStore
from task_framework.repositories.elasticsearch.index_manager import (
    ensure_all_indices,
    ensure_indices_on_startup,
)

__all__ = [
    "ElasticsearchClientFactory",
    "ElasticsearchRepository",
    "ElasticsearchDistributedLock",
    "LockAcquisitionError",
    "ElasticsearchDatabase",
    "ElasticsearchWebhookRepository",
    "ElasticsearchWebhookDeliveryRepository",
    "ElasticsearchTaskRegistryStore",
    "ElasticsearchDeploymentTracker",
    "ElasticsearchIdempotencyStore",
    "ensure_all_indices",
    "ensure_indices_on_startup",
]
