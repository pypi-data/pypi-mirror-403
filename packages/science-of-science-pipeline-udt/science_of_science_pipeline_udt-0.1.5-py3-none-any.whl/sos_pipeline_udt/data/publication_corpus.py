"""
data.publication_corpus

Author: Duco Trompert
Course: Afstudeerproject bachelor Informatica
Thesis: Science of Science: An Integrated Pipeline for Tracing Conceptual Emergence and Evolution in Semantic Space
Date: 2026-01-23

Corpus container for Publication objects tied to a single concept.

Handles:
- fetching publications from OpenAlex (or loading from cache),
- writing cached corpus + metadata to disk,
- building different NetworkX networks derived from the corpus,
- training/caching (optionally persisting) Word2Vec models used for semantic networks.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from threading import Lock

import networkx as nx
from gensim.models import Word2Vec

from sos_pipeline_udt.analysis.embeddings import Word2VecConfig, train_word2vec
from sos_pipeline_udt.analysis.networks import (
    build_concept_method_bipartite,
    build_cooccurrence_network,
    build_semantic_similarity_network,
    build_temporal_concept_method_bipartite,
    build_temporal_network,
    build_temporal_semantic_similarity_network,
)
from sos_pipeline_udt.config import (
    CACHE_DIR,
    OPENALEX_CURSOR_START,
    OPENALEX_FILTER_TEMPLATE,
    OPENALEX_MAILTO,
    OPENALEX_PER_PAGE,
    OPENALEX_WORKS_ENDPOINT,
    W2V_CACHE_DIR,
)
from sos_pipeline_udt.data.collectors import collect_openalex_data
from sos_pipeline_udt.data.publication import Publication


class PublicationCorpus:
    """
    A collection of Publication objects associated with a specific concept.

    If use_cache is True and the cache file exists, data is loaded from that file.
    Otherwise, data is fetched live from OpenAlex and written to the cache.
    """

    def __init__(self, concept: str, use_cache: bool = True) -> None:
        """Create a corpus for the given concept, loading from cache or fetching live."""
        self._concept: str = concept

        self._safe_concept = concept.lower().strip().replace(" ", "_")
        self._cache_path: Path = CACHE_DIR / f"{self._safe_concept}.json"

        self._w2v_models: dict[tuple[int | None, Word2VecConfig], Word2Vec] = {}
        self._w2v_lock: Lock = Lock()
        self._w2v_cache_dir: Path = W2V_CACHE_DIR / self._safe_concept

        if use_cache and self._cache_path.exists():
            raw = self._cache_path.read_text(encoding="utf-8")
            records = json.loads(raw)
            self._data: list[Publication] = [Publication.from_dict(r) for r in records]
        else:
            publications = collect_openalex_data(concept)
            self._data = publications

            self._cache_path.parent.mkdir(parents=True, exist_ok=True)
            records = [p.to_dict() for p in publications]
            self._cache_path.write_text(
                json.dumps(records, indent=2),
                encoding="utf-8",
            )

        pubs_per_year = self.years()
        min_year = min(pubs_per_year) if pubs_per_year else None
        max_year = max(pubs_per_year) if pubs_per_year else None

        kws_occurrence = self.keywords_occurrence()
        top_keywords = sorted(
            kws_occurrence.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:20]

        self._meta_data = {
            "concept": concept,
            "description": (
                f"OpenAlex works where '{concept}' appears in title or abstract"
            ),
            "data_source": {
                "name": "OpenAlex",
                "endpoint": OPENALEX_WORKS_ENDPOINT,
            },
            "query": {
                "filter": OPENALEX_FILTER_TEMPLATE.format(concept=concept),
                "per-page": OPENALEX_PER_PAGE,
                "cursor_start": OPENALEX_CURSOR_START,
                "mailto": OPENALEX_MAILTO,
            },
            "retrieval": {
                "date": date.today().isoformat(),
                "use_cache": use_cache,
                "cache_path": str(self._cache_path),
            },
            "preprocessing": {
                "record_filters": [
                    "must have non-empty title",
                    "must have non-empty abstract",
                    "must have valid publication date",
                    "must have at least one keyword",
                ],
                "keyword_normalisation": "lowercased, spaces replaced with underscores",
            },
            "corpus_stats": {
                "n_publications": len(self._data),
                "year_min": min_year,
                "year_max": max_year,
                "pubs_per_year": pubs_per_year,
                "top_keywords": top_keywords,
            },
            "version": {
                "schema_version": 1,
            },
        }

        meta_path = self._cache_path.with_suffix(".meta.json")
        meta_path.write_text(
            json.dumps(self._meta_data, indent=2),
            encoding="utf-8",
        )

    def __len__(self) -> int:
        """Return the number of publications in the corpus."""
        return len(self._data)

    def __iter__(self):
        """Iterate over publications in the corpus."""
        return iter(self._data)

    def __getitem__(self, index: int) -> Publication:
        """Return the publication at the given index."""
        return self._data[index]

    @property
    def data(self) -> list[Publication]:
        """Return a copy of the internal publication list."""
        return list(self._data)

    @property
    def concept(self) -> str:
        """Return the concept associated with this corpus."""
        return self._concept

    @property
    def meta(self) -> dict:
        """Return a shallow copy of the metadata dictionary."""
        return dict(self._meta_data)

    def keywords_occurrence(self) -> dict[str, int]:
        """Count keyword occurrences across all publications in the corpus."""
        counts: dict[str, int] = {}
        for pub in self._data:
            for kw in pub.keywords:
                counts[kw] = counts.get(kw, 0) + 1
        return counts

    def years(self) -> dict[int, int]:
        """Return a mapping of {year -> number of publications in that year}."""
        counts: dict[int, int] = {}
        for pub in self._data:
            pub_year = pub.publication_date.year
            counts[pub_year] = counts.get(pub_year, 0) + 1
        return dict(sorted(counts.items()))

    def summary(self) -> str:
        """Return a short, human-readable summary of the corpus."""
        years = self.years().keys()
        year_range = (min(years), max(years)) if years else (None, None)
        return (
            f"PublicationCorpus(concept={self._concept!r}, "
            f"n_pubs={len(self)}, "
            f"year_range={year_range}, "
            f"n_unique_keywords={len(self.keywords_occurrence())})"
        )

    def cooccurrence_network(self, min_value: int = 0) -> nx.Graph:
        """Build a keyword co-occurrence network for the full corpus."""
        return build_cooccurrence_network(publications=self._data, min_value=min_value)

    def temporal_network(self, min_value: int = 0) -> dict[int, nx.Graph]:
        """Build a keyword co-occurrence network per publication year."""
        return build_temporal_network(publications=self._data, min_value=min_value)

    def concept_method_network(self, min_value: int = 0) -> nx.Graph:
        """Build a concept-method bipartite network for the full corpus."""
        return build_concept_method_bipartite(
            publications=self._data,
            min_value=min_value,
        )

    def temporal_concept_method_network(self, min_value: int = 0) -> nx.Graph:
        """Build a concept-method bipartite network per publication year."""
        return build_temporal_concept_method_bipartite(
            publications=self._data,
            min_value=min_value,
        )

    def _w2v_model_path(self, w2v_config: Word2VecConfig, year: int | None) -> Path:
        """
        Return the disk path for a cached Word2Vec model.

        If tokenization/sentence construction changes, bump tokv to invalidate caches.
        """
        tokv = 1
        scope = "overall" if year is None else f"year{year}"
        cfg = (
            f"vs{w2v_config.vector_size}_"
            f"win{w2v_config.window}_"
            f"mc{w2v_config.min_count}_"
            f"sg{w2v_config.sg}_"
            f"ep{w2v_config.epochs}_"
            f"seed{w2v_config.seed}"
        )
        return self._w2v_cache_dir / f"{scope}__tokv{tokv}__{cfg}.model"

    def get_or_train_word2vec_model(
        self,
        w2v_config: Word2VecConfig,
        *,
        year: int | None = None,
        persist: bool = False,
    ) -> Word2Vec:
        """
        Return a Word2Vec model trained on the corpus (or a specific year).

        Models are cached in memory. If persist=True, models may be loaded from / saved
        to disk under the per-concept Word2Vec cache directory.
        """
        key = (year, w2v_config)
        cached = self._w2v_models.get(key)
        if cached is not None:
            return cached

        with self._w2v_lock:
            cached = self._w2v_models.get(key)
            if cached is not None:
                return cached

            model_path = self._w2v_model_path(w2v_config, year)

            if persist and model_path.exists():
                model = Word2Vec.load(str(model_path))
                self._w2v_models[key] = model
                return model

            if year is None:
                pubs = self._data
            else:
                pubs = [p for p in self._data if p.publication_date.year == year]

            model = train_word2vec(publications=pubs, config=w2v_config)

            if persist:
                self._w2v_cache_dir.mkdir(parents=True, exist_ok=True)
                model.save(str(model_path))

            self._w2v_models[key] = model
            return model

    def semantic_similarity_network(
        self,
        w2v_config: Word2VecConfig,
        min_keyword_freq: int = 5,
        similarity_threshold: float = 0.5,
        top_k: int | None = None,
    ) -> nx.Graph:
        """Build a semantic similarity network for the full corpus using Word2Vec."""
        model = self.get_or_train_word2vec_model(w2v_config, year=None)
        return build_semantic_similarity_network(
            publications=self._data,
            w2v_config=w2v_config,
            min_keyword_freq=min_keyword_freq,
            similarity_threshold=similarity_threshold,
            top_k=top_k,
            model=model,
        )

    def temporal_semantic_similarity_network(
        self,
        w2v_config: Word2VecConfig,
        min_keyword_freq: int = 5,
        similarity_threshold: float = 0.5,
        top_k: int | None = None,
    ) -> dict[int, nx.Graph]:
        """Build a semantic similarity network per year using per-year Word2Vec models."""
        years = list(self.years().keys())
        models_by_year = {
            y: self.get_or_train_word2vec_model(w2v_config, year=y) for y in years
        }
        return build_temporal_semantic_similarity_network(
            publications=self._data,
            w2v_config=w2v_config,
            min_keyword_freq=min_keyword_freq,
            similarity_threshold=similarity_threshold,
            top_k=top_k,
            models_by_year=models_by_year,
        )
