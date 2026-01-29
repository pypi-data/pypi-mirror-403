"""API Keys resource."""

from __future__ import annotations

from planvantage.models.apikey import ApiKeyCreateResponse, ApiKeyData
from planvantage.resources.base import BaseResource


class ApiKeysResource(BaseResource):
    """Resource for managing API keys."""

    def list(self) -> list[ApiKeyData]:
        """List all API keys for the current user.

        Returns:
            List of API key data (keys are masked, showing only prefix).

        Example:
            >>> keys = client.api_keys.list()
            >>> for key in keys:
            ...     print(f"{key.name}: {key.key_prefix}...")
        """
        data = self._http.get("/apikeys")
        if isinstance(data, list):
            return [ApiKeyData.model_validate(item) for item in data]
        return []

    def create(self, name: str) -> ApiKeyCreateResponse:
        """Create a new API key.

        Args:
            name: Name/description for the API key.

        Returns:
            Response containing the full API key (only shown once).

        Example:
            >>> result = client.api_keys.create("Production Key")
            >>> print(f"Save this key: {result.key}")  # Only chance to see full key
        """
        data = self._http.post("/apikeys", json={"name": name})
        return ApiKeyCreateResponse.model_validate(data)

    def revoke(self, guid: str) -> None:
        """Revoke an API key (soft delete).

        The key will no longer work for authentication but
        remains in the list with a revoked_at timestamp.

        Args:
            guid: The API key's GUID.

        Example:
            >>> client.api_keys.revoke("key_abc123")
        """
        self._http.post("/apikeys/revoke", json={"guid": guid})

    def delete(self, guid: str) -> None:
        """Delete an API key permanently.

        Args:
            guid: The API key's GUID.

        Example:
            >>> client.api_keys.delete("key_abc123")
        """
        self._http.delete(f"/apikeys/{guid}")
