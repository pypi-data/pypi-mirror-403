"""Webhook API endpoints."""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from task_framework.dependencies import AuthenticatedRequest, get_authenticated_request, get_framework
from task_framework.errors import WEBHOOK_INVALID_URL, WEBHOOK_NOT_FOUND, problem_json_dict
from task_framework.logging import logger
from task_framework.metrics import api_requests_total
from task_framework.models.webhook import (
    Webhook,
    WebhookCreateRequest,
    WebhookDelivery,
    WebhookDeliveryListResponse,
    WebhookListResponse,
    WebhookUpdateRequest,
)
from task_framework.services.webhook_service import WebhookService

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def get_webhook_service(
    framework: "TaskFramework" = Depends(get_framework),
) -> WebhookService:
    """Get WebhookService instance with dependencies from framework.

    Args:
        framework: TaskFramework instance injected via FastAPI dependency

    Returns:
        WebhookService instance using storage-factory-backed repositories
    """
    return WebhookService(
        webhook_repository=framework.webhook_repository,
        delivery_repository=framework.webhook_delivery_repository,
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=Webhook)
async def create_webhook(
    request: WebhookCreateRequest,
    auth: AuthenticatedRequest = Depends(get_authenticated_request),
    webhook_service: WebhookService = Depends(get_webhook_service),
) -> Webhook:
    """Create a new webhook subscription.

    Args:
        request: Webhook creation request
        auth: Authenticated request context
        webhook_service: WebhookService instance

    Returns:
        Created Webhook instance with generated secret

    Raises:
        HTTPException: 400 if validation fails
    """
    try:
        # Determine created_by from auth context
        created_by = auth.user_id or auth.app_id

        webhook = await webhook_service.create_webhook(request, created_by=created_by)

        # Log webhook creation
        logger.info(
            "webhook.created",
            webhook_id=webhook.id,
            url=webhook.url,
            enabled=webhook.enabled,
            created_by=created_by,
        )

        api_requests_total.labels(method="POST", endpoint="/webhooks", status="201").inc()
        return webhook

    except ValueError as e:
        error_msg = str(e)
        if "url" in error_msg.lower():
            api_requests_total.labels(method="POST", endpoint="/webhooks", status="400").inc()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=problem_json_dict(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    title="Bad Request",
                    detail=error_msg,
                    code=WEBHOOK_INVALID_URL,
                ),
            )
        api_requests_total.labels(method="POST", endpoint="/webhooks", status="400").inc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=problem_json_dict(
                status_code=status.HTTP_400_BAD_REQUEST,
                title="Bad Request",
                detail=error_msg,
                code="VALIDATION_FAILED",
            ),
        )


@router.get("", response_model=WebhookListResponse)
async def list_webhooks(
    is_enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    task_id: Optional[str] = Query(None, description="Filter by task ID"),
    task_version: Optional[str] = Query(None, description="Filter by task version"),
    source: Optional[str] = Query(None, description="Filter by webhook source (manual, thread, schedule)"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Page size"),
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    offset: Optional[int] = Query(None, ge=0, description="Offset for pagination"),
    auth: AuthenticatedRequest = Depends(get_authenticated_request),
    webhook_service: WebhookService = Depends(get_webhook_service),
) -> WebhookListResponse:
    """List webhooks with optional filtering.

    Args:
        is_enabled: Filter by enabled status
        task_id: Filter by task ID
        task_version: Filter by task version
        source: Filter by webhook source (manual, thread, schedule)
        limit: Page size (1-1000, default: 50)
        cursor: Pagination cursor
        offset: Offset for pagination (alternative to cursor)
        auth: Authenticated request context
        webhook_service: WebhookService instance

    Returns:
        WebhookListResponse with paginated results
    """
    response = await webhook_service.list_webhooks(
        is_enabled=is_enabled,
        task_id=task_id,
        task_version=task_version,
        source=source,
        limit=limit,
        cursor=cursor,
        offset=offset,
    )

    api_requests_total.labels(method="GET", endpoint="/webhooks", status="200").inc()
    return response


@router.get("/{webhook_id}", response_model=Webhook)
async def get_webhook(
    webhook_id: str,
    auth: AuthenticatedRequest = Depends(get_authenticated_request),
    webhook_service: WebhookService = Depends(get_webhook_service),
) -> Webhook:
    """Get webhook details by ID.

    Args:
        webhook_id: Webhook identifier
        auth: Authenticated request context
        webhook_service: WebhookService instance

    Returns:
        Webhook instance

    Raises:
        HTTPException: 404 if webhook not found
    """
    webhook = await webhook_service.get_webhook(webhook_id)

    if not webhook:
        api_requests_total.labels(method="GET", endpoint=f"/webhooks/{webhook_id}", status="404").inc()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=problem_json_dict(
                status_code=status.HTTP_404_NOT_FOUND,
                title="Not Found",
                detail=f"Webhook {webhook_id} not found",
                code=WEBHOOK_NOT_FOUND,
            ),
        )

    api_requests_total.labels(method="GET", endpoint=f"/webhooks/{webhook_id}", status="200").inc()
    return webhook


