---
title: AnythingLLM Config
tags: [mcp, anythingllm, ai-agents, config, windows]
status: active
created: 2026-07-07
---

# AnythingLLM — MCP Server Setup Guide

> Connect all stack MCP servers to AnythingLLM so your AI agents can browse the web, search Elasticsearch, read your Logseq graph, convert documents, and remember everything across sessions.

## What is AnythingLLM?

[AnythingLLM](https://anythingllm.com) is an open-source, all-in-one AI assistant that supports MCP servers, local and cloud LLMs, RAG over your own documents, and full agent tool-use. It has a native MCP integration that reads a single JSON config file.

## Prerequisites

- **AnythingLLM Desktop** installed on Windows 11
  → Download: https://anythingllm.com/download
- The **MCP stack is running** (`docker compose up -d` — see [[MCP Stack]])
- An LLM configured in AnythingLLM that supports tool-use (e.g., GPT-4o, Claude 3.5, Llama 3.1)

---

## Step 1 — Find the MCP Config File

AnythingLLM reads MCP servers from:

```
C:\Users\<YourName>\AppData\Roaming\anythingllm-desktop\storage\plugins\anythingllm_mcp_servers.json
```

### Quick way to open the folder (PowerShell):

```powershell
explorer "$env:APPDATA\anythingllm-desktop\storage\plugins"
```

If the file doesn't exist yet, AnythingLLM will create it automatically when you first open the MCP settings. You can also create it manually.

> **Tip**: You can also edit this file directly from the AnythingLLM UI:
> Settings (⚙️) → **Agent Configuration** → **MCP Servers** → **Edit Config File**

---

## Step 2 — Paste the Full Configuration

Open `anythingllm_mcp_servers.json` in Notepad or VS Code and replace the contents with:

```json
{
  "mcpServers": {

    "logseq": {
      "url": "http://localhost:8001/mcp",
      "type": "streamable",
      "headers": {
        "Authorization": "Bearer logseqbdBD1974"
      },
      "anythingllm": {
        "autoStart": true
      }
    },

    "firecrawl": {
      "url": "http://localhost:8002/mcp",
      "type": "streamable",
      "anythingllm": {
        "autoStart": true
      }
    },

    "elasticsearch": {
      "url": "http://localhost:8003/mcp",
      "type": "streamable",
      "anythingllm": {
        "autoStart": true
      }
    },

    "mem0": {
      "url": "http://localhost:8004/mcp",
      "type": "streamable",
      "anythingllm": {
        "autoStart": true
      }
    },

    "markitdown": {
      "url": "http://localhost:8005/mcp",
      "type": "streamable",
      "anythingllm": {
        "autoStart": true
      }
    }

  }
}
```

> Mem0 is a streamable HTTP MCP server on port 8004. SearXNG remains a JSON HTTP API and is not an MCP entry in this file.

---

## Step 3 — Reload MCP Servers in AnythingLLM

After saving the file:

1. Open AnythingLLM Desktop
2. Go to **Settings (⚙️)** → **Agent Configuration** → **MCP Servers**
3. Click **🔄 Reload MCP Servers**
4. All five servers should appear with a green ✅ status

If a server shows ❌ (failed), click the error icon to see the log — usually it means the Docker container isn't running yet.

---

## Step 4 — Enable MCP Tools for a Workspace

MCP tools are **per-workspace**. For each workspace where you want agent access:

1. Open the workspace → **⚙️ Workspace Settings**
2. Go to **Agent Configuration**
3. Under **Available Tools**, toggle on the MCP servers you want
4. Click **Save**

---

## Step 5 — Test Each Server

Start a chat in your workspace and use the `@agent` directive:

### Test Logseq
```
@agent List all pages in my Logseq graph
```

### Test Firecrawl
```
@agent Scrape https://news.ycombinator.com and summarize the top 5 stories
```

### Test Elasticsearch
```
@agent List all Elasticsearch indices and show how many documents are in each
```

### Test MarkItDown
```
@agent Convert https://docs.python.org/3/whatsnew/3.12.html to Markdown and summarize it
```

---

## Using SearXNG in AnythingLLM

SearXNG runs as a JSON HTTP API that AnythingLLM can call via its **Custom Agent Tools** system or via **HTTP Tool** definitions. Mem0 is configured above as a native MCP server.

### Option A — System Prompt Integration (Simplest)

Add these instructions to your workspace's **System Prompt**:

```
You have access to two additional services via HTTP:

1. SearXNG search: GET http://localhost:8080/search?q={query}&format=json
   Use this to search the web for current information.
2. Mem0 is available through the `mem0` MCP tools. Use `search_memories` at the
   start of a conversation and `add_memory` after important user facts appear.
```

### Option B — AnythingLLM Custom Agent Skill (Advanced)

Create a custom skill in AnythingLLM that wraps both APIs. Store the skill in:

```
C:\Users\<YourName>\AppData\Roaming\anythingllm-desktop\storage\plugins\agent-skills\
```

See the [AnythingLLM custom skills docs](https://docs.anythingllm.com/agent/custom/introduction) for the full skill format.

---

## Server Reference Table

| Server | Port | Config Type | AnythingLLM Entry |
|--------|------|-------------|-------------------|
| Logseq MCP | 8001 | Streamable HTTP | ✅ In JSON config |
| Firecrawl MCP | 8002 | Streamable HTTP | ✅ In JSON config |
| Elasticsearch MCP | 8003 | Streamable HTTP | ✅ In JSON config |
| Mem0 MCP | 8004 | Streamable HTTP | ✅ In JSON config |
| SearXNG JSON API | 8080 | Plain HTTP | Via system prompt |
| MarkItDown MCP | 8005 | Streamable HTTP | ✅ In JSON config |

---

## Troubleshooting

### Server shows ❌ in the MCP panel

1. Check the Docker container is running:
   ```powershell
   docker compose ps
   ```
2. Check the container logs:
   ```powershell
   docker compose logs logseq-mcp --tail 30
   ```
3. Test the endpoint manually:
   ```powershell
   Invoke-RestMethod http://localhost:8004/health
   # Should return {"status":"ok",...}
   ```

### "No tools available" even after enabling

- Some LLMs don't support tool-use — switch to GPT-4o, Claude 3.5 Sonnet, or Llama 3.1 70B+
- Check the workspace's Agent Configuration to confirm the server is toggled on

### AnythingLLM can't reach localhost ports

AnythingLLM Desktop runs on the same Windows host as Docker Desktop. The services bind to `127.0.0.1` (localhost). If AnythingLLM can't connect:

- Open the Docker container port check:
  ```powershell
  netstat -an | findstr "8001 8002 8003 8005"
  ```
  You should see `LISTENING` for each port.

- Try `host.docker.internal` if localhost doesn't work:
  ```json
  "url": "http://host.docker.internal:8002/mcp"
  ```

### Logseq MCP returns "connection refused"

Make sure Logseq is running and the HTTP API server is **started**:
- Logseq → click 🔌 icon in top bar → **Start server**
- Verify at: http://localhost:12315/api/page/all (should return JSON)

---

## Workspace Prompt Templates

Paste these as the **System Prompt** for a workspace called `MCP Agent`:

```
You are a powerful AI assistant with access to:

**Knowledge & Memory**
- Logseq graph (read/write notes, pages, and tasks via the `logseq` MCP tool)
- Mem0 persistent memory via the `mem0` MCP server (search at start of each session)

**Research & Web**  
- Firecrawl (scrape URLs, search the web, crawl sites via the `firecrawl` MCP tool)
- SearXNG (meta-search: GET http://localhost:8080/search?q={query}&format=json)

**Data & Documents**
- Elasticsearch (query indices via the `elasticsearch` MCP tool)
- MarkItDown (convert any file or URL to Markdown via the `markitdown` MCP tool)

At the start of every conversation, search Mem0 for relevant memories about the user.
After every conversation, save important facts to Mem0.
Always cite sources when presenting research results.
```

---

## Related Pages

- [[MCP Stack]] — Main stack overview and quick start
- [[MCP Stack/Logseq MCP]] — Logseq server details
- [[MCP Stack/Firecrawl MCP]] — Firecrawl server details
- [[MCP Stack/Elasticsearch MCP]] — Elasticsearch MCP details
- [[MCP Stack/Mem0 MCP Server]] — Mem0 MCP details
- [[MCP Stack/SearXNG]] — SearXNG JSON API details
- [[MCP Stack/MarkItDown MCP]] — MarkItDown server details
- [[MCP Stack/Claude Desktop Config]] — Claude Desktop setup
