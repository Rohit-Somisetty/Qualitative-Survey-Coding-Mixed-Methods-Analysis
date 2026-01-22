"""Utilities for selecting exemplar qualitative quotes."""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd


def select_exemplar_quotes(
    df_raw: pd.DataFrame,
    df_long: pd.DataFrame,
    theme: str,
    k: int = 5,
    seed: int = 42,
) -> pd.DataFrame:
    """Select exemplar quotes for a given theme with basic diversity heuristics."""

    if df_long.empty:
        return pd.DataFrame(columns=["theme", "frame", "wave", "state", "quote"])

    theme_rows = df_long[df_long["theme"] == theme].copy()
    if theme_rows.empty:
        return pd.DataFrame(columns=["theme", "frame", "wave", "state", "quote"])

    merged = theme_rows.dropna(subset=["open_response_text"]).drop_duplicates(subset=["cleaned_text"])
    if merged.empty:
        return pd.DataFrame(columns=["theme", "frame", "wave", "state", "quote"])

    rng = np.random.default_rng(seed + abs(hash(theme)) % (2**32))
    shuffled_idx = rng.permutation(len(merged))
    merged = merged.iloc[shuffled_idx].reset_index(drop=True)

    # First pass: prioritize unique states for geographic diversity.
    state_selected = merged.drop_duplicates(subset=["state"]).head(k)
    if len(state_selected) < k:
        remaining = merged.drop(index=state_selected.index, errors="ignore")
        filler = remaining.head(k - len(state_selected))
        state_selected = pd.concat([state_selected, filler], ignore_index=True)

    state_selected = state_selected.sort_values(["frame", "wave", "state"]).head(k)

    return state_selected.assign(
        theme=theme,
        quote=state_selected["open_response_text"].str.strip(),
    )[["theme", "frame", "wave", "state", "quote"]]


__all__ = ["select_exemplar_quotes"]
