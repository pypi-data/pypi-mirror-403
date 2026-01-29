"""Secret manager for handling secrets operations."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..types import ListResponse, Secret

if TYPE_CHECKING:
    from ..client import ToothFairyClient


class SecretManager:
    """Manager for secrets operations.

    This manager provides methods to create, update, and manage secrets.

    Example:
        >>> client = ToothFairyClient(api_key="...", workspace_id="...")
        >>> secret = client.secrets.create(...)
    """

    def __init__(self, client: "ToothFairyClient"):
        """Initialize the SecretManager.

        Args:
            client: The ToothFairyClient instance.
        """
        self._client = client

    def create(
        self,
        name: str,
        description: Optional[str] = None,
    ) -> Secret:
        """Create a new secret.

        Args:
            name: Secret name.
            description: Secret description.

        Returns:
            The created Secret object.
        """
        data: Dict[str, Any] = {
            "name": name,
        }

        if description is not None:
            data["description"] = description

        response = self._client.request("POST", "/secret/create", data=data)
        return Secret.from_dict(response)

    def delete(self, secret_id: str) -> Dict[str, bool]:
        """Delete a secret.

        Args:
            secret_id: ID of the secret to delete.

        Returns:
            A dictionary with success status.
        """
        self._client.request("DELETE", f"/secret/delete/{secret_id}")
        return {"success": True}
