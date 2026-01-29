"""Request Log manager for handling request logs operations."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..types import ListResponse, RequestLog

if TYPE_CHECKING:
    from ..client import ToothFairyClient


class RequestLogManager:
    """Manager for request logs operations.

    This manager provides methods to create, update, and manage request logs.

    Example:
        >>> client = ToothFairyClient(api_key="...", workspace_id="...")
        >>> request_log = client.request_logs.get(...)
    """

    def __init__(self, client: "ToothFairyClient"):
        """Initialize the RequestLogManager.

        Args:
            client: The ToothFairyClient instance.
        """
        self._client = client

    def get(self, request_log_id: str) -> RequestLog:
        """Get a request_log by ID.

        Args:
            request_log_id: ID of the request_log to retrieve.

        Returns:
            The RequestLog object.
        """
        response = self._client.request("GET", f"/request/get/{request_log_id}")
        return RequestLog.from_dict(response)

    def list(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> ListResponse:
        """List all request logs.

        Args:
            limit: Maximum number of request logs to return.
            offset: Number of request logs to skip.

        Returns:
            A ListResponse containing the request logs.
        """
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        response = self._client.request("GET", "/request/list", params=params)

        items = []
        if isinstance(response, list):
            items = [RequestLog.from_dict(item) for item in response]
        elif isinstance(response, dict):
            items = [RequestLog.from_dict(item) for item in response.get("items", [])]

        return ListResponse(items=items)

    def get_by_type(self, log_type: str) -> List[RequestLog]:
        """Get request logs by type.

        Args:
            log_type: Type of request to filter by.

        Returns:
            A list of RequestLog objects with the specified type.
        """
        result = self.list()
        return [log for log in result.items if log.type == log_type]

    def get_by_status(self, status: str) -> List[RequestLog]:
        """Get request logs by status.

        Args:
            status: Status to filter by.

        Returns:
            A list of RequestLog objects with the specified status.
        """
        result = self.list()
        return [log for log in result.items if log.status == status]
