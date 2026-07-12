---
title: Logseq MCP
tags: [mcp, logseq, knowledge-base]
status: active
source: https://github.com/ergut/mcp-logseq
---

# Logseq MCP Server

> Connect your AI assistant directly to your Logseq knowledge graph — read pages, create content, search by meaning.

## What It Does

The `mcp-logseq` server (by [@ergut](https://github.com/ergut/mcp-logseq)) exposes your Logseq graph as an MCP tool set. Your AI can:

- List, read, create, update, and delete pages
- Search across your graph by keyword or DSL query
- Execute Logseq DSL queries (e.g., find all `TODO` tasks)
- (Optional) Semantic vector search using Ollama embeddings

## Available Tools

| Tool | Description |
|------|-------------|
| `list_pages` | Browse all pages in your graph |
| `get_page_content` | Read the full content of a page |
| `create_page` | Create a new page with structured blocks |
| `update_page` | Append or replace page content |
| `delete_page` | Remove a page |
| `search` | Full-text search across the graph |
| `query` | Run a Logseq DSL query |
| `find_pages_by_property` | Find pages by a specific property |
| `get_pages_from_namespace` | List all pages under a namespace |
| `rename_page` | Rename a page and update all backlinks |
| `get_page_backlinks` | Find pages that link to a given page |
| `insert_nested_block` | Insert child/sibling blocks |
| `update_block` | Edit a specific block by UUID |
| `delete_block` | Delete a specific block by UUID |

## Prerequisites

### Enable the Logseq HTTP API

1. Open Logseq
2. Go to **Settings → Features**
3. Enable **"Enable HTTP APIs server"**
4. Click the 🔌 **API button** in the top bar → **"Start server"**
5. Click **"Authorization tokens"** → Create a new token
6. Copy the token into your `.env` file as `LOGSEQ_API_TOKEN`

> **Default port**: Logseq listens on `http://localhost:12315`

## Docker Compose Config

```yaml
logseq-mcp:
  image: python:3.12-slim
  environment:
    LOGSEQ_API_TOKEN: ${LOGSEQ_API_TOKEN}
    LOGSEQ_API_URL: http://host.docker.internal:12315
  command: >
    sh -c "pip install mcp-logseq && mcp-logseq"
  ports:
    - "8001:8001"
  extra_hosts:
    - "host.docker.internal:host-gateway"
```

> `host.docker.internal` resolves to your host machine IP — this is how the container reaches Logseq which runs on your desktop.

## MCP Client Configuration

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "logseq": {
      "url": "http://localhost:8001/mcp",
      "transport": "http"
    }
  }
}
```

Or use the direct `uv` approach (no Docker):

```json
{
  "mcpServers": {
    "logseq": {
      "command": "uv",
      "args": ["run", "--with", "mcp-logseq", "mcp-logseq"],
      "env": {
        "LOGSEQ_API_TOKEN": "your_token_here",
        "LOGSEQ_API_URL": "http://localhost:12315"
      }
    }
  }
}
```

## Troubleshooting

- **"Connection refused"** — Make sure Logseq is running and the HTTP API server is started (🔌 button → Start)
- **"401 Unauthorized"** — Check your `LOGSEQ_API_TOKEN` matches the token in Logseq
- **"host.docker.internal not resolving"** on Linux — The `extra_hosts` entry in the compose file handles this; ensure Docker version ≥ 20.10

## References

- [[MCP Stack]] — Back to main stack overview
- Source: https://github.com/ergut/mcp-logseq
