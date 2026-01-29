"""
Webhooks resource for the Workbench SDK.

Provides methods for managing webhook subscriptions in Workbench CRM.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from workbench.types import (
    Webhook,
    WebhookDelivery,
    WebhookEvent,
    WebhookSecretResponse,
    WebhookEventTypeInfo,
    ApiResponse,
    ListResponse,
)

if TYPE_CHECKING:
    from workbench.client import WorkbenchClient


class WebhooksResource:
    """
    Webhooks resource.

    Example:
        >>> client = WorkbenchClient(api_key="wbk_live_xxx")
        >>>
        >>> # Create a webhook
        >>> webhook = client.webhooks.create(
        ...     name="Invoice Notifications",
        ...     url="https://example.com/webhooks/workbench",
        ...     events=["invoice.created", "invoice.paid"]
        ... )
        >>>
        >>> # Store the secret securely!
        >>> print(f"Webhook secret: {webhook['data']['secret']}")
    """

    def __init__(self, client: "WorkbenchClient"):
        self._client = client

    def list(
        self,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
    ) -> ListResponse[Webhook]:
        """
        List all webhooks.

        Args:
            page: Page number (1-indexed, default: 1)
            per_page: Items per page (1-100, default: 20)

        Returns:
            Paginated list of webhooks
        """
        params: Dict[str, Any] = {
            "page": page,
            "per_page": per_page,
        }
        return self._client.get("/v1/webhooks", params=params)  # type: ignore

    def get(self, id: str) -> ApiResponse[Webhook]:
        """
        Get a webhook by ID.

        Args:
            id: Webhook UUID

        Returns:
            Webhook details
        """
        return self._client.get(f"/v1/webhooks/{id}")  # type: ignore

    def create(
        self,
        name: str,
        url: str,
        events: List[WebhookEvent],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ApiResponse[Webhook]:
        """
        Create a new webhook.

        The webhook secret is returned in the response - store it securely
        to verify webhook signatures.

        Args:
            name: Webhook name
            url: Webhook endpoint URL
            events: List of events to subscribe to
            metadata: Optional custom metadata to attach to the webhook

        Returns:
            Created webhook (includes secret)
        """
        data: Dict[str, Any] = {
            "name": name,
            "url": url,
            "events": events,
        }
        if metadata is not None:
            data["metadata"] = metadata
        return self._client.post("/v1/webhooks", json=data)  # type: ignore

    def update(
        self,
        id: str,
        name: Optional[str] = None,
        url: Optional[str] = None,
        events: Optional[List[WebhookEvent]] = None,
        is_active: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ApiResponse[Webhook]:
        """
        Update a webhook.

        Args:
            id: Webhook UUID
            name: New webhook name
            url: New webhook URL
            events: New list of events
            is_active: Whether the webhook is active
            metadata: Custom metadata to attach to the webhook

        Returns:
            Updated webhook
        """
        data: Dict[str, Any] = {
            "name": name,
            "url": url,
            "events": events,
            "is_active": is_active,
            "metadata": metadata,
        }
        data = {k: v for k, v in data.items() if v is not None}
        return self._client.put(f"/v1/webhooks/{id}", json=data)  # type: ignore

    def delete(self, id: str) -> None:
        """
        Delete a webhook.

        Args:
            id: Webhook UUID
        """
        self._client.delete(f"/v1/webhooks/{id}")

    def list_deliveries(
        self,
        webhook_id: str,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
        event_type: Optional[WebhookEvent] = None,
    ) -> ListResponse[WebhookDelivery]:
        """
        List webhook deliveries.

        Args:
            webhook_id: Webhook UUID
            page: Page number (1-indexed, default: 1)
            per_page: Items per page (1-100, default: 20)
            event_type: Filter by event type

        Returns:
            Paginated list of delivery attempts
        """
        params: Dict[str, Any] = {
            "page": page,
            "per_page": per_page,
            "event_type": event_type,
        }
        return self._client.get(f"/v1/webhooks/{webhook_id}/deliveries", params=params)  # type: ignore

    def get_delivery(
        self,
        webhook_id: str,
        delivery_id: str,
    ) -> ApiResponse[WebhookDelivery]:
        """
        Get a single webhook delivery.

        Returns details about a specific delivery attempt, including
        request/response headers and timing information.

        Args:
            webhook_id: Webhook UUID
            delivery_id: Delivery UUID

        Returns:
            Delivery details
        """
        return self._client.get(f"/v1/webhooks/{webhook_id}/deliveries/{delivery_id}")  # type: ignore

    def test(self, id: str) -> ApiResponse[Dict[str, str]]:
        """
        Send a test webhook.

        Args:
            id: Webhook UUID

        Returns:
            Test delivery result with message and delivery_id
        """
        return self._client.post(f"/v1/webhooks/{id}/test")  # type: ignore

    def regenerate_secret(self, id: str) -> ApiResponse[WebhookSecretResponse]:
        """
        Regenerate webhook secret.

        Generates a new secret for the webhook. The old secret will
        immediately stop working. Make sure to update your webhook
        handler with the new secret.

        Args:
            id: Webhook UUID

        Returns:
            New webhook secret
        """
        return self._client.post(f"/v1/webhooks/{id}/secret")  # type: ignore

    def list_event_types(self) -> ApiResponse[List[WebhookEventTypeInfo]]:
        """
        List available webhook event types.

        Returns all event types that can be subscribed to, with
        descriptions and categories.

        Returns:
            List of available event types with descriptions
        """
        return self._client.get("/v1/webhooks/event-types")  # type: ignore
