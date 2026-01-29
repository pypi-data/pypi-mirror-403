"""
Clients resource for the Workbench SDK.

Provides methods for managing clients in Workbench CRM.
"""

from typing import TYPE_CHECKING, Any, Dict, Optional

from workbench.types import (
    Client,
    ClientStatus,
    CreateClientParams,
    UpdateClientParams,
    ApiResponse,
    ListResponse,
)

if TYPE_CHECKING:
    from workbench.client import WorkbenchClient


class ClientsResource:
    """
    Clients resource.

    Example:
        >>> client = WorkbenchClient(api_key="wbk_live_xxx")
        >>>
        >>> # List clients
        >>> response = client.clients.list(status="active")
        >>> for c in response["data"]:
        ...     print(c["first_name"])
        >>>
        >>> # Create a client
        >>> new_client = client.clients.create(
        ...     first_name="John",
        ...     last_name="Doe",
        ...     email="john@example.com"
        ... )
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
        status: Optional[ClientStatus] = None,
    ) -> ListResponse[Client]:
        """
        List all clients.

        Args:
            page: Page number (1-indexed, default: 1)
            per_page: Items per page (1-100, default: 20)
            search: Search query
            sort: Field to sort by
            order: Sort order ("asc" or "desc")
            status: Filter by status

        Returns:
            Paginated list of clients
        """
        params: Dict[str, Any] = {
            "page": page,
            "per_page": per_page,
            "search": search,
            "sort": sort,
            "order": order,
            "status": status,
        }
        return self._client.get("/v1/clients", params=params)  # type: ignore

    def get(self, id: str) -> ApiResponse[Client]:
        """
        Get a client by ID.

        Args:
            id: Client UUID

        Returns:
            Client details
        """
        return self._client.get(f"/v1/clients/{id}")  # type: ignore

    def create(
        self,
        first_name: str,
        last_name: Optional[str] = None,
        company: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        status: Optional[ClientStatus] = None,
        source: Optional[str] = None,
        notes: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> ApiResponse[Client]:
        """
        Create a new client.

        Args:
            first_name: Client's first name (required)
            last_name: Client's last name
            company: Company name
            email: Email address
            phone: Phone number
            status: Client status
            source: How the client was acquired
            notes: Additional notes
            tags: Custom tags

        Returns:
            Created client
        """
        data: Dict[str, Any] = {
            "first_name": first_name,
            "last_name": last_name,
            "company": company,
            "email": email,
            "phone": phone,
            "status": status,
            "source": source,
            "notes": notes,
            "tags": tags,
        }
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        return self._client.post("/v1/clients", json=data)  # type: ignore

    def update(self, id: str, **kwargs: Any) -> ApiResponse[Client]:
        """
        Update a client.

        Args:
            id: Client UUID
            **kwargs: Fields to update (first_name, last_name, email, etc.)

        Returns:
            Updated client
        """
        # Remove None values
        data = {k: v for k, v in kwargs.items() if v is not None}
        return self._client.put(f"/v1/clients/{id}", json=data)  # type: ignore

    def delete(self, id: str) -> None:
        """
        Delete a client.

        Args:
            id: Client UUID
        """
        self._client.delete(f"/v1/clients/{id}")
