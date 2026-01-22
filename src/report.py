"""Automated qualitative + mixed-methods briefing generator."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import pandas as pd


def _format_top_themes(theme_counts: pd.DataFrame) -> str:
    if theme_counts.empty:
        return "No coded themes available."
    overall = (
        theme_counts.groupby("theme", as_index=False)["count"].sum().sort_values("count", ascending=False).head(5)
    )
    lines = ["### Overall leaders"]
    for _, row in overall.iterrows():
        lines.append(f"- {row['theme']}: {int(row['count'])} mentions")

    lines.append("\n### By frame")
    frame_counts = (
        theme_counts.groupby(["frame", "theme"], as_index=False)["count"].sum().sort_values(["frame", "count"], ascending=[True, False])
    )
    for frame, frame_df in frame_counts.groupby("frame"):
        top = frame_df.head(3)
        formatted = ", ".join(f"{row.theme} ({int(row.count)})" for row in top.itertuples())
        lines.append(f"- {frame.title()}: {formatted}")
    return "\n".join(lines)


def _format_quotes(exemplar_df: pd.DataFrame, max_quotes: int = 5) -> str:
    if exemplar_df.empty:
        return "No exemplar quotes captured."
    selected = exemplar_df.groupby("theme" , as_index=False).head(1)
    if selected.shape[0] < max_quotes:
        extras = exemplar_df[~exemplar_df.index.isin(selected.index)].head(max_quotes - len(selected))
        selected = pd.concat([selected, extras], ignore_index=True)
    selected = selected.head(max_quotes)
    lines: List[str] = []
    for _, row in selected.iterrows():
        quote = row["quote"].strip().replace("\n", " ")
        lines.append(f"> **{row['theme']} ({row['frame']} – wave {int(row['wave'])}, {row['state']}):** {quote}")
    return "\n\n".join(lines)


def _format_cooccurrence(coocc_df: pd.DataFrame) -> str:
    if coocc_df.empty:
        return "No theme pairings detected."
    top_pairs = coocc_df.head(3)
    lines = []
    for _, row in top_pairs.iterrows():
        rate_pct = float(row["normalized_rate"]) * 100
        lines.append(
            f"- {row['theme_a']} + {row['theme_b']}: {int(row['count'])} co-mentions ({rate_pct:.1f}% of responses)"
        )
    return "\n".join(lines)


def _format_mixed_methods(summary_df: pd.DataFrame) -> str:
    if summary_df.empty:
        return "No mixed-methods statistics yet."
    lines: List[str] = []
    stress = summary_df[summary_df["metric"] == "stress_score_mean"]
    present = stress[stress["group"] == "theme_present"].groupby("theme")["estimate"].mean()
    absent = stress[stress["group"] == "theme_absent"].groupby("theme")["estimate"].mean()
    shared = present.index.intersection(absent.index)
    stress_diff = (present[shared] - absent[shared]).sort_values(ascending=False).head(3)
    for theme, delta in stress_diff.items():
        lines.append(f"- {theme}: +{delta:.1f} stress pts when theme is present")

    food = summary_df[summary_df["metric"] == "food_insecurity_rate"]
    food_present = food[food["group"] == "theme_present"].groupby("theme")["estimate"].mean()
    food_absent = food[food["group"] == "theme_absent"].groupby("theme")["estimate"].mean()
    food_shared = food_present.index.intersection(food_absent.index)
    food_diff = (food_present[food_shared] - food_absent[food_shared]).sort_values(ascending=False).head(3)
    for theme, delta in food_diff.items():
        lines.append(f"- {theme}: +{delta*100:.1f} pp in food insecurity when present")

    provider = summary_df[(summary_df["metric"] == "closure_risk_high_rate") & (summary_df["frame"] == "provider")]
    provider_present = provider[provider["group"] == "theme_present"].groupby("theme")["estimate"].mean()
    provider_absent = provider[provider["group"] == "theme_absent"].groupby("theme")["estimate"].mean()
    provider_shared = provider_present.index.intersection(provider_absent.index)
    provider_diff = (provider_present[provider_shared] - provider_absent[provider_shared]).sort_values(ascending=False).head(2)
    for theme, delta in provider_diff.items():
        lines.append(f"- Providers citing {theme}: +{delta*100:.1f} pp risk of closure")

    return "\n".join(lines)


def generate_brief(paths: Dict[str, str]) -> str:
    """Create the Markdown qualitative brief and return the output path."""

    theme_counts = pd.read_csv(paths["theme_counts"]) if Path(paths["theme_counts"]).exists() else pd.DataFrame()
    exemplars = pd.read_csv(paths["exemplar_quotes"]) if Path(paths["exemplar_quotes"]).exists() else pd.DataFrame()
    coocc = pd.read_csv(paths["theme_cooccurrence"]) if Path(paths["theme_cooccurrence"]).exists() else pd.DataFrame()
    summary = pd.read_csv(paths["mixed_methods_summary"]) if Path(paths["mixed_methods_summary"]).exists() else pd.DataFrame()

    top_themes_section = _format_top_themes(theme_counts)
    quotes_section = _format_quotes(exemplars)
    coocc_section = _format_cooccurrence(coocc)
    mixed_section = _format_mixed_methods(summary)

    report_text = f"""# Qualitative + Mixed-Methods Brief
_Generated on {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC} from deterministic synthetic data._

## Top themes
{top_themes_section}

## Exemplar quotes
{quotes_section}

## Theme co-occurrence insights
{coocc_section}

## Mixed-methods highlights
{mixed_section}

## Methods & limitations
- Rule-based keywords from a transparent codebook (see docs/codebook.md) drive multi-label tagging.
- Quantitative indicators are simulated with interpretable correlations; they approximate but do not replace observed data.
- Synthetic sample mirrors Jan–Mar 2024 household/provider frames; interpret directional signals, not literal magnitudes.
"""

    output_path = Path(paths["brief_path"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_text, encoding="utf-8")
    return str(output_path)


__all__ = ["generate_brief"]
