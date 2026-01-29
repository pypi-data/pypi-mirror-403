"""
Type definitions for the Workbench SDK.

These types mirror the API response structures and provide
full type safety when working with the Workbench API.
"""

from datetime import datetime
from typing import Any, Dict, Generic, List, Literal, Optional, TypedDict, TypeVar
from typing_extensions import NotRequired

# ===========================================
# GENERIC TYPES
# ===========================================

T = TypeVar("T")


class Pagination(TypedDict, total=False):
    """
    Pagination information for list responses.
    Supports both page-based and offset-based pagination.
    """

    # Page-based pagination
    page: int
    per_page: int
    total_pages: int
    # Offset-based pagination
    limit: int
    offset: int
    # Common fields
    total: int
    has_more: bool


class ResponseMeta(TypedDict):
    """Standard API response metadata."""

    request_id: str
    timestamp: str


class ApiResponse(TypedDict, Generic[T]):
    """Standard API response wrapper for single items."""

    data: T
    meta: ResponseMeta


class ListResponse(TypedDict, Generic[T]):
    """Standard API response wrapper for lists."""

    data: List[T]
    meta: ResponseMeta
    pagination: Pagination


# ===========================================
# CLIENT TYPES
# ===========================================

# Client lifecycle status
ClientStatus = Literal["active", "inactive", "archived"]

# Lead pipeline stage
LeadStatus = Literal["new", "contacted", "qualified", "proposal", "negotiation", "won", "lost"]


class Client(TypedDict):
    """Client record."""

    id: str
    business_id: str
    first_name: str
    last_name: Optional[str]
    company: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    status: ClientStatus
    lead_status: Optional[LeadStatus]  # Lead pipeline stage
    source: Optional[str]
    notes: Optional[str]
    internal_notes: Optional[str]  # Internal notes visible only to business users
    tags: Optional[List[str]]
    next_contact_date: Optional[str]
    ask_for_review: Optional[bool]
    created_at: str
    updated_at: Optional[str]


class CreateClientParams(TypedDict):
    """Parameters for creating a client."""

    first_name: str
    last_name: NotRequired[Optional[str]]
    company: NotRequired[Optional[str]]
    email: NotRequired[Optional[str]]
    phone: NotRequired[Optional[str]]
    status: NotRequired[ClientStatus]  # Defaults to 'active'
    lead_status: NotRequired[Optional[LeadStatus]]  # Defaults to 'new'
    source: NotRequired[Optional[str]]
    notes: NotRequired[Optional[str]]
    internal_notes: NotRequired[Optional[str]]
    tags: NotRequired[Optional[List[str]]]


class UpdateClientParams(TypedDict, total=False):
    """Parameters for updating a client."""

    first_name: str
    last_name: Optional[str]
    company: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    status: ClientStatus
    lead_status: Optional[LeadStatus]
    source: Optional[str]
    notes: Optional[str]
    internal_notes: Optional[str]
    tags: Optional[List[str]]
    next_contact_date: Optional[str]
    ask_for_review: Optional[bool]


class ListClientsParams(TypedDict, total=False):
    """Parameters for listing clients."""

    page: int
    per_page: int
    limit: int
    offset: int
    search: str
    sort: str
    order: Literal["asc", "desc"]
    status: ClientStatus
    lead_status: LeadStatus


# ===========================================
# INVOICE TYPES
# ===========================================

InvoiceStatus = Literal[
    "draft", "sent", "viewed", "partial", "paid", "overdue", "cancelled", "voided"
]


class InvoiceItem(TypedDict):
    """Invoice line item."""

    id: NotRequired[str]
    description: str
    quantity: float
    unit_price: float
    sort_order: NotRequired[int]


class Invoice(TypedDict):
    """Invoice record."""

    id: str
    business_id: str
    client_id: Optional[str]
    job_id: Optional[str]
    invoice_number: str
    status: InvoiceStatus
    issue_date: str
    due_date: Optional[str]
    subtotal: float
    tax_rate: Optional[float]
    tax_amount: Optional[float]
    discount_amount: Optional[float]
    total: float
    amount_paid: float
    notes: Optional[str]
    terms: Optional[str]
    sent_at: Optional[str]  # Timestamp when the invoice was sent to the client
    paid_at: Optional[str]  # Timestamp when the invoice was fully paid
    items: List[InvoiceItem]
    client: NotRequired[Client]
    created_at: str
    updated_at: Optional[str]


