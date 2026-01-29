"""Benchmark manager for handling benchmarks operations."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..types import Benchmark, ListResponse

if TYPE_CHECKING:
    from ..client import ToothFairyClient


class BenchmarkManager:
    """Manager for benchmarks operations.

    This manager provides methods to create, update, and manage benchmarks.

    Example:
        >>> client = ToothFairyClient(api_key="...", workspace_id="...")
        >>> benchmark = client.benchmarks.create(...)
    """

    def __init__(self, client: "ToothFairyClient"):
        """Initialize the BenchmarkManager.

        Args:
            client: The ToothFairyClient instance.
        """
        self._client = client

    def create(
        self,
        name: str,
        description: Optional[str] = None,
        questions: Optional[List[Dict[str, str]]] = None,
        files: Optional[List[str]] = None,
    ) -> Benchmark:
        """Create a new benchmark.

        Args:
            name: Benchmark name.
            description: Benchmark description.
            questions: List of test questions with expected answers.
            files: List of document IDs to use for testing.

        Returns:
            The created Benchmark object.
        """
        data: Dict[str, Any] = {
            "name": name,
        }

        if description is not None:
            data["description"] = description
        if questions is not None:
            data["questions"] = questions
        if files is not None:
            data["files"] = files

        response = self._client.request("POST", "/benchmark/create", data=data)
        return Benchmark.from_dict(response)

    def update(
        self,
        benchmark_id: str,
        **kwargs: Any,
    ) -> Benchmark:
        """Update a benchmark.

        Args:
            benchmark_id: ID of the benchmark to update.
            **kwargs: Fields to update.

        Returns:
            The updated Benchmark object.
        """
        data: Dict[str, Any] = {"id": benchmark_id}
        data.update(kwargs)
        response = self._client.request("POST", "/benchmark/update", data=data)
        return Benchmark.from_dict(response)

    def delete(self, benchmark_id: str) -> Dict[str, bool]:
        """Delete a benchmark.

        Args:
            benchmark_id: ID of the benchmark to delete.

        Returns:
            A dictionary with success status.
        """
        self._client.request("DELETE", f"/benchmark/delete/{benchmark_id}")
        return {"success": True}

    def get(self, benchmark_id: str) -> Benchmark:
        """Get a benchmark by ID.

        Args:
            benchmark_id: ID of the benchmark to retrieve.

        Returns:
            The Benchmark object.
        """
        response = self._client.request("GET", f"/benchmark/get/{benchmark_id}")
        return Benchmark.from_dict(response)

    def list(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> ListResponse:
        """List all benchmarks.

        Args:
            limit: Maximum number of benchmarks to return.
            offset: Number of benchmarks to skip.

        Returns:
            A ListResponse containing the benchmarks.
        """
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        response = self._client.request("GET", "/benchmark/list", params=params)

        items = []
        if isinstance(response, list):
            items = [Benchmark.from_dict(item) for item in response]
        elif isinstance(response, dict):
            items = [Benchmark.from_dict(item) for item in response.get("items", [])]

        return ListResponse(items=items)

    def search(self, search_term: str) -> List[Benchmark]:
        """Search benchmarks by name.

        Args:
            search_term: Term to search for in benchmark names.

        Returns:
            A list of matching Benchmark objects.
        """
        all_benchmarks = self.list()
        search_lower = search_term.lower()
        return [
            benchmark
            for benchmark in all_benchmarks.items
            if search_lower in benchmark.name.lower()
        ]
