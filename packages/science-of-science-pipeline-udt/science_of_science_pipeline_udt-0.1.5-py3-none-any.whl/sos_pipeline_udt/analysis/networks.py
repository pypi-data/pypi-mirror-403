"""
analysis.networks

Author: Duco Trompert
Course: Afstudeerproject bachelor Informatica
Thesis: Science of Science: An Integrated Pipeline for Tracing Conceptual Emergence and Evolution in Semantic Space
Date: 2026-01-23

Network construction utilities for the thesis project.

This module builds several NetworkX graph types from publication metadata:
- keyword co-occurrence networks (static and temporal),
- concept-method bipartite networks (static and temporal),
- semantic similarity networks based on Word2Vec (static and temporal).
"""

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Callable, Dict, List, Literal

import networkx as nx
from gensim.models import Word2Vec

from sos_pipeline_udt.analysis.embeddings import Word2VecConfig, keyword_frequencies, train_word2vec
from sos_pipeline_udt.analysis.metrics import (
    add_communities,
    add_edge_widths,
    add_node_sizes,
    jaccard_similarity_temporal_network,
    node_birth_death,
)
from sos_pipeline_udt.config import KEYWORD_LABELS_PATH
from sos_pipeline_udt.data.publication import Publication

KeywordKind = Literal["concept", "method"]

try:
    _LABELS: dict[str, str] = json.loads(
        KEYWORD_LABELS_PATH.read_text(encoding="utf-8")
    )
except FileNotFoundError:
    _LABELS = {}


def llm_classify_keyword(keyword: str) -> KeywordKind | None:
    """
    Classify a keyword as 'concept', 'method', or None using precomputed LLM labels.

    Supports two formats for entries in the labels file:
    1) single label per keyword (legacy), or
    2) per-model labels (ensemble), resolved by strict majority vote. (current implementation)
    """
    if not _LABELS:
        raise RuntimeError(
            "classification/keyword_labels.json not found, run keyword_classification.py first."
        )

    k = keyword.strip()
    if not k:
        return None

    raw = _LABELS.get(k)
    if raw is None:
        return None

    if isinstance(raw, str):
        label = raw.strip().lower()
        if label == "concept":
            return "concept"
        if label == "method":
            return "method"
        return None

    if isinstance(raw, dict):
        labels = [str(v).strip().lower() for v in raw.values() if v is not None]
        if not labels:
            return None

        counts = Counter(labels)
        winner, votes = counts.most_common(1)[0]
        total = len(labels)

        if votes > total / 2:
            if winner == "concept":
                return "concept"
            if winner == "method":
                return "method"
            return None
        return None
    return None


def bucket_publications_by_year(
    publications: List[Publication],
) -> Dict[int, List[Publication]]:
    """Group publications into a mapping of {year -> [Publication, ...]}."""
    buckets: Dict[int, List[Publication]] = defaultdict(list)
    for pub in publications:
        year = pub.publication_date.year
        buckets[year].append(pub)

    return dict(sorted(buckets.items()))


def keywords_cooccurrence(
    publications: list[Publication],
) -> dict[tuple[str, str], int]:
    """
    Compute co-occurrence counts for keyword pairs across publications.

    Two keywords co-occur if they both appear in the same publication. Each
    publication contributes at most +1 to a given keyword pair.
    """
    counts: dict[tuple[str, str], int] = {}

    for pub in publications:
        kws = list(pub.keywords)
        kws = sorted(set(pub.keywords))
        n = len(kws)
        for i in range(n):
            for j in range(i + 1, n):
                k1 = kws[i]
                k2 = kws[j]
                if k1 == k2:
                    continue
                pair = (k1, k2) if k1 < k2 else (k2, k1)
                counts[pair] = counts.get(pair, 0) + 1

    return counts


