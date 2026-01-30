"""Configuration dataclasses for pycewl."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class AuthType(str, Enum):
    """Authentication type enumeration."""

    NONE = "none"
    BASIC = "basic"
    DIGEST = "digest"
    BEARER = "bearer"


@dataclass(frozen=True)
class SpiderConfig:
    """Configuration for the web spider."""

    depth: int = 2
    offsite: bool = False
    user_agent: str = "Mozilla/5.0 (compatible; pycewl/0.1.0)"
    exclude_paths: tuple[str, ...] = ()
    allowed_pattern: str | None = None
    concurrency: int = 10
    timeout: float = 30.0
    verify_ssl: bool = False
    follow_redirects: bool = True


@dataclass(frozen=True)
class AuthConfig:
    """Configuration for HTTP authentication."""

    auth_type: AuthType = AuthType.NONE
    username: str | None = None
    password: str | None = None
    token: str | None = None


@dataclass(frozen=True)
class ProxyConfig:
    """Configuration for HTTP proxy."""

    host: str | None = None
    port: int | None = None
    username: str | None = None
    password: str | None = None

    @property
    def url(self) -> str | None:
        """Get the proxy URL."""
        if not self.host:
            return None

        if self.username and self.password:
            auth = f"{self.username}:{self.password}@"
        else:
            auth = ""

        port = f":{self.port}" if self.port else ""
        return f"http://{auth}{self.host}{port}"


@dataclass(frozen=True)
class WordConfig:
    """Configuration for word extraction."""

    min_length: int = 3
    max_length: int | None = None
    lowercase: bool = False
    with_numbers: bool = False
    convert_umlauts: bool = False
    group_size: int | None = None


@dataclass(frozen=True)
class OutputConfig:
    """Configuration for output."""

    word_file: Path | None = None
    email_file: Path | None = None
    meta_file: Path | None = None
    related_file: Path | None = None
    unrelated_file: Path | None = None
    show_count: bool = False
    no_words: bool = False
    verbose: bool = False
    keep_files: bool = False


@dataclass(frozen=True)
class GoogleConfig:
    """Configuration for Google services."""

    api_key: str | None = None
    search_engine_id: str | None = None
    keyword: str | None = None
    max_results: int = 10
    relevance_scoring: bool = False
    relevance_threshold: float = 0.5


@dataclass(frozen=True)
class HeaderConfig:
    """Configuration for HTTP headers."""

    headers: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class CeWLConfig:
    """Aggregate configuration for CeWL."""

    url: str | None = None
    spider: SpiderConfig = field(default_factory=SpiderConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    word: WordConfig = field(default_factory=WordConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    google: GoogleConfig = field(default_factory=GoogleConfig)
    http_headers: HeaderConfig = field(default_factory=HeaderConfig)

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if not self.url and not self.google.keyword:
            pass  # Allow empty for now, validation happens at runtime


@dataclass
class CrawlResult:
    """Result from crawling a single page."""

    url: str
    status_code: int
    content_type: str
    html: str | None = None
    error: str | None = None
    redirected_from: str | None = None


@dataclass
class WordResult:
    """Result from word extraction."""

    word: str
    count: int
    sources: set[str] = field(default_factory=set)


@dataclass
class RelevanceResult:
    """Result from relevance scoring."""

    word: str
    count: int
    score: float
    is_related: bool
    entity_type: str | None = None