class CreateInvoiceParams(TypedDict):
    """Parameters for creating an invoice."""

    items: List[InvoiceItem]
    client_id: NotRequired[Optional[str]]
    job_id: NotRequired[Optional[str]]
    status: NotRequired[InvoiceStatus]
    issue_date: NotRequired[str]
    due_date: NotRequired[Optional[str]]
    tax_rate: NotRequired[Optional[float]]
    discount_amount: NotRequired[Optional[float]]
    notes: NotRequired[Optional[str]]
    terms: NotRequired[Optional[str]]


class UpdateInvoiceParams(TypedDict, total=False):
    """Parameters for updating an invoice."""

    client_id: Optional[str]
    job_id: Optional[str]
    status: InvoiceStatus
    issue_date: str
    due_date: Optional[str]
    tax_rate: Optional[float]
    discount_amount: Optional[float]
    notes: Optional[str]
    terms: Optional[str]
    items: List[InvoiceItem]


class ListInvoicesParams(TypedDict, total=False):
    """Parameters for listing invoices."""

    page: int
    per_page: int
    limit: int
    offset: int
    search: str
    sort: str
    order: Literal["asc", "desc"]
    status: InvoiceStatus
    client_id: str


# ===========================================
# QUOTE TYPES
# ===========================================

QuoteStatus = Literal[
    "draft", "sent", "viewed", "approved", "rejected", "expired", "converted"
]


class QuoteItem(TypedDict):
    """Quote line item."""

    id: NotRequired[str]
    description: str
    quantity: float
    unit_price: float
    sort_order: NotRequired[int]


class Quote(TypedDict):
    """Quote record."""

    id: str
    business_id: str
    client_id: Optional[str]
    job_id: Optional[str]
    quote_number: str
    status: QuoteStatus
    issue_date: str
    valid_until: Optional[str]
    subtotal: float
    tax_rate: Optional[float]
    tax_amount: Optional[float]
    discount_amount: Optional[float]
    total: float
    notes: Optional[str]
    terms: Optional[str]
    sent_at: Optional[str]  # Timestamp when the quote was sent to the client
    approved_at: Optional[str]  # Timestamp when the quote was approved/accepted
    approved_by: Optional[str]  # User ID or name of who approved the quote
    items: List[QuoteItem]
    client: NotRequired[Client]
    created_at: str
    updated_at: Optional[str]


class CreateQuoteParams(TypedDict):
    """Parameters for creating a quote."""

    items: List[QuoteItem]
    client_id: NotRequired[Optional[str]]
    job_id: NotRequired[Optional[str]]
    status: NotRequired[QuoteStatus]
    issue_date: NotRequired[str]
    valid_until: NotRequired[Optional[str]]
    tax_rate: NotRequired[Optional[float]]
    discount_amount: NotRequired[Optional[float]]
    notes: NotRequired[Optional[str]]
    terms: NotRequired[Optional[str]]


class UpdateQuoteParams(TypedDict, total=False):
    """Parameters for updating a quote."""

    client_id: Optional[str]
    job_id: Optional[str]
    status: QuoteStatus
    issue_date: str
    valid_until: Optional[str]
    tax_rate: Optional[float]
    discount_amount: Optional[float]
    notes: Optional[str]
    terms: Optional[str]
    items: List[QuoteItem]


class ListQuotesParams(TypedDict, total=False):
    """Parameters for listing quotes."""

    page: int
    per_page: int
    limit: int
    offset: int
    search: str
    sort: str
    order: Literal["asc", "desc"]
    status: QuoteStatus
    client_id: str


# ===========================================
# JOB TYPES
# ===========================================

JobStatus = Literal[
    "draft", "scheduled", "in_progress", "on_hold", "completed", "cancelled", "invoiced", "closed"
]
JobPriority = Literal["low", "medium", "normal", "high", "urgent"]


