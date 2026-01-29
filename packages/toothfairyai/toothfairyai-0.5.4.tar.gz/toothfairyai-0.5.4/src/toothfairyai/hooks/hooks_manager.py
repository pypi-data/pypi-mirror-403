"""Hook manager for handling hooks operations."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..types import Hook, ListResponse

if TYPE_CHECKING:
    from ..client import ToothFairyClient


class HookManager:
    """Manager for hooks operations.

    This manager provides methods to create, update, and manage hooks.

    Example:
        >>> client = ToothFairyClient(api_key="...", workspace_id="...")
        >>> hook = client.hooks.create(...)
    """

    def __init__(self, client: "ToothFairyClient"):
        """Initialize the HookManager.

        Args:
            client: The ToothFairyClient instance.
        """
        self._client = client

    def create(
        self,
        name: str,
        description: Optional[str] = None,
        function_name: Optional[str] = None,
        custom_execution_code: Optional[str] = None,
        custom_execution_instructions: Optional[str] = None,
        available_libraries: Optional[str] = None,
        allow_external_api: bool = False,
        hardcoded_script: bool = False,
        is_template: bool = False,
    ) -> Hook:
        """Create a new hook.

        Args:
            name: Hook name.
            description: Hook description.
            function_name: Name of the function to execute.
            custom_execution_code: Custom Python code to execute.
            custom_execution_instructions: Instructions for code execution.
            available_libraries: Available Python libraries.
            allow_external_api: Whether to allow external API calls.
            hardcoded_script: Whether this is a hardcoded script.
            is_template: Whether this is a template hook.

        Returns:
            The created Hook object.
        """
        data: Dict[str, Any] = {
            "name": name,
            "allowExternalAPI": allow_external_api,
            "hardcodedScript": hardcoded_script,
            "isTemplate": is_template,
        }

        if description is not None:
            data["description"] = description
        if function_name is not None:
            data["functionName"] = function_name
        if custom_execution_code is not None:
            data["customExecutionCode"] = custom_execution_code
        if custom_execution_instructions is not None:
            data["customExecutionInstructions"] = custom_execution_instructions
        if available_libraries is not None:
            data["availableLibraries"] = available_libraries

        response = self._client.request("POST", "/hook/create", data=data)
        return Hook.from_dict(response)

    def update(
        self,
        hook_id: str,
        **kwargs: Any,
    ) -> Hook:
        """Update a hook.

        Args:
            hook_id: ID of the hook to update.
            **kwargs: Fields to update.

        Returns:
            The updated Hook object.
        """
        data: Dict[str, Any] = {"id": hook_id}
        data.update(kwargs)
        response = self._client.request("POST", "/hook/update", data=data)
        return Hook.from_dict(response)

    def delete(self, hook_id: str) -> Dict[str, bool]:
        """Delete a hook.

        Args:
            hook_id: ID of the hook to delete.

        Returns:
            A dictionary with success status.
        """
        self._client.request("DELETE", f"/hook/delete/{hook_id}")
        return {"success": True}

    def get(self, hook_id: str) -> Hook:
        """Get a hook by ID.

        Args:
            hook_id: ID of the hook to retrieve.

        Returns:
            The Hook object.
        """
        response = self._client.request("GET", f"/hook/get/{hook_id}")
        return Hook.from_dict(response)

    def list(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> ListResponse:
        """List all hooks.

        Args:
            limit: Maximum number of hooks to return.
            offset: Number of hooks to skip.

        Returns:
            A ListResponse containing the hooks.
        """
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        response = self._client.request("GET", "/hook/list", params=params)

        items = []
        if isinstance(response, list):
            items = [Hook.from_dict(item) for item in response]
        elif isinstance(response, dict):
            items = [Hook.from_dict(item) for item in response.get("items", [])]

        return ListResponse(items=items)

    def get_templates(self) -> List[Hook]:
        """Get all template hooks.

        Returns:
            A list of template Hook objects.
        """
        result = self.list()
        return [hook for hook in result.items if hook.is_template]

    def get_active(self) -> List[Hook]:
        """Get all non-template hooks.

        Returns:
            A list of active Hook objects.
        """
        result = self.list()
        return [hook for hook in result.items if not hook.is_template]

    def search(self, search_term: str) -> List[Hook]:
        """Search hooks by name.

        Args:
            search_term: Term to search for in hook names.

        Returns:
            A list of matching Hook objects.
        """
        all_hooks = self.list()
        search_lower = search_term.lower()
        return [hook for hook in all_hooks.items if search_lower in hook.name.lower()]
