---
title: Mem0
tags: [mcp, mem0, memory, ai-agents, elasticsearch, lm-studio]
status: active
source: https://github.com/mem0ai/mem0
updated: 2026-07-12
related: [[Mem0 MCP Server]], [[Elasticsearch]]
---

# Mem0 — AI Memory Layer (MCP Server)

> Persistent, personalized AI memory backed by [[Elasticsearch]] and local [[LM Studio]] models — exposed as a full **Model Context Protocol** server.

## What It Does

[Mem0](https://mem0.ai) ("mem-zero") is an intelligent memory layer for AI agents. Instead of losing context between sessions, Mem0:

- **Extracts** facts and preferences from conversations using the LLM
- **Stores** them as 1024-dimensional vector embeddings in Elasticsearch
- **Retrieves** the most relevant memories when answering new questions
- Uses **multi-signal retrieval**: semantic similarity + BM25 keyword matching

## Current Architecture (MCP Server)

```
MCP Client (AnythingLLM / Claude)
        │
        │  POST http://localhost:8004/mcp   (Streamable HTTP MCP)
        ▼
  ┌─────────────┐
  │  mem0 MCP   │  python:3.12-slim · FastMCP + mem0ai + uvicorn
  │  container  │  port 8000 → host 8004
  └──────┬──────┘
         │
         ├── Elasticsearch :9200  (vector store, index: mem0_memories)
         └── LM Studio :1234      (LLM + embedder via host.docker.internal)
```

> **Note:** The original `mem0_server.py` (FastAPI REST) was replaced with `mem0_mcp_server.py` (FastMCP MCP server). See [[Mem0 MCP Server]] for full tool documentation.

## MCP Tools

| Tool | Description |
|------|-------------|
| `add_memory` | Extract + store facts from a conversation |
| `search_memories` | Semantic vector search (k-NN) |
| `get_all_memories` | List all memories for a user |
| `get_memory` | Fetch one record by UUID |
| `update_memory` | Overwrite memory text + re-embed |
| `delete_memory` | Delete one record permanently |
| `delete_all_memories` | ⚠️ Wipe all records for a user |
| `get_memory_history` | Full audit trail of changes |

For parameter details and response schemas → [[Mem0 MCP Server]]

## Docker Compose Config (current — fixed)

```yaml
mem0:
  image: python:3.12-slim
  depends_on:
    elasticsearch:
      condition: service_healthy
  environment:
    HOST: "0.0.0.0"
    PORT: "8000"
    MEM0_VECTOR_STORE_HOST: elasticsearch
    MEM0_VECTOR_STORE_PORT: "9200"
    MEM0_VECTOR_STORE_INDEX: mem0_memories
    ELASTIC_USERNAME: elastic
    ELASTIC_PASSWORD: elasticbdBD1974
    MEM0_LLM_MODEL: google/gemma-4-26b-a4b-qat
    MEM0_EMBEDDER_MODEL: text-embedding-mxbai-embed-large-v1
    MEM0_EMBEDDER_DIMS: "1024"
  volumes:
    - ./config/mem0_mcp_server.py:/app/server.py:ro
  command: >
    sh -c "pip install --quiet mem0ai 'elasticsearch>=8,<9' 'mcp[cli]' uvicorn &&
           python server.py"
  ports:
    - "8004:8000"
```

## Bug Fixes Applied (runtime debugging log)

| Error | Root Cause | Fix Applied |
|-------|-----------|-------------|
| `Extra fields not allowed: index_name, url` | mem0ai renamed ES config fields | Changed `url`→`host`+`port`, `index_name`→`collection_name` |
| `Either api_key or user/password must be provided` | mem0ai pydantic validation | Added `user` + `password` to vector_store config |
| `ImportError: Elasticsearch requires extra dependencies` | Missing pip package | Added `elasticsearch` to install command |
| `ValueError: Could not parse URL 'http://elasticsearch:9200:9200'` | mem0ai appends port to host | Changed to `host=http://elasticsearch` (scheme+name only) |
| `BadRequestError(400) — Accept version must be compatible-with=9` | ES client v9 installed, server is ES 8.x | Pinned `elasticsearch>=8,<9` |
| `FastMCP.run() unexpected keyword argument 'host'` | FastMCP run() API doesn't accept host/port | Use `mcp.streamable_http_app()` + `uvicorn.run()` directly |

## MCP Client Configuration

### AnythingLLM

```json
{
  "mem0": {
    "url": "http://localhost:8004/mcp",
    "type": "streamable"
  }
}
```

## Required LM Studio Models

| Role | Model |
|------|-------|
| LLM (memory extraction) | `google/gemma-4-26b-a4b-qat` |
| Embedder | `text-embedding-mxbai-embed-large-v1` (1024 dims) |

Both must be loaded in LM Studio before starting the stack.

## Troubleshooting

- **Container restarting with ES validation errors** → See bug fix table above
- **LLM errors** → Start LM Studio and load `google/gemma-4-26b-a4b-qat`
- **Embedder errors** → Load `text-embedding-mxbai-embed-large-v1` in LM Studio
- **Wrong embedding dims** → Delete the `mem0_memories` ES index and restart mem0; it will recreate with 1024 dims

## References

- [[Mem0 MCP Server]] — Full MCP tool documentation
- [[MCP Stack]] — Main stack overview
- [[Elasticsearch]] — Vector store backend
- Source: https://github.com/mem0ai/mem0
