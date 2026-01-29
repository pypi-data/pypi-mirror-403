"""
dashboard.callbacks_overall

Author: Duco Trompert
Course: Afstudeerproject bachelor Informatica
Thesis: Science of Science: An Integrated Pipeline for Tracing Conceptual Emergence and Evolution in Semantic Space
Date: 2026-01-23

Dash callbacks for the aggregated network view.

This module registers callbacks that:
- render node/edge details on selection,
- toggle bipartite headers for concept-method networks,
- export the current aggregated graph view as an SVG.
"""

from __future__ import annotations

import networkx as nx
import numpy as np
from dash import Dash, Input, Output, State, html, no_update

from sos_pipeline_udt.config import (
    DEFAULT_SIM_THRESHOLD,
    EDGE_WIDTH_MAX,
    EDGE_WIDTH_MIN,
    POS_SCALE,
    RANDOM_SEED,
    SPRING_ITER,
)

from sos_pipeline_udt.dashboard.data_store import corpus, kw_index
from sos_pipeline_udt.dashboard.graph_store import get_graph
from sos_pipeline_udt.dashboard.temporal_helpers import spring_layout_cyto
from sos_pipeline_udt.dashboard.vis_elements import bipartite_column_positions, nx_to_cytoscape_elements


def register(app: Dash) -> None:
    """Register all callbacks for the overall network dashboard view."""

    @app.callback(
        Output("overall-cyto", "elements"),
        Output("overall-cyto", "layout"),
        Output("overall-bipartite-headers", "style"),
        Output("overall-meta", "children"),
        Input("overall-network", "value"),
        Input("overall-min-value", "value"),
        Input("overall-node-scaling", "value"),
        Input("overall-edge-scaling", "value"),
        Input("overall-community", "value"),
        Input("overall-sim-threshold", "value"),
        prevent_initial_call=False,
    )
    def update_overall(
        network_kind, min_value, node_scaling, edge_scaling, community, sim_threshold
    ):
        """
        Update overall network elements and layout based on the UI controls.

        We intentionally match the *final* temporal visualisation:
        - positions are computed with NetworkX spring layout (same seed/iters/scale)
        - Cytoscape uses a preset layout (no COSE animation)
        """
        min_value = int(min_value or 0)
        sim_threshold = float(sim_threshold or DEFAULT_SIM_THRESHOLD)
        node_scaling = str(node_scaling)
        edge_scaling = str(edge_scaling)
        community = str(community)

        G = get_graph(
            str(network_kind),
            None,
            min_value=min_value,
            sim_threshold=sim_threshold,
        )

        elements = nx_to_cytoscape_elements(
            G,
            node_scaling=node_scaling,
            edge_scaling=edge_scaling,
            community_attr=community,
        )

        is_bip = str(network_kind).startswith("concept_method")

        if is_bip:
            node_els = [e for e in elements if "source" not in e.get("data", {})]
            concepts, methods = [], []
            for e in node_els:
                nt = (e.get("data", {}) or {}).get("node_type", "")
                if nt == "concept":
                    concepts.append(e)
                elif nt == "method":
                    methods.append(e)

            def score(e):
                """Return a sorting score for bipartite nodes based on precomputed degree."""
                d = e.get("data", {}) or {}
                return float(d.get("raw_weighted_degree") or d.get("raw_degree") or 0.0)

            concepts.sort(key=score, reverse=True)
            methods.sort(key=score, reverse=True)

            left_ids = [e["data"]["id"] for e in concepts]
            right_ids = [e["data"]["id"] for e in methods]

            pos = bipartite_column_positions(
                left_ids, right_ids, left_x=0.0, right_x=650.0, y_gap=42.0
            )

            for e in node_els:
                nid = e["data"]["id"]
                if nid in pos:
                    e["position"] = pos[nid]
                    e["locked"] = True

            layout = {"name": "preset", "fit": True, "padding": 20}
            headers_style = {
                "display": "flex",
                "justifyContent": "space-between",
                "padding": "0 18px 6px 18px",
                "fontWeight": 600,
                "color": "#444",
            }
        else:
            if G.number_of_nodes() > 0:
                pos = spring_layout_cyto(G, init_pos_cyto={}, scale=2.5)
            else:
                pos = {}

            for e in elements:
                d = e.get("data", {}) or {}
                if "source" in d:
                    continue
                nid = d.get("id")
                if nid in pos:
                    x, y = pos[nid]
                else:
                    x, y = pos.get(str(nid), (0.0, 0.0))
                e["position"] = {"x": float(x), "y": float(y)}

            layout = {"name": "preset", "fit": True, "padding": 50}
            headers_style = {"display": "none"}

        meta = [
            html.Div("Aggregated network"),
            html.Div(
                f"Nodes: {sum(1 for e in elements if 'source' not in e.get('data', {}))}\n"
                f"Edges: {sum(1 for e in elements if 'source' in e.get('data', {}))}"
            ),
        ]

        return elements, layout, headers_style, meta

    @app.callback(
        Output("overall-details", "children"),
        Input("overall-cyto", "tapNodeData"),
        Input("overall-cyto", "tapEdgeData"),
        State("overall-network", "value"),
        prevent_initial_call=False,
    )
    def show_overall_selection(node_data, edge_data, network_kind):
        """Render a details panel for the currently selected node or edge."""
        if node_data is None and edge_data is None:
            return html.Div("Click a node or edge to see details.")

        if node_data is not None:
            kw = node_data.get("id", "")
            pubs = [corpus[i] for i in kw_index.get(kw, [])][:12]
            return html.Div(
                [
                    html.Div([html.B("Node:"), f" {kw}"]),
                    html.Div(
                        [html.B("node_type:"), f" {node_data.get('node_type','N/A')}"]
                    ),
                    html.Div(
                        [html.B("community:"), f" {node_data.get('community','')}"]
                    ),
                    html.Hr(),
                    html.B("Publications containing this keyword (max 10):"),
                    (
                        html.Ul(
                            [
                                html.Li(
                                    [
                                        html.B(p.title),
                                        html.Div(
                                            f"{p.publication_date.isoformat()}, cited_by={p.total_cited_by}, source={p.source}"
                                        ),
                                    ],
                                    style={"marginBottom": "8px"},
                                )
                                for p in pubs
                            ]
                        )
                        if pubs
                        else html.Div(
                            "No publications found for this node (keyword normalization mismatch)."
                        )
                    ),
                ]
            )

        src = edge_data.get("source")
        tgt = edge_data.get("target")
        raw_w = edge_data.get("raw_weight")
        return html.Div(
            [
                html.Div([html.B("Edge:"), f" {src} - {tgt}"]),
                html.Div([html.B("raw_weight:"), f" {raw_w}"]),
            ]
        )

    @app.callback(
        Output("overall-cyto", "generateImage"),
        Input("overall-btn-svg", "n_clicks"),
        State("overall-network", "value"),
        prevent_initial_call=True,
    )
    def download_overall_svg(n_clicks, network_kind):
        """Trigger a Cytoscape SVG download of the current overall network view."""
        if not n_clicks:
            return no_update

        def _clean(x):
            """Sanitize a string for use as a filename."""
            return str(x or "").strip().replace(" ", "_").replace("/", "_")

        return {"type": "svg", "action": "download", "filename": _clean(network_kind)}
