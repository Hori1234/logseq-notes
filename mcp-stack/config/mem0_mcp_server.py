"""
Mem0 MCP Server
===============
A fully compliant Model Context Protocol server that wraps mem0ai,
backed by Elasticsearch as the vector store.

Transport : Streamable HTTP  →  /mcp
Port      : 8000  (mapped to host 8004 via docker-compose)

Tools
-----
  add_memory           — extract and store memories from a conversation
  search_memories      — semantic search across stored memories
  get_all_memories     — list every memory for a user
  get_memory           — fetch one memory by ID
  update_memory        — overwrite the text of a memory
  delete_memory        — remove one memory by ID
  delete_all_memories  — wipe all memories for a user  ⚠ irreversible
  get_memory_history   — audit trail of how a memory changed over time
"""

import json
import os
from typing import Optional

from mcp.server.fastmcp import FastMCP
from mem0 import Memory

# ── Monkey-patch: strip response_format from LLM calls ───────────────────────
# mem0ai hardcodes response_format={"type":"json_object"} which Gemma (and most
# local LM Studio models) reject. We patch the OpenAI client's chat.completions
# .create method to silently drop the field before the request is sent.
import openai as _openai
_original_create = _openai.OpenAI.chat  # placeholder — patch after Memory init

def _patch_openai_client(client):
    """Wrap client.chat.completions.create to strip response_format."""
    original = client.chat.completions.create
    def _patched_create(*args, **kwargs):
        kwargs.pop("response_format", None)
        return original(*args, **kwargs)
    client.chat.completions.create = _patched_create



_es_host = os.getenv("MEM0_VECTOR_STORE_HOST", "elasticsearch")
_es_port = int(os.getenv("MEM0_VECTOR_STORE_PORT", "9200"))

_config = {
    "vector_store": {
        "provider": "elasticsearch",
        "config": {
            "host": f"http://{_es_host}",   # scheme+name only; mem0ai appends :port itself
            "port": _es_port,
            "collection_name": os.getenv("MEM0_VECTOR_STORE_INDEX", "mem0_memories"),
            "embedding_model_dims": int(os.getenv("MEM0_EMBEDDER_DIMS", "1024")),
            "use_ssl": False,
            "user": os.getenv("ELASTIC_USERNAME", "elastic"),
            "password": os.getenv("ELASTIC_PASSWORD", ""),
        },
    },
    "llm": {
        "provider": os.getenv("MEM0_LLM_PROVIDER", "openai"),
        "config": {
            "model": os.getenv("MEM0_LLM_MODEL"),
            "api_key": os.getenv("MEM0_LLM_API_KEY", "lm-studio"),
            "openai_base_url": os.getenv(
                "MEM0_LLM_BASE_URL", "http://host.docker.internal:1234/v1"
            ),
            # Gemma (and most local models) don't support response_format=json_object.
            # response_format is stripped via monkey-patch below instead.
        },
    },
    "embedder": {
        "provider": os.getenv("MEM0_EMBEDDER_PROVIDER", "openai"),
        "config": {
            "model": os.getenv(
                "MEM0_EMBEDDER_MODEL", "text-embedding-mxbai-embed-large-v1"
            ),
            "api_key": os.getenv("MEM0_EMBEDDER_API_KEY", "lm-studio"),
            "openai_base_url": os.getenv(
                "MEM0_EMBEDDER_BASE_URL", "http://host.docker.internal:1234/v1"
            ),
        },
    },
}

_memory = Memory.from_config(_config)

# Apply the patch to the LLM client mem0 created internally
try:
    _patch_openai_client(_memory.llm.client)
except Exception:
    pass  # if internal API changes, fail silently — calls will surface errors naturally

# ── MCP server ────────────────────────────────────────────────────────────────

mcp = FastMCP(
    name="mem0-memory-server",
    instructions=(
        "This server provides persistent AI memory backed by Elasticsearch. "
        "Use add_memory to store facts extracted from conversations. "
        "Use search_memories at the start of every session to recall relevant context. "
        "Always pass a consistent user_id so memories are scoped correctly."
    ),
)


# ── Tool 1 — add_memory ───────────────────────────────────────────────────────

