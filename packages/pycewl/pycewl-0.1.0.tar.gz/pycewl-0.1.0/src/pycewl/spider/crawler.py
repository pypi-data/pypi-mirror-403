"""Async web crawler for pycewl."""

from __future__ import annotations

import asyncio
import signal
from collections.abc import AsyncIterator

from rich.console import Console

from pycewl.config import CeWLConfig, CrawlResult
from pycewl.http.client import AsyncHTTPClient
from pycewl.spider.filters import URLFilter, extract_links
from pycewl.spider.url_manager import URLManager

console = Console()


class Crawler:
    """Async web crawler with depth tracking and concurrency control."""

    def __init__(self, config: CeWLConfig) -> None:
        """Initialize the crawler.

        Args:
            config: CeWL configuration.
        """
        self._config = config
        self._url_manager: URLManager | None = None
        self._url_filter: URLFilter | None = None
        self._shutdown_event = asyncio.Event()
        self._results: list[CrawlResult] = []
        self._active_tasks = 0
        self._lock = asyncio.Lock()

    @property
    def results(self) -> list[CrawlResult]:
        """Get collected crawl results."""
        return self._results.copy()

    @property
    def mailto_urls(self) -> set[str]:
        """Get collected mailto URLs."""
        if self._url_manager:
            return self._url_manager.mailto_urls
        return set()

    def _setup_signal_handlers(self) -> None:
        """Set up SIGINT handler for graceful shutdown."""
        loop = asyncio.get_event_loop()

        def signal_handler() -> None:
            if self._config.output.verbose:
                console.print("\n[yellow]Received interrupt, shutting down gracefully...[/yellow]")
            self._shutdown_event.set()

        try:
            loop.add_signal_handler(signal.SIGINT, signal_handler)
        except NotImplementedError:
            # Windows doesn't support add_signal_handler
            pass

    async def _process_url(
        self,
        client: AsyncHTTPClient,
        url: str,
        depth: int,
        semaphore: asyncio.Semaphore,
    ) -> CrawlResult | None:
        """Process a single URL.

        Args:
            client: HTTP client.
            url: URL to fetch.
            depth: Current depth.
            semaphore: Concurrency semaphore.

        Returns:
            CrawlResult if successful, None otherwise.
        """
        if self._shutdown_event.is_set():
            return None

        async with semaphore:
            if self._shutdown_event.is_set():
                return None

            if self._config.output.verbose:
                console.print(f"[dim]Fetching (depth={depth}): {url}[/dim]")

            result = await client.fetch(url)

            if result.error:
                if self._config.output.verbose:
                    console.print(f"[red]Error fetching {url}: {result.error}[/red]")
                return result

            # Extract and queue new links
            if result.html and self._url_filter and self._url_manager:
                links = extract_links(result.html, result.url)

                for link in links:
                    normalized = self._url_filter.normalize(link, result.url)
                    if normalized and self._url_filter.should_crawl(normalized):
                        await self._url_manager.add_url(
                            normalized,
                            referrer=result.url,
                            depth=depth + 1,
                        )

            return result

    async def crawl(self, seed_urls: list[str]) -> AsyncIterator[CrawlResult]:
        """Crawl starting from seed URLs.

        Args:
            seed_urls: List of seed URLs to start crawling from.

        Yields:
            CrawlResult for each crawled page.
        """
        if not seed_urls:
            return

        # Initialize URL manager and filter with first seed URL
        base_url = seed_urls[0]
        self._url_manager = URLManager(max_depth=self._config.spider.depth)
        self._url_filter = URLFilter(self._config.spider, base_url)

        # Add all seed URLs
        for url in seed_urls:
            await self._url_manager.add_seed(url)

        # Set up signal handlers
        self._setup_signal_handlers()

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self._config.spider.concurrency)

        async with AsyncHTTPClient(self._config) as client:
            pending_tasks: set[asyncio.Task[CrawlResult | None]] = set()

            while True:
                # Check for shutdown
                if self._shutdown_event.is_set():
                    break

                # Get next URL from queue
                node = await self._url_manager.get_next()

                if node is not None:
                    # Create task for this URL
                    task = asyncio.create_task(
                        self._process_url(client, node.url, node.depth, semaphore)
                    )
                    pending_tasks.add(task)

                # Process completed tasks
                if pending_tasks:
                    done, pending_tasks = await asyncio.wait(
                        pending_tasks,
                        timeout=0.1,
                        return_when=asyncio.FIRST_COMPLETED,
                    )

                    for task in done:
                        result = task.result()
                        if result is not None:
                            self._results.append(result)
                            yield result

                # Check if we're done
                if node is None and not pending_tasks:
                    # Wait a bit for any new URLs
                    await asyncio.sleep(0.1)
                    if self._url_manager.is_empty and not pending_tasks:
                        break

            # Cancel remaining tasks on shutdown
            if self._shutdown_event.is_set():
                for task in pending_tasks:
                    task.cancel()

                # Wait for cancellation
                if pending_tasks:
                    await asyncio.gather(*pending_tasks, return_exceptions=True)

    async def crawl_all(self, seed_urls: list[str]) -> list[CrawlResult]:
        """Crawl all URLs and return results.

        Args:
            seed_urls: List of seed URLs.

        Returns:
            List of all CrawlResults.
        """
        results: list[CrawlResult] = []
        async for result in self.crawl(seed_urls):
            results.append(result)
        return results
