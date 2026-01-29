"""Site manager for handling sites operations."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..types import ListResponse, Site

if TYPE_CHECKING:
    from ..client import ToothFairyClient


class SiteManager:
    """Manager for sites operations.

    This manager provides methods to create, update, and manage sites.

    Example:
        >>> client = ToothFairyClient(api_key="...", workspace_id="...")
        >>> site = client.sites.get(...)
    """

    def __init__(self, client: "ToothFairyClient"):
        """Initialize the SiteManager.

        Args:
            client: The ToothFairyClient instance.
        """
        self._client = client

    def update(
        self,
        site_id: str,
        **kwargs: Any,
    ) -> Site:
        """Update a site.

        Args:
            site_id: ID of the site to update.
            **kwargs: Fields to update.

        Returns:
            The updated Site object.
        """
        data: Dict[str, Any] = {"id": site_id}
        data.update(kwargs)
        response = self._client.request("POST", "/site/update", data=data)
        return Site.from_dict(response)

    def delete(self, site_id: str) -> Dict[str, bool]:
        """Delete a site.

        Args:
            site_id: ID of the site to delete.

        Returns:
            A dictionary with success status.
        """
        self._client.request("DELETE", f"/site/delete/{site_id}")
        return {"success": True}

    def get(self, site_id: str) -> Site:
        """Get a site by ID.

        Args:
            site_id: ID of the site to retrieve.

        Returns:
            The Site object.
        """
        response = self._client.request("GET", f"/site/get/{site_id}")
        return Site.from_dict(response)

    def list(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> ListResponse:
        """List all sites.

        Args:
            limit: Maximum number of sites to return.
            offset: Number of sites to skip.

        Returns:
            A ListResponse containing the sites.
        """
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        response = self._client.request("GET", "/site/list", params=params)

        items = []
        if isinstance(response, list):
            items = [Site.from_dict(item) for item in response]
        elif isinstance(response, dict):
            items = [Site.from_dict(item) for item in response.get("items", [])]

        return ListResponse(items=items)

    def get_active(self) -> List[Site]:
        """Get all active sites.

        Returns:
            A list of active Site objects.
        """
        result = self.list()
        return [site for site in result.items if site.status == "active"]

    def get_by_status(self, status: str) -> List[Site]:
        """Get sites by status.

        Args:
            status: Status to filter by (active, inactive, pending).

        Returns:
            A list of Site objects with the specified status.
        """
        result = self.list()
        return [site for site in result.items if site.status == status]

    def search(self, search_term: str) -> List[Site]:
        """Search sites by name.

        Args:
            search_term: Term to search for in site names.

        Returns:
            A list of matching Site objects.
        """
        all_sites = self.list()
        search_lower = search_term.lower()
        return [site for site in all_sites.items if search_lower in site.name.lower()]
