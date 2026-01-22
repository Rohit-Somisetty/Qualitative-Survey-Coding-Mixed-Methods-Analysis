"""Generate publication-style qualitative + mixed-methods fact sheet."""

from __future__ import annotations

import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape

try:  # pragma: no cover - optional dependency
    from weasyprint import HTML  # type: ignore
except ImportError:  # pragma: no cover
    HTML = None  # type: ignore


def _format_theme_list(df: pd.DataFrame, top_n: int = 3) -> str:
    if df.empty:
        return "n/a"
    rows = df.head(top_n).itertuples()
    return ", ".join(f"{row.theme} ({int(row.count)})" for row in rows)


def _build_key_findings(theme_counts: pd.DataFrame, coocc: pd.DataFrame, summary: pd.DataFrame, reliability_df: pd.DataFrame) -> List[str]:
    findings: List[str] = []

    overall = theme_counts.groupby("theme", as_index=False)["count"].sum().sort_values("count", ascending=False)
    by_frame = (
        theme_counts.groupby(["frame", "theme"], as_index=False)["count"].sum().sort_values(["frame", "count"], ascending=[True, False])
    )
    household = _format_theme_list(by_frame[by_frame["frame"] == "household"])
    provider = _format_theme_list(by_frame[by_frame["frame"] == "provider"])
    findings.append(
        f"Top themes overall: {_format_theme_list(overall)}. Household focus: {household}. Provider focus: {provider}."
    )

    if not coocc.empty:
        top_pairs = coocc.head(2).apply(
            lambda row: f"{row['theme_a']} + {row['theme_b']} ({int(row['count'])} co-mentions)", axis=1
        )
        findings.append(f"Theme pairs surfacing together: {', '.join(top_pairs)}.")
    else:
        findings.append("Theme co-occurrence signals pending additional data.")

    stress = summary[summary["metric"] == "stress_score_mean"]
    stress_gap_lines = []
    for frame in ["household", "provider"]:
        frame_rows = stress[stress["frame"] == frame]
        if frame_rows.empty:
            continue
        pivot = frame_rows.pivot_table(index="theme", columns="group", values="estimate", aggfunc="mean")
        pivot["delta"] = pivot.get("theme_present", 0) - pivot.get("theme_absent", 0)
        top = pivot["delta"].sort_values(ascending=False).head(1)
        if not top.empty:
            theme = top.index[0]
            delta = float(top.iloc[0])
            stress_gap_lines.append(f"{frame.title()}: {theme} +{delta:.1f} stress pts")
    if stress_gap_lines:
        findings.append("Biggest stress gaps → " + "; ".join(stress_gap_lines) + ".")
    else:
        findings.append("Stress score gaps pending future waves.")

    food = summary[summary["metric"] == "food_insecurity_rate"]
    if not food.empty:
        pivot = food.pivot_table(index="theme", columns="group", values="estimate", aggfunc="mean")
        pivot["delta"] = pivot.get("theme_present", 0) - pivot.get("theme_absent", 0)
        top = pivot["delta"].sort_values(ascending=False).head(1)
        if not top.empty:
            theme = top.index[0]
            delta = float(top.iloc[0] * 100)
            findings.append(f"Food insecurity spikes by {delta:.1f} pp when {theme} is present.")
    if len(findings) < 4:
        findings.append("Food insecurity deltas pending additional data.")

    if not reliability_df.empty:
        findings.append(
            f"Simulated coder agreement averages {reliability_df['percent_agreement'].mean():.0%} with κ={reliability_df['kappa'].mean():.2f}."
        )
    else:
        findings.append("Coder reliability summary will populate after coding outputs exist.")

    return findings[:5]


def _select_quotes(exemplar_df: pd.DataFrame, frame: str, k: int = 2) -> List[Dict[str, str]]:
    frame_df = exemplar_df[exemplar_df["frame"] == frame]
    if frame_df.empty:
        return []
    frame_df = frame_df.drop_duplicates(subset=["theme"])
    return (
        frame_df.head(k)[["theme", "quote", "wave", "state"]]
        .to_dict(orient="records")
    )


