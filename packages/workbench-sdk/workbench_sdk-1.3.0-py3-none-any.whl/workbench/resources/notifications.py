"""
Notifications resource for the Workbench SDK.

Provides methods for sending email notifications to clients and
business team members via the Workbench API.

Example:
    >>> client = WorkbenchClient(api_key="wbk_live_xxx")
    >>>
    >>> # Send notification to a client
    >>> result = client.notifications.send_to_client(
    ...     client_id="client-uuid",
    ...     event="sdk_client_created",
    ...     template_data={"client_name": "John Doe"}
    ... )
    >>> print(f"Sent to {result['data']['sent_count']} recipient(s)")
    >>>
    >>> # Notify business team members
    >>> result = client.notifications.send_to_team(
    ...     event="sdk_request_created",
    ...     roles=["owner", "admin"],
    ...     template_data={"request_title": "AC Repair", "client_name": "John"}
    ... )
    >>>
    >>> # Send custom notification
    >>> result = client.notifications.send_custom(
    ...     type="CLIENT",
    ...     client_id="client-uuid",
    ...     subject="Your appointment is confirmed!",
    ...     html="<h1>Confirmed!</h1><p>See you tomorrow at 10am.</p>"
    ... )
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from workbench.types import (
    NotificationType,
    NotificationEvent,
    BusinessUserRole,
    NotificationResult,
    ApiResponse,
)

if TYPE_CHECKING:
    from workbench.client import WorkbenchClient


class NotificationsResource:
    """
    Notifications resource for sending email notifications.

    Supports sending notifications to:
    - Clients: Individual client notification via their email
    - Business team: Team members filtered by role

    Example:
        >>> client = WorkbenchClient(api_key="wbk_live_xxx")
        >>>
        >>> # Welcome notification to new client
        >>> result = client.notifications.send_to_client(
        ...     client_id="client-uuid",
        ...     event="sdk_client_created",
        ...     template_data={"client_name": "John"}
        ... )
    """

    def __init__(self, client: "WorkbenchClient"):
        """
        Initialize the notifications resource.

        Args:
            client: The WorkbenchClient instance
        """
        self._client = client

    def send_to_client(
        self,
        client_id: str,
        event: NotificationEvent,
        template_data: Optional[Dict[str, Any]] = None,
        subject_override: Optional[str] = None,
        html_override: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
    ) -> ApiResponse[NotificationResult]:
        """
        Send a notification to a specific client.

        Sends an email notification to a client using a predefined template
        or custom content. The client must have a valid email address.

        Args:
            client_id: The UUID of the client to notify (required)
            event: The notification event type (required)
            template_data: Variables to interpolate in the email template
            subject_override: Custom email subject (overrides template default)
            html_override: Custom HTML body (overrides template default)
            entity_type: Optional entity type for logging (e.g., "invoice")
            entity_id: Optional entity ID for logging context

        Returns:
            Notification result with delivery statistics

        Example:
            >>> result = client.notifications.send_to_client(
            ...     client_id="client-uuid",
            ...     event="sdk_quote_created",
            ...     template_data={
            ...         "client_name": "John",
            ...         "quote_number": "Q-001",
            ...         "quote_total": "$1,500.00"
            ...     },
            ...     subject_override="Your custom quote is ready!"
            ... )
            >>> print(f"Sent to {result['data']['sent_count']} recipients")
        """
        data: Dict[str, Any] = {
            "type": "CLIENT",
            "event": event,
            "client_id": client_id,
        }

        if template_data is not None:
            data["template_data"] = template_data
        if subject_override is not None:
            data["subject_override"] = subject_override
        if html_override is not None:
            data["html_override"] = html_override
        if entity_type is not None:
            data["entity_type"] = entity_type
        if entity_id is not None:
            data["entity_id"] = entity_id

        return self._client.post("/v1/notifications", json=data)  # type: ignore

    def send_to_team(
        self,
        event: NotificationEvent,
        roles: Optional[List[BusinessUserRole]] = None,
        template_data: Optional[Dict[str, Any]] = None,
        subject_override: Optional[str] = None,
        html_override: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
    ) -> ApiResponse[NotificationResult]:
        """
        Send a notification to business team members.

        Sends an email notification to team members, optionally filtered
        by their role in the business.

        Args:
            event: The notification event type (required)
            roles: List of roles to target (e.g., ["owner", "admin"]).
                   If None, all team members are notified.
            template_data: Variables to interpolate in the email template
            subject_override: Custom email subject (overrides template default)
            html_override: Custom HTML body (overrides template default)
            entity_type: Optional entity type for logging (e.g., "invoice")
            entity_id: Optional entity ID for logging context

        Returns:
            Notification result with delivery statistics

        Example:
            >>> # Notify all team members
            >>> result = client.notifications.send_to_team(
            ...     event="sdk_request_created",
            ...     template_data={
            ...         "request_title": "Emergency AC Repair",
            ...         "client_name": "John Doe"
            ...     }
            ... )
            >>>
            >>> # Notify only owners and admins
            >>> result = client.notifications.send_to_team(
            ...     event="sdk_invoice_created",
            ...     roles=["owner", "admin"],
            ...     template_data={
            ...         "invoice_number": "INV-001",
            ...         "invoice_total": "$2,500.00",
            ...         "client_name": "Acme Corp"
            ...     }
            ... )
        """
        data: Dict[str, Any] = {
            "type": "BUSINESS",
            "event": event,
        }

        if roles is not None:
            data["roles"] = roles
        if template_data is not None:
            data["template_data"] = template_data
        if subject_override is not None:
            data["subject_override"] = subject_override
        if html_override is not None:
            data["html_override"] = html_override
        if entity_type is not None:
            data["entity_type"] = entity_type
        if entity_id is not None:
            data["entity_id"] = entity_id

        return self._client.post("/v1/notifications", json=data)  # type: ignore

    def send_custom(
        self,
        type: NotificationType,
        subject: str,
        html: str,
        client_id: Optional[str] = None,
        roles: Optional[List[BusinessUserRole]] = None,
        template_data: Optional[Dict[str, Any]] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
    ) -> ApiResponse[NotificationResult]:
        """
        Send a custom notification with fully custom subject and HTML content.

        Can be sent to either a client or business team members.

        Args:
            type: Recipient type ("CLIENT" or "BUSINESS") (required)
            subject: Custom email subject (required)
            html: Custom HTML body (required)
            client_id: Client UUID (required if type is "CLIENT")
            roles: List of roles to target (for "BUSINESS" type)
            template_data: Additional template data for logging context
            entity_type: Optional entity type for logging
            entity_id: Optional entity ID for logging

        Returns:
            Notification result with delivery statistics

        Example:
            >>> # Send custom notification to client
            >>> result = client.notifications.send_custom(
            ...     type="CLIENT",
            ...     client_id="client-uuid",
            ...     subject="Your appointment is confirmed for tomorrow!",
            ...     html="<h1>Appointment Confirmed</h1><p>See you at 10am!</p>"
            ... )
            >>>
            >>> # Send custom alert to admins
            >>> result = client.notifications.send_custom(
            ...     type="BUSINESS",
            ...     roles=["owner", "admin"],
            ...     subject="High-value quote approved!",
            ...     html="<p>Quote Q-001 for $10,000 has been approved.</p>"
            ... )
        """
        data: Dict[str, Any] = {
            "type": type,
            "event": "sdk_custom",
            "subject_override": subject,
            "html_override": html,
        }

        if client_id is not None:
            data["client_id"] = client_id
        if roles is not None:
            data["roles"] = roles
        if template_data is not None:
            data["template_data"] = template_data
        if entity_type is not None:
            data["entity_type"] = entity_type
        if entity_id is not None:
            data["entity_id"] = entity_id

        return self._client.post("/v1/notifications", json=data)  # type: ignore
