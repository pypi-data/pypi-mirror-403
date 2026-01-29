"""
Workbench SDK - Official Python SDK for the Workbench CRM API

Example usage:
    from workbench import WorkbenchClient

    client = WorkbenchClient(api_key="wbk_live_xxx")

    # List clients
    clients = client.clients.list(status="active")

    # Create an invoice
    invoice = client.invoices.create(
        client_id="client-uuid",
        items=[{"description": "Service", "quantity": 1, "unit_price": 100}]
    )
"""

from workbench.client import WorkbenchClient, WorkbenchError
from workbench.webhooks import (
    verify_webhook_signature,
    construct_webhook_event,
    WebhookVerificationError,
)
from workbench.types import (
    # Client types
    Client,
    ClientStatus,
    CreateClientParams,
    UpdateClientParams,
    ListClientsParams,
    # Invoice types
    Invoice,
    InvoiceItem,
    InvoiceStatus,
    CreateInvoiceParams,
    UpdateInvoiceParams,
    ListInvoicesParams,
    # Quote types
    Quote,
    QuoteItem,
    QuoteStatus,
    CreateQuoteParams,
    UpdateQuoteParams,
    ListQuotesParams,
    # Job types
    Job,
    JobStatus,
    JobPriority,
    CreateJobParams,
    UpdateJobParams,
    ListJobsParams,
    # Service Request types
    ServiceRequest,
    ServiceRequestStatus,
    ServiceRequestPriority,
    CreateServiceRequestParams,
    UpdateServiceRequestParams,
    ListServiceRequestsParams,
    # Webhook types
    Webhook,
    WebhookDelivery,
    WebhookEvent,
    CreateWebhookParams,
    UpdateWebhookParams,
    # Notification types
    NotificationType,
    NotificationEvent,
    BusinessUserRole,
    NotificationResult,
    SendToClientParams,
    SendToTeamParams,
    SendCustomNotificationParams,
    # Response types
    ApiResponse,
    ListResponse,
    Pagination,
)

__version__ = "1.2.1"
__all__ = [
    # Main client
    "WorkbenchClient",
    "WorkbenchError",
    # Webhook utilities
    "verify_webhook_signature",
    "construct_webhook_event",
    "WebhookVerificationError",
    # Types
    "Client",
    "ClientStatus",
    "CreateClientParams",
    "UpdateClientParams",
    "ListClientsParams",
    "Invoice",
    "InvoiceItem",
    "InvoiceStatus",
    "CreateInvoiceParams",
    "UpdateInvoiceParams",
    "ListInvoicesParams",
    "Quote",
    "QuoteItem",
    "QuoteStatus",
    "CreateQuoteParams",
    "UpdateQuoteParams",
    "ListQuotesParams",
    "Job",
    "JobStatus",
    "JobPriority",
    "CreateJobParams",
    "UpdateJobParams",
    "ListJobsParams",
    "ServiceRequest",
    "ServiceRequestStatus",
    "ServiceRequestPriority",
    "CreateServiceRequestParams",
    "UpdateServiceRequestParams",
    "ListServiceRequestsParams",
    "Webhook",
    "WebhookDelivery",
    "WebhookEvent",
    "CreateWebhookParams",
    "UpdateWebhookParams",
    # Notification types
    "NotificationType",
    "NotificationEvent",
    "BusinessUserRole",
    "NotificationResult",
    "SendToClientParams",
    "SendToTeamParams",
    "SendCustomNotificationParams",
    # Response types
    "ApiResponse",
    "ListResponse",
    "Pagination",
]
