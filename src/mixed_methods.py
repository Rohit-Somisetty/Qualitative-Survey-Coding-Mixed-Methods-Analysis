"""Mixed-methods integration utilities for qualitative + quantitative outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List

import numpy as np
import pandas as pd


def simulate_quant_indicators(raw_responses_path: str, seed: int = 42) -> pd.DataFrame:
    """Simulate correlated quantitative indicators for each respondent."""

    raw_path = Path(raw_responses_path)
    raw_df = pd.read_csv(raw_path)

    data_dir = raw_path.parent.parent
    coded_wide_path = data_dir / "processed" / "coded_responses_wide.csv"
    if not coded_wide_path.exists():
        raise FileNotFoundError("coded_responses_wide.csv is required before simulating indicators")
    coded_df = pd.read_csv(coded_wide_path)

    merged = raw_df[["respondent_id", "frame", "wave"]].merge(
        coded_df[["respondent_id"] + [col for col in coded_df.columns if col.isupper()]],
        on="respondent_id",
        how="left",
    )

    rng = np.random.default_rng(seed)
    n = len(merged)

    stress = np.clip(rng.normal(loc=18, scale=6, size=n), 0, 40)
    stress += merged.get("STRESS_BURNOUT", 0).astype(int) * rng.normal(8, 2, n)
    stress += merged.get("SCHEDULING_CONSTRAINTS", 0).astype(int) * rng.normal(2, 1, n)
    merged["stress_score"] = np.clip(stress, 0, 40)

    base_food_prob = 0.15 + rng.normal(0, 0.02, n)
    food_prob = base_food_prob
    food_prob += merged.get("FOOD_INSECURITY", 0) * 0.35
    food_prob += merged.get("AFFORDABILITY", 0) * 0.2
    merged["food_insecurity"] = (rng.uniform(size=n) < np.clip(food_prob, 0, 1)).astype(int)

    employment_prob = 0.1 + rng.normal(0, 0.01, n)
    employment_prob += merged.get("EMPLOYMENT_DISRUPTION", 0) * 0.5
    employment_prob += merged.get("CHILDCARE_ACCESS", 0) * 0.15
    merged["employment_disruption"] = (
        (merged["frame"] == "household") & (rng.uniform(size=n) < np.clip(employment_prob, 0, 1))
    ).astype(int)

    closure_base = rng.normal(loc=1.0, scale=0.4, size=n)
    closure_base += merged.get("PROVIDER_STAFF_SHORTAGE", 0) * rng.normal(1.2, 0.2, n)
    closure_base += merged.get("SCHEDULING_CONSTRAINTS", 0) * 0.2
    closure_score = np.clip(np.round(closure_base), 0, 3)
    merged["provider_closure_risk"] = np.where(merged["frame"] == "provider", closure_score, 0)
    merged["closure_risk_high"] = (merged["provider_closure_risk"] >= 2).astype(int)

    quant_path = data_dir / "outputs" / "quantitative_indicators.csv"
    quant_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(quant_path, index=False)
    return merged


def _summarize_metric(
    df: pd.DataFrame,
    theme: str,
    metric_col: str,
    metric_name: str,
    frames: Iterable[str] | None = None,
) -> List[Dict[str, object]]:
    records: List[Dict[str, object]] = []
    frames = frames or df["frame"].unique().tolist()

    for frame in frames:
        frame_df = df[df["frame"] == frame]
        if frame_df.empty:
            continue
        for wave in sorted(frame_df["wave"].unique()):
            wave_df = frame_df[frame_df["wave"] == wave]
            if wave_df.empty:
                continue
            for flag_value, group_df in wave_df.groupby(theme):
                group_label = "theme_present" if bool(flag_value) else "theme_absent"
                if group_df.empty:
                    continue
                estimate = group_df[metric_col].mean()
                records.append(
                    {
                        "frame": frame,
                        "wave": wave,
                        "theme": theme,
                        "metric": metric_name,
                        "group": group_label,
                        "estimate": float(estimate),
                        "n": int(group_df.shape[0]),
                    }
                )
    return records


def mixed_methods_summary(
    coded_wide_path: str,
    quant_path: str,
    out_dir: str,
) -> Dict[str, str]:
    """Join qualitative theme flags with quantitative indicators and summarize."""

    coded_df = pd.read_csv(coded_wide_path)
    quant_df = pd.read_csv(quant_path)
    merged = coded_df.merge(
        quant_df[["respondent_id", "stress_score", "food_insecurity", "employment_disruption", "provider_closure_risk", "closure_risk_high"]],
        on="respondent_id",
        how="left",
    )

    theme_columns = [col for col in coded_df.columns if col.isupper() and col not in {"FRAME", "STATE"}]

    records: List[Dict[str, object]] = []
    for theme in theme_columns:
        records.extend(_summarize_metric(merged, theme, "stress_score", "stress_score_mean"))
        records.extend(_summarize_metric(merged, theme, "food_insecurity", "food_insecurity_rate"))
        records.extend(
            _summarize_metric(
                merged,
                theme,
                "closure_risk_high",
                "closure_risk_high_rate",
                frames=["provider"],
            )
        )

    summary_df = pd.DataFrame(records)
    out_path = Path(out_dir) / "mixed_methods_summary.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(out_path, index=False)
    return {"mixed_methods_summary": str(out_path)}


__all__ = ["simulate_quant_indicators", "mixed_methods_summary"]
