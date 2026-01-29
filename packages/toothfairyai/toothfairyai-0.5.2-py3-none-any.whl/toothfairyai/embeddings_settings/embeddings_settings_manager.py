"""Embeddings Settings manager for handling embeddings settings operations."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..types import EmbeddingsSettings, ListResponse

if TYPE_CHECKING:
    from ..client import ToothFairyClient


class EmbeddingsSettingsManager:
    """Manager for embeddings settings operations.

    This manager provides methods to create, update, and manage embeddings settings.

    Example:
        >>> client = ToothFairyClient(api_key="...", workspace_id="...")
        >>> embeddings_settings = client.embeddings_settings.get(...)
    """

    def __init__(self, client: "ToothFairyClient"):
        """Initialize the EmbeddingsSettingsManager.

        Args:
            client: The ToothFairyClient instance.
        """
        self._client = client

    def update(
        self,
        embeddings_settings_id: str,
        max_chunk_words: Optional[int] = None,
        max_overlap_sentences: Optional[int] = None,
        chunking_strategy: Optional[str] = None,
        image_extraction_strategy: Optional[str] = None,
        min_image_width: Optional[int] = None,
        min_image_height: Optional[int] = None,
        aspect_ratio_min: Optional[float] = None,
        aspect_ratio_max: Optional[float] = None,
    ) -> EmbeddingsSettings:
        """Update embeddings settings.

        Args:
            embeddings_settings_id: ID of the embeddings settings to update.
            max_chunk_words: Maximum words per chunk.
            max_overlap_sentences: Maximum overlapping sentences.
            chunking_strategy: Chunking strategy (keywords, semantic).
            image_extraction_strategy: Image extraction strategy (safe, aggressive).
            min_image_width: Minimum image width in pixels.
            min_image_height: Minimum image height in pixels.
            aspect_ratio_min: Minimum aspect ratio.
            aspect_ratio_max: Maximum aspect ratio.

        Returns:
            The updated EmbeddingsSettings object.
        """
        data: Dict[str, Any] = {"id": embeddings_settings_id}

        if max_chunk_words is not None:
            data["maxChunkWords"] = max_chunk_words
        if max_overlap_sentences is not None:
            data["maxOverlapSentences"] = max_overlap_sentences
        if chunking_strategy is not None:
            data["chunkingStrategy"] = chunking_strategy
        if image_extraction_strategy is not None:
            data["imageExtractionStrategy"] = image_extraction_strategy
        if min_image_width is not None:
            data["minImageWidth"] = min_image_width
        if min_image_height is not None:
            data["minImageHeight"] = min_image_height
        if aspect_ratio_min is not None:
            data["aspectRatioMin"] = aspect_ratio_min
        if aspect_ratio_max is not None:
            data["aspectRatioMax"] = aspect_ratio_max

        response = self._client.request("POST", "/embeddings_settings/update", data=data)
        return EmbeddingsSettings.from_dict(response)

    def get(self, embeddings_settings_id: str) -> EmbeddingsSettings:
        """Get a embeddings_settings by ID.

        Args:
            embeddings_settings_id: ID of the embeddings_settings to retrieve.

        Returns:
            The EmbeddingsSettings object.
        """
        response = self._client.request("GET", f"/embeddings_settings/get/{embeddings_settings_id}")
        return EmbeddingsSettings.from_dict(response)
