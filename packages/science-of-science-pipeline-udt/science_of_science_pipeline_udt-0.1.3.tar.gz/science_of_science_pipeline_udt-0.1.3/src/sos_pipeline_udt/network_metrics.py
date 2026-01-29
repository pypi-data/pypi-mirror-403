"""
network_metrics

Author: Duco Trompert
Course: Afstudeerproject bachelor Informatica
Thesis: Science of Science: An Integrated Pipeline for Tracing Conceptual Emergence and Evolution in Semantic Space
Date: 2026-01-23

Standalone export script that only writes a single CSV:
- network_metrics_by_year_min5.csv

The exported metrics mirror the dashboard "Network evolution over time" computation
for a temporal keyword co-occurrence network with min edge weight = 5.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from sos_pipeline_udt.config import CONCEPT, USE_CACHE
from sos_pipeline_udt.dashboard.stats_store import build_temporal_cooccurrence, compute_network_metrics_over_time, publications_to_df
from sos_pipeline_udt.data.publication_corpus import PublicationCorpus

# Output location
OUTPUT_DIR: Path = Path("overleaf_files/network_metrics")

# Only exports min_value=5
MIN_VALUE: int = 5

# Cutoff for consistency with thesis data
MAX_YEAR: int = 2025


def _ensure_dir(p: Path) -> None:
    """Create the output directory if it does not exist."""
    p.mkdir(parents=True, exist_ok=True)


def export_network_metrics_by_year_min5(df: pd.DataFrame, out_dir: Path) -> Path:
    """Compute and write temporal network metrics for min edge weight = 5."""
    _ensure_dir(out_dir)

    temporal = build_temporal_cooccurrence(df, min_weight=MIN_VALUE)
    metrics = compute_network_metrics_over_time(temporal).copy()
    metrics.insert(0, "min_value", MIN_VALUE)

    out_path = out_dir / f"network_metrics_by_year_min{MIN_VALUE}.csv"
    metrics.to_csv(out_path, index=False)
    return out_path


def main() -> None:
    """Build the corpus, compute metrics, and write the single output CSV."""
    corpus = PublicationCorpus(CONCEPT, use_cache=USE_CACHE)
    df = publications_to_df(corpus.data)

    if not df.empty:
        df = df[df["year"] <= MAX_YEAR].copy()

    out_path = export_network_metrics_by_year_min5(df, OUTPUT_DIR)
    print(f"Wrote: {out_path.resolve()}")


if __name__ == "__main__":
    main()
