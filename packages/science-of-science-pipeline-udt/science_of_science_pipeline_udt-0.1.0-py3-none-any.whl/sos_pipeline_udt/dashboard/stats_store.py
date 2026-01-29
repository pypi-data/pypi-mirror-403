"""
dashboard.stats_store

Author: Duco Trompert
Course: Afstudeerproject bachelor Informatica
Thesis: Science of Science: An Integrated Pipeline for Tracing Conceptual Emergence and Evolution in Semantic Space
Date: 2026-01-23

Statistics and aggregation utilities used by the Dash dashboard.

This module provides helpers to:
- convert Publication objects into a pandas DataFrame,
- compute high-level KPIs and publication time series,
- compute keyword counts and "movers" (emerging/fading) over time,
- build simple temporal co-occurrence graphs and derive network metrics per year.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
from typing import Any, Iterable

import networkx as nx
import numpy as np
import pandas as pd

from sos_pipeline_udt.analysis.embeddings import keyword_token
from sos_pipeline_udt.analysis.networks import build_temporal_network
from sos_pipeline_udt.config import RANDOM_SEED


def _author_name(a: Any) -> str:
    """Convert an author representation into a clean display name string."""
    if a is None:
        return ""
    if isinstance(a, str):
        return a.strip()
    return str(getattr(a, "name", str(a))).strip()


def publications_to_df(publications: list[Any]) -> pd.DataFrame:
    """Convert a list of publication-like objects into a normalized DataFrame."""
    rows = []
    for i, pub in enumerate(publications):
        dt = getattr(pub, "publication_date", None)
        if dt is None:
            continue

        kws = []
        for kw in getattr(pub, "keywords", []) or []:
            tok = keyword_token(str(kw))
            if tok:
                kws.append(tok)

        authors_raw = getattr(pub, "authors", None)
        authors = []
        if authors_raw:
            authors = [_author_name(a) for a in authors_raw if _author_name(a)]

        rows.append(
            {
                "id": i,
                "date": pd.to_datetime(dt),
                "year": int(dt.year),
                "keywords": kws,
                "authors": authors,
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df["date_day"] = df["date"].dt.floor("D")
    return df


def compute_kpis(df: pd.DataFrame) -> dict[str, Any]:
    """Compute high-level KPI values (publication count, span, keyword/author totals)."""
    if df.empty:
        return {
            "total_pubs": 0,
            "time_span": "N/A",
            "n_keywords": 0,
            "n_authors": "N/A",
        }

    total = int(len(df))
    min_d, max_d = df["date"].min(), df["date"].max()
    time_span = f"{min_d.date()} -> {max_d.date()} ({(max_d - min_d).days} days)"

    kw_set = set()
    for kws in df["keywords"]:
        kw_set.update(kws or [])
    n_keywords = int(len(kw_set))

    authors_present = (
        df["authors"].apply(lambda x: isinstance(x, list) and len(x) > 0).any()
    )
    if authors_present:
        au_set = set()
        for aus in df["authors"]:
            au_set.update(aus or [])
        n_authors: Any = int(len(au_set))
    else:
        n_authors = "N/A"

    return {
        "total_pubs": total,
        "time_span": time_span,
        "n_keywords": n_keywords,
        "n_authors": n_authors,
    }


def pubs_timeseries_daily(df: pd.DataFrame) -> pd.DataFrame:
    """Compute a daily publication count time series with missing days filled as 0."""
    if df.empty:
        return pd.DataFrame({"date": [], "count": []})

    daily = (
        df.groupby("date_day")
        .size()
        .rename("count")
        .reset_index()
        .rename(columns={"date_day": "date"})
        .sort_values("date")
    )

    all_days = pd.date_range(daily["date"].min(), daily["date"].max(), freq="D")
    daily = (
        daily.set_index("date")
        .reindex(all_days)
        .fillna(0.0)
        .rename_axis("date")
        .reset_index()
    )
    daily["count"] = daily["count"].astype(int)
    return daily


def smooth_counts(daily: pd.DataFrame, window_days: int) -> pd.DataFrame:
    """Add a rolling-mean smoothed count column to a daily time series."""
    out = daily.copy()
    w = max(int(window_days), 1)
    out["smooth"] = out["count"].rolling(window=w, min_periods=1, center=True).mean()
    return out


def keyword_counts_by_year(df: pd.DataFrame) -> pd.DataFrame:
    """Compute keyword occurrence counts per year from the publications DataFrame."""
    if df.empty:
        return pd.DataFrame({"year": [], "keyword": [], "count": []})

    long = df[["year", "keywords"]].explode("keywords").dropna()
    long = long.rename(columns={"keywords": "keyword"})
    kw_year = long.groupby(["year", "keyword"]).size().rename("count").reset_index()
    return kw_year.sort_values(["year", "count"], ascending=[True, False])


def keyword_movers(
    kw_year: pd.DataFrame,
    end_year: int | None = None,
    lookback_years: int = 3,
    min_total: int = 5,
    top_n: int = 15,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (emerging, fading) keywords using a linear slope over a lookback window."""
    if kw_year.empty:
        cols = ["keyword", "total", "slope", "last", "prev"]
        empty = pd.DataFrame(columns=cols)
        return empty, empty

    years = sorted(kw_year["year"].unique().tolist())
    if end_year is None:
        end_year = years[-1]
    start_year = end_year - int(lookback_years)

    window = kw_year[
        (kw_year["year"] >= start_year) & (kw_year["year"] <= end_year)
    ].copy()
    if window.empty:
        cols = ["keyword", "total", "slope", "last", "prev"]
        empty = pd.DataFrame(columns=cols)
        return empty, empty

    pivot = window.pivot_table(
        index="keyword", columns="year", values="count", fill_value=0
    )
    pivot["total"] = pivot.sum(axis=1)

    pivot = pivot[pivot["total"] >= int(min_total)]
    if pivot.empty:
        cols = ["keyword", "total", "slope", "last", "prev"]
        empty = pd.DataFrame(columns=cols)
        return empty, empty

    year_cols = [c for c in pivot.columns if c != "total"]
    xs = np.array(sorted(year_cols), dtype=float)

    def slope(row) -> float:
        """Compute a simple linear trend slope for one keyword row."""
        ys = row[year_cols].values.astype(float)
        if ys.sum() == 0:
            return 0.0
        return float(np.polyfit(xs, ys, 1)[0])

    pivot["slope"] = pivot.apply(slope, axis=1)
    pivot["last"] = pivot.get(end_year, 0)
    pivot["prev"] = pivot.get(end_year - 1, 0)

    emerging = pivot.sort_values("slope", ascending=False).head(top_n).reset_index()
    fading = pivot.sort_values("slope", ascending=True).head(top_n).reset_index()

    keep = ["keyword", "total", "slope", "last", "prev"]
    return emerging[keep], fading[keep]


