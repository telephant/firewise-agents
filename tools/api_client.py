"""
API Client for Firewise API

Handles authenticated HTTP requests to the firewise-api service.
"""

import httpx
import logging
from typing import Optional, Any
from contextvars import ContextVar

logger = logging.getLogger(__name__)

# Context variable for per-request client
_api_client_var: ContextVar[Optional["APIClient"]] = ContextVar(
    "api_client", default=None
)


class APIClient:
    """HTTP client for firewise-api calls."""

    def __init__(self, base_url: str, auth_token: str):
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token
        self.headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        }

    async def request(
        self,
        method: str,
        path: str,
        data: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> dict:
        """
        Make authenticated request to API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API path (e.g., "/fire/assets")
            data: Request body for POST/PUT
            params: Query parameters for GET

        Returns:
            API response as dict

        Raises:
            httpx.HTTPStatusError: On 4xx/5xx responses
        """
        url = f"{self.base_url}{path}"
        logger.info(f"API Request: {method} {url}")

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                params=params,
                timeout=30.0,
            )

            # Log response status
            logger.info(f"API Response: {response.status_code}")

            # Raise on error status
            response.raise_for_status()

            return response.json()

    async def get(self, path: str, params: Optional[dict] = None) -> dict:
        """GET request."""
        return await self.request("GET", path, params=params)

    async def post(self, path: str, data: dict) -> dict:
        """POST request."""
        return await self.request("POST", path, data=data)

    async def put(self, path: str, data: dict) -> dict:
        """PUT request."""
        return await self.request("PUT", path, data=data)

    async def delete(self, path: str) -> dict:
        """DELETE request."""
        return await self.request("DELETE", path)


# =============================================================================
# Context Management
# =============================================================================


def set_api_client(base_url: str, auth_token: str) -> APIClient:
    """
    Set the API client for the current request context.

    Call this at the start of each chat request to set up
    the authenticated client.
    """
    client = APIClient(base_url, auth_token)
    _api_client_var.set(client)
    return client


def get_api_client() -> APIClient:
    """
    Get the API client for the current context.

    Raises:
        RuntimeError: If no client has been set
    """
    client = _api_client_var.get()
    if client is None:
        raise RuntimeError(
            "API client not initialized. Call set_api_client() first."
        )
    return client


def clear_api_client() -> None:
    """Clear the API client from context."""
    _api_client_var.set(None)