def build_cooccurrence_network(
    publications: list[Publication],
    min_value: int = 0,
) -> nx.Graph:
    """
    Build a keyword co-occurrence network from a list of publications.

    Nodes are keywords and edges connect keywords that co-occur within at least one
    publication. Edge attribute 'raw_weight' stores the co-occurrence count.

    Edges with raw_weight < min_value are dropped. Node sizes, edge widths, and
    community labels are precomputed.
    """
    if min_value < 0:
        min_value = 0

    G = nx.Graph()

    if min_value == 0:
        all_keywords: set[str] = set()
        for pub in publications:
            all_keywords.update(pub.keywords)
        G.add_nodes_from(all_keywords)

    counts = keywords_cooccurrence(publications)
    for (k1, k2), v in counts.items():
        if v >= min_value:
            G.add_edge(k1, k2, raw_weight=v)

    if not G.nodes:
        return G

    add_node_sizes(G, minimum=10, maximum=50)
    add_edge_widths(G, minimum=1, maximum=20)
    add_communities(G)

    return G


def build_temporal_network(
    publications: list[Publication],
    min_value: int = 0,
) -> dict[int, nx.Graph]:
    """
    Build a co-occurrence network per publication year.

    Each yearly graph is annotated with:
    - G.graph["year"]
    - G.graph["jaccard_prev"] (Jaccard similarity to the previous year)
    - G.graph["births"]       (nodes appearing in this year)
    - G.graph["deaths"]       (nodes disappearing after this year)
    """
    buckets = bucket_publications_by_year(publications)

    temporal_network: dict[int, nx.Graph] = {}
    for year, bucket in buckets.items():
        temporal_network[year] = build_cooccurrence_network(
            publications=bucket,
            min_value=min_value,
        )

    temporal_network = dict(sorted(temporal_network.items()))

    jacc = jaccard_similarity_temporal_network(temporal_network)
    births_deaths = node_birth_death(temporal_network)

    for year, G in temporal_network.items():
        G.graph["year"] = year
        G.graph["jaccard_prev"] = jacc.get(year, 0.0)

        bd = births_deaths.get(year, {"births": [], "deaths": []})
        G.graph["births"] = bd.get("births", [])
        G.graph["deaths"] = bd.get("deaths", [])

    return temporal_network


def build_concept_method_bipartite(
    publications: list[Publication],
    min_value: int = 0,
    classifier: Callable[[str], KeywordKind | None] = llm_classify_keyword,
) -> nx.Graph:
    """
    Build a bipartite network linking concept keywords to method keywords.

    Nodes are classified into two sets ('concept' and 'method') using the provided
    classifier. Edges connect concept <-> method when both appear in the same
    publication, with 'raw_weight' counting co-occurrences.

    Edges with raw_weight < min_value are dropped and isolated nodes are removed.
    Node sizes, edge widths, and community labels are precomputed.
    """
    G = nx.Graph()

    for pub in publications:
        concepts: set[str] = set()
        methods: set[str] = set()

        for kw in pub.keywords:
            kind = classifier(kw)
            if kind == "concept":
                concepts.add(kw)
            elif kind == "method":
                methods.add(kw)

        for c in concepts:
            if c not in G:
                G.add_node(c, node_type="concept", bipartite=0)
            for m in methods:
                if m not in G:
                    G.add_node(m, node_type="method", bipartite=1)

                if G.has_edge(c, m):
                    G[c][m]["raw_weight"] += 1
                else:
                    G.add_edge(c, m, raw_weight=1)

    if min_value > 0:
        to_remove = [
            (u, v)
            for u, v, data in G.edges(data=True)
            if data.get("raw_weight", 0) < min_value
        ]
        G.remove_edges_from(to_remove)

    isolates = list(nx.isolates(G))
    if isolates:
        G.remove_nodes_from(isolates)

    if not G.nodes:
        return G

    add_node_sizes(G, minimum=10, maximum=50)
    add_edge_widths(G, minimum=1, maximum=20)
    add_communities(G)

    return G


def build_temporal_concept_method_bipartite(
    publications: list[Publication],
    min_value: int = 0,
    classifier: Callable[[str], KeywordKind | None] = llm_classify_keyword,
) -> dict[int, nx.Graph]:
    """
    Build a concept-method bipartite network per publication year.

    Each yearly graph receives the same temporal annotations as build_temporal_network.
    """
    buckets = bucket_publications_by_year(publications)

    temporal_network: dict[int, nx.Graph] = {}
    for year, bucket in buckets.items():
        temporal_network[year] = build_concept_method_bipartite(
            publications=bucket,
            min_value=min_value,
            classifier=classifier,
        )

    temporal_network = dict(sorted(temporal_network.items()))

    jacc = jaccard_similarity_temporal_network(temporal_network)
    births_deaths = node_birth_death(temporal_network)

    for year, G in temporal_network.items():
        G.graph["year"] = year
        G.graph["jaccard_prev"] = jacc.get(year, 0.0)

        bd = births_deaths.get(year, {"births": [], "deaths": []})
        G.graph["births"] = bd.get("births", [])
        G.graph["deaths"] = bd.get("deaths", [])

    return temporal_network


