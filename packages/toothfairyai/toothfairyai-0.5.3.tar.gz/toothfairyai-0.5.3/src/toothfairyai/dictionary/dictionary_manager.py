"""Dictionary manager for handling dictionary entries operations."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..types import DictionaryEntry, ListResponse

if TYPE_CHECKING:
    from ..client import ToothFairyClient


class DictionaryManager:
    """Manager for dictionary entries operations.

    This manager provides methods to create, update, and manage dictionary entries.

    Example:
        >>> client = ToothFairyClient(api_key="...", workspace_id="...")
        >>> dictionary_entry = client.dictionary.get(...)
    """

    def __init__(self, client: "ToothFairyClient"):
        """Initialize the DictionaryManager.

        Args:
            client: The ToothFairyClient instance.
        """
        self._client = client

    def get(self, dictionary_entry_id: str) -> DictionaryEntry:
        """Get a dictionary_entry by ID.

        Args:
            dictionary_entry_id: ID of the dictionary_entry to retrieve.

        Returns:
            The DictionaryEntry object.
        """
        response = self._client.request("GET", f"/dictionary/get/{dictionary_entry_id}")
        return DictionaryEntry.from_dict(response)

    def list(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> ListResponse:
        """List all dictionary entries.

        Args:
            limit: Maximum number of dictionary entries to return.
            offset: Number of dictionary entries to skip.

        Returns:
            A ListResponse containing the dictionary entries.
        """
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        response = self._client.request("GET", "/dictionary/list", params=params)

        items = []
        if isinstance(response, list):
            items = [DictionaryEntry.from_dict(item) for item in response]
        elif isinstance(response, dict):
            items = [DictionaryEntry.from_dict(item) for item in response.get("items", [])]

        return ListResponse(items=items)

    def get_by_language_pair(
        self,
        source_language: str,
        target_language: str,
    ) -> List[DictionaryEntry]:
        """Get dictionary entries by language pair.

        Args:
            source_language: Source language code.
            target_language: Target language code.

        Returns:
            A list of DictionaryEntry objects for the language pair.
        """
        result = self.list()
        return [
            entry
            for entry in result.items
            if entry.source_language == source_language and entry.target_language == target_language
        ]

    def search(self, search_term: str) -> List[DictionaryEntry]:
        """Search dictionary entries by source text.

        Args:
            search_term: Term to search for in source text.

        Returns:
            A list of matching DictionaryEntry objects.
        """
        all_entries = self.list()
        search_lower = search_term.lower()
        return [entry for entry in all_entries.items if search_lower in entry.source_text.lower()]
