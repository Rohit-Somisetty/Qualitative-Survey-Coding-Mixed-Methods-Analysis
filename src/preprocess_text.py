"""Lightweight preprocessing helpers for qualitative text."""

from __future__ import annotations

from typing import Iterable, Set

import pandas as pd
import regex as re

BASIC_STOPWORDS: Set[str] = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "we",
    "with",
}


def normalize_text(text: str) -> str:
    """Lowercase text and strip punctuation with unicode awareness."""

    if not isinstance(text, str):
        return ""
    lowered = text.lower()
    no_punct = re.sub(r"[^\p{L}\p{N}\s]", " ", lowered)
    squeezed = re.sub(r"\s+", " ", no_punct).strip()
    return squeezed


def remove_stopwords(text: str, stopwords: Iterable[str] | None = None) -> str:
    """Remove a lightweight set of stopwords to simplify downstream matching."""

    tokens = text.split()
    if stopwords is None:
        stopwords = BASIC_STOPWORDS
    filtered = [token for token in tokens if token not in stopwords]
    return " ".join(filtered)


def preprocess_text(text: str) -> str:
    """Full preprocessing pipeline for a single string."""

    normalized = normalize_text(text)
    return remove_stopwords(normalized)


def preprocess_series(series: pd.Series) -> pd.Series:
    """Apply preprocessing to a pandas Series of open-ended responses."""

    return series.fillna("").astype(str).apply(preprocess_text)


__all__ = ["preprocess_text", "preprocess_series", "normalize_text", "remove_stopwords"]
