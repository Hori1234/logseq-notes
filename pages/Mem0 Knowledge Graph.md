---
tags: mcp-stack, mem0, knowledge-graph, visualization, umap, elasticsearch
---

# Mem0 Knowledge Graph

## Overview

A custom Dash dashboard that visualises every memory stored by the [[Mem0 MCP Server]] as either a **2D cluster map** or an interactive **knowledge graph**.

- **URL**: http://localhost:8006
- **Data source**: `mem0_memories` index in Elasticsearch
- **First start**: slow (~3–5 min) — pip must compile `umap-learn` + `numba`

---

## The two views

### 📍 Tab 1 — Cluster Map

Uses **UMAP** (Uniform Manifold Approximation and Projection) to compress each memory's 1024-dimensional embedding vector down to 2 dimensions and plots them on a scatter chart.

**What it shows:**
- Memories that are **semantically similar cluster together** — e.g. all "tech stack" memories will appear near each other
- Each dot = one stored memory fact
- Hover over any dot to read the full memory text, user ID, source (user/assistant), and save date
- Different colours = different `user_id` values

**How to read it:**
| Visual pattern | Meaning |
|---|---|
| Tight cluster of dots | Many related memories — the AI has deep knowledge of this topic |
| Isolated dot | Unique fact with no similar memories yet |
| Two clusters far apart | Distinct, unrelated topics in memory |
| Dots overlapping | Nearly identical memories (possible duplicates) |

### 🕸️ Tab 2 — Knowledge Graph

A force-directed network graph where:
- **Nodes** = individual memory facts
- **Edges** = cosine similarity ≥ threshold (adjustable slider)
- **Node colour** = user ID
- **Edge thickness** = similarity score (thicker = more similar)

**What it shows:**
- How memories **connect to each other** by semantic content
- Highly connected nodes = "hub" memories that relate to many other facts
- Disconnected nodes = unique, isolated facts
- Clusters = topic groups (e.g. all "Windows setup" memories form a cluster)

**Click any node** to see the full memory text and metadata in the right panel.

---

## Controls

| Control | What it does |
|---|---|
| **Edge similarity threshold** slider | Minimum cosine similarity (0.50–0.99) to draw an edge between two memories. Lower = more edges, higher = only the strongest connections |
| **🔄 Refresh memories** button | Re-fetches all memories from ES and re-runs UMAP projection |

**Tip:** Start with threshold `0.75` — this shows meaningful connections without overwhelming the graph. Raise to `0.90` to see only very strongly related memory pairs.

---

## Understanding the knowledge graph

```
add_memory("Hori uses Logseq") 
  → mem0 extracts: "User uses Logseq for note-taking"
  → embedding: [0.12, -0.34, 0.89, ...] (1024 numbers)
  → stored in Elasticsearch

add_memory("Hori takes notes in Logseq daily")
  → mem0 extracts: "User takes notes in Logseq daily"
  → embedding: [0.11, -0.35, 0.91, ...] (very similar!)
  → cosine similarity with previous = 0.97
  → appears as an EDGE in the knowledge graph
```

The graph reveals the **structure of the AI's memory** — which facts it knows deeply (many connections) and which are peripheral (no connections).

---

## Technical details

### UMAP projection
- Input: N × 1024 matrix (one row per memory, one column per embedding dimension)
- Output: N × 2 matrix (x, y coordinates for the scatter plot)
- Parameters: `n_neighbors=15`, `min_dist=0.1`, `random_state=42`
- Up to **500 memories** loaded per refresh

### Similarity computation
- Algorithm: **cosine similarity** between each pair of embedding vectors
- Range: 0.0 (completely different) → 1.0 (identical meaning)
- Computed as a full N×N matrix — all pairs at once

### Docker service
```yaml
mem0-graph:
  image: python:3.12-slim
  ports:
    - "8006:8050"
  environment:
    ES_HOST: elasticsearch
    ES_INDEX: mem0_memories
  depends_on:
    elasticsearch:
      condition: service_healthy
```

**Dependencies installed at startup:**
- `dash` — web framework
- `dash-cytoscape` — network graph component
- `plotly` — scatter/cluster chart
- `umap-learn` — dimensionality reduction
- `scikit-learn` — cosine similarity matrix
- `elasticsearch>=8,<9` — ES client

---

## Workflow: explore your AI's memory

1. Open AnythingLLM → chat with the agent → it calls `add_memory` automatically
2. Open http://localhost:8006
3. Click **🔄 Refresh memories**
4. Switch to **Cluster Map** — see all memories laid out spatially
5. Switch to **Knowledge Graph** — see which memories connect
6. Adjust the **threshold slider** to reveal more or fewer connections
7. Click any node to read the memory detail

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| "No memories found" on load | ES index empty or unreachable | Run `add_memory` from AnythingLLM first, or check `docker logs mem0` |
| Container keeps restarting | Still installing deps (umap-learn takes 3–5 min) | Wait and check `docker logs mem0-graph` |
| Graph has no edges at threshold 0.75 | Memories are too diverse / not enough memories | Lower threshold to 0.5, or add more related memories |
| UMAP looks random | Only 2–3 memories | Add more memories — UMAP needs ≥5 points to form meaningful clusters |

---

## Related pages
- [[Mem0 MCP Server]]
- [[Mem0]]
- [[Kibana - Mem0 Memory Browser]]
- [[MCP Stack]]
