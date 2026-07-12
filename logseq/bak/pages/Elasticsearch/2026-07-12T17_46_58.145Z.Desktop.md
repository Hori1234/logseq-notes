---
title: Elasticsearch
tags: [mcp, elasticsearch, search, vector-db]
status: active
source: https://www.elastic.co/elasticsearch
---

# Elasticsearch

> The search and analytics engine powering [[MCP Stack/Elasticsearch MCP]] and [[MCP Stack/Mem0]].

## Role in This Stack

Elasticsearch serves two purposes:
1. **Vector store** for [[MCP Stack/Mem0]] — stores AI memory embeddings
2. **Full-text / analytics engine** — queryable via [[MCP Stack/Elasticsearch MCP]]

## Docker Compose Config

```yaml
elasticsearch:
  image: docker.elastic.co/elasticsearch/elasticsearch:8.17.0
  environment:
    - discovery.type=single-node
    - xpack.security.enabled=false       # TLS off for local dev
    - ES_JAVA_OPTS=-Xms512m -Xmx512m
    - ELASTIC_PASSWORD=${ELASTIC_PASSWORD}
  volumes:
    - es-data:/usr/share/elasticsearch/data
  ports:
    - "9200:9200"
```

> **Security note**: `xpack.security.enabled=false` is appropriate for local development only. Enable it in production.

## Verify It's Running

```bash
curl http://localhost:9200/_cluster/health?pretty
```

Expected response:

```json
{
  "cluster_name" : "docker-cluster",
  "status" : "green",
  "number_of_nodes" : 1,
  ...
}
```

## Useful Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /_cluster/health` | Cluster health |
| `GET /_cat/indices?v` | List all indices |
| `GET /mem0_memories/_count` | Count Mem0 memory docs |
| `GET /_nodes/stats` | Node statistics |

## Memory Requirements

| Heap (`ES_JAVA_OPTS`) | Recommended RAM |
|----------------------|-----------------|
| 512m | 2 GB |
| 1g | 4 GB |
| 2g | 8 GB |

Increase heap size in `.env` or compose file if indexing large volumes of documents.

## Optional: Kibana UI

Kibana is included as an optional service in the compose file. Start it with:

```bash
docker compose --profile kibana up -d
```

Then open http://localhost:5601 in your browser.

## Data Persistence

Data is stored in the `es-data` Docker volume. To back it up:

```bash
# Snapshot to a directory
curl -X PUT "localhost:9200/_snapshot/my_backup" \
  -H 'Content-Type: application/json' \
  -d '{"type":"fs","settings":{"location":"/usr/share/elasticsearch/backup"}}'
```

## Troubleshooting

- **"max virtual memory areas vm.max_map_count [65530] is too low"** (Linux):
  ```bash
  sudo sysctl -w vm.max_map_count=262144
  # Make permanent: echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
  ```
- **Container keeps restarting** — Check `docker logs elasticsearch`; often a memory issue, increase Docker Desktop RAM allocation

## References

- [[MCP Stack]] — Back to main stack overview
- [[MCP Stack/Elasticsearch MCP]] — MCP server on top of this cluster
- [[MCP Stack/Mem0]] — Uses this as vector store
