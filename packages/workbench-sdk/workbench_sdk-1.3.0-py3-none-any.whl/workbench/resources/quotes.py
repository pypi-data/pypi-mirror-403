"""
Quotes resource for the Workbench SDK.

Provides methods for managing quotes/estimates in Workbench CRM.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from workbench.types import (
    Quote,
    QuoteItem,
    QuoteStatus,
    ApiResponse,
    ListResponse,
)

if TYPE_CHECKING:
    from workbench.client import WorkbenchClient


class QuotesResource:
    """
    Quotes resource.

    Example:
        >>> client = WorkbenchClient(api_key="wbk_live_xxx")
        >>>
        >>> # Create a quote
        >>> quote = client.quotes.create(
        ...     client_id="client-uuid",
        ...     valid_until="2024-03-01",
        ...     items=[
        ...         {"description": "Kitchen Renovation", "quantity": 1, "unit_price": 5000}
        ...     ]
        ... )
        >>>
        >>> # Send the quote
        >>> client.quotes.send(quote["data"]["id"])
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
        status: Optional[QuoteStatus] = None,
        client_id: Optional[str] = None,
    ) -> ListResponse[Quote]:
        """
        List all quotes.

        Args:
            page: Page number (1-indexed, default: 1)
            per_page: Items per page (1-100, default: 20)
            search: Search query
            sort: Field to sort by
            order: Sort order ("asc" or "desc")
            status: Filter by status
            client_id: Filter by client ID

        Returns:
            Paginated list of quotes
        """
        params: Dict[str, Any] = {
            "page": page,
            "per_page": per_page,
            "search": search,
            "sort": sort,
            "order": order,
            "status": status,
            "client_id": client_id,
        }
        return self._client.get("/v1/quotes", params=params)  # type: ignore

    def get(self, id: str) -> ApiResponse[Quote]:
        """
        Get a quote by ID.

        Args:
            id: Quote UUID

        Returns:
            Quote details with line items
        """
        return self._client.get(f"/v1/quotes/{id}")  # type: ignore

    def create(
        self,
        items: List[QuoteItem],
        client_id: Optional[str] = None,
        job_id: Optional[str] = None,
        status: Optional[QuoteStatus] = None,
        issue_date: Optional[str] = None,
        valid_until: Optional[str] = None,
        tax_rate: Optional[float] = None,
        discount_amount: Optional[float] = None,
        notes: Optional[str] = None,
        terms: Optional[str] = None,
    ) -> ApiResponse[Quote]:
        """
        Create a new quote.

        Args:
            items: Line items (required)
            client_id: Client UUID
            job_id: Associated job UUID
            status: Quote status
            issue_date: Issue date
            valid_until: Quote expiration date
            tax_rate: Tax rate percentage
            discount_amount: Discount amount
            notes: Notes visible to client
            terms: Terms and conditions

        Returns:
            Created quote
        """
        data: Dict[str, Any] = {
            "items": items,
            "client_id": client_id,
            "job_id": job_id,
            "status": status,
            "issue_date": issue_date,
            "valid_until": valid_until,
            "tax_rate": tax_rate,
            "discount_amount": discount_amount,
            "notes": notes,
            "terms": terms,
        }
        data = {k: v for k, v in data.items() if v is not None or k == "items"}
        return self._client.post("/v1/quotes", json=data)  # type: ignore

    def update(self, id: str, **kwargs: Any) -> ApiResponse[Quote]:
        """
        Update a quote.

        If items are provided, they will replace all existing line items.

        Args:
            id: Quote UUID
            **kwargs: Fields to update

        Returns:
            Updated quote
        """
        data = {k: v for k, v in kwargs.items() if v is not None}
        return self._client.put(f"/v1/quotes/{id}", json=data)  # type: ignore

    def delete(self, id: str) -> None:
        """
        Delete a quote.

        Args:
            id: Quote UUID
        """
        self._client.delete(f"/v1/quotes/{id}")

    def send(self, id: str) -> ApiResponse[Dict[str, str]]:
        """
        Send a quote via email.

        Args:
            id: Quote UUID

        Returns:
            Success response
        """
        return self._client.post(f"/v1/quotes/{id}/send")  # type: ignore
