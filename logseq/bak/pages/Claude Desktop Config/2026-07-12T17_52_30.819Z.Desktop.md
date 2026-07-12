---
title: Claude Desktop Config
tags: [mcp, claude, config]
status: active
---

# Claude Desktop MCP Configuration

Add this to your `claude_desktop_config.json` to connect Claude Desktop to all stack services.

**File location:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

## Full Config Snippet

```json
{
  "mcpServers": {
    "logseq": {
      "url": "http://localhost:8001/mcp",
      "transport": "http"
    },
    "firecrawl": {
      "url": "http://localhost:8002/mcp",
      "transport": "http"
    },
    "elasticsearch": {
      "url": "http://localhost:8003/mcp",
      "transport": "http"
    },
    "markitdown": {
      "url": "http://localhost:8005/mcp",
      "transport": "http"
    }
  }
}
```

> **Note:** Mem0 and SearXNG are HTTP REST APIs, not MCP protocol servers. Call them directly from tools or via a custom MCP wrapper.

## Port Reference

| Service | Host Port | MCP URL |
|---------|-----------|---------|
| Logseq MCP | 8001 | http://localhost:8001/mcp |
| Firecrawl MCP | 8002 | http://localhost:8002/mcp |
| Elasticsearch MCP | 8003 | http://localhost:8003/mcp |
| Mem0 REST API | 8004 | http://localhost:8004 |
| SearXNG JSON API | 8080 | http://localhost:8080/search?format=json |
| MarkItDown MCP | 8005 | http://localhost:8005/mcp |
| Elasticsearch | 9200 | http://localhost:9200 |
| Kibana (optional) | 5601 | http://localhost:5601 |

## References

- [[MCP Stack]] — Back to main stack overview
