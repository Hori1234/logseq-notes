---
title: Mem0
tags: [mcp, mem0, memory, ai-agents, elasticsearch]
status: active
---

# Mem0 - AI Memory Layer

Mem0 provides persistent memory for the local AI stack. It extracts facts
from conversations with Gemma, embeds them with mxbai, and stores them in
Elasticsearch.

## Architecture

```text
AnythingLLM
    |
    | Streamable HTTP MCP: http://localhost:8004/mcp
    v
Custom Mem0 MCP server
    |-- Gemma 4 26B in LM Studio (port 1234)
    |-- mxbai-embed-large-v1 in LM Studio (1024 dimensions)
    `-- Elasticsearch 8.x (http://elasticsearch:9200)
          `-- mem0_memories
```

## MCP tools

| Tool | Purpose |
|---|---|
| `add_memory` | Extract and save facts from `messages` for a `user_id` |
| `search_memories` | Semantic search using `query` and `user_id` |
| `get_all_memories` | List all memories for a user |
| `get_memory` | Retrieve one memory by ID |
| `update_memory` | Replace the text of a memory |
| `delete_memory` | Delete one memory |
| `delete_all_memories` | Delete all memories for a user |
| `get_memory_history` | Inspect changes to a memory |

The server translates user scoping to the current mem0ai API:
`filters={"user_id": user_id}`.

## Connection and health

- MCP endpoint: `http://localhost:8004/mcp`
- Health endpoint: `http://localhost:8004/health`
- Elasticsearch index: `mem0_memories`
- Kibana: `http://localhost:5601`
- Knowledge graph dashboard: `http://localhost:8006`

AnythingLLM must configure mem0 as `"type": "streamable"`.

## LM Studio configuration

Load these models:

```text
google/gemma-4-26b-a4b-qat
text-embedding-mxbai-embed-large-v1
```

Set Gemma's context length to **32768**. Mem0's extraction prompt is too
large for an 8192-token context.

## Elasticsearch document fields

Each extracted fact is stored as a document. The memory text is
`metadata.data`; useful fields include:

| Field | Meaning |
|---|---|
| `metadata.data` | Extracted memory text |
| `metadata.user_id` | User scope |
| `metadata.created_at` | First creation time |
| `metadata.updated_at` | Last update time |
| `metadata.hash` | Deduplication hash |
| `metadata.attributed_to` | User or assistant source |
| `vector` | 1024-dimensional embedding |

## FastMCP lifecycle fix

The server uses `mcp.streamable_http_app()` inside an outer Starlette
application. The outer app reuses
`mcp_app.router.lifespan_context`, which initializes FastMCP's session manager.
Without this lifecycle wiring, POST requests fail with:

```text
RuntimeError: Task group is not initialized. Make sure to use run().
```

The server also provides `/health` and responds to bare GET `/mcp` probes from
AnythingLLM. Actual MCP tool traffic uses POST `/mcp`.

## Troubleshooting

```powershell
docker compose ps mem0
docker logs mem0 --tail 80
Invoke-RestMethod http://localhost:8004/health
```

If AnythingLLM reports a 500 after recreating the container, reconnect or
toggle the mem0 server so it creates a fresh MCP session.

## Related pages

- [[Mem0 MCP Server]]
- [[Kibana - Mem0 Memory Browser]]
- [[Mem0 Knowledge Graph]]
- [[MCP Stack]]
