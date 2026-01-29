"""
analysis.metrics

Author: Duco Trompert
Course: Afstudeerproject bachelor Informatica
Thesis: Science of Science: An Integrated Pipeline for Tracing Conceptual Emergence and Evolution in Semantic Space
Date: 2026-01-23

Graph metric utilities used for analysis and visualization, including:
- node size scaling (centrality-based),
- edge width scaling (weight transforms),
- community detection,
- temporal network similarity and birth/death analysis.
"""

import math
from enum import StrEnum
from typing import Any

import networkx as nx

from sos_pipeline_udt.config import RANDOM_SEED


def scale_to_range(values: dict, minimum: int, maximum: int) -> dict:
    """Linearly scale a mapping of item -> value into the range [minimum, maximum]."""
    if not values:
        return {}

    v_min = min(values.values())
    v_max = max(values.values())

    if v_max == v_min:
        mid = (minimum + maximum) / 2
        return {node: mid for node in values}

    scaled: dict = {}
    for node, v in values.items():
        norm = (v - v_min) / (v_max - v_min)  # 0-1
        scaled[node] = minimum + norm * (maximum - minimum)
    return scaled


def degree(G: nx.Graph) -> dict[Any, float]:
    """Compute degree centrality for nodes in the graph."""
    return nx.degree_centrality(G)


def weighted_degree(G: nx.Graph) -> dict[Any, float]:
    """Compute weighted node degree using the 'raw_weight' edge attribute."""
    return dict(G.degree(weight="raw_weight"))


def betweenness(G: nx.Graph) -> dict[Any, float]:
    """Compute betweenness centrality using 'raw_weight' as the edge weight."""
    return nx.betweenness_centrality(G, weight="raw_weight", normalized=True)


def closeness(G: nx.Graph) -> dict[Any, float]:
    """Compute closeness centrality for nodes in the graph."""
    return nx.closeness_centrality(G)


def eigenvector(G: nx.Graph) -> dict[Any, float]:
    """Compute eigenvector centrality (falls back to 0.0 for all nodes on failure)."""
    try:
        return nx.eigenvector_centrality(G, max_iter=1000, weight="raw_weight")
    except Exception:
        return {n: 0.0 for n in G.nodes()}


class NodeScaling(StrEnum):
    """Enum of node scaling strategies stored as node attributes."""

    NONE = "NODESCALING.NONE"
    DEGREE = "NODESCALING.DEGREE"
    WEIGHTED_DEGREE = "NODESCALING.WEIGHTED_DEGREE"
    BETWEENNESS = "NODESCALING.BETWEENNESS"
    CLOSENESS = "NODESCALING.CLOSENESS"
    EIGENVECTOR = "NODESCALING.EIGENVECTOR"


def add_node_sizes(G: nx.Graph, minimum: int = 10, maximum: int = 50) -> None:
    """Precompute node size variants and store them as node attributes."""
    mid = (minimum + maximum) / 2
    values = {node: mid for node in G.nodes}
    for node, value in values.items():
        G.nodes[node][NodeScaling.NONE] = value

    size_metrics = [
        (degree, NodeScaling.DEGREE),
        (weighted_degree, NodeScaling.WEIGHTED_DEGREE),
        (betweenness, NodeScaling.BETWEENNESS),
        (closeness, NodeScaling.CLOSENESS),
        (eigenvector, NodeScaling.EIGENVECTOR),
    ]

    for fun, key in size_metrics:
        values = fun(G)
        values = scale_to_range(values, minimum, maximum)
        for node, value in values.items():
            G.nodes[node][key] = value


def linear(values: dict[Any, int]) -> dict[Any, float]:
    """Apply a linear transform to integer weights (cast to float)."""
    return {edge: float(w) for edge, w in values.items()}


def sqrt(values: dict[Any, int]) -> dict[Any, float]:
    """Apply a square-root transform to integer weights."""
    return {edge: math.sqrt(float(w)) for edge, w in values.items()}


def log(values: dict[Any, int]) -> dict[Any, float]:
    """Apply a log(1 + w) transform to integer weights."""
    return {edge: math.log(1.0 + float(w)) for edge, w in values.items()}


