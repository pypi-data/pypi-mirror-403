# Usage Guide

## Basic Usage

The simplest way to use pycewl is to provide a URL:

```bash
pycewl https://example.com
```

This will spider the site to depth 2 and output words to stdout.

### Save to File

```bash
pycewl https://example.com -w words.txt
```

### Show Word Counts

```bash
pycewl https://example.com -c
```

Output:
```
hello, 42
world, 38
example, 25
...
```

## Spider Configuration

### Depth

Control how deep to follow links:

```bash
# Only spider the target page
pycewl https://example.com -d 0

# Default depth (2)
pycewl https://example.com -d 2

# Deep spider
pycewl https://example.com -d 5
```

### Offsite Links

By default, pycewl only follows links on the same domain. To follow external links:

```bash
pycewl https://example.com -o
```

### Concurrency

Adjust the number of concurrent requests (default 10):

```bash
pycewl https://example.com --concurrency 20
```

## Word Filtering

### Length Filters

```bash
# Minimum 5 characters
pycewl https://example.com -m 5

# Maximum 10 characters
pycewl https://example.com -x 10

# Both
pycewl https://example.com -m 5 -x 10
```

### Case Conversion

```bash
# Convert all words to lowercase
pycewl https://example.com --lowercase
```

### Include Numbers

By default, words containing numbers are excluded:

```bash
# Include words with numbers (e.g., "Python3", "web2.0")
pycewl https://example.com --with-numbers
```

### German Umlaut Conversion

```bash
# Convert umlauts: ä→ae, ö→oe, ü→ue, ß→ss
pycewl https://example.com --convert-umlauts
```

## Email Extraction

Extract email addresses from pages:

```bash
# Print emails to stdout
pycewl https://example.com -e

# Save to file
pycewl https://example.com -e --email-file emails.txt
```

## Metadata Extraction

Extract author names from PDF and Office documents:

```bash
# Enable metadata extraction
pycewl https://example.com -a

# Save to file
pycewl https://example.com -a --meta-file authors.txt
```

## Authentication

### Basic Auth

```bash
pycewl https://example.com --auth-type basic \
    --auth-user username --auth-pass password
```

### Digest Auth

```bash
pycewl https://example.com --auth-type digest \
    --auth-user username --auth-pass password
```

### Bearer Token / JWT

For APIs or sites that use token-based authentication:

```bash
# Just provide the token (bearer type is auto-detected)
pycewl https://api.example.com --auth-token "your-access-token"

# With explicit auth type
pycewl https://api.example.com --auth-type bearer \
    --auth-token "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

The token is sent as an `Authorization: Bearer <token>` header with every request.

## Proxy Configuration

```bash
pycewl https://example.com \
    --proxy-host proxy.example.com \
    --proxy-port 8080

# With authentication
pycewl https://example.com \
    --proxy-host proxy.example.com \
    --proxy-port 8080 \
    --proxy-user proxyuser \
    --proxy-pass proxypass
```

## Custom Headers

Add custom HTTP headers:

```bash
pycewl https://example.com \
    -H "Authorization: Bearer token123" \
    -H "X-Custom-Header: value"
```

## Google Search Integration

Use Google to find seed URLs for spidering:

```bash
# Set up credentials first
export GOOGLE_API_KEY="your-key"
export GOOGLE_SEARCH_ENGINE_ID="your-cx"

# Search and spider
pycewl --google-keyword "star trek fan site" -w words.txt

# Combine with URL
pycewl https://startrek.com --google-keyword "star trek fan site" -w words.txt

# Limit search results
pycewl --google-keyword "star trek" --google-max-results 5 -w words.txt
```

## Smart Relevance Scoring

Group words by their relevance to your search query using Google's Natural Language API:

```bash
# Set up Google Cloud credentials
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"

# Enable relevance scoring
pycewl --google-keyword "star trek" --relevance-scoring -c

# Save to separate files
pycewl --google-keyword "star trek" --relevance-scoring \
    --related-file related.txt \
    --unrelated-file general.txt

# Adjust threshold (0.0-1.0, default 0.5)
pycewl --google-keyword "star trek" --relevance-scoring \
    --relevance-threshold 0.7
```

Output example:
```
=== Words Related to "star trek" ===
enterprise, 42
spock, 38
federation, 25
starfleet, 22

=== General Words (Not Query-Specific) ===
welcome, 15
contact, 12
page, 8
```

## Complete Example

```bash
# Full-featured spider with all options
pycewl https://startrek.com \
    -d 3 \
    -m 4 \
    --lowercase \
    -c \
    -w words.txt \
    -e --email-file emails.txt \
    -a --meta-file authors.txt \
    --google-keyword "star trek episodes" \
    --relevance-scoring \
    --related-file trek-words.txt \
    --unrelated-file general-words.txt \
    --concurrency 15 \
    -v
```
