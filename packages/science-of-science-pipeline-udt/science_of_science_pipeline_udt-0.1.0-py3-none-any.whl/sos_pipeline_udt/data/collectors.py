"""
data.collectors

Author: Duco Trompert
Course: Afstudeerproject bachelor Informatica
Thesis: Science of Science: An Integrated Pipeline for Tracing Conceptual Emergence and Evolution in Semantic Space
Date: 2026-01-23

Data collection utilities for retrieving and validating publication metadata
from external sources (currently OpenAlex) and converting them into Publication objects.
"""

from datetime import date

import requests

from sos_pipeline_udt.config import (
    OPENALEX_CURSOR_START,
    OPENALEX_FILTER_TEMPLATE,
    OPENALEX_MAILTO,
    OPENALEX_PER_PAGE,
    OPENALEX_TIMEOUT_S,
    OPENALEX_WORKS_ENDPOINT,
)
from sos_pipeline_udt.data.publication import Publication


def reconstruct_abstract(abstract_inverted_index: dict[str, list[int]]) -> str:
    """Reconstruct an abstract string from an OpenAlex inverted index (or return empty)."""
    if not isinstance(abstract_inverted_index, dict):
        return ""
    position_map = {
        pos: word
        for word, positions in abstract_inverted_index.items()
        for pos in positions
    }
    if not position_map:
        return ""
    return " ".join(position_map[i] for i in sorted(position_map))


def is_valid_record(record: dict) -> bool:
    """
    Validate that an OpenAlex record contains the required fields for this project.

    Required:
    - non-empty title
    - non-empty abstract (after reconstruction)
    - valid publication_date (YYYY-MM-DD)
    - non-empty keywords list
    """
    title = record.get("title")
    if not title or not title.strip():
        return False

    abstract_raw = record.get("abstract_inverted_index")
    abstract = reconstruct_abstract(abstract_raw)
    if not abstract.strip():
        return False

    pub_date = record.get("publication_date")
    if not pub_date:
        return False
    try:
        y, m, d = [int(x) for x in pub_date.split("-")]
        _ = date(y, m, d)
    except Exception:
        return False

    keywords = record.get("keywords")
    if not isinstance(keywords, list) or len(keywords) == 0:
        return False

    return True


def collect_openalex_data(concept: str) -> list[Publication]:
    """Query OpenAlex for a concept and return a list of validated Publication objects."""
    BASE_URL = OPENALEX_WORKS_ENDPOINT
    parameters = {
        "filter": OPENALEX_FILTER_TEMPLATE.format(concept=concept),
        "per-page": OPENALEX_PER_PAGE,
        "cursor": OPENALEX_CURSOR_START,
        "mailto": OPENALEX_MAILTO,
    }

    publications: list[Publication] = []

    while True:
        r = requests.get(url=BASE_URL, params=parameters, timeout=OPENALEX_TIMEOUT_S)
        r.raise_for_status()
        payload = r.json()

        results = payload.get("results", [])
        if not results:
            break

        for result in results:
            if is_valid_record(result):
                y, m, d = [int(x) for x in result["publication_date"].split("-")]
                authorships = result.get("authorships", []) or []
                authors = []
                for a in authorships:
                    author = (a.get("author") or {}).get("display_name")
                    if author:
                        authors.append(author.lower())

                publications.append(
                    Publication(
                        source_id=result["id"],
                        doi=result.get("doi", ""),
                        title=result["title"].lower(),
                        abstract=reconstruct_abstract(
                            result["abstract_inverted_index"]
                        ).lower(),
                        publication_date=date(y, m, d),
                        keywords=[
                            kw["display_name"].strip().lower().replace(" ", "_")
                            for kw in result["keywords"]
                        ],
                        authors=authors,
                        total_cited_by=int(result.get("cited_by_count", 0)),
                        source="OpenAlex",
                    )
                )

        cursor = payload.get("meta", {}).get("next_cursor")
        if not cursor:
            break
        parameters["cursor"] = cursor

    return publications