def build_temporal_cooccurrence(
    df: pd.DataFrame, min_weight: int = 2
) -> dict[int, nx.Graph]:
    """Build a simple co-occurrence graph per year from the publications DataFrame."""
    temporal: dict[int, nx.Graph] = {}
    if df.empty:
        return temporal

    for year in sorted(df["year"].unique().tolist()):
        sub = df[df["year"] == year]
        pair_counts = defaultdict(int)

        for kws in sub["keywords"]:
            if not kws:
                continue
            kws = sorted(set(kws))
            for i in range(len(kws)):
                for j in range(i + 1, len(kws)):
                    pair_counts[(kws[i], kws[j])] += 1

        G = nx.Graph(year=int(year))
        for (a, b), w in pair_counts.items():
            if w >= int(min_weight):
                G.add_edge(a, b, raw_weight=int(w))
        temporal[int(year)] = G

    return temporal


def compute_network_metrics_over_time(temporal: dict[int, nx.Graph]) -> pd.DataFrame:
    """Compute per-year network metrics (size, structure, similarity, churn) over time."""

    def edge_set(G: nx.Graph) -> set[tuple[str, str]]:
        """Return a canonical set of undirected edges as sorted (u, v) tuples."""
        return {tuple(sorted((u, v))) for u, v in G.edges()}

    rows: list[dict[str, Any]] = []
    prev_edges: set[tuple[str, str]] | None = None
    prev_nodes: set[str] | None = None

    for year in sorted(temporal.keys()):
        G = temporal[year]
        n = G.number_of_nodes()
        m = G.number_of_edges()

        nodes_now = set(G.nodes())
        edges_now = edge_set(G)

        if prev_edges is None:
            edge_jacc = 0.0
        else:
            union = len(edges_now | prev_edges)
            inter = len(edges_now & prev_edges)
            edge_jacc = (inter / union) if union else 1.0

        if prev_nodes is None:
            node_jacc = 0.0
        else:
            union_n = len(nodes_now | prev_nodes)
            inter_n = len(nodes_now & prev_nodes)
            node_jacc = (inter_n / union_n) if union_n else 1.0

        births = len(nodes_now - prev_nodes) if prev_nodes is not None else 0
        deaths = len(prev_nodes - nodes_now) if prev_nodes is not None else 0

        density = float(nx.density(G)) if n > 1 else 0.0
        avg_degree = float((2 * m / n)) if n > 0 else 0.0

        avg_clustering = (
            float(nx.average_clustering(G, weight="raw_weight")) if n > 1 else 0.0
        )

        modularity = 0.0
        n_communities = 0
        if m > 0 and n > 1:
            comms = nx.community.louvain_communities(
                G, weight="raw_weight", seed=RANDOM_SEED
            )
            n_communities = len(comms)
            modularity = float(
                nx.algorithms.community.quality.modularity(
                    G, comms, weight="raw_weight"
                )
            )

        rows.append(
            {
                "year": int(year),
                "nodes": int(n),
                "edges": int(m),
                "density": density,
                "avg_degree": avg_degree,
                "avg_clustering": avg_clustering,
                "modularity": modularity,
                "n_communities": int(n_communities),
                "jaccard_prev": float(edge_jacc),
                "edge_jaccard_prev": float(edge_jacc),
                "node_jaccard_prev": float(node_jacc),
                "births": int(births),
                "deaths": int(deaths),
            }
        )

        prev_edges = edges_now
        prev_nodes = nodes_now

    return pd.DataFrame(rows).sort_values("year")
