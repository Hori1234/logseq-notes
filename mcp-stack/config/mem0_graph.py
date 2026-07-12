"""
Mem0 Knowledge Graph Dashboard
================================
Fetches all memories from Elasticsearch, projects their 1024-dim vectors
to 2D using UMAP, then renders two interactive views in a Dash web app:

  Tab 1 — Cluster Map    : scatter plot where semantically similar memories
                           cluster together (UMAP projection)
  Tab 2 — Knowledge Graph: force-directed network where nodes are memories
                           and edges connect pairs above a cosine similarity
                           threshold

Open: http://localhost:8006
"""

import os
import numpy as np
import plotly.graph_objects as go
import dash
from dash import dcc, html, Input, Output
import dash_cytoscape as cyto
from elasticsearch import Elasticsearch

# ── Config ────────────────────────────────────────────────────────────────────

ES_HOST  = os.getenv("ES_HOST", "elasticsearch")
ES_PORT  = int(os.getenv("ES_PORT", "9200"))
ES_INDEX = os.getenv("ES_INDEX", "mem0_memories")
HOST     = os.getenv("HOST", "0.0.0.0")
PORT     = int(os.getenv("PORT", "8050"))

es = Elasticsearch(f"http://{ES_HOST}:{ES_PORT}")

USER_COLORS = [
    "#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A",
    "#19D3F3", "#FF6692", "#B6E880", "#FF97FF", "#FECB52",
]

# ── Data helpers ──────────────────────────────────────────────────────────────

def fetch_memories():
    """Return list of memory dicts with vectors included."""
    try:
        resp = es.search(index=ES_INDEX, body={"size": 500, "query": {"match_all": {}}})
    except Exception as e:
        print(f"ES error: {e}")
        return []

    docs = []
    for hit in resp["hits"]["hits"]:
        src  = hit["_source"]
        meta = src.get("metadata", {})
        vec  = src.get("vector")
        text = meta.get("data") or src.get("text", "")
        if not vec or not text:
            continue
        docs.append({
            "id":           hit["_id"],
            "text":         text,
            "user_id":      meta.get("user_id", "unknown"),
            "attributed_to":meta.get("attributed_to", "unknown"),
            "created_at":   str(meta.get("created_at", "")),
            "vector":       vec,
        })
    return docs


def project_umap(vectors):
    """Reduce N×1024 → N×2 with UMAP."""
    import umap as umap_lib
    n = len(vectors)
    if n == 1:
        return np.array([[0.0, 0.0]])
    n_neighbors = min(15, n - 1)
    reducer = umap_lib.UMAP(n_components=2, n_neighbors=n_neighbors,
                             min_dist=0.1, random_state=42)
    return reducer.fit_transform(np.array(vectors, dtype=np.float32))


def cosine_sim_matrix(vectors):
    """Pairwise cosine similarity matrix."""
    from sklearn.metrics.pairwise import cosine_similarity
    return cosine_similarity(np.array(vectors, dtype=np.float32))


# ── Figure builders ───────────────────────────────────────────────────────────

def cluster_figure(docs, coords):
    users      = sorted(set(d["user_id"] for d in docs))
    user_color = {u: USER_COLORS[i % len(USER_COLORS)] for i, u in enumerate(users)}
    fig        = go.Figure()

    for user in users:
        idx = [i for i, d in enumerate(docs) if d["user_id"] == user]
        xs  = coords[idx, 0]
        ys  = coords[idx, 1]
        labels = [
            (d["text"][:45] + "…") if len(d["text"]) > 45 else d["text"]
            for d in [docs[i] for i in idx]
        ]
        fig.add_trace(go.Scatter(
            x=xs, y=ys,
            mode="markers+text",
            name=user,
            marker=dict(size=14, color=user_color[user], opacity=0.88,
                        line=dict(width=1.5, color="#ffffff")),
            text=labels,
            textposition="top center",
            textfont=dict(size=9, color="#cccccc"),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "<span style='color:#aaa'>user:</span> %{customdata[1]}<br>"
                "<span style='color:#aaa'>source:</span> %{customdata[2]}<br>"
                "<span style='color:#aaa'>saved:</span> %{customdata[3]}"
                "<extra></extra>"
            ),
            customdata=[
                [docs[i]["text"], docs[i]["user_id"],
                 docs[i]["attributed_to"], docs[i]["created_at"]]
                for i in idx
            ],
        ))

    fig.update_layout(
        title=dict(text="Memory Cluster Map — UMAP 2D projection",
                   font=dict(color="#e2e2e2", size=16)),
        xaxis=dict(title="UMAP-1", color="#666", showgrid=True,
                   gridcolor="#1e1e3a", zeroline=False),
        yaxis=dict(title="UMAP-2", color="#666", showgrid=True,
                   gridcolor="#1e1e3a", zeroline=False),
        hovermode="closest",
        plot_bgcolor="#0f0f1a",
        paper_bgcolor="#16213e",
        font_color="#cccccc",
        legend=dict(bgcolor="#1a1a2e", bordercolor="#533483", borderwidth=1),
        height=700,
        margin=dict(l=50, r=30, t=60, b=50),
    )
    return fig


