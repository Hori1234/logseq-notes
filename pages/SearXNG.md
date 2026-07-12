---
title: SearXNG
tags: [mcp, searxng, search, privacy]
status: active
source: https://github.com/searxng/searxng
---

# SearXNG — Privacy-Respecting Meta-Search

> Aggregate results from Google, Bing, DuckDuckGo and dozens more — with JSON API output enabled for programmatic use.

## What It Does

[SearXNG](https://searxng.github.io/searxng/) is a self-hosted, privacy-respecting metasearch engine. In this stack it serves as:

1. A **human-friendly search UI** at http://localhost:8080
2. A **JSON API** for AI agents and MCP tools to query search results programmatically

## JSON API (Critical for MCP Use)

The `settings.yml` includes `json` in the `formats` list, which enables:

```
GET http://localhost:8080/search?q=your+query&format=json
```

### Example response structure

```json
{
  "query": "python asyncio",
  "number_of_results": 1200000,
  "results": [
    {
      "title": "asyncio — Asynchronous I/O",
      "url": "https://docs.python.org/3/library/asyncio.html",
      "content": "This module provides infrastructure for writing single-threaded concurrent code...",
      "engine": "google",
      "score": 1.0
    }
  ]
}
```

### Full API parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `q` | string | Search query |
| `format` | `json`, `html`, `csv`, `rss` | Output format |
| `language` | `en`, `de`, etc. | Language filter |
| `time_range` | `day`, `week`, `month`, `year` | Recency filter |
| `categories` | `general`, `images`, `news`, `science` | Category filter |
| `engines` | `google,bing` | Comma-separated engines |
| `pageno` | integer | Page number |

### Example: search with curl

```bash
curl "http://localhost:8080/search?q=docker+compose+tutorial&format=json" | jq '.results[].title'
```

## Docker Compose Config

```yaml
searxng:
  image: searxng/searxng:latest
  depends_on:
    valkey:
      condition: service_healthy
  environment:
    SEARXNG_BASE_URL: http://localhost:8080/
    SEARXNG_SECRET: ${SEARXNG_SECRET}
  volumes:
    - ./config/searxng:/etc/searxng:rw
  ports:
    - "8080:8080"
```

## SearXNG Settings (settings.yml)

The key section enabling JSON output:

```yaml
search:
  formats:
    - html
    - json    # ← this line is REQUIRED
    - csv
    - rss
```

The Redis/Valkey cache line:

```yaml
redis:
  url: redis://valkey:6379/0
```

## Engines Configured

| Engine | Shortcut | Category |
|--------|----------|----------|
| Google | `g` | General |
| Bing | `b` | General |
| DuckDuckGo | `ddg` | General |
| Wikipedia | `wp` | Knowledge |
| GitHub | `gh` | Code |
| StackOverflow | `so` | Code |

Add more engines in `config/searxng/settings.yml`. See the [full engine list](https://docs.searxng.org/user/configured_engines.html).

## Generating the Secret Key

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output into your `.env` as `SEARXNG_SECRET`.

## Troubleshooting

- **"403 Forbidden" on JSON requests** — The `json` format must be listed in `settings.yml → search.formats`; restart the container after changes
- **Search results from only one engine** — Some engines require a browser-like User-Agent; DuckDuckGo is the most reliable
- **Container fails to start** — Check that `config/searxng/settings.yml` exists and is valid YAML
- **Rate limiting** — SearXNG uses Valkey to rate-limit per-IP; increase limits in `settings.yml → server.limiter`

## References

- [[MCP Stack]] — Back to main stack overview
- Docs: https://docs.searxng.org
- Engines list: https://docs.searxng.org/user/configured_engines.html
