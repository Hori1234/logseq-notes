---
title: Elasticsearch MCP
tags: [mcp, elasticsearch, search]
status: active
source: https://github.com/elastic/mcp-server-elasticsearch
---

# Elasticsearch MCP Server

> Query and analyze your Elasticsearch data using natural language through an AI agent.

## What It Does

The official Elastic MCP server exposes your [[MCP Stack/Elasticsearch]] cluster as an MCP tool set, letting your AI:

- List, describe, and explore indices
- Search documents using natural language (translated to Elasticsearch queries)
- Retrieve and analyze specific documents
- Inspect mappings, settings, and cluster health

## Available Tools

| Tool | Description |
|------|-------------|
| `list_indices` | List all available Elasticsearch indices |
| `get_mappings` | Get the field mappings of an index |
| `search` | Search an index with natural language |
| `get_document` | Retrieve a document by ID |
| `get_cluster_info` | Get cluster health and stats |

## Docker Compose Config

```yaml
elasticsearch-mcp:
  image: docker.elastic.co/mcp/elasticsearch:latest
  depends_on:
    elasticsearch:
      condition: service_healthy
  environment:
    ES_URL: http://elasticsearch:9200
    ES_USERNAME: ${ELASTIC_USERNAME:-elastic}
    ES_PASSWORD: ${ELASTIC_PASSWORD:-changeme}
  ports:
    - "8003:8080"
  command: http   # run in Streamable HTTP mode
```

The server runs in **HTTP mode** (not stdio) so it can serve multiple clients and be reached over the network.

## MCP Client Configuration

```json
{
  "mcpServers": {
    "elasticsearch": {
      "url": "http://localhost:8003/mcp",
      "transport": "http"
    }
  }
}
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ES_URL` | ✅ | Elasticsearch cluster URL |
| `ES_USERNAME` | One of | Basic auth username |
| `ES_PASSWORD` | One of | Basic auth password |
| `ES_API_KEY` | One of | API key (alternative to user/pass) |
| `ES_SSL_SKIP_VERIFY` | ❌ | Set `true` to skip TLS verification (dev only) |

## Example Prompts

```
"What indices are available in Elasticsearch?"
"Search the 'logs' index for errors from the last hour"
"Show me the mapping for the mem0_memories index"
"How many documents are in each index?"
```

## Note on Deprecation

As of 2025, Elastic has marked the standalone MCP server as *maintenance-only* in favor of their hosted Elastic Agent Builder. For self-hosted Elasticsearch, the standalone image (`docker.elastic.co/mcp/elasticsearch`) remains the correct approach.

## Troubleshooting

- **Container fails to start** — Elasticsearch must be healthy first; check `docker compose logs elasticsearch`
- **"Index not found"** — The index may not exist yet; create data first (e.g., let Mem0 add memories)
- **Empty search results** — Try a broader query; Elasticsearch needs populated indices

## References

- [[MCP Stack]] — Back to main stack overview
- [[MCP Stack/Elasticsearch]] — The cluster this server connects to
- Source: https://github.com/elastic/mcp-server-elasticsearch