def cyto_elements(docs, sim_matrix, threshold):
    users      = sorted(set(d["user_id"] for d in docs))
    user_color = {u: USER_COLORS[i % len(USER_COLORS)] for i, u in enumerate(users)}

    nodes = [
        {
            "data": {
                "id":           d["id"],
                "label":        (d["text"][:50] + "…") if len(d["text"]) > 50 else d["text"],
                "full_text":    d["text"],
                "user_id":      d["user_id"],
                "attributed_to":d["attributed_to"],
                "color":        user_color.get(d["user_id"], "#636EFA"),
            }
        }
        for d in docs
    ]

    edges = [
        {
            "data": {
                "source": docs[i]["id"],
                "target": docs[j]["id"],
                "weight": round(float(sim_matrix[i][j]), 3),
                "label":  f"{sim_matrix[i][j]:.2f}",
            }
        }
        for i in range(len(docs))
        for j in range(i + 1, len(docs))
        if float(sim_matrix[i][j]) >= threshold
    ]

    return nodes + edges


# ── Dash layout ───────────────────────────────────────────────────────────────

cyto.load_extra_layouts()

_DARK_BG  = "#0f0f1a"
_CARD_BG  = "#1a1a2e"
_PANEL_BG = "#16213e"
_PURPLE   = "#533483"
_GREEN    = "#00CC96"

app = dash.Dash(__name__, title="Mem0 Knowledge Graph",
                meta_tags=[{"name": "viewport",
                             "content": "width=device-width, initial-scale=1"}])
