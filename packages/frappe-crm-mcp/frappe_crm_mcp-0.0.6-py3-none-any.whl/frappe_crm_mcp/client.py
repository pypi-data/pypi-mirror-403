"""Frappe REST API client."""

import json
import os
from functools import lru_cache
from typing import Any

import httpx


@lru_cache(maxsize=1)
def get_client() -> "FrappeClient":
    """Get the singleton Frappe client instance.

    Reads configuration from environment variables:
    - FRAPPE_URL: Base URL of the Frappe instance
    - FRAPPE_API_KEY: API key from Frappe user settings
    - FRAPPE_API_SECRET: API secret from Frappe user settings

    Returns:
        FrappeClient instance

    Raises:
        ValueError: If required environment variables are missing
    """
    url = os.environ.get("FRAPPE_URL")
    api_key = os.environ.get("FRAPPE_API_KEY")
    api_secret = os.environ.get("FRAPPE_API_SECRET")

    if not all([url, api_key, api_secret]):
        raise ValueError(
            "Missing required environment variables: FRAPPE_URL, FRAPPE_API_KEY, FRAPPE_API_SECRET"
        )

    return FrappeClient(url=url, api_key=api_key, api_secret=api_secret)


class FrappeClient:
    """Async HTTP client for Frappe REST API.

    Handles authentication and provides methods for standard Frappe
    document operations (list, get, create, update, delete) as well
    as calling whitelisted methods.
    """

    def __init__(self, url: str, api_key: str, api_secret: str) -> None:
        """Initialize the Frappe client.

        Args:
            url: Base URL of the Frappe instance (e.g., https://your-site.frappe.cloud)
            api_key: API key from Frappe user settings
            api_secret: API secret from Frappe user settings
        """
        self.base_url = url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"token {api_key}:{api_secret}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=30.0,
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def get_list(
        self,
        doctype: str,
        *,
        filters: dict[str, Any] | None = None,
        fields: list[str] | None = None,
        order_by: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Get list of documents.

        Args:
            doctype: Document type (e.g., "CRM Deal", "CRM Lead")
            filters: Filter conditions as dict
            fields: List of fields to return
            order_by: Sort order (e.g., "modified desc")
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of document dictionaries
        """
        params: dict[str, Any] = {
            "limit_page_length": limit,
            "limit_start": offset,
        }

        if filters:
            params["filters"] = json.dumps(filters)

        if fields:
            params["fields"] = json.dumps(fields)

        if order_by:
            params["order_by"] = order_by

        response = await self._client.get(
            f"/api/resource/{doctype}",
            params=params,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])

    async def get_doc(self, doctype: str, name: str) -> dict[str, Any]:
        """Get a single document by name.

        Args:
            doctype: Document type
            name: Document name/ID

        Returns:
            Document dictionary
        """
        response = await self._client.get(f"/api/resource/{doctype}/{name}")
        response.raise_for_status()
        data = response.json()
        return data.get("data", {})

    async def create_doc(self, doctype: str, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new document.

        Args:
            doctype: Document type
            data: Document fields

        Returns:
            Created document dictionary
        """
        response = await self._client.post(
            f"/api/resource/{doctype}",
            json=data,
        )
        response.raise_for_status()
        result = response.json()
        return result.get("data", {})

    async def update_doc(
        self, doctype: str, name: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an existing document.

        Args:
            doctype: Document type
            name: Document name/ID
            data: Fields to update

        Returns:
            Updated document dictionary
        """
        response = await self._client.put(
            f"/api/resource/{doctype}/{name}",
            json=data,
        )
        response.raise_for_status()
        result = response.json()
        return result.get("data", {})

    async def delete_doc(self, doctype: str, name: str) -> None:
        """Delete a document.

        Args:
            doctype: Document type
            name: Document name/ID
        """
        response = await self._client.delete(f"/api/resource/{doctype}/{name}")
        response.raise_for_status()

    async def call_method(self, method: str, **kwargs: Any) -> Any:
        """Call a whitelisted Frappe method.

        Args:
            method: Full method path (e.g., "crm.api.activities.get_activities")
            **kwargs: Method arguments

        Returns:
            Method response (typically in "message" key)
        """
        response = await self._client.post(
            f"/api/method/{method}",
            json=kwargs,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("message")
