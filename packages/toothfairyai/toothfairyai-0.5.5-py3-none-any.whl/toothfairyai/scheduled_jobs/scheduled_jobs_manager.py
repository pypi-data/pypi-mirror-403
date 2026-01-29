"""Scheduled Job manager for handling scheduled jobs operations."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..types import ListResponse, ScheduledJob

if TYPE_CHECKING:
    from ..client import ToothFairyClient


class ScheduledJobManager:
    """Manager for scheduled jobs operations.

    This manager provides methods to create, update, and manage scheduled jobs.

    Example:
        >>> client = ToothFairyClient(api_key="...", workspace_id="...")
        >>> scheduled_job = client.scheduled_jobs.create(...)
    """

    def __init__(self, client: "ToothFairyClient"):
        """Initialize the ScheduledJobManager.

        Args:
            client: The ToothFairyClient instance.
        """
        self._client = client

    def create(
        self,
        name: str,
        agent_id: Optional[str] = None,
        custom_prompt_id: Optional[str] = None,
        forced_prompt: Optional[str] = None,
        schedule: Optional[Dict[str, Any]] = None,
        timezone: Optional[str] = None,
        is_active: bool = True,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        description: Optional[str] = None,
    ) -> ScheduledJob:
        """Create a new scheduled job.

        Args:
            name: Job name.
            agent_id: ID of the agent to run.
            custom_prompt_id: ID of custom prompt to use.
            forced_prompt: Forced prompt text.
            schedule: Schedule configuration (cron expression).
            timezone: Timezone for the schedule.
            is_active: Whether the job is active.
            start_date: Start date for the job.
            end_date: End date for the job.
            description: Job description.

        Returns:
            The created ScheduledJob object.
        """
        data: Dict[str, Any] = {
            "name": name,
            "isActive": is_active,
        }

        if agent_id is not None:
            data["agentID"] = agent_id
        if custom_prompt_id is not None:
            data["customPromptID"] = custom_prompt_id
        if forced_prompt is not None:
            data["forcedPrompt"] = forced_prompt
        if schedule is not None:
            data["schedule"] = schedule
        if timezone is not None:
            data["timezone"] = timezone
        if start_date is not None:
            data["startDate"] = start_date
        if end_date is not None:
            data["endDate"] = end_date
        if description is not None:
            data["description"] = description

        response = self._client.request("POST", "/scheduled_job/create", data=data)
        return ScheduledJob.from_dict(response)

    def update(
        self,
        scheduled_job_id: str,
        **kwargs: Any,
    ) -> ScheduledJob:
        """Update a scheduled_job.

        Args:
            scheduled_job_id: ID of the scheduled_job to update.
            **kwargs: Fields to update.

        Returns:
            The updated ScheduledJob object.
        """
        data: Dict[str, Any] = {"id": scheduled_job_id}
        data.update(kwargs)
        response = self._client.request("POST", "/scheduled_job/update", data=data)
        return ScheduledJob.from_dict(response)

    def delete(self, scheduled_job_id: str) -> Dict[str, bool]:
        """Delete a scheduled_job.

        Args:
            scheduled_job_id: ID of the scheduled_job to delete.

        Returns:
            A dictionary with success status.
        """
        self._client.request("DELETE", f"/scheduled_job/delete/{scheduled_job_id}")
        return {"success": True}

    def get(self, scheduled_job_id: str) -> ScheduledJob:
        """Get a scheduled_job by ID.

        Args:
            scheduled_job_id: ID of the scheduled_job to retrieve.

        Returns:
            The ScheduledJob object.
        """
        response = self._client.request("GET", f"/scheduled_job/get/{scheduled_job_id}")
        return ScheduledJob.from_dict(response)

    def list(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> ListResponse:
        """List all scheduled jobs.

        Args:
            limit: Maximum number of scheduled jobs to return.
            offset: Number of scheduled jobs to skip.

        Returns:
            A ListResponse containing the scheduled jobs.
        """
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        response = self._client.request("GET", "/scheduled_job/list", params=params)

        items = []
        if isinstance(response, list):
            items = [ScheduledJob.from_dict(item) for item in response]
        elif isinstance(response, dict):
            items = [ScheduledJob.from_dict(item) for item in response.get("items", [])]

        return ListResponse(items=items)

    def get_active(self) -> List[ScheduledJob]:
        """Get all active scheduled jobs.

        Returns:
            A list of active ScheduledJob objects.
        """
        result = self.list()
        return [job for job in result.items if job.is_active]

    def get_by_agent(self, agent_id: str) -> List[ScheduledJob]:
        """Get scheduled jobs by agent ID.

        Args:
            agent_id: ID of the agent to filter by.

        Returns:
            A list of ScheduledJob objects for the specified agent.
        """
        result = self.list()
        return [job for job in result.items if job.agent_id == agent_id]

    def search(self, search_term: str) -> List[ScheduledJob]:
        """Search scheduled jobs by name.

        Args:
            search_term: Term to search for in job names.

        Returns:
            A list of matching ScheduledJob objects.
        """
        all_jobs = self.list()
        search_lower = search_term.lower()
        return [job for job in all_jobs.items if search_lower in job.name.lower()]
