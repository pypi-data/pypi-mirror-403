# CLI Reference

Complete reference for all pycewl command-line options.

## Synopsis

```
pycewl [OPTIONS] [URL]
```

## Arguments

### URL

Target URL to spider. Optional if `--google-keyword` is provided.

## Options

### Spider Options

| Option | Default | Description |
|--------|---------|-------------|
| `-d, --depth INT` | 2 | Spider depth. How many levels of links to follow. |
| `-o, --offsite` | False | Allow following links to other domains. |
| `-u, --user-agent TEXT` | `Mozilla/5.0 (compatible; pycewl/0.1.0)` | User-Agent header for requests. |
| `--concurrency INT` | 10 | Number of concurrent HTTP requests. |

### Word Options

| Option | Default | Description |
|--------|---------|-------------|
| `-m, --min-word-length INT` | 3 | Minimum word length to include. |
| `-x, --max-word-length INT` | None | Maximum word length to include. |
| `--lowercase` | False | Convert all words to lowercase. |
| `--with-numbers` | False | Include words containing numbers (e.g., "web2.0"). |
| `--convert-umlauts` | False | Convert German umlauts to ASCII (ä→ae, ö→oe, ü→ue, ß→ss). |
| `-g, --groups INT` | None | Group words by count ranges. |

### Output Options

| Option | Default | Description |
|--------|---------|-------------|
| `-w, --write PATH` | stdout | Output file for wordlist. |
| `-n, --no-words` | False | Don't output the wordlist. |
| `-c, --count` | False | Show word occurrence counts. |
| `-e, --email` | False | Extract email addresses. |
| `--email-file PATH` | stdout | Output file for emails. |
| `-a, --meta` | False | Extract metadata from documents. |
| `--meta-file PATH` | stdout | Output file for metadata. |
| `-k, --keep` | False | Keep downloaded document files. |
| `-v, --verbose` | False | Enable verbose output. |

### Authentication Options

| Option | Default | Description |
|--------|---------|-------------|
| `--auth-type TEXT` | None | Authentication type: `basic`, `digest`, or `bearer`. |
| `--auth-user TEXT` | None | Username for authentication. |
| `--auth-pass TEXT` | None | Password for authentication. |
| `--auth-token TEXT` | None | Bearer/JWT token. When provided without `--auth-type`, bearer is assumed. |

### Proxy Options

| Option | Default | Description |
|--------|---------|-------------|
| `--proxy-host TEXT` | None | Proxy server hostname. |
| `--proxy-port INT` | None | Proxy server port. |
| `--proxy-user TEXT` | None | Proxy authentication username. |
| `--proxy-pass TEXT` | None | Proxy authentication password. |

### HTTP Options

| Option | Default | Description |
|--------|---------|-------------|
| `-H, --header TEXT` | None | Custom HTTP header in "Name: Value" format. Can be specified multiple times. |

### Google Options

| Option | Default | Description |
|--------|---------|-------------|
| `--google-keyword TEXT` | None | Search Google for seed URLs using this query. Requires `GOOGLE_API_KEY` and `GOOGLE_SEARCH_ENGINE_ID` environment variables. |
| `--google-max-results INT` | 10 | Maximum number of Google search results to use as seeds. |

### Relevance Scoring Options

| Option | Default | Description |
|--------|---------|-------------|
| `--relevance-scoring` | False | Enable word relevance scoring using Google NLP. Requires `--google-keyword`. |
| `--relevance-threshold FLOAT` | 0.5 | Score threshold (0.0-1.0) for classifying words as "related" to the query. |
| `--related-file PATH` | stdout | Output file for query-related words. |
| `--unrelated-file PATH` | stdout | Output file for general/unrelated words. |

### General Options

| Option | Description |
|--------|-------------|
| `--version` | Show version and exit. |
| `--help` | Show help message and exit. |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GOOGLE_API_KEY` | Google API key for Custom Search API. |
| `GOOGLE_SEARCH_ENGINE_ID` | Google Programmable Search Engine ID (cx). |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to Google Cloud service account JSON key for NLP API. |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 130 | Interrupted by user (Ctrl+C) |

## Examples

### Basic Spider

```bash
pycewl https://example.com -w words.txt
```

### Deep Spider with Counts

```bash
pycewl https://example.com -d 5 -c -w words.txt
```

### Extract Everything

```bash
pycewl https://example.com \
    -w words.txt \
    -e --email-file emails.txt \
    -a --meta-file authors.txt
```

### Google Search + Relevance Scoring

```bash
pycewl --google-keyword "machine learning tutorial" \
    --relevance-scoring \
    --related-file ml-terms.txt \
    --unrelated-file general.txt \
    -c
```

### Bearer Token Authentication

```bash
# Token auto-detects bearer type
pycewl https://api.example.com \
    --auth-token "eyJhbGciOiJIUzI1NiIs..." \
    -w words.txt

# Explicit bearer type
pycewl https://api.example.com \
    --auth-type bearer \
    --auth-token "your-access-token" \
    -w words.txt
```

### Authenticated with Proxy

```bash
pycewl https://internal.example.com \
    --auth-type basic \
    --auth-user admin \
    --auth-pass secret \
    --proxy-host proxy.corp.com \
    --proxy-port 8080 \
    -w words.txt
```
