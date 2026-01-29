"""
Main Workbench API client.

The WorkbenchClient is the primary interface for interacting with the
Workbench CRM API. It handles authentication, request management, and
provides access to all API resources.
"""

import time
from typing import Any, Dict, Optional, TypeVar, Union
import httpx

from workbench.resources.clients import ClientsResource
from workbench.resources.invoices import InvoicesResource
from workbench.resources.quotes import QuotesResource
from workbench.resources.jobs import JobsResource
from workbench.resources.requests import RequestsResource
from workbench.resources.webhooks import WebhooksResource
from workbench.resources.notifications import NotificationsResource
from workbench.resources.integrations import IntegrationsResource

T = TypeVar("T")

DEFAULT_BASE_URL = "https://api.tryworkbench.app"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3


class WorkbenchError(Exception):
    """Error raised when an API request fails."""

    def __init__(
        self,
        message: str,
        status: int = 0,
        code: str = "UNKNOWN_ERROR",
        details: Optional[list[dict[str, str]]] = None,
        request_id: Optional[str] = None,
    ):
        super().__init__(message)
        self.status = status
        self.code = code
        self.details = details
        self.request_id = request_id

    def __str__(self) -> str:
        parts = [f"{self.code}: {super().__str__()}"]
        if self.status:
            parts.append(f"(status={self.status})")
        if self.request_id:
            parts.append(f"[request_id={self.request_id}]")
        return " ".join(parts)


class WorkbenchClient:
    """
    Main Workbench API client.

    Example:
        >>> from workbench import WorkbenchClient
        >>>
        >>> # Using API key authentication
        >>> client = WorkbenchClient(api_key="wbk_live_xxx")
        >>>
        >>> # Using OAuth access token
        >>> client = WorkbenchClient(access_token="wbk_at_xxx")
        >>>
        >>> # List clients
        >>> response = client.clients.list(status="active")
        >>> for client in response["data"]:
        ...     print(client["first_name"])
        >>>
        >>> # Create an invoice
        >>> invoice = client.invoices.create(
        ...     client_id="client-uuid",
        ...     items=[{"description": "Service", "quantity": 1, "unit_price": 100}]
        ... )
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        access_token: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ):
        """
        Initialize the Workbench client.

        Args:
            api_key: API key for authentication (wbk_live_xxx or wbk_test_xxx)
            access_token: OAuth access token for third-party app authentication
            base_url: Base URL for the API (default: https://api.tryworkbench.app)
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum number of retries for failed requests (default: 3)

        Raises:
            ValueError: If neither api_key nor access_token is provided
        """
        if not api_key and not access_token:
            raise ValueError("Either api_key or access_token must be provided")

        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries
        self._auth_header = f"Bearer {access_token or api_key}"

        # Initialize HTTP client
        self._http = httpx.Client(
            base_url=self._base_url,
            timeout=timeout,
            headers={
                "Authorization": self._auth_header,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

        # Initialize resources
        self.clients = ClientsResource(self)
        self.invoices = InvoicesResource(self)
        self.quotes = QuotesResource(self)
        self.jobs = JobsResource(self)
        self.requests = RequestsResource(self)
        self.webhooks = WebhooksResource(self)
        self.notifications = NotificationsResource(self)
        self.integrations = IntegrationsResource(self)

    def close(self) -> None:
        """Close the HTTP client."""
        self._http.close()

    def __enter__(self) -> "WorkbenchClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def _get_retry_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay."""
        return min(1.0 * (2**attempt), 10.0)

    def _is_retryable(self, status: int) -> bool:
        """Determine if an error is retryable."""
        return status == 429 or (status >= 500 and status < 600)

    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make an API request.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: Request path (without base URL)
            params: Query parameters
            json: Request body

        Returns:
            API response as a dictionary

        Raises:
            WorkbenchError: If the request fails
        """
        # Filter out None values from params
        if params:
            params = {k: v for k, v in params.items() if v is not None}

        last_error: Optional[Exception] = None

        for attempt in range(self._max_retries + 1):
            try:
                response = self._http.request(
                    method=method,
                    url=path,
                    params=params,
                    json=json,
                )

                # Handle error responses
                if not response.is_success:
                    try:
                        error_data = response.json()
                        error_info = error_data.get("error", {})
                        meta = error_data.get("meta", {})
                    except Exception:
                        error_info = {}
                        meta = {}

                    # Check if retryable
                    if self._is_retryable(response.status_code) and attempt < self._max_retries:
                        delay = self._get_retry_delay(attempt)
                        time.sleep(delay)
                        continue

                    raise WorkbenchError(
                        message=error_info.get("message", "Unknown error"),
                        status=response.status_code,
                        code=error_info.get("code", "UNKNOWN_ERROR"),
                        details=error_info.get("details"),
                        request_id=meta.get("request_id"),
                    )

                # Parse successful response
                if response.status_code == 204:
                    return {}

                return response.json()

            except httpx.TimeoutException:
                last_error = WorkbenchError("Request timeout", code="TIMEOUT")
                if attempt < self._max_retries:
                    delay = self._get_retry_delay(attempt)
                    time.sleep(delay)
                    continue

            except httpx.RequestError as e:
                last_error = WorkbenchError(str(e), code="REQUEST_ERROR")
                if attempt < self._max_retries:
                    delay = self._get_retry_delay(attempt)
                    time.sleep(delay)
                    continue

        if last_error:
            raise last_error

        raise WorkbenchError("Request failed", code="UNKNOWN_ERROR")

    def get(
        self, path: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a GET request."""
        return self.request("GET", path, params=params)

    def post(
        self, path: str, json: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a POST request."""
        return self.request("POST", path, json=json)

    def put(
        self, path: str, json: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a PUT request."""
        return self.request("PUT", path, json=json)

    def delete(self, path: str) -> Dict[str, Any]:
        """Make a DELETE request."""
        return self.request("DELETE", path)
