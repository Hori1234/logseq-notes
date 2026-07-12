---
title: Mem0 MCP Server
tags: [mcp, mem0, elasticsearch, lm-studio]
status: active
---

# Mem0 MCP Server

## Connection

- URL: `http://localhost:8004/mcp`
- Transport: Streamable HTTP
- Health: `http://localhost:8004/health`
- Index: `mem0_memories`

## Tools

| Tool | Required arguments | Purpose |
|---|---|---|
| `add_memory` | `messages`, `user_id` | Extract and persist facts |
| `search_memories` | `query`, `user_id` | Semantic retrieval |
| `get_all_memories` | `user_id` | List a user's memories |
| `get_memory` | `memory_id` | Retrieve one memory |
| `update_memory` | `memory_id`, `data` | Correct memory text |
| `delete_memory` | `memory_id` | Delete one memory |
| `delete_all_memories` | `user_id` | Erase a user's memories |
| `get_memory_history` | `memory_id` | Read the audit history |

Use the same `user_id` when adding and searching. The server internally
converts it to the mem0ai API's `filters={"user_id": ...}` parameter.

## LM Studio requirement

Load:

- `google/gemma-4-26b-a4b-qat`
- `text-embedding-mxbai-embed-large-v1`

Set Gemma's context length to **32768**.

## Lifecycle and AnythingLLM compatibility

The MCP app must run with FastMCP's lifespan context. The custom server
mounts `mcp.streamable_http_app()` and passes
`mcp_app.router.lifespan_context` to the outer Starlette application. This
prevents:

```text
Task group is not initialized. Make sure to use run().
```

The server also returns a JSON response for bare GET `/mcp` liveness probes.
Tool calls continue to use POST `/mcp`.

## Recovery

```powershell
docker compose up -d --force-recreate mem0
Invoke-RestMethod http://localhost:8004/health
docker logs mem0 --tail 80
```

After recreation, reconnect mem0 in AnythingLLM to establish a fresh session.

## Related pages

- [[Mem0]]
- [[Kibana - Mem0 Memory Browser]]
- [[Mem0 Knowledge Graph]]