def build_semantic_similarity_network(
    publications: list[Publication],
    w2v_config: Word2VecConfig,
    min_keyword_freq: int = 5,
    similarity_threshold: float = 0.5,
    top_k: int | None = None,
    model: Word2Vec | None = None,
) -> nx.Graph:
    """
    Build a semantic similarity network between keywords using a Word2Vec model.

    Candidate keywords are filtered by minimum frequency and presence in the model
    vocabulary. Edges are added when cosine similarity >= similarity_threshold,
    stored in 'raw_weight'. If top_k is provided, each node only connects to its
    top-k most similar neighbors above the threshold.
    """
    if model is None:
        model = train_word2vec(
            publications=publications,
            config=w2v_config,
        )

    freqs: dict[str, int] = keyword_frequencies(publications)

    candidates = [
        kw
        for kw, count in freqs.items()
        if count >= min_keyword_freq and kw in model.wv
    ]

    G = nx.Graph()
    for kw in candidates:
        G.add_node(kw, frequency=freqs[kw])

    if not candidates:
        return G

    if top_k is None:
        for i, kw1 in enumerate(candidates):
            for kw2 in candidates[i + 1 :]:
                sim = float(model.wv.similarity(kw1, kw2))
                if sim >= similarity_threshold:
                    G.add_edge(kw1, kw2, raw_weight=sim)
    else:
        edge_sims: dict[tuple[str, str], float] = {}

        for kw1 in candidates:
            sims: list[tuple[str, float]] = []

            for kw2 in candidates:
                if kw1 == kw2:
                    continue
                sim = float(model.wv.similarity(kw1, kw2))
                if sim >= similarity_threshold:
                    sims.append((kw2, sim))

            sims.sort(key=lambda x: x[1], reverse=True)
            for kw2, sim in sims[:top_k]:
                u, v = sorted((kw1, kw2))
                current = edge_sims.get((u, v))
                if current is None or sim > current:
                    edge_sims[(u, v)] = sim

        for (u, v), sim in edge_sims.items():
            G.add_edge(u, v, raw_weight=sim)

    isolates = list(nx.isolates(G))
    G.remove_nodes_from(isolates)

    if not G.nodes:
        return G

    add_node_sizes(G, minimum=10, maximum=50)
    add_edge_widths(G, minimum=1, maximum=20)
    add_communities(G)

    return G


def build_temporal_semantic_similarity_network(
    publications: list[Publication],
    w2v_config: Word2VecConfig,
    min_keyword_freq: int = 5,
    similarity_threshold: float = 0.5,
    top_k: int | None = None,
    models_by_year: dict[int, Word2Vec] | None = None,
) -> dict[int, nx.Graph]:
    """
    Build a semantic similarity network per publication year.

    If models_by_year is provided, the corresponding Word2Vec model is reused per year.
    Each yearly graph receives the same temporal annotations as build_temporal_network.
    """
    buckets = bucket_publications_by_year(publications)

    temporal_network: dict[int, nx.Graph] = {}

    for year, bucket in buckets.items():
        G_year = build_semantic_similarity_network(
            publications=bucket,
            w2v_config=w2v_config,
            min_keyword_freq=min_keyword_freq,
            similarity_threshold=similarity_threshold,
            top_k=top_k,
            model=(models_by_year.get(year) if models_by_year else None),
        )

        temporal_network[year] = G_year

    temporal_network = dict(sorted(temporal_network.items()))

    jacc = jaccard_similarity_temporal_network(temporal_network)
    births_deaths = node_birth_death(temporal_network)

    for year, G in temporal_network.items():
        G.graph["year"] = year
        G.graph["jaccard_prev"] = jacc.get(year, 0.0)

        bd = births_deaths.get(year, {"births": [], "deaths": []})
        G.graph["births"] = bd.get("births", [])
        G.graph["deaths"] = bd.get("deaths", [])

    return temporal_network
