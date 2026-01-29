"""Charting Settings manager for handling charting settings operations."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..types import ChartingSettings, ListResponse

if TYPE_CHECKING:
    from ..client import ToothFairyClient


class ChartingSettingsManager:
    """Manager for charting settings operations.

    This manager provides methods to create, update, and manage charting settings.

    Example:
        >>> client = ToothFairyClient(api_key="...", workspace_id="...")
        >>> charting_settings = client.charting_settings.get(...)
    """

    def __init__(self, client: "ToothFairyClient"):
        """Initialize the ChartingSettingsManager.

        Args:
            client: The ToothFairyClient instance.
        """
        self._client = client

    def update(
        self,
        charting_settings_id: str,
        primary_color: Optional[str] = None,
        secondary_color: Optional[str] = None,
        tertiary_color: Optional[str] = None,
        primary_text_color: Optional[str] = None,
        primary_border_color: Optional[str] = None,
        line_color: Optional[str] = None,
        plot_primary_color: Optional[str] = None,
        plot_secondary_color: Optional[str] = None,
        plot_tertiary_color: Optional[str] = None,
        xy_background_color: Optional[str] = None,
    ) -> ChartingSettings:
        """Update charting settings.

        Args:
            charting_settings_id: ID of the charting settings to update.
            primary_color: Primary color hex code.
            secondary_color: Secondary color hex code.
            tertiary_color: Tertiary color hex code.
            primary_text_color: Primary text color hex code.
            primary_border_color: Primary border color hex code.
            line_color: Line color hex code.
            plot_primary_color: Plot primary color hex code.
            plot_secondary_color: Plot secondary color hex code.
            plot_tertiary_color: Plot tertiary color hex code.
            xy_background_color: XY background color hex code.

        Returns:
            The updated ChartingSettings object.
        """
        data: Dict[str, Any] = {"id": charting_settings_id}

        if primary_color is not None:
            data["primaryColor"] = primary_color
        if secondary_color is not None:
            data["secondaryColor"] = secondary_color
        if tertiary_color is not None:
            data["tertiaryColor"] = tertiary_color
        if primary_text_color is not None:
            data["primaryTextColor"] = primary_text_color
        if primary_border_color is not None:
            data["primaryBorderColor"] = primary_border_color
        if line_color is not None:
            data["lineColor"] = line_color
        if plot_primary_color is not None:
            data["plotPrimaryColor"] = plot_primary_color
        if plot_secondary_color is not None:
            data["plotSecondaryColor"] = plot_secondary_color
        if plot_tertiary_color is not None:
            data["plotTertiaryColor"] = plot_tertiary_color
        if xy_background_color is not None:
            data["xyBackgroundColor"] = xy_background_color

        response = self._client.request("POST", "/charting_settings/update", data=data)
        return ChartingSettings.from_dict(response)

    def get(self, charting_settings_id: str) -> ChartingSettings:
        """Get a charting_settings by ID.

        Args:
            charting_settings_id: ID of the charting_settings to retrieve.

        Returns:
            The ChartingSettings object.
        """
        response = self._client.request("GET", f"/charting_settings/get/{charting_settings_id}")
        return ChartingSettings.from_dict(response)
