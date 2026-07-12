---
title: MCP Stack — Setup Guide
tags: [mcp, docker, ai-tools, setup, windows11]
status: active
created: 2026-07-07
platform: Windows 11 + Docker Desktop (WSL2)
---

# MCP Stack — Complete Setup Guide

> **Platform**: Windows 11 with Docker Desktop (WSL2 backend)

## Stack Overview

| # | Service | Port | Purpose |
|---|---------|------|---------|
| 1 | [[MCP Stack/Logseq MCP]] | 8001 | Read/write your Logseq graph from AI |
| 2 | [[MCP Stack/Firecrawl MCP]] | 8002 | Web scraping & crawling for AI agents |
| 3 | [[MCP Stack/Elasticsearch]] | 9200 | Vector + full-text search backend |
| 4 | [[MCP Stack/Elasticsearch MCP]] | 8003 | Query Elasticsearch via MCP |
| 5 | [[MCP Stack/Mem0]] | 8004 | AI memory layer backed by Elasticsearch |
| 6 | [[MCP Stack/SearXNG]] | 8080 | Privacy-respecting meta-search (JSON API) |
| 7 | [[MCP Stack/MarkItDown MCP]] | 8005 | Convert any file/URL to Markdown |

## Client Configuration Guides

- [[MCP Stack/Claude Desktop Config]] — Add all servers to Claude Desktop
- [[MCP Stack/AnythingLLM Config]] — Add all servers to AnythingLLM (step-by-step)

## Quick Start (Windows 11)

### Prerequisites
- **Windows 11** with [Docker Desktop](https://www.docker.com/products/docker-desktop/) (WSL2 backend — the default)
- WSL2 enabled: run `wsl --install` in an elevated PowerShell if not already done
- (Optional) Logseq running on your host with the HTTP API enabled
- Python 3.x installed (only needed to generate the SearXNG secret)

### Step 1 — Fix Elasticsearch memory limit (one-time WSL2 fix)

Open **PowerShell as Administrator** and run:

```powershell
wsl -d docker-desktop sysctl -w vm.max_map_count=262144
```

To make this **permanent**, create or edit `C:\Users\<YourName>\.wslconfig`:

```ini
[wsl2]
kernelCommandLine = sysctl.vm.max_map_count=262144
```

Then restart WSL2:

```powershell
wsl --shutdown
# Then reopen Docker Desktop
```

### Step 2 — Copy and configure `.env`

Open **PowerShell** in the `mcp-stack` folder:

```powershell
Copy-Item .env.example .env
notepad .env
```

Fill in all required values:

| Variable | Where to get it |
|----------|----------------|
| `LOGSEQ_API_TOKEN` | Logseq → Settings → Features → HTTP API → Tokens |
| `FIRECRAWL_API_KEY` | https://www.firecrawl.dev/app/api-keys |
| `ELASTIC_PASSWORD` | Choose any strong password |
| `OPENAI_API_KEY` | https://platform.openai.com/api-keys |
| `SEARXNG_SECRET` | Run: `python -c "import secrets; print(secrets.token_hex(32))"` |

### Step 3 — Start the stack

```powershell
docker compose up -d
```

Optional — also start Kibana (Elasticsearch UI):

```powershell
docker compose --profile kibana up -d
```

### Step 4 — Verify all services are healthy

```powershell
docker compose ps
```

All services should show `Up` or `Up (healthy)`. Elasticsearch can take 60+ seconds on first start.

### Step 5 — Test key endpoints

```powershell
# Elasticsearch health
Invoke-RestMethod http://localhost:9200/_cluster/health | ConvertTo-Json

# SearXNG JSON search
Invoke-RestMethod "http://localhost:8080/search?q=test&format=json" | Select-Object -ExpandProperty results | Select-Object title, url

# Mem0 health
Invoke-RestMethod http://localhost:8004/health
```

### Step 6 — Configure your AI client

- **Claude Desktop**: See [[MCP Stack/Claude Desktop Config]]
- **AnythingLLM**: See [[MCP Stack/AnythingLLM Config]]

## Windows 11 Firewall / Port Notes

All services bind to `localhost` by default. If Windows Firewall prompts you when starting Docker, allow access only on **Private networks**. No ports need to be exposed to the internet.

| Service | Port | URL |
|---------|------|-----|
| Logseq MCP | 8001 | http://localhost:8001 |
| Firecrawl MCP | 8002 | http://localhost:8002 |
| Elasticsearch MCP | 8003 | http://localhost:8003 |
| Mem0 API | 8004 | http://localhost:8004 |
| SearXNG | 8080 | http://localhost:8080 |
| MarkItDown MCP | 8005 | http://localhost:8005 |
| Elasticsearch | 9200 | http://localhost:9200 |
| Kibana (optional) | 5601 | http://localhost:5601 |

## File Structure

```
mcp-stack\
├── docker-compose.yml        ← main compose file
├── .env.example              ← copy to .env and fill in values
├── .env                      ← your secrets (NEVER commit!)
├── config\
│   ├── mem0_server.py        ← Mem0 FastAPI server
│   └── searxng\
│       └── settings.yml      ← SearXNG config with JSON enabled
└── data\
    └── markitdown\           ← drop files here for MarkItDown conversion
```

## Updating the Stack

```powershell
docker compose pull          # pull latest images
docker compose up -d         # recreate changed containers
```

## Stopping the Stack

```powershell
docker compose down          # stop & remove containers (keeps volumes)
docker compose down -v       # ⚠️  also deletes all data volumes
```
