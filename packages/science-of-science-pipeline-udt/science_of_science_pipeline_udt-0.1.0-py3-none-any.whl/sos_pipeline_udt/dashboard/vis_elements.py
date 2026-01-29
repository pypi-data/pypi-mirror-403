"""
dashboard.vis_elements

Author: Duco Trompert
Course: Afstudeerproject bachelor Informatica
Thesis: Science of Science: An Integrated Pipeline for Tracing Conceptual Emergence and Evolution in Semantic Space
Date: 2026-01-23

Visualization helpers for converting NetworkX graphs into Dash Cytoscape elements.

This module includes utilities for:
- generating consistent community colors,
- mapping edge weights to display widths,
- converting graphs into Cytoscape element dictionaries,
- building an index from keywords to publications for detail panes,
- computing fixed positions for bipartite concept–method layouts.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple

import networkx as nx

from sos_pipeline_udt.analysis.embeddings import keyword_token
from sos_pipeline_udt.config import EDGE_WIDTH_MAX, EDGE_WIDTH_MIN
from sos_pipeline_udt.data.publication_corpus import PublicationCorpus


def _hsv_color(i: int, n: int) -> str:
    """Generate a visually distinct RGB color using evenly spaced HSV hues."""
    import colorsys

    n = max(n, 1)
    h = (i % n) / n
    r, g, b = colorsys.hsv_to_rgb(h, 0.55, 0.95)
    return f"rgb({int(r*255)},{int(g*255)},{int(b*255)})"


def _community_color_map(G: nx.Graph, community_attr: str) -> Dict[Any, str]:
    """Create a stable mapping from community id to display color."""
    groups = sorted({data.get(community_attr, 0) for _, data in G.nodes(data=True)})
    return {g: _hsv_color(i, len(groups)) for i, g in enumerate(groups)}


def _scale_to_range(values: List[float], out_min: float, out_max: float) -> List[float]:
    """Rescale numeric values linearly into the range [out_min, out_max]."""
    if not values:
        return []
    vmin = min(values)
    vmax = max(values)
    if vmax == vmin:
        mid = (out_min + out_max) / 2.0
        return [mid for _ in values]
    return [out_min + (v - vmin) * (out_max - out_min) / (vmax - vmin) for v in values]


def edge_width_map(G: nx.Graph, scaling: str) -> Dict[Tuple[Any, Any], float]:
    """
    Compute edge display widths from 'raw_weight' and rescale to [EDGE_WIDTH_MIN, EDGE_WIDTH_MAX].

    This avoids the very large default widths coming from add_edge_widths(min=10,max=50).
    """
    edges = []
    raw_vals = []
    for u, v, w in G.edges(data="raw_weight"):
        if w is None:
            continue
        edges.append((u, v))
        raw_vals.append(float(w))

    if not edges:
        return {}

    scaling_upper = scaling.upper()

    def transform(x: float) -> float:
        """Transform a raw weight based on the requested scaling mode."""
        if scaling_upper.endswith("NONE"):
            return 1.0
        if scaling_upper.endswith("LINEAR"):
            return x
        if scaling_upper.endswith("SQRT"):
            return math.sqrt(max(x, 0.0))
        if scaling_upper.endswith("LOG"):
            return math.log(1.0 + max(x, 0.0))
        return x

    transformed = [transform(x) for x in raw_vals]
    widths = _scale_to_range(transformed, EDGE_WIDTH_MIN, EDGE_WIDTH_MAX)

    return {e: w for e, w in zip(edges, widths)}


def nx_to_cytoscape_elements(
    G: nx.Graph,
    *,
    node_scaling: str,
    edge_scaling: str,
    community_attr: str,
) -> List[dict]:
    """Convert a NetworkX graph into a list of Dash Cytoscape elements."""
    color_map = _community_color_map(G, community_attr)
    ew = edge_width_map(G, edge_scaling)

    elements: List[dict] = []

    for node, data in G.nodes(data=True):
        size = float(data.get(node_scaling, 18.0))
        comm = data.get(community_attr, 0)
        node_type = data.get("node_type")

        elements.append(
            {
                "data": {
                    "id": str(node),
                    "label": str(node),
                    "size": size,
                    "community": comm,
                    "color": color_map.get(comm, "rgb(160,160,160)"),
                    "node_type": node_type or "",
                    "raw_degree": data.get("raw_degree", None),
                    "raw_weighted_degree": data.get("raw_weighted_degree", None),
                }
            }
        )

    for u, v, data in G.edges(data=True):
        width = ew.get((u, v), ew.get((v, u), 1.0))
        elements.append(
            {
                "data": {
                    "id": f"{u}__{v}",
                    "source": str(u),
                    "target": str(v),
                    "width": float(width),
                    "raw_weight": data.get("raw_weight", None),
                }
            }
        )

    return elements


def publications_index(corpus: PublicationCorpus) -> Dict[str, List[int]]:
    """
    Build a mapping of keyword -> list of publication indices that contain it.

    Note: this includes both the raw keyword strings and the normalized keyword_token
    variant (when different) to improve matching in the dashboard detail views.
    """
    index: Dict[str, List[int]] = {}
    for i, pub in enumerate(corpus.data):
        for kw in pub.keywords:
            index.setdefault(kw, []).append(i)
            tok = keyword_token(kw)
            if tok and tok != kw:
                index.setdefault(tok, []).append(i)
    return index


def bipartite_column_positions(
    left_ids: list[str],
    right_ids: list[str],
    *,
    left_x: float = 0.0,
    right_x: float = 650.0,
    y_gap: float = 42.0,
) -> dict[str, dict[str, float]]:
    """
    Compute fixed positions for a strict two-column bipartite layout.

    Returns a mapping: {node_id: {"x": ..., "y": ...}}.
    Input lists should already be sorted in the desired top-to-bottom order.
    """
    pos: dict[str, dict[str, float]] = {}

    def _centered_y(ids: list[str], x: float):
        n = len(ids)
        y0 = -((n - 1) * y_gap) / 2.0 if n > 1 else 0.0
        for i, nid in enumerate(ids):
            pos[nid] = {"x": float(x), "y": float(y0 + i * y_gap)}

    _centered_y(left_ids, left_x)
    _centered_y(right_ids, right_x)
    return pos
