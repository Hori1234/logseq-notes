---
title: Firecrawl MCP
tags: [mcp, firecrawl, web-scraping]
status: active
source: https://github.com/firecrawl/firecrawl-mcp-server
---

# Firecrawl MCP Server

> Give your AI the ability to browse, scrape, and deeply crawl any website — returning clean Markdown ready for analysis.

## What It Does

Firecrawl MCP wraps the [Firecrawl](https://www.firecrawl.dev) web-crawling service as an MCP tool. Your AI can:

- Scrape any URL into clean Markdown
- Perform web searches with full page content
- Crawl entire sites (following links)
- Map website structure
- Do deep autonomous research across the web
- Interact with pages (click, fill forms, navigate)

## Available Tools

| Tool | Description |
|------|-------------|
| `firecrawl_scrape` | Scrape a single URL → clean Markdown |
| `firecrawl_search` | Search the web and get full page content |
| `firecrawl_crawl` | Crawl a site (async, follows links) |
| `firecrawl_map` | Map all URLs of a website |
| `firecrawl_check_crawl_status` | Poll status of a running crawl |
| `firecrawl_extract` | Extract structured data from pages |
| `firecrawl_deep_research` | Autonomous multi-step web research |
| `firecrawl_interact` | Click, type, navigate on a page |

## API Key Options

### Option A — Cloud API (Easiest)
1. Sign up at https://www.firecrawl.dev/app/api-keys
2. Copy your key into `.env` as `FIRECRAWL_API_KEY`
3. Leave `FIRECRAWL_API_URL` unset (defaults to `api.firecrawl.dev`)

### Option B — Self-Hosted (Advanced)
- Deploy the [Firecrawl API server](https://github.com/firecrawl/firecrawl)
- Set `FIRECRAWL_API_URL=http://firecrawl-api:3002` in your `.env`

## Docker Compose Config

```yaml
firecrawl-mcp:
  image: node:22-slim
  environment:
    FIRECRAWL_API_KEY: ${FIRECRAWL_API_KEY}
    HTTP_STREAMABLE_SERVER: "true"
    PORT: "3000"
  command: npx -y firecrawl-mcp
  ports:
    - "8002:3000"
```

The server runs in **Streamable HTTP mode** on port 8002 so multiple MCP clients can connect simultaneously.

## MCP Client Configuration

```json
{
  "mcpServers": {
    "firecrawl": {
      "url": "http://localhost:8002/mcp",
      "transport": "http"
    }
  }
}
```

## Example Prompts

```
"Scrape https://docs.python.org/3/ and summarize the key features of Python 3.12"
"Search the web for the latest news on large language models"
"Crawl my company website and list all pages that mention pricing"
"Research the competitive landscape for project management tools"
```

## Rate Limits (Cloud)

| Tier | Scrapes/min | Crawl pages |
|------|------------|-------------|
| Free | 10 | 500 |
| Hobby | 20 | 5000 |
| Standard | 50 | Unlimited |

## Troubleshooting

- **401 errors** — Invalid API key; check `FIRECRAWL_API_KEY` in `.env`
- **Slow first start** — `npx` downloads the package on first run (~30s); subsequent starts are faster
- **Crawl timeouts** — Large crawls are async; use `firecrawl_check_crawl_status` to poll

## References

- [[MCP Stack]] — Back to main stack overview
- Source: https://github.com/firecrawl/firecrawl-mcp-server
- API Keys: https://www.firecrawl.dev/app/api-keys
