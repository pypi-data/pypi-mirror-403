"""Channel manager for handling channels operations."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..types import Channel, ListResponse

if TYPE_CHECKING:
    from ..client import ToothFairyClient


class ChannelManager:
    """Manager for channels operations.

    This manager provides methods to create, update, and manage channels.

    Example:
        >>> client = ToothFairyClient(api_key="...", workspace_id="...")
        >>> channel = client.channels.create(...)
    """

    def __init__(self, client: "ToothFairyClient"):
        """Initialize the ChannelManager.

        Args:
            client: The ToothFairyClient instance.
        """
        self._client = client

    def create(
        self,
        name: str,
        channel: str,
        provider: str,
        description: Optional[str] = None,
        senderid: Optional[str] = None,
        is_active: bool = True,
    ) -> Channel:
        """Create a new channel.

        Args:
            name: Channel name.
            channel: Communication channel type (sms, whatsapp, email).
            provider: Service provider (twilio, sms_magic, sms_magic_sf, whatsapp, ses).
            description: Channel description.
            senderid: Sender ID for SMS/WhatsApp channels.
            is_active: Whether the channel is active.

        Returns:
            The created Channel object.
        """
        data: Dict[str, Any] = {
            "name": name,
            "channel": channel,
            "provider": provider,
            "isActive": is_active,
        }

        if description is not None:
            data["description"] = description
        if senderid is not None:
            data["senderid"] = senderid

        response = self._client.request("POST", "/channel/create", data=data)
        return Channel.from_dict(response)

    def update(
        self,
        channel_id: str,
        **kwargs: Any,
    ) -> Channel:
        """Update a channel.

        Args:
            channel_id: ID of the channel to update.
            **kwargs: Fields to update.

        Returns:
            The updated Channel object.
        """
        data: Dict[str, Any] = {"id": channel_id}
        data.update(kwargs)
        response = self._client.request("POST", "/channel/update", data=data)
        return Channel.from_dict(response)

    def delete(self, channel_id: str) -> Dict[str, bool]:
        """Delete a channel.

        Args:
            channel_id: ID of the channel to delete.

        Returns:
            A dictionary with success status.
        """
        self._client.request("DELETE", f"/channel/delete/{channel_id}")
        return {"success": True}

    def get(self, channel_id: str) -> Channel:
        """Get a channel by ID.

        Args:
            channel_id: ID of the channel to retrieve.

        Returns:
            The Channel object.
        """
        response = self._client.request("GET", f"/channel/get/{channel_id}")
        return Channel.from_dict(response)

    def list(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> ListResponse:
        """List all channels.

        Args:
            limit: Maximum number of channels to return.
            offset: Number of channels to skip.

        Returns:
            A ListResponse containing the channels.
        """
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        response = self._client.request("GET", "/channel/list", params=params)

        items = []
        if isinstance(response, list):
            items = [Channel.from_dict(item) for item in response]
        elif isinstance(response, dict):
            items = [Channel.from_dict(item) for item in response.get("items", [])]

        return ListResponse(items=items)

    def get_by_channel_type(self, channel_type: str) -> List[Channel]:
        """Get channels by type.

        Args:
            channel_type: Channel type to filter by (sms, whatsapp, email).

        Returns:
            A list of Channel objects with the specified type.
        """
        result = self.list()
        return [ch for ch in result.items if ch.channel == channel_type]

    def get_active(self) -> List[Channel]:
        """Get all active channels.

        Returns:
            A list of active Channel objects.
        """
        result = self.list()
        return [ch for ch in result.items if ch.is_active]

    def search(self, search_term: str) -> List[Channel]:
        """Search channels by name.

        Args:
            search_term: Term to search for in channel names.

        Returns:
            A list of matching Channel objects.
        """
        all_channels = self.list()
        search_lower = search_term.lower()
        return [channel for channel in all_channels.items if search_lower in channel.name.lower()]