@router.patch("/{webhook_id}", response_model=Webhook)
async def update_webhook(
    webhook_id: str,
    request: WebhookUpdateRequest,
    auth: AuthenticatedRequest = Depends(get_authenticated_request),
    webhook_service: WebhookService = Depends(get_webhook_service),
) -> Webhook:
    """Update webhook configuration (partial update).

    Args:
        webhook_id: Webhook identifier
        request: Webhook update request (partial)
        auth: Authenticated request context
        webhook_service: WebhookService instance

    Returns:
        Updated Webhook instance

    Raises:
        HTTPException: 400 if validation fails, 404 if webhook not found
    """
    try:
        webhook = await webhook_service.update_webhook(webhook_id, request)

        api_requests_total.labels(method="PATCH", endpoint=f"/webhooks/{webhook_id}", status="200").inc()
        return webhook

    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            api_requests_total.labels(method="PATCH", endpoint=f"/webhooks/{webhook_id}", status="404").inc()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=problem_json_dict(
                    status_code=status.HTTP_404_NOT_FOUND,
                    title="Not Found",
                    detail=error_msg,
                    code=WEBHOOK_NOT_FOUND,
                ),
            )
        api_requests_total.labels(method="PATCH", endpoint=f"/webhooks/{webhook_id}", status="400").inc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=problem_json_dict(
                status_code=status.HTTP_400_BAD_REQUEST,
                title="Bad Request",
                detail=error_msg,
                code=WEBHOOK_INVALID_URL if "url" in error_msg.lower() else "VALIDATION_FAILED",
            ),
        )


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: str,
    auth: AuthenticatedRequest = Depends(get_authenticated_request),
    webhook_service: WebhookService = Depends(get_webhook_service),
) -> Response:
    """Delete webhook and stop all deliveries.

    Args:
        webhook_id: Webhook identifier
        auth: Authenticated request context
        webhook_service: WebhookService instance

    Returns:
        204 No Content

    Raises:
        HTTPException: 404 if webhook not found
    """
    try:
        await webhook_service.delete_webhook(webhook_id)

        api_requests_total.labels(method="DELETE", endpoint=f"/webhooks/{webhook_id}", status="204").inc()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except ValueError as e:
        error_msg = str(e)
        api_requests_total.labels(method="DELETE", endpoint=f"/webhooks/{webhook_id}", status="404").inc()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=problem_json_dict(
                status_code=status.HTTP_404_NOT_FOUND,
                title="Not Found",
                detail=error_msg,
                code=WEBHOOK_NOT_FOUND,
            ),
        )


@router.post("/{webhook_id}:regenerate-secret", response_model=Webhook)
async def regenerate_webhook_secret(
    webhook_id: str,
    auth: AuthenticatedRequest = Depends(get_authenticated_request),
    webhook_service: WebhookService = Depends(get_webhook_service),
) -> Webhook:
    """Regenerate webhook secret.

    Args:
        webhook_id: Webhook identifier
        auth: Authenticated request context
        webhook_service: WebhookService instance

    Returns:
        Updated Webhook instance with new secret

    Raises:
        HTTPException: 404 if webhook not found
    """
    try:
        webhook = await webhook_service.regenerate_secret(webhook_id)

        api_requests_total.labels(method="POST", endpoint=f"/webhooks/{webhook_id}:regenerate-secret", status="200").inc()
        return webhook

    except ValueError as e:
        error_msg = str(e)
        api_requests_total.labels(method="POST", endpoint=f"/webhooks/{webhook_id}:regenerate-secret", status="404").inc()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=problem_json_dict(
                status_code=status.HTTP_404_NOT_FOUND,
                title="Not Found",
                detail=error_msg,
                code=WEBHOOK_NOT_FOUND,
            ),
        )


@router.get("/{webhook_id}/deliveries", response_model=WebhookDeliveryListResponse)
async def list_webhook_deliveries(
    webhook_id: str,
    status: Optional[str] = Query(None, description="Filter by delivery status"),
    thread_id: Optional[str] = Query(None, description="Filter by thread ID"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Page size"),
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    offset: Optional[int] = Query(None, ge=0, description="Offset for pagination"),
    auth: AuthenticatedRequest = Depends(get_authenticated_request),
    webhook_service: WebhookService = Depends(get_webhook_service),
) -> WebhookDeliveryListResponse:
    """List delivery history for a webhook.

    Args:
        webhook_id: Webhook identifier
        status: Filter by delivery status ("success" | "failed")
        thread_id: Filter by thread ID
        limit: Page size (1-1000, default: 50)
        cursor: Pagination cursor
        offset: Offset for pagination (alternative to cursor)
        auth: Authenticated request context
        webhook_service: WebhookService instance

    Returns:
        WebhookDeliveryListResponse with paginated results
    """
    response = await webhook_service.list_deliveries(
        webhook_id=webhook_id,
        status=status,
        thread_id=thread_id,
        limit=limit,
        cursor=cursor,
        offset=offset,
    )

    api_requests_total.labels(method="GET", endpoint=f"/webhooks/{webhook_id}/deliveries", status="200").inc()
    return response


@router.get("/{webhook_id}/deliveries/{delivery_id}", response_model=WebhookDelivery)
async def get_webhook_delivery(
    webhook_id: str,
    delivery_id: str,
    auth: AuthenticatedRequest = Depends(get_authenticated_request),
    webhook_service: WebhookService = Depends(get_webhook_service),
) -> WebhookDelivery:
    """Get delivery details by ID.

    Args:
        webhook_id: Webhook identifier
        delivery_id: Delivery identifier
        auth: Authenticated request context
        webhook_service: WebhookService instance

    Returns:
        WebhookDelivery instance

    Raises:
        HTTPException: 404 if delivery not found
    """
    delivery = await webhook_service.get_delivery(webhook_id, delivery_id)

    if not delivery:
        api_requests_total.labels(
            method="GET", endpoint=f"/webhooks/{webhook_id}/deliveries/{delivery_id}", status="404"
        ).inc()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=problem_json_dict(
                status_code=status.HTTP_404_NOT_FOUND,
                title="Not Found",
                detail=f"Delivery {delivery_id} not found for webhook {webhook_id}",
                code="DELIVERY_NOT_FOUND",
            ),
        )

    api_requests_total.labels(method="GET", endpoint=f"/webhooks/{webhook_id}/deliveries/{delivery_id}", status="200").inc()
    return delivery

