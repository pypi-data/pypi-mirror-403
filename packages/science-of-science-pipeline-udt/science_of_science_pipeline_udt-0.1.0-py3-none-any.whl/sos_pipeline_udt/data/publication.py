"""
data.publication

Author: Duco Trompert
Course: Afstudeerproject bachelor Informatica
Thesis: Science of Science: An Integrated Pipeline for Tracing Conceptual Emergence and Evolution in Semantic Space
Date: 2026-01-23

Data model for representing a single publication and converting to/from
a serializable dictionary format (used for caching and I/O).
"""

from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True)
class Publication:
    """Immutable representation of a publication and its key metadata."""

    source_id: str
    doi: str
    title: str
    abstract: str
    publication_date: date
    keywords: list[str]
    authors: list[str]
    total_cited_by: int
    source: str

    def __repr__(self) -> str:
        """Return a compact, human-readable representation for debugging/logging."""
        return (
            f"Publication(title={self.title!r}, "
            f"date={self.publication_date}, "
            f"source={self.source})"
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert this publication into a JSON-serializable dictionary."""
        return {
            "source_id": self.source_id,
            "doi": self.doi,
            "title": self.title,
            "abstract": self.abstract,
            "publication_date": self.publication_date.isoformat(),
            "keywords": list(self.keywords),
            "authors": list(self.authors),
            "total_cited_by": self.total_cited_by,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Publication":
        """Create a Publication from a cached/serialized dictionary."""
        kws = d.get("keywords", [])
        if not isinstance(kws, list):
            kws = [str(kws)]

        authors = d.get("authors", [])
        if not isinstance(authors, list):
            authors = [str(authors)]

        return cls(
            source_id=d.get("source_id", ""),
            doi=d.get("doi", ""),
            title=d.get("title", ""),
            abstract=d.get("abstract", ""),
            publication_date=date.fromisoformat(str(d["publication_date"])),
            keywords=[str(k) for k in kws],
            authors=[str(a) for a in authors],
            total_cited_by=int(d.get("total_cited_by", 0)),
            source=d.get("source", "OpenAlex"),
        )
