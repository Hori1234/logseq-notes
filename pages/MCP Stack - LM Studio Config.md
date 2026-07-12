---
title: MCP Stack — LM Studio Configuration
tags: [mcp, docker, lm-studio, configuration, mem0, elasticsearch]
status: active
created: 2026-07-12
updated: 2026-07-12
platform: Windows 11 + Docker Desktop (WSL2)
related: [[MCP Stack]]
---

# MCP Stack — LM Studio Configuration

> Documents all changes made to get `docker compose up` working with a local **LM Studio** backend, the `{service}bdBD1974` password convention, and all runtime bugs fixed.

---

## Step 1 — The `.env` File

Create at `C:\Users\swhyo\Documents\Logseq\mcp-stack\.env`:

```dotenv
###############################################################################
# MCP Stack — .env  |  NEVER commit to version control
###############################################################################

# ── Logseq ───────────────────────────────────────────────────────────────────
# In Logseq: Settings → Features → HTTP API → add token with value below
LOGSEQ_API_TOKEN=logseqbdBD1974
MCP_HTTP_AUTH_TOKEN=logseqbdBD1974
LOGSEQ_API_URL=http://host.docker.internal:12315

# ── Firecrawl ─────────────────────────────────────────────────────────────────
FIRECRAWL_API_KEY=fc-3c2677e6221e4893aff7f02eb5886b45

# ── Elasticsearch ─────────────────────────────────────────────────────────────
ELASTIC_USERNAME=elastic
ELASTIC_PASSWORD=elasticbdBD1974

# ── SearXNG ───────────────────────────────────────────────────────────────────
SEARXNG_SECRET=searxngbdBD1974

# ── Mem0 MCP — LM Studio (fully local) ───────────────────────────────────────
MEM0_LLM_PROVIDER=openai
MEM0_LLM_BASE_URL=http://host.docker.internal:1234/v1
MEM0_LLM_API_KEY=lm-studio
MEM0_LLM_MODEL=google/gemma-4-26b-a4b-qat

MEM0_EMBEDDER_PROVIDER=openai
MEM0_EMBEDDER_BASE_URL=http://host.docker.internal:1234/v1
MEM0_EMBEDDER_API_KEY=lm-studio
MEM0_EMBEDDER_MODEL=text-embedding-mxbai-embed-large-v1
MEM0_EMBEDDER_DIMS=1024
```

---

## Step 2 — Password Convention

All **internal** service credentials follow the `{service}bdBD1974` pattern:

| Service | Variable | Value |
|---------|----------|-------|
| Logseq API | `LOGSEQ_API_TOKEN` | `logseqbdBD1974` |
| Logseq MCP bearer | `MCP_HTTP_AUTH_TOKEN` | `logseqbdBD1974` |
| Elasticsearch | `ELASTIC_PASSWORD` | `elasticbdBD1974` |
| SearXNG | `SEARXNG_SECRET` | `searxngbdBD1974` |

> `MEM0_LLM_API_KEY` / `MEM0_EMBEDDER_API_KEY` use `lm-studio` — LM Studio ignores the key value.
> `FIRECRAWL_API_KEY` is an external cloud credential (not a password we define).

---

## Step 3 — LM Studio Models

| Role | LM Studio identifier | Variable |
|------|---------------------|----------|
| Agent / Chat LLM | `google/gemma-4-26b-a4b-qat` | `MEM0_LLM_MODEL` |
| Embedder | `text-embedding-mxbai-embed-large-v1` | `MEM0_EMBEDDER_MODEL` |

**Why `MEM0_EMBEDDER_DIMS=1024`?**
`mxbai-embed-large-v1` outputs **1024-dimensional** vectors. The compose default was `768` — `.env` overrides it so Elasticsearch creates the correct index mapping.

**Why `provider=openai`?**
LM Studio exposes an OpenAI-compatible API at port `1234`. `host.docker.internal` is Docker Desktop's hostname that resolves to the Windows host from inside any container.

---

## Step 4 — Logseq API Token (manual action)

In the current version of Logseq you **create the token yourself**:

1. Open Logseq → **Settings → Features → HTTP API**
2. Enable the HTTP API server (port `12315`)
3. Add a new authorization token with value **`logseqbdBD1974`**
4. The `.env` already has `LOGSEQ_API_TOKEN=logseqbdBD1974` — no further changes needed

---

## Runtime Fixes Applied

These bugs were found and fixed after initial `docker compose up`:

| Container | Error | Fix |
|-----------|-------|-----|
| `logseq-mcp` | `invalid choice: sse` | Changed `--transport sse` → `--transport http` |
| `logseq-mcp` | `MCP_HTTP_AUTH_TOKEN is required` | Added `MCP_HTTP_AUTH_TOKEN` env var |
| `logseq-mcp` | Refusing to bind over plain HTTP | Added `--insecure` flag |
| `firecrawl-mcp` | `fetch failed` / empty replies | Added `HOST: "0.0.0.0"` (was binding to loopback) |
| `mem0` | `Extra fields not allowed: url, index_name` | Rewrote as full MCP server with corrected ES config fields |
| `mem0` | `BadRequestError(400)` — ES client v9 vs server v8 | Pinned `elasticsearch>=8,<9` |
| `mem0` | `FastMCP.run() unexpected keyword 'host'` | Use `mcp.streamable_http_app()` + `uvicorn.run()` |

---

## Start the Stack

```powershell
cd C:\Users\swhyo\Documents\Logseq\mcp-stack

docker compose up -d          # start everything
docker compose logs -f        # watch logs
docker compose ps             # check health
```

## Service Ports

| Service | Port | MCP URL |
|---------|------|---------|
| Logseq MCP | 8001 | http://localhost:8001/mcp |
| Firecrawl MCP | 8002 | http://localhost:8002/mcp |
| Elasticsearch MCP | 8003 | http://localhost:8003/mcp |
| Mem0 MCP | 8004 | http://localhost:8004/mcp |
| SearXNG | 8080 | http://localhost:8080 (REST, not MCP) |
| MarkItDown MCP | 8005 | http://localhost:8005/mcp |
| Elasticsearch | 9200 | http://localhost:9200 |

## Troubleshooting

- **Elasticsearch won't start** → Run once in elevated PowerShell:
  ```powershell
  wsl -d docker-desktop sysctl -w vm.max_map_count=262144
  ```
- **Mem0 embedding errors** → Verify LM Studio has `text-embedding-mxbai-embed-large-v1` loaded and server is on port `1234`
- **Mem0 LLM errors** → Verify `google/gemma-4-26b-a4b-qat` is loaded in LM Studio
- **Logseq MCP fails** → Check `LOGSEQ_API_TOKEN` in `.env` matches the token you created in Logseq settings
