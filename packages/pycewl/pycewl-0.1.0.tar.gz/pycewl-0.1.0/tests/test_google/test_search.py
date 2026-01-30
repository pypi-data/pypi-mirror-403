"""Tests for Google Search integration."""

from __future__ import annotations

import pytest

from pycewl.google.search import GoogleSearch, SearchResult


class TestGoogleSearch:
    """Tests for GoogleSearch class."""

    def test_not_configured_without_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test is_configured returns False without env vars."""
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_SEARCH_ENGINE_ID", raising=False)

        search = GoogleSearch()

        assert search.is_configured is False

    def test_configured_with_args(self) -> None:
        """Test is_configured returns True with constructor args."""
        search = GoogleSearch(
            api_key="test-key",
            search_engine_id="test-id",
        )

        assert search.is_configured is True

    def test_configured_with_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test is_configured returns True with env vars."""
        monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
        monkeypatch.setenv("GOOGLE_SEARCH_ENGINE_ID", "test-id")

        search = GoogleSearch()

        assert search.is_configured is True

    @pytest.mark.asyncio
    async def test_search_requires_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test search raises error when not configured."""
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_SEARCH_ENGINE_ID", raising=False)

        search = GoogleSearch()

        with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
            await search.search("test query")


class TestSearchResult:
    """Tests for SearchResult dataclass."""

    def test_creation(self) -> None:
        """Test SearchResult creation."""
        result = SearchResult(
            title="Test Title",
            url="https://example.com",
            snippet="This is a test snippet",
        )

        assert result.title == "Test Title"
        assert result.url == "https://example.com"
        assert result.snippet == "This is a test snippet"
