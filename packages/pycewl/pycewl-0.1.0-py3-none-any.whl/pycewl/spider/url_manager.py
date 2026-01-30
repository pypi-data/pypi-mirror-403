"""URL management for depth-aware crawling."""

from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class URLNode:
    """A node in the URL tree, tracking depth and referrer."""

    url: str
    depth: int
    referrer: str | None = None
    visited: bool = False

    @property
    def is_mailto(self) -> bool:
        """Check if this is a mailto link."""
        return self.url.startswith("mailto:")


class URLManager:
    """Manages URL queue with depth tracking.

    """

    def __init__(self, max_depth: int) -> None:
        """Initialize the URL manager.

        Args:
            max_depth: Maximum crawl depth.
        """
        self._max_depth = max_depth
        self._queue: asyncio.Queue[URLNode] = asyncio.Queue()
        self._seen: set[str] = set()
        self._mailto_urls: set[str] = set()
        self._lock = asyncio.Lock()

    @property
    def max_depth(self) -> int:
        """Get the maximum crawl depth."""
        return self._max_depth

    @property
    def seen_count(self) -> int:
        """Get the number of seen URLs."""
        return len(self._seen)

    @property
    def mailto_urls(self) -> set[str]:
        """Get collected mailto URLs."""
        return self._mailto_urls.copy()

    def _normalize_url(self, url: str) -> str:
        """Normalize a URL for deduplication.

        Args:
            url: URL to normalize.

        Returns:
            Normalized URL string.
        """
        # Remove fragment
        parsed = urlparse(url)
        normalized = parsed._replace(fragment="")
        return normalized.geturl()

    async def add_seed(self, url: str) -> None:
        """Add a seed URL at depth 0.

        Args:
            url: Seed URL to add.
        """
        normalized = self._normalize_url(url)

        async with self._lock:
            if normalized not in self._seen:
                self._seen.add(normalized)
                node = URLNode(url=normalized, depth=0)
                await self._queue.put(node)

    async def add_url(self, url: str, referrer: str, depth: int) -> bool:
        """Add a discovered URL.

        Args:
            url: URL to add.
            referrer: URL that linked to this URL.
            depth: Current crawl depth.

        Returns:
            True if URL was added, False if already seen or too deep.
        """
        # Handle mailto links specially - collect but don't crawl
        if url.startswith("mailto:"):
            async with self._lock:
                email = url.replace("mailto:", "").split("?")[0]
                self._mailto_urls.add(email)
            return False

        # Check depth limit
        if depth > self._max_depth:
            return False

        normalized = self._normalize_url(url)

        async with self._lock:
            if normalized in self._seen:
                return False

            self._seen.add(normalized)
            node = URLNode(url=normalized, depth=depth, referrer=referrer)
            await self._queue.put(node)
            return True

    async def get_next(self) -> URLNode | None:
        """Get the next URL to crawl.

        Returns:
            Next URLNode, or None if queue is empty.
        """
        try:
            return self._queue.get_nowait()
        except asyncio.QueueEmpty:
            return None

    async def wait_for_next(self, wait_seconds: float = 1.0) -> URLNode | None:
        """Wait for the next URL to crawl.

        Args:
            wait_seconds: Maximum time to wait in seconds.

        Returns:
            Next URLNode, or None if timeout reached.
        """
        try:
            return await asyncio.wait_for(self._queue.get(), timeout=wait_seconds)
        except TimeoutError:
            return None

    def mark_done(self) -> None:
        """Mark current task as done."""
        with contextlib.suppress(ValueError):
            self._queue.task_done()

    @property
    def is_empty(self) -> bool:
        """Check if the queue is empty."""
        return self._queue.empty()

    @property
    def pending_count(self) -> int:
        """Get the number of pending URLs."""
        return self._queue.qsize()
