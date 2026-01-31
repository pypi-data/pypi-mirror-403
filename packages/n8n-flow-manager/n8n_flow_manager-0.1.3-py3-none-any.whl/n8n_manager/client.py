"""Main N8N Client."""

import os
from typing import Optional

import httpx
from dotenv import load_dotenv

from .api.credentials import CredentialAPI
from .api.executions import ExecutionAPI
from .api.workflows import WorkflowAPI
from .exceptions import N8NAPIError, N8NAuthError, N8NRateLimitError


class N8NClient:
    """
    Main async client for interacting with the n8n Public API.

    Provides access to workflows, executions, and credentials through
    dedicated API modules with proper error handling and retry logic.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        poll_interval: int = 2,
        max_poll_timeout: int = 300,
    ) -> None:
        """
        Initialize the N8N client.

        Args:
            api_key: n8n API key (or set N8N_API_KEY env var)
            base_url: n8n instance URL (or set N8N_BASE_URL env var)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            poll_interval: Seconds between execution status polls
            max_poll_timeout: Maximum time to wait for execution completion

        Raises:
            N8NAuthError: If API key or base URL is not provided
        """
        # Load environment variables
        load_dotenv()

        # Get configuration from args or environment
        self.api_key = api_key or os.getenv("N8N_API_KEY")
        self.base_url = base_url or os.getenv("N8N_BASE_URL")

        if not self.api_key:
            raise N8NAuthError(
                "API key is required. Provide via api_key parameter or N8N_API_KEY environment variable."
            )

        if not self.base_url:
            raise N8NAuthError(
                "Base URL is required. Provide via base_url parameter or N8N_BASE_URL environment variable."
            )

        # Prepare headers
        self.headers = {
            "X-N8N-API-KEY": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Create async HTTP client with retry logic
        transport = httpx.AsyncHTTPTransport(retries=max_retries)

        self._client = httpx.AsyncClient(
            base_url=f"{self.base_url.rstrip('/')}/api/v1",
            headers=self.headers,
            timeout=timeout,
            transport=transport,
            event_hooks={"response": [self._handle_response_errors]},
        )

        # Initialize API modules
        self.workflows = WorkflowAPI(self._client)
        self.executions = ExecutionAPI(
            self._client,
            poll_interval=poll_interval,
            max_poll_timeout=max_poll_timeout,
        )
        self.credentials = CredentialAPI(self._client)

    async def _handle_response_errors(self, response: httpx.Response) -> None:
        """
        Handle common HTTP errors across all requests.

        Args:
            response: HTTP response object
        """
        if response.status_code == 401:
            raise N8NAuthError(
                "Authentication failed. Check your API key.",
                details={"status_code": 401},
            )
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise N8NRateLimitError(
                retry_after=int(retry_after) if retry_after else None,
            )
        elif response.status_code >= 500:
            raise N8NAPIError(
                f"n8n server error: {response.status_code}",
                status_code=response.status_code,
                response=response.json() if response.content else None,
            )

    async def close(self) -> None:
        """Close the HTTP client and cleanup resources."""
        await self._client.aclose()

    async def __aenter__(self) -> "N8NClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        """Async context manager exit."""
        await self.close()

    async def health_check(self) -> bool:
        """
        Perform a health check by attempting to list workflows.

        Returns:
            True if the connection is healthy

        Raises:
            N8NAuthError: If authentication fails
            N8NAPIError: If the API is not accessible
        """
        try:
            await self.workflows.list()
            return True
        except Exception as e:
            raise N8NAPIError(f"Health check failed: {e}")
