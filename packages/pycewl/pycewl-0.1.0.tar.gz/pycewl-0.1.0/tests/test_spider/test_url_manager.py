"""Tests for URL manager."""

from __future__ import annotations

import pytest

from pycewl.spider.url_manager import URLManager, URLNode


class TestURLNode:
    """Tests for URLNode dataclass."""

    def test_basic_node(self) -> None:
        """Test basic URLNode creation."""
        node = URLNode(url="https://example.com", depth=0)

        assert node.url == "https://example.com"
        assert node.depth == 0
        assert node.referrer is None
        assert node.visited is False

    def test_node_with_referrer(self) -> None:
        """Test URLNode with referrer."""
        node = URLNode(
            url="https://example.com/page",
            depth=1,
            referrer="https://example.com",
        )

        assert node.referrer == "https://example.com"
        assert node.depth == 1

    def test_is_mailto(self) -> None:
        """Test mailto detection."""
        mailto_node = URLNode(url="mailto:test@example.com", depth=0)
        http_node = URLNode(url="https://example.com", depth=0)

        assert mailto_node.is_mailto is True
        assert http_node.is_mailto is False


class TestURLManager:
    """Tests for URLManager class."""

    @pytest.mark.asyncio
    async def test_add_seed(self) -> None:
        """Test adding seed URL."""
        manager = URLManager(max_depth=2)

        await manager.add_seed("https://example.com")

        assert manager.seen_count == 1
        assert manager.pending_count == 1

    @pytest.mark.asyncio
    async def test_add_seed_deduplication(self) -> None:
        """Test that duplicate seeds are ignored."""
        manager = URLManager(max_depth=2)

        await manager.add_seed("https://example.com")
        await manager.add_seed("https://example.com")

        assert manager.seen_count == 1
        assert manager.pending_count == 1

    @pytest.mark.asyncio
    async def test_add_url(self) -> None:
        """Test adding discovered URL."""
        manager = URLManager(max_depth=2)

        result = await manager.add_url(
            "https://example.com/page",
            referrer="https://example.com",
            depth=1,
        )

        assert result is True
        assert manager.seen_count == 1

    @pytest.mark.asyncio
    async def test_add_url_depth_limit(self) -> None:
        """Test URL rejected when over depth limit."""
        manager = URLManager(max_depth=2)

        result = await manager.add_url(
            "https://example.com/deep",
            referrer="https://example.com",
            depth=3,
        )

        assert result is False
        assert manager.seen_count == 0

    @pytest.mark.asyncio
    async def test_add_url_deduplication(self) -> None:
        """Test duplicate URLs are ignored."""
        manager = URLManager(max_depth=2)

        result1 = await manager.add_url(
            "https://example.com/page",
            referrer="https://example.com",
            depth=1,
        )
        result2 = await manager.add_url(
            "https://example.com/page",
            referrer="https://example.com",
            depth=1,
        )

        assert result1 is True
        assert result2 is False
        assert manager.seen_count == 1

    @pytest.mark.asyncio
    async def test_mailto_collection(self) -> None:
        """Test that mailto URLs are collected separately."""
        manager = URLManager(max_depth=2)

        result = await manager.add_url(
            "mailto:test@example.com",
            referrer="https://example.com",
            depth=1,
        )

        assert result is False  # Not added to queue
        assert "test@example.com" in manager.mailto_urls

    @pytest.mark.asyncio
    async def test_get_next(self) -> None:
        """Test getting next URL from queue."""
        manager = URLManager(max_depth=2)

        await manager.add_seed("https://example.com")
        node = await manager.get_next()

        assert node is not None
        assert node.url == "https://example.com"
        assert node.depth == 0

    @pytest.mark.asyncio
    async def test_get_next_empty(self) -> None:
        """Test getting from empty queue."""
        manager = URLManager(max_depth=2)

        node = await manager.get_next()

        assert node is None

    @pytest.mark.asyncio
    async def test_url_normalization(self) -> None:
        """Test URL normalization removes fragments."""
        manager = URLManager(max_depth=2)

        await manager.add_seed("https://example.com/page#section")
        await manager.add_seed("https://example.com/page")

        # Should be considered same URL
        assert manager.seen_count == 1

    @pytest.mark.asyncio
    async def test_is_empty(self) -> None:
        """Test is_empty property."""
        manager = URLManager(max_depth=2)

        assert manager.is_empty is True

        await manager.add_seed("https://example.com")
        assert manager.is_empty is False

        await manager.get_next()
        assert manager.is_empty is True
