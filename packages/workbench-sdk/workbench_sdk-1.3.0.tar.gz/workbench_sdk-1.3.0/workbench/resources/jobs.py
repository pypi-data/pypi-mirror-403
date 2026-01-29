"""
Jobs resource for the Workbench SDK.

Provides methods for managing jobs/work orders in Workbench CRM.
"""

from typing import TYPE_CHECKING, Any, Dict, Optional

from workbench.types import (
    Job,
    JobStatus,
    JobPriority,
    ApiResponse,
    ListResponse,
)

if TYPE_CHECKING:
    from workbench.client import WorkbenchClient


class JobsResource:
    """
    Jobs resource.

    Example:
        >>> client = WorkbenchClient(api_key="wbk_live_xxx")
        >>>
        >>> # Create a job
        >>> job = client.jobs.create(
        ...     client_id="client-uuid",
        ...     title="Kitchen Faucet Installation",
        ...     priority="high",
        ...     scheduled_start="2024-01-20T09:00:00Z"
        ... )
        >>>
        >>> # Update job status
        >>> client.jobs.update(job["data"]["id"], status="completed")
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
        status: Optional[JobStatus] = None,
        priority: Optional[JobPriority] = None,
        client_id: Optional[str] = None,
    ) -> ListResponse[Job]:
        """
        List all jobs.

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
            Paginated list of jobs
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
        return self._client.get("/v1/jobs", params=params)  # type: ignore

    def get(self, id: str) -> ApiResponse[Job]:
        """
        Get a job by ID.

        Args:
            id: Job UUID

        Returns:
            Job details
        """
        return self._client.get(f"/v1/jobs/{id}")  # type: ignore

    def create(
        self,
        title: str,
        client_id: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[JobStatus] = None,
        priority: Optional[JobPriority] = None,
        scheduled_start: Optional[str] = None,
        scheduled_end: Optional[str] = None,
        estimated_duration: Optional[int] = None,
        address_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> ApiResponse[Job]:
        """
        Create a new job.

        Args:
            title: Job title (required)
            client_id: Client UUID
            description: Job description
            status: Job status
            priority: Job priority
            scheduled_start: Scheduled start datetime (ISO 8601)
            scheduled_end: Scheduled end datetime (ISO 8601)
            estimated_duration: Estimated duration in minutes
            address_id: Address UUID
            notes: Additional notes

        Returns:
            Created job
        """
        data: Dict[str, Any] = {
            "title": title,
            "client_id": client_id,
            "description": description,
            "status": status,
            "priority": priority,
            "scheduled_start": scheduled_start,
            "scheduled_end": scheduled_end,
            "estimated_duration": estimated_duration,
            "address_id": address_id,
            "notes": notes,
        }
        data = {k: v for k, v in data.items() if v is not None or k == "title"}
        return self._client.post("/v1/jobs", json=data)  # type: ignore

    def update(self, id: str, **kwargs: Any) -> ApiResponse[Job]:
        """
        Update a job.

        Args:
            id: Job UUID
            **kwargs: Fields to update (status, priority, actual_start, actual_end, etc.)

        Returns:
            Updated job
        """
        data = {k: v for k, v in kwargs.items() if v is not None}
        return self._client.put(f"/v1/jobs/{id}", json=data)  # type: ignore

    def delete(self, id: str) -> None:
        """
        Delete a job.

        Args:
            id: Job UUID
        """
        self._client.delete(f"/v1/jobs/{id}")