def generate_factsheet(
    data_paths: Dict[str, str],
    template_path: str,
    output_html: str,
    assets_dir: str,
    figure_paths: Dict[str, str],
) -> Dict[str, str]:
    """Build the fact sheet HTML (and optional PDF) with embedded figures."""

    theme_counts = pd.read_csv(data_paths["theme_counts"]) if Path(data_paths["theme_counts"]).exists() else pd.DataFrame()
    coocc = pd.read_csv(data_paths["theme_cooccurrence"]) if Path(data_paths["theme_cooccurrence"]).exists() else pd.DataFrame()
    summary = pd.read_csv(data_paths["mixed_methods_summary"]) if Path(data_paths["mixed_methods_summary"]).exists() else pd.DataFrame()
    exemplars = pd.read_csv(data_paths["exemplar_quotes"]) if Path(data_paths["exemplar_quotes"]).exists() else pd.DataFrame()
    reliability_df = pd.read_csv(data_paths["reliability_csv"]) if Path(data_paths["reliability_csv"]).exists() else pd.DataFrame()
    reliability_note = Path(data_paths["reliability_md"]).read_text(encoding="utf-8") if Path(data_paths["reliability_md"]).exists() else "Simulated coder reliability forthcoming."

    key_findings = _build_key_findings(theme_counts, coocc, summary, reliability_df)
    quotes = {
        "household": _select_quotes(exemplars, "household"),
        "provider": _select_quotes(exemplars, "provider"),
    }

    env = Environment(
        loader=FileSystemLoader(str(Path(template_path).parent)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template(Path(template_path).name)

    assets_root = Path(assets_dir)
    figures_dest = assets_root / "figures"
    figures_dest.mkdir(parents=True, exist_ok=True)

    figure_captions = {
        "theme_frequencies_trend": "Theme frequencies across waves",
        "theme_cooccurrence_heatmap": "Theme co-occurrence heatmap",
        "mixed_methods_theme_vs_stress": "Stress score gap by theme",
    }

    figure_cards = []
    output_parent = Path(output_html).parent
    output_parent.mkdir(parents=True, exist_ok=True)

    for key, source_path in figure_paths.items():
        if not source_path:
            continue
        src = Path(source_path)
        if not src.exists():
            continue
        dest = figures_dest / src.name
        shutil.copyfile(src, dest)
        rel = Path(os.path.relpath(dest, output_parent))
        figure_cards.append(
            {
                "src": str(rel).replace("\\", "/"),
                "caption": figure_captions.get(key, src.stem.replace("_", " ").title()),
            }
        )

    context = {
        "header_title": "Qualitative Themes & Mixed-Methods Insights (Synthetic RAPID-style Survey)",
        "key_findings": key_findings,
        "exemplar_quotes": quotes,
        "reliability_note": reliability_note,
        "reliability_rows": [
            {
                "theme": row.theme,
                "percent_agreement": f"{row.percent_agreement:.0%}",
                "kappa": f"{row.kappa:.2f}",
            }
            for row in reliability_df.itertuples()
        ],
        "figure_cards": figure_cards,
        "generated_ts": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }

    html_text = template.render(**context)
    Path(output_html).write_text(html_text, encoding="utf-8")

    pdf_path = None
    if HTML is not None and figure_cards:
        try:  # pragma: no cover - optional
            pdf_path = Path(output_html).with_suffix(".pdf")
            HTML(string=html_text, base_url=str(output_parent)).write_pdf(str(pdf_path))
        except Exception:
            pdf_path = None

    return {
        "factsheet_html": output_html,
        "factsheet_pdf": str(pdf_path) if pdf_path else "",
    }


__all__ = ["generate_factsheet"]
