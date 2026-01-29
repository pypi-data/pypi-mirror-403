"""Connection manager for handling connections operations."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..types import Connection, ListResponse

if TYPE_CHECKING:
    from ..client import ToothFairyClient


class ConnectionManager:
    """Manager for connections operations.

    This manager provides methods to create, update, and manage connections.

    Example:
        >>> client = ToothFairyClient(api_key="...", workspace_id="...")
        >>> connection = client.connections.get(...)
    """

    def __init__(self, client: "ToothFairyClient"):
        """Initialize the ConnectionManager.

        Args:
            client: The ToothFairyClient instance.
        """
        self._client = client

    def delete(self, connection_id: str) -> Dict[str, bool]:
        """Delete a connection.

        Args:
            connection_id: ID of the connection to delete.

        Returns:
            A dictionary with success status.
        """
        self._client.request("DELETE", f"/connection/delete/{connection_id}")
        return {"success": True}

    def get(self, connection_id: str) -> Connection:
        """Get a connection by ID.

        Args:
            connection_id: ID of the connection to retrieve.

        Returns:
            The Connection object.
        """
        response = self._client.request("GET", f"/connection/get/{connection_id}")
        return Connection.from_dict(response)

    def list(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> ListResponse:
        """List all connections.

        Args:
            limit: Maximum number of connections to return.
            offset: Number of connections to skip.

        Returns:
            A ListResponse containing the connections.
        """
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        response = self._client.request("GET", "/connection/list", params=params)

        items = []
        if isinstance(response, list):
            items = [Connection.from_dict(item) for item in response]
        elif isinstance(response, dict):
            items = [Connection.from_dict(item) for item in response.get("items", [])]

        return ListResponse(items=items)

    def get_by_type(self, connection_type: str) -> List[Connection]:
        """Get connections by type.

        Args:
            connection_type: Connection type to filter by.

        Returns:
            A list of Connection objects with the specified type.
        """
        result = self.list()
        return [conn for conn in result.items if conn.type == connection_type]

    def search(self, search_term: str) -> List[Connection]:
        """Search connections by name.

        Args:
            search_term: Term to search for in connection names.

        Returns:
            A list of matching Connection objects.
        """
        all_connections = self.list()
        search_lower = search_term.lower()
        return [conn for conn in all_connections.items if search_lower in conn.name.lower()]
