"""Prompt manager for handling prompt operations."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..types import ListResponse, Prompt, PromptCreateData

if TYPE_CHECKING:
    from ..client import ToothFairyClient


class PromptManager:
    """Manager for prompt operations.

    This manager provides methods to create, update, and manage prompt templates.

    Example:
        >>> client = ToothFairyClient(api_key="...", workspace_id="...")
        >>> prompt = client.prompts.create(
        ...     label="Greeting",
        ...     interpolation_string="Hello {{name}}! Welcome to our service."
        ... )
    """

    def __init__(self, client: "ToothFairyClient"):
        """Initialize the PromptManager.

        Args:
            client: The ToothFairyClient instance.
        """
        self._client = client

    def create(
        self,
        label: str,
        interpolation_string: str,
        scope: Optional[str] = None,
        style: Optional[str] = None,
        domain: Optional[str] = None,
        prompt_placeholder: Optional[str] = None,
        available_to_agents: Optional[List[str]] = None,
    ) -> Prompt:
        """Create a new prompt.

        Args:
            label: Prompt label.
            interpolation_string: The prompt template string (minimum 128 characters).
            scope: Prompt scope.
            style: Prompt style.
            domain: Prompt domain.
            prompt_placeholder: Placeholder text.
            available_to_agents: List of agent IDs that can use this prompt.

        Returns:
            The created Prompt object.

        Note:
            The API requires promptLength >= 128, so ensure your
            interpolation_string is at least 128 characters.
        """
        data: Dict[str, Any] = {
            "label": label,
            "interpolationString": interpolation_string,
            "promptLength": max(len(interpolation_string), 128),
        }

        if scope is not None:
            data["scope"] = scope
        if style is not None:
            data["style"] = style
        if domain is not None:
            data["domain"] = domain
        if prompt_placeholder is not None:
            data["promptPlaceholder"] = prompt_placeholder
        if available_to_agents is not None:
            data["availableToAgents"] = available_to_agents

        response = self._client.request("POST", "/prompt/create", data=data)
        return Prompt.from_dict(response)

    def get(self, prompt_id: str) -> Prompt:
        """Get a prompt by ID.

        Args:
            prompt_id: ID of the prompt to retrieve.

        Returns:
            The Prompt object.
        """
        response = self._client.request("GET", f"/prompt/get/{prompt_id}")
        return Prompt.from_dict(response)

    def delete(self, prompt_id: str) -> Dict[str, bool]:
        """Delete a prompt.

        Args:
            prompt_id: ID of the prompt to delete.

        Returns:
            A dictionary with success status.
        """
        self._client.request("DELETE", f"/prompt/delete/{prompt_id}")
        return {"success": True}

    def update(
        self,
        prompt_id: str,
        label: Optional[str] = None,
        interpolation_string: Optional[str] = None,
        scope: Optional[str] = None,
        style: Optional[str] = None,
        domain: Optional[str] = None,
        prompt_placeholder: Optional[str] = None,
        available_to_agents: Optional[List[str]] = None,
    ) -> Prompt:
        """Update a prompt.

        Args:
            prompt_id: ID of the prompt to update.
            label: New label.
            interpolation_string: New template string.
            scope: New scope.
            style: New style.
            domain: New domain.
            prompt_placeholder: New placeholder.
            available_to_agents: New list of agent IDs.

        Returns:
            The updated Prompt object.
        """
        data: Dict[str, Any] = {"id": prompt_id}

        if label is not None:
            data["label"] = label
        if interpolation_string is not None:
            data["interpolationString"] = interpolation_string
            data["promptLength"] = max(len(interpolation_string), 128)
        if scope is not None:
            data["scope"] = scope
        if style is not None:
            data["style"] = style
        if domain is not None:
            data["domain"] = domain
        if prompt_placeholder is not None:
            data["promptPlaceholder"] = prompt_placeholder
        if available_to_agents is not None:
            data["availableToAgents"] = available_to_agents

        response = self._client.request("POST", "/prompt/update", data=data)
        return Prompt.from_dict(response)

    def list(
        self,
        prompt_type: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> ListResponse:
        """List prompts.

        Args:
            prompt_type: Filter by prompt type.
            limit: Maximum number of prompts to return.
            offset: Number of prompts to skip.

        Returns:
            A ListResponse containing the prompts.
        """
        params: Dict[str, Any] = {}
        if prompt_type is not None:
            params["type"] = prompt_type
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        response = self._client.request("GET", "/prompt/list", params=params)

        items = []
        if isinstance(response, list):
            items = [Prompt.from_dict(item) for item in response]
        elif isinstance(response, dict):
            items = [Prompt.from_dict(item) for item in response.get("items", [])]

        return ListResponse(items=items)

    def get_by_type(
        self,
        prompt_type: str,
        limit: Optional[int] = None,
    ) -> List[Prompt]:
        """Get prompts by type.

        Args:
            prompt_type: Type of prompts to retrieve.
            limit: Maximum number of prompts to return.

        Returns:
            A list of Prompt objects.
        """
        result = self.list(prompt_type=prompt_type, limit=limit)
        return result.items

    def get_by_agent(self, agent_id: str) -> List[Prompt]:
        """Get prompts available to a specific agent.

        Args:
            agent_id: ID of the agent.

        Returns:
            A list of Prompt objects available to the agent.
        """
        all_prompts = self.list()
        return [
            prompt for prompt in all_prompts.items if agent_id in (prompt.available_to_agents or [])
        ]

    def get_by_scope(self, scope: str) -> List[Prompt]:
        """Get prompts by scope.

        Args:
            scope: Prompt scope to filter by.

        Returns:
            A list of Prompt objects with the specified scope.
        """
        all_prompts = self.list()
        return [prompt for prompt in all_prompts.items if prompt.scope == scope]

    def search(
        self,
        search_term: str,
        prompt_type: Optional[str] = None,
    ) -> List[Prompt]:
        """Search prompts by label.

        Args:
            search_term: Term to search for in prompt labels.
            prompt_type: Filter by prompt type.

        Returns:
            A list of matching Prompt objects.
        """
        all_prompts = self.list(prompt_type=prompt_type)
        search_lower = search_term.lower()
        return [prompt for prompt in all_prompts.items if search_lower in prompt.label.lower()]

    def clone(
        self,
        prompt_id: str,
        label: Optional[str] = None,
        interpolation_string: Optional[str] = None,
        scope: Optional[str] = None,
        style: Optional[str] = None,
        domain: Optional[str] = None,
        prompt_placeholder: Optional[str] = None,
        available_to_agents: Optional[List[str]] = None,
    ) -> Prompt:
        """Clone a prompt with optional modifications.

        Args:
            prompt_id: ID of the prompt to clone.
            label: New label (defaults to original + " (copy)").
            interpolation_string: New template (defaults to original).
            scope: New scope (defaults to original).
            style: New style (defaults to original).
            domain: New domain (defaults to original).
            prompt_placeholder: New placeholder (defaults to original).
            available_to_agents: New agent list (defaults to original).

        Returns:
            The cloned Prompt object.
        """
        # Get the original prompt
        original = self.get(prompt_id)

        # Create new prompt with modifications
        return self.create(
            label=label or f"{original.label} (copy)",
            interpolation_string=interpolation_string or original.interpolation_string,
            scope=scope if scope is not None else original.scope,
            style=style if style is not None else original.style,
            domain=domain if domain is not None else original.domain,
            prompt_placeholder=(
                prompt_placeholder
                if prompt_placeholder is not None
                else original.prompt_placeholder
            ),
            available_to_agents=(
                available_to_agents
                if available_to_agents is not None
                else original.available_to_agents
            ),
        )