@mcp.tool()
def add_memory(
    messages: list,
    user_id: str,
    metadata: Optional[dict] = None,
) -> str:
    """
    Extract and persist memories from a conversation for a specific user.

    mem0 uses the LLM to intelligently extract facts worth remembering
    from the message list, then stores them as embeddings in Elasticsearch.
    Duplicate or contradictory memories are automatically merged/updated.

    Parameters
    ----------
    messages : list of dicts, each with 'role' and 'content' keys
        Example:
          [
            {"role": "user",      "content": "I always use dark mode"},
            {"role": "assistant", "content": "Got it, I'll remember that."}
          ]
        Supported roles: "user", "assistant", "system"

    user_id : str
        Unique identifier scoping these memories (e.g. "alice", "session-42").
        All later searches must use the same user_id to retrieve these memories.

    metadata : dict, optional
        Arbitrary key-value pairs stored alongside the memory for filtering.
        Example: {"source": "onboarding", "importance": "high"}

    Returns
    -------
    JSON string with 'results' list. Each item contains:
      - id      : UUID of the memory record
      - memory  : the extracted memory text
      - event   : "ADD" (new) or "UPDATE" (merged with existing)
      - score   : similarity score when updating an existing memory
    """
    try:
        result = _memory.add(messages, user_id=user_id, metadata=metadata or {})
        return json.dumps({"results": result})
    except Exception as exc:
        return json.dumps({"error": str(exc)})


# ── Tool 2 — search_memories ──────────────────────────────────────────────────

@mcp.tool()
def search_memories(query: str, user_id: str, limit: int = 10) -> str:
    """
    Semantically search stored memories for a user using vector similarity.

    Embeds the query with the configured embedding model, then performs
    a k-nearest-neighbour search in Elasticsearch. Returns the most relevant
    memories ranked by cosine similarity.

    Parameters
    ----------
    query : str
        Natural-language question or topic.
        Example: "What UI preferences does the user have?"

    user_id : str
        Scope the search to a specific user's memories.

    limit : int, default 10
        Maximum number of results (recommended: 5–20).

    Returns
    -------
    JSON string with 'results' list. Each item contains:
      - id         : UUID of the memory
      - memory     : text content of the memory
      - score      : cosine similarity (0–1, higher = more relevant)
      - metadata   : any metadata stored with the memory
      - user_id    : owner of this memory
      - created_at : ISO timestamp
      - updated_at : ISO timestamp
    """
    try:
        results = _memory.search(query, filters={"user_id": user_id}, limit=limit)
        return json.dumps({"results": results})
    except Exception as exc:
        return json.dumps({"error": str(exc)})


# ── Tool 3 — get_all_memories ─────────────────────────────────────────────────

@mcp.tool()
def get_all_memories(user_id: str) -> str:
    """
    Retrieve every stored memory for a user without any search or filtering.

    Use this to present a full memory summary or to audit what has been stored.
    For large memory sets, prefer search_memories to stay within context limits.

    Parameters
    ----------
    user_id : str
        Unique identifier for the user.

    Returns
    -------
    JSON string with 'memories' list. Each item contains:
      - id         : UUID
      - memory     : text content
      - metadata   : stored metadata dict
      - user_id    : owner
      - created_at : ISO timestamp
      - updated_at : ISO timestamp
    """
    try:
        results = _memory.get_all(filters={"user_id": user_id})
        return json.dumps({"memories": results})
    except Exception as exc:
        return json.dumps({"error": str(exc)})


# ── Tool 4 — get_memory ───────────────────────────────────────────────────────

@mcp.tool()
def get_memory(memory_id: str) -> str:
    """
    Fetch a single memory record by its unique ID.

    Use this when you already know the memory ID (e.g. from a prior
    add_memory or search_memories call) and want full detail.

    Parameters
    ----------
    memory_id : str
        UUID of the memory to retrieve.
        Example: "3f2a1b4c-8e9d-4c7a-b6f5-1a2b3c4d5e6f"

    Returns
    -------
    JSON string with the memory object:
      - id, memory, metadata, user_id, created_at, updated_at
    Returns {"error": "..."} if the ID does not exist.
    """
    try:
        result = _memory.get(memory_id)
        if result is None:
            return json.dumps({"error": f"Memory '{memory_id}' not found"})
        return json.dumps(result)
    except Exception as exc:
        return json.dumps({"error": str(exc)})


# ── Tool 5 — update_memory ────────────────────────────────────────────────────

@mcp.tool()
def update_memory(memory_id: str, data: str) -> str:
    """
    Overwrite the text content of an existing memory.

    The new text is re-embedded and the Elasticsearch document is updated
    in place. The memory's ID and metadata are preserved; only the text
    and updated_at change.

    Use this to correct inaccurate memories or to enrich them with new detail.

    Parameters
    ----------
    memory_id : str
        UUID of the memory to update.

    data : str
        New text content for the memory.
        Example: "User prefers dark mode and high contrast themes"

    Returns
    -------
    JSON string with the updated memory object, or {"error": "..."} on failure.
    """
    try:
        result = _memory.update(memory_id, data=data)
        if result is None:
            return json.dumps({"error": f"Memory '{memory_id}' not found"})
        return json.dumps(result)
    except Exception as exc:
        return json.dumps({"error": str(exc)})


