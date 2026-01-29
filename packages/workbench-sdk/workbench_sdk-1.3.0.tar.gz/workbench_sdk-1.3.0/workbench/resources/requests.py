"""
Requests resource for the Workbench SDK.

Provides methods for managing service requests in Workbench CRM.
"""

from typing import TYPE_CHECKING, Any, Dict, Optional

from workbench.types import (
    ServiceRequest,
    ServiceRequestStatus,
    ServiceRequestPriority,
    ApiResponse,
    ListResponse,
)

if TYPE_CHECKING:
    from workbench.client import WorkbenchClient


class RequestsResource:
    """
    Requests resource for managing service requests.

    Example:
        >>> client = WorkbenchClient(api_key="wbk_live_xxx")
        >>>
        >>> # Create a service request
        >>> request = client.requests.create(
        ...     title="AC Not Cooling",
        ...     contact_name="John Doe",
        ...     contact_email="john@example.com",
        ...     address="123 Main St",
        ...     priority="urgent"
        ... )
        >>>
        >>> # Update request status
        >>> client.requests.update(request["data"]["id"], status="scheduled")
    """

    def __init__(self, client: "WorkbenchClient"):
        self._client = client

    def list(
        self,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
        search: Optional[str] = None,
        sort: Optional[str] = None,
        order: Optional[str] = None,
        status: Optional[ServiceRequestStatus] = None,
        priority: Optional[ServiceRequestPriority] = None,
        client_id: Optional[str] = None,
    ) -> ListResponse[ServiceRequest]:
        """
        List all requests.

        Args:
            page: Page number (1-indexed, default: 1)
            per_page: Items per page (1-100, default: 20)
            search: Search query
            sort: Field to sort by
            order: Sort order ("asc" or "desc")
            status: Filter by status
            priority: Filter by priority
            client_id: Filter by client ID

        Returns:
            Paginated list of requests
        """
        params: Dict[str, Any] = {
            "page": page,
            "per_page": per_page,
            "search": search,
            "sort": sort,
            "order": order,
            "status": status,
            "priority": priority,
            "client_id": client_id,
        }
        return self._client.get("/v1/requests", params=params)  # type: ignore

    def get(self, id: str) -> ApiResponse[ServiceRequest]:
        """
        Get a request by ID.

        Args:
            id: Request UUID

        Returns:
            Request details
        """
        return self._client.get(f"/v1/requests/{id}")  # type: ignore

    def create(
        self,
        title: str,
        client_id: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[ServiceRequestStatus] = None,
        source: Optional[str] = None,
        priority: Optional[ServiceRequestPriority] = None,
        requested_date: Optional[str] = None,
        preferred_time: Optional[str] = None,
        address: Optional[str] = None,
        contact_name: Optional[str] = None,
        contact_email: Optional[str] = None,
        contact_phone: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> ApiResponse[ServiceRequest]:
        """
        Create a new request.

        Args:
            title: Request title (required)
            client_id: Client UUID
            description: Request description
            status: Request status
            source: Request source
            priority: Request priority
            requested_date: Requested service date
            preferred_time: Preferred time slot
            address: Service address
            contact_name: Contact name
            contact_email: Contact email
            contact_phone: Contact phone
            notes: Additional notes

        Returns:
            Created request
        """
        data: Dict[str, Any] = {
            "title": title,
            "client_id": client_id,
            "description": description,
            "status": status,
            "source": source,
            "priority": priority,
            "requested_date": requested_date,
            "preferred_time": preferred_time,
            "address": address,
            "contact_name": contact_name,
            "contact_email": contact_email,
            "contact_phone": contact_phone,
            "notes": notes,
        }
        data = {k: v for k, v in data.items() if v is not None or k == "title"}
        return self._client.post("/v1/requests", json=data)  # type: ignore

    def update(self, id: str, **kwargs: Any) -> ApiResponse[ServiceRequest]:
        """
        Update a request.

        Args:
            id: Request UUID
            **kwargs: Fields to update

        Returns:
            Updated request
        """
        data = {k: v for k, v in kwargs.items() if v is not None}
        return self._client.put(f"/v1/requests/{id}", json=data)  # type: ignore

    def delete(self, id: str) -> None:
        """
        Delete a request.

        Args:
            id: Request UUID
        """
        self._client.delete(f"/v1/requests/{id}")