class Job(TypedDict):
    """Job record."""

    id: str
    business_id: str
    client_id: Optional[str]
    job_number: Optional[str]  # Unique job number for display/reference
    title: str
    description: Optional[str]
    status: JobStatus
    priority: JobPriority
    scheduled_start: Optional[str]
    scheduled_end: Optional[str]
    actual_start: Optional[str]
    actual_end: Optional[str]
    estimated_duration: Optional[int]
    address_id: Optional[str]
    notes: Optional[str]
    client: NotRequired[Client]
    created_at: str
    updated_at: Optional[str]


class CreateJobParams(TypedDict):
    """Parameters for creating a job."""

    title: str
    client_id: NotRequired[Optional[str]]
    description: NotRequired[Optional[str]]
    status: NotRequired[JobStatus]
    priority: NotRequired[JobPriority]
    scheduled_start: NotRequired[Optional[str]]
    scheduled_end: NotRequired[Optional[str]]
    estimated_duration: NotRequired[Optional[int]]
    address_id: NotRequired[Optional[str]]
    notes: NotRequired[Optional[str]]


class UpdateJobParams(TypedDict, total=False):
    """Parameters for updating a job."""

    client_id: Optional[str]
    title: str
    description: Optional[str]
    status: JobStatus
    priority: JobPriority
    scheduled_start: Optional[str]
    scheduled_end: Optional[str]
    actual_start: Optional[str]
    actual_end: Optional[str]
    estimated_duration: Optional[int]
    address_id: Optional[str]
    notes: Optional[str]


class ListJobsParams(TypedDict, total=False):
    """Parameters for listing jobs."""

    page: int
    per_page: int
    limit: int
    offset: int
    search: str
    sort: str
    order: Literal["asc", "desc"]
    status: JobStatus
    priority: JobPriority
    client_id: str


# ===========================================
# SERVICE REQUEST TYPES
# ===========================================

ServiceRequestStatus = Literal[
    "new", "in_progress", "assessment_complete", "completed", "cancelled"
]
ServiceRequestPriority = Literal["low", "medium", "high", "urgent"]


class ServiceRequest(TypedDict):
    """Service request record."""

    id: str
    business_id: str
    client_id: Optional[str]
    request_number: str  # Unique request number for display/reference (auto-generated)
    title: str
    description: Optional[str]
    status: ServiceRequestStatus
    source: Optional[str]
    priority: Optional[ServiceRequestPriority]
    requested_date: Optional[str]
    preferred_time: Optional[str]
    address: Optional[str]
    contact_name: Optional[str]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    notes: Optional[str]
    client: NotRequired[Client]
    created_at: str
    updated_at: Optional[str]


class CreateServiceRequestParams(TypedDict):
    """Parameters for creating a service request."""

    title: str
    client_id: NotRequired[Optional[str]]
    description: NotRequired[Optional[str]]
    status: NotRequired[ServiceRequestStatus]
    source: NotRequired[Optional[str]]
    priority: NotRequired[Optional[ServiceRequestPriority]]
    requested_date: NotRequired[Optional[str]]
    preferred_time: NotRequired[Optional[str]]
    address: NotRequired[Optional[str]]
    contact_name: NotRequired[Optional[str]]
    contact_email: NotRequired[Optional[str]]
    contact_phone: NotRequired[Optional[str]]
    notes: NotRequired[Optional[str]]


class UpdateServiceRequestParams(TypedDict, total=False):
    """Parameters for updating a service request."""

    client_id: Optional[str]
    title: str
    description: Optional[str]
    status: ServiceRequestStatus
    source: Optional[str]
    priority: Optional[ServiceRequestPriority]
    requested_date: Optional[str]
    preferred_time: Optional[str]
    address: Optional[str]
    contact_name: Optional[str]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    notes: Optional[str]


class ListServiceRequestsParams(TypedDict, total=False):
    """Parameters for listing service requests."""

    page: int
    per_page: int
    limit: int
    offset: int
    search: str
    sort: str
    order: Literal["asc", "desc"]
    status: ServiceRequestStatus
    priority: ServiceRequestPriority
    client_id: str


# ===========================================
# WEBHOOK TYPES
# ===========================================

