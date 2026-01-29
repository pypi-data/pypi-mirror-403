"""Member manager for handling members operations."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..types import ListResponse, Member

if TYPE_CHECKING:
    from ..client import ToothFairyClient


class MemberManager:
    """Manager for members operations.

    This manager provides methods to create, update, and manage members.

    Example:
        >>> client = ToothFairyClient(api_key="...", workspace_id="...")
        >>> member = client.members.get(...)
    """

    def __init__(self, client: "ToothFairyClient"):
        """Initialize the MemberManager.

        Args:
            client: The ToothFairyClient instance.
        """
        self._client = client

    def update(
        self,
        member_id: str,
        **kwargs: Any,
    ) -> Member:
        """Update a member.

        Args:
            member_id: ID of the member to update.
            **kwargs: Fields to update.

        Returns:
            The updated Member object.
        """
        data: Dict[str, Any] = {"id": member_id}
        data.update(kwargs)
        response = self._client.request("POST", "/member/update", data=data)
        return Member.from_dict(response)

    def delete(self, member_id: str) -> Dict[str, bool]:
        """Delete a member.

        Args:
            member_id: ID of the member to delete.

        Returns:
            A dictionary with success status.
        """
        self._client.request("DELETE", f"/member/delete/{member_id}")
        return {"success": True}

    def get(self, member_id: str) -> Member:
        """Get a member by ID.

        Args:
            member_id: ID of the member to retrieve.

        Returns:
            The Member object.
        """
        response = self._client.request("GET", f"/member/get/{member_id}")
        return Member.from_dict(response)

    def list(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> ListResponse:
        """List all members.

        Args:
            limit: Maximum number of members to return.
            offset: Number of members to skip.

        Returns:
            A ListResponse containing the members.
        """
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        response = self._client.request("GET", "/member/list", params=params)

        items = []
        if isinstance(response, list):
            items = [Member.from_dict(item) for item in response]
        elif isinstance(response, dict):
            items = [Member.from_dict(item) for item in response.get("items", [])]

        return ListResponse(items=items)

    def get_by_role(self, role: str) -> List[Member]:
        """Get members by role.

        Args:
            role: Role to filter by (admin, member, viewer).

        Returns:
            A list of Member objects with the specified role.
        """
        result = self.list()
        return [member for member in result.items if member.role == role]

    def search(self, search_term: str) -> List[Member]:
        """Search members by user ID.

        Args:
            search_term: Term to search for in user IDs.

        Returns:
            A list of matching Member objects.
        """
        all_members = self.list()
        search_lower = search_term.lower()
        return [member for member in all_members.items if search_lower in member.user_id.lower()]
