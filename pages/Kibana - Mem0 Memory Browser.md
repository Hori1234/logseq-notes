---
title: Kibana - Mem0 Memory Browser
tags: [kibana, elasticsearch, mem0, visualization]
status: active
---

# Kibana - Mem0 Memory Browser

Open `http://localhost:5601`. Kibana starts with the normal
`docker compose up -d` command.

## Create the data view

1. Open **Stack Management -> Data Views -> Create data view**.
2. Use index pattern `mem0_memories`.
3. Select `metadata.created_at` as the timestamp field.
4. If it is unavailable, choose **I don't want to use the time filter**.

In Discover, add:

- `metadata.data` - extracted memory text
- `metadata.user_id` - owner
- `metadata.attributed_to` - user or assistant
- `metadata.created_at` - creation time

Hide `vector`, which contains 1024 embedding values.

## KQL searches

```kql
metadata.user_id : "user_1234"
metadata.data : "Logseq"
metadata.data : "Windows" or metadata.data : "Docker"
metadata.user_id : "user_1234" and metadata.data : "MCP"
```

Use **Last 30 days** or **All time** if Discover appears empty.

## Dev Tools

```text
GET /mem0_memories/_count

GET /mem0_memories/_search
{
  "_source": {"excludes": ["vector"]},
  "query": {"term": {"metadata.user_id": "user_1234"}},
  "sort": [{"metadata.created_at": "desc"}],
  "size": 50
}

GET /mem0_memories/_search
{
  "_source": {"excludes": ["vector"]},
  "query": {"match": {"metadata.data": "Logseq"}}
}
```

Mem0 first extracts facts with Gemma and then compares them with existing
facts. Each resulting fact is a separate document. A later update is visible
when `metadata.updated_at` differs from `metadata.created_at`.

For semantic visualization, open `http://localhost:8006`. The companion
dashboard provides a UMAP cluster map and a similarity-based knowledge graph.