class EdgeScaling(StrEnum):
    """Enum of edge scaling strategies stored as edge attributes."""

    NONE = "EDGESCALING.NONE"
    LINEAR = "EDGESCALING.LINEAR"
    SQRT = "EDGESCALING.SQRT"
    LOG = "EDGESCALING.LOG"


def add_edge_widths(
    G: nx.Graph,
    minimum: int = 10,
    maximum: int = 50,
) -> None:
    """Precompute edge width variants and store them as edge attributes."""
    base_values = {}
    for u, v, raw_weight in G.edges(data="raw_weight"):
        if raw_weight is not None:
            base_values[(u, v)] = raw_weight

    mid = (minimum + maximum) / 2

    for u, v in base_values:
        G.edges[u, v][EdgeScaling.NONE] = mid

    width_metrics = [
        (linear, EdgeScaling.LINEAR),
        (sqrt, EdgeScaling.SQRT),
        (log, EdgeScaling.LOG),
    ]

    for fun, key in width_metrics:
        values = fun(base_values)
        values = scale_to_range(values, minimum, maximum)
        for (u, v), width in values.items():
            G.edges[u, v][key] = width


class CommunityDetection(StrEnum):
    """Enum of community detection methods stored as node attributes."""

    NONE = "COMMUNITYDETECTION.NONE"
    LOUVAIN = "COMMUNITYDETECTION.LOUVAIN"


def constant_partition(G: nx.Graph, value: int = 0) -> dict[Any, int]:
    """Assign every node to the same community id (default: 0)."""
    return {n: value for n in G.nodes}


def louvain_partition(G: nx.Graph, weight: str = "raw_weight") -> dict[Any, int]:
    """Compute a Louvain community partition mapping node -> community id."""
    comms = nx.community.louvain_communities(G, weight=weight, seed=RANDOM_SEED)
    node2comm: dict[Any, int] = {}
    for i, c in enumerate(comms):
        for n in c:
            node2comm[n] = i
    return node2comm


def add_communities(G: nx.Graph, weight: str = "raw_weight") -> None:
    """Precompute community partitions and store them as node attributes."""
    methods = [
        (lambda g: constant_partition(g, 0), CommunityDetection.NONE),
        (lambda g: louvain_partition(g, weight), CommunityDetection.LOUVAIN),
    ]

    for func, key in methods:
        node2comm = func(G)
        for n, cid in node2comm.items():
            G.nodes[n][key] = int(cid)


def jaccard_similarity_temporal_network(
    temporal_network: dict[int, nx.Graph],
) -> dict[int, float]:
    """Compute year-to-year Jaccard similarity of node sets in a temporal network."""
    if not temporal_network:
        return {}

    years = list(temporal_network.keys())
    similarity: dict[int, float] = {years[0]: 0.0}
    prev_kws = set([name for name in temporal_network[years[0]].nodes])
    for year in years[1:]:
        cur_kws = set([name for name in temporal_network[year].nodes])
        union = prev_kws | cur_kws
        intersection = prev_kws & cur_kws
        similarity[year] = (len(intersection) / len(union)) if union else 0.0
        prev_kws = cur_kws

    return similarity


def node_birth_death(
    temporal_network: dict[int, nx.Graph],
) -> dict[int, dict[str, list[str]]]:
    """Compute per-year node births and deaths based on adjacent years in the network."""
    if not temporal_network:
        return {}

    years = list(temporal_network.keys())
    births_deaths: dict[int, dict[str, list[str]]] = {}

    for i, year in enumerate(years):
        G_current = temporal_network[year]
        current_nodes = set(G_current.nodes())

        births_deaths[year] = {}

        if i == 0:
            births_deaths[year]["births"] = list(current_nodes)
        else:
            prev_year = years[i - 1]
            prev_nodes = set(temporal_network[prev_year].nodes())
            births_deaths[year]["births"] = list(current_nodes - prev_nodes)

        if i == len(years) - 1:
            births_deaths[year]["deaths"] = []
        else:
            next_year = years[i + 1]
            next_nodes = set(temporal_network[next_year].nodes())
            births_deaths[year]["deaths"] = list(current_nodes - next_nodes)

    return births_deaths
