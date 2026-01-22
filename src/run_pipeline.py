"""End-to-end orchestration for the qualitative + mixed-methods project."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict

try:  # pragma: no cover - allow package or script execution
    from .apply_coding import apply_thematic_coding
    from .codebook import get_codebook
    from .generate_qual_data import generate_synthetic_responses
    from .mixed_methods import mixed_methods_summary, simulate_quant_indicators
    from .reliability import compute_reliability, simulate_second_coder
    from .factsheet import generate_factsheet
    from .report import generate_brief
    from .viz_qual import generate_visualizations
except ImportError:  # pragma: no cover
    from apply_coding import apply_thematic_coding
    from codebook import get_codebook
    from generate_qual_data import generate_synthetic_responses
    from mixed_methods import mixed_methods_summary, simulate_quant_indicators
    from reliability import compute_reliability, simulate_second_coder
    from factsheet import generate_factsheet
    from report import generate_brief
    from viz_qual import generate_visualizations

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_SUBDIRS = [
    "data/raw",
    "data/processed",
    "data/outputs",
    "docs",
    "reports/figures",
    "reports/factsheet_assets/figures",
]


def ensure_directories(base_dir: Path) -> Dict[str, Path]:
    paths: Dict[str, Path] = {}
    for subdir in DATA_SUBDIRS:
        target = base_dir / subdir
        target.mkdir(parents=True, exist_ok=True)
        paths[subdir] = target
    return paths


def run_pipeline(responses: int, waves: int, seed: int, base_dir: Path | None = None) -> None:
    base = Path(base_dir) if base_dir is not None else BASE_DIR
    ensure_directories(base)

    raw_path = (base / "data" / "raw" / "open_ended_responses.csv").resolve()
    raw_df = generate_synthetic_responses(num_responses=responses, num_waves=waves, seed=seed)
    raw_df.to_csv(raw_path, index=False)

    coding_paths = apply_thematic_coding(
        raw_path=str(raw_path),
        codebook=get_codebook(),
        out_dir=str(base / "data"),
        seed=seed,
    )

    simulate_quant_indicators(str(raw_path), seed=seed)
    quant_path = base / "data" / "outputs" / "quantitative_indicators.csv"

    summary_paths = mixed_methods_summary(
        coded_wide_path=coding_paths["coded_wide"],
        quant_path=str(quant_path),
        out_dir=str(base / "data" / "outputs"),
    )

    figures = generate_visualizations(
        theme_freq_path=coding_paths["theme_frequencies"],
        cooccurrence_path=coding_paths["theme_cooccurrence"],
        summary_path=summary_paths["mixed_methods_summary"],
        figures_dir=str(base / "reports" / "figures"),
    )

    coder2_paths = simulate_second_coder(
        coded_wide_path=coding_paths["coded_wide"],
        out_dir=str(base / "data" / "outputs"),
        seed=seed,
    )
    reliability_paths = compute_reliability(
        coded_wide_path=coding_paths["coded_wide"],
        coded_wide_coder2_path=coder2_paths["coded_wide_coder2"],
        out_dir=str(base / "data" / "outputs"),
    )

    brief_path = generate_brief(
        {
            "theme_counts": coding_paths["theme_counts"],
            "exemplar_quotes": coding_paths["exemplar_quotes"],
            "theme_cooccurrence": coding_paths["theme_cooccurrence"],
            "mixed_methods_summary": summary_paths["mixed_methods_summary"],
            "brief_path": str(base / "docs" / "qualitative_brief.md"),
        }
    )

    template_path = base / "templates" / "qual_factsheet_template.html"
    if not template_path.exists():
        template_path = BASE_DIR / "templates" / "qual_factsheet_template.html"

    factsheet_paths = generate_factsheet(
        data_paths={
            "theme_counts": coding_paths["theme_counts"],
            "theme_cooccurrence": coding_paths["theme_cooccurrence"],
            "mixed_methods_summary": summary_paths["mixed_methods_summary"],
            "exemplar_quotes": coding_paths["exemplar_quotes"],
            "reliability_csv": reliability_paths["reliability_csv"],
            "reliability_md": reliability_paths["reliability_md"],
        },
        template_path=str(template_path),
        output_html=str(base / "reports" / "qual_factsheet_latest.html"),
        assets_dir=str(base / "reports" / "factsheet_assets"),
        figure_paths=figures,
    )

    print("Pipeline complete ✔")
    print(f"Raw responses: {raw_path.relative_to(base)}")
    print(f"Coded outputs: {coding_paths['coded_wide']}")
    print(f"Mixed-methods summary: {summary_paths['mixed_methods_summary']}")
    print(f"Reliability table: {reliability_paths['reliability_csv']}")
    print(f"Figures: {figures}")
    print(f"Fact sheet: {factsheet_paths['factsheet_html']}")
    print(f"Brief written to: {Path(brief_path).relative_to(base)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Step A qualitative pipeline.")
    parser.add_argument("--responses", type=int, default=2000, help="Total number of synthetic responses to generate.")
    parser.add_argument("--waves", type=int, default=3, help="Number of survey waves (max 3 for Jan–Mar 2024).")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic random seed.")
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    run_pipeline(responses=arguments.responses, waves=arguments.waves, seed=arguments.seed)
