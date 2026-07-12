---
title: Mem0
tags: [mcp, mem0, memory, ai-agents]
status: active
source: https://github.com/mem0ai/mem0
---

# Mem0 — AI Memory Layer

> Give your AI persistent, personalized memory that improves with every conversation — backed by [[MCP Stack/Elasticsearch]].

## What It Does

[Mem0](https://mem0.ai) ("mem-zero") is an intelligent memory layer for AI agents. Instead of losing context between sessions, Mem0:

- **Extracts** facts and preferences from conversations using an LLM
- **Stores** them as vector embeddings in Elasticsearch
- **Retrieves** the most relevant memories when answering new questions
- Uses **multi-signal retrieval**: semantic, BM25 keyword, and entity matching in parallel

## Architecture in This Stack

```
AI Agent / Claude
     │
     ▼
Mem0 API (port 8004)
     │
     ├── LLM (OpenAI/gpt-4o-mini) — extracts memories
     │
     └── Elasticsearch (port 9200)
             └── Index: mem0_memories
                   ├── Embeddings (text-embedding-3-small)
                   └── Full-text metadata
```

## API Endpoints

The `config/mem0_server.py` FastAPI server exposes:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/memories/add` | Add memories from a conversation |
| `POST` | `/memories/search` | Semantic search for relevant memories |
| `GET` | `/memories/{user_id}` | Get all memories for a user |
| `DELETE` | `/memories/{memory_id}` | Delete a specific memory |
| `DELETE` | `/memories/user/{user_id}` | Delete all memories for a user |

## Docker Compose Config

```yaml
mem0:
  image: python:3.12-slim
  depends_on:
    elasticsearch:
      condition: service_healthy
  environment:
    MEM0_VECTOR_STORE_PROVIDER: elasticsearch
    MEM0_VECTOR_STORE_URL: http://elasticsearch:9200
    MEM0_VECTOR_STORE_INDEX: mem0_memories
    OPENAI_API_KEY: ${OPENAI_API_KEY}
    MEM0_LLM_MODEL: gpt-4o-mini
    MEM0_EMBEDDER_MODEL: text-embedding-3-small
  volumes:
    - ./config/mem0_server.py:/app/server.py:ro
  ports:
    - "8004:8000"
```

## Required Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key (for embeddings + LLM) |
| `MEM0_LLM_MODEL` | LLM for memory extraction (`gpt-4o-mini` recommended) |
| `MEM0_EMBEDDER_MODEL` | Embedding model (`text-embedding-3-small`) |
| `MEM0_VECTOR_STORE_URL` | Elasticsearch URL |

## Example Usage

### Add a memory

```bash
curl -X POST http://localhost:8004/memories/add \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "I prefer Python over JavaScript"},
      {"role": "assistant", "content": "Got it, I will use Python for your code examples"}
    ],
    "user_id": "alice"
  }'
```

### Search memories

```bash
curl -X POST http://localhost:8004/memories/search \
  -H "Content-Type: application/json" \
  -d '{"query": "programming language preferences", "user_id": "alice"}'
```

### Get all memories for a user

```bash
curl http://localhost:8004/memories/alice
```

## Alternative LLM Providers

If you don't want to use OpenAI, Mem0 supports:

| Provider | Set `MEM0_LLM_PROVIDER` | Notes |
|----------|------------------------|-------|
| OpenAI | `openai` | Default |
| Anthropic | `anthropic` | Set `ANTHROPIC_API_KEY` |
| Ollama | `ollama` | Fully local; set `MEM0_LLM_BASE_URL` |
| Groq | `groq` | Set `GROQ_API_KEY` |

For Ollama (fully local, no data leaves machine):
```env
MEM0_LLM_PROVIDER=ollama
MEM0_LLM_BASE_URL=http://host.docker.internal:11434
MEM0_LLM_MODEL=llama3.2
MEM0_EMBEDDER_PROVIDER=ollama
MEM0_EMBEDDER_MODEL=nomic-embed-text
MEM0_EMBEDDER_DIMS=768
```

## Troubleshooting

- **"Connection refused to Elasticsearch"** — Wait for Elasticsearch to be healthy (`docker compose ps`)
- **"OpenAI API error"** — Check `OPENAI_API_KEY` is correct and has quota
- **Slow first memory add** — First call creates the Elasticsearch index; subsequent calls are fast
- **Empty search results** — Add memories first, then search; index needs data

## References

- [[MCP Stack]] — Back to main stack overview
- [[MCP Stack/Elasticsearch]] — The vector store backing Mem0
- Source: https://github.com/mem0ai/mem0
- Docs: https://docs.mem0.ai
