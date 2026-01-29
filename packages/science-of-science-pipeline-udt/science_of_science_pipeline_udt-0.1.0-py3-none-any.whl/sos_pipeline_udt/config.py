"""
config

Author: Duco Trompert
Course: Afstudeerproject bachelor Informatica
Thesis: Science of Science: An Integrated Pipeline for Tracing Conceptual Emergence and Evolution in Semantic Space
Date: 2026-01-23

Project-wide configuration constants for the thesis pipeline and dashboard.

This module defines:
- repository paths and cache locations,
- the core concept query and reproducibility settings,
- OpenAlex retrieval parameters,
- default thresholds for networks and embeddings,
- Word2Vec training parameters,
- keyword classification (Ollama) settings,
- dashboard rendering and animation constants.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final, Optional

# ----- Repo paths -----
REPO_ROOT: Final[Path] = Path(__file__).resolve().parent

CACHE_DIR: Final[Path] = REPO_ROOT / "cache"
W2V_CACHE_DIR: Final[Path] = CACHE_DIR / "w2v"

CLASSIFICATION_DIR: Final[Path] = REPO_ROOT / "classification"
KEYWORD_LABELS_PATH: Final[Path] = CLASSIFICATION_DIR / "keyword_labels.json"


# ----- Core concept and caching policy -----
CONCEPT: Final[str] = "Urban Digital Twin"

# Reproducibility default: prefer cache. Set False only when you intentionally want a live refresh.
USE_CACHE: Final[bool] = True


# ----- Global reproducibility seed -----
RANDOM_SEED: Final[int] = 42


# ----- OpenAlex retrieval (dataset-defining parameters) -----
OPENALEX_WORKS_ENDPOINT: Final[str] = "https://api.openalex.org/works"

# Your current query behavior: phrase search against title_and_abstract.
OPENALEX_FILTER_TEMPLATE: Final[str] = 'title_and_abstract.search:"{concept}"'

# Pagination/cursor settings (these define what you retrieve).
OPENALEX_PER_PAGE: Final[int] = 200
OPENALEX_CURSOR_START: Final[str] = "*"

# Network timeout; must be long enough for cursor pagination.
OPENALEX_TIMEOUT_S: Final[int] = 60

# OpenAlex asks for a mailto for polite pool usage. Keep it explicit and consistent.
OPENALEX_MAILTO: Final[str] = "duco@trompert.net"


# ----- Default network / analysis thresholds used by dashboard controls -----
DEFAULT_MIN_VALUE: Final[int] = 5  # min co-occurrence count threshold
DEFAULT_SIM_THRESHOLD: Final[float] = 0.9  # semantic similarity edge threshold
DEFAULT_MIN_KW_FREQ: Final[int] = (
    5  # min keyword frequency for embeddings/semantic networks
)
DEFAULT_TOP_K: Final[Optional[int]] = None  # e.g. 50 if you want to cap keywords


# ----- Word2Vec configuration -----
@dataclass(frozen=True)
class Word2VecParams:
    vector_size: int = 100
    window: int = 5
    min_count: int = 2
    workers: int = 1
    sg: int = 1
    seed: int = RANDOM_SEED
    epochs: int = 50


W2V_PARAMS: Final[Word2VecParams] = Word2VecParams()


#  -----Keyword classification (5 local LLMs via Ollama) -----
OLLAMA_GENERATE_URL: Final[str] = "http://localhost:11434/api/generate"

# Models used in the thesis pipeline (exact naming matters for reproducibility).
LLM_MODELS: Final[list[str]] = ["llama3", "mistral", "gemma2", "phi3", "qwen2.5"]

# Deterministic generation settings (methodology-critical).
LLM_TEMPERATURE: Final[float] = 0.0

# Output length control used by your scripts (keep explicit).
LLM_NUM_PREDICT_SINGLE: Final[int] = 32
LLM_NUM_PREDICT_BATCH: Final[int] = 256

# HTTP timeouts used by classification scripts.
OLLAMA_TIMEOUT_SINGLE_S: Final[int] = 30
OLLAMA_TIMEOUT_BATCH_S: Final[int] = 90

# Classification script checkpointing behavior.
CLASSIFY_BATCH_SIZE: Final[int] = 10
CLASSIFY_SAVE_EVERY: Final[int] = 1

# Voting rule: strict majority (>= 3 of 5).
LLM_VOTE_MAJORITY: Final[int] = 3


#  -----Dashboard rendering / UI constants -----
EDGE_WIDTH_MIN: Final[float] = 0.5
EDGE_WIDTH_MAX: Final[float] = 5.0

# Startup precompute behavior (affects perceived performance and startup time).
PRECOMPUTE_LIGHT_NETWORKS: Final[bool] = True
PRECOMPUTE_SEMANTIC: Final[bool] = True

# Temporal animation + layout stability (affects UX + visual reproducibility of movement).
ANIM_INTERVAL_MS: Final[int] = 60
FADE_STEPS: Final[int] = 10
REVEAL_STEPS: Final[int] = 8
MOVE_STEPS: Final[int] = 26
BIRTH_STEPS: Final[int] = REVEAL_STEPS

SPRING_SEED: Final[int] = RANDOM_SEED
SPRING_ITER: Final[int] = 80
POS_SCALE: Final[float] = 150.0
MAX_MOVE_PER_TRANSITION: Final[float] = 450.0

# Bipartite layout spacing (concept-method networks)
BIPARTITE_GAP: Final[float] = 42.0
