"""
dashboard.graph_store

Author: Duco Trompert
Course: Afstudeerproject bachelor Informatica
Thesis: Science of Science: An Integrated Pipeline for Tracing Conceptual Emergence and Evolution in Semantic Space
Date: 2026-01-23

Graph and element caching layer for the Dash dashboard.

This module:
- optionally precomputes commonly used networks (overall + yearly),
- provides get_graph() to retrieve (or build) a specific network variant,
- provides get_elements() to convert graphs into Cytoscape elements with caching.
"""

from __future__ import annotations

from typing import Any, Dict, List

import networkx as nx

from sos_pipeline_udt.analysis.embeddings import Word2VecConfig
from sos_pipeline_udt.analysis.networks import llm_classify_keyword
from sos_pipeline_udt.config import (
    DEFAULT_MIN_KW_FREQ,
    DEFAULT_MIN_VALUE,
    DEFAULT_SIM_THRESHOLD,
    DEFAULT_TOP_K,
    PRECOMPUTE_LIGHT_NETWORKS,
    PRECOMPUTE_SEMANTIC,
    W2V_PARAMS,
)

W2V_CONFIG = Word2VecConfig(**W2V_PARAMS.__dict__)
from sos_pipeline_udt.dashboard.data_store import corpus
from sos_pipeline_udt.dashboard.vis_elements import nx_to_cytoscape_elements

PRECOMP: Dict[str, Any] = {}


def _error_graph(msg: str) -> nx.Graph:
    """Create a small graph containing a single ERROR node for display in the UI."""
    G = nx.Graph()
    G.add_node(f"ERROR: {msg}")
    return G


if PRECOMPUTE_LIGHT_NETWORKS:
    PRECOMP["coocc_overall"] = corpus.cooccurrence_network(min_value=DEFAULT_MIN_VALUE)
    PRECOMP["coocc_yearly"] = corpus.temporal_network(min_value=DEFAULT_MIN_VALUE)
    try:
        PRECOMP["cm_overall"] = corpus.concept_method_network(
            min_value=DEFAULT_MIN_VALUE
        )
        PRECOMP["cm_yearly"] = corpus.temporal_concept_method_network(
            min_value=DEFAULT_MIN_VALUE
        )
    except Exception as e:
        PRECOMP["cm_overall"] = _error_graph(str(e))
        PRECOMP["cm_yearly"] = {}

if PRECOMPUTE_SEMANTIC:
    PRECOMP["sem_overall"] = corpus.semantic_similarity_network(
        w2v_config=W2V_CONFIG,
        min_keyword_freq=DEFAULT_MIN_KW_FREQ,
        similarity_threshold=DEFAULT_SIM_THRESHOLD,
        top_k=DEFAULT_TOP_K,
    )
    PRECOMP["sem_yearly"] = corpus.temporal_semantic_similarity_network(
        w2v_config=W2V_CONFIG,
        min_keyword_freq=DEFAULT_MIN_KW_FREQ,
        similarity_threshold=DEFAULT_SIM_THRESHOLD,
        top_k=DEFAULT_TOP_K,
    )


_ELEMENTS_CACHE: Dict[str, List[dict]] = {}


def _key(*parts: Any) -> str:
    """Build a stable cache key from a list of cache-relevant parts."""
    return "|".join(map(str, parts))


def get_graph(
    network_kind: str, year: int | None, *, min_value: int, sim_threshold: float
) -> nx.Graph:
    """Return a NetworkX graph for the requested network type and parameters."""
    if network_kind == "cooccurrence_overall":
        if PRECOMPUTE_LIGHT_NETWORKS and min_value == DEFAULT_MIN_VALUE:
            return PRECOMP["coocc_overall"]
        return corpus.cooccurrence_network(min_value=min_value)

    if network_kind == "concept_method_overall":
        if PRECOMPUTE_LIGHT_NETWORKS and min_value == DEFAULT_MIN_VALUE:
            return PRECOMP["cm_overall"]
        try:
            return corpus.concept_method_network(min_value=min_value)
        except Exception as e:
            return _error_graph(str(e))

    if network_kind == "semantic_overall":
        if PRECOMPUTE_SEMANTIC and sim_threshold == DEFAULT_SIM_THRESHOLD:
            return PRECOMP["sem_overall"]
        return corpus.semantic_similarity_network(
            w2v_config=W2V_CONFIG,
            min_keyword_freq=DEFAULT_MIN_KW_FREQ,
            similarity_threshold=sim_threshold,
            top_k=DEFAULT_TOP_K,
        )

    if network_kind == "cooccurrence_yearly":
        temporal = (
            PRECOMP.get("coocc_yearly")
            if (PRECOMPUTE_LIGHT_NETWORKS and min_value == DEFAULT_MIN_VALUE)
            else corpus.temporal_network(min_value=min_value)
        )
        year = int(year) if year is not None else max(temporal.keys())
        return temporal.get(year, nx.Graph())

    if network_kind == "concept_method_yearly":
        temporal = (
            PRECOMP.get("cm_yearly")
            if (PRECOMPUTE_LIGHT_NETWORKS and min_value == DEFAULT_MIN_VALUE)
            else corpus.temporal_concept_method_network(min_value=min_value)
        )
        if not temporal:
            return _error_graph(
                "Concept-method labels missing. Run classification/keyword_classification.py first."
            )
        year = int(year) if year is not None else max(temporal.keys())
        return temporal.get(year, nx.Graph())

    if network_kind == "semantic_yearly":
        temporal = (
            PRECOMP.get("sem_yearly")
            if (PRECOMPUTE_SEMANTIC and sim_threshold == DEFAULT_SIM_THRESHOLD)
            else corpus.temporal_semantic_similarity_network(
                w2v_config=W2V_CONFIG,
                min_keyword_freq=DEFAULT_MIN_KW_FREQ,
                similarity_threshold=sim_threshold,
                top_k=DEFAULT_TOP_K,
            )
        )
        year = int(year) if year is not None else max(temporal.keys())
        return temporal.get(year, nx.Graph())

    return nx.Graph()


def get_elements(
    network_kind: str,
    year: int | None,
    *,
    min_value: int,
    sim_threshold: float,
    node_scaling: str,
    edge_scaling: str,
    community: str,
) -> List[dict]:
    """Return Cytoscape elements for the requested graph variant (with caching)."""
    cache_key = _key(
        network_kind,
        year,
        min_value,
        sim_threshold,
        node_scaling,
        edge_scaling,
        community,
    )
    if cache_key in _ELEMENTS_CACHE:
        return _ELEMENTS_CACHE[cache_key]

    G = get_graph(network_kind, year, min_value=min_value, sim_threshold=sim_threshold)
    elements = nx_to_cytoscape_elements(
        G,
        node_scaling=node_scaling,
        edge_scaling=edge_scaling,
        community_attr=community,
    )
    _ELEMENTS_CACHE[cache_key] = elements
    return elements
