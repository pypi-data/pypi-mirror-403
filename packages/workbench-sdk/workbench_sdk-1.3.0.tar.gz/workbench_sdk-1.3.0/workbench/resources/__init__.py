"""Resource modules for the Workbench SDK."""

from workbench.resources.clients import ClientsResource
from workbench.resources.invoices import InvoicesResource
from workbench.resources.quotes import QuotesResource
from workbench.resources.jobs import JobsResource
from workbench.resources.service_requests import ServiceRequestsResource
from workbench.resources.webhooks import WebhooksResource
from workbench.resources.notifications import NotificationsResource
from workbench.resources.integrations import IntegrationsResource

__all__ = [
    "ClientsResource",
    "InvoicesResource",
    "QuotesResource",
    "JobsResource",
    "ServiceRequestsResource",
    "WebhooksResource",
    "NotificationsResource",
    "IntegrationsResource",
]
