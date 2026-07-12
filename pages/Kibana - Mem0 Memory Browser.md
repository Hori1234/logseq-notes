---
tags: mcp-stack, kibana, elasticsearch, mem0, visualization
---

# Kibana — Mem0 Memory Browser

## Overview

Kibana is the official Elasticsearch UI. In this stack it is the **primary interface for browsing, searching, and understanding every memory** the [[Mem0 MCP Server]] stores for your AI agents.

- **URL**: http://localhost:5601
- **No login required** — xpack security is disabled
- **ES index**: `mem0_memories`

---

## Real document structure

Every `add_memory` call stores documents shaped like this (vector field hidden):

```json
{
  "metadata": {
    "data": "User's name is Hori.",
    "user_id": "user_1234",
    "attributed_to": "user",
    "text_lemmatized": "User's name is Hori.",
    "hash": "1e0a28f50c5ca710979bcd86c57feef7",
    "created_at": "2026-07-12T16:52:11.838682+02:00",
    "updated_at": "2026-07-12T16:52:11.838682+02:00"
  },
  "vector": [ ... 1024 floats ... ]
}
```

| Field | Description |
|---|---|
| `metadata.data` | ⭐ The extracted memory fact — **this is what the AI remembers** |
| `metadata.user_id` | Who the memory belongs to (e.g. `user_1234`) |
| `metadata.attributed_to` | Whether the fact came from `user` or `assistant` turn |
| `metadata.text_lemmatized` | Lemmatized form used for deduplication |
| `metadata.hash` | SHA hash for dedup — same fact → same hash |
| `metadata.created_at` | When this memory was first stored |
| `metadata.updated_at` | When mem0 last updated it (dedup merge) |
| `vector` | 1024-dim embedding — hide this column in Discover |

---

## First-time setup

### Step 1 — Create a Data View
1. Open **http://localhost:5601**
2. Click the hamburger menu (☰) → **Stack Management** → **Data Views**
3. Click **Create data view**
4. Fill in:
   - **Name**: `mem0 Memories`
   - **Index pattern**: `mem0_memories`
   - **Timestamp field**: select `metadata.created_at`
5. Click **Save data view to Kibana**

### Step 2 — Open Discover
1. Click ☰ → **Discover**
2. Select the `mem0 Memories` data view from the top-left dropdown
3. You will see every stored memory as a row

### Step 3 — Set up useful columns
In the field list on the left, click **+** next to these fields to add them as columns:
- `metadata.data` — the memory text
- `metadata.user_id` — who it belongs to
- `metadata.attributed_to` — user or assistant
- `metadata.created_at` — when it was stored

Click the **eye icon** on `vector` to hide it (it's a 1024-float array — not readable).

---

## Searching memories

### KQL (Kibana Query Language) — search bar at the top

```kql
# All memories for a specific user
metadata.user_id : "user_1234"

# Search memory text for a keyword
metadata.data : "Logseq"

# Memories about a topic
metadata.data : "Windows" or metadata.data : "Docker"

# Memories attributed to the user (not assistant)
metadata.attributed_to : "user"

# Combine filters
metadata.user_id : "user_1234" and metadata.data : "Windows"
```

### Time filter (top-right)
Use the time picker to narrow to:
- **Last 24 hours** — memories added today
- **Last 7 days** — recent session memories
- **Custom range** — any date range

---

## Dev Tools queries

Click ☰ → **Dev Tools** → paste these queries:

```
# Count all stored memories
GET /mem0_memories/_count

# See all memories for a user (newest first, no vector)
GET /mem0_memories/_search
{
  "_source": { "excludes": ["vector"] },
  "query": {
    "term": { "metadata.user_id": "user_1234" }
  },
  "sort": [{ "metadata.created_at": "desc" }],
  "size": 50
}

# Search memory text (full-text)
GET /mem0_memories/_search
{
  "_source": { "excludes": ["vector"] },
  "query": {
    "match": { "metadata.data": "Logseq" }
  }
}

# Find all unique users (who has memories?)
GET /mem0_memories/_search
{
  "size": 0,
  "aggs": {
    "users": {
      "terms": { "field": "metadata.user_id", "size": 100 }
    }
  }
}

# Count memories per user
GET /mem0_memories/_search
{
  "size": 0,
  "aggs": {
    "per_user": {
      "terms": { "field": "metadata.user_id" }
    }
  }
}

# See exact index mapping (all field types)
GET /mem0_memories/_mapping

# Index stats (doc count, storage size)
GET /mem0_memories/_stats/docs,store

# Semantic similarity search (kNN — finds memories SIMILAR to a query vector)
# (Use search_memories tool instead — it handles embedding generation automatically)
```

---

## Understanding the memory thinking process

When an agent calls `add_memory`, mem0 runs **two LLM passes**:

```
Conversation input
      │
      ▼
┌─────────────────────┐
│  Pass 1: EXTRACT    │  Gemma reads the conversation → outputs JSON list of facts
│  (Gemma 4 26B)      │  e.g. ["User's name is Hori", "User uses Logseq"]
└─────────────────────┘
      │
      ▼
┌─────────────────────┐
│  Pass 2: DEDUP      │  Gemma compares new facts vs existing memories in ES
│  (Gemma 4 26B)      │  → decides: ADD / UPDATE / DELETE / NOOP per fact
└─────────────────────┘
      │
      ▼
Elasticsearch write (one doc per fact)
```

You can see this in Kibana:
- **Multiple docs with same `user_id`** = the AI's full knowledge of that user
- **`updated_at` != `created_at`** = fact was merged/updated from a later conversation
- **Same `hash`** = duplicate fact detected (mem0 updates instead of inserting)
- **`attributed_to: "assistant"`** = fact extracted from assistant's own output

---

## Building a Memory Dashboard

☰ → **Dashboards** → **Create dashboard** → **Create visualization**

| Panel | Visualization | Config |
|---|---|---|
| Total memories | **Metric** | Count of docs in `mem0_memories` |
| Memories per user | **Donut** | Terms aggregation on `metadata.user_id` |
| Memory growth over time | **Bar chart** | Date histogram on `metadata.created_at`, interval = day |
| User vs Assistant facts | **Pie** | Terms aggregation on `metadata.attributed_to` |
| Latest memories table | **Data table** | Top 20 by `metadata.created_at` desc — columns: `metadata.data`, `metadata.user_id`, `metadata.created_at` |

---

## Tips and tricks

- **Expand a row** — click the **>** arrow on any memory row in Discover to see all fields as a table
- **Inspect the vector** — expand a row → `vector` field shows all 1024 embedding values (good for debugging embedding quality)
- **Compare two memories** — open both rows, look at their `metadata.hash` — same hash = mem0 treated them as duplicates
- **Find what changed** — filter `metadata.updated_at > metadata.created_at` to see memories that were updated by the dedup pass
- **Delete a bad memory** — copy the `_id` from Discover, then in Dev Tools: `DELETE /mem0_memories/_doc/<id>`

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| No documents in Discover | add_memory never succeeded | Check mem0 container logs: `docker logs mem0` |
| `metadata.created_at` grayed out in Data View | Field type not mapped as `date` | Run: `PUT /mem0_memories/_mapping` with `"metadata.created_at": {"type":"date"}` |
| Vector field makes rows huge | Dense vector displayed | Click the eye icon next to `vector` in field list to hide it |
| Discover shows old data | Time filter too narrow | Change time picker to `Last 30 days` or `All time` |

---

## Related pages
- [[Mem0 MCP Server]]
- [[Mem0]]
- [[MCP Stack]]
- [[MCP Stack - LM Studio Config]]
