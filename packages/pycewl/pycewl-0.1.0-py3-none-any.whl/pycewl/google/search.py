"""Google Custom Search API integration for pycewl."""

from __future__ import annotations

import os
from dataclasses import dataclass

import httpx


@dataclass
class SearchResult:
    """A single search result."""

    title: str
    url: str
    snippet: str


class GoogleSearchError(Exception):
    """Error from Google Search API."""

    pass


class GoogleSearch:
    """Google Custom Search API client."""

    API_ENDPOINT = "https://www.googleapis.com/customsearch/v1"

    def __init__(
        self,
        api_key: str | None = None,
        search_engine_id: str | None = None,
    ) -> None:
        """Initialize the Google Search client.

        Args:
            api_key: Google API key. Falls back to GOOGLE_API_KEY env var.
            search_engine_id: Custom Search Engine ID. Falls back to
                GOOGLE_SEARCH_ENGINE_ID env var.
        """
        self._api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        self._search_engine_id = search_engine_id or os.environ.get("GOOGLE_SEARCH_ENGINE_ID")

    @property
    def is_configured(self) -> bool:
        """Check if the client is properly configured."""
        return bool(self._api_key and self._search_engine_id)

    async def search(
        self,
        query: str,
        max_results: int = 10,
    ) -> list[SearchResult]:
        """Search Google for URLs.

        Args:
            query: Search query string.
            max_results: Maximum number of results to return (max 100).

        Returns:
            List of SearchResult objects.

        Raises:
            GoogleSearchError: If API call fails.
            ValueError: If client is not configured.
        """
        if not self.is_configured:
            raise ValueError(
                "Google Search requires GOOGLE_API_KEY and GOOGLE_SEARCH_ENGINE_ID "
                "environment variables or constructor arguments"
            )

        results: list[SearchResult] = []
        start_index = 1

        async with httpx.AsyncClient() as client:
            while len(results) < max_results:
                # Google API returns max 10 results per request
                num = min(10, max_results - len(results))

                params = {
                    "key": self._api_key,
                    "cx": self._search_engine_id,
                    "q": query,
                    "num": num,
                    "start": start_index,
                }

                try:
                    response = await client.get(self.API_ENDPOINT, params=params)
                    response.raise_for_status()
                    data = response.json()
                except httpx.HTTPError as e:
                    raise GoogleSearchError(f"API request failed: {e}") from e

                # Check for API error
                if "error" in data:
                    error = data["error"]
                    raise GoogleSearchError(
                        f"API error {error.get('code')}: {error.get('message')}"
                    )

                # Extract results
                items = data.get("items", [])
                if not items:
                    break

                for item in items:
                    results.append(
                        SearchResult(
                            title=item.get("title", ""),
                            url=item.get("link", ""),
                            snippet=item.get("snippet", ""),
                        )
                    )

                # Check if there are more results
                if "nextPage" not in data.get("queries", {}):
                    break

                start_index += num

        return results[:max_results]

    async def get_urls(
        self,
        query: str,
        max_results: int = 10,
    ) -> list[str]:
        """Search Google and return just the URLs.

        Args:
            query: Search query string.
            max_results: Maximum number of results.

        Returns:
            List of URLs from search results.
        """
        results = await self.search(query, max_results)
        return [r.url for r in results]
