"""Coder reliability simulation and reporting utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

AMBIGUOUS_THEMES = {"AFFORDABILITY", "FOOD_INSECURITY"}


def _get_theme_columns(df: pd.DataFrame) -> List[str]:
    return [col for col in df.columns if col.isupper() and col not in {"ID"}]


def simulate_second_coder(
    coded_wide_path: str,
    out_dir: str,
    seed: int = 42,
    base_flip: float = 0.05,
    ambiguous_flip: float = 0.08,
) -> Dict[str, str]:
    """Simulate a second coder by randomly flipping theme labels."""

    coded_df = pd.read_csv(coded_wide_path)
    theme_cols = _get_theme_columns(coded_df)
    rng = np.random.default_rng(seed)

    coder2 = coded_df.copy()
    for theme in theme_cols:
        values = coder2[theme].astype(int).to_numpy(copy=True)
        flip_rate = ambiguous_flip if theme in AMBIGUOUS_THEMES else base_flip
        flips = rng.random(len(values)) < flip_rate
        values[flips] = 1 - values[flips]
        coder2[theme] = values.astype(bool)

    out_path = Path(out_dir) / "coded_responses_wide_coder2.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    coder2.to_csv(out_path, index=False)
    return {"coded_wide_coder2": str(out_path)}


def _cohens_kappa(series_a: pd.Series, series_b: pd.Series) -> float:
    a = series_a.astype(int)
    b = series_b.astype(int)
    po = (a == b).mean()
    p_yes_a = a.mean()
    p_yes_b = b.mean()
    p_no_a = 1 - p_yes_a
    p_no_b = 1 - p_yes_b
    pe = p_yes_a * p_yes_b + p_no_a * p_no_b
    denom = 1 - pe
    if denom == 0:
        return 0.0
    return float((po - pe) / denom)


def compute_reliability(
    coded_wide_path: str,
    coded_wide_coder2_path: str,
    out_dir: str,
) -> Dict[str, str]:
    """Compute percent agreement and Cohen's kappa per theme."""

    coder1 = pd.read_csv(coded_wide_path).set_index("respondent_id")
    coder2 = pd.read_csv(coded_wide_coder2_path).set_index("respondent_id")
    coder2 = coder2.reindex(coder1.index)

    theme_cols = _get_theme_columns(coder1)

    records = []
    for theme in theme_cols:
        if theme not in coder2.columns:
            continue
        series_a = coder1[theme].astype(bool)
        series_b = coder2[theme].astype(bool)
        percent_agreement = float((series_a == series_b).mean())
        kappa = _cohens_kappa(series_a, series_b)
        records.append(
            {
                "theme": theme,
                "percent_agreement": percent_agreement,
                "kappa": kappa,
            }
        )

    reliability_df = pd.DataFrame(records)
    out_csv = Path(out_dir) / "reliability_by_theme.csv"
    out_md = Path(out_dir) / "reliability_summary.md"
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    reliability_df.to_csv(out_csv, index=False)

    avg_agreement = reliability_df["percent_agreement"].mean() if not reliability_df.empty else 0
    avg_kappa = reliability_df["kappa"].mean() if not reliability_df.empty else 0
    lowest = reliability_df.sort_values("kappa").head(1).to_dict(orient="records") if not reliability_df.empty else []
    low_msg = ""
    if lowest:
        low = lowest[0]
        low_msg = f"Lowest agreement on {low['theme']} (κ={low['kappa']:.2f})."

    summary_text = (
        "## Reliability overview\n"
        f"Average percent agreement: {avg_agreement:.2%}.\n\n"
        f"Average Cohen's kappa: {avg_kappa:.2f}. {low_msg}\n"
        "Simulated coder 2 flips 5–8% of labels to mimic human noise; real coder studies recommended before deployment.\n"
    )
    out_md.write_text(summary_text, encoding="utf-8")

    return {
        "reliability_csv": str(out_csv),
        "reliability_md": str(out_md),
    }


__all__ = ["simulate_second_coder", "compute_reliability"]
