"""Authorisation manager for handling authorisations operations."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..types import Authorisation, ListResponse

if TYPE_CHECKING:
    from ..client import ToothFairyClient


class AuthorisationManager:
    """Manager for authorisations operations.

    This manager provides methods to create, update, and manage authorisations.

    Example:
        >>> client = ToothFairyClient(api_key="...", workspace_id="...")
        >>> authorisation = client.authorisations.create(...)
    """

    def __init__(self, client: "ToothFairyClient"):
        """Initialize the AuthorisationManager.

        Args:
            client: The ToothFairyClient instance.
        """
        self._client = client

    def create(
        self,
        name: str,
        auth_type: str,
        token_secret: Optional[str] = None,
        description: Optional[str] = None,
        scope: Optional[str] = None,
        grant_type: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        authorization_base_url: Optional[str] = None,
        static_args: Optional[str] = None,
        token_base_url: Optional[str] = None,
    ) -> Authorisation:
        """Create a new authorisation.

        Args:
            name: Human-readable name for the authorisation.
            auth_type: Type of authorisation (bearer, apikey, oauth, password, env, generic, none, username_and_password, basic).
            token_secret: Token or secret value (encrypted).
            description: Description of the authorisation's purpose.
            scope: OAuth scope or permission scope.
            grant_type: OAuth grant type.
            client_id: OAuth client ID.
            client_secret: OAuth client secret (encrypted).
            authorization_base_url: OAuth authorization base URL.
            static_args: Static arguments as JSON string.
            token_base_url: OAuth token base URL.

        Returns:
            The created Authorisation object.
        """
        data: Dict[str, Any] = {
            "name": name,
            "type": auth_type,
        }

        if token_secret is not None:
            data["tokenSecret"] = token_secret
        if description is not None:
            data["description"] = description
        if scope is not None:
            data["scope"] = scope
        if grant_type is not None:
            data["grantType"] = grant_type
        if client_id is not None:
            data["clientId"] = client_id
        if client_secret is not None:
            data["clientSecret"] = client_secret
        if authorization_base_url is not None:
            data["authorizationBaseUrl"] = authorization_base_url
        if static_args is not None:
            data["staticArgs"] = static_args
        if token_base_url is not None:
            data["tokenBaseUrl"] = token_base_url

        response = self._client.request("POST", "/authorisation/create", data=data)
        return Authorisation.from_dict(response)

    def update(
        self,
        authorisation_id: str,
        **kwargs: Any,
    ) -> Authorisation:
        """Update a authorisation.

        Args:
            authorisation_id: ID of the authorisation to update.
            **kwargs: Fields to update.

        Returns:
            The updated Authorisation object.
        """
        data: Dict[str, Any] = {"id": authorisation_id}
        data.update(kwargs)
        response = self._client.request("POST", "/authorisation/update", data=data)
        return Authorisation.from_dict(response)

    def delete(self, authorisation_id: str) -> Dict[str, bool]:
        """Delete a authorisation.

        Args:
            authorisation_id: ID of the authorisation to delete.

        Returns:
            A dictionary with success status.
        """
        self._client.request("DELETE", f"/authorisation/delete/{authorisation_id}")
        return {"success": True}

    def get(self, authorisation_id: str) -> Authorisation:
        """Get a authorisation by ID.

        Args:
            authorisation_id: ID of the authorisation to retrieve.

        Returns:
            The Authorisation object.
        """
        response = self._client.request("GET", f"/authorisation/get/{authorisation_id}")
        return Authorisation.from_dict(response)

    def list(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> ListResponse:
        """List all authorisations.

        Args:
            limit: Maximum number of authorisations to return.
            offset: Number of authorisations to skip.

        Returns:
            A ListResponse containing the authorisations.
        """
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        response = self._client.request("GET", "/authorisation/list", params=params)

        items = []
        if isinstance(response, list):
            items = [Authorisation.from_dict(item) for item in response]
        elif isinstance(response, dict):
            items = [Authorisation.from_dict(item) for item in response.get("items", [])]

        return ListResponse(items=items)

    def get_by_type(self, auth_type: str) -> List[Authorisation]:
        """Get authorisations by type.

        Args:
            auth_type: Type of authorisation to filter by.

        Returns:
            A list of Authorisation objects with the specified type.
        """
        result = self.list()
        return [auth for auth in result.items if auth.type == auth_type]

    def search(self, search_term: str) -> List[Authorisation]:
        """Search authorisations by name.

        Args:
            search_term: Term to search for in authorisation names.

        Returns:
            A list of matching Authorisation objects.
        """
        all_auths = self.list()
        search_lower = search_term.lower()
        return [auth for auth in all_auths.items if search_lower in auth.name.lower()]
