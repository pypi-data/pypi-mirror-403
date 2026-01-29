"""
analysis.embeddings.

Author: Duco Trompert
Course: Afstudeerproject bachelor Informatica
Thesis: Science of Science: An Integrated Pipeline for Tracing Conceptual Emergence and Evolution in Semantic Space
Date: 2026-01-23

Utilities for training a Word2Vec model on publication metadata.
Includes tokenization helpers, sentence construction, model training,
and keyword frequency counting.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from gensim.models import Word2Vec
from gensim.parsing.preprocessing import STOPWORDS
from gensim.utils import simple_preprocess

from sos_pipeline_udt.data.publication import Publication


@dataclass(frozen=True)
class Word2VecConfig:
    """Configuration parameters for training a gensim Word2Vec model."""

    vector_size: int = 100
    """Embedding dimensionality."""

    window: int = 5
    """Maximum distance between the current and predicted word."""

    min_count: int = 2
    """Ignore words with total frequency lower than this threshold."""

    workers: int = 1
    """Number of worker threads used in training."""

    sg: int = 1
    """Training algorithm: 1 for skip-gram; 0 for CBOW."""

    seed: int | None = None
    """Random seed for reproducibility (if set)."""

    epochs: int = 50
    """Number of training epochs."""


def tokenize(text: str) -> list[str]:
    """Tokenize and normalize free text into a list of non-stopword tokens."""
    if not text:
        return []
    tokens = simple_preprocess(text, deacc=True, min_len=2)
    tokens = [t for t in tokens if t not in STOPWORDS]
    return tokens


def keyword_token(kw: str) -> str | None:
    """Normalize a keyword string to a single token (lowercase, underscores)."""
    kw = kw.strip()
    if not kw:
        return None
    return kw.lower().replace(" ", "_")


def make_sentences(publications: List[Publication]) -> list[list[str]]:
    """Build Word2Vec training sentences from keywords, titles, and abstracts."""
    sentences: list[list[str]] = []

    for pub in publications:
        keyword_tokens = [
            t for t in (keyword_token(kw) for kw in pub.keywords) if t is not None
        ]
        title_tokens = tokenize(pub.title)
        abstract_tokens = tokenize(pub.abstract)
        sentence = keyword_tokens + title_tokens + abstract_tokens
        sentences.append(sentence)

    return sentences


def train_word2vec(publications: List[Publication], config: Word2VecConfig) -> Word2Vec:
    """Train and return a Word2Vec model from a list of publications."""
    sentences = make_sentences(publications=publications)

    if not sentences:
        raise ValueError("No training sentences found. Check your publications.")

    model = Word2Vec(
        sentences=sentences,
        vector_size=config.vector_size,
        window=config.window,
        min_count=config.min_count,
        workers=config.workers,
        sg=config.sg,
        seed=config.seed,
        epochs=config.epochs,
    )

    return model


def keyword_frequencies(publications: List[Publication]) -> dict[str, int]:
    """Count normalized keyword token frequencies across a set of publications."""
    freqs: dict[str, int] = {}
    for pub in publications:
        for kw in pub.keywords:
            token = keyword_token(kw)
            if token is None:
                continue
            freqs[token] = freqs.get(token, 0) + 1
    return freqs
