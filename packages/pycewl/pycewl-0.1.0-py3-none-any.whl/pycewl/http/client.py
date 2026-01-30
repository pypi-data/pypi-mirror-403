"""Async HTTP client wrapper for pycewl."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import httpx

from pycewl.config import CeWLConfig, CrawlResult
from pycewl.http.auth import create_auth, create_auth_headers

if TYPE_CHECKING:
    from collections.abc import Mapping


class AsyncHTTPClient:
    """Async HTTP client wrapper using httpx."""

    def __init__(self, config: CeWLConfig) -> None:
        """Initialize the HTTP client.

        Args:
            config: CeWL configuration.
        """
        self._config = config
        self._client: httpx.AsyncClient | None = None

    def _build_client(self) -> httpx.AsyncClient:
        """Build and configure the httpx client."""
        auth = create_auth(self._config.auth)
        auth_headers = create_auth_headers(self._config.auth)
        proxy_url = self._config.proxy.url

        headers: dict[str, str] = {
            "User-Agent": self._config.spider.user_agent,
            **auth_headers,
            **self._config.http_headers.headers,
        }

        return httpx.AsyncClient(
            auth=auth,
            proxy=proxy_url,
            headers=headers,
            timeout=httpx.Timeout(self._config.spider.timeout),
            verify=self._config.spider.verify_ssl,
            follow_redirects=self._config.spider.follow_redirects,
        )

    async def __aenter__(self) -> AsyncHTTPClient:
        """Enter the async context manager."""
        self._client = self._build_client()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit the async context manager."""
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get the underlying httpx client."""
        if self._client is None:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        return self._client

    async def fetch(
        self,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
    ) -> CrawlResult:
        """Fetch a URL and return the result.

        Args:
            url: URL to fetch.
            headers: Optional additional headers.

        Returns:
            CrawlResult with the response data.
        """
        try:
            response = await self.client.get(url, headers=dict(headers) if headers else None)

            content_type = response.headers.get("content-type", "")
            html: str | None = None
            redirected_from: str | None = None

            # Check if this was a redirect
            if response.history:
                redirected_from = str(response.history[0].url)

            # Only read text content for HTML/text responses
            if "text/" in content_type or "html" in content_type:
                html = response.text

            return CrawlResult(
                url=str(response.url),
                status_code=response.status_code,
                content_type=content_type,
                html=html,
                redirected_from=redirected_from,
            )

        except httpx.TimeoutException:
            return CrawlResult(
                url=url,
                status_code=0,
                content_type="",
                error="Request timed out",
            )
        except httpx.ConnectError as e:
            return CrawlResult(
                url=url,
                status_code=0,
                content_type="",
                error=f"Connection error: {e}",
            )
        except httpx.HTTPError as e:
            return CrawlResult(
                url=url,
                status_code=0,
                content_type="",
                error=f"HTTP error: {e}",
            )

    async def fetch_binary(self, url: str) -> tuple[bytes | None, str | None]:
        """Fetch binary content from a URL.

        Args:
            url: URL to fetch.

        Returns:
            Tuple of (content bytes, error message).
        """
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.content, None
        except httpx.HTTPError as e:
            return None, str(e)


@asynccontextmanager
async def create_client(config: CeWLConfig) -> AsyncGenerator[AsyncHTTPClient, None]:
    """Create an async HTTP client context manager.

    Args:
        config: CeWL configuration.

    Yields:
        Configured AsyncHTTPClient.
    """
    client = AsyncHTTPClient(config)
    async with client:
        yield client
