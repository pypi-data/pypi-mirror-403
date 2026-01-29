"""Embeddings manager for handling embeddings operations."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..types import Embedding, ListResponse

if TYPE_CHECKING:
    from ..client import ToothFairyClient


class EmbeddingsManager:
    """Manager for embeddings operations.

    This manager provides methods to create, update, and manage embeddings.

    Example:
        >>> client = ToothFairyClient(api_key="...", workspace_id="...")
        >>> embedding = client.embeddings.get(...)
    """

    def __init__(self, client: "ToothFairyClient"):
        """Initialize the EmbeddingsManager.

        Args:
            client: The ToothFairyClient instance.
        """
        self._client = client

    def get(self, document_id: str) -> List[Embedding]:
        """Get embeddings for a document.

        Args:
            document_id: ID of the document to get embeddings for.

        Returns:
            A list of Embedding objects for the document.
        """
        params: Dict[str, Any] = {"documentId": document_id}
        response = self._client.request("GET", "/embedding/get", params=params)

        items = []
        if isinstance(response, list):
            items = [Embedding.from_dict(item) for item in response]
        elif isinstance(response, dict):
            items = [Embedding.from_dict(item) for item in response.get("items", [])]

        return items
