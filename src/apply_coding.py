"""Rule-based thematic coding utilities for the qualitative pipeline."""

from __future__ import annotations

from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Dict, Iterable, List

import pandas as pd

try:  # pragma: no cover
    from .codebook import Theme
    from .exemplars import select_exemplar_quotes
    from .preprocess_text import preprocess_series, preprocess_text
except ImportError:  # pragma: no cover
    from codebook import Theme
    from exemplars import select_exemplar_quotes
    from preprocess_text import preprocess_series, preprocess_text


def _prepare_keyword_map(codebook: Dict[str, Theme]) -> Dict[str, List[str]]:
    keyword_map: Dict[str, List[str]] = {}
    for theme_name, theme in codebook.items():
        normalized_keywords = [preprocess_text(keyword) for keyword in theme.keywords]
        keyword_map[theme_name] = [kw for kw in normalized_keywords if kw]
    return keyword_map


def _match_themes(text: str, keyword_map: Dict[str, List[str]]) -> List[str]:
    matched: List[str] = []
    for theme_name, keywords in keyword_map.items():
        if any(keyword in text for keyword in keywords):
            matched.append(theme_name)
    return sorted(set(matched))


def _build_theme_counts(df_long: pd.DataFrame) -> pd.DataFrame:
    if df_long.empty:
        return pd.DataFrame(columns=["theme", "frame", "wave", "count"])
    return (
        df_long.groupby(["theme", "frame", "wave"], as_index=False)
        .size()
        .rename(columns={"size": "count"})
    )


def _build_theme_frequencies(df_counts: pd.DataFrame, raw_df: pd.DataFrame) -> pd.DataFrame:
    totals = raw_df.groupby(["frame", "wave"], as_index=False).size().rename(columns={"size": "n_responses"})
    freq = df_counts.merge(totals, on=["frame", "wave"], how="left")
    if freq.empty:
        freq = df_counts.copy()
        freq["n_responses"] = 0
    freq["percent"] = freq["count"] / freq["n_responses"].replace({0: pd.NA})
    return freq


def _build_cooccurrence(theme_lists: Iterable[List[str]], total_responses: int) -> pd.DataFrame:
    counter: Counter[tuple[str, str]] = Counter()
    for themes in theme_lists:
        unique = sorted(set(themes))
        for theme_a, theme_b in combinations(unique, 2):
            counter[(theme_a, theme_b)] += 1
    if not counter:
        return pd.DataFrame(columns=["theme_a", "theme_b", "count", "normalized_rate"])
    rows = []
    for (theme_a, theme_b), count in counter.items():
        rows.append(
            {
                "theme_a": theme_a,
                "theme_b": theme_b,
                "count": count,
                "normalized_rate": count / max(total_responses, 1),
            }
        )
    return pd.DataFrame(rows).sort_values(by="count", ascending=False).reset_index(drop=True)


def apply_thematic_coding(
    raw_path: str,
    codebook: Dict[str, Theme],
    out_dir: str,
    seed: int = 42,
) -> Dict[str, str]:
    """Apply rule-based thematic coding and persist summary artifacts."""

    data_dir = Path(out_dir)
    processed_dir = data_dir / "processed"
    outputs_dir = data_dir / "outputs"
    processed_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    raw_df = pd.read_csv(raw_path)
    raw_df["cleaned_text"] = preprocess_series(raw_df["open_response_text"])

    keyword_map = _prepare_keyword_map(codebook)
    raw_df["themes"] = raw_df["cleaned_text"].apply(lambda text: _match_themes(text, keyword_map))

    theme_lists = raw_df["themes"].tolist()

    coded_responses_path = processed_dir / "coded_responses.csv"
    raw_df.assign(themes=raw_df["themes"].apply(lambda items: "|".join(items))).to_csv(coded_responses_path, index=False)

    theme_columns = sorted(keyword_map.keys())
    df_wide = raw_df.copy()
    for theme in theme_columns:
        df_wide[theme] = df_wide["themes"].apply(lambda items, t=theme: t in items)
    coded_wide_path = processed_dir / "coded_responses_wide.csv"
    df_wide.to_csv(coded_wide_path, index=False)

    df_long = df_wide[[
        "respondent_id",
        "frame",
        "wave",
        "survey_month",
        "state",
        "open_response_text",
        "cleaned_text",
        "themes",
    ]].explode("themes")
    df_long = df_long[df_long["themes"].notna() & (df_long["themes"] != "")]
    df_long = df_long.rename(columns={"themes": "theme"})
    coded_long_path = processed_dir / "coded_responses_long.csv"
    df_long.to_csv(coded_long_path, index=False)

    theme_counts = _build_theme_counts(df_long)
    theme_counts_path = processed_dir / "theme_counts.csv"
    theme_counts.to_csv(theme_counts_path, index=False)

    theme_frequencies = _build_theme_frequencies(theme_counts, raw_df)
    theme_freq_path = outputs_dir / "theme_frequencies.csv"
    theme_frequencies.to_csv(theme_freq_path, index=False)

    cooccurrence = _build_cooccurrence(theme_lists, total_responses=len(raw_df))
    theme_cooccurrence_path = outputs_dir / "theme_cooccurrence.csv"
    cooccurrence.to_csv(theme_cooccurrence_path, index=False)

    exemplar_frames = []
    if not df_long.empty:
        for theme in theme_columns:
            exemplars = select_exemplar_quotes(raw_df, df_long, theme=theme, k=5, seed=seed)
            if not exemplars.empty:
                exemplar_frames.append(exemplars)
    exemplar_df = pd.concat(exemplar_frames, ignore_index=True) if exemplar_frames else pd.DataFrame(columns=["theme", "frame", "wave", "state", "quote"])
    exemplar_path = outputs_dir / "exemplar_quotes.csv"
    exemplar_df.to_csv(exemplar_path, index=False)

    return {
        "coded_responses": str(coded_responses_path),
        "coded_wide": str(coded_wide_path),
        "coded_long": str(coded_long_path),
        "theme_counts": str(theme_counts_path),
        "theme_frequencies": str(theme_freq_path),
        "theme_cooccurrence": str(theme_cooccurrence_path),
        "exemplar_quotes": str(exemplar_path),
    }


__all__ = ["apply_thematic_coding"]
