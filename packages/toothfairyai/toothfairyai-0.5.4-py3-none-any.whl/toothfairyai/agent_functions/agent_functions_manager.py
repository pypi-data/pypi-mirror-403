"""Agent Function manager for handling agent functions operations."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..types import AgentFunction, ListResponse

if TYPE_CHECKING:
    from ..client import ToothFairyClient


class AgentFunctionManager:
    """Manager for agent functions operations.

    This manager provides methods to create, update, and manage agent functions.

    Example:
        >>> client = ToothFairyClient(api_key="...", workspace_id="...")
        >>> agent_function = client.agent_functions.create(...)
    """

    def __init__(self, client: "ToothFairyClient"):
        """Initialize the AgentFunctionManager.

        Args:
            client: The ToothFairyClient instance.
        """
        self._client = client

    def create(
        self,
        name: str,
        description: str,
        url: str,
        request_type: str = "GET",
        authorisation_type: str = "none",
        authorisation_key: Optional[str] = None,
        parameters: Optional[List[Dict[str, Any]]] = None,
        headers: Optional[List[Dict[str, str]]] = None,
        static_args: Optional[List[Dict[str, str]]] = None,
        custom_execution_code: Optional[str] = None,
    ) -> AgentFunction:
        """Create a new agent function.

        Args:
            name: Human-readable name of the function.
            description: Detailed description of function purpose (required).
            url: Endpoint URL for the function.
            request_type: HTTP method (GET, POST, PUT, PATCH, DELETE).
            authorisation_type: Authentication method (bearer, apikey, none).
            authorisation_key: Authentication key or token.
            parameters: Function parameters schema.
            headers: Required HTTP headers.
            static_args: Static arguments passed to function.
            custom_execution_code: Custom code for function execution.

        Returns:
            The created AgentFunction object.
        """
        data: Dict[str, Any] = {
            "name": name,
            "description": description,
            "url": url,
            "requestType": request_type,
            "authorisationType": authorisation_type,
        }

        if authorisation_key is not None:
            data["authorisationKey"] = authorisation_key
        if parameters is not None:
            data["parameters"] = parameters
        if headers is not None:
            data["headers"] = headers
        if static_args is not None:
            data["staticArgs"] = static_args
        if custom_execution_code is not None:
            data["customExecutionCode"] = custom_execution_code

        response = self._client.request("POST", "/function/create", data=data)
        return AgentFunction.from_dict(response)

    def update(
        self,
        agent_function_id: str,
        **kwargs: Any,
    ) -> AgentFunction:
        """Update a agent_function.

        Args:
            agent_function_id: ID of the agent_function to update.
            **kwargs: Fields to update.

        Returns:
            The updated AgentFunction object.
        """
        data: Dict[str, Any] = {"id": agent_function_id}
        data.update(kwargs)
        response = self._client.request("POST", "/function/update", data=data)
        return AgentFunction.from_dict(response)

    def delete(self, agent_function_id: str) -> Dict[str, bool]:
        """Delete a agent_function.

        Args:
            agent_function_id: ID of the agent_function to delete.

        Returns:
            A dictionary with success status.
        """
        self._client.request("DELETE", f"/function/delete/{agent_function_id}")
        return {"success": True}

    def get(self, agent_function_id: str) -> AgentFunction:
        """Get a agent_function by ID.

        Args:
            agent_function_id: ID of the agent_function to retrieve.

        Returns:
            The AgentFunction object.
        """
        response = self._client.request("GET", f"/function/get/{agent_function_id}")
        return AgentFunction.from_dict(response)

    def list(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> ListResponse:
        """List all agent functions.

        Args:
            limit: Maximum number of agent functions to return.
            offset: Number of agent functions to skip.

        Returns:
            A ListResponse containing the agent functions.
        """
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        response = self._client.request("GET", "/function/list", params=params)

        items = []
        if isinstance(response, list):
            items = [AgentFunction.from_dict(item) for item in response]
        elif isinstance(response, dict):
            items = [AgentFunction.from_dict(item) for item in response.get("items", [])]

        return ListResponse(items=items)

    def search(self, search_term: str) -> List[AgentFunction]:
        """Search agent functions by name.

        Args:
            search_term: Term to search for in function names.

        Returns:
            A list of matching AgentFunction objects.
        """
        all_functions = self.list()
        search_lower = search_term.lower()
        return [func for func in all_functions.items if search_lower in func.name.lower()]