app.layout = html.Div(
    style={"backgroundColor": _DARK_BG, "minHeight": "100vh",
           "fontFamily": "'Inter', 'Segoe UI', sans-serif"},
    children=[

        # ── Header ────────────────────────────────────────────────────────────
        html.Div(
            style={"backgroundColor": _CARD_BG, "padding": "18px 30px",
                   "borderBottom": f"2px solid {_PURPLE}",
                   "display": "flex", "justifyContent": "space-between",
                   "alignItems": "center"},
            children=[
                html.Div([
                    html.H1("🧠 Mem0 Knowledge Graph",
                            style={"color": "#e2e2e2", "margin": 0, "fontSize": "22px",
                                   "fontWeight": 700}),
                    html.P("Visual explorer for AI memories stored in Elasticsearch",
                           style={"color": "#666", "margin": "3px 0 0", "fontSize": "12px"}),
                ]),
                html.Div(id="memory-count",
                         style={"color": _GREEN, "fontSize": "15px", "fontWeight": 600}),
            ]
        ),

        # ── Controls ──────────────────────────────────────────────────────────
        html.Div(
            style={"backgroundColor": _PANEL_BG, "padding": "12px 30px",
                   "display": "flex", "gap": "24px", "alignItems": "center",
                   "flexWrap": "wrap", "borderBottom": "1px solid #222244"},
            children=[
                html.Div([
                    html.Label("Edge similarity threshold",
                               style={"color": "#999", "fontSize": "11px",
                                      "display": "block", "marginBottom": "4px"}),
                    dcc.Slider(
                        id="threshold-slider",
                        min=0.50, max=0.99, step=0.01, value=0.75,
                        marks={0.5: {"label": "0.50", "style": {"color": "#999"}},
                               0.7: {"label": "0.70", "style": {"color": "#999"}},
                               0.9: {"label": "0.90", "style": {"color": "#999"}}},
                        tooltip={"placement": "bottom", "always_visible": True},
                    ),
                ], style={"flex": "1", "minWidth": "260px", "maxWidth": "420px"}),

                html.Button(
                    "🔄  Refresh memories", id="refresh-btn", n_clicks=0,
                    style={"backgroundColor": _PURPLE, "color": "white",
                           "border": "none", "padding": "9px 18px",
                           "borderRadius": "6px", "cursor": "pointer",
                           "fontSize": "13px", "fontWeight": 600},
                ),
            ]
        ),

        # ── Tabs ──────────────────────────────────────────────────────────────
        dcc.Tabs(
            id="tabs", value="cluster",
            style={"backgroundColor": _PANEL_BG},
            colors={"border": _PURPLE, "primary": _PURPLE, "background": _CARD_BG},
            children=[
                dcc.Tab(label="📍  Cluster Map",    value="cluster",
                        style={"color": "#999", "backgroundColor": _CARD_BG},
                        selected_style={"color": "white", "backgroundColor": "#0f3460",
                                        "borderTop": f"3px solid {_GREEN}"}),
                dcc.Tab(label="🕸️  Knowledge Graph", value="graph",
                        style={"color": "#999", "backgroundColor": _CARD_BG},
                        selected_style={"color": "white", "backgroundColor": "#0f3460",
                                        "borderTop": f"3px solid {_GREEN}"}),
            ]
        ),

        html.Div(id="tab-content", style={"padding": "20px 30px"}),

        # ── Hidden stores ─────────────────────────────────────────────────────
        dcc.Store(id="docs-store"),
        dcc.Store(id="coords-store"),
        dcc.Store(id="sim-store"),
    ]
)


# ── Callbacks ─────────────────────────────────────────────────────────────────

@app.callback(
    Output("docs-store",   "data"),
    Output("coords-store", "data"),
    Output("sim-store",    "data"),
    Output("memory-count", "children"),
    Input("refresh-btn",   "n_clicks"),
    prevent_initial_call=False,
)
def load_data(_):
    docs = fetch_memories()
    if not docs:
        return [], [], [], "⚠  No memories found"

    vectors = [d["vector"] for d in docs]
    coords  = project_umap(vectors).tolist()
    sim     = cosine_sim_matrix(vectors).tolist()

    # Strip vectors before storing (too large for dcc.Store)
    clean = [{k: v for k, v in d.items() if k != "vector"} for d in docs]
    return clean, coords, sim, f"✓  {len(docs)} memories loaded"


