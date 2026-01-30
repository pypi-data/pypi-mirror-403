"""Command-line interface for pycewl."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from pycewl.config import (
    AuthConfig,
    AuthType,
    CeWLConfig,
    GoogleConfig,
    HeaderConfig,
    OutputConfig,
    ProxyConfig,
    SpiderConfig,
    WordConfig,
)
from pycewl.extractors import WordExtractor, extract_emails
from pycewl.google import GoogleSearch, RelevanceScorer
from pycewl.google.nlp import NLPError
from pycewl.google.search import GoogleSearchError
from pycewl.output import write_emails, write_relevance_grouped, write_words
from pycewl.spider import Crawler

app = typer.Typer(
    name="pycewl",
    help="Custom Word List Generator - Python async implementation of CeWL",
    no_args_is_help=True,
)

console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        from pycewl import __version__

        console.print(f"pycewl version {__version__}")
        raise typer.Exit()


def parse_headers(headers: list[str] | None) -> dict[str, str]:
    """Parse header strings into a dictionary.

    Args:
        headers: List of "Name: Value" strings.

    Returns:
        Dictionary of headers.
    """
    result: dict[str, str] = {}
    if not headers:
        return result

    for header in headers:
        if ":" in header:
            name, value = header.split(":", 1)
            result[name.strip()] = value.strip()

    return result


async def run_crawler(config: CeWLConfig, seed_urls: list[str]) -> None:
    """Run the crawler and process results.

    Args:
        config: CeWL configuration.
        seed_urls: List of seed URLs to crawl.
    """
    crawler = Crawler(config)
    word_extractor = WordExtractor(config.word)
    all_emails: set[str] = set()
    pages_crawled = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Crawling...", total=None)

        async for result in crawler.crawl(seed_urls):
            pages_crawled += 1
            progress.update(task, description=f"Crawled {pages_crawled} pages...")

            if result.html and not config.output.no_words:
                word_extractor.process_html(result.html)

            # Extract emails if requested
            if result.html:
                emails = extract_emails(result.html)
                all_emails.update(emails)

        # Add mailto URLs collected during crawling
        all_emails.update(crawler.mailto_urls)

    # Get results
    words = word_extractor.get_sorted_words()

    # Handle relevance scoring if enabled
    if config.google.relevance_scoring and config.google.keyword:
        await _handle_relevance_scoring(config, words)
    elif not config.output.no_words:
        # Write normal word output
        write_words(
            words,
            output_path=config.output.word_file,
            show_count=config.output.show_count,
        )

    # Write emails if requested
    if all_emails and config.output.email_file:
        write_emails(all_emails, config.output.email_file)
        if config.output.verbose:
            console.print(f"[green]Wrote {len(all_emails)} emails to {config.output.email_file}")

    # Summary
    console.print("\n[bold]Results:[/bold]")
    console.print(f"  Pages crawled: {pages_crawled}")
    if not config.output.no_words:
        console.print(f"  Unique words: {len(words)}")
    if all_emails:
        console.print(f"  Emails found: {len(all_emails)}")


async def _handle_relevance_scoring(
    config: CeWLConfig,
    words: list[tuple[str, int]],
) -> None:
    """Handle relevance scoring for words.

    Args:
        config: CeWL configuration.
        words: List of (word, count) tuples.
    """
    keyword = config.google.keyword
    if not keyword:
        return

    try:
        scorer = RelevanceScorer(threshold=config.google.relevance_threshold)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("Analyzing query with NLP...", total=None)
            scorer.analyze_query(keyword)

        related, unrelated = scorer.classify_words(words)

        write_relevance_grouped(
            query=keyword,
            related=related,
            unrelated=unrelated,
            related_path=config.output.related_file,
            unrelated_path=config.output.unrelated_file,
            show_count=config.output.show_count,
        )

        console.print("\n[bold]Relevance Scoring:[/bold]")
        console.print(f"  Related words: {len(related)}")
        console.print(f"  Unrelated words: {len(unrelated)}")

    except NLPError as e:
        console.print(f"[yellow]Warning: Relevance scoring unavailable: {e}[/yellow]")
        console.print("[yellow]Falling back to standard word output[/yellow]")

        write_words(
            words,
            output_path=config.output.word_file,
            show_count=config.output.show_count,
        )


@app.command()
def main(
    url: Annotated[
        str | None,
        typer.Argument(help="Target URL to spider"),
    ] = None,
    # Spider options
    depth: Annotated[
        int,
        typer.Option("-d", "--depth", help="Spider depth"),
    ] = 2,
    offsite: Annotated[
        bool,
        typer.Option("-o", "--offsite", help="Allow spider to visit offsite URLs"),
    ] = False,
    user_agent: Annotated[
        str,
        typer.Option("--user-agent", "-u", help="User agent string"),
    ] = "Mozilla/5.0 (compatible; pycewl/0.1.0)",
    concurrency: Annotated[
        int,
        typer.Option("--concurrency", help="Number of concurrent requests"),
    ] = 10,
    # Word options
    min_word_length: Annotated[
        int,
        typer.Option("-m", "--min-word-length", help="Minimum word length"),
    ] = 3,
    max_word_length: Annotated[
        int | None,
        typer.Option("-x", "--max-word-length", help="Maximum word length"),
    ] = None,
    lowercase: Annotated[
        bool,
        typer.Option("--lowercase", help="Convert words to lowercase"),
    ] = False,
    with_numbers: Annotated[
        bool,
        typer.Option("--with-numbers", help="Include words with numbers"),
    ] = False,
    convert_umlauts: Annotated[
        bool,
        typer.Option("--convert-umlauts", help="Convert German umlauts to ASCII"),
    ] = False,
    groups: Annotated[
        int | None,
        typer.Option("-g", "--groups", help="Group words by count ranges"),
    ] = None,
    # Output options
    write: Annotated[
        Path | None,
        typer.Option("-w", "--write", help="Output file for words"),
    ] = None,
    no_words: Annotated[
        bool,
        typer.Option("-n", "--no-words", help="Don't output wordlist"),
    ] = False,
    count: Annotated[
        bool,
        typer.Option("-c", "--count", help="Show word counts"),
    ] = False,
    email: Annotated[
        bool,
        typer.Option("-e", "--email", help="Extract email addresses"),
    ] = False,
    email_file: Annotated[
        Path | None,
        typer.Option("--email-file", help="Output file for emails"),
    ] = None,
    meta: Annotated[
        bool,
        typer.Option("-a", "--meta", help="Extract metadata from documents"),
    ] = False,
    meta_file: Annotated[
        Path | None,
        typer.Option("--meta-file", help="Output file for metadata"),
    ] = None,
    keep: Annotated[
        bool,
        typer.Option("-k", "--keep", help="Keep downloaded files"),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option("-v", "--verbose", help="Verbose output"),
    ] = False,
    # Auth options
    auth_type: Annotated[
        str | None,
        typer.Option("--auth-type", help="Authentication type (basic/digest/bearer)"),
    ] = None,
    auth_user: Annotated[
        str | None,
        typer.Option("--auth-user", help="Authentication username"),
    ] = None,
    auth_pass: Annotated[
        str | None,
        typer.Option("--auth-pass", help="Authentication password"),
    ] = None,
    auth_token: Annotated[
        str | None,
        typer.Option("--auth-token", help="Bearer/JWT token for authentication"),
    ] = None,
    # Proxy options
    proxy_host: Annotated[
        str | None,
        typer.Option("--proxy-host", help="Proxy host"),
    ] = None,
    proxy_port: Annotated[
        int | None,
        typer.Option("--proxy-port", help="Proxy port"),
    ] = None,
    proxy_user: Annotated[
        str | None,
        typer.Option("--proxy-user", help="Proxy username"),
    ] = None,
    proxy_pass: Annotated[
        str | None,
        typer.Option("--proxy-pass", help="Proxy password"),
    ] = None,
    # HTTP options
    header: Annotated[
        list[str] | None,
        typer.Option("-H", "--header", help="HTTP headers (Name: Value)"),
    ] = None,
    # Google options
    google_keyword: Annotated[
        str | None,
        typer.Option("--google-keyword", help="Search Google for seed URLs"),
    ] = None,
    google_max_results: Annotated[
        int,
        typer.Option("--google-max-results", help="Maximum Google results"),
    ] = 10,
    # Relevance scoring options
    relevance_scoring: Annotated[
        bool,
        typer.Option("--relevance-scoring", help="Enable word relevance scoring"),
    ] = False,
    relevance_threshold: Annotated[
        float,
        typer.Option("--relevance-threshold", help="Score threshold for related words"),
    ] = 0.5,
    related_file: Annotated[
        Path | None,
        typer.Option("--related-file", help="Output file for query-related words"),
    ] = None,
    unrelated_file: Annotated[
        Path | None,
        typer.Option("--unrelated-file", help="Output file for unrelated words"),
    ] = None,
    # Version
    _version: Annotated[
        bool,
        typer.Option("--version", callback=version_callback, is_eager=True),
    ] = False,
) -> None:
    """pycewl - Custom Word List Generator.

    Spider a website and extract words for wordlist generation.
    """
    # Validate inputs
    if not url and not google_keyword:
        console.print("[red]Error: Either URL or --google-keyword is required[/red]")
        raise typer.Exit(1)

    if relevance_scoring and not google_keyword:
        console.print("[red]Error: --relevance-scoring requires --google-keyword[/red]")
        raise typer.Exit(1)

    # Build configuration
    auth_type_enum = AuthType.NONE
    if auth_token and not auth_type:
        # Shortcut: --auth-token without --auth-type implies bearer
        auth_type_enum = AuthType.BEARER
    elif auth_type:
        try:
            auth_type_enum = AuthType(auth_type.lower())
        except ValueError:
            console.print(f"[red]Error: Invalid auth type: {auth_type}[/red]")
            raise typer.Exit(1) from None

    config = CeWLConfig(
        url=url,
        spider=SpiderConfig(
            depth=depth,
            offsite=offsite,
            user_agent=user_agent,
            concurrency=concurrency,
        ),
        auth=AuthConfig(
            auth_type=auth_type_enum,
            username=auth_user,
            password=auth_pass,
            token=auth_token,
        ),
        proxy=ProxyConfig(
            host=proxy_host,
            port=proxy_port,
            username=proxy_user,
            password=proxy_pass,
        ),
        word=WordConfig(
            min_length=min_word_length,
            max_length=max_word_length,
            lowercase=lowercase,
            with_numbers=with_numbers,
            convert_umlauts=convert_umlauts,
            group_size=groups,
        ),
        output=OutputConfig(
            word_file=write,
            email_file=email_file if email else None,
            meta_file=meta_file if meta else None,
            related_file=related_file,
            unrelated_file=unrelated_file,
            show_count=count,
            no_words=no_words,
            verbose=verbose,
            keep_files=keep,
        ),
        google=GoogleConfig(
            keyword=google_keyword,
            max_results=google_max_results,
            relevance_scoring=relevance_scoring,
            relevance_threshold=relevance_threshold,
        ),
        http_headers=HeaderConfig(headers=parse_headers(header)),
    )

    # Determine seed URLs
    seed_urls: list[str] = []

    if google_keyword:
        # Use Google Search to find seed URLs
        try:
            search = GoogleSearch()
            if not search.is_configured:
                console.print(
                    "[yellow]Warning: Google Search not configured. "
                    "Set GOOGLE_API_KEY and GOOGLE_SEARCH_ENGINE_ID environment variables.[/yellow]"
                )
                if not url:
                    console.print("[red]Error: No URL provided and Google Search unavailable[/red]")
                    raise typer.Exit(1)
            else:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                ) as progress:
                    progress.add_task(f"Searching Google for '{google_keyword}'...", total=None)
                    seed_urls = asyncio.run(search.get_urls(google_keyword, google_max_results))

                console.print(f"[green]Found {len(seed_urls)} URLs from Google Search[/green]")

        except GoogleSearchError as e:
            console.print(f"[red]Google Search error: {e}[/red]")
            if not url:
                raise typer.Exit(1) from None

    # Add explicit URL if provided
    if url and url not in seed_urls:
        seed_urls.insert(0, url)

    if not seed_urls:
        console.print("[red]Error: No URLs to crawl[/red]")
        raise typer.Exit(1)

    # Run the crawler
    try:
        asyncio.run(run_crawler(config, seed_urls))
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        raise typer.Exit(130) from None


if __name__ == "__main__":
    app()