WebhookEvent = Literal[
    # Client events
    "client.created",
    "client.updated",
    "client.deleted",
    # Invoice events
    "invoice.created",
    "invoice.updated",
    "invoice.sent",
    "invoice.viewed",
    "invoice.paid",
    "invoice.overdue",
    "invoice.voided",
    # Quote events
    "quote.created",
    "quote.updated",
    "quote.sent",
    "quote.viewed",
    "quote.accepted",
    "quote.rejected",
    "quote.expired",
    # Job events
    "job.created",
    "job.updated",
    "job.status_changed",
    "job.completed",
    "job.cancelled",
    # Service request events
    "service_request.created",
    "service_request.updated",
    "service_request.assigned",
    "service_request.completed",
]

WebhookEventCategory = Literal[
    "client", "invoice", "quote", "job", "service_request"
]


class Webhook(TypedDict):
    """Webhook subscription."""

    id: str
    business_id: str
    name: str
    url: str
    events: List[WebhookEvent]
    secret: str
    is_active: bool
    metadata: Optional[Dict[str, Any]]  # Custom metadata attached to the webhook
    failure_count: int  # Number of consecutive delivery failures
    last_triggered_at: Optional[str]  # Timestamp of the last webhook trigger
    last_success_at: Optional[str]  # Timestamp of the last successful delivery
    last_failure_at: Optional[str]  # Timestamp of the last failed delivery
    created_by: Optional[str]  # User ID who created the webhook
    created_at: str
    updated_at: Optional[str]


class WebhookDelivery(TypedDict):
    """Webhook delivery record."""

    id: str
    webhook_id: str
    event_id: str  # Unique event ID for idempotency
    event_type: WebhookEvent
    payload: Dict[str, Any]
    request_headers: Optional[Dict[str, str]]  # Headers sent with the webhook request
    response_status: Optional[int]
    response_headers: Optional[Dict[str, str]]  # Headers received in the response
    response_body: Optional[str]
    response_time_ms: Optional[int]  # Response time in milliseconds
    attempt_count: int
    max_attempts: int  # Maximum number of delivery attempts
    next_retry_at: Optional[str]
    delivered_at: Optional[str]
    failed_at: Optional[str]
    error_message: Optional[str]  # Error message if delivery failed
    created_at: str


class CreateWebhookParams(TypedDict):
    """Parameters for creating a webhook."""

    name: str
    url: str
    events: List[WebhookEvent]
    metadata: NotRequired[Optional[Dict[str, Any]]]


class UpdateWebhookParams(TypedDict, total=False):
    """Parameters for updating a webhook."""

    name: str
    url: str
    events: List[WebhookEvent]
    is_active: bool
    metadata: Optional[Dict[str, Any]]


class ListWebhookDeliveriesParams(TypedDict, total=False):
    """Parameters for listing webhook deliveries."""

    page: int
    per_page: int
    limit: int
    offset: int
    event_type: WebhookEvent
    status: Literal["pending", "delivered", "failed"]


class WebhookSecretResponse(TypedDict):
    """Response from regenerating a webhook secret."""

    secret: str


class WebhookEventTypeInfo(TypedDict):
    """Webhook event type information."""

    event: WebhookEvent
    description: str
    category: WebhookEventCategory


# ===========================================
# NOTIFICATION TYPES
# ===========================================

NotificationType = Literal["CLIENT", "BUSINESS"]
"""Type of notification recipient: CLIENT (to a client) or BUSINESS (to team members)."""

NotificationEvent = Literal[
    "sdk_client_created",
    "sdk_request_created",
    "sdk_quote_created",
    "sdk_invoice_created",
    "sdk_job_created",
    "sdk_custom",
]
"""Notification events triggered by SDK operations."""

BusinessUserRole = Literal["owner", "admin", "manager", "member"]
"""Business team member role for targeting notifications."""


class NotificationResult(TypedDict):
    """Result of sending a notification."""

    notification_id: str
    recipients_count: int
    sent_count: int
    failed_count: int