@app.callback(
    Output("tab-content", "children"),
    Input("tabs",             "value"),
    Input("docs-store",       "data"),
    Input("coords-store",     "data"),
    Input("sim-store",        "data"),
    Input("threshold-slider", "value"),
)
def render_tab(tab, docs, coords, sim_matrix, threshold):
    empty_msg = html.P(
        "No memories yet — ask the agent to remember something first.",
        style={"color": "#555", "textAlign": "center", "marginTop": "80px",
               "fontSize": "15px"}
    )

    if not docs:
        return empty_msg

    # ── Cluster Map ───────────────────────────────────────────────────────────
    if tab == "cluster":
        coords_np = np.array(coords)
        fig = cluster_figure(docs, coords_np)
        return dcc.Graph(
            figure=fig,
            style={"height": "700px"},
            config={"scrollZoom": True, "displayModeBar": True,
                    "modeBarButtonsToRemove": ["lasso2d", "select2d"]},
        )

    # ── Knowledge Graph ───────────────────────────────────────────────────────
    if tab == "graph":
        sim_np   = np.array(sim_matrix)
        elements = cyto_elements(docs, sim_np, threshold)
        n_edges  = sum(1 for e in elements if "source" in e.get("data", {}))

        return html.Div([
            html.P(
                f"{len(docs)} memory nodes · {n_edges} edges "
                f"(cosine similarity ≥ {threshold})",
                style={"color": "#777", "fontSize": "12px", "marginBottom": "10px"},
            ),
            html.Div(
                style={"display": "flex", "gap": "16px", "height": "680px"},
                children=[
                    cyto.Cytoscape(
                        id="cyto-graph",
                        layout={
                            "name": "cose-bilkent",
                            "animate": True,
                            "idealEdgeLength": 140,
                            "nodeRepulsion": 10000,
                            "gravity": 0.25,
                            "numIter": 2500,
                        },
                        style={"flex": "1", "height": "680px",
                               "backgroundColor": _CARD_BG, "borderRadius": "8px",
                               "border": f"1px solid {_PURPLE}"},
                        elements=elements,
                        stylesheet=[
                            {
                                "selector": "node",
                                "style": {
                                    "background-color":  "data(color)",
                                    "label":             "data(label)",
                                    "color":             "#e2e2e2",
                                    "font-size":         "9px",
                                    "text-wrap":         "wrap",
                                    "text-max-width":    "100px",
                                    "width":             "70px",
                                    "height":            "70px",
                                    "text-valign":       "center",
                                    "text-halign":       "center",
                                    "border-width":      "2px",
                                    "border-color":      _PURPLE,
                                    "text-background-color":   _CARD_BG,
                                    "text-background-opacity": 0.75,
                                    "text-background-padding": "3px",
                                },
                            },
                            {
                                "selector": "edge",
                                "style": {
                                    "width":       "data(weight)",
                                    "line-color":  _PURPLE,
                                    "opacity":     0.55,
                                    "label":       "data(label)",
                                    "font-size":   "8px",
                                    "color":       "#888",
                                    "curve-style": "bezier",
                                },
                            },
                            {
                                "selector": "node:selected",
                                "style": {
                                    "border-width":      "3px",
                                    "border-color":      _GREEN,
                                    "background-color":  _GREEN,
                                },
                            },
                        ],
                        userZoomingEnabled=True,
                        userPanningEnabled=True,
                        boxSelectionEnabled=False,
                    ),

                    # Info panel ──────────────────────────────────────────────
                    html.Div(
                        id="node-info",
                        style={
                            "width": "280px", "minWidth": "280px",
                            "backgroundColor": _CARD_BG, "borderRadius": "8px",
                            "padding": "16px", "color": "#ccc", "fontSize": "13px",
                            "overflowY": "auto", "border": f"1px solid {_PURPLE}",
                        },
                        children=[
                            html.P("← Click any node to inspect it",
                                   style={"color": "#444", "textAlign": "center",
                                          "marginTop": "60px", "fontSize": "13px"}),
                        ]
                    ),
                ]
            ),
        ])


@app.callback(
    Output("node-info", "children"),
    Input("cyto-graph", "tapNodeData"),
    prevent_initial_call=True,
)
def show_node_detail(data):
    if not data:
        return html.P("Nothing selected")
    return html.Div([
        html.H4("Memory Detail", style={"color": _GREEN, "marginTop": 0,
                                         "fontSize": "14px", "fontWeight": 700}),
        html.Hr(style={"borderColor": _PURPLE, "margin": "8px 0"}),
        html.Div([
            html.P(data.get("full_text", ""),
                   style={"lineHeight": "1.65", "color": "#ddd",
                           "backgroundColor": "#0f0f1a", "padding": "10px",
                           "borderRadius": "6px", "fontSize": "12px"}),
            html.Table([
                html.Tr([html.Td("User",   style={"color": "#777", "paddingRight": "10px"}),
                         html.Td(data.get("user_id", "—"), style={"color": "#ccc"})]),
                html.Tr([html.Td("Source", style={"color": "#777", "paddingRight": "10px"}),
                         html.Td(data.get("attributed_to", "—"), style={"color": "#ccc"})]),
            ], style={"marginTop": "10px", "fontSize": "12px", "width": "100%"}),
            html.Hr(style={"borderColor": "#222244", "margin": "10px 0"}),
            html.P("ES document ID", style={"color": "#555", "fontSize": "10px",
                                              "margin": "0 0 3px"}),
            html.Code(data.get("id", ""), style={"fontSize": "9px", "color": "#666",
                                                   "wordBreak": "break-all"}),
        ])
    ])


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"Starting Mem0 Knowledge Graph on http://{HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=False)
