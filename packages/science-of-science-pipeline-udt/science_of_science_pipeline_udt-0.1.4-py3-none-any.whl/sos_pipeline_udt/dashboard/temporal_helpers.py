"""
dashboard.temporal_helpers

Author: Duco Trompert
Course: Afstudeerproject bachelor Informatica
Thesis: Science of Science: An Integrated Pipeline for Tracing Conceptual Emergence and Evolution in Semantic Space
Date: 2026-01-23

Helper utilities for temporal network animation in the Dash dashboard.

This module provides small utilities for:
- stable edge keys and position storage,
- smooth interpolation helpers,
- placing new nodes near neighbors,
- aligning layouts between years to reduce global sweeps,
- computing spring layouts in Cytoscape coordinate space (including component packing).
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import networkx as nx
import numpy as np

from sos_pipeline_udt.config import (
    ANIM_INTERVAL_MS,
    FADE_STEPS,
    MAX_MOVE_PER_TRANSITION,
    MOVE_STEPS,
    POS_SCALE,
    RANDOM_SEED,
    REVEAL_STEPS,
    SPRING_ITER,
)


def _edge_key(u: str, v: str) -> Tuple[str, str]:
    """Return a stable undirected edge key as a sorted (u, v) tuple."""
    return (u, v) if u <= v else (v, u)


def _pos_get(
    pos_store: Dict[str, List[float]], node_id: str
) -> Tuple[float, float] | None:
    """Get a node position (x, y) from a simple store, or None if missing/invalid."""
    v = pos_store.get(node_id)
    if not v or len(v) != 2:
        return None
    return float(v[0]), float(v[1])


def _pos_set(
    pos_store: Dict[str, List[float]], node_id: str, x: float, y: float
) -> None:
    """Set a node position (x, y) into the store using rounded float values."""
    pos_store[node_id] = [round(float(x), 3), round(float(y), 3)]


def _smoothstep(t: float) -> float:
    """Smooth interpolation function mapping t in [0, 1] to an eased value in [0, 1]."""
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _neighbors_centroid(
    G: nx.Graph, node_id: str, pos_store: Dict[str, List[float]]
) -> Tuple[float, float] | None:
    """Compute the centroid of positioned neighbors of node_id, or None if unavailable."""
    pts = []
    if node_id not in G:
        return None
    for nb in G.neighbors(node_id):
        p = _pos_get(pos_store, str(nb))
        if p is not None:
            pts.append(p)
    if not pts:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (sum(xs) / len(xs), sum(ys) / len(ys))


def align_target_to_start(
    start_pos: Dict[str, List[float]],
    target_pos: Dict[str, List[float]],
    align_nodes: List[str],
) -> Dict[str, List[float]]:
    """Align target positions onto start positions to reduce global translation/rotation."""
    pts_s = []
    pts_t = []
    for n in align_nodes:
        if n in start_pos and n in target_pos:
            pts_s.append(start_pos[n])
            pts_t.append(target_pos[n])

    if len(pts_s) < 3:
        return target_pos

    S = np.array(pts_s, dtype=float)
    T = np.array(pts_t, dtype=float)

    S_mean = S.mean(axis=0)
    T_mean = T.mean(axis=0)
    S0 = S - S_mean
    T0 = T - T_mean

    sS = float(np.linalg.norm(S0)) + 1e-9
    sT = float(np.linalg.norm(T0)) + 1e-9
    S0 /= sS
    T0 /= sT

    U, _, Vt = np.linalg.svd(T0.T @ S0)
    R = U @ Vt

    out: Dict[str, List[float]] = {}
    for n, (x, y) in target_pos.items():
        v = np.array([x, y], dtype=float)
        v0 = (v - T_mean) / sT
        v1 = (v0 @ R) * sS + S_mean
        out[n] = [float(v1[0]), float(v1[1])]
    return out


def spring_layout_cyto(
    G: nx.Graph,
    *,
    init_pos_cyto: Dict[str, Tuple[float, float]],
    scale=1.0,
) -> Dict[str, Tuple[float, float]]:
    """
    Compute a spring layout per connected component and pack components horizontally.

    Accepts/returns Cytoscape coordinates (scaled by POS_SCALE).
    """
    if G.number_of_nodes() == 0:
        return {}

    init_norm: Dict[Any, Tuple[float, float]] = {}
    for n in G.nodes():
        nid = str(n)
        if nid in init_pos_cyto:
            x, y = init_pos_cyto[nid]
            init_norm[n] = (float(x) / POS_SCALE, float(y) / POS_SCALE)

    comps = list(nx.connected_components(G))
    comps.sort(key=lambda c: (-len(c), min(map(str, c))))

    COMPONENT_GAP_CYTO = 10
    gap_norm = COMPONENT_GAP_CYTO / POS_SCALE

    pos_all: Dict[Any, Tuple[float, float]] = {}
    cursor_x = 0.0

    for comp in comps:
        H = G.subgraph(comp)

        init_sub = {n: init_norm[n] for n in H.nodes() if n in init_norm}

        pos_comp = nx.spring_layout(
            H,
            pos=init_sub if init_sub else None,
            seed=RANDOM_SEED,
            iterations=SPRING_ITER,
            scale=scale,
        )

        xs = [p[0] for p in pos_comp.values()]
        ys = [p[1] for p in pos_comp.values()]
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)
        width = maxx - minx

        for n, (x, y) in pos_comp.items():
            pos_all[n] = (x - minx + cursor_x, y - miny)

        cursor_x += width + gap_norm

    return {
        str(n): (float(x) * POS_SCALE, float(y) * POS_SCALE)
        for n, (x, y) in pos_all.items()
    }


def spring_layout_components_cyto(
    G: nx.Graph,
    *,
    init_pos_cyto: Dict[str, Tuple[float, float]],
    component_gap: float = 220.0,
) -> Dict[str, Tuple[float, float]]:
    """
    Compute a spring layout per connected component and pack components to reduce zoom-out.

    This helps disconnected graphs where small satellite components can inflate the
    bounding box and force the camera to zoom too far out.
    """
    if G.number_of_nodes() == 0:
        return {}

    comps = list(nx.connected_components(G))

    if len(comps) <= 1:
        return spring_layout_cyto(G, init_pos_cyto=init_pos_cyto)

    comps_sorted = sorted(
        comps,
        key=lambda c: (-len(c), ",".join(sorted(map(str, c)))[:200]),
    )

    def _bbox(nodes: list[str], pos_map: Dict[str, Tuple[float, float]]):
        """Compute (minx, miny, maxx, maxy) for a set of nodes given a position map."""
        xs = [pos_map[n][0] for n in nodes if n in pos_map]
        ys = [pos_map[n][1] for n in nodes if n in pos_map]
        return (min(xs), min(ys), max(xs), max(ys))

    per_comp_pos: list[tuple[list[str], Dict[str, Tuple[float, float]]]] = []

    for comp in comps_sorted:
        H = G.subgraph(comp).copy()

        init_norm: Dict[Any, Tuple[float, float]] = {}
        for n in H.nodes():
            nid = str(n)
            if nid in init_pos_cyto:
                x, y = init_pos_cyto[nid]
                init_norm[n] = (float(x), float(y))

        pos_norm = nx.spring_layout(
            H,
            pos=init_norm,
            seed=RANDOM_SEED,
            iterations=SPRING_ITER,
            scale=1.0,
        )

        pos_cyto = {
            str(n): (float(x) * POS_SCALE, float(y) * POS_SCALE)
            for n, (x, y) in pos_norm.items()
        }
        per_comp_pos.append((list(map(str, H.nodes())), pos_cyto))

    packed: Dict[str, Tuple[float, float]] = {}

    main_nodes, main_pos = per_comp_pos[0]
    packed.update(main_pos)
    main_bb = _bbox(main_nodes, main_pos)
    cursor_x = main_bb[2] + component_gap
    cursor_y = main_bb[1]

    for nodes_c, pos_c in per_comp_pos[1:]:
        bb = _bbox(nodes_c, pos_c)
        dx = cursor_x - bb[0]
        dy = cursor_y - bb[1]

        for n in nodes_c:
            x, y = pos_c[n]
            packed[n] = (x + dx, y + dy)

        cursor_y += (bb[3] - bb[1]) + component_gap

    return packed


BIRTH_STEPS = REVEAL_STEPS
"""Alias used by the temporal animation controller for birth/fade-in step count."""
