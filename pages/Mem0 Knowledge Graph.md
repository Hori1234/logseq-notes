---
title: Mem0 Knowledge Graph
tags: [mem0, knowledge-graph, umap, visualization]
status: active
---

# Mem0 Knowledge Graph

The dashboard at `http://localhost:8006` visualizes the embeddings stored in
Elasticsearch.

## Views

- **Cluster Map**: UMAP projects 1024-dimensional embeddings to two dimensions.
  Semantically similar memories appear near one another.
- **Knowledge Graph**: memories are nodes and edges connect pairs whose cosine
  similarity is above the selected threshold.

Use **Refresh memories** after adding memories in AnythingLLM. In the graph,
adjust the threshold slider; lower values show more connections.

## Interpretation

- Tight clusters indicate related topics.
- Isolated nodes indicate unique facts.
- A later `updated_at` indicates a memory changed during deduplication.
- One Elasticsearch document represents one extracted fact.

The dashboard reads `metadata.data` for text and `vector` for embeddings.
It loads up to 500 documents per refresh.

## Troubleshooting

```powershell
docker logs mem0-graph --tail 80
docker compose ps mem0-graph
```

If the dashboard is unhealthy while its page works, its health check may be
too strict for the Dash development server; the visualization can still be
opened at `http://localhost:8006`.

## Related pages

- [[Mem0]]
- [[Mem0 MCP Server]]
- [[Kibana - Mem0 Memory Browser]]
