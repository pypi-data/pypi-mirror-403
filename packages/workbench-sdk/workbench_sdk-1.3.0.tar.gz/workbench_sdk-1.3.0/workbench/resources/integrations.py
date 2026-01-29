"""
Integration marketplace resource for browsing and managing integrations.

The IntegrationsResource provides methods for:
- Browsing the public integration marketplace
- Viewing integration details and reviews
- Managing installed integrations on your business account
"""

from typing import TYPE_CHECKING, Optional

from ..types import (
    ApiResponse,
    ListResponse,
    Integration,
    IntegrationReview,
    InstalledIntegration,
    ListIntegrationsParams,
    ListIntegrationReviewsParams,
    InstallIntegrationParams,
    SubmitReviewParams,
)

if TYPE_CHECKING:
    from ..client import WorkbenchClient


class IntegrationsResource:
    """
    Integration marketplace resource.

    Provides access to the Workbench integration marketplace, allowing you to
    browse published integrations, view reviews, and manage installations.

    Example:
        >>> # Browse marketplace
        >>> integrations = workbench.integrations.list(category="accounting")
        >>> for integration in integrations["data"]:
        ...     print(f"{integration['name']} - {integration['install_count']} installs")

        >>> # Get integration details
        >>> integration = workbench.integrations.get("quickbooks")
        >>> print(f"Scopes: {[s['scope'] for s in integration['data']['scopes']]}")

        >>> # List installed integrations
        >>> installed = workbench.integrations.list_installed()
        >>> for install in installed["data"]:
        ...     print(f"{install['integration']['name']} - Active: {install['is_active']}")
    """

    def __init__(self, client: "WorkbenchClient") -> None:
        self._client = client

    # ===========================================
    # MARKETPLACE (Public)
    # ===========================================

    def list(
        self,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
        search: Optional[str] = None,
        category: Optional[str] = None,
        scope: Optional[str] = None,
        sort_by: Optional[str] = None,
    ) -> ListResponse[Integration]:
        """
        List published integrations in the marketplace.

        Returns a paginated list of published integrations available for installation.
        This endpoint is publicly accessible.

        Args:
            page: Page number (1-indexed)
            per_page: Items per page (1-100)
            search: Search query string
            category: Filter by category (accounting, analytics, etc.)
            scope: Filter by scope (returns integrations that request this scope)
            sort_by: Sort by: 'popular', 'recent', 'rating', 'name'

        Returns:
            Paginated list of integrations

        Example:
            >>> # List all integrations
            >>> result = workbench.integrations.list()
            >>> print(f"Found {result['pagination']['total']} integrations")

            >>> # Filter by category
            >>> result = workbench.integrations.list(
            ...     category="accounting",
            ...     sort_by="popular",
            ...     per_page=10
            ... )
        """
        params: ListIntegrationsParams = {}
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        if search is not None:
            params["search"] = search
        if category is not None:
            params["category"] = category  # type: ignore
        if scope is not None:
            params["scope"] = scope
        if sort_by is not None:
            params["sort_by"] = sort_by  # type: ignore

        return self._client._get("/v1/integrations", params=params)

    def get(self, id_or_slug: str) -> ApiResponse[Integration]:
        """
        Get an integration by ID or slug.

        Returns detailed information about a specific integration.

        Args:
            id_or_slug: Integration UUID or URL slug

        Returns:
            Integration details

        Example:
            >>> integration = workbench.integrations.get("quickbooks")
            >>> print(f"{integration['data']['name']} by {integration['data']['developer']['name']}")
            >>> print(f"Installs: {integration['data']['install_count']}")
        """
        return self._client._get(f"/v1/integrations/{id_or_slug}")

    def get_reviews(
        self,
        integration_id: str,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
        min_rating: Optional[int] = None,
    ) -> ListResponse[IntegrationReview]:
        """
        Get reviews for an integration.

        Returns a paginated list of user reviews for a specific integration.

        Args:
            integration_id: Integration UUID or slug
            page: Page number
            per_page: Items per page
            min_rating: Minimum rating to filter by (1-5)

        Returns:
            Paginated list of reviews

        Example:
            >>> reviews = workbench.integrations.get_reviews(
            ...     "quickbooks",
            ...     min_rating=4,
            ...     per_page=10
            ... )
            >>> for review in reviews["data"]:
            ...     print(f"{review['rating']}/5 - {review['title']}")
        """
        params: ListIntegrationReviewsParams = {}
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        if min_rating is not None:
            params["min_rating"] = min_rating

        return self._client._get(
            f"/v1/integrations/{integration_id}/reviews", params=params
        )

    # ===========================================
    # INSTALLED INTEGRATIONS (Authenticated)
    # ===========================================

    def list_installed(self) -> ListResponse[InstalledIntegration]:
        """
        List installed integrations on your business account.

        Returns all integrations that have been installed on the authenticated
        business account.

        Returns:
            List of installed integrations

        Example:
            >>> installed = workbench.integrations.list_installed()
            >>> for install in installed["data"]:
            ...     print(f"{install['integration']['name']} - Active: {install['is_active']}")
            ...     print(f"Scopes: {', '.join(install['granted_scopes'])}")
        """
        return self._client._get("/v1/integrations/installed")

    def get_installed(self, installation_id: str) -> ApiResponse[InstalledIntegration]:
        """
        Get an installed integration by ID.

        Args:
            installation_id: Installation UUID

        Returns:
            Installed integration details

        Example:
            >>> install = workbench.integrations.get_installed("install-uuid")
            >>> print(f"Installed on: {install['data']['installed_at']}")
        """
        return self._client._get(f"/v1/integrations/installed/{installation_id}")

    def install(
        self,
        integration_id: str,
        scopes: list[str],
        authorization_code: str,
        code_verifier: str,
    ) -> ApiResponse[InstalledIntegration]:
        """
        Install an integration on your business account.

        Completes the OAuth flow and installs an integration. This requires an
        authorization code obtained from the user consent flow.

        Args:
            integration_id: Integration UUID to install
            scopes: Scopes to grant (must be subset of integration's requested scopes)
            authorization_code: Authorization code from OAuth consent flow
            code_verifier: PKCE code verifier

        Returns:
            Installed integration details

        Example:
            >>> # After user completes OAuth consent flow:
            >>> install = workbench.integrations.install(
            ...     integration_id="integration-uuid",
            ...     scopes=["clients:read", "invoices:read"],
            ...     authorization_code="code_from_oauth_flow",
            ...     code_verifier="pkce_code_verifier"
            ... )
            >>> print(f"Installed! Token prefix: {install['data']['access_token_prefix']}")
        """
        data: InstallIntegrationParams = {
            "integration_id": integration_id,
            "scopes": scopes,
            "authorization_code": authorization_code,
            "code_verifier": code_verifier,
        }
        return self._client._post("/v1/integrations/install", data=data)

    def uninstall(self, installation_id: str) -> None:
        """
        Uninstall an integration from your business account.

        Revokes all access tokens and removes the integration. This action
        cannot be undone.

        Args:
            installation_id: Installation UUID

        Example:
            >>> workbench.integrations.uninstall("install-uuid")
            >>> print("Integration uninstalled")
        """
        self._client._delete(f"/v1/integrations/installed/{installation_id}")

    def disable(self, installation_id: str) -> ApiResponse[InstalledIntegration]:
        """
        Temporarily disable an installed integration.

        Pauses the integration without uninstalling it. The integration can
        be re-enabled later.

        Args:
            installation_id: Installation UUID

        Returns:
            Updated installation

        Example:
            >>> install = workbench.integrations.disable("install-uuid")
            >>> print(f"Active: {install['data']['is_active']}")  # False
        """
        return self._client._post(
            f"/v1/integrations/installed/{installation_id}/disable"
        )

    def enable(self, installation_id: str) -> ApiResponse[InstalledIntegration]:
        """
        Re-enable a disabled integration.

        Args:
            installation_id: Installation UUID

        Returns:
            Updated installation

        Example:
            >>> install = workbench.integrations.enable("install-uuid")
            >>> print(f"Active: {install['data']['is_active']}")  # True
        """
        return self._client._post(
            f"/v1/integrations/installed/{installation_id}/enable"
        )

    # ===========================================
    # REVIEWS (Authenticated)
    # ===========================================

    def submit_review(
        self,
        integration_id: str,
        rating: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
    ) -> ApiResponse[IntegrationReview]:
        """
        Submit a review for an installed integration.

        You can only review integrations that are installed on your business account.

        Args:
            integration_id: Integration UUID
            rating: Rating 1-5
            title: Review title (optional)
            content: Review body (optional)

        Returns:
            Created review

        Example:
            >>> review = workbench.integrations.submit_review(
            ...     "integration-uuid",
            ...     rating=5,
            ...     title="Great integration!",
            ...     content="This integration saved us hours of manual work..."
            ... )
        """
        data: SubmitReviewParams = {"rating": rating}
        if title is not None:
            data["title"] = title
        if content is not None:
            data["content"] = content

        return self._client._post(
            f"/v1/integrations/{integration_id}/reviews", data=data
        )