# ── Tool 6 — delete_memory ────────────────────────────────────────────────────

@mcp.tool()
def delete_memory(memory_id: str) -> str:
    """
    Permanently delete a single memory by its ID.

    This removes both the Elasticsearch document and the embedding vector.
    The operation cannot be undone. Use get_memory_history beforehand
    if you want to record the memory before deletion.

    Parameters
    ----------
    memory_id : str
        UUID of the memory to delete.

    Returns
    -------
    JSON string: {"deleted": "<memory_id>"} on success,
    or {"error": "..."} on failure.
    """
    try:
        _memory.delete(memory_id)
        return json.dumps({"deleted": memory_id})
    except Exception as exc:
        return json.dumps({"error": str(exc)})


# ── Tool 7 — delete_all_memories ──────────────────────────────────────────────

@mcp.tool()
def delete_all_memories(user_id: str) -> str:
    """
    ⚠ IRREVERSIBLE — Delete ALL memories belonging to a user.

    Removes every Elasticsearch document scoped to this user_id, including
    all embeddings and metadata. Use with caution; there is no undo.

    Typical use cases:
      - User requests a "forget me" / data erasure
      - Resetting a test/demo user between runs

    Parameters
    ----------
    user_id : str
        Unique identifier of the user whose memories to erase.

    Returns
    -------
    JSON string: {"deleted_all_for": "<user_id>", "status": "ok"}
    """
    try:
        _memory.delete_all(filters={"user_id": user_id})
        return json.dumps({"deleted_all_for": user_id, "status": "ok"})
    except Exception as exc:
        return json.dumps({"error": str(exc)})


# ── Tool 8 — get_memory_history ───────────────────────────────────────────────

@mcp.tool()
def get_memory_history(memory_id: str) -> str:
    """
    Retrieve the full change history of a memory — an audit trail showing
    every ADD, UPDATE, and DELETE event that has occurred for this memory ID.

    Useful for:
      - Debugging why a memory has unexpected content
      - Understanding how the AI's understanding of a user has evolved
      - Compliance / auditing purposes

    Parameters
    ----------
    memory_id : str
        UUID of the memory to inspect.

    Returns
    -------
    JSON string with 'history' list. Each entry contains:
      - id          : UUID of the history event
      - memory_id   : the memory this event belongs to
      - old_memory  : text before the change (null for ADD events)
      - new_memory  : text after the change (null for DELETE events)
      - event       : "ADD", "UPDATE", or "DELETE"
      - created_at  : ISO timestamp of when this change occurred
      - updated_at  : ISO timestamp
    """
    try:
        history = _memory.history(memory_id)
        return json.dumps({"history": history})
    except Exception as exc:
        return json.dumps({"error": str(exc)})

# ── Entrypoint ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import JSONResponse, Response
    from starlette.routing import Mount, Route
    from starlette.middleware.base import BaseHTTPMiddleware

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    async def health(request: Request):
        return JSONResponse({"status": "ok", "server": "mem0-memory-server"})

    mcp_app = mcp.streamable_http_app()

    class GetMcpInterceptMiddleware(BaseHTTPMiddleware):
        """Return 200 for bare GET /mcp probes (no SSE Accept header).
        AnythingLLM sends these to check liveness; without a 2xx reply it
        marks the server as stopped and never sends POST tool calls."""
        async def dispatch(self, request: Request, call_next):
            if request.method == "GET" and request.url.path == "/mcp":
                accept = request.headers.get("accept", "")
                if "text/event-stream" not in accept:
                    return JSONResponse({
                        "status": "ok",
                        "server": "mem0-memory-server",
                        "transport": "streamable-http",
                        "endpoint": "POST /mcp",
                    })
            return await call_next(request)

    # Mounting the MCP app alone does not propagate its lifespan, so the
    # session manager never starts and POST /mcp returns "Task group is not
    # initialized". Reuse FastMCP's lifespan on the outer application.
    app = Starlette(
        routes=[
            Route("/health", health),
            Mount("/", app=mcp_app),
        ],
        lifespan=mcp_app.router.lifespan_context,
    )
    app.add_middleware(GetMcpInterceptMiddleware)

    uvicorn.run(app, host=host, port=port)
