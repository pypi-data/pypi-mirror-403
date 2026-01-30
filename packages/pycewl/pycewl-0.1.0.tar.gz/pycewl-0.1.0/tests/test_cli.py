"""Tests for CLI interface."""

from __future__ import annotations

from typer.testing import CliRunner

from pycewl.cli import app, parse_headers

runner = CliRunner()


class TestParseHeaders:
    """Tests for header parsing function."""

    def test_parse_single_header(self) -> None:
        """Test parsing single header."""
        headers = parse_headers(["Content-Type: application/json"])

        assert headers == {"Content-Type": "application/json"}

    def test_parse_multiple_headers(self) -> None:
        """Test parsing multiple headers."""
        headers = parse_headers([
            "Accept: text/html",
            "Authorization: Bearer token",
        ])

        assert headers == {
            "Accept": "text/html",
            "Authorization": "Bearer token",
        }

    def test_parse_header_with_colon_in_value(self) -> None:
        """Test parsing header with colon in value."""
        headers = parse_headers(["X-Custom: value:with:colons"])

        assert headers == {"X-Custom": "value:with:colons"}

    def test_parse_header_whitespace_trimmed(self) -> None:
        """Test that whitespace is trimmed."""
        headers = parse_headers(["  Name  :  Value  "])

        assert headers == {"Name": "Value"}

    def test_parse_empty_list(self) -> None:
        """Test parsing empty list."""
        headers = parse_headers([])

        assert headers == {}

    def test_parse_none(self) -> None:
        """Test parsing None."""
        headers = parse_headers(None)

        assert headers == {}


class TestCLIBasic:
    """Basic CLI tests."""

    def test_help(self) -> None:
        """Test help message."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "Custom Word List Generator" in result.stdout

    def test_version(self) -> None:
        """Test version display."""
        result = runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        assert "pycewl version" in result.stdout

    def test_no_args_shows_help(self) -> None:
        """Test no arguments shows help."""
        result = runner.invoke(app, [])

        # Should show help/error about missing arguments
        assert result.exit_code == 0 or "Error" in result.stdout

    def test_url_or_google_required(self) -> None:
        """Test that URL or --google-keyword is required."""
        # Run without URL or google keyword
        result = runner.invoke(app, ["--no-words"])

        assert result.exit_code != 0
        assert "URL" in result.stdout or "google-keyword" in result.stdout

    def test_relevance_requires_google_keyword(self) -> None:
        """Test --relevance-scoring requires --google-keyword."""
        result = runner.invoke(app, [
            "https://example.com",
            "--relevance-scoring",
        ])

        assert result.exit_code != 0
        assert "relevance-scoring requires" in result.stdout.lower()

    def test_invalid_auth_type(self) -> None:
        """Test invalid auth type."""
        result = runner.invoke(app, [
            "https://example.com",
            "--auth-type", "invalid",
        ])

        assert result.exit_code != 0
        assert "Invalid auth type" in result.stdout