class SendToClientParams(TypedDict):
    """Parameters for sending a notification to a client."""

    client_id: str
    event: NotificationEvent
    template_data: NotRequired[Optional[Dict[str, Any]]]
    subject_override: NotRequired[Optional[str]]
    html_override: NotRequired[Optional[str]]
    entity_type: NotRequired[Optional[str]]
    entity_id: NotRequired[Optional[str]]


class SendToTeamParams(TypedDict):
    """Parameters for sending a notification to business team members."""

    event: NotificationEvent
    roles: NotRequired[Optional[List[BusinessUserRole]]]
    template_data: NotRequired[Optional[Dict[str, Any]]]
    subject_override: NotRequired[Optional[str]]
    html_override: NotRequired[Optional[str]]
    entity_type: NotRequired[Optional[str]]
    entity_id: NotRequired[Optional[str]]


class SendCustomNotificationParams(TypedDict):
    """Parameters for sending a custom notification."""

    type: NotificationType
    subject: str
    html: str
    client_id: NotRequired[Optional[str]]
    roles: NotRequired[Optional[List[BusinessUserRole]]]
    template_data: NotRequired[Optional[Dict[str, Any]]]
    entity_type: NotRequired[Optional[str]]
    entity_id: NotRequired[Optional[str]]


# ===========================================
# INTEGRATION MARKETPLACE TYPES
# ===========================================

IntegrationStatus = Literal[
    "draft", "pending_review", "published", "rejected", "suspended"
]
"""Integration status values."""

IntegrationCategory = Literal[
    "accounting",
    "analytics",
    "automation",
    "communication",
    "crm",
    "ecommerce",
    "marketing",
    "payments",
    "productivity",
    "scheduling",
    "other",
]
"""Integration category values for filtering/discovery."""


class IntegrationScope(TypedDict):
    """OAuth scope information for an integration."""

    scope: str  # Scope identifier (e.g., 'clients:read')
    description: str  # Human-readable description of what the scope allows
    required: bool  # Whether this scope is required for the integration


class IntegrationDeveloper(TypedDict):
    """Developer/company information for an integration."""

    id: str
    name: str
    website: Optional[str]
    verified: bool


class Integration(TypedDict):
    """Published integration in the marketplace."""

    id: str
    slug: str  # URL-friendly identifier
    name: str
    short_description: str  # Max 200 chars
    description: str  # Full description with markdown support
    category: IntegrationCategory
    icon_url: Optional[str]
    website_url: Optional[str]
    support_email: Optional[str]
    privacy_policy_url: Optional[str]
    terms_url: Optional[str]
    scopes: List[IntegrationScope]
    webhook_events: List[WebhookEvent]
    install_count: int
    average_rating: Optional[float]  # 1-5
    review_count: int
    developer: IntegrationDeveloper
    published_at: str
    created_at: str
    updated_at: Optional[str]


class IntegrationReview(TypedDict):
    """Integration review from a user."""

    id: str
    integration_id: str
    rating: int  # 1-5
    title: Optional[str]
    content: Optional[str]
    reviewer_name: str
    created_at: str


class ListIntegrationsParams(TypedDict, total=False):
    """Parameters for listing integrations."""

    page: int
    per_page: int
    search: str
    category: IntegrationCategory
    scope: str  # Filter by scope
    sort_by: Literal["popular", "recent", "rating", "name"]


class ListIntegrationReviewsParams(TypedDict, total=False):
    """Parameters for listing integration reviews."""

    page: int
    per_page: int
    min_rating: int


class InstalledIntegration(TypedDict):
    """Installed integration on a business account."""

    id: str
    integration_id: str
    integration: Integration
    access_token_prefix: str  # Masked for security
    granted_scopes: List[str]
    installed_at: str
    installed_by: Optional[str]
    is_active: bool


class InstallIntegrationParams(TypedDict):
    """Parameters for installing an integration."""

    integration_id: str
    scopes: List[str]  # Must be subset of integration's requested scopes
    authorization_code: str  # From OAuth consent flow
    code_verifier: str  # PKCE code verifier


class SubmitReviewParams(TypedDict):
    """Parameters for submitting an integration review."""

    rating: int  # 1-5
    title: NotRequired[Optional[str]]
    content: NotRequired[Optional[str]]
