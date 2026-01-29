"""Billing manager for handling billing operations."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..types import ListResponse, MonthCostsResponse

if TYPE_CHECKING:
    from ..client import ToothFairyClient


class BillingManager:
    """Manager for billing operations.

    This manager provides methods to create, update, and manage billing.

    Example:
        >>> client = ToothFairyClient(api_key="...", workspace_id="...")
        >>> billing = client.billing.get(...)
    """

    def __init__(self, client: "ToothFairyClient"):
        """Initialize the BillingManager.

        Args:
            client: The ToothFairyClient instance.
        """
        self._client = client

    def get_month_costs(self) -> MonthCostsResponse:
        """Get monthly usage and cost breakdown.

        Returns:
            The MonthCostsResponse object with API and training usage data.
        """
        response = self._client.request("GET", "/billing/monthCosts")
        return MonthCostsResponse.from_dict(response)
